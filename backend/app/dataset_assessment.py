"""Reproducible, read-only admission diagnosis. No strategy fitting or data acquisition."""
from datetime import date, datetime, time, timezone
from decimal import Decimal
import json
from zoneinfo import ZoneInfo
from sqlalchemy import select
from app.alpaca_normalize import normalize_bars, normalize_calendar, normalize_corporate_actions
from app.data_identity import fingerprint
from app.instrument_evidence import identity_evidence, archived_bytes
from app.market_store import JOBS, RECEIPTS, BARS
from app.universe_store import LISTINGS, utc_text

POLICY = 'daily-trend-data-v2'
MIN_SESSIONS = 252  # Preliminary data floor, not a statistical-power or profitability claim.


def check(code, ok, label, detail, *, warning=False):
    return dict(code=code,state='PASS' if ok else 'WARN' if warning else 'BLOCKED',label=label,detail=detail)


def verified_history(job, receipts, bars, raw_root):
    """Reparse saved originals and compare them to normalized rows and receipt parameters."""
    req = job['request']
    originals, calendar, chain, seen, complete = {}, None, None, set(), False
    actions_chain,actions_seen,actions_complete = None,set(),False
    eastern=ZoneInfo('America/New_York')
    start=datetime.combine(date.fromisoformat(req['start']),time.min,eastern).isoformat()
    end=datetime.combine(date.fromisoformat(req['end']),time(23,59,59),eastern).isoformat()
    bar_receipts = [r for r in receipts if r['kind']=='bars']
    if not 1<=len(bar_receipts)<=12:
        raise ValueError('BAR_RECEIPTS_MISSING')
    for receipt in receipts:
        if receipt['listing_id']!=job['listing_id']:
            raise ValueError('RECEIPT_IDENTITY_MISMATCH')
        if not receipt['payload'].get('real_connection') or receipt['payload'].get('parser_version')!='alpaca-read-v1':
            raise ValueError('NON_REAL_OR_UNKNOWN_PARSER')
        params = receipt['params']
        body = json.loads(archived_bytes(raw_root,receipt['payload_hash']),parse_float=Decimal)
        if receipt['kind']=='bars':
            if (complete or params.get('page_token')!=chain or params.get('feed')!='iex' or params.get('currency')!='USD'
                    or params.get('adjustment')!=req['adjustment'] or params.get('asof')!='-' or params.get('timeframe')!='1Day'
                    or params.get('start')!=start or params.get('end')!=end
                    or receipt['source']!='https://data.alpaca.markets/v2/stocks/'+req['symbol']+'/bars'):
                raise ValueError('HISTORY_REQUEST_MISMATCH')
            rows, token = normalize_bars(body,req['symbol'],params['start'],params['end'],req['adjustment'])
            if receipt['payload']['data']!={'count':len(rows),'next_page_token':token}:
                raise ValueError('BAR_RECEIPT_MISMATCH')
            for row in rows:
                if row['timestamp'] in originals and originals[row['timestamp']]!=row:
                    raise ValueError('CONTRADICTORY_ORIGINAL_BAR')
                originals[row['timestamp']]=row
            if token and token in seen:
                raise ValueError('PAGINATION_CYCLE')
            if token: seen.add(token)
            chain, complete = token, token is None
        elif receipt['kind']=='calendar':
            if calendar is not None or params!={'start':req['start'],'end':req['end']} or receipt['source']!='https://paper-api.alpaca.markets/v2/calendar':
                raise ValueError('CALENDAR_REQUEST_MISMATCH')
            calendar = normalize_calendar(body,req['start'],req['end'])
            if calendar!=receipt['payload']['data']:
                raise ValueError('CALENDAR_RECEIPT_MISMATCH')
        elif receipt['kind']=='corporate_actions':
            if (params.get('symbols')!=req['symbol'] or params.get('start')!=req['start'] or params.get('end')!=req['end']
                    or actions_complete or params.get('page_token')!=actions_chain or params.get('region')!='us'
                    or params.get('data_quality')!='complete'
                    or receipt['source']!='https://data.alpaca.markets/v1/corporate-actions'):
                raise ValueError('ACTIONS_REQUEST_MISMATCH')
            actions,token = normalize_corporate_actions(body,req['symbol'],req['start'],req['end'])
            if actions!=receipt['payload']['data']:
                raise ValueError('ACTIONS_RECEIPT_MISMATCH')
            if token and token in actions_seen:raise ValueError('ACTIONS_PAGINATION_CYCLE')
            if token:actions_seen.add(token)
            actions_chain,actions_complete=token,token is None
        else:
            raise ValueError('UNEXPECTED_HISTORY_RECEIPT')
    if not complete or not actions_complete or calendar is None or sorted(originals.values(),key=lambda r:r['timestamp'])!=bars:
        raise ValueError('ORIGINAL_ROWS_MISMATCH')
    return calendar


def assess_market(service, listing_id, adjustment='raw', cutoff=None, pilot=None, contract_review=None):
    cutoff = cutoff or service.data.clock()
    if cutoff.utcoffset() is None or cutoff>service.data.clock():
        raise ValueError('INVALID_KNOWLEDGE_CUTOFF')
    cutoff=cutoff.astimezone(timezone.utc)
    if service.access()=='DISABLED':
        raise PermissionError('SOURCE_DISABLED')
    if adjustment not in ('raw','split','all'):
        raise ValueError('INVALID_ADJUSTMENT')
    stamp = utc_text(cutoff)
    with service.data.engine.connect() as connection:
        connection.exec_driver_sql('BEGIN')  # Consistent WAL read snapshot; no writes or migration.
        target = connection.execute(select(LISTINGS).where(LISTINGS.c.id==listing_id)).mappings().first()
        if not target:
            raise KeyError(listing_id)
        sec_disabled='A09' in service.data.settings.data_disabled_sources.split(',')
        identity = identity_evidence(connection,service.raw_root.parent.parent/'sec',listing_id,cutoff,{'items':[]} if sec_disabled else pilot,contract_review)
        if sec_disabled:identity['reason']='La fuente SEC está desactivada; no se confirma el vínculo.'
        market_id = identity['market_listing_id'] or (listing_id if target['provider']=='ALPACA' else None)
        job = connection.execute(select(JOBS).where(JOBS.c.listing_id==market_id,JOBS.c.kind=='history',
            JOBS.c.created_at<=stamp,JOBS.c.updated_at<=stamp).order_by(JOBS.c.created_at.desc())).mappings()
        job = next((dict(j) for j in job if j['request'].get('adjustment')==adjustment),None) if market_id else None
        receipts, bars = [], []
        if job:
            receipts = [dict(r) for r in connection.execute(select(RECEIPTS).where(RECEIPTS.c.job_id==job['id'],
                RECEIPTS.c.received_at<=stamp).order_by(RECEIPTS.c.received_at,RECEIPTS.c.id).limit(38)).mappings()]
            bars = list(connection.scalars(select(BARS.c.payload).where(BARS.c.job_id==job['id']).order_by(BARS.c.timestamp).limit(5001)))
    checks = [check('ISSUER_CLASS',identity['state']=='DOCUMENTED','Empresa y clase de acción',identity['reason'])]
    dataset = None
    if not job:
        checks.append(check('HISTORY_PRESENT',False,'Histórico disponible','No hay una captación de esta serie para el instrumento y la fecha de conocimiento seleccionados.'))
    else:
        req, progress = job['request'],job['progress']
        bounded = len(bars)<=5000 and len(receipts)<=37
        complete = job['state']=='SUCCEEDED' and all(progress.get(k+'_complete') for k in ('calendar','bars','corporate_actions'))
        matching = (identity['state']=='DOCUMENTED' and req.get('identity_hash')==identity.get('market_identity_hash')
                    and req.get('asset_id')==identity.get('provider_asset_id')
                    and req.get('listing_id')==market_id and req.get('symbol')==target['symbol'])
        checks.extend([
            check('IMPORT_COMPLETE',complete,'Captación terminada','Estado: '+job['state']+'. Se exige calendario, paginación de barras y consulta de acciones corporativas terminados.'),
            check('DATASET_IDENTITY',matching,'Identidad fijada en la descarga','La identidad observada al descargar debe coincidir con la revisión actual.'),
            check('DIAGNOSTIC_LIMIT',bounded,'Tamaño revisable','Diagnóstico acotado a 5.000 barras y 37 recibos por serie.')])
        calendar, integrity = None, False
        try:
            if not bounded: raise ValueError('DIAGNOSTIC_LIMIT')
            calendar = verified_history(job,receipts,bars,service.raw_root)
            integrity = True
        except (OSError,EOFError,ValueError,KeyError,TypeError,IndexError,OverflowError):
            pass
        checks.append(check('ORIGINAL_INTEGRITY',integrity,'Originales y procedencia','Hashes, parámetros, paginación y filas contrastados contra los originales locales.' if integrity else 'Faltan originales verificables o las filas, parámetros o recibos no coinciden.'))
        days, valid = [], True
        for row in bars:
            try:
                when = datetime.fromisoformat(row['timestamp'])
                local = when.astimezone(ZoneInfo('America/New_York'))
                values = [Decimal(row[k]) for k in ('open','high','low','close','volume')]
                o,h,l,c,v = values
                valid &= (when.utcoffset() is not None and when<=cutoff and local.hour==local.minute==local.second==0
                    and all(x.is_finite() for x in values) and min(o,h,l,c)>0 and v>=0 and l<=min(o,c)<=max(o,c)<=h
                    and row['symbol']==req['symbol'] and row['feed']=='iex' and row['currency']=='USD' and row['adjustment']==adjustment)
                days.append(local.date().isoformat())
            except (ValueError,KeyError,TypeError,ArithmeticError): valid=False
        expected = {r['date'] for r in calendar} if calendar is not None else None
        missing = sorted(expected-set(days)) if expected is not None else None
        unexpected = sorted(set(days)-expected) if expected is not None else None
        duplicates = len(days)-len(set(days))
        in_window = all(req['start']<=day<=req['end'] for day in days)
        checks.extend([
            check('BAR_VALIDITY',valid and bool(bars) and in_window,'Valores y unidades','OHLC positivos, volumen no negativo, una serie IEX/USD por acción y fechas dentro del intervalo.'),
            check('DAILY_GRAIN',bool(days) and duplicates==0,'Una barra por sesión',f'{duplicates} sesiones duplicadas; fechas interpretadas en America/New_York.'),
            check('SESSION_COVERAGE',bool(expected) and missing==[] and unexpected==[],'Cobertura del intervalo',f'{len(set(days))} sesiones observadas; '+(f'{len(expected)} esperadas, {len(missing)} ausentes y {len(unexpected)} inesperadas.' if expected is not None else 'calendario no verificable.')),
            check('MINIMUM_HISTORY',len(set(days))>=MIN_SESSIONS,'Longitud para tendencia diaria',f'{len(set(days))} sesiones; mínimo preliminar {MIN_SESSIONS}. No acredita potencia estadística ni sustituye el protocolo de B3.')])
        dataset = dict(id=job['id'],start=req['start'],end=req['end'],adjustment=adjustment,feed='iex',price_currency='USD',
            price_unit='PER_SHARE',volume_unit='SHARES',bars=len(bars),sessions=len(set(days)),expected_sessions=len(expected) if expected is not None else None,
            missing_sessions=missing,unexpected_sessions=unexpected,duplicate_sessions=duplicates,known_from=max((r['received_at'] for r in receipts),default=job['created_at']),
            rows_sha256=fingerprint(bars),receipts=[dict(id=r['id'],kind=r['kind'],sha256=r['payload_hash'],received_at=r['received_at'],url=r['source']) for r in receipts])
    checks.extend([
        check('NATIVE_CURRENCY',identity['native_currency_state']=='DOCUMENTED_OBSERVATION','Divisa del contrato observado',identity['native_currency_reason']),
        check('HISTORICAL_IDENTITY',False,'Identidad durante el histórico','El vínculo revisado no acredita continuidad de clase, mercado y símbolo durante todo el intervalo. Faltan aliases y cambios históricos contrastados.'),
        check('CORPORATE_ACTIONS',False,'Ajustes y acciones corporativas','La consulta por fecha de proceso no acredita exhaustividad por fecha efectiva. Falta conciliar dividendos, splits y ajustes contra los precios.'),
        check('KNOWLEDGE_TIME',False,'Disponibilidad en cada fecha','Los recibos acreditan conocimiento local desde la descarga; no lo que se sabía en cada sesión histórica. asof=- solo desactiva el mapeo de símbolos.'),
        check('UNIVERSE_SELECTION',False,'Selección del universo','Piloto de datos seleccionado para pruebas de ingeniería. Sin universo histórico ni tratamiento de bajas; no permite inferir rendimiento de un universo amplio.'),
        check('BACKTEST_USAGE',False,'Alcance autorizado de los datos','El diagnóstico conserva el uso local del piloto. No acredita derechos de redistribución ni admisibilidad del conjunto para minería a escala.'),
        check('FEED_SCOPE',False,'Cobertura de mercado','IEX es un solo mercado; no representa el precio consolidado estadounidense.',warning=True)])
    structural = {'ISSUER_CLASS','IMPORT_COMPLETE','DATASET_IDENTITY','DIAGNOSTIC_LIMIT','ORIGINAL_INTEGRITY','BAR_VALIDITY','DAILY_GRAIN','SESSION_COVERAGE'}
    exploratory = dataset is not None and all(c['state']=='PASS' for c in checks if c['code'] in structural)
    result = dict(policy=POLICY,family='Tendencia diaria · piloto de datos',as_of=stamp,listing_id=listing_id,identity=identity,dataset=dataset,
        checks=checks,research_state='EXPLORATORY_ONLY' if exploratory else 'INSUFFICIENT_DATA',backtest_state='BLOCKED',execution_ready=False,
        scope='PERSONAL_LOCAL',minimum_sessions=MIN_SESSIONS)
    result['manifest_id']=fingerprint({k:v for k,v in result.items() if k!='as_of'})
    return result

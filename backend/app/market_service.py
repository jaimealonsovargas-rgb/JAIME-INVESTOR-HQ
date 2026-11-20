"""Explicit, bounded reads; no trading, background subscription or paid feed fallback."""
import hashlib
import json
import threading
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo
from sqlalchemy import select, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.alpaca_http import AlpacaHttp, request_spec
from app.alpaca_normalize import (normalize_bars, normalize_snapshot, normalize_calendar,
    normalize_clock, normalize_account, normalize_positions, normalize_corporate_actions)
from app.alpaca_quota import reserve, backoff
from app.data_http import FetchError
from app.data_identity import fingerprint
from app.market_store import MarketStore, JOBS, RECEIPTS, BARS, ENDPOINTS
from app.universe_store import LISTINGS, utc_text
from app.universe_contracts import parse_catalogue
from app.sec_http import archive_raw
from app.storage_budget import admitted, StorageBlocked

LABELS = dict(assets='Catálogo de instrumentos', clock='Sesión de mercado', calendar='Calendario bursátil',
    snapshot='Último precio IEX', bars='Históricos diarios IEX', corporate_actions='Acciones corporativas',
    account='Cuenta PAPER', positions='Posiciones PAPER')


class MarketService:
    def __init__(self, data, http=None, raw_root=None):
        self.data, self.store = data, MarketStore(data.engine)
        self.http = http or AlpacaHttp(data.settings)
        self.raw_root = Path(raw_root) if raw_root else Path(make_url(str(data.engine.url)).database).parent / 'market' / 'raw'
        self._stop, self._thread, self.worker_error = threading.Event(), None, None

    def access(self):
        s = self.data.settings
        if not s.alpaca_market_enabled or not s.data_public_enabled or 'B04' in s.data_disabled_sources.split(','):
            return 'DISABLED'
        return 'READY_TO_FETCH' if all(s.secret(k) for k in ('alpaca_api_key', 'alpaca_secret_key')) else 'NO_CREDENTIALS'

    @admitted
    def enqueue(self, key, body):
        if self.access() != 'READY_TO_FETCH':
            raise ValueError(self.access())
        if body['kind'] == 'history':
            a, b = date.fromisoformat(body['start']), date.fromisoformat(body['end'])
            today = self.data.clock().astimezone(ZoneInfo('America/New_York')).date()
            if a > b or (b-a).days > 3660 or b >= today or a < date(2016, 1, 1):
                raise ValueError('HISTORY_WINDOW_INVALID')
        return self.store.job(self.store.enqueue(key, body, self.data.clock()))

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name='market-read-worker', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=55)

    def _run(self):
        while not self._stop.is_set():
            try:
                worked = self.step()
                self.worker_error = None
            except Exception:
                self.worker_error, worked = 'LOCAL_WORKER_ERROR', False
            self._stop.wait(0.1 if worked else 1)

    @staticmethod
    def params(job, kind):
        req, p = job['request'], {}
        if kind in ('calendar', 'corporate_actions'):
            p.update(start=req['start'], end=req['end'])
        if kind in ('snapshot', 'bars', 'corporate_actions'):
            p['symbol'] = req['symbol']
        if kind == 'bars':
            eastern = ZoneInfo('America/New_York')
            p.update(start=datetime.combine(date.fromisoformat(req['start']), time.min, eastern).isoformat(),
                end=datetime.combine(date.fromisoformat(req['end']), time(23, 59, 59), eastern).isoformat(),
                adjustment=req['adjustment'])
        if kind in ('bars', 'corporate_actions'):
            p['limit'] = 1000
            if job['progress']['next_token']:
                p['page_token'] = job['progress']['next_token']
        return p

    def step(self):
        try:
            result = self._admitted_step()
            self.storage_block = None
            return result
        except StorageBlocked as error:
            self.storage_block = str(error)
            return False

    @admitted
    def _admitted_step(self):
        if self.access() != 'READY_TO_FETCH':
            return False
        now = self.data.clock()
        job = self.store.claim(now)
        if job is None:
            return False
        kind = job['progress']['steps'][job['progress']['step']]
        optional = kind in ('clock', 'calendar', 'corporate_actions', 'account', 'positions')
        try:
            if job['listing_id']:
                current = self.store.target(job['listing_id'])
                if fingerprint(current['payload']) != job['request']['identity_hash']:
                    raise ValueError('IDENTITY_CHANGED')
            with Session(self.data.engine) as s, s.begin():
                s.connection().exec_driver_sql('BEGIN IMMEDIATE')
                blocked = reserve(s, now)
            if blocked:
                self.store.defer(job, 'RATE_LIMITED', now,
                    max(1, (datetime.fromisoformat(blocked)-now).total_seconds()), attempted=False)
                return True
            params = self.params(job, kind)
            raw = self.http.fetch(kind, params)
            received = self.data.clock()
            body = json.loads(raw, parse_float=Decimal, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NON_FINITE')))
            bars, next_token, catalogue = None, None, None
            if kind == 'assets':
                catalogue = parse_catalogue('ALPACA', body)
                payload = {'count': len(catalogue), 'selection': 'active us_equity; no universo histórico'}
            elif kind == 'bars':
                bars, next_token = normalize_bars(body, params['symbol'], params['start'], params['end'], params['adjustment'])
                payload = {'count': len(bars), 'next_page_token': next_token}
            elif kind == 'snapshot':
                payload = normalize_snapshot(body, params['symbol'], received)
            elif kind == 'calendar':
                payload = normalize_calendar(body, params['start'], params['end'])
            elif kind == 'clock':
                payload = normalize_clock(body, received)
            elif kind == 'account':
                payload = normalize_account(body)
            elif kind == 'positions':
                payload = normalize_positions(body)
            else:
                payload, next_token = normalize_corporate_actions(body, params['symbol'], params['start'], params['end'])
            digest = hashlib.sha256(raw).hexdigest()
            # Private account identifiers are deliberately not archived. Their validated fields and hash are retained.
            if kind not in ('account', 'positions'):
                size = sum(f.stat().st_size for f in self.raw_root.rglob('*.gz')) if self.raw_root.exists() else 0
                if size + len(raw) > 512 * 1024 * 1024:
                    raise ValueError('LOCAL_STORAGE_LIMIT')
                archive_raw(self.raw_root, raw)
            source, sent = request_spec(kind, params)
            envelope = dict(data=payload, real_connection=bool(self.http.real), parser_version='alpaca-read-v1')
            self.store.accept(job, kind, envelope, digest, source, sent, received, self.data.clock(),
                bars=bars, next_token=next_token, catalogue=catalogue)
        except FetchError as error:
            now = self.data.clock()
            delay = max(1, error.retry_after) if error.state == 'RATE_LIMITED' else min(60, 5*3**job['attempts'])
            if error.state == 'RATE_LIMITED':
                with Session(self.data.engine) as s, s.begin():
                    s.connection().exec_driver_sql('BEGIN IMMEDIATE')
                    backoff(s, now, delay)
            self.store.defer(job, error.state, now, delay, terminal=error.state in (
                'AUTH_FAILED', 'RIGHTS_RESTRICTED', 'NOT_FOUND', 'CONFIG_REQUIRED', 'NO_CREDENTIALS', 'INVALID_PAYLOAD'), optional=optional)
        except ValueError as error:
            code = str(error) if str(error) in ('LOCAL_STORAGE_LIMIT', 'IDENTITY_CHANGED', 'PAGINATION_CYCLE_OR_LIMIT', 'CONTRADICTORY_BAR') else 'INVALID_PAYLOAD'
            self.store.defer(job, code, self.data.clock(), terminal=True, optional=optional and code == 'INVALID_PAYLOAD')
        except (KeyError, TypeError, IndexError, InvalidOperation, OverflowError, AttributeError):
            self.store.defer(job, 'INVALID_PAYLOAD', self.data.clock(), terminal=True, optional=optional)
        except OSError:
            self.store.defer(job, 'LOCAL_STORAGE_ERROR', self.data.clock(), delay=30)
        return True

    def summary(self):
        now, access = self.data.clock(), self.access()
        with self.data.engine.connect() as c:
            statuses = {r['id']: dict(r) for r in c.execute(select(ENDPOINTS)).mappings()}
            jobs = [self.store.public(r) for r in c.execute(select(JOBS).order_by(JOBS.c.created_at.desc()).limit(10)).mappings()]
            counts = dict(assets=c.execute(select(func.count()).select_from(LISTINGS).where(LISTINGS.c.provider == 'ALPACA')).scalar_one(),
                bars=c.execute(select(func.count()).select_from(BARS)).scalar_one(),
                bar_sets=c.execute(select(func.count()).select_from(JOBS).where(JOBS.c.kind == 'history', JOBS.c.state.in_(('SUCCEEDED', 'PARTIAL')))).scalar_one())
        endpoints = []
        for ident, label in LABELS.items():
            saved = statuses.get(ident)
            state = saved['state'] if saved else 'NOT_VERIFIED'
            reason = saved['reason'] if saved else 'Todavía no se ha comprobado este acceso.'
            if access != 'READY_TO_FETCH':
                state, reason = access, 'Configura las claves PAPER localmente y reinicia el backend.' if access == 'NO_CREDENTIALS' else 'Captación desactivada en la configuración local.'
            elif saved and state == 'AVAILABLE' and now-datetime.fromisoformat(saved['checked_at']) > timedelta(days=1):
                state, reason = 'STALE', 'Última comprobación de acceso de más de un día.'
            endpoints.append(dict(id=ident, label=label, state=state, checked_at=saved['checked_at'] if saved else None, reason=reason))
        account = self.store.latest('account', as_of=now)
        positions = self.store.latest('positions', as_of=now)
        paper_state = 'NO_DATA'
        if account:
            paper_state = 'AVAILABLE' if now-datetime.fromisoformat(account['received_at']) <= timedelta(minutes=5) else 'STALE'
        if access != 'READY_TO_FETCH':
            paper_state = access
        # Positions from another refresh are not silently joined to the latest account snapshot.
        coherent = account and positions and account['job_id'] == positions['job_id']
        visible = access != 'DISABLED'
        return dict(as_of=utc_text(now), source=dict(state=access, feed='iex', mode='PAPER_READ_ONLY',
            reason='Claves presentes; comprueba cada acceso. IEX es cobertura parcial del mercado.' if access == 'READY_TO_FETCH' else
                'Faltan ALPACA_API_KEY y ALPACA_SECRET_KEY en .env; no compartas claves por chat.' if access == 'NO_CREDENTIALS' else 'Captación Alpaca desactivada.'),
            endpoints=endpoints, counts=counts, jobs=jobs,
            paper=dict(state=paper_state, as_of=account['received_at'] if account and visible else None,
                account=account['payload']['data'] if account and visible else None,
                positions=positions['payload']['data'] if coherent and visible else [], positions_complete=bool(coherent)),
            orders_enabled=False, worker_running=bool(self._thread and self._thread.is_alive()), worker_error=self.worker_error,
            refresh_mode='EXPLICIT_REQUESTS', streaming_enabled=False)

    def detail(self, ident, adjustment='raw', as_of=None):
        now = as_of or self.data.clock()
        with self.data.engine.connect() as c:
            row = c.execute(select(LISTINGS).where(LISTINGS.c.id == ident)).mappings().first()
            if not row:
                raise KeyError(ident)
            if row['first_seen_at'] > utc_text(now):
                raise KeyError(ident)
            candidates = []
            if row['provider'] == 'SEC':
                for r in c.execute(select(LISTINGS).where(LISTINGS.c.provider == 'ALPACA', LISTINGS.c.symbol == row['symbol'],
                    LISTINGS.c.venue == row['venue'], LISTINGS.c.state == 'IDENTIFIED', LISTINGS.c.first_seen_at <= utc_text(now)).limit(10)).mappings():
                    candidates.append(dict(id=r['id'], name=r['name'], symbol=r['symbol'], venue=r['venue'],
                        reason='Coinciden símbolo y mercado; vínculo de emisor y clase accionaria sin confirmar. Abrir por separado.'))
        valid = False
        try:
            self.store.target(ident)
            valid = True
        except (ValueError, KeyError):
            pass
        quote = dict(state='NO_DATA' if valid else 'BLOCKED', as_of=None, received_at=None, feed='iex',
            price=None, bid=None, ask=None, reason='Solicita una observación del instrumento Alpaca.' if valid else
                'Selecciona un instrumento Alpaca identificado; no se asignan precios por ticker SEC.',
            market_state='UNKNOWN', market_checked_at=None, quote_at=None)
        clock = self.store.latest('clock', as_of=now)
        if clock:
            clock_data = clock['payload']['data']
            age = (now-datetime.fromisoformat(clock_data['timestamp'])).total_seconds()
            if 0 <= age <= 120:
                quote.update(market_state='OPEN' if clock_data['is_open'] else 'CLOSED', market_checked_at=clock_data['timestamp'])
        observed = self.store.latest('snapshot', ident, now, fingerprint(row['payload'])) if valid else None
        history = self.history(ident, adjustment, now, fingerprint(row['payload'])) if valid else dict(series=[], manifest=None, sets=[])
        if observed:
            data = observed['payload']['data']
            trade, q = data['trade'], data['quote']
            if trade and datetime.fromisoformat(trade['timestamp']) <= now:
                age = (now-datetime.fromisoformat(trade['timestamp'])).total_seconds()
                quote.update(state='AVAILABLE' if age <= 90 else 'STALE', price=trade['price'], as_of=trade['timestamp'],
                    reason='Última operación observada en IEX; no precio consolidado.' if age <= 90 else
                        'Última operación IEX antigua; no debe utilizarse como precio actual.')
            quote.update(received_at=observed['received_at'])
            if q and 0 <= (now-datetime.fromisoformat(q['timestamp'])).total_seconds() <= 90:
                quote.update(bid=q['bid'], ask=q['ask'], quote_at=q['timestamp'])
        result = dict(listing_id=ident, identity=dict(state='PROVIDER_IDENTIFIED' if valid else 'UNLINKED',
            reason='Identificado por UUID de Alpaca. Emisor SEC y clase accionaria detallada sin certificar.' if valid else
                'Identidad SEC conservada; el vínculo con un instrumento de mercado todavía no está confirmado.',
            asset_id=row['provider_key'] if valid else None, symbol=row['symbol'], venue=row['venue'],
            currency='USD' if observed or history['manifest'] else None, issuer_link='UNCONFIRMED', candidates=candidates),
            quote=quote, history=history, execution_ready=False, backtest_ready=False)
        from app.dataset_assessment import assess_market
        result['assessment'] = assess_market(self,ident,adjustment,now)
        if result['assessment']['identity']['state']=='DOCUMENTED':
            result['identity'].update(issuer_link='DOCUMENTED',reason=result['assessment']['identity']['reason'])
        return result

    def history(self, ident, adjustment, now, identity_hash=None):
        manifests, series = [], []
        if identity_hash is None:
            identity_hash = fingerprint(self.store.target(ident)['payload'])
        with self.data.engine.connect() as c:
            jobs = list(c.execute(select(JOBS).where(JOBS.c.listing_id == ident, JOBS.c.kind == 'history',
                JOBS.c.state.in_(('SUCCEEDED', 'PARTIAL')), JOBS.c.updated_at <= utc_text(now),
                func.json_extract(JOBS.c.request, '$.identity_hash') == identity_hash,
                func.json_extract(JOBS.c.request, '$.adjustment') == adjustment)
                .order_by(JOBS.c.updated_at.desc()).limit(5)).mappings())
            for job in jobs:
                if not job['progress'].get('bars_complete') or job['request']['adjustment'] != adjustment:
                    continue
                req = job['request']
                rows = [r['payload'] for r in c.execute(select(BARS).where(BARS.c.job_id == job['id']).order_by(BARS.c.timestamp)).mappings()]
                calendar = c.execute(select(RECEIPTS).where(RECEIPTS.c.job_id == job['id'], RECEIPTS.c.kind == 'calendar')).mappings().first()
                days = {datetime.fromisoformat(r['timestamp']).astimezone(ZoneInfo('America/New_York')).date().isoformat() for r in rows}
                sessions = {r['date'] for r in calendar['payload']['data']} if calendar else None
                missing = len(sessions-days) if sessions is not None else None
                unexpected = len(days-sessions) if sessions is not None else None
                manifest = dict(id=job['id'], start=req['start'], end=req['end'], adjustment=adjustment, feed='iex',
                    state='OBSERVED_SESSIONS' if missing == 0 and unexpected == 0 and rows else 'PARTIAL_COVERAGE',
                    bars=len(rows), first_at=rows[0]['timestamp'] if rows else None, last_at=rows[-1]['timestamp'] if rows else None,
                    received_at=job['updated_at'], expected_sessions=len(sessions) if sessions is not None else None,
                    missing_sessions=missing, unexpected_sessions=unexpected,
                    coverage_note='IEX es un solo mercado. Las ausencias no se rellenan. Acciones corporativas por fecha de proceso, sin certificar exhaustividad. Sin universo histórico ni aceptación para backtest.',
                    corporate_actions_state='AVAILABLE' if job['progress'].get('corporate_actions_complete') else 'NOT_VERIFIED',
                    source='https://data.alpaca.markets/v2/stocks/' + req['symbol'] + '/bars',
                    receipt_hashes=[r for r in c.execute(select(RECEIPTS.c.payload_hash).where(RECEIPTS.c.job_id == job['id'])).scalars()],
                    currency='USD', symbol_mapping='disabled', temporal_scope='LOCAL_KNOWLEDGE_ONLY')
                manifests.append(manifest)
                if len(manifests) == 1:
                    series = [dict(t=r['timestamp'], o=r['open'], h=r['high'], l=r['low'], c=r['close'], v=r['volume']) for r in rows]
        return dict(series=series, manifest=manifests[0] if manifests else None, sets=manifests)

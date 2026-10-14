"""Parsers compartidos sin SDK. Decimal desde texto; periodos no son publicación."""
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET
from app.data_catalog import Source
from app.data_contracts import Observation

UTC=timezone.utc

def number(value):
    if value in (None,'','.','NA','N/A',':','-','–'):
        return None
    try:value=Decimal(str(value))
    except InvalidOperation:raise ValueError('Valor no numérico.') from None
    if not value.is_finite():
        raise ValueError('Número no finito.')
    return value

def period_time(period):
    period=str(period)
    if re.fullmatch(r'\d{4}',period):
        return datetime(int(period),1,1,tzinfo=UTC),'year'
    if re.fullmatch(r'\d{4}-Q[1-4]',period):
        return datetime(int(period[:4]),int(period[-1])*3-2,1,tzinfo=UTC),'quarter'
    if re.fullmatch(r'\d{4}-\d{2}',period):
        return datetime.fromisoformat(period+'-01').replace(tzinfo=UTC),'month'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',period):
        return datetime.fromisoformat(period).replace(tzinfo=UTC),'day'
    dt=datetime.fromisoformat(period.replace('Z','+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp sin zona horaria.')
    return dt.astimezone(UTC),'instant'

def safe_xml(raw):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Entidades XML prohibidas.')
    try:return ET.fromstring(raw)
    except ET.ParseError:raise ValueError('XML inválido.') from None

def parse(source: Source, raw: bytes, received: datetime):
    digest=hashlib.sha256(raw).hexdigest();result=[]
    def emit(period,value,unit,series=None,currency=None,metadata=None,bid=None,ask=None,country=None):
        when,precision=period_time(period);series=str(series or source.feed)
        val=number(value)
        if val is None and source.kind not in ('instrument_metadata','news_metadata'):
            return
        flags=('REFERENCE_NOT_EXECUTABLE',) if source.kind in ('fx_reference','yield_curve','macro_series') else ('NON_EXECUTABLE_P2',)
        if source.parser=='imf':flags+=('ESTIMATE_OR_FORECAST',)
        if source.parser in ('alpaca','alpha'):flags+=('HISTORICAL_EOD',)
        fields=dict(provider=source.provider,access_id=source.id,feed=source.feed,series_id=series,data_kind=source.kind,venue=source.venue,country=country or source.country,asset_class=source.asset_class,source_ref=source.url or source.docs,payload_hash=digest,observed_at=when,received_at=received,period=str(period),period_precision=precision,currency=currency,unit=unit,value=val,bid=number(bid),ask=number(ask),metadata={str(k):str(v) for k,v in (metadata or {}).items() if v is not None},delay_seconds=None,stale_after_seconds=source.ttl,rights=source.rights,quality_flags=flags)
        ident=hashlib.sha256((source.id+series+str(period)+digest).encode()).hexdigest()
        result.append(Observation(id=ident,**fields))
    parser=source.parser
    # SDMX 2.1 permite negociación a XML; BIS devuelve StructureSpecificData.
    if parser=='sdmx_csv' and raw.lstrip().startswith(b'<'):
        root=safe_xml(raw)
        if root.tag.split('}')[-1] not in ('StructureSpecificData','GenericData'):
            raise ValueError('XML no es SDMX Data.')
        for series in root.findall('.//{*}Series'):
            dimensions=dict(series.attrib)
            for node in series.findall('.//{*}SeriesKey/{*}Value'):
                dimensions[node.attrib['id']]=node.attrib['value']
            key=dimensions.get('KEY') or '.'.join(dimensions.get(k,'') for k in ('FREQ','EER_TYPE','EER_BASKET','REF_AREA'))
            for obs in series.findall('./{*}Obs'):
                row={**dimensions,**obs.attrib}
                time=row.get('TIME_PERIOD');value=row.get('OBS_VALUE')
                dimension=obs.find('./{*}ObsDimension');observation=obs.find('./{*}ObsValue')
                if dimension is not None:time=dimension.attrib.get('value')
                if observation is not None:value=observation.attrib.get('value')
                if time:
                    emit(time,value,row.get('UNIT_MEASURE','SDMX index'),key,metadata={k:row[k] for k in ('UNIT_MULT','DECIMALS','OBS_STATUS','BASE_PER') if k in row},country=row.get('REF_AREA'))
        return tuple(result[:500])
    if parser=='sdmx_csv':
        text=raw.decode('utf-8-sig')
        reader=csv.DictReader(io.StringIO(text))
        if not {'TIME_PERIOD','OBS_VALUE'}<=set(reader.fieldnames or []):raise ValueError('Cabecera SDMX-CSV ausente.')
        for row in reader:
            key=row.get('KEY') or '.'.join(str(row.get(k,'')) for k in ('REF_AREA','FREQ','MEASURE','UNIT_MEASURE'))
            value=number(row.get('OBS_VALUE'))
            multiplier=int(row.get('UNIT_MULT') or 0)
            if abs(multiplier)>18:raise ValueError('Multiplicador SDMX no admitido.')
            unit=row.get('UNIT_MEASURE') or row.get('UNIT') or 'SDMX (unidad del feed)'
            if source.id=='A01':unit='USD per EUR · fixing BCE'
            emit(row['TIME_PERIOD'],value*(Decimal(10)**multiplier) if value is not None else None,unit,key,currency=row.get('CURRENCY'),metadata={k:row[k] for k in ('UNIT_MULT','OBS_STATUS','DECIMALS','CURRENCY_DENOM','REF_AREA','Reference area','Unit of measure') if k in row},country=row.get('REF_AREA'))
    elif parser in ('treasury','firds','firds_index'):
        root=safe_xml(raw)
        if parser=='treasury':
            for entry in root.findall('.//{*}entry'):
                fields={node.tag.split('}')[-1]:node.text for node in entry.iter() if node.text and not list(node)}
                date=fields.get('NEW_DATE') or fields.get('date')
                for key,value in fields.items():
                    if key.startswith('BC_'):
                        emit(date[:10],value,'percent per annum',key,metadata={'curve':'nominal par yield; NOT bond price'})
        elif parser=='firds_index':
            for doc in root.findall('.//doc'):
                row={n.attrib.get('name'):n.text for n in doc if n.text}
                if row.get('download_link') and row.get('publication_date'):
                    emit(row['publication_date'],None,'FIRDS file index',row.get('file_name') or row['download_link'],metadata={k:row.get(k) for k in ('download_link','file_name','publication_date')})
        else:
            for node in root.findall('.//{*}FinInstrmGnlAttrbts'):
                fields={n.tag.split('}')[-1]:n.text for n in node.iter() if n.text and not list(n)}
                if fields.get('Id'):
                    emit(received.isoformat(),None,'metadata',fields['Id'],metadata=fields)
    else:
        data=json.loads(raw,parse_float=Decimal,parse_constant=lambda _v:(_ for _ in ()).throw(ValueError('No finito')))
        if parser=='bde':
            for row in data:
                precision=str(row.get('codFrecuencia','')).upper()
                period=row['fechaValor'][:7] if precision=='M' else row['fechaValor'][:4] if precision=='A' else row['fechaValor'][:10]
                emit(period,row['valor'],str(row.get('simbolo') or row.get('descripcionCorta') or 'BIEST'),row['serie'],metadata={k:row[k] for k in ('codFrecuencia','decimales','descripcionCorta') if k in row})
        elif parser=='ine':
            for series in data:
                for row in series.get('Data',[]):
                    stamp=datetime.fromtimestamp(float(Decimal(row['Fecha'])/1000),tz=UTC)
                    emit(stamp.date().isoformat(),row.get('Valor'),str(series.get('Nombre','INE')),series.get('COD',series.get('Nombre')),metadata={'frequency':row.get('FK_Periodo'),'year':row.get('Anyo'),'period_start':'Fecha INE, no fecha de publicación'})
        elif parser=='jsonstat':
            dimensions=data['dimension'];ids=data['id'];sizes=data['size'];values=data.get('value',{})
            indexed={dim:{int(i):label for label,i in dimensions[dim]['category']['index'].items()} for dim in ids}
            for idx,value in (values.items() if isinstance(values,dict) else enumerate(values)):
                if value is None:continue
                n=int(idx);coords={}
                for dim,size in reversed(list(zip(ids,sizes))):
                    coords[dim]=indexed[dim][n%size];n//=size
                unit=dimensions.get('unit',{}).get('category',{}).get('label',{}).get(coords.get('unit'),coords.get('unit','Eurostat'))
                emit(coords['time'],value,unit,'.'.join(coords[d] for d in ids if d!='time'),metadata=coords)
        elif parser=='worldbank':
            for row in data[1] or []:
                emit(row['date'],row['value'],'current USD',row['indicator']['id'],currency='USD',metadata={'indicator':row['indicator']['value'],'country':row['country']['value']})
        elif parser=='imf':
            for indicator,countries in data['values'].items():
                if indicator!='NGDP_RPCH':continue
                for country,points in countries.items():
                    if country!='ESP':continue
                    for year,value in points.items():
                        if year not in source.params['periods'].split(','):continue
                        emit(year,value,'percent change · WEO estimates/projections',indicator+'/'+country,metadata={'dataset':'IMF World Economic Outlook','quality':'ESTIMATE_OR_FORECAST; not a trading signal'})
        elif parser=='bls':
            if data.get('status')!='REQUEST_SUCCEEDED':raise ValueError('BLS no devuelve datos.')
            for series in data['Results']['series']:
                for row in series['data']:
                    if row['period']=='M13':continue
                    emit(row['year']+'-'+row['period'][1:],row['value'],'CPI index 1982-84=100',series['seriesID'],metadata={'periodName':row.get('periodName'),'footnotes':row.get('footnotes')})
        elif parser=='sec':
            for tag,fact in data['facts'].get('us-gaap',{}).items():
                if tag not in ('Assets','Revenues','NetIncomeLoss','StockholdersEquity'):continue
                for unit,rows in fact['units'].items():
                    for row in rows[-5:]:
                        emit(row['end'],row['val'],unit,'CIK'+str(data['cik'])+'/us-gaap/'+tag,currency=unit if len(unit)==3 else None,metadata={'start':row.get('start'),'filed':row.get('filed'),'form':row.get('form'),'accn':row['accn'],'frame':row.get('frame'),'label':fact.get('label')})
        elif parser=='kraken':
            if data['error']:raise ValueError('Kraken rechaza consulta.')
            for pair,rows in data['result'].items():
                if pair=='last':continue
                for row in rows:
                    emit(datetime.fromtimestamp(float(Decimal(row[2])),UTC).isoformat(),row[0],'USD per XBT',pair,currency='USD',metadata={'trade_time':'exchange timestamp'})
        elif parser=='binance':
            for row in data:
                emit(datetime.fromtimestamp(float(Decimal(row['T'])/1000),UTC).isoformat(),row['p'],'USDT per BTC','BTCUSDT',currency='USDT',metadata={'aggTradeId':row['a'],'quote_asset':'USDT (not USD)'})
        elif parser=='paprika':
            emit(data['last_updated'],data['quotes']['USD']['price'],'USD per BTC',data['id'],currency='USD',metadata={'name':data['name'],'symbol':data['symbol'],'price_type':'aggregated'})
        elif parser=='coingecko':
            for coin,row in data.items():
                emit(datetime.fromtimestamp(row['last_updated_at'],UTC).isoformat(),row['usd'],'USD per crypto',coin,currency='USD',metadata={'price_type':'aggregated'})
        elif parser=='coinbase':
            emit(data['time'],data['price'],'USD per BTC','BTC-USD',currency='USD',bid=data.get('bid'),ask=data.get('ask'))
        elif parser=='gdelt':
            for row in data.get('articles',[]):
                stamp=datetime.strptime(row['seendate'],'%Y%m%dT%H%M%SZ').replace(tzinfo=UTC)
                emit(stamp.isoformat(),None,'news metadata',row['url'],metadata={k:row.get(k) for k in ('title','url','domain','language','sourcecountry')})
        elif parser=='openfigi':
            for job in data:
                for row in job.get('data',[]):
                    emit(received.isoformat(),None,'identifier metadata',row['figi'],metadata={k:row.get(k) for k in ('figi','name','ticker','exchCode','securityType','marketSector','shareClassFIGI','compositeFIGI')})
        elif parser=='fred':
            for row in data['observations']:
                emit(row['date'],row['value'],'percent per annum','DGS10',metadata={'realtime_start':row.get('realtime_start'),'realtime_end':row.get('realtime_end'),'original_provider':'US Treasury'})
        elif parser=='bea':
            for row in data['BEAAPI']['Results']['Data']:
                emit(row['TimePeriod'],str(row['DataValue']).replace(',',''),row.get('UNIT','BEA table T10101'),row['SeriesCode'],metadata={k:row.get(k) for k in ('LineDescription','METRIC_NAME','UNIT_MULT','CL_UNIT')})
        elif parser=='eia':
            for row in data['response']['data']:
                emit(row['period'],row['value'],row['units'],row['series'],currency='USD' if 'dollars' in row['units'].lower() else None,metadata={'description':row.get('series-description')})
        elif parser=='alpaca':
            for row in data['bars']:
                emit(row['t'],row['c'],'USD per share',data['symbol'],currency='USD',metadata={'price_type':'IEX daily raw close; NOT SIP','volume':row.get('v')})
        elif parser=='alpha':
            if 'Note' in data or 'Information' in data:raise ValueError('Cuota o plan Alpha Vantage.')
            for date,row in list(data['Time Series (Daily)'].items())[:5]:
                emit(date,row['4. close'],'USD per share','IBM',currency='USD',metadata={'price_type':'raw EOD','timezone':data['Meta Data'].get('5. Time Zone')})
        elif parser in ('t212','twelve','fmp','tiingo'):
            rows=data.get('data',[]) if parser=='twelve' else [data] if parser=='tiingo' else data
            for row in rows[:500]:
                keys={'t212':('ticker','name','isin','currencyCode','type','shortName'),'twelve':('symbol','instrument_name','exchange','mic_code','currency','instrument_type','country'),'fmp':('symbol','companyName','currency','isin','cusip','cik','exchange','isEtf'),'tiingo':('ticker','name','exchangeCode','startDate','endDate')}[parser]
                symbol=row.get('ticker') or row.get('symbol')
                if not symbol:continue
                emit(received.isoformat(),None,'instrument metadata',symbol,currency=row.get('currencyCode') or row.get('currency'),metadata={k:row.get(k) for k in keys})
        elif parser=='massive':
            emit(data['serverTime'],None,'market status','US',metadata={k:data.get(k) for k in ('market','exchanges','earlyHours','afterHours')})
        else:
            raise ValueError('Parser no implementado.')
    return tuple(result[:500])

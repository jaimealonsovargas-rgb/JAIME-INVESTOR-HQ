"""Datos sintéticos TEST_ONLY, red prohibida, nunca ingesta en DB del usuario."""
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.contracts import Instrument
from app.database import InstrumentRegistry, create_db_engine, DataRecord, InstrumentAlias
from app.data_registry import ingest
from app.data_catalog import CATALOG
from app.data_config import DataSettings
from app.data_http import SafeDataHttp, FetchError, validate_request, public_dns, retry_seconds
from app.data_parsers import parse, safe_xml, period_time
from app.data_service import DataService, select_equivalent

NOW=datetime(2026,10,14,tzinfo=timezone.utc)
FIXTURES={
 'bde':[{'fechaValor':'2026-09-01T00:00:00Z','valor':'1.234567890123456789','serie':'TEST_ONLY','descripcionCorta':'TEST_ONLY','simbolo':'%'}],
 'ine':[{'COD':'TEST_ONLY','Nombre':'TEST_ONLY','Data':[{'Fecha':1756684800000,'Valor':'2.3','Anyo':2025,'FK_Periodo':9}]}],
 'jsonstat':{'id':['geo','unit','time'],'size':[1,1,1],'dimension':{'geo':{'category':{'index':{'ES':0}}},'unit':{'category':{'index':{'I15':0},'label':{'I15':'index'}}},'time':{'category':{'index':{'2026-09':0}}}},'value':{'0':'103.1'}},
 'worldbank':[{'pages':1},[{'date':'2025','value':'123','indicator':{'id':'TEST_ONLY','value':'TEST_ONLY'},'country':{'value':'TEST_ONLY'}}]],
 'imf':{'values':{'NGDP_RPCH':{'ESP':{'2025':'1.5','2035':'99'},'TEST_ONLY':{'2025':'99'}}}},
 'bls':{'status':'REQUEST_SUCCEEDED','Results':{'series':[{'seriesID':'TEST_ONLY','data':[{'year':'2025','period':'M01','periodName':'January','value':'103'}]}]}},
 'sec':{'cik':1,'facts':{'us-gaap':{'Assets':{'label':'TEST_ONLY','units':{'USD':[{'end':'2025-12-31','val':100,'accn':'TEST_ONLY','filed':'2026-02-01','form':'10-K'}]}}}}},
 'kraken':{'error':[],'result':{'TEST_ONLY':[['1.234567890123456789','1',1756684800]],'last':'TEST_ONLY'}},
 'binance':[{'T':1756684800000,'p':'1.234567890123456789','a':1}],
 'paprika':{'last_updated':'2026-09-01T00:00:00Z','quotes':{'USD':{'price':'1.234567890123456789'}},'id':'TEST_ONLY','name':'TEST_ONLY','symbol':'TEST_ONLY'},
 'coingecko':{'TEST_ONLY':{'last_updated_at':1756684800,'usd':'1.234567890123456789'}},
 'coinbase':{'time':'2026-09-01T00:00:00Z','price':'1.5','bid':'1.4','ask':'1.6'},
 'gdelt':{'articles':[{'url':'https://example.org/TEST_ONLY','title':'TEST_ONLY','seendate':'20260901T000000Z'}]},
 'openfigi':[{'data':[{'figi':'TEST_ONLY','ticker':'TEST_ONLY','exchCode':'TEST_ONLY','name':'TEST_ONLY'}]}],
 'fred':{'observations':[{'date':'2025-01-01','value':'1.234567890123456789'}]},
 'bea':{'BEAAPI':{'Results':{'Data':[{'TimePeriod':'2025','DataValue':'1,234.5','UNIT':'percent','SeriesCode':'TEST_ONLY'}]}}},
 'eia':{'response':{'data':[{'period':'2025-01-01','value':'1.5','units':'dollars per barrel','series':'TEST_ONLY'}]}},
 'alpaca':{'symbol':'TEST_ONLY','bars':[{'t':'2026-09-01T04:00:00Z','c':'1.5','v':10}]},
 'alpha':{'Meta Data':{'5. Time Zone':'US/Eastern'},'Time Series (Daily)':{'2026-09-01':{'4. close':'1.5'}}},
 't212':[{'ticker':'TEST_ONLY','name':'TEST_ONLY','currencyCode':'EUR','type':'STOCK','isin':'TEST_ONLY'}],
 'twelve':{'data':[{'symbol':'TEST_ONLY','currency':'EUR','instrument_type':'Stock'}]},
 'fmp':[{'symbol':'TEST_ONLY','currency':'EUR','companyName':'TEST_ONLY'}],
 'tiingo':{'ticker':'TEST_ONLY','name':'TEST_ONLY','exchangeCode':'TEST_ONLY'},
 'massive':{'serverTime':'2026-09-01T00:00:00Z','market':'closed'},
}

def body(parser):
    if parser=='sdmx_csv':return b'KEY,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,UNIT_MULT\nTEST_ONLY,2026-09,1.234567890123456789,index,0\n'
    if parser=='treasury':return b'<feed><entry><NEW_DATE>2026-09-01T00:00:00</NEW_DATE><BC_10YEAR>1.5</BC_10YEAR></entry></feed>'
    if parser=='firds_index':return b'<response><result><doc><str name="download_link">https://example.org/TEST_ONLY.zip</str><date name="publication_date">2026-09-01T00:00:00Z</date><str name="file_name">TEST_ONLY.zip</str></doc></result></response>'
    return json.dumps(FIXTURES[parser]).encode()

@pytest.mark.parametrize('source',[s for s in CATALOG.values() if s.implemented],ids=lambda s:s.id)
def test_each_useful_adapter_normalizes_its_response(source):
    rows=parse(source,body(source.parser),NOW)
    assert rows and all(o.access_id==source.id and o.execution_eligible is False for o in rows)
    assert all(o.observed_at.tzinfo is not None and len(o.payload_hash)==64 for o in rows)
    assert all(not isinstance(o.value,float) for o in rows)

def test_catalog_counts_do_not_inflate():
    assert len(CATALOG)==34 and len({s.provider for s in CATALOG.values()})==31
    assert sum(s.implemented for s in CATALOG.values())==32

def http(settings,handler):
    return SafeDataHttp(settings,httpx.MockTransport(handler),resolver=lambda _h:None)

@pytest.mark.parametrize('status,state',[(401,'AUTH_FAILED'),(403,'RIGHTS_RESTRICTED'),(429,'RATE_LIMITED'),(500,'ERROR'),(302,'ERROR')])
def test_http_errors_no_redirects_and_no_response_leak(status,state):
    client=http(DataSettings(_env_file=None),lambda request:httpx.Response(status,headers={'Retry-After':'120','Location':'http://127.0.0.1/'},text='PRIVATE_SECRET'))
    with pytest.raises(FetchError) as caught:client.fetch(CATALOG['A01'])
    assert caught.value.state==state and 'PRIVATE_SECRET' not in str(caught.value)

@pytest.mark.parametrize('method,url',[('POST','https://api.kraken.com/0/private/AddOrder'),('GET','http://127.0.0.1/'),('DELETE',CATALOG['A19'].url),('POST','https://api.openfigi.com/v3/search'),('GET',CATALOG['A01'].url+'?url=http://localhost'),('GET','https://data-api.ecb.europa.eu.evil.test/service/data/EXR/D.USD.EUR.SP00.A')])
def test_exact_request_allowlist(method,url):
    with pytest.raises(FetchError):validate_request(CATALOG['A19'] if method=='POST' else CATALOG['A01'],method,url,[] if method=='POST' else None)

def test_only_two_bounded_read_post_exceptions():
    for id in ('A19','B09','B03'):
        source=CATALOG[id];validate_request(source,'POST',source.url,source.payload)
    for payload in ([],[{'idType':'ORDER','idValue':'TEST'}],[{'idType':'ID_ISIN','idValue':'TEST','order':'BUY'}],CATALOG['A19'].payload*11):
        with pytest.raises(FetchError):validate_request(CATALOG['A19'],'POST',CATALOG['A19'].url,payload)

def test_dns_private_denied(monkeypatch):
    monkeypatch.setattr('socket.getaddrinfo',lambda *a,**k:[(None,None,None,None,('127.0.0.1',443))])
    with pytest.raises(FetchError):public_dns('api.worldbank.org')

def service(migrated,handler=None,settings=None,clock=None):
    settings=settings or DataSettings(_env_file=None)
    return DataService(create_db_engine(migrated.database_url),settings,http(settings,handler or (lambda request:httpx.Response(200,content=body('sdmx_csv')))),clock or (lambda:NOW))

def test_cache_expiry_decimal_and_mock_not_connection(migrated):
    calls=[];now=[NOW]
    data=service(migrated,lambda request:(calls.append(request) or httpx.Response(200,content=body('sdmx_csv'))),clock=lambda:now[0])
    first=data.query('A01');assert first.observations[0].value==Decimal('1.234567890123456789')
    assert not first.real_connection and not first.usable
    assert data.query('A01').cache_hit and len(calls)==1
    now[0]+=timedelta(days=2);assert not data.query('A01').cache_hit and len(calls)==2
    assert data.quality()['counts']['verified_connections']==0

def test_quota_retry_after_and_circuit(migrated):
    calls=[]
    data=service(migrated,lambda request:(calls.append(request) or httpx.Response(429,headers={'Retry-After':'120'})))
    assert data.query('A01').state=='RATE_LIMITED'
    assert data.query('A01').state=='RATE_LIMITED' and len(calls)==1

def test_credentials_missing_and_public_disabled_no_network(migrated):
    data=service(migrated,lambda request:pytest.fail('No debería conectar'),DataSettings(_env_file=None,data_public_enabled=False))
    assert data.query('A01').state=='DISABLED'
    assert data.query('B01').state=='NO_CREDENTIALS'
    assert data.query('A09').state=='CONFIG_REQUIRED'

def test_timeout_disconnect_invalid_no_fake_data(migrated):
    for error,state in ((httpx.ReadTimeout('SECRET'),'TIMEOUT'),(httpx.ConnectError('SECRET'),'OFFLINE')):
        def handler(request):raise error
        assert service(migrated,handler).query('A02').state==state
    result=service(migrated,lambda request:httpx.Response(200,text='SECRET invalid')).query('A02')
    assert result.state=='INVALID_PAYLOAD' and not result.observations and not result.real_connection

def test_restricted_display_and_storage(migrated):
    data=service(migrated,lambda request:httpx.Response(200,content=body('binance')))
    result=data.query('A14');assert result.state=='RIGHTS_RESTRICTED' and not result.observations
    with Session(data.engine) as session:assert session.get(DataRecord,'cache:A14') is None

def test_statistical_semantics_future_bidask_xml():
    fx=parse(CATALOG['A01'],body('sdmx_csv'),NOW)[0]
    assert fx.data_kind=='fx_reference' and not fx.execution_eligible
    with pytest.raises(ValidationError):fx.model_validate({**fx.model_dump(),'observed_at':NOW+timedelta(days=1)})
    with pytest.raises(ValidationError):parse(CATALOG['A18'],json.dumps({**FIXTURES['coinbase'],'bid':'2','ask':'1'}).encode(),NOW)
    with pytest.raises(ValueError):safe_xml(b'<!DOCTYPE x [<!ENTITY a SYSTEM "file:///private">]><x/>')
    with pytest.raises(ValueError):period_time('2026-01-01T00:00:00')
    assert parse(CATALOG['A14'],body('binance'),NOW)[0].currency=='USDT'
    assert select_equivalent([fx],kind='market_quote',series_id=fx.series_id,feed=fx.feed,period_precision=fx.period_precision,venue=fx.venue,currency=fx.currency,unit=fx.unit,now=NOW) is None

def test_registry_identity_asset_class_and_null_macro(migrated):
    engine=create_db_engine(migrated.database_url)
    with Session(engine) as session,session.begin():
        registry=InstrumentRegistry(session)
        for asset in ('EQUITY','ETF'):
            registry.add(Instrument(id=uuid4(),symbol='TEST_ONLY',venue='TEST',currency='EUR',asset_class=asset))
        registry.add(Instrument(id=uuid4(),symbol='TEST_MACRO',venue='TEST',asset_class='MACRO_SERIES'))
        assert len(registry.list('TEST_ONLY'))==2
        assert len(registry.list(limit=1))==1
    with pytest.raises(ValidationError):Instrument(id=uuid4(),symbol='TEST_ONLY',venue='TEST',currency='US1',asset_class='EQUITY')

def test_quality_does_not_query_or_expose_secrets(client):
    result=client.get('/api/data/quality');assert result.status_code==200
    assert result.json()['counts']['candidate_access_modes']==34
    assert result.json()['counts']['verified_connections']==0
    assert client.get('/api/data/sources/https://evil.test').status_code==404
    assert client.post('/api/orders',json={'mode':'LIVE'}).status_code==403

def test_ingest_reference_is_not_bond_or_broker_and_is_idempotent(migrated):
    rows=parse(CATALOG['A08'],body('treasury'),NOW)+parse(CATALOG['A15'],body('paprika'),NOW)
    engine=create_db_engine(migrated.database_url)
    with Session(engine) as session,session.begin():
        assert ingest(session,rows)==2
        assert ingest(session,rows)==0
        items=InstrumentRegistry(session).list()
        assert {i.asset_class for i in items}=={'MACRO_SERIES','CRYPTO'}
        assert all(not i.bond_terms and not i.provider_capabilities[0].broker_paper and not i.provider_capabilities[0].valuation for i in items)
        assert session.query(InstrumentAlias).count()==2

def test_migration_preserves_existing_payload_and_asset_class(settings):
    from alembic import command
    from alembic.config import Config
    from app.config import ROOT
    from sqlalchemy import text
    config=Config(str(ROOT/'alembic.ini'));command.upgrade(config,'0001_instruments')
    item=Instrument(id=uuid4(),symbol='TEST_ONLY',venue='TEST',currency='EUR',asset_class='ETF')
    engine=create_db_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(text('INSERT INTO instruments (id,symbol,venue,currency,payload) VALUES (:id,:symbol,:venue,:currency,:payload)'),{'id':str(item.id),'symbol':item.symbol,'venue':item.venue,'currency':item.currency,'payload':item.model_dump_json()})
    command.upgrade(config,'head')
    with Session(engine) as session:
        assert InstrumentRegistry(session).list()==[item]
        assert session.get(__import__('app.database',fromlist=['InstrumentRecord']).InstrumentRecord,str(item.id)).asset_class=='ETF'

def test_get_credentials_only_backend_and_posts_strict():
    seen=[];settings=DataSettings(_env_file=None,fred_api_key='TEST_SECRET',bls_api_key='TEST_BLS')
    client=http(settings,lambda request:(seen.append(request) or httpx.Response(200,content=body('fred'))))
    client.fetch(CATALOG['B01']);assert seen[0].method=='GET' and seen[0].url.params['api_key']=='TEST_SECRET'
    assert 'TEST_SECRET' not in repr(settings)
    with pytest.raises(FetchError):validate_request(CATALOG['B03'],'POST',CATALOG['B03'].url,{'seriesid':['TEST'],'order':'BUY'})

def test_sdmx_xml_and_multiplier_not_false_connection():
    xml=b'<StructureSpecificData><DataSet><Series FREQ="M" EER_TYPE="N" EER_BASKET="B" REF_AREA="ES" UNIT_MEASURE="index"><Obs TIME_PERIOD="2026-09" OBS_VALUE="12.34"/></Series></DataSet></StructureSpecificData>'
    assert parse(CATALOG['A07'],xml,NOW)[0].value==Decimal('12.34')
    with pytest.raises(ValueError):parse(CATALOG['A07'],b'<html>not data</html>',NOW)
    assert parse(CATALOG['A05'],b'TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,UNIT_MULT\n2026-09,1.234,index,3\n',NOW)[0].value==Decimal('1234.000')

def test_quota_inside_http_200_not_available():
    with pytest.raises(FetchError) as error:parse(CATALOG['B07'],b'{"Note":"TEST_ONLY quota"}',NOW)
    assert error.value.state=='RATE_LIMITED'

def test_quality_contract_and_rights_revocation(migrated,monkeypatch):
    from app.data_contracts import QualityReport
    data=service(migrated);data.query('A01');report=data.quality()
    QualityReport.model_validate(report)
    with pytest.raises(ValidationError):QualityReport.model_validate({**report,'counts':{**report['counts'],'verified_connections':99}})
    source=CATALOG['A01'];monkeypatch.setitem(CATALOG,'A01',replace(source,rights=source.rights.model_copy(update={'display_allowed':False,'access_allowed':False})))
    assert data.query('A01').state=='RIGHTS_RESTRICTED'
    row=next(r for r in data.quality()['sources'] if r['access_id']=='A01')
    assert not row['usable'] and row['state']=='RIGHTS_RESTRICTED'

def test_bls_read_post_year_range_bounded():
    source=CATALOG['B03']
    for start,end in (('1900','2100'),('2026','2025'),('TEST','2026')):
        with pytest.raises(FetchError):validate_request(source,'POST',source.url,{'seriesid':['CUUR0000SA0'],'startyear':start,'endyear':end})
    assert retry_seconds('Wed, 14 Oct 2026 00:05:00 GMT',NOW)==300
    assert retry_seconds('TEST_ONLY invalid date',NOW)==60

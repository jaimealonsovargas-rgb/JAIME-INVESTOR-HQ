"""Synthetic evidence only. No network, real credentials, or writes to the personal DB."""
from datetime import timedelta
import json
import pytest
from sqlalchemy import insert,select,update
from app.data_identity import fingerprint
from app.dataset_assessment import assess_market
from app.instrument_evidence import common_stock_cover,identity_evidence
from app.sec_http import archive_raw,statement_url
from app.sec_store import SNAPSHOTS,FILINGS
from app.universe_store import UniverseStore,LISTINGS
from app.universe_contracts import parse_catalogue
from app.market_store import BARS,RECEIPTS,JOBS
from test_market_data import market,catalogue,history,drain,protected

CIK='0000000001'
ACC='0000000001-26-000001'


def cover(title='Common stock, $0.01 par value per share',extra='',context='equity'):
    return (f'''<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:dei="http://xbrl.sec.gov/dei/2026">
      <xbrli:context id="equity"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{CIK}</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>2024-12-31</xbrli:endDate></xbrli:period></xbrli:context>
      <xbrli:context id="bond"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{CIK}</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:endDate>2024-12-31</xbrli:endDate></xbrli:period></xbrli:context>
      <dei:EntityCentralIndexKey contextRef="equity">{CIK}</dei:EntityCentralIndexKey>
      <dei:DocumentPeriodEndDate contextRef="equity">2024-12-31</dei:DocumentPeriodEndDate>
      <dei:Security12bTitle contextRef="equity">{title}</dei:Security12bTitle>
      <dei:TradingSymbol contextRef="{context}">TEST</dei:TradingSymbol><dei:SecurityExchangeName contextRef="equity">NASDAQ</dei:SecurityExchangeName>
      {extra}</xbrli:xbrl>''').encode()


def test_cover_uses_class_and_context_not_ticker_alone():
    bond='<dei:Security12bTitle contextRef="bond">3% Notes due 2030</dei:Security12bTitle><dei:TradingSymbol contextRef="bond">TEST</dei:TradingSymbol><dei:SecurityExchangeName contextRef="bond">NASDAQ</dei:SecurityExchangeName>'
    assert common_stock_cover(cover(extra=bond),CIK,'TEST','NASDAQ')['context_id']=='equity'


@pytest.mark.parametrize('raw',[
    cover(title='Preferred stock'),cover(context='bond'),cover().replace(CIK.encode(),b'0000000002'),
    cover().replace(b'http://xbrl.sec.gov/dei/2026',b'http://malicious.example/dei/2026'),
    cover().replace(b'<xbrli:xbrl',b'<!DOCTYPE x [<!ENTITY e "x">]><xbrli:xbrl'),
    cover(extra='<dei:TradingSymbol contextRef="equity">OTHER</dei:TradingSymbol>'),
])
def test_cover_rejects_wrong_class_entity_namespace_context_and_entities(raw):
    with pytest.raises(ValueError):common_stock_cover(raw,CIK,'TEST','NASDAQ')


@pytest.fixture
def reviewed(market,tmp_path):
    market.raw_root=tmp_path/'data/market/raw'
    original=market.http.fetch
    def fetch(kind,params=None):
        raw=original(kind,params)
        if kind=='assets':
            data=json.loads(raw);data[0].update(name='SYNTHETIC TEST ONLY Common Stock',exchange='NASDAQ')
            return json.dumps(data).encode()
        return raw
    market.http.fetch=fetch
    market.http.real=True  # Simulated flag only, not evidence of a real external connection.
    ident=catalogue(market)
    now=market.test_clock[0];stamp=now.isoformat()
    store=UniverseStore(market.data.engine)
    rows=parse_catalogue('SEC',{'fields':['cik','name','ticker','exchange'],'data':[[CIK,'SYNTHETIC TEST ONLY','TEST','NASDAQ']]})
    assert store.claim('sec-test-catalogue','SEC',now)[0]
    store.apply_snapshot('sec-test-catalogue','SEC',rows,'https://www.sec.gov/files/company_tickers_exchange.json','a'*64,now)
    sec_listing=store.search(provider='SEC')['items'][0]['id']
    secroot=tmp_path/'data/sec'
    digest=archive_raw(secroot/'statements/raw',cover(),extension='.xml.gz')
    receipt=dict(cik=CIK,accession=ACC,primary='test-20241231.htm',received_at=stamp,
        instance=dict(kind='instance',url=statement_url(CIK,ACC,'test-20241231.htm','instance'),sha256=digest))
    folder=secroot/'statements'/CIK;folder.mkdir(parents=True)
    (folder/(ACC+'.json')).write_text(json.dumps(receipt),encoding='utf-8')
    with market.data.engine.begin() as c:
        c.execute(insert(SNAPSHOTS).values(id='s'*64,cik=CIK,kind='submissions',payload_hash='b'*64,parser_version='test-only',source='https://data.sec.gov/submissions/CIK'+CIK+'.json',first_received_at=stamp,metadata={}))
        c.execute(insert(FILINGS).values(snapshot_id='s'*64,accession=ACC,filed='2025-01-30',form='10-K',payload=dict(primary_document=receipt['primary'],form='10-K',report_date='2024-12-31',filed='2025-01-30')))
        payloads={r['id']:r['payload'] for r in c.execute(select(LISTINGS)).mappings()}
    pilot=dict(version='test-only',reviewed_at=stamp,items=[dict(cik=CIK,symbol='TEST',sec_listing_id=sec_listing,market_listing_id=ident,
        sec_identity_hash=fingerprint(payloads[sec_listing]),market_identity_hash=fingerprint(payloads[ident]),filing=receipt)])
    history(market,ident);assert drain(market,'history-test')['state']=='SUCCEEDED'
    return market,ident,pilot,secroot


def run(reviewed,**kw):
    market,ident,pilot,_=reviewed
    return assess_market(market,ident,pilot=pilot,**kw)


def states(result):return {c['code']:c['state'] for c in result['checks']}


def test_documented_identity_does_not_promote_backtest_or_modify_database(reviewed):
    market,ident,pilot,_=reviewed
    before=protected(market.data.engine)
    result=run(reviewed)
    assert result['identity']['state']=='DOCUMENTED'
    assert result['identity']['native_currency'] is None
    assert result['dataset']['bars']==4 and result['dataset']['missing_sessions']==[]
    assert result['research_state']=='EXPLORATORY_ONLY' and result['backtest_state']=='BLOCKED'
    assert states(result)['MINIMUM_HISTORY']=='BLOCKED'
    assert states(result)['ORIGINAL_INTEGRITY']=='PASS'
    assert run(reviewed)['manifest_id']==result['manifest_id']
    assert protected(market.data.engine)==before
    sec=assess_market(market,pilot['items'][0]['sec_listing_id'],pilot=pilot)
    assert sec['dataset']==result['dataset']


def test_identity_not_visible_before_review_and_source_cutoff(reviewed):
    market,_,pilot,_=reviewed
    from datetime import datetime
    result=run(reviewed,cutoff=datetime.fromisoformat(pilot['reviewed_at'])-timedelta(seconds=1))
    assert result['identity']['state']=='UNREVIEWED' and result['identity']['cik'] is None
    assert result['dataset'] is None


def test_changed_provider_identity_revokes_link_and_eligibility(reviewed):
    market,ident,_,_=reviewed
    with market.data.engine.begin() as c:
        row=c.scalar(select(LISTINGS.c.payload).where(LISTINGS.c.id==ident))
        c.execute(update(LISTINGS).where(LISTINGS.c.id==ident).values(payload={**row,'name':'Another issuer Common Stock'}))
    result=run(reviewed)
    assert result['identity']['state']=='REVIEW_REQUIRED'
    assert states(result)['DATASET_IDENTITY']=='BLOCKED'


def test_conflicting_catalogue_candidate_revokes_link(reviewed):
    market,ident,_,_=reviewed
    with market.data.engine.begin() as c:
        row=dict(c.execute(select(LISTINGS).where(LISTINGS.c.id==ident)).mappings().one())
        row.update(id='9'*64,provider_key='another-asset')
        c.execute(insert(LISTINGS).values(**row))
    assert run(reviewed)['identity']['state']=='REVIEW_REQUIRED'


def test_missing_or_changed_original_is_not_accepted(reviewed):
    market,_,_,_=reviewed
    with market.data.engine.connect() as c:
        digest=c.scalar(select(RECEIPTS.c.payload_hash).where(RECEIPTS.c.kind=='bars'))
    (market.raw_root/(digest+'.json.gz')).write_bytes(b'corrupted synthetic archive')
    assert states(run(reviewed))['ORIGINAL_INTEGRITY']=='BLOCKED'


def test_tampered_normalized_bar_and_duplicate_daily_grain(reviewed):
    market,_,_,_=reviewed
    with market.data.engine.begin() as c:
        row=c.scalar(select(BARS.c.payload).limit(1));other={**row,'timestamp':row['timestamp'].replace('05:00','06:00')}
        c.execute(insert(BARS).values(job_id='history-test',timestamp=other['timestamp'],payload=other))
    result=run(reviewed)
    assert states(result)['ORIGINAL_INTEGRITY']=='BLOCKED'
    assert states(result)['DAILY_GRAIN']=='BLOCKED'
    assert states(result)['BAR_VALIDITY']=='BLOCKED'


def test_calendar_hole_is_explicit_never_filled(reviewed):
    market,_,_,_=reviewed
    with market.data.engine.begin() as c:
        c.execute(BARS.delete().where(BARS.c.timestamp.like('2024-01-03%')))
    result=run(reviewed)
    # Integrity failure prevents treating a separately stored calendar as verified.
    assert states(result)['SESSION_COVERAGE']=='BLOCKED'
    assert result['dataset']['bars']==3


def test_pending_import_and_other_adjustments_are_not_certified(reviewed):
    market,_,_,_=reviewed
    assert run(reviewed,adjustment='all')['dataset'] is None
    with market.data.engine.begin() as c:c.execute(update(JOBS).where(JOBS.c.id=='history-test').values(state='RUNNING'))
    assert states(run(reviewed))['IMPORT_COMPLETE']=='BLOCKED'


def test_changed_filing_hash_or_class_revokes_identity(reviewed):
    market,ident,pilot,root=reviewed
    spec=pilot['items'][0]
    (root/'statements/raw'/(spec['filing']['instance']['sha256']+'.xml.gz')).write_bytes(b'broken')
    with market.data.engine.connect() as c:
        result=identity_evidence(c,root,ident,market.data.clock(),pilot)
    assert result['state']=='REVIEW_REQUIRED'


def test_synthetic_connection_and_changed_feed_are_blocked(reviewed):
    market,_,_,_=reviewed
    with market.data.engine.begin() as c:
        row=c.execute(select(RECEIPTS).where(RECEIPTS.c.kind=='bars')).mappings().first()
        c.execute(update(RECEIPTS).where(RECEIPTS.c.id==row['id']).values(payload={**row['payload'],'real_connection':False}))
    assert states(run(reviewed))['ORIGINAL_INTEGRITY']=='BLOCKED'


def test_same_cutoff_with_another_timezone_has_identical_result(reviewed):
    from datetime import timezone
    market,_,_,_=reviewed
    cutoff=market.data.clock()
    assert run(reviewed,cutoff=cutoff)==run(reviewed,cutoff=cutoff.astimezone(timezone(timedelta(hours=-5))))


def test_real_source_session_gap_is_reported_without_filling(reviewed):
    market,ident,_,_=reviewed
    original=market.http.fetch
    def fetch(kind,params=None):
        raw=original(kind,params)
        if kind=='bars':
            body=json.loads(raw);body['bars']=[b for b in body['bars'] if '2024-01-03' not in b['t']]
            return json.dumps(body).encode()
        return raw
    market.http.fetch=fetch
    history(market,ident,key='history-hole');assert drain(market,'history-hole')['state']=='SUCCEEDED'
    result=run(reviewed)
    assert states(result)['ORIGINAL_INTEGRITY']=='PASS'
    assert states(result)['SESSION_COVERAGE']=='BLOCKED'
    assert result['dataset']['missing_sessions']==['2024-01-03']
    assert result['dataset']['bars']==3


@pytest.mark.parametrize('param,value',[('feed','sip'),('asof','2024-01-01'),('start','2024-01-02T12:00:00-05:00'),('page_token','invented')])
def test_changed_request_parameters_fail_original_verification(reviewed,param,value):
    market,_,_,_=reviewed
    with market.data.engine.begin() as c:
        row=c.execute(select(RECEIPTS).where(RECEIPTS.c.kind=='bars').order_by(RECEIPTS.c.received_at).limit(1)).mappings().one()
        c.execute(update(RECEIPTS).where(RECEIPTS.c.id==row['id']).values(params={**row['params'],param:value}))
    assert states(run(reviewed))['ORIGINAL_INTEGRITY']=='BLOCKED'


def test_missing_actions_page_and_disabled_sources_do_not_pass(reviewed):
    market,_,_,_=reviewed
    with market.data.engine.begin() as c:c.execute(RECEIPTS.delete().where(RECEIPTS.c.kind=='corporate_actions'))
    assert states(run(reviewed))['ORIGINAL_INTEGRITY']=='BLOCKED'
    market.data.settings.data_disabled_sources='A09'
    assert run(reviewed)['identity']['state']=='UNREVIEWED'
    market.data.settings.data_public_enabled=False
    with pytest.raises(PermissionError):run(reviewed)

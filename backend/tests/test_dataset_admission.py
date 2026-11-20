from copy import deepcopy
import pytest
from app.admission_fixture import fixture_bundle
from app.admission_contracts import candidate_hash, fingerprint
from app.dataset_evidence import evidence_record
from app.dataset_admission import evaluate


def seal(c,e):
    e['records']=[evidence_record(r['kind'],candidate_hash(c),r['payload'],r['published_at']) for r in e['records']]


def record(e,kind): return next(r for r in e['records'] if r['kind']==kind)
def gate(m,code): return next(r['state'] for r in m['checks'] if r['code']==code)


def test_positive_is_only_engineering_and_manifest_has_no_prices():
    c,e=fixture_bundle(); m=evaluate(c,e)
    assert m['engineering_state']=='ENGINEERING_READY'
    assert m['readiness']=={'research':'ENGINEERING_ONLY','backtest':'ENGINEERING_ONLY','execution_sim':'BLOCKED'}
    assert m['manifest_id']==fingerprint({k:v for k,v in m.items() if k!='manifest_id'})
    assert m['input_scope']['universe_hash']==c['universe_hash']
    assert m['input_scope']['identity_hash']==c['identity_hash']
    assert m['input_scope']['adjustment']==c['adjustment']
    assert 'bars' not in str(m) and '1000' not in str(m)


@pytest.mark.parametrize('mutation,expected',[
    ('gap','calendar'),('duplicate','ohlcv_grain'),('ohlc','ohlcv_grain'),
    ('leak','knowledge_time'),('identitygap','identity'),('currency','identity'),
    ('actions','corporate_actions'),('expost','universe'),('fake','rights'),
    ('wrongsubject','evidence_integrity'),('future','evidence_integrity'),('real','domain')])
def test_fail_closed(mutation,expected):
    c,e=fixture_bundle()
    if mutation=='gap': c['bars'].pop(20)
    if mutation=='duplicate': c['bars'][20]=deepcopy(c['bars'][19])
    if mutation=='ohlc': c['bars'][0]['high']='1'
    if mutation=='leak': record(e,'knowledge')['payload']['observations'][0]['available_at']='2023-01-02T15:00:00+00:00'
    if mutation=='identitygap': record(e,'identity')['payload']['intervals'][0]['start']='2023-01-03'
    if mutation=='currency': record(e,'identity')['payload']['intervals'][0]['currency']='EUR'
    if mutation=='actions': record(e,'actions')['payload']['events']=[{'type':'SPLIT'}]
    if mutation=='expost': record(e,'universe')['payload']['selected_at']='2023-02-01T00:00:00+00:00'
    if mutation=='fake': record(e,'rights')['payload']={'approved':True}
    if mutation=='real': c['domain']='MARKET_DATA'; c['provider']='IBKR_TWS'
    seal(c,e)
    if mutation=='wrongsubject': e['records'][0]['subject_hash']='0'*64
    if mutation=='future':
        r=e['records'][0]; e['records'][0]=evidence_record(r['kind'],candidate_hash(c),r['payload'],'2030-01-01T00:00:00+00:00')
    m=evaluate(c,e)
    assert gate(m,expected)=='BLOCKED'
    assert m['readiness']['backtest']=='BLOCKED'


def test_timezone_hash_and_cutoff_are_canonical():
    c,e=fixture_bundle(); original=evaluate(c,e)
    c['cutoff']='2024-02-01T01:00:00+01:00'
    c['sources'][0]['received_at']='2024-02-01T01:00:00+01:00'
    assert evaluate(c,e)==original


def test_bad_contract_has_no_input_echo():
    assert evaluate({'secret':'DO_NOT_ECHO'})['candidate_hash'] is None
    assert 'DO_NOT_ECHO' not in str(evaluate({'secret':'DO_NOT_ECHO'}))


def test_extreme_valid_iso_period_blocks_without_date_overflow():
    c,_=fixture_bundle(); c['start']='9999-01-01'; c['end']='9999-12-31'
    m=evaluate(c)
    assert gate(m,'candidate_contract')=='BLOCKED'
    assert m['readiness']['backtest']=='BLOCKED'


def test_missing_evidence_and_sources_block():
    c,e=fixture_bundle(); c['sources']=[]; seal(c,e)
    assert gate(evaluate(c,e),'source_integrity')=='BLOCKED'
    assert evaluate(c)['engineering_state']=='BLOCKED'


def test_unknown_native_currency_is_specific_gate():
    c,e=fixture_bundle(); c['currency']=None; seal(c,e)
    m=evaluate(c,e)
    assert m['candidate_hash'] is not None
    assert gate(m,'native_currency')=='BLOCKED'


def test_explicit_calendar_preserves_dst_and_next_open():
    c,e=fixture_bundle()
    sessions=record(e,'calendar')['payload']['sessions']
    assert any(s['open'].endswith('-05:00') for s in sessions)
    assert any(s['open'].endswith('-04:00') for s in sessions)
    sessions[10]['next_open']=sessions[10]['close']; seal(c,e)
    assert gate(evaluate(c,e),'calendar')=='BLOCKED'


@pytest.mark.parametrize('value',['1e999999999','NaN','Infinity','9'*200])
def test_decimal_bombs_rejected_without_echo(value):
    c,e=fixture_bundle(); c['bars'][0]['close']=value
    assert evaluate(c,e)['candidate_hash'] is None


def test_untrusted_market_fixture_never_promotes():
    c,e=fixture_bundle(); c.update(domain='MARKET_DATA',provider='ALPACA',listing_id='ALPACA:1',symbol='AAA',venue='XNYS')
    c['sources'][0]['id']='ALPACA:SOURCE'; seal(c,e)
    m=evaluate(c,e)
    assert gate(m,'domain')=='PASS'
    assert gate(m,'evidence_integrity')=='BLOCKED'
    assert gate(m,'rights')=='BLOCKED'
    assert m['readiness']['research']=='BLOCKED'


def test_nested_evidence_bomb_and_unknown_keys_fail_closed():
    c,e=fixture_bundle()
    r=record(e,'rights'); r['payload']={'approved':'x'*10000}; seal(c,e)
    assert gate(evaluate(c,e),'evidence_integrity')=='BLOCKED'
    c['rights_approved']=True
    assert evaluate(c,e)['candidate_hash'] is None


def test_calendar_shifted_year_blocks_even_with_concordant_knowledge():
    c,e=fixture_bundle()
    for s in record(e,'calendar')['payload']['sessions']:
        for k in ('open','close','next_open'): s[k]=s[k].replace('2023-','2022-')
    for o in record(e,'knowledge')['payload']['observations']:
        o['available_at']=o['available_at'].replace('2023-','2022-')
    seal(c,e)
    assert gate(evaluate(c,e),'calendar')=='BLOCKED'


def test_historical_alias_events_are_unsupported():
    c,e=fixture_bundle(); record(e,'identity')['payload']['intervals'][0]['aliases']=['TEST_OLD']; seal(c,e)
    assert gate(evaluate(c,e),'identity')=='BLOCKED'


def test_trusted_registry_rights_validator_is_engineering_test_only(monkeypatch):
    # Isolated trust-anchor injection, never a production rights assertion.
    from app import dataset_evidence
    c,e=fixture_bundle(); c.update(domain='MARKET_DATA',provider='ALPACA',listing_id='ALPACA:1',symbol='AAA',venue='XNYS')
    c['sources'][0]['id']='ALPACA:SOURCE'
    p=record(e,'identity')['payload']['intervals'][0]
    p.update({k:c[k] for k in ('listing_id','symbol','venue')})
    record(e,'calendar')['payload']['venue']=c['venue']
    u=record(e,'universe')['payload']; u['inclusions']=[c['listing_id']]; u['membership_coverage']['listing_id']=c['listing_id']
    record(e,'rights')['payload']={**{k:c[k] for k in ('start','end','provider','feed','listing_id')},'account_scope_hash':'a'*64,'uses':['LOCAL_RESEARCH','BACKTEST','ARCHIVE'],'retention':{'days':365,'review':'FINITE_REVIEWED'},'cost_eur':'0','redistribution':'PROHIBITED','valid_from':'2022-01-01T00:00:00+00:00','valid_to':'2025-01-01T00:00:00+00:00'}
    seal(c,e)
    monkeypatch.setattr(dataset_evidence,'REAL_EVIDENCE_REGISTRY',{r['hash']:r for r in e['records']})
    m=evaluate(c,e)
    assert m['readiness']['research']=='RESEARCH_READY'
    assert m['readiness']['backtest']=='BACKTEST_READY'
    # Production call path resolves reviewed entries by subject without a CLI override.
    assert evaluate(c)==m
    record(e,'rights')['payload']['cost_eur']='1'; seal(c,e)
    monkeypatch.setattr(dataset_evidence,'REAL_EVIDENCE_REGISTRY',{r['hash']:r for r in e['records']})
    assert gate(evaluate(c,e),'rights')=='BLOCKED'


@pytest.mark.parametrize('days,received,expected',[(30,'2024-01-15T00:00:00+00:00','PASS'),(1,'2024-01-15T00:00:00+00:00','BLOCKED'),(True,'2024-02-01T00:00:00+00:00','BLOCKED')])
def test_retention_uses_reviewed_days_and_actual_receipt(monkeypatch,days,received,expected):
    from app import dataset_evidence
    c,e=fixture_bundle()
    c.update(domain='MARKET_DATA',provider='ALPACA',listing_id='ALPACA:1',symbol='AAA',venue='XNYS')
    c['sources'][0].update(id='ALPACA:SOURCE',received_at=received)
    record(e,'rights')['payload']={**{k:c[k] for k in ('start','end','provider','feed','listing_id')},
        'account_scope_hash':'a'*64,'uses':['LOCAL_RESEARCH','BACKTEST','ARCHIVE'],
        'retention':{'days':days,'review':'FINITE_REVIEWED'},'cost_eur':'0','redistribution':'PROHIBITED',
        'valid_from':'2024-01-01T00:00:00+00:00','valid_to':'2025-01-01T00:00:00+00:00'}
    seal(c,e)
    monkeypatch.setattr(dataset_evidence,'REAL_EVIDENCE_REGISTRY',{r['hash']:r for r in e['records']})
    assert gate(evaluate(c),'rights')==expected

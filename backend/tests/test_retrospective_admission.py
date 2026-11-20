from copy import deepcopy
from datetime import datetime,timedelta
import json
import pytest
from app.admission_fixture import fixture_bundle
from app.admission_contracts import fingerprint
from app import dataset_evidence
from app.dataset_admission import evaluate
from app.b32_review import PROTOCOL


def retro_bundle(monkeypatch):
    c,e=fixture_bundle()
    c.update(domain='MARKET_DATA',provider='ALPACA',symbol='UNIT',venue='NYSE',listing_id='UNIT:LISTING',feed='iex',adjustment='raw')
    c['sources'][0]['id']='UNIT:SOURCE'
    payloads={r['kind']:r['payload'] for r in e['records']}
    payloads['identity']['intervals'][0].update({k:c[k] for k in ('symbol','venue','listing_id')})
    payloads['calendar']['venue']='NYSE'
    payloads['semantics'].update(feed='iex',adjustment='raw',price_basis='IEX_DAILY_OPEN_PROXY',execution_claim=False,open_close_basis='ELIGIBLE_REGULAR_SESSION_TRADES')
    payloads['knowledge']=dict(basis='CURRENT_REVISED_HISTORY',signal_information='PRIOR_SESSION_CLOSE_ASSUMED',point_in_time_claim=False,observations=[])
    payloads['universe'].update(rule='FIXED_EX_POST_SINGLE_ASSET',selected_at='2024-01-31T00:00:00+00:00',inclusions=[c['listing_id']],survivorship_bias_acknowledged=True,oos_reserved=False)
    start='2024-01-31T00:00:00+00:00'; end='2024-03-01T00:00:00+00:00'
    payloads['rights']=dict(start=c['start'],end=c['end'],provider='ALPACA',feed='iex',listing_id=c['listing_id'],account_scope_hash='a'*64,scope='PERSONAL_LOCAL_NONCOMMERCIAL',uses=['LOCAL_RESEARCH','BACKTEST','ARCHIVE'],retention=dict(provider_period='UNSPECIFIED',internal_review_days=30,review_expires_at=end),valid_from=start,valid_to=end,cost_eur='0',redistribution='PROHIBITED')
    records=[]
    for kind,p in payloads.items():
        body=dict(id='UNIT:'+kind,kind=kind,authority='UNIT_REVIEW',subject_hash=fingerprint(c),published_at=c['cutoff'],payload=p)
        records.append(dict(body,hash=fingerprint(body)))
    e['records']=records
    monkeypatch.setattr(dataset_evidence,'trusted_registry',lambda:{r['hash']:r for r in records})
    return c,e


def reseal(c,e):
    for r in e['records']:
        r['subject_hash']=fingerprint(c)
        r['hash']=fingerprint({k:v for k,v in r.items() if k!='hash'})


def test_retrospective_does_not_promote_strict_pit(monkeypatch):
    c,e=retro_bundle(monkeypatch)
    m=evaluate(c,e,protocol=PROTOCOL)
    assert m['readiness']['backtest']=='BACKTEST_READY_EXPLORATORY'
    assert m['readiness']['execution_sim']=='BLOCKED'
    assert not m['scope']['point_in_time_claim'] and not m['scope']['oos_reserved']
    assert evaluate(c,e)['readiness']['backtest']=='BLOCKED'


@pytest.mark.parametrize('case',['missing_bar','paid','redistribution','future_selection','pit_claim','expiry','fake_authority','raw_tamper','unknown_protocol','synthetic'])
def test_retrospective_gates_still_fail_closed(monkeypatch,case):
    c,e=retro_bundle(monkeypatch)
    p={r['kind']:r['payload'] for r in e['records']}
    if case=='missing_bar': c['bars'].pop()
    if case=='paid': p['rights']['cost_eur']='1'
    if case=='redistribution': p['rights']['redistribution']='ALLOWED'
    if case=='future_selection': p['universe']['selected_at']='2025-01-01T00:00:00+00:00'
    if case=='pit_claim': p['knowledge']['point_in_time_claim']=True
    if case=='expiry': p['rights']['valid_to']='2024-01-30T00:00:00+00:00'
    if case=='raw_tamper': c['source_errors']=['ORIGINAL_INTEGRITY_FAILED']
    if case=='synthetic': c['domain']='SYNTHETIC_TEST'; c['provider']='SYNTHETIC_TEST'
    reseal(c,e)
    if case=='fake_authority': monkeypatch.setattr(dataset_evidence,'trusted_registry',lambda:{})
    if case=='unknown_protocol':
        with pytest.raises(ValueError): evaluate(c,e,protocol='anything')
    else: assert evaluate(c,e,protocol=PROTOCOL)['readiness']['backtest']=='BLOCKED'


def test_private_review_rejects_changed_file(tmp_path,monkeypatch):
    from app import b32_review
    f=tmp_path/'review.json';f.write_text('{}')
    monkeypatch.setattr(b32_review,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='INTEGRITY'): b32_review.checked_file('review.json','0'*64)
    with pytest.raises(ValueError): b32_review.checked_file('../review.json','0'*64)


def test_unreviewed_user_assertion_does_not_fill_currency(monkeypatch):
    from app import b32_review
    c,_=fixture_bundle()
    monkeypatch.setattr(b32_review,'reviewed_bundle',lambda:dict(source_candidate_hash='0'*64))
    with pytest.raises(ValueError,match='CANDIDATE_MISMATCH'): b32_review.apply_identity_review(c)

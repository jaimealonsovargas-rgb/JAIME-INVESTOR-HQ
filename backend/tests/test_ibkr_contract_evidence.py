"""Synthetic contract evidence; no TWS, network or personal database."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json

import pytest
from sqlalchemy import select, update
from app.data_identity import fingerprint
from app.instrument_evidence import identity_evidence
from app.sec_http import archive_raw
from app.universe_store import LISTINGS
from test_dataset_assessment import reviewed, run, states
from test_market_data import market, protected


def save(root, review, report):
    raw = json.dumps(report).encode()
    review['report_sha256'] = archive_raw(root/'ibkr/contracts/raw', raw)


@pytest.fixture
def linked(reviewed):
    service, ident, pilot, secroot = reviewed
    with service.data.engine.connect() as c:
        identity = identity_evidence(c, secroot, ident, service.data.clock(), pilot)
    for symbol in ('SECOND', 'THIRD'):
        pilot['items'].append({**pilot['items'][0], 'symbol':symbol})
    stamp = service.data.clock().isoformat()
    review = dict(version='pilot-ibkr-review-v1', reviewed_at=stamp, pilot_sha256=fingerprint(pilot), bindings=[])
    report = dict(version='ibkr-readonly-probe-v1', state='CONNECTED_READ_ONLY_PROBE', checked_at=stamp,
        server_time_utc=stamp, connected=True, paper_account_matched=True, disconnected_after_probe=True,
        orders_enabled=False, market_data_requested=False, read_only_basis='TWS_UI_CONFIRMED_BY_USER',
        sent_message_ids=[71,49,9,9,9], errors=[], contracts=[])
    for i, spec in enumerate(pilot['items']):
        contract = dict(conId=i+1, symbol=spec['symbol'], secType='STK', currency='USD', exchange='SMART',
            primaryExchange='NASDAQ', localSymbol=spec['symbol'], tradingClass='NMS', longName='SYNTHETIC ONLY')
        review['bindings'].append(dict(symbol=spec['symbol'], identity_spec_sha256=fingerprint(spec),
            instrument_id=identity['instrument_id'], contract_sha256=fingerprint(contract), con_id=i+1))
        report['contracts'].append(dict(symbol=spec['symbol'], candidates=[contract], completed=True,
            error_codes=[], state='CURRENT_CONTRACT_CANDIDATE'))
    save(secroot.parent, review, report)
    return reviewed, review, report


def test_current_currency_and_provenance_do_not_certify_history_or_mutate_database(linked):
    fixture, review, _ = linked
    before = protected(fixture[0].data.engine)
    result = run(fixture, contract_review=review)
    identity = result['identity']
    assert identity['native_currency'] == 'USD'
    assert identity['current_contract']['con_id'] == 1
    assert identity['current_contract']['primary_exchange'] == 'NASDAQ'
    assert identity['current_contract']['routing_exchange'] == 'SMART'
    assert identity['current_contract']['report_sha256'] == review['report_sha256']
    assert identity['historical_identity'] is False
    assert states(result)['NATIVE_CURRENCY'] == 'PASS'
    assert states(result)['HISTORICAL_IDENTITY'] == 'BLOCKED'
    assert result['backtest_state'] == 'BLOCKED' and result['execution_ready'] is False
    assert result == run(fixture, contract_review=review)
    assert before == protected(fixture[0].data.engine)


def test_cutoff_before_review_cannot_inherit_later_currency(linked):
    fixture, review, _ = linked
    cutoff = fixture[0].data.clock()-timedelta(microseconds=1)
    result = run(fixture, cutoff=cutoff, contract_review=review)
    assert result['identity']['state'] == 'DOCUMENTED'
    assert result['identity']['native_currency'] is None
    assert result['identity']['current_contract'] is None


@pytest.mark.parametrize('mode', ['missing','tampered','bad-digest','wrong-instrument','changed-review','naive-time'])
def test_unverifiable_contract_revokes_currency_but_preserves_sec_link(linked, mode):
    fixture, review, _ = linked
    path = fixture[3].parent/'ibkr/contracts/raw'/(review['report_sha256']+'.json.gz')
    if mode == 'missing': path.unlink()
    elif mode == 'tampered': path.write_bytes(b'broken')
    elif mode == 'bad-digest': review['report_sha256'] = '../outside'
    elif mode == 'wrong-instrument': review['bindings'][0]['instrument_id'] = 'f'*64
    elif mode == 'changed-review': review['pilot_sha256'] = 'f'*64
    else: review['reviewed_at'] = '2026-10-28T15:00:00'
    result = run(fixture, contract_review=review)
    assert result['identity']['state'] == 'DOCUMENTED'
    assert result['identity']['current_contract'] is None
    assert states(result)['NATIVE_CURRENCY'] == 'BLOCKED'


@pytest.mark.parametrize('field,value', [('currency','EUR'),('primaryExchange','SMART'),('secType','OPT'),
    ('symbol','OTHER'),('localSymbol','OTHER'),('conId',True),('tradingClass','OTHER')])
def test_wrong_contract_fields_fail_even_with_matching_hash(linked, field, value):
    fixture, review, report = linked
    contract = report['contracts'][0]['candidates'][0]
    contract[field] = value
    review['bindings'][0]['contract_sha256'] = fingerprint(contract)
    save(fixture[3].parent, review, report)
    assert run(fixture, contract_review=review)['identity']['native_currency'] is None


@pytest.mark.parametrize('mode',['ambiguous','incomplete','error','order-message','duplicate-symbol','future-observation','class-pin'])
def test_incomplete_ambiguous_or_unreviewed_bundle_is_rejected(linked, mode):
    fixture, review, report = linked
    item = report['contracts'][0]
    if mode == 'ambiguous': item['candidates'].append(deepcopy(item['candidates'][0]))
    elif mode == 'incomplete': item['completed'] = False
    elif mode == 'error': report['errors'].append(dict(code=200))
    elif mode == 'order-message': report['sent_message_ids'].append(3)
    elif mode == 'duplicate-symbol': report['contracts'][1]['symbol'] = item['symbol']
    elif mode == 'future-observation': report['server_time_utc'] = '2027-01-01T00:00:00Z'
    else: review['bindings'][0]['identity_spec_sha256'] = 'f'*64
    save(fixture[3].parent, review, report)
    assert run(fixture, contract_review=review)['identity']['native_currency'] is None


def test_changed_alpaca_identity_also_withdraws_contract_binding(linked):
    fixture, review, _ = linked
    service, ident, _, _ = fixture
    with service.data.engine.begin() as c:
        payload = c.scalar(select(LISTINGS.c.payload).where(LISTINGS.c.id==ident))
        c.execute(update(LISTINGS).where(LISTINGS.c.id==ident).values(payload={**payload,'name':'Different issuer'}))
    result = run(fixture, contract_review=review)
    assert result['identity']['state'] == 'REVIEW_REQUIRED'
    assert result['identity']['current_contract'] is None


def test_archiving_identical_evidence_is_idempotent(linked):
    fixture, review, report = linked
    root = fixture[3].parent
    path = root/'ibkr/contracts/raw'/(review['report_sha256']+'.json.gz')
    before = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    save(root, review, report)
    assert before == (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())

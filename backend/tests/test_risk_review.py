"""B5 risk and cycle acceptance on synthetic, isolated account and market evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib

import pytest
from pydantic import ValidationError

from app.cycle_service import CYCLES, CycleService
from app.dataset_manifests import canonical
from app.quant_store import digest
from app.risk_contracts import RiskInputs
from app.risk_engine import POLICY_HASH, assess
from app.risk_review import Binding, RiskReview
from test_cycles import count, cycles, drain_cycle, request_for
from test_sec_financials import service


NOW = datetime(2026, 11, 20, 10, tzinfo=timezone.utc)
END = NOW + timedelta(hours=2)


def packet(at=NOW):
    return dict(version='paper-risk-inputs-v1', dossier_id='a'*64,
        account=dict(domain='ALPACA_PAPER', account_ref='b'*64, snapshot_ref='c'*64, currency='USD',
            as_of=at.isoformat(), reconciled=True, complete=True, kill_switch=False, cash='10000',
            high_water_equity='10000', session_open_equity='10000', turnover_today='0', open_orders=0),
        instruments=[dict(listing_id='example', issuer='issuer', sector='industry', factor='factor',
            currency='USD', eligible=True, market_open=True, quote_ref='d'*64, quote_at=at.isoformat(),
            bid='9.99', ask='10', liquidity_ref='e'*64, liquidity_at=at.isoformat(), average_daily_shares='100000',
            shares=0, pending_buy_shares=0, pending_buy_cash='0', pending_sell_shares=0)],
        proposals=[dict(candidate_id='s', listing_id='example', side='BUY', quantity=10, committee_ref='f'*64,
            committee_approved=True, approved_at=(at-timedelta(seconds=10)).isoformat(),
            expires_at=(at+timedelta(minutes=1)).isoformat(),
            downside=dict(evidence_ref='1'*64,invalidation='9.7',stressed_exit='9.5'))])


def evaluate(raw, at=NOW, end=END):
    return assess(RiskInputs.model_validate(raw), at, end)


def test_purchase_is_reproducible_time_limited_and_never_changes_inputs():
    raw = packet()
    prior = deepcopy(raw)
    decision, = evaluate(raw)
    assert decision['decision']=='BUY' and not decision['veto']
    assert decision['notional_with_buffer']=='100.200' and decision['remaining_cash_after_reservations']=='9899.800'
    assert datetime.fromisoformat(decision['expires_at']) == NOW+timedelta(seconds=30)
    assert evaluate(raw)==[decision] and raw==prior


@pytest.mark.parametrize(('target','overrides','reason'), [
    ('account', {'kill_switch':True}, 'KILL_SWITCH'),
    ('account', {'complete':False}, 'ACCOUNT_UNRECONCILED_OR_INCOMPLETE'),
    ('account', {'reconciled':False}, 'ACCOUNT_UNRECONCILED_OR_INCOMPLETE'),
    ('account', {'as_of':NOW-timedelta(seconds=60)}, 'ACCOUNT_STALE_OR_FUTURE'),
    ('account', {'as_of':NOW+timedelta(seconds=1)}, 'ACCOUNT_STALE_OR_FUTURE'),
    ('account', {'high_water_equity':'12000'}, 'LOSS_OR_DRAWDOWN_LIMIT'),
    ('account', {'high_water_equity':'11000','session_open_equity':'11000'}, 'LOSS_OR_DRAWDOWN_LIMIT'),
    ('account', {'high_water_equity':'9900'}, 'INCONSISTENT_ACCOUNT_EQUITY'),
    ('account', {'turnover_today':'2400'}, 'ORDER_COUNT_OR_TURNOVER_LIMIT'),
    ('instrument', {'quote_at':NOW-timedelta(seconds=30)}, 'QUOTE_STALE_OR_FUTURE'),
    ('instrument', {'quote_at':NOW+timedelta(seconds=1)}, 'QUOTE_STALE_OR_FUTURE'),
    ('instrument', {'liquidity_at':NOW-timedelta(days=7)}, 'LIQUIDITY_STALE_OR_FUTURE'),
    ('instrument', {'average_daily_shares':'1999'}, 'SPREAD_OR_LIQUIDITY_LIMIT'),
    ('instrument', {'bid':'9'}, 'SPREAD_OR_LIQUIDITY_LIMIT'),
    ('instrument', {'market_open':False}, 'INSTRUMENT_OR_SESSION_INELIGIBLE'),
    ('instrument', {'eligible':False}, 'INSTRUMENT_OR_SESSION_INELIGIBLE'),
    ('instrument', {'sector':'UNKNOWN'}, 'EXPOSURE_CLASSIFICATION_MISSING'),
    ('proposal', {'quantity':50}, 'ORDER_SIZE_LIMIT'),
    ('proposal', {'committee_approved':False}, 'COMMITTEE_APPROVAL_MISSING'),
    ('proposal', {'expires_at':NOW}, 'PROPOSAL_STALE_OR_FUTURE'),
    ('proposal', {'approved_at':NOW+timedelta(seconds=1)}, 'PROPOSAL_STALE_OR_FUTURE'),
])
def test_policy_denies_with_a_reason(target,overrides,reason):
    raw=packet()
    {'account':raw['account'],'instrument':raw['instruments'][0],'proposal':raw['proposals'][0]}[target].update(overrides)
    result, = evaluate(raw)
    assert result['veto'] and result['decision']=='HOLD' and reason in result['reasons']


@pytest.mark.parametrize(('target','overrides'), [
    ('account', {'domain':'LIVE'}), ('account', {'domain':'MASTER'}), ('account', {'cash':100.01}),
    ('account', {'cash':'NaN'}), ('account', {'cash':'-1'}), ('account', {'high_water_equity':'0'}),
    ('account', {'open_orders':1}), ('account', {'cash':'10000.123456789'}),
    ('instrument', {'currency':'EUR'}), ('instrument', {'ask':'8'}), ('instrument', {'pending_buy_shares':1}),
    ('proposal', {'quantity':True}), ('proposal', {'quantity':0}), ('proposal', {'side':'SHORT'}),
    ('proposal', {'listing_id':'absent'}), ('proposal', {'approved_at':'2026-11-20T10:00:00'}),
])
def test_invalid_inputs_cannot_enter_financial_arithmetic(target,overrides):
    raw=packet()
    {'account':raw['account'],'instrument':raw['instruments'][0],'proposal':raw['proposals'][0]}[target].update(overrides)
    with pytest.raises(ValidationError):
        evaluate(raw)


def test_shared_issuer_and_classified_exposures_include_cash_reserved_for_open_buys():
    raw=packet()
    asset=raw['instruments'][0]
    raw['account']['open_orders']=1
    raw['instruments'].append(dict(asset,listing_id='other',pending_buy_shares=1,pending_buy_cash='9100'))
    case,=evaluate(raw)
    assert set(case['reasons']) >= {'CASH_RESERVE_LIMIT','GROSS_EXPOSURE_LIMIT','ISSUER_LIMIT','SECTOR_LIMIT','FACTOR_LIMIT'}
    assert case['remaining_cash_after_reservations']=='900' and case['veto']


def test_accepted_intents_reserve_capacity_once_per_batch_and_rejected_ones_spend_nothing():
    raw=packet()
    raw['account']['turnover_today']='1750'
    p=raw['proposals'][0]
    p['quantity']=40
    raw['proposals'] += [dict(p,candidate_id='s2'),dict(p,candidate_id='s3',quantity=10)]
    first,second,third=evaluate(raw)
    assert [r['veto'] for r in (first,second,third)]==[False,True,False]
    assert second['reasons']==['ORDER_COUNT_OR_TURNOVER_LIMIT']
    assert first['remaining_cash_after_reservations']==second['remaining_cash_after_reservations']
    assert third['remaining_cash_after_reservations']=='9499.000'


def test_sales_cannot_use_reserved_shares_or_finance_new_purchases():
    raw=packet()
    raw['account'].update(open_orders=1, cash='9500')
    a=raw['instruments'][0]
    a.update(shares=50,pending_sell_shares=35)
    p=raw['proposals'][0]
    p.update(side='SELL',quantity=10)
    raw['proposals'] += [dict(p,candidate_id='s2',quantity=6),dict(p,candidate_id='s3',side='BUY')]
    sell,oversell,buy=evaluate(raw)
    assert sell['decision']=='SELL' and sell['remaining_cash_after_reservations']=='9500'
    assert 'SELL_EXCEEDS_UNRESERVED_SHARES' in oversell['reasons']
    assert 'OPPOSING_OPEN_INTENT' in buy['reasons']


def test_open_and_new_proposals_share_one_listings_liquidity_allowance():
    raw=packet()
    raw['account']['open_orders']=1
    raw['instruments'][0].update(average_daily_shares='4000',pending_buy_shares=5,pending_buy_cash='51')
    first=raw['proposals'][0]
    raw['proposals'] += [dict(first,candidate_id='s2',quantity=6),dict(first,candidate_id='s3',quantity=5)]
    assert [(r['veto'],r['adv_fraction']) for r in evaluate(raw)]==[
        (False,'0.00375'),(True,'0.00525'),(False,'0.005')]


@pytest.mark.parametrize(('changes','reason'),[
    (None,'DOWNSIDE_SCENARIO_MISSING'),
    ({'invalidation':'10','stressed_exit':'9'},'DOWNSIDE_SCENARIO_INVALID'),
    ({'invalidation':'9','stressed_exit':'9.5'},'DOWNSIDE_SCENARIO_INVALID'),
])
def test_buy_requires_an_applicable_downside_scenario_but_hold_does_not(changes,reason):
    raw=packet()
    p=raw['proposals'][0]
    p['downside']=None if changes is None else dict(changes,evidence_ref='f'*64)
    assert reason in evaluate(raw)[0]['reasons']
    p.update(side='HOLD',quantity=0,downside=None)
    assert evaluate(raw)[0]['reasons']==['EXPLICIT_HOLD']


def test_stress_loss_combines_prior_reservations_and_keeps_the_worse_reviewed_exit():
    raw=packet()
    p=raw['proposals'][0]
    p['downside']['stressed_exit']='8'
    p['quantity']=20
    better=dict(p['downside'],stressed_exit='9.5')
    raw['proposals'] += [dict(p,candidate_id='s2',quantity=5,downside=better),
                         dict(p,candidate_id='s3',quantity=4,downside=better)]
    first,second,third=evaluate(raw)
    assert first['downside']['max_additional_shares']==24
    assert second['downside']['max_additional_shares']==4 and second['downside']['stressed_exit']=='8'
    assert second['reasons']==['LISTING_STRESS_LOSS_LIMIT'] and not third['veto']


def test_downside_counts_held_and_open_shares_and_a_total_loss_scenario():
    raw=packet()
    raw['account'].update(cash='9900.10',open_orders=1)
    raw['instruments'][0].update(shares=10,pending_buy_shares=5,pending_buy_cash='50.1')
    raw['proposals'][0]['downside']['stressed_exit']='8'
    row=evaluate(raw)[0]
    assert row['downside']['max_additional_shares']==9 and 'LISTING_STRESS_LOSS_LIMIT' in row['reasons']
    raw['proposals'][0]['downside']['stressed_exit']='0'
    assert evaluate(raw)[0]['downside']['max_additional_shares']==0


def test_explicit_hold_expiry_and_slot_budget():
    raw=packet()
    raw['proposals'][0].update(side='HOLD',quantity=0)
    case,=evaluate(raw)
    assert (case['decision'],case['veto'],case['reasons'])==('HOLD',False,['EXPLICIT_HOLD'])
    assert 'EVIDENCE_EXPIRED' in evaluate(raw,end=NOW)[0]['reasons']
    raw=packet()
    raw['account']['open_orders']=10
    raw['instruments'][0].update(pending_buy_shares=10,pending_buy_cash='100')
    assert 'ORDER_COUNT_OR_TURNOVER_LIMIT' in evaluate(raw)[0]['reasons']


def dossier(at, status='CANDIDATES_FOR_REVIEW', **changes):
    selected = status=='CANDIDATES_FOR_REVIEW'
    policy = {'version':'synthetic-test'}
    result = dict(version='b4-validation-dossier-v1', policy=policy, policy_hash=digest(policy),
        hypotheses=[dict(id='s',selected=selected,comparisons={} if status=='EVIDENCE_INCOMPLETE' else {'base':{},'adverse':{}})],
        search=dict(planned_trials=1,recorded_trials=1,hypotheses=1,scenarios=['base','adverse']),trials=[{}],
        decision=dict(status=status,next_action='REVIEW' if selected else 'OBSERVE',candidate_ids=['s'] if selected else [],
                      orders_enabled=False,execution_ready=False),
        source={'review_expires_at':(at+timedelta(days=1)).isoformat()},point_in_time=True,
        reserved_oos_sessions=126,temporal_reasons=[],instruments=['listing:example'])
    return result | changes


def bind(cycles, doc, raw=None):
    review=RiskReview(cycles.data.storage)
    ident=review.store.publish(doc)
    pin=None
    if raw is not None:
        raw['dossier_id']=ident
        payload=canonical(raw)
        pin=hashlib.sha256(payload).hexdigest()
        review.root.mkdir(parents=True,exist_ok=True)
        (review.root/(pin+'.json')).write_bytes(payload)
    cycles.risk=RiskReview(cycles.data.storage,Binding(ident,pin))
    return cycles.risk


def test_qualified_synthetic_case_persists_in_one_claim_and_replays_after_restart(cycles):
    at=cycles.clock()
    bind(cycles,dossier(at),packet(at))
    request=request_for(at)
    new,duplicate=cycles.submit(request)
    assert not duplicate
    risk=new['result']['risk']
    assert risk['outcome']=='ASSESSED' and risk['cases'][0]['decision']=='BUY'
    assert not risk['orders_enabled'] and not risk['execution_ready'] and risk['policy_hash']==POLICY_HASH
    assert cycles.status()['risk_policy']==dict(version=risk['policy_id'], policy_hash=risk['policy_hash'])
    assert risk['decision_id']==digest({k:v for k,v in risk.items() if k!='decision_id'})
    assert risk['budget']['cost_eur']==risk['budget']['network_calls']==risk['budget']['llm_calls']==0
    recovered=CycleService(cycles.sec,cycles.settings)
    assert recovered.submit(request)==(new,True)
    assert drain_cycle(cycles,new['id'])['result']['risk']==risk
    assert count(cycles,CYCLES)==1


@pytest.mark.parametrize(('status','changes','reason'),[
    ('NO_CANDIDATES',{},'NO_CANDIDATES'),('EVIDENCE_INCOMPLETE',{},'VALIDATION_INCOMPLETE'),
    ('CANDIDATES_FOR_REVIEW',{'point_in_time':False},'INDEPENDENT_VALIDATION_REQUIRED'),
    ('CANDIDATES_FOR_REVIEW',{'reserved_oos_sessions':0},'INDEPENDENT_VALIDATION_REQUIRED'),
    ('CANDIDATES_FOR_REVIEW',{'temporal_reasons':['EXPOSED']},'INDEPENDENT_VALIDATION_REQUIRED'),
    ('CANDIDATES_FOR_REVIEW',{},'REVIEWED_PAPER_INPUTS_MISSING'),
    ('NO_CANDIDATES',{'source':{'review_expires_at':NOW.replace(year=2025).isoformat()}},'EVIDENCE_EXPIRED'),
])
def test_validation_gate_before_loading_the_paper_account(cycles,status,changes,reason,monkeypatch):
    at=cycles.clock()
    review=bind(cycles,dossier(at,status,**changes))
    monkeypatch.setattr(review,'packet',lambda:pytest.fail('should not read an account'))
    risk=cycles.submit(request_for(at))[0]['result']['risk']
    assert (risk['outcome'],risk['reason'])==('OBSERVE' if reason=='NO_CANDIDATES' else 'VETO',reason)
    assert risk['cases']==[] and risk['account'] is None


@pytest.mark.parametrize('failure',['missing','tamper','scope','expired','veto','too_slow'])
def test_integrity_veto_and_budget_are_durable(cycles,monkeypatch,failure):
    at=cycles.clock()
    raw=packet(at)
    if failure=='scope':
        raw['proposals'][0]['candidate_id']='unregistered'
    if failure=='veto':
        raw['account']['kill_switch']=True
    if failure=='expired':
        raw['account']['as_of']=(at-timedelta(minutes=1)).isoformat()
    review=bind(cycles,dossier(at),raw)
    if failure=='missing':
        review.store.path(review.binding.dossier).unlink()
    if failure=='tamper':
        (review.root/(review.binding.packet_sha256+'.json')).write_bytes(b'{}')
    if failure=='too_slow':
        clock=iter((0,5))
        monkeypatch.setattr('app.risk_review.monotonic',lambda:next(clock))
    result=cycles.submit(request_for(at))[0]['result']['risk']
    expected={'missing':'DOSSIER_MISSING','tamper':'RISK_INPUTS_INVALID','scope':'RISK_INPUTS_INVALID',
              'expired':'ALL_PROPOSALS_VETOED','veto':'ALL_PROPOSALS_VETOED','too_slow':'RISK_TIME_BUDGET_EXCEEDED'}
    assert (result['outcome'],result['reason'])==('VETO',expected[failure])


def test_crash_before_receipt_rolls_back_the_window(cycles,monkeypatch):
    at=cycles.clock()
    review=bind(cycles,dossier(at,'NO_CANDIDATES'))
    with monkeypatch.context() as patch:
        def interrupt(*args):
            raise RuntimeError('simulated process interruption')
        patch.setattr(review,'run',interrupt)
        with pytest.raises(RuntimeError):
            cycles.submit(request_for(at))
    assert count(cycles,CYCLES)==0
    cycle,duplicate=cycles.submit(request_for(at))
    assert not duplicate and cycle['result']['risk']['outcome']=='OBSERVE'

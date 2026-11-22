"""B6 acceptance on actual B5 receipts, isolated SQLite and synthetic venue faults."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.config import ROOT, Settings
from app.cycle_contracts import window
from app.paper_simulator import PaperSimulator
from app.quant_store import digest
from app.storage_budget import StorageGovernor, StorageSettings
from scripts.probe_paper_simulator import check_cycle, demo
from test_cycles import cycles, request_for
from test_risk_review import NOW, bind, dossier, packet
from test_sec_financials import service


@pytest.fixture
def lab(tmp_path):
    storage = StorageGovernor(tmp_path / 'data', tmp_path / 'evidence', StorageSettings(_env_file=None))
    scope = SimpleNamespace(data=SimpleNamespace(storage=storage))
    clock = [NOW]
    folder = tmp_path / 'lab'

    def issue(raw=None, *, stamp=NOW, number=1, status='CANDIDATES_FOR_REVIEW'):
        raw = packet(stamp) if raw is None else deepcopy(raw)
        review = bind(scope, dossier(stamp, status), raw if status == 'CANDIDATES_FOR_REVIEW' else None)
        cycle_id = digest(['fixture', number])
        receipt = review.run(cycle_id, stamp, window(stamp)[1])
        return cycle_id, receipt, review

    return SimpleNamespace(clock=clock, folder=folder, issue=issue,
                           reopen=lambda: PaperSimulator(folder, clock=lambda: clock[0]))


def start(lab, raw=None):
    issued = lab.issue(raw)
    sim = lab.reopen()
    receipt = sim.consume(*issued)
    key, = receipt['client_order_ids']
    return sim, issued, key


def test_all_fixture_faults_replay_to_the_same_final_states():
    report = demo()
    assert report == demo() and report['source'] == 'SYNTHETIC_TEST'
    assert not report['external_orders_enabled']
    assert [(r['state'], r['filled']) for r in report['scenarios']] == [
        ('FILLED', 10), ('REJECTED', 0), ('CANCELED', 0), ('ACCEPTED', 0), ('CANCELED', 4), ('FILLED', 10), ('EXPIRED', 3)]
    assert len({r['client_order_id'] for r in report['scenarios']}) == 1


def test_real_cycle_contract_abstains_without_creating_a_simulator(cycles, tmp_path):
    at = cycles.clock()
    bind(cycles, dossier(at, 'NO_CANDIDATES'))
    cycle, _ = cycles.submit(request_for(at))
    settings = Settings(_env_file=None, database_url=str(cycles.engine.url))
    for identifier in ('latest', cycle['id']):
        receipt = check_cycle(identifier, settings)
        assert receipt['decision_id'] == cycle['result']['risk']['decision_id']
        assert receipt['reason'] == 'NO_CANDIDATES' and receipt['client_order_ids'] == []
    assert not list(tmp_path.rglob('b6-simulator.sqlite3'))
    with pytest.raises(ValueError, match='CYCLE_NOT_FOUND'):
        check_cycle('0' * 64, settings)


@pytest.mark.parametrize('change', ['hash', 'cycle', 'live', 'order_flag', 'quantity', 'packet', 'dossier', 'policy'])
def test_receipts_cannot_be_swapped_or_promoted_by_rehashing(lab, change):
    cycle, record, review = lab.issue()
    if change == 'cycle':
        cycle = digest('other')
    elif change == 'hash':
        record['decision_id'] = '0' * 64
    elif change in ('packet', 'dossier'):
        path = (review.root / (review.binding.packet_sha256 + '.json') if change == 'packet' else review.store.path(review.binding.dossier))
        path.write_bytes(b'{}')
    else:
        if change == 'live':
            record['mode'] = 'LIVE'
        elif change == 'order_flag':
            record['orders_enabled'] = True
        elif change == 'quantity':
            record['cases'][0]['quantity'] += 1
        else:
            record['policy_hash'] = '0' * 64
        record['decision_id'] = digest({k:v for k, v in record.items() if k != 'decision_id'})
    sim = lab.reopen()
    if change == 'policy':
        assert sim.consume(cycle, record, review)['reason'] == 'UNSUPPORTED_RISK_DECISION'
    else:
        with pytest.raises((ValueError, KeyError)):
            sim.consume(cycle, record, review)
    if sim.path.exists():
        with sim.transaction() as db:
            assert db.execute('select count(*) from intents').fetchone()[0] == 0


def test_future_expired_observation_hold_and_veto(lab):
    sim = lab.reopen()
    fresh = lab.issue()
    for offset in (-1, 30):
        lab.clock[0] = NOW+timedelta(seconds=offset)
        assert sim.consume(*fresh)['reason'] == 'RISK_OUTSIDE_VALIDITY'
    assert sim.consume(*lab.issue(status='NO_CANDIDATES'))['client_order_ids'] == []
    raw = packet()
    raw['proposals'][0].update(side='HOLD', quantity=0, downside=None)
    lab.clock[0] = NOW
    assert sim.consume(*lab.issue(raw))['reason'] == 'NO_ACTIONABLE_CASES'
    raw = packet()
    raw['account']['kill_switch'] = True
    assert sim.consume(*lab.issue(raw))['reason'] == 'ALL_PROPOSALS_VETOED'


def test_retries_and_changed_attempts_are_distinguished(lab):
    sim, issued, key = start(lab)
    order = sim.get(key)
    assert order['spec']['decision_id'] == issued[1]['decision_id'] and order['spec']['limit_price'] == '10'
    assert len(key) <= 48 and Decimal(order['reserved_cash']) == Decimal('100.20')
    assert sim.submit(key, 'a1', 'DROP_AFTER')['state'] == 'UNKNOWN'
    assert lab.reopen().submit(key, 'a1', 'DROP_AFTER')['state'] == 'UNKNOWN'
    assert sim.submit(key, 'a2')['reason'] == 'LOOKUP_REQUIRED'
    assert sim.cancel(key, 'c1')['reason'] == 'LOOKUP_REQUIRED'
    for fault in ('NOT_VISIBLE', 'UNAVAILABLE'):
        assert sim.lookup(key, 'lookup-' + fault, fault)['state'] == 'UNKNOWN'
    with pytest.raises(ValueError, match='EVENT_ID_CONFLICT'):
        sim.submit(key, 'a1', 'OK')
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')
    assert sim.lookup(key, 'found')['state'] == 'ACCEPTED'
    assert sim.submit(key, 'a3')['reason'] == 'ALREADY_ACCEPTED'
    assert [event['event_id'] for event in sim.history(key)] == [
        'a1', 'a2', 'c1', 'lookup-NOT_VISIBLE', 'lookup-UNAVAILABLE', 'found', 'a3']


def test_expiry_releases_unsent_orders_but_never_an_ambiguous_one(lab):
    sim, issued, key = start(lab)
    sim.submit(key, 'lost', 'DROP_BEFORE')
    lab.clock[0] += timedelta(seconds=30)
    assert sim.get(key)['state'] == 'UNKNOWN'
    assert sim.submit(key, 'unsafe')['reason'] == 'LOOKUP_REQUIRED'
    assert sim.lookup(key, 'absent')['state'] == 'EXPIRED'
    assert Decimal(sim.get(key)['reserved_cash']) == 0
    assert sim.consume(*issued)['client_order_ids'] == [key]
    assert sim.submit(key, 'after-expiry')['reason'] == 'ALREADY_EXPIRED'


def test_ready_expiry_and_reversed_clock(lab):
    sim, _, key = start(lab)
    lab.clock[0] += timedelta(seconds=30)
    assert sim.submit(key, 'late')['state'] == 'EXPIRED'
    assert Decimal(sim.get(key)['reserved_cash']) == 0
    lab.clock[0] = NOW
    with pytest.raises(ValueError, match='CLOCK_REVERSED'):
        sim.submit(key, 'clock-reversed')


def test_simulated_snapshot_and_committee_approval_are_bound(lab):
    sim, first, key = start(lab)
    renewed = sim.consume(*lab.issue(number=2))
    assert renewed['client_order_ids'] == [] and renewed['skipped'][0]['prior_order_id'] == key
    raw = packet()
    raw['proposals'][0]['quantity'] = 5
    with pytest.raises(ValueError, match='CONFLICTING_COMMITTEE_APPROVAL'):
        sim.consume(*lab.issue(raw, number=3))
    for field in ('account_ref', 'snapshot_ref'):
        raw = packet()
        raw['account'][field] = '9' * 64
        assert sim.consume(*lab.issue(raw, number=4))['reason'] == 'DIFFERENT_SIMULATION_SNAPSHOT'
    assert sim.consume(*first)['client_order_ids'] == [key]


def test_concurrent_receipts_share_turnover_and_release_only_after_confirmed_cancel(lab):
    raw = packet()
    raw['account']['turnover_today'] = '2350'
    first = lab.issue(raw)
    raw['proposals'][0]['committee_ref'] = '3' * 64
    second = lab.issue(raw, number=2)

    def admit(issued):
        return lab.reopen().consume(*issued)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(admit, [first, second]))
    winner = next(i for i, r in enumerate(results) if r['client_order_ids'])
    assert results[1 - winner]['reason'] == 'RESERVATIONS_VETO'
    assert 'ORDER_COUNT_OR_TURNOVER_LIMIT' in results[1 - winner]['skipped'][0]['reasons']
    sim = lab.reopen()
    key, = results[winner]['client_order_ids']
    sim.submit(key, 'send')
    sim.cancel(key, 'cancel', 'DROP_AFTER')
    loser = (first, second)[1 - winner]
    assert sim.consume(*loser)['reason'] == 'RECONCILIATION_REQUIRED'
    sim.lookup(key, 'cancel-confirmed')
    assert sim.consume(*loser)['reason'] == 'INTENTS_RESERVED'


def test_restart_with_a_changed_risk_policy_withdraws_the_reservation(lab, monkeypatch):
    sim, _, key = start(lab)
    monkeypatch.setattr('app.paper_simulator.POLICY_HASH', '0' * 64)
    event = lab.reopen().submit(key, 'different-policy')
    assert (event['state'], event['reason']) == ('REJECTED', 'RISK_POLICY_CHANGED')
    assert Decimal(sim.get(key)['reserved_cash']) == 0


def test_send_rechecks_other_unresolved_intents(lab):
    sim, _, first = start(lab)
    raw = packet()
    raw['proposals'][0]['committee_ref'] = '3' * 64
    second, = sim.consume(*lab.issue(raw, number=2))['client_order_ids']
    assert sim.submit(first, 'ambiguous', 'DROP_AFTER')['state'] == 'UNKNOWN'
    blocked = sim.submit(second, 'blocked')
    assert (blocked['state'], blocked['reason']) == ('READY', 'RECONCILIATION_REQUIRED')
    assert Decimal(sim.get(second)['reserved_cash']) == Decimal('100.20')
    assert sim.lookup(first, 'confirmed')['state'] == 'ACCEPTED'
    assert sim.submit(second, 'after-confirmation')['state'] == 'ACCEPTED'


def test_duplicate_concurrent_receipt_and_fill_only_count_once(lab):
    sim, issued, key = start(lab)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: lab.reopen().consume(*issued), range(8)))
    assert all(r['client_order_ids'] == [key] for r in results)
    sim.submit(key, 'send')
    with ThreadPoolExecutor(max_workers=4) as pool:
        fills = list(pool.map(lambda _: lab.reopen().fill(key, 'execution', 4, '9.99'), range(8)))
    assert len({digest(f) for f in fills}) == 1
    assert sim.get(key)['filled'] == 4 and Decimal(sim.get(key)['reserved_cash']) == Decimal('60.12')
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT', 'FILL', 'FILL_NOTICE']
    assert sim.history(key)[1]['payload'] == {'quantity': 4, 'price': '9.99'}
    with pytest.raises(ValueError, match='EVENT_ID_CONFLICT'):
        sim.fill(key, 'execution', 5, '9.99')


@pytest.mark.parametrize(('quantity', 'price'), [(True, '10'), (0, '10'), (-1, '10'), (1, '0'), (1, 'NaN'), (1, 10.0), (11, '10'), (1, '10.01')])
def test_invalid_fill_rolls_back_without_changing_the_order(lab, quantity, price):
    sim, _, key = start(lab)
    sim.submit(key, 'send')
    before = sim.get(key)
    with pytest.raises(ValueError):
        sim.fill(key, 'bad', quantity, price)
    assert sim.get(key) == before and len(sim.history(key)) == 1


def test_late_execution_notifications_cannot_reopen_a_closed_order(lab):
    sim, _, key = start(lab)
    sim.submit(key, 'send')
    sim.fill(key, 'first', 3, '9.95', deliver=False)
    sim.fill(key, 'second', 2, '9.96', deliver=False)
    assert sim.get(key)['filled'] == 0
    assert sim.deliver_fill(key, 'second')['filled'] == 5
    sim.cancel(key, 'cancel')
    assert sim.fill(key, 'first', 3, '9.95')['state'] == 'CANCELED'
    assert Decimal(sim.get(key)['filled_value']) == Decimal('49.77')
    assert sim.get(key)['filled'] == 5 and Decimal(sim.get(key)['reserved_cash']) == 0
    with pytest.raises(ValueError, match='NOT_FILLABLE'):
        sim.fill(key, 'after-cancel', 1, '9.90')


def test_sell_quantities_and_prior_reservations_are_never_double_spent(lab):
    raw = packet()
    raw['account'].update(cash='9900.10', open_orders=1)
    raw['instruments'][0].update(shares=10, pending_sell_shares=2)
    raw['proposals'][0].update(side='SELL', quantity=6, downside=None)
    sim, _, key = start(lab, raw)
    assert sim.get(key)['reserved_shares'] == 6
    sim.submit(key, 'sell')
    with pytest.raises(ValueError, match='FILL_OUTSIDE_LIMIT'):
        sim.fill(key, 'worse', 1, '9.98')
    sim.fill(key, 'partial', 3, '10.01')
    raw['proposals'][0].update(quantity=5, committee_ref='3' * 64)
    second = lab.issue(raw, number=2)
    assert sim.consume(*second)['reason'] == 'RESERVATIONS_VETO'
    sim.cancel(key, 'cancel')
    assert sim.consume(*second)['reason'] == 'INTENTS_RESERVED'


def test_two_reserved_sales_include_both_cost_buffers_at_the_turnover_limit(lab):
    raw = packet()
    raw['account'].update(cash='9800.20', turnover_today='2399.85')
    raw['instruments'][0]['shares'] = 20
    raw['proposals'][0].update(side='SELL', quantity=5, downside=None)
    sim, _, first = start(lab, raw)
    raw['proposals'][0]['committee_ref'] = '3' * 64
    second = lab.issue(raw, number=2)
    assert second[1]['outcome'] == 'ASSESSED'
    blocked = sim.consume(*second)
    assert blocked['skipped'][0]['reasons'] == ['ORDER_COUNT_OR_TURNOVER_LIMIT']
    assert sim.cancel(first, 'release')['state'] == 'CANCELED'
    assert sim.consume(*second)['reason'] == 'INTENTS_RESERVED'


def test_fill_and_cancel_race_has_one_consistent_venue_outcome(lab):
    sim, _, key = start(lab)
    sim.submit(key, 'send')

    def try_fill():
        try:
            return lab.reopen().fill(key, 'execution', 10, '9.99')['state']
        except ValueError as error:
            assert str(error) == 'VENUE_NOT_FILLABLE'
            return 'CANCELED'

    with ThreadPoolExecutor(max_workers=2) as pool:
        fill = pool.submit(try_fill)
        cancel = pool.submit(lambda: lab.reopen().cancel(key, 'cancel')['state'])
        states = (fill.result(), cancel.result())
    final = sim.get(key)
    assert states == (final['state'], final['state'])
    assert (final['state'], final['filled']) in [('FILLED', 10), ('CANCELED', 0)]
    assert Decimal(final['reserved_cash']) == 0


def test_process_restart_after_lost_response_uses_the_same_client_order(lab):
    sim, issued, key = start(lab)
    script = """import sys
from datetime import datetime
sys.path.insert(0, sys.argv[1])
from app.paper_simulator import PaperSimulator
sim = PaperSimulator(sys.argv[2], clock=lambda: datetime.fromisoformat(sys.argv[4]))
print(sim.submit(sys.argv[3], 'unique-attempt', 'DROP_AFTER')['state'])
"""
    child = subprocess.run([sys.executable, '-c', script, str(ROOT / 'backend'), str(lab.folder), key, NOW.isoformat()],
                           check=True, capture_output=True, text=True, timeout=30)
    assert child.stdout.strip() == 'UNKNOWN'
    assert sim.consume(*issued)['client_order_ids'] == [key]
    assert sim.lookup(key, 'recover')['state'] == 'ACCEPTED'
    assert [a['event_id'] for a in sim.history(key)] == ['unique-attempt', 'recover']


def test_interrupted_fill_rolls_back_prior_to_commit(lab, monkeypatch):
    sim, _, key = start(lab)
    sim.submit(key, 'send')
    original = sim._fill

    def broken(*args):
        original(*args)
        raise RuntimeError('process interrupted during local transaction')

    with monkeypatch.context() as patch:
        patch.setattr(sim, '_fill', broken)
        with pytest.raises(RuntimeError):
            sim.fill(key, 'trade', 3, '9.99')
    assert sim.get(key)['filled'] == 0 and len(sim.history(key)) == 1
    assert lab.reopen().fill(key, 'trade', 3, '9.99')['filled'] == 3


def test_refuses_an_unrelated_database(lab):
    lab.folder.mkdir()
    file = lab.folder / 'b6-simulator.sqlite3'
    with closing(sqlite3.connect(file)) as db:
        db.execute('create table original(v int)')
        db.commit()
    with pytest.raises(ValueError, match='NOT_A_B6_SIMULATOR_DATABASE'):
        lab.reopen().consume(*lab.issue())
    with closing(sqlite3.connect(file)) as db:
        assert db.execute('select name from sqlite_master').fetchall() == [('original',)]

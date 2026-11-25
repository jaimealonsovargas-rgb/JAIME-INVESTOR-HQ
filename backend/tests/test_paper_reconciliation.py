"""Execution identity, independent venue balances and recovery at the SQLite commit boundary."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import timedelta
import sqlite3

import pytest

from app.config import Settings
from app.cycle_contracts import window
from app.paper_outbox import PaperOutbox
from app.paper_reconciliation import reconcile
from app.paper_venue import venue_account
from app.quant_store import canonical, digest
from scripts import probe_paper_outbox as worker
from scripts.probe_paper_reconciliation import demo
from test_paper_simulator import lab, start
from test_cycles import cycles
from test_risk_review import bind, dossier, packet
from test_sec_financials import service


def test_process_dies_mid_recovery_then_replay_and_late_notice_are_economically_identical():
    report = demo()
    assert report == demo() and report['child_exit'] == 73
    assert report['before_hash'] == report['after_crash_hash']
    assert report['after_hash'] == report['replay_hash'] == report['late_notice_hash']
    assert report['before']['balances']['local'] == dict(cash='9990.02', positions={'SIM-ONLY': 1})
    expected = dict(cash='9960.07', positions={'SIM-ONLY': 4})
    assert report['before']['balances']['venue'] == expected
    assert all(b == expected for b in report['after']['balances'].values())
    order, = report['after']['orders']
    assert (order['state'], order['quantity'], order['local']['quantity'], order['reserved_cash']) == ('CANCELED', 10, 4, '0')
    assert [e['execution_id'] for e in report['recovered']] == ['fill-b', 'fill-c']
    assert report['after']['differences'] == []
    assert report['pending']['differences'] == [
        dict(code='VENUE_CASH_MISMATCH', recoverable=False, expected='9960.07', actual='9960.06'),
        dict(code='VENUE_POSITION_MISMATCH', recoverable=False, listing_id='SIM-ONLY', expected=4, actual=5)]


def test_sales_buys_and_untouched_initial_holdings_from_actual_fill_prices(lab):
    raw = packet()
    asset = raw['instruments'][0]
    asset['shares'] = 10
    raw['instruments'].append(dict(asset, listing_id='untouched', shares=5))
    raw['account']['cash'] = '9850.15'
    buy = raw['proposals'][0].copy()
    raw['proposals'][0].update(side='SELL', quantity=4, downside=None)
    sim, _, sell_id = start(lab, raw)
    sim.submit(sell_id, 'sell')
    sim.fill(sell_id, 'sale', 3, '10.01234567', deliver=False)
    sim.cancel(sell_id, 'cancel')
    first = reconcile(sim)
    assert first['before']['balances']['local'] == first['before']['balances']['venue']
    assert first['before']['balances']['booked']['positions']['example'] == 10
    assert first['recovered'] == [dict(client_order_id=sell_id, execution_id='sale')]
    raw['proposals'] = [dict(buy, quantity=2, committee_ref='3' * 64)]
    buy_id, = sim.consume(*lab.issue(raw, number=2))['client_order_ids']
    sim.submit(buy_id, 'buy')
    with pytest.raises(ValueError, match='EVENT_ID_CONFLICT'):
        sim.fill(buy_id, 'sale', 2, '9.95555555')
    with pytest.raises(ValueError, match='UNKNOWN_EXECUTION_ID'):
        sim.deliver_fill(buy_id, 'sale')
    sim.fill(buy_id, 'purchase', 2, '9.95555555', deliver=False)
    report = reconcile(lab.reopen())
    assert report['status'] == 'RECONCILED'
    expected = dict(cash='9860.27592591', positions=dict(example=9, untouched=5))
    assert all(b == expected for b in report['after']['balances'].values())
    states = {o['client_order_id']: (o['state'], o['reserved_shares']) for o in report['after']['orders']}
    assert states == {buy_id: ('FILLED', 0), sell_id: ('CANCELED', 0)}


def test_concurrent_reconciliation_deduplicates_by_execution_even_with_distinct_envelopes(lab):
    sim, _, key = start(lab)
    sim.submit(key, 'send')
    sim.fill(key, 'first', 2, '9.98', deliver=False)
    sim.fill(key, 'second', 2, '9.98')
    for envelope in ('redelivery', 'other-envelope', 'redelivery'):
        sim.deliver_fill(key, 'second', notice_id=envelope)
    assert sim.get(key)['filled'] == 4
    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(lambda _: reconcile(lab.reopen()), range(8)))
    assert [e for r in reports for e in r['recovered']] == [dict(client_order_id=key, execution_id='first')]
    assert len({r['snapshot_hash'] for r in reports}) == 1
    history = sim.history(key)
    assert sum(e['action'] == 'FILL_RECOVERED' for e in history) == 1
    assert sum(e['action'] == 'FILL_NOTICE' for e in history) == 3
    assert reconcile(sim)['after']['balances']['booked'] == dict(cash='9960.08', positions=dict(example=4))
    assert sim.history(key) == history


def test_equal_fills_on_different_listings_rebuild_each_position_separately(lab, cycles):
    at = lab.clock[0]
    raw = packet(at)
    raw['instruments'].append(dict(raw['instruments'][0], listing_id='other', shares=5))
    raw['account']['cash'] = '9950.05'
    raw['proposals'].append(dict(raw['proposals'][0], listing_id='other', side='SELL', quantity=3, downside=None))
    review = bind(cycles, dossier(at, instruments=['listing:example', 'listing:other']), raw)
    cycle = digest('two-listings')
    sim = lab.reopen()
    ids = sim.consume(cycle, review.run(cycle, at, window(at)[1]), review)['client_order_ids']
    by_side = {sim.get(i)['spec']['side']: i for i in ids}
    for side in ('BUY', 'SELL'):
        key = by_side[side]
        sim.submit(key, 'send-' + side)
        sim.fill(key, 'fill-' + side, 2, '9.99', deliver=False)
        sim.end_session(key, 'end-' + side)
    report = reconcile(sim)
    assert len(report['recovered']) == 2 and report['status'] == 'RECONCILED'
    expected = dict(cash='9950.05', positions=dict(example=2, other=3))
    assert all(b == expected for b in report['after']['balances'].values())
    assert all(o['state'] == 'EXPIRED' for o in report['after']['orders'])


@pytest.mark.parametrize('version', [1, 2])
def test_legacy_lab_adopts_venue_totals_once_and_preserves_unseen_executions(lab, version):
    sim, _, key = start(lab)
    sim.submit(key, 'sent')
    sim.fill(key, 'legacy', 4, '9.99', deliver=False)
    attempts = PaperOutbox(lab.folder).history(key)
    events = sim.history(key)
    with closing(sqlite3.connect(sim.path)) as db, db:
        db.execute("DELETE FROM meta WHERE key='venue_account'")
        if version == 1:
            db.execute('DROP TABLE outbox_attempts')
            db.execute('DROP TABLE outbox')
        db.execute(f'PRAGMA user_version={version}')
    state = reconcile(sim, repair=False)
    assert state['before']['balances']['venue'] == dict(cash='9960.04', positions=dict(example=4))
    assert state['before']['balances']['local']['positions'] == dict(example=0)
    assert sim.history(key) == events
    first = reconcile(lab.reopen())
    assert first['recovered'] == [dict(client_order_id=key, execution_id='legacy')]
    assert reconcile(lab.reopen())['snapshot_hash'] == first['snapshot_hash']
    assert PaperOutbox(lab.folder).history(key) == attempts
    with sim.transaction() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 3


@pytest.mark.parametrize(('change', 'code'), [
    ('venue_value', 'VENUE_TOTAL_WITHOUT_MATCHING_EXECUTIONS'),
    ('local_value', 'LOCAL_TOTAL_WITHOUT_MATCHING_EXECUTIONS'),
    ('receipt', 'UNMATCHED_EXECUTION_RECEIPT'),
    ('position', 'VENUE_POSITION_MISMATCH'),
    ('account', 'VENUE_ACCOUNT_MISSING'),
])
def test_unexplained_differences_preserve_evidence_and_block_worker(lab, monkeypatch, change, code):
    sim, _, key = start(lab)
    sim.submit(key, 'submit')
    sim.fill(key, 'seen', 2, '9.99')
    sim.fill(key, 'missing', 1, '9.98', deliver=False)
    with sim.transaction() as db:
        if change == 'venue_value':
            db.execute('UPDATE intents SET venue_value=?', ('30.06',))
        elif change == 'local_value':
            db.execute('UPDATE intents SET filled_value=?', ('19.97',))
        elif change == 'receipt':
            db.execute("UPDATE events SET payload=? WHERE action='FILL_NOTICE'", (canonical(dict(execution_id='absent')),))
        elif change == 'account':
            db.execute("DELETE FROM meta WHERE key='venue_account'")
        else:
            statement = venue_account(db)
            statement['positions']['example'] += 1
            db.execute("UPDATE meta SET value=? WHERE key='venue_account'", (canonical(statement),))
    original = sim.history(key)
    report = reconcile(lab.reopen())
    assert report['status'] == 'PENDING' and report['recovered'] == []
    assert report['before'] == report['after']
    assert code in [d['code'] for d in report['after']['differences'] if not d['recoverable']]
    monkeypatch.setattr(worker, 'simulator_folder', lambda settings: lab.folder)
    monkeypatch.setattr(worker, 'check_cycle', lambda *a: pytest.fail('Admission before reconciliation'))
    readout = worker.drain('a' * 64, settings=Settings(_env_file=None))
    assert readout['worked'] == 0 and readout['admission']['reason'] == 'RECONCILIATION_REQUIRED'
    assert sim.history(key) == original and PaperOutbox(lab.folder).history(key) == []


def test_worker_recovers_fills_when_outbox_has_already_finished(lab, monkeypatch):
    sim, _, key = start(lab)
    q = PaperOutbox(lab.folder, clock=lambda: lab.clock[0])
    assert q.run_once('submit')['status'] == 'DONE'
    sim.fill(key, 'missed', 1, '10', deliver=False)
    sim.cancel(key, 'cancel')
    monkeypatch.setattr(worker, 'simulator_folder', lambda settings: lab.folder)
    monkeypatch.setattr(worker, 'PaperOutbox', lambda folder: q)
    monkeypatch.setattr(worker, 'check_cycle', lambda *a: dict(reason='NO_CANDIDATES'))
    report = worker.drain('a' * 64, settings=Settings(_env_file=None))
    assert report['worked'] == 0 and report['reconciliation']['status'] == 'RECONCILED'
    assert report['reconciliation']['recovered'] == [dict(client_order_id=key, execution_id='missed')]
    assert len(q.history(key)) == 1 and sim.get(key)['filled'] == 1


def test_discrepancy_after_worker_poll_blocks_claimed_delivery_and_new_admission(lab):
    sim, _, first = start(lab)
    q = PaperOutbox(lab.folder, clock=lambda: lab.clock[0])
    q.run_once('first-worker')
    raw = packet()
    raw['proposals'][0]['committee_ref'] = '3' * 64
    second, = sim.consume(*lab.issue(raw, number=2))['client_order_ids']
    assert reconcile(sim)['status'] == 'RECONCILED'

    def drift_after_claim():
        with sim.transaction() as db:
            statement = venue_account(db)
            statement['cash'] = '9999.99'
            db.execute("UPDATE meta SET value=? WHERE key='venue_account'", (canonical(statement),))

    attempted = q.run_once('second-worker', after_claim=drift_after_claim)
    assert (attempted['reason'], attempted['state'], attempted['status']) == ('RECONCILIATION_REQUIRED', 'READY', 'PENDING')
    with sim.transaction() as db:
        assert sim.row(db, second)['venue_state'] is None
    raw['proposals'][0]['committee_ref'] = '4' * 64
    assert sim.consume(*lab.issue(raw, number=3))['reason'] == 'RECONCILIATION_REQUIRED'
    assert {entry['client_order_id'] for entry in q.entries()} == {first, second}


def test_no_account_does_not_create_a_database_or_assume_a_starting_balance(lab):
    sim = lab.reopen()
    assert reconcile(sim)['status'] == 'NO_ACCOUNT' and not sim.path.exists()
    with sim.transaction():
        pass
    assert reconcile(sim)['opening'] is None


def test_ambiguous_absence_uses_lookup_and_never_resends(lab):
    sim, _, key = start(lab)
    sim.submit(key, 'drop', fault='DROP_BEFORE')
    lab.clock[0] += timedelta(minutes=1)
    report = reconcile(sim)
    assert report['status'] == 'RECONCILED' and report['recovered'] == []
    assert sim.get(key)['state'] == 'EXPIRED'
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT', 'LOOKUP']
    assert all(b['cash'] == '10000' for b in report['after']['balances'].values())


def test_recovery_preserves_preexisting_caller_event_with_same_identifier(lab):
    sim, _, key = start(lab)
    existing_id = 'b63:' + digest([key, 'FILL_RECOVERED', 'missed'])
    sim.submit(key, existing_id)
    sim.fill(key, 'missed', 1, '10', deliver=False)
    assert reconcile(sim)['status'] == 'RECONCILED'
    history = sim.history(key)
    assert len(history) == 3 and history[0]['event_id'] == existing_id
    assert history[-1]['event_id'] != existing_id and history[-1]['action'] == 'FILL_RECOVERED'

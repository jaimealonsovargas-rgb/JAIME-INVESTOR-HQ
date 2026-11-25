"""B6 durable dispatch acceptance, using real B5 receipts and a controlled clock."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import sqlite3
from threading import Event

import pytest

from app.paper_outbox import PaperOutbox
from test_paper_simulator import lab, start
from test_risk_review import packet


def queue(lab):
    return PaperOutbox(lab.folder, clock=lambda: lab.clock[0])


def crash():
    raise RuntimeError('simulated process crash')


def entry(lab, key):
    row, = queue(lab).entries()
    assert row['client_order_id'] == key
    return row


def test_receipt_replay_has_one_durable_entry_and_reservation(lab):
    sim, issued, key = start(lab)
    assert entry(lab, key)['status'] == 'PENDING'
    assert entry(lab, key)['attempts'] == 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda _: lab.reopen().consume(*issued), range(8)))
    assert all(r['client_order_ids'] == [key] for r in receipts)
    assert len(queue(lab).entries()) == 1
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')
    assert queue(lab).run_once('first')['state'] == 'ACCEPTED'
    assert entry(lab, key)['status'] == 'DONE'
    assert entry(lab, key)['attempts'] == 1
    assert queue(lab).run_once('restarted') is None
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT']


@pytest.mark.parametrize('decision', ['OBSERVE', 'HOLD', 'VETO'])
def test_non_actionable_decisions_never_enqueue(lab, decision):
    raw = packet()
    if decision == 'HOLD':
        raw['proposals'][0].update(side='HOLD', quantity=0, downside=None)
    elif decision == 'VETO':
        raw['account']['kill_switch'] = True
    issued = lab.issue(raw, status='NO_CANDIDATES' if decision == 'OBSERVE' else 'CANDIDATES_FOR_REVIEW')
    assert lab.reopen().consume(*issued)['client_order_ids'] == []
    assert queue(lab).entries() == []
    assert queue(lab).run_once('idle') is None


def test_two_workers_cannot_deliver_the_same_claim(lab):
    sim, _, key = start(lab)
    claimed, release = Event(), Event()

    def hold_claim():
        claimed.set()
        assert release.wait(10), 'competing worker did not finish'

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(queue(lab).run_once, 'worker-one', after_claim=hold_claim)
        try:
            assert claimed.wait(10), 'first worker did not claim'
            assert entry(lab, key)['status'] == 'CLAIMED'
            assert entry(lab, key)['attempts'] == 1
            assert queue(lab).run_once('worker-two') is None
        finally:
            release.set()
        assert first.result(timeout=10)['state'] == 'ACCEPTED'
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT']
    assert entry(lab, key)['status'] == 'DONE'


@pytest.mark.parametrize('hook', ['after_claim', 'after_delivery'])
def test_crashed_worker_is_recovered_after_lease_without_duplicate_delivery(lab, hook):
    sim, _, key = start(lab)
    with pytest.raises(RuntimeError, match='simulated process crash'):
        queue(lab).run_once('crashing', **{hook: crash})
    assert entry(lab, key)['status'] == 'CLAIMED'
    assert entry(lab, key)['attempts'] == 1
    assert queue(lab).run_once('early-restart') is None
    lab.clock[0] += timedelta(seconds=9)
    assert queue(lab).run_once('still-leased') is None
    lab.clock[0] += timedelta(seconds=1)
    recovered = queue(lab).run_once('recovered')
    if hook == 'after_claim':
        assert recovered['state'] == 'READY'
        assert entry(lab, key)['status'] == 'PENDING'
        lab.clock[0] += timedelta(seconds=1)
        recovered = queue(lab).run_once('retry-after-confirmed-absence')
    assert recovered['state'] == 'ACCEPTED'
    assert entry(lab, key)['status'] == 'DONE'
    assert entry(lab, key)['attempts'] == (3 if hook == 'after_claim' else 2)
    history = sim.history(key)
    assert sum(e['action'] == 'SUBMIT' for e in history) == 1
    if hook == 'after_delivery':
        assert any(e['action'] == 'LOOKUP' for e in history)
    assert sim.get(key)['filled'] == 0


@pytest.mark.parametrize('fault', ['DROP_BEFORE', 'DROP_AFTER'])
def test_ambiguous_delivery_retains_reservation_and_queries_before_retry(lab, fault):
    sim, _, key = start(lab)
    assert queue(lab).run_once('first', submit_fault=fault)['state'] == 'UNKNOWN'
    assert entry(lab, key)['status'] == 'UNCERTAIN'
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')
    assert queue(lab).run_once('too-soon') is None
    lab.clock[0] += timedelta(seconds=1)
    assert queue(lab).run_once('unavailable', lookup_fault='UNAVAILABLE')['state'] == 'UNKNOWN'
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT', 'LOOKUP']
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')
    lab.clock[0] += timedelta(seconds=1)
    recovered = queue(lab).run_once('reconcile')
    if fault == 'DROP_BEFORE':
        assert recovered['state'] == 'READY'
        assert entry(lab, key)['status'] == 'PENDING'
        lab.clock[0] += timedelta(seconds=1)
        recovered = queue(lab).run_once('confirmed-absent-retry')
    assert recovered['state'] == 'ACCEPTED'
    assert entry(lab, key)['status'] == 'DONE'
    actions = [e['action'] for e in sim.history(key)]
    assert actions[:3] == ['SUBMIT', 'LOOKUP', 'LOOKUP']
    assert actions.count('SUBMIT') == (2 if fault == 'DROP_BEFORE' else 1)
    sim.fill(key, 'only-execution', 10, '9.99')
    assert queue(lab).run_once('finished') is None
    assert sim.get(key)['filled'] == 10


def test_expired_unsent_entry_is_closed_without_venue_acceptance(lab):
    sim, _, key = start(lab)
    lab.clock[0] += timedelta(seconds=30)
    assert queue(lab).run_once('late')['state'] == 'EXPIRED'
    assert entry(lab, key)['status'] == 'DONE'
    assert Decimal(sim.get(key)['reserved_cash']) == 0
    with sim.transaction() as db:
        assert db.execute('SELECT venue_state FROM intents WHERE client_id=?', (key,)).fetchone()[0] is None


def test_ambiguous_accepted_order_survives_local_expiry(lab):
    sim, _, key = start(lab)
    assert queue(lab).run_once('lost', submit_fault='DROP_AFTER')['state'] == 'UNKNOWN'
    lab.clock[0] += timedelta(seconds=30)
    assert queue(lab).run_once('blind', lookup_fault='UNAVAILABLE')['state'] == 'UNKNOWN'
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')
    lab.clock[0] += timedelta(seconds=1)
    assert queue(lab).run_once('found')['state'] == 'ACCEPTED'
    assert entry(lab, key)['status'] == 'DONE'
    assert sum(e['action'] == 'SUBMIT' for e in sim.history(key)) == 1


def test_dispatch_rechecks_risk_policy_after_restart(lab, monkeypatch):
    sim, _, key = start(lab)
    monkeypatch.setattr('app.paper_simulator.POLICY_HASH', '0' * 64)
    assert queue(lab).run_once('new-policy')['state'] == 'REJECTED'
    assert entry(lab, key)['status'] == 'DONE'
    assert Decimal(sim.get(key)['reserved_cash']) == 0


def test_outbox_failure_rolls_back_intention_admission_and_reservation(lab):
    sim = lab.reopen()
    with sim.transaction() as db:
        db.execute("CREATE TRIGGER fail_enqueue BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT, 'enqueue interrupted'); END")
    issued = lab.issue()
    with pytest.raises(sqlite3.IntegrityError, match='enqueue interrupted'):
        sim.consume(*issued)
    with sim.transaction() as db:
        assert db.execute('SELECT count(*) FROM intents').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM admissions').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM outbox').fetchone()[0] == 0
        db.execute('DROP TRIGGER fail_enqueue')
    key, = sim.consume(*issued)['client_order_ids']
    assert entry(lab, key)['status'] == 'PENDING'
    assert Decimal(sim.get(key)['reserved_cash']) == Decimal('100.20')


def test_old_worker_cannot_deliver_after_another_worker_recovers_lease(lab):
    sim, _, key = start(lab)
    recovered = {}

    def recover_before_old_delivery():
        lab.clock[0] += timedelta(seconds=10)
        assert queue(lab).run_once('worker-b')['state'] == 'READY'
        lab.clock[0] += timedelta(seconds=1)
        assert queue(lab).run_once('worker-b')['state'] == 'ACCEPTED'
        recovered['entry'] = entry(lab, key)
        recovered['attempts'] = queue(lab).history(key)
        recovered['events'] = sim.history(key)

    result = queue(lab).run_once('worker-a', after_claim=recover_before_old_delivery)
    assert result['reason'] == 'LEASE_LOST'
    assert entry(lab, key) == recovered['entry']
    assert queue(lab).history(key) == recovered['attempts']
    assert sim.history(key) == recovered['events']
    attempts = recovered['attempts']
    assert [a['attempt'] for a in attempts] == [1, 2, 3]
    assert [a['action'] for a in attempts] == ['SUBMIT', 'LOOKUP', 'SUBMIT']
    assert attempts[0]['disposition'] == 'LEASE_EXPIRED'
    assert attempts[0]['delivered_at'] is None
    assert len({a['event_id'] for a in attempts}) == 3
    assert [e['event_id'] for e in sim.history(key)] == [a['event_id'] for a in attempts[1:]]
    assert entry(lab, key)['status'] == 'DONE'


def test_old_worker_cannot_ack_after_recovery_even_with_reused_worker_name(lab):
    sim, _, key = start(lab)
    recovered = {}

    def recover_before_old_ack():
        lab.clock[0] += timedelta(seconds=10)
        # A restarted process can reuse the same worker name: its attempt must fence A.
        assert queue(lab).run_once('worker')['state'] == 'ACCEPTED'
        recovered['entry'] = entry(lab, key)
        recovered['attempts'] = queue(lab).history(key)
        recovered['events'] = sim.history(key)

    result = queue(lab).run_once('worker', after_delivery=recover_before_old_ack)
    assert result['reason'] == 'LEASE_LOST'
    assert entry(lab, key) == recovered['entry']
    assert queue(lab).history(key) == recovered['attempts']
    assert sim.history(key) == recovered['events']
    attempts = recovered['attempts']
    assert [a['attempt'] for a in attempts] == [1, 2]
    assert [a['action'] for a in attempts] == ['SUBMIT', 'LOOKUP']
    assert [a['disposition'] for a in attempts] == ['LEASE_EXPIRED', 'DONE']
    assert attempts[0]['delivered_at'] is not None
    assert len({a['event_id'] for a in attempts}) == 2
    assert [e['event_id'] for e in sim.history(key)] == [a['event_id'] for a in attempts]
    assert entry(lab, key)['status'] == 'DONE'
    sim.fill(key, 'one-fill-after-recovery', 10, '9.99')
    assert sim.get(key)['filled'] == 10

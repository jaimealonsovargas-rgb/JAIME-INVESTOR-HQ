"""Compatibility with existing labs and actual process loss at the delivery boundary."""
from contextlib import closing
from datetime import timedelta
import sqlite3
import subprocess
import sys

import pytest

from app.config import ROOT, Settings
from app.paper_outbox import PaperOutbox
from app.quant_store import digest
from scripts import probe_paper_outbox as probe
from test_paper_simulator import lab, start


@pytest.mark.parametrize(('state', 'expected'), [
    ('READY', 'PENDING'), ('UNKNOWN', 'UNCERTAIN'), ('ACCEPTED', 'DONE'),
    ('PARTIALLY_FILLED', 'DONE'), ('CANCELED', 'DONE'), ('FILLED', 'DONE'),
])
def test_pre_queue_lab_is_adopted_once(lab, state, expected):
    sim, issued, key = start(lab)
    # v1 let a caller record arbitrary event IDs, including a future worker's ID.
    old_event = 'outbox:' + digest([key, 1])
    sim.lookup(key, old_event)
    if state != 'READY':
        sim.submit(key, 'old-submit', 'DROP_AFTER' if state == 'UNKNOWN' else 'OK')
    if state in ('PARTIALLY_FILLED', 'FILLED'):
        sim.fill(key, 'old-fill', 3 if state == 'PARTIALLY_FILLED' else 10, '9.99')
    if state == 'CANCELED':
        sim.cancel(key, 'old-cancel')
    order = sim.get(key)
    events = sim.history(key)
    assert order['state'] == state
    # Restore the exact four-table v1 schema in the isolated test database.
    with closing(sqlite3.connect(sim.path)) as db, db:
        db.execute('DROP TABLE outbox_attempts')
        db.execute('DROP TABLE outbox')
        db.execute("DELETE FROM meta WHERE key='venue_account'")
        db.execute('PRAGMA user_version=1')
    queue = PaperOutbox(lab.folder, clock=lambda: lab.clock[0])
    entry, = queue.entries()
    assert (entry['status'], entry['attempts']) == (expected, 0)
    assert lab.reopen().consume(*issued)['client_order_ids'] == [key]
    assert lab.reopen().history(key) == events and lab.reopen().get(key) == order
    report = queue.run_once('recover-v1')
    if expected == 'DONE':
        assert report is None
    else:
        assert report['action'] == ('LOOKUP' if state == 'UNKNOWN' else 'SUBMIT')
        assert report['state'] == 'ACCEPTED'
        assert report['event_id'] != old_event
    assert queue.run_once('restart') is None
    assert queue.entries()[0]['status'] == 'DONE'


def test_abrupt_exit_after_venue_fill_recovers_without_a_second_fill(lab):
    sim, _, key = start(lab)
    child = """import os,sys
from datetime import datetime
sys.path.insert(0,sys.argv[1])
from app.paper_outbox import PaperOutbox
queue = PaperOutbox(sys.argv[2], clock=lambda: datetime.fromisoformat(sys.argv[4]))
def cut_power():
    queue.sim.fill(sys.argv[3], 'execution-before-exit', 4, '9.99', deliver=False)
    os._exit(73)
queue.run_once('terminated', after_delivery=cut_power)
"""
    process = subprocess.run([sys.executable, '-c', child, str(ROOT / 'backend'), str(lab.folder),
                              key, lab.clock[0].isoformat()], timeout=40, capture_output=True)
    assert process.returncode == 73, process.stderr
    queue = PaperOutbox(lab.folder, clock=lambda: lab.clock[0])
    assert queue.entries()[0]['status'] == 'CLAIMED'
    lab.clock[0] += timedelta(seconds=10)
    result = queue.run_once('replacement')
    assert (result['action'], result['state'], result['filled']) == ('LOOKUP', 'PARTIALLY_FILLED', 4)
    assert queue.run_once('replacement') is None
    assert [e['action'] for e in sim.history(key)] == ['SUBMIT', 'FILL', 'LOOKUP']
    assert sim.deliver_fill(key, 'execution-before-exit')['filled'] == 4
    assert [e['disposition'] for e in queue.history(key)] == ['LEASE_EXPIRED', 'DONE']


def test_worker_retries_admission_after_a_transient_failure(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, database_url='sqlite:///' + str(tmp_path / 'data' / 'fixture.db'))
    reports = iter([ValueError('STORAGE_BUSY'), {'reason': 'RESERVATIONS_VETO'}, {'reason': 'NO_CANDIDATES'}])
    def inspect(cycle, settings):
        result = next(reports)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(probe, 'check_cycle', inspect)
    cache = {}
    for reason in ['STORAGE_BUSY', 'RESERVATIONS_VETO', 'NO_CANDIDATES', 'NO_CANDIDATES']:
        report = probe.drain('a' * 64, settings=settings, admission_cache=cache)
        assert report['admission']['reason'] == reason and report['worked'] == 0
    assert not probe.simulator_folder(settings).exists()

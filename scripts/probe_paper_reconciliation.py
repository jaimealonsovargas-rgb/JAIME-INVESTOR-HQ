"""Concilia la cuenta del simulador local o reproduce el ensayo sintético de B6.3."""
import argparse
from datetime import datetime
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

if __package__:
    from .probe_paper_simulator import fixture_review, simulator_folder
else:
    from probe_paper_simulator import fixture_review, simulator_folder

from app.paper_outbox import PaperOutbox
from app.paper_reconciliation import reconcile
from app.paper_simulator import PaperSimulator
from app.paper_venue import venue_account
from app.quant_store import canonical, digest


def interrupt_fixture(folder, at):
    class InterruptedSimulator(PaperSimulator):
        def record_event(self, db, client_id, event_id, action, payload, now):
            result = super().record_event(db, client_id, event_id, action, payload, now)
            if action == 'FILL_RECOVERED':
                os._exit(73)  # Solo el hijo del ensayo, tras la primera escritura y antes del commit.
            return result

    sim = InterruptedSimulator(folder, clock=lambda: datetime.fromisoformat(at))
    reconcile(sim)


def demo():
    with TemporaryDirectory(prefix='jaime-b63-fixture-') as temp:
        root = Path(temp)
        at, review, risk = fixture_review(root)
        folder = root / 'simulator'
        sim = PaperSimulator(folder, clock=lambda: at)
        admission = sim.consume(risk['cycle_id'], risk, review)
        client, = admission['client_order_ids']
        PaperOutbox(folder, clock=lambda: at).run_once('b63-fixture')
        sim.fill(client, 'fill-a', 1, '9.98')
        sim.deliver_fill(client, 'fill-a', notice_id='duplicate-a')
        sim.fill(client, 'fill-b', 2, '9.99', deliver=False)
        sim.fill(client, 'fill-c', 1, '9.97', deliver=False)
        sim.cancel(client, 'cancel', fault='DROP_AFTER')
        before = reconcile(sim, repair=False)

        child = multiprocessing.get_context('spawn').Process(target=interrupt_fixture, args=(folder, at.isoformat()))
        child.start()
        child.join(30)
        if child.is_alive():
            child.terminate()
            child.join()
        if child.exitcode != 73:
            raise ValueError('FIXTURE_INTERRUPTION_FAILED')
        restarted = PaperSimulator(folder, clock=lambda: at)
        interrupted = reconcile(restarted, repair=False)
        repaired = reconcile(restarted)
        repeated = reconcile(restarted)
        restarted.deliver_fill(client, 'fill-b')
        late = reconcile(restarted)
        final = repaired['after']
        expected = dict(cash='9960.07', positions={'SIM-ONLY': 4})
        if (before != interrupted or repaired['status'] != 'RECONCILED' or
                [r['execution_id'] for r in repaired['recovered']] != ['fill-b', 'fill-c'] or
                final != repeated['after'] or final != late['after'] or repeated['recovered'] or
                final['orders'][0]['state'] != 'CANCELED' or any(v != expected for v in final['balances'].values())):
            raise ValueError('FIXTURE_RECONCILIATION_FAILED')

        # Descuadrar solo el extracto ficticio para comprobar que el diario no oculta la diferencia.
        with restarted.transaction() as db:
            statement = venue_account(db)
            statement['cash'] = '9960.06'
            statement['positions']['SIM-ONLY'] += 1
            db.execute("UPDATE meta SET value=? WHERE key='venue_account'", (canonical(statement),))
        mismatch = reconcile(restarted)
        if (mismatch['status'] != 'PENDING' or mismatch['before'] != mismatch['after'] or
                {d['code'] for d in mismatch['after']['differences']} != {'VENUE_CASH_MISMATCH', 'VENUE_POSITION_MISMATCH'}):
            raise ValueError('FIXTURE_UNRESOLVED_DIFFERENCE_LOST')
        evidence = dict(domain='LOCAL_SIMULATOR', source='SYNTHETIC_TEST', external_orders_enabled=False,
                        opening=before['opening'], before=before['before'], child_exit=child.exitcode,
                        before_hash=before['snapshot_hash'], after_crash_hash=interrupted['snapshot_hash'],
                        recovered=repaired['recovered'], after=final, after_hash=repaired['snapshot_hash'],
                        replay_hash=repeated['snapshot_hash'], late_notice_hash=late['snapshot_hash'],
                        pending=mismatch['after'])
        return dict(**evidence, evidence_hash=digest(evidence))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--inspect', action='store_true', help='Comparar sin registrar recuperaciones')
    group.add_argument('--demo', action='store_true', help='Ensayar una caída en una base temporal')
    args = parser.parse_args(argv)
    try:
        report = demo() if args.demo else reconcile(PaperSimulator(simulator_folder()), repair=not args.inspect)
    except (ValueError, OSError, sqlite3.Error) as error:
        reason = str(error)
        print(json.dumps(dict(status='BLOCKED', reason=reason if reason.isidentifier() and reason.isupper()
                              else 'RECONCILIATION_UNAVAILABLE', external_orders_enabled=False)))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report.get('status') == 'PENDING' else 0


if __name__ == '__main__':
    sys.exit(main())

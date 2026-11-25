"""Consume B5 y drena la cola local B6; nunca programa ciclos ni conecta un bróker."""
import argparse
from contextlib import closing
from datetime import timedelta
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from tempfile import TemporaryDirectory
import time

from sqlalchemy.engine import make_url

if __package__:
    from .probe_paper_simulator import check_cycle, fixture_review, simulator_folder
else:
    from probe_paper_simulator import check_cycle, fixture_review, simulator_folder

from app.config import Settings
from app.paper_outbox import PaperOutbox
from app.paper_reconciliation import reconcile
from app.paper_simulator import PaperSimulator
from app.quant_store import digest


def blocked(error):
    reason = str(error)
    return dict(state='BLOCKED', reason=reason if re.fullmatch('[A-Z0-9_]+', reason) else 'OUTBOX_UNAVAILABLE')


def drain(cycle='latest', worker='local-cli', max_steps=100, settings=None, admission_cache=None):
    # Un recibo ausente, antiguo o inválido no impide recuperar trabajo ya admitido.
    settings = settings or Settings()
    queue = PaperOutbox(simulator_folder(settings))
    report = reconcile(queue.sim)
    differences = report['after']['differences'] if report['after'] else []
    reconciliation = dict(status=report['status'], snapshot_hash=report['snapshot_hash'],
                          recovered=report['recovered'], differences=differences)
    if differences:
        return dict(domain='LOCAL_SIMULATOR', source='STORED_B5_CYCLE', reconciliation=reconciliation,
                    admission=blocked(ValueError('RECONCILIATION_REQUIRED')), worked=0, results=[],
                    entries=queue.entries(), external_orders_enabled=False)
    try:
        selected = cycle
        if admission_cache is not None and cycle == 'latest':
            path = Path(make_url(settings.database_url).database).resolve()
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
                row = db.execute('SELECT id FROM automation_cycles ORDER BY created_at DESC, id LIMIT 1').fetchone()
            if row is None:
                raise ValueError('CYCLE_NOT_FOUND')
            selected = row[0]
        if admission_cache is not None and admission_cache.get('cycle') == selected:
            admission = admission_cache['report']
        else:
            try:
                admission = check_cycle(selected, settings)
            except (ValueError, KeyError, OSError, sqlite3.Error) as error:
                admission = blocked(error)
            # Only immutable admissions can be reused. Storage pressure and unresolved
            # reservations may clear within this very same B5 cycle.
            if admission_cache is not None and (admission.get('client_order_ids') or
                    admission.get('reason') in {'NO_CANDIDATES', 'ALL_PROPOSALS_VETOED',
                                                'APPROVAL_ALREADY_CONSUMED', 'NO_ACTIONABLE_CASES'}):
                admission_cache.update(cycle=selected, report=admission)
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        admission = blocked(error)
    results = []
    for _ in range(max_steps):
        result = queue.run_once(worker)
        if result is None:
            break
        results.append(result)
        # Un envío ambiguo se recupera en otro sondeo, sin bucle apretado de consultas.
        if result.get('state') == 'UNKNOWN':
            break
    return dict(domain='LOCAL_SIMULATOR', source='STORED_B5_CYCLE', reconciliation=reconciliation, admission=admission,
                worked=len(results), results=results, entries=queue.entries(), external_orders_enabled=False)


def demo():
    with TemporaryDirectory(prefix='jaime-b6-outbox-') as temp:
        root = Path(temp)
        at, review, risk = fixture_review(root)
        if risk['outcome'] != 'ASSESSED':
            raise ValueError('FIXTURE_RISK_FAILED')
        scenarios = []
        class Crash(Exception):
            pass
        def crash(*args):
            raise Crash()
        for scenario in ('lost_response', 'after_claim', 'after_delivery'):
            now = at
            folder = root / scenario
            sim = PaperSimulator(folder, clock=lambda: now)
            receipt = sim.consume(risk['cycle_id'], risk, review)
            queue = PaperOutbox(folder, clock=lambda: now)
            before = queue.entries()
            try:
                options = dict(submit_fault='DROP_AFTER') if scenario == 'lost_response' else {scenario: crash}
                first = queue.run_once('demo-before-restart', **options)
            except Crash:
                first = dict(state='SYNTHETIC_PROCESS_CRASH', point=scenario)
            now += timedelta(seconds=1 if scenario == 'lost_response' else 11)
            recovered = PaperOutbox(folder, clock=lambda: now).run_once('demo-after-restart')
            recovery = [recovered]
            if recovered and recovered['state'] == 'READY':
                now += timedelta(seconds=1)
                recovered = PaperOutbox(folder, clock=lambda: now).run_once('demo-after-lookup')
                recovery.append(recovered)
            entries = PaperOutbox(folder, clock=lambda: now).entries()
            if len(before) != 1 or first is None or recovered is None or recovered['state'] != 'ACCEPTED':
                raise ValueError('OUTBOX_DEMO_RECOVERY_FAILED')
            if PaperOutbox(folder, clock=lambda: now).run_once('demo-empty') is not None:
                raise ValueError('OUTBOX_DEMO_NOT_DRAINED')
            scenarios.append(dict(scenario=scenario, admission=receipt, before=before,
                                  interrupted=first, recovered=recovered, recovery=recovery, entries=entries))
        evidence = dict(scenarios=scenarios)
        return dict(domain='LOCAL_SIMULATOR', source='SYNTHETIC_TEST', external_orders_enabled=False,
                    **evidence, evidence_hash=digest(evidence))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycle', default='latest', metavar='ID', help='Recibo B5 existente (por defecto latest)')
    parser.add_argument('--worker', default='local-cli', help='Identificador estable del trabajador local')
    parser.add_argument('--max-steps', type=int, default=100, help='Máximo de reclamaciones por sondeo')
    parser.add_argument('--continuous', action='store_true', help='Sondear recibos y pendientes hasta Ctrl+C')
    parser.add_argument('--poll-seconds', type=float, default=1, help='Espera entre sondeos continuos')
    parser.add_argument('--demo', action='store_true', help='Recuperar una respuesta perdida en una carpeta temporal')
    args = parser.parse_args(argv)
    if args.max_steps < 1 or not math.isfinite(args.poll_seconds) or args.poll_seconds <= 0:
        parser.error('max-steps y poll-seconds deben ser positivos y finitos')
    if args.cycle != 'latest' and not re.fullmatch('[a-f0-9]{64}', args.cycle):
        parser.error('cycle debe ser latest o un hash hexadecimal de 64 caracteres')
    if args.demo and args.continuous:
        parser.error('demo no admite continuous')
    previous = None
    try:
        settings = None if args.demo else Settings()
        admission_cache = {} if args.continuous else None
        while True:
            try:
                report = demo() if args.demo else drain(args.cycle, args.worker, args.max_steps, settings, admission_cache)
            except (OSError, sqlite3.OperationalError) as error:
                if not args.continuous:
                    raise
                report = dict(**blocked(error), external_orders_enabled=False)
            # Mostrar cambios o trabajo; evitar repetir un diagnóstico negativo sin cambios.
            serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
            if serialized != previous or report.get('worked'):
                print(serialized, flush=True)
                previous = serialized
            if not args.continuous:
                return 2 if report.get('admission', {}).get('state') == 'BLOCKED' else 0
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 0
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        print(json.dumps(dict(**blocked(error), external_orders_enabled=False)), flush=True)
        return 2


if __name__ == '__main__':
    sys.exit(main())

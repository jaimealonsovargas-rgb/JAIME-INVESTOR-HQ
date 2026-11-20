"""Piloto opcional de minería sobre un fixture local. No consulta proveedores ni la base de JAIME."""
import argparse
from collections import Counter
from contextlib import contextmanager
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.dataset_manifests import canonical, publish_no_replace
from app.storage_budget import MIB, StorageGovernor

LAB = ROOT / 'integrations/quant_search'
FILES = ('integrations/quant_search/pilot_protocol.json', 'integrations/quant_search/requirements-win-py314.lock',
         'integrations/quant_search/worker.py', 'backend/app/quant_contracts.py', 'backend/app/quant_engine.py',
         'scripts/probe_quant_search.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def freeze(path, raw):
    if path.resolve() != path.absolute():
        raise ValueError('PILOT_PATH_REDIRECTED')
    if not path.exists():
        temporary = path.with_name('.' + uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                publish_no_replace(temporary, path)
            except FileExistsError:
                pass
        finally:
            temporary.unlink(missing_ok=True)
    if path.read_bytes() != raw:
        raise ValueError('PILOT_ARTIFACT_CONFLICT')


def inspect_trace(raw, plan):
    if len(raw) > 2 * MIB:
        raise ValueError('PILOT_TRACE_TOO_LARGE')
    events = [json.loads(line) for line in raw.splitlines()]
    budget, folds = plan['attempt_budget'], plan['development_folds']
    if (len(events) < 2 * budget + 3 or events[0]['event'] != 'START'
            or events[0]['protocol_sha256'] != sha((LAB / 'pilot_protocol.json').read_bytes())):
        raise ValueError('PILOT_TRACE_INCOMPLETE')
    states, windows, evaluated = Counter(), set(), set()
    finished, pruned = set(), set()
    known_steps, complete_scores = {}, {}
    reports = 0
    for i in range(budget):
        registered, terminal = events[2*i + 1:2*i + 3]
        w = registered.get('lookback')
        if (registered.get('event') != 'REGISTERED' or terminal.get('event') != 'FINISHED'
                or registered.get('attempt') != i or terminal.get('attempt') != i
                or registered.get('family') != plan['family'] or type(w) is not int or not plan['lookback'][0] <= w <= plan['lookback'][1]):
            raise ValueError('PILOT_TRIAL_SEQUENCE')
        state, scores = terminal['state'], terminal['development_excess']
        if not ((state == 'COMPLETE' and len(scores) == folds) or (state == 'PRUNED' and 0 < len(scores) < folds)):
            raise ValueError('PILOT_TRIAL_OUTCOME')
        values = [Decimal(s) for s in scores]
        for step, value in enumerate(values):
            if not value.is_finite() or known_steps.setdefault((w, step), value) != value:
                raise ValueError('PILOT_SCORE_CONFLICT')
        if state == 'COMPLETE':
            complete_scores[w] = sum(values) / folds
        states[state] += 1
        windows.add(w)
        (finished if state == 'COMPLETE' else pruned).add(w)
        reports += len(scores)
        evaluated.update((w, j) for j in range(len(scores)))
    closed, *audits, summary = events[2*budget + 1:]
    missed = pruned - finished
    for audit in audits:
        w = audit['lookback']
        values = [Decimal(v) for v in audit['development_excess']]
        if (len(values) != folds or any(not v.is_finite() or known_steps.get((w, s), v) != v
                                       for s, v in enumerate(values))
                or Decimal(audit['full_development_excess']) != sum(values) / folds):
            raise ValueError('PILOT_SHADOW_AUDIT_CONFLICT')
    if (closed != dict(event='SEARCH_CLOSED', attempts=budget, unique_parameters=len(windows))
            or any(a.get('event') != 'SHADOW_AUDIT' for a in audits)
            or [a['lookback'] for a in audits] != sorted(missed)
            or summary.get('event') != 'SUMMARY' or summary['purpose'] != 'ENGINEERING_ONLY'
            or summary['attempts'] != budget or summary['states'] != dict(states)
            or summary['unique_parameters'] != len(windows) or summary['repeated_proposals'] != budget - len(windows)
            or summary['search_fold_calculations'] != len(evaluated) or summary['logical_fold_reports'] != reports
            or summary['avoided_during_search'] != summary['shadow_fold_calculations']
            or summary['full_unique_fold_calculations'] != folds * len(windows)
            or summary['avoided_during_search'] != folds * len(windows) - len(evaluated)
            or summary['exclusively_pruned_parameters'] != len(missed)
            or not complete_scores or summary['pruned_strictly_better_than_best_completed'] != sum(
                Decimal(a['full_development_excess']) > max(complete_scores.values()) for a in audits)
            or summary['reserved_oos_sessions'] != 0 or summary['real_trials'] != 0
            or summary['execution_ready'] is not False):
        raise ValueError('PILOT_RECONCILIATION_FAILED')
    return summary


@contextmanager
def worker_slot(folder):
    path = folder / 'worker.lock'
    if path.resolve() != path.absolute():
        raise ValueError('PILOT_PATH_REDIRECTED')
    with path.open('a+b') as lock:
        try:
            if os.name == 'nt':
                import msvcrt
                if lock.tell() == 0:
                    lock.write(b'0')
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError('PILOT_WORKER_BUSY') from None
        yield  # Closing releases the OS lock, including after a process failure.


def execute(folder, python, plan):
    # Retain even interrupted attempts. Only reconciled complete traces are published.
    attempt_dir = folder / ('attempt-' + uuid4().hex)
    attempt_dir.mkdir()
    trace = attempt_dir / 'events.jsonl'
    env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP') if k in os.environ}
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    with trace.open('xb') as stream:
        run = subprocess.run([str(python), '-I', '-B', str(LAB / 'worker.py')], cwd=attempt_dir, env=env,
                             stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.PIPE,
                             timeout=plan['timeout_seconds'], check=False,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if run.returncode:
        raise RuntimeError('PILOT_WORKER_FAILED')
    measures = json.loads(run.stderr.splitlines()[-1])
    freeze(attempt_dir / 'resources.json', canonical(measures))
    return trace.read_bytes(), measures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', action='store_true', help='Repetir y verificar el mismo hash con la semilla fijada')
    args = parser.parse_args(argv)
    python = ROOT / '.tools/quant-search/Scripts/python.exe'
    if not python.is_file():
        parser.exit(2, 'Falta el entorno opcional de integrations/quant_search.\n')
    plan = json.loads((LAB / 'pilot_protocol.json').read_bytes())
    sources = {f: sha((ROOT/f).read_bytes()) for f in FILES}
    ident = sha(canonical(sources))
    storage = StorageGovernor(ROOT/'data', ROOT/'output')
    folder = storage.output_root / 'quant-search-pilot' / ident
    if folder.resolve() != folder.absolute():
        raise ValueError('PILOT_PATH_REDIRECTED')
    with storage.admission(reserve=8*MIB, destination='output'):
        folder.mkdir(parents=True, exist_ok=True)
        freeze(folder/'registration.json', canonical(dict(plan=plan, sources=sources, plan_id=ident)))
    with worker_slot(folder.parent):
        target = folder/'result.json'
        measures = None
        if target.exists() and not args.replay:
            saved = json.loads(target.read_bytes())
            trace_id = saved['trace_sha256']
            if not isinstance(trace_id, str) or len(trace_id) != 64 or any(c not in '0123456789abcdef' for c in trace_id):
                raise ValueError('INVALID_TRACE_ID')
            trace_path = folder/(trace_id + '.jsonl')
            if trace_path.resolve() != trace_path.absolute() or trace_path.stat().st_size > 2*MIB:
                raise ValueError('INVALID_SAVED_TRACE')
            raw = trace_path.read_bytes()
        else:
            raw, measures = execute(folder, python, plan)
        summary = inspect_trace(raw, plan)
        trace_id = sha(raw)
        result = dict(plan_id=ident, trace_sha256=trace_id, summary=summary)
        with storage.admission(reserve=2*MIB, destination='output'):
            freeze(folder/(trace_id + '.jsonl'), raw)
            freeze(target, canonical(result))
    print(json.dumps(dict(**result, resources_this_run=measures, result_path=str(target)), indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ArithmeticError, RuntimeError, KeyError, subprocess.TimeoutExpired) as error:
        print('PILOT_UNAVAILABLE', type(error).__name__, str(error) if str(error).isupper() else '', file=sys.stderr)
        raise SystemExit(2)

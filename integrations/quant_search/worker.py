"""Isolated Optuna compatibility pilot. Input is exclusively the fixed synthetic protocol."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import re
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'backend'))
import optuna
from app.quant_contracts import Bar, ExperimentConfig, SyntheticDataset
from app.quant_engine import _calculate


def emit(**event):
    print(json.dumps(event, sort_keys=True, separators=(',', ':'), allow_nan=False), flush=True)


def make_folds(plan):
    rng = random.Random(plan['seed_data'])
    day = datetime(2000, 1, 1, 9, tzinfo=timezone.utc)
    price = 10000  # Integer cents, steps of at most ten cents, independently drawn.
    folds = []
    for _ in range(plan['development_folds']):
        bars = []
        for _ in range(plan['warmup_sessions_per_fold'] + plan['scored_sessions_per_fold']):
            after = price + rng.choice((-10, -5, 5, 10))
            close = day + timedelta(hours=6)
            bars.append(Bar(opens_at=day, closes_at=close, available_at=close,
                            open=Decimal(price) / 100, close=Decimal(after) / 100))
            day += timedelta(days=1)
            price = after
        folds.append(SyntheticDataset(kind='SYNTHETIC_TEST', instrument='TEST_ONLY', calendar='EXPLICIT_SYNTHETIC_SESSIONS',
                                      adjustments='NO_CORPORATE_ACTIONS_SYNTHETIC', currency='TEST_CCU', bars=tuple(bars)))
    return folds


def evaluate(plan, dataset, family, lookback=None):
    config = ExperimentConfig(genome=dict(family=family, lookback=lookback,
        mechanism='Prueba aritmética local de ventanas sobre incrementos sin señal plantada.',
        falsification='Comparar el exceso neto con ambos controles en los tramos de desarrollo.'),
        initial_cash=plan['initial_cash'], costs=plan['costs'])
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 40, ROUND_HALF_UP
        # Same JAIME calculator and same common flat warmup for every rule and both controls.
        result = _calculate(dataset, config, warmup=plan['warmup_sessions_per_fold'])
    return Decimal(result['return_fraction'])


def run(plan):
    optuna.logging.set_verbosity(optuna.logging.ERROR)
    folds = make_folds(plan)
    benchmark = [max(evaluate(plan, f, 'CASH'), evaluate(plan, f, 'BUY_HOLD')) for f in folds]
    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=plan['seed_optimizer']),
                                pruner=optuna.pruners.MedianPruner(**plan['pruner']))
    cache, completed, pruned = {}, {}, []
    states = Counter()
    reported_steps = 0

    def excess(window, step):
        key = (window, step)
        if key not in cache:
            cache[key] = evaluate(plan, folds[step], plan['family'], window) - benchmark[step]
        return cache[key]

    for _ in range(plan['attempt_budget']):
        trial = study.ask()
        window = trial.suggest_int('lookback', *plan['lookback'])
        emit(event='REGISTERED', attempt=trial.number, family=plan['family'], lookback=window)
        values = []
        try:
            for step in range(len(folds)):
                values.append(excess(window, step))
                score = sum(values) / len(values)
                trial.report(float(score), step)
                reported_steps += 1
                if step + 1 < len(folds) and trial.should_prune():
                    study.tell(trial, state=optuna.trial.TrialState.PRUNED)
                    state = 'PRUNED'
                    pruned.append(window)
                    break
            else:
                study.tell(trial, float(score))
                state = 'COMPLETE'
                completed[window] = score
        except Exception as error:
            study.tell(trial, state=optuna.trial.TrialState.FAIL)
            emit(event='FINISHED', attempt=trial.number, state='FAIL', error=type(error).__name__)
            raise
        states[state] += 1
        emit(event='FINISHED', attempt=trial.number, state=state, development_excess=[str(v) for v in values])

    evaluations_before_audit = len(cache)
    windows = sorted(set(pruned).union(completed))
    # Shadow audit on synthetic folds only. It cannot send any further observations to the sampler.
    emit(event='SEARCH_CLOSED', attempts=len(study.trials), unique_parameters=len(windows))
    full_scores = {w: sum(excess(w, step) for step in range(len(folds))) / len(folds) for w in windows}
    missed = set(pruned) - completed.keys()
    best_completed = max(completed.values())
    for w in sorted(missed):
        emit(event='SHADOW_AUDIT', lookback=w, full_development_excess=str(full_scores[w]),
             development_excess=[str(cache[w, s]) for s in range(len(folds))])
    full_unique = len(windows) * len(folds)
    emit(event='SUMMARY', purpose='ENGINEERING_ONLY', family=plan['family'], states=dict(states),
         attempts=len(study.trials), unique_parameters=len(windows), repeated_proposals=len(study.trials) - len(windows),
         registered_budget=plan['attempt_budget'], development_folds=len(folds), control_calculations=2 * len(folds),
         logical_fold_reports=reported_steps, full_unique_fold_calculations=full_unique,
         search_fold_calculations=evaluations_before_audit, shadow_fold_calculations=len(cache) - evaluations_before_audit,
         avoided_during_search=full_unique - evaluations_before_audit, exclusively_pruned_parameters=len(missed),
         pruned_strictly_better_than_best_completed=sum(full_scores[w] > best_completed for w in missed),
         real_trials=0, reserved_oos_sessions=0, execution_ready=False)


def peak_mib():
    if sys.platform != 'win32':
        import resource
        divisor = 1024 ** 2 if sys.platform == 'darwin' else 1024
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divisor, 1)
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('faults', wintypes.DWORD),
                    ('peak', ctypes.c_size_t), ('rest', ctypes.c_size_t * 7)]
    counters = Counters()
    counters.size = ctypes.sizeof(counters)
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if get_memory(wintypes.HANDLE(-1), ctypes.byref(counters), counters.size):
        return round(counters.peak / 1024 ** 2, 1)
    return None


def main():
    start = time.monotonic()
    plan_bytes = (HERE / 'pilot_protocol.json').read_bytes()
    plan = json.loads(plan_bytes)
    locked = dict(re.findall(r'^([A-Za-z0-9._-]+)==([^\s]+)', (HERE / 'requirements-win-py314.lock').read_text(), re.M))
    if (sys.version_info[:2] != (3, 14) or optuna.__version__ != plan['optuna_version']
            or any(importlib.metadata.version(k) != v for k, v in locked.items())):
        raise RuntimeError('PILOT_RUNTIME_LOCK_MISMATCH')
    emit(event='START', protocol_sha256=hashlib.sha256(plan_bytes).hexdigest(), python=platform.python_version(),
         optuna=optuna.__version__, packages=locked)
    run(plan)
    print(json.dumps(dict(peak_process_mib=peak_mib(), seconds=round(time.monotonic()-start, 3))), file=sys.stderr)


if __name__ == '__main__':
    main()

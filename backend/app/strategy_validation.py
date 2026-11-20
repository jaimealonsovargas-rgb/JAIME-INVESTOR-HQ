"""Deterministic B4 selection on verified, session-aligned private NAV paths."""
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction

from app.quant_store import digest
from app.validation_policy import POLICY, block_sign_test, export_policy, export_reservation, probability, temporal_checks


@dataclass(frozen=True)
class TrialPath:
    state: str
    reason: str
    initial: Decimal | None = None
    equity: tuple[Decimal, ...] = ()
    positions: tuple[int, ...] = ()


def performance(path, start, end):
    previous = path.equity[start - 1] if start else path.initial
    peak, worst = previous, Decimal(0)
    for value in path.equity[start:end + 1]:
        peak = max(peak, value)
        worst = max(worst, (peak - value) / peak)
    return path.equity[end] / previous - 1, worst


def compare(path, cash, held, start, end):
    net, drawdown = performance(path, start, end)
    cash_net, _ = performance(cash, start, end)
    held_net, held_drawdown = performance(held, start, end)
    reasons = []
    if net <= cash_net:
        reasons.append('NET_RETURN_NOT_ABOVE_CASH')
    if net <= held_net:
        reasons.append('NET_RETURN_NOT_ABOVE_BUY_HOLD')
    if drawdown > held_drawdown:
        reasons.append('DRAWDOWN_ABOVE_BUY_HOLD')
    return dict(net_return=str(net), max_drawdown=str(drawdown),
                excess_vs_cash=str(net - cash_net), excess_vs_buy_hold=str(net - held_net),
                drawdown_minus_buy_hold=str(drawdown - held_drawdown),
                sessions_in_market=sum(p > 0 for p in path.positions[start:end + 1]), reasons=reasons)


def search_design_hash(hypotheses, costs, study):
    """Digest to register before first validation. Observation timestamps are separate receipts."""
    reservation = study.reservation
    return digest(dict(policy=export_policy(), hypotheses=hypotheses, costs=costs,
                       instruments=study.instruments, ancestors=study.ancestor_instruments,
                       evaluation=asdict(study.evaluation), search_protocol_ref=study.search_protocol_ref,
                       block_assumptions_ref=study.block_assumptions_ref,
                       folds=[asdict(f) for f in reservation.folds], oos=asdict(reservation.oos),
                       purge_sessions=reservation.purge_sessions, embargo_sessions=reservation.embargo_sessions))


def validate_search(hypotheses, costs, paths, study):
    """The trusted adapter supplies the entire declared grid, including terminal failures."""
    with localcontext() as context:
        context.prec = 40
        context.rounding = ROUND_HALF_UP
        return _select(hypotheses, costs, paths, study)


def family_diagnostics(results, scenarios, windows):
    """Descriptive dispersion of the preregistered variants, including failed members."""
    families = defaultdict(list)
    for hypothesis in results:
        families[hypothesis['family']].append(hypothesis)
    diagnostics = {}
    for family, members in families.items():
        ranges = {}
        for cost in scenarios:
            ranges[cost] = {}
            for stage, _, _ in windows:
                values = [Decimal(member['comparisons'][cost][stage]['net_return']) for member in members
                          if cost in member['comparisons']]
                ranges[cost][stage] = dict(observed=len(values), minimum=str(min(values)) if values else None,
                                           maximum=str(max(values)) if values else None)
        diagnostics[family] = dict(planned=len(members), variants=[m['id'] for m in members],
                                   economic_passes=sum(m['economic_screen_passed'] for m in members),
                                   net_return_ranges=ranges)
    return diagnostics


def _select(hypotheses, costs, paths, study):
    controls = POLICY.benchmark_ids
    names = [h['id'] for h in hypotheses]
    scenarios = [cost['id'] for cost in costs]
    if (not names or len(names + list(controls)) != len(set(names + list(controls)))
            or len(set(scenarios)) != len(scenarios) or not {'base', 'adverse'} <= set(scenarios)):
        raise ValueError('INVALID_SEARCH_FAMILY')
    terms = {cost['id']: tuple(Decimal(cost[k]) for k in ('commission_bps', 'slippage_bps', 'fixed_per_fill'))
             for cost in costs}
    if (any(not value.is_finite() or value < 0 for case in terms.values() for value in case)
            or terms['base'] == terms['adverse'] or any(b > a for b, a in zip(terms['base'], terms['adverse']))):
        raise ValueError('INVALID_STRESS_COSTS')
    expected = {(name, cost) for name in [*names, *controls] for cost in scenarios}
    if expected != set(paths):
        raise ValueError('SEARCH_GRID_MISSING_OR_EXTRA_TRIALS')
    temporal, oos = temporal_checks(study)
    if study.reservation and (not study.search_protocol_ref or
            study.reservation.locked_design_hash != search_design_hash(hypotheses, costs, study)):
        temporal = sorted(set(temporal + ['REGISTERED_DESIGN_MISMATCH']))
    days = {d: i for i, d in enumerate(study.sessions)}
    size = len(days)
    for path in paths.values():
        if path.state not in {'COMPLETED', 'REJECTED', 'FAILED'}:
            raise ValueError('NONTERMINAL_CAMPAIGN')
        if path.state == 'COMPLETED':
            if (path.initial is None or not path.initial.is_finite() or path.initial <= 0
                    or len(path.equity) != size or len(path.positions) != size
                    or any(not val.is_finite() or val <= 0 for val in path.equity)
                    or any(type(pos) is not int or pos < 0 for pos in path.positions)):
                raise ValueError('INVALID_OR_UNALIGNED_TRIAL_PATH')
        elif path.equity or path.positions:
            raise ValueError('NONCOMPLETED_TRIAL_WITH_PATH')
    if len({p.initial for p in paths.values() if p.state == 'COMPLETED'}) > 1:
        raise ValueError('INCOMPARABLE_STARTING_CAPITAL')
    if any(paths[c, s].state != 'COMPLETED' for c in controls for s in scenarios):
        temporal = sorted(set(temporal + ['BENCHMARK_UNAVAILABLE']))
    evaluation = (days[study.evaluation.first], days[study.evaluation.last])
    windows = [('exploration', *evaluation)]
    if study.reservation and not temporal:
        windows = [('validation_' + str(i), days[f.validation.first], days[f.validation.last])
                   for i, f in enumerate(study.reservation.folds, 1)]
        windows.append(('oos', *oos))
    results = []
    signatures = defaultdict(list)
    for hypothesis in hypotheses:
        name = hypothesis['id']
        reasons, comparisons, tests = set(), {}, {}
        worst_p = Fraction(0)
        all_completed = all(paths[name, s].state == 'COMPLETED' for s in scenarios)
        can_test = not temporal and all_completed
        if can_test and any(start and paths[k, s].positions[start - 1] != 0
                            for _, start, _ in windows for k in (name, *controls) for s in scenarios):
            reasons.add('POSITION_CARRIED_INTO_RESERVED_WINDOW')
            can_test = False
        for cost in scenarios:
            path, cash, held = (paths[k, cost] for k in (name, *controls))
            if path.state != 'COMPLETED':
                reasons.add('STRATEGY_TRIAL_' + path.state)
            if cash.state != 'COMPLETED' or held.state != 'COMPLETED':
                reasons.add('BENCHMARK_UNAVAILABLE')
            if any(p.state != 'COMPLETED' for p in (path, cash, held)):
                continue
            comparisons[cost] = {}
            for stage, start, end in windows:
                check = compare(path, cash, held, start, end)
                comparisons[cost][stage] = check
                reasons.update(check['reasons'])
            if can_test:
                tests[cost] = {}
                for benchmark, control in zip(controls, (cash, held)):
                    p, detail = block_sign_test(path.equity, control.equity, path.initial, *oos)
                    worst_p = max(worst_p, p)
                    tests[cost][benchmark] = dict(**detail, p_one_sided=probability(p))
        # Identical inventories across every cost and day get a single review
        # slot. The full declared denominator always includes every variant.
        if all_completed:
            signature = digest([paths[name, cost].positions for cost in scenarios])
            signatures[signature].append(name)
        else:
            signature = None
        adjusted = min(Fraction(1), worst_p * len(names)) if can_test else None
        screen = all_completed and len(comparisons) == len(scenarios) and all(
            not check['reasons'] for stages in comparisons.values() for check in stages.values())
        if adjusted is not None and adjusted > Fraction(POLICY.family_alpha):
            reasons.add('FAMILY_ADJUSTED_TEST_NOT_SIGNIFICANT')
        reasons.update(temporal)
        sensitivity = {stage: str(Decimal(comparisons['adverse'][stage]['net_return'])
                                  - Decimal(comparisons['base'][stage]['net_return']))
                       for stage, _, _ in windows} if {'base', 'adverse'} <= comparisons.keys() else {}
        results.append(dict(**hypothesis, comparisons=comparisons, adverse_minus_base_return=sensitivity,
                            economic_screen_passed=screen,
                            statistical_evidence='ASSESSED' if can_test else 'INSUFFICIENT_EVIDENCE',
                            test_details=tests, family_adjusted_p=probability(adjusted) if can_test else None,
                            position_signature=signature, reasons=sorted(reasons), selected=not reasons))
    selected, seen = [], set()
    for row in results:  # Preregistered order breaks ties between identical exposures.
        if row['selected'] and row['position_signature'] in seen:
            row.update(selected=False, reasons=['DUPLICATE_EXPOSURE_PATH'])
        if row['selected']:
            selected.append(row['id'])
            seen.add(row['position_signature'])
    comparable = any(len(h['comparisons']) == len(scenarios) for h in results)
    status = 'CANDIDATES_FOR_REVIEW' if selected else ('NO_CANDIDATES' if comparable else 'EVIDENCE_INCOMPLETE')
    return dict(policy=export_policy(), policy_hash=digest(export_policy()), evaluation=asdict(study.evaluation),
                reservation=export_reservation(study.reservation),
                prior_exposure=[asdict(e) for e in study.history], instruments=study.instruments,
                ancestor_instruments=study.ancestor_instruments, point_in_time=study.point_in_time,
                exposure_inventory_complete=study.exposure_inventory_complete,
                block_assumptions_ref=study.block_assumptions_ref, search_protocol_ref=study.search_protocol_ref,
                temporal_reasons=temporal,
                search=dict(hypotheses=len(names), benchmarks=list(controls), scenarios=list(scenarios),
                            planned_trials=len(expected), recorded_trials=len(paths),
                            trial_states=dict(sorted(Counter(p.state for p in paths.values()).items())),
                            family_sizes=dict(Counter(h['family'] for h in hypotheses)),
                            distinct_position_paths=len(signatures)),
                family_diagnostics=family_diagnostics(results, scenarios, windows), hypotheses=results,
                decision=dict(status=status,
                              candidate_ids=selected, next_action='REVIEW' if selected else 'OBSERVE',
                              orders_enabled=False, execution_ready=False))

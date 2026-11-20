"""B4 tests use arithmetic fixtures. They do not establish investment performance."""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
import json

import pytest
from app.quant_store import digest
from app.strategy_validation import TrialPath, search_design_hash, validate_search
from app.validation_policy import Exposure, Fold, POLICY, Reservation, Span, Study, block_sign_test, temporal_checks

COSTS = [dict(id='base', commission_bps='1', slippage_bps='5', fixed_per_fill='0'),
         dict(id='adverse', commission_bps='5', slippage_bps='20', fixed_per_fill='0')]
HYPOTHESES = [dict(id='rule', family='ARITHMETIC_FIXTURE', parameter=1)]
UTC = timezone.utc


def day_time(day):
    return datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=UTC)


def fixture_study(hypotheses=HYPOTHESES):
    days = tuple((date(2000, 1, 1) + timedelta(days=i)).isoformat() for i in range(323))
    train, validation, oos = (Span(days[a], days[b]) for a, b in [(0, 125), (128, 190), (193, 322)])
    plan = Reservation((Fold(train, validation),), oos, 1, 1, day_time(days[0]) - timedelta(days=1),
                       day_time(days[-1]) + timedelta(days=1))
    study = Study(days, ('TEST_ONLY:asset',), (), (), Span(days[0], days[-1]), plan, True, True,
                  digest('fixture-block-assumptions'), digest('fixture-hypotheses-controls-and-calendar'))
    return replace(study, reservation=replace(plan, locked_design_hash=search_design_hash(hypotheses, COSTS, study)))


def fixture_grid(study, hypotheses=HYPOTHESES):
    size = len(study.sessions)
    # Numeric test vectors with known signs, arbitrary test units and flat boundaries.
    positions = tuple(0 if i in (127, 192) else 1 for i in range(size))
    rising = TrialPath('COMPLETED', 'ARITHMETIC_FIXTURE', D(100), tuple(D(101 + i) for i in range(size)), positions)
    constant = TrialPath('COMPLETED', 'ARITHMETIC_FIXTURE', D(100), (D(100),) * size, (0,) * size)
    paths = {(v['id'], cost['id']): rising for v in hypotheses for cost in COSTS}
    paths.update({(control, cost['id']): constant for control in POLICY.benchmark_ids for cost in COSTS})
    return paths


def select(study, paths=None, hypotheses=HYPOTHESES):
    return validate_search(hypotheses, COSTS, paths or fixture_grid(study, hypotheses), study)


def test_eligible_arithmetic_vectors_only_go_to_review():
    study = fixture_study()
    result = select(study)
    assert result['temporal_reasons'] == []
    assert result['decision'] == dict(status='CANDIDATES_FOR_REVIEW', candidate_ids=['rule'],
                                      next_action='REVIEW', orders_enabled=False, execution_ready=False)
    assert D(result['hypotheses'][0]['family_adjusted_p']) == D(1) / 8192
    assert json.loads(json.dumps(result))['reservation']['locked_design_hash'] == study.reservation.locked_design_hash


def test_economic_pass_in_reused_period_cannot_be_promoted_even_after_rename():
    study = fixture_study()
    exposure = Exposure('earlier-campaign-with-another-name', ('original-listing',), study.reservation.oos)
    study = replace(study, ancestor_instruments=('original-listing',), history=(exposure,))
    # Even a design freshly and correctly registered under the new name inherits the exposure.
    study = replace(study, reservation=replace(study.reservation, locked_design_hash=search_design_hash(HYPOTHESES, COSTS, study)))
    result = select(study)
    row = result['hypotheses'][0]
    assert row['economic_screen_passed'] and not row['selected']
    assert row['statistical_evidence'] == 'INSUFFICIENT_EVIDENCE' and row['family_adjusted_p'] is None
    assert 'PRIOR_OR_INHERITED_EXPOSURE' in row['reasons']
    assert result['decision']['next_action'] == 'OBSERVE'


def test_warmup_and_training_exposure_outside_reserved_intervals_is_permitted():
    study = fixture_study()
    study = replace(study, history=(Exposure('previous', study.instruments, study.reservation.folds[0].train),
                                    Exposure('other', ('other-instrument',), study.reservation.oos)))
    assert temporal_checks(study)[0] == []


@pytest.mark.parametrize('mutation,reason', [
    ('overlap', 'TEMPORAL_OVERLAP_OR_EMBARGO'), ('purge', 'TEMPORAL_OVERLAP_OR_EMBARGO'),
    ('embargo', 'TEMPORAL_OVERLAP_OR_EMBARGO'), ('short_train', 'DEVELOPMENT_SAMPLE_TOO_SHORT'),
    ('short_validation', 'DEVELOPMENT_SAMPLE_TOO_SHORT'), ('short_oos', 'OOS_SAMPLE_TOO_SHORT'),
    ('first_access', 'RESERVATION_CHRONOLOGY_INVALID'), ('late_plan', 'RESERVATION_CHRONOLOGY_INVALID'),
    ('missing_folds', 'MISSING_DEVELOPMENT_FOLDS'), ('outside', 'PARTITION_OUTSIDE_CALENDAR'),
    ('unknown_pit', 'POINT_IN_TIME_NOT_ESTABLISHED'), ('missing_inventory', 'EXPOSURE_INVENTORY_NOT_CERTIFIED'),
    ('no_assumptions', 'BLOCK_SIGN_ASSUMPTIONS_UNVERIFIED'), ('no_oos', 'NO_RESERVED_OUT_OF_SAMPLE'),
    ('unlocked', 'REGISTERED_DESIGN_MISMATCH'), ('other_protocol', 'REGISTERED_DESIGN_MISMATCH'),
])
def test_unsafe_or_insufficient_evidence_has_no_significance(mutation, reason):
    s = fixture_study()
    d, r = s.sessions, s.reservation
    f = r.folds[0]
    changes = {
        'overlap': replace(r, oos=Span(d[190], d[-1])), 'purge': replace(r, purge_sessions=2),
        'embargo': replace(r, embargo_sessions=2), 'short_train': replace(r, folds=(replace(f, train=Span(d[1], d[125])),)),
        'short_validation': replace(r, folds=(replace(f, validation=Span(d[129], d[190])),)),
        'short_oos': replace(r, oos=Span(d[198], d[-1])),
        'first_access': replace(r, first_oos_access_at=day_time(d[-2])),
        'late_plan': replace(r, locked_at=day_time(f.validation.first)), 'missing_folds': replace(r, folds=()),
        'outside': replace(r, oos=Span(d[-3], '2002-01-01')), 'unlocked': replace(r, locked_design_hash=None),
        'no_oos': None,
    }
    if mutation in changes:
        s = replace(s, reservation=changes[mutation])
    else:
        s = replace(s, **{'other_protocol': {'search_protocol_ref': digest('different')},
                          'unknown_pit': {'point_in_time': False}, 'missing_inventory': {'exposure_inventory_complete': False},
                          'no_assumptions': {'block_assumptions_ref': None}}[mutation])
    row = select(s)['hypotheses'][0]
    assert reason in row['reasons'] and row['family_adjusted_p'] is None
    assert not row['selected'] and not row['test_details']


def test_walk_forward_rejects_reused_validation_fold_and_accepts_ordered_folds():
    s = fixture_study()
    d = tuple((date(2000, 1, 1) + timedelta(days=i)).isoformat() for i in range(403))
    second = Fold(Span(d[0], d[190]), Span(d[193], d[255]))
    r = replace(s.reservation, folds=(*s.reservation.folds, second), oos=Span(d[259], d[402]),
                first_oos_access_at=day_time(d[402]) + timedelta(days=1))
    s = replace(s, sessions=d, evaluation=Span(d[0], d[-1]), reservation=r)
    assert temporal_checks(s)[0] == []
    s = replace(s, reservation=replace(r, folds=(r.folds[0], r.folds[0])))
    assert 'TEMPORAL_OVERLAP_OR_EMBARGO' in temporal_checks(s)[0]


def test_ties_are_not_wins_and_short_tail_is_not_an_extra_block():
    nav = (D(100),) * 129
    p, stats = block_sign_test(nav, nav, D(100), 0, 128)
    assert p == 1 and stats == dict(blocks=12, wins=0, unused_tail_sessions=9)
    with pytest.raises(ValueError, match='TOO_SHORT'):
        block_sign_test(nav, nav, D(100), 0, 118)


def test_cost_stress_and_both_benchmarks_are_binding():
    s = fixture_study()
    paths = fixture_grid(s)
    paths['buy_hold', 'adverse'] = paths['rule', 'adverse']
    row = select(s, paths)['hypotheses'][0]
    assert 'NET_RETURN_NOT_ABOVE_BUY_HOLD' in row['reasons'] and row['family_adjusted_p'] == '1'
    assert not row['economic_screen_passed'] and not row['selected']


def test_stress_scenario_must_be_at_least_as_expensive():
    s = fixture_study()
    with pytest.raises(ValueError, match='INVALID_STRESS_COSTS'):
        validate_search(HYPOTHESES, [COSTS[0], dict(COSTS[0], id='adverse')], fixture_grid(s), s)
    changed = [COSTS[0], dict(COSTS[1], slippage_bps='21')]
    r = validate_search(HYPOTHESES, changed, fixture_grid(s), s)
    assert 'REGISTERED_DESIGN_MISMATCH' in r['temporal_reasons']


def test_one_failed_variant_stays_in_denominator_and_control_failure_is_distinct():
    hs = [*HYPOTHESES, dict(id='failed', family='ARITHMETIC_FIXTURE')]
    s = fixture_study(hs)
    paths = fixture_grid(s, hs)
    paths['failed', 'adverse'] = TrialPath('FAILED', 'DEADLINE')
    result = select(s, paths, hs)
    assert result['search']['trial_states'] == dict(COMPLETED=7, FAILED=1)
    assert D(result['hypotheses'][0]['family_adjusted_p']) == D(2) / 8192
    assert 'STRATEGY_TRIAL_FAILED' in result['hypotheses'][1]['reasons']
    paths['cash', 'base'] = TrialPath('REJECTED', 'REJECTED_CONTROL')
    result = select(s, paths, hs)
    assert result['decision']['status'] == 'EVIDENCE_INCOMPLETE'
    assert all(h['family_adjusted_p'] is None for h in result['hypotheses'])


def test_entire_search_of_500_variants_counts_as_500_hypotheses_and_1004_trials():
    hs = [dict(id=f'fixture-{i}', family='ARITHMETIC_FIXTURE', parameter=i) for i in range(500)]
    s = fixture_study(hs)
    result = select(s, hypotheses=hs)
    assert result['search']['trial_states'] == {'COMPLETED': 1004}
    assert result['search']['hypotheses'] == 500
    family = result['family_diagnostics']['ARITHMETIC_FIXTURE']
    assert family['planned'] == 500 and family['economic_passes'] == 500
    bounds = family['net_return_ranges']['adverse']['oos']
    assert bounds['observed'] == 500 and bounds['minimum'] == bounds['maximum']
    assert all(h['economic_screen_passed'] and D(h['family_adjusted_p']) == D(500) / 8192 for h in result['hypotheses'])
    assert result['decision']['status'] == 'NO_CANDIDATES'


def test_identical_exposure_and_completed_variants_keep_one_review_slot():
    hs = [*HYPOTHESES, dict(id='renamed', family='ARITHMETIC_FIXTURE')]
    r = select(fixture_study(hs), hypotheses=hs)
    assert r['search']['distinct_position_paths'] == 1 and r['decision']['candidate_ids'] == ['rule']
    assert 'DUPLICATE_EXPOSURE_PATH' in r['hypotheses'][1]['reasons']


@pytest.mark.parametrize('fault,reason', [('missing', 'GRID'), ('extra', 'GRID'), ('running', 'NONTERMINAL'),
    ('short', 'UNALIGNED'), ('short_positions', 'UNALIGNED'), ('nav_nan', 'UNALIGNED'),
    ('negative_equity', 'UNALIGNED'), ('different_capital', 'INCOMPARABLE'), ('duplicate_days', 'CALENDAR')])
def test_invalid_campaign_is_not_an_ordinary_rejection(fault, reason):
    s = fixture_study()
    paths = fixture_grid(s)
    k = ('rule', 'base')
    p = paths[k]
    if fault == 'missing':
        del paths[k]
    elif fault == 'extra':
        paths['not_declared', 'base'] = p
    elif fault == 'duplicate_days':
        s = replace(s, sessions=(s.sessions[0], *s.sessions))
    else:
        paths[k] = replace(p, **{'running': {'state': 'RUNNING'}, 'short': {'equity': p.equity[:-1]},
            'short_positions': {'positions': p.positions[:-1]}, 'nav_nan': {'equity': (D('NaN'), *p.equity[1:])},
            'negative_equity': {'equity': (-D(1), *p.equity[1:])},
            'different_capital': {'initial': D(99)}}[fault])
    with pytest.raises(ValueError, match=reason):
        select(s, paths)


def test_carry_across_embargo_makes_statistic_unavailable():
    s = fixture_study()
    paths = fixture_grid(s)
    k = ('rule', 'base')
    paths[k] = replace(paths[k], positions=(1,) * len(s.sessions))
    row = select(s, paths)['hypotheses'][0]
    assert 'POSITION_CARRIED_INTO_RESERVED_WINDOW' in row['reasons']
    assert row['family_adjusted_p'] is None and not row['selected']

"""The B4 author receives structural information. The optional pilot has its own engineering trace."""
from copy import deepcopy
import json
import pytest

from app.proposer_view import proposer_view
from scripts.probe_quant_search import LAB, freeze, inspect_trace, sha, worker_slot


def dossier():
    return dict(search_protocol_ref='a'*64, source=dict(universe_hash='b'*64, dataset_hash='private'),
                warmup=dict(first='2024-12-30'), evaluation=dict(last='2025-12-31'),
                hypotheses=[dict(id='sma20', family='SMA_LONG_CASH', lookback=20, reasons=['PRIVATE']),
                            dict(id='sma60', family='SMA_LONG_CASH', lookback=60)],
                trials=[dict(result_hash='PRIVATE')], decision=dict(status='NO_CANDIDATES'))


def test_author_view_is_invariant_to_outcomes_and_names():
    first = dossier()
    other = deepcopy(first)
    other.update(trials=[], decision=dict(status='CANDIDATES_FOR_REVIEW'))
    other['hypotheses'].reverse()
    for h in other['hypotheses']:
        h.update(id='PRIVATE', mechanism='PRIVATE', position_signature='PRIVATE', selected=True, family_adjusted_p='0.001')
    assert proposer_view(first) == proposer_view(other)
    view = proposer_view(other)
    assert 'PRIVATE' not in json.dumps(view)
    assert set(view) == {'version', 'protocol', 'universe', 'observed_period', 'previously_registered'}
    assert [h['lookback'] for h in view['previously_registered']] == [20, 60]


@pytest.mark.parametrize('mutation', [dict(family='UNSUPPORTED'), dict(lookback=True), dict(lookback=300)])
def test_proposer_projection_requires_a_recognized_structure(mutation):
    data = dossier()
    data['hypotheses'][0].update(mutation)
    with pytest.raises(ValueError, match='PROPOSER_SCHEMA'):
        proposer_view(data)


def trace():
    plan = dict(attempt_budget=3, development_folds=2, family='SMA_LONG_CASH', lookback=[4, 131])
    events = [dict(event='START', protocol_sha256=sha((LAB / 'pilot_protocol.json').read_bytes()))]
    for i, window in enumerate([5, 8, 5]):
        events.append(dict(event='REGISTERED', attempt=i, family=plan['family'], lookback=window))
        events.append(dict(event='FINISHED', attempt=i, state='PRUNED' if window == 8 else 'COMPLETE',
                           development_excess=['-1'] if window == 8 else ['1', '1']))
    events.append(dict(event='SEARCH_CLOSED', attempts=3, unique_parameters=2))
    events.append(dict(event='SHADOW_AUDIT', lookback=8, development_excess=['-1','5'], full_development_excess='2'))
    events.append(dict(event='SUMMARY', purpose='ENGINEERING_ONLY', attempts=3, states={'COMPLETE': 2, 'PRUNED': 1},
                       unique_parameters=2, repeated_proposals=1, search_fold_calculations=3, logical_fold_reports=5,
                       avoided_during_search=1, shadow_fold_calculations=1, full_unique_fold_calculations=4,
                       exclusively_pruned_parameters=1, pruned_strictly_better_than_best_completed=1,
                       execution_ready=False, real_trials=0, reserved_oos_sessions=0))
    return plan, events


def encoded(events):
    return b'\n'.join(json.dumps(e).encode() for e in events)


def test_shadow_audit_counts_pruned_winner_and_repeated_proposals():
    plan, events = trace()
    result = inspect_trace(encoded(events), plan)
    assert result['pruned_strictly_better_than_best_completed'] == 1
    assert result['repeated_proposals'] == 1 and result['execution_ready'] is False


@pytest.mark.parametrize('case', ['registration', 'lost', 'cutoff', 'score', 'repeated', 'count', 'shadow',
                                  'winner', 'live', 'missing_audit', 'oos', 'wrong_protocol'])
def test_trace_reconciliation_blocks_invalid_experiments(case):
    plan, e = trace()
    if case == 'registration':
        e[1], e[2] = e[2], e[1]
    elif case == 'lost':
        e.pop(4)
    elif case == 'cutoff':
        e[4]['development_excess'] = ['-1', '5']
    elif case == 'score':
        e[6]['development_excess'] = ['1','3']
    elif case == 'repeated':
        e[-1]['repeated_proposals'] = 0
    elif case == 'count':
        e[-1]['full_unique_fold_calculations'] = 9
    elif case == 'shadow':
        e[-2]['development_excess'] = ['-2', '6']
    elif case == 'winner':
        e[-1]['pruned_strictly_better_than_best_completed'] = 0
    elif case == 'live':
        e[-1]['execution_ready'] = True
    elif case == 'missing_audit':
        e.pop(-2)
    elif case == 'oos':
        e[-1]['reserved_oos_sessions'] = 192
    else:
        e[0]['protocol_sha256'] = 'c'*64
    with pytest.raises((ValueError, KeyError)):
        inspect_trace(encoded(e), plan)


def test_one_worker_released_after_failure_and_immutable_publication(tmp_path):
    with pytest.raises(LookupError):
        with worker_slot(tmp_path):
            with pytest.raises(RuntimeError, match='PILOT_WORKER_BUSY'):
                with worker_slot(tmp_path):
                    pytest.fail('second worker admitted')
            raise LookupError()
    with worker_slot(tmp_path):
        target = tmp_path/'result.json'
        freeze(target, b'one')
        freeze(target, b'one')
        with pytest.raises(ValueError, match='CONFLICT'):
            freeze(target, b'two')

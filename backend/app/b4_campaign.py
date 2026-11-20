"""Read-only adapter for the sealed B3.2 campaign. Never executes a trial."""
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from pathlib import Path
import sqlite3

from app.admission_contracts import fingerprint, instant, validate_candidate
from app.b32_review import PROTOCOL_PATH, PROTOCOL_SHA256, REVIEW_SHA256, checked_file, reviewed_bundle
from app.dataset_manifests import ManifestStore, canonical
from app.quant_real import planned_configs
from app.quant_store import code_hash, digest
from app.strategy_validation import TrialPath, performance, validate_search
from app.validation_policy import Exposure, Span, Study


RUN = 'b32-brkb-20261119-v1'
MANIFEST = '7d80ac5f3ea55193859398c84394bb69e1649e7cb055369129a933aa73114715'
CAMPAIGN = '53b1a415c056094a2299f8e730692a8561d4c44a9cf8b1251de451b0575ffcea'
SUMMARY_FIELDS = ('return_fraction', 'max_drawdown_fraction', 'commission', 'slippage_cost',
                  'final_cash', 'final_shares', 'final_equity')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def implementation_hash():
    folder = Path(__file__).parent
    names = ('b4_campaign.py', 'strategy_validation.py', 'validation_policy.py', 'validation_store.py')
    return digest({name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in names})


def campaign_receipt(storage):
    path = Path(storage.output_root) / 'quant-campaigns' / RUN / (CAMPAIGN + '.json')
    require(path.resolve() == path.absolute(), 'CAMPAIGN_PATH_REDIRECTED')
    with path.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, 'CAMPAIGN_REPORT_TOO_LARGE')
    report = json.loads(raw)
    require(digest(report) == CAMPAIGN and canonical(report) == raw, 'CAMPAIGN_REPORT_INTEGRITY')
    return report


def ledger_events(db, prefix):
    histories = defaultdict(list)
    for event in db.execute('SELECT * FROM quant_trial_events WHERE substr(trial_id,1,?)=? ORDER BY sequence',
                            (len(prefix), prefix)):
        histories[event['trial_id']].append(dict(event))
    return histories


def verify_registration(row, events):
    require(events and events[0]['state'] == 'QUEUED' and events[0]['at'] == row['created_at']
            and events[0]['attempt'] == 0 and events[-1]['state'] == row['state']
            and events[-1]['at'] == row['updated_at'] and events[-1]['reason'] == row['reason']
            and events[-1]['attempt'] == row['attempt'], 'TRIAL_EVENT_CHAIN_MISMATCH')
    times = [instant(e['at']) for e in events]
    require(times == sorted(times) and any(e['state'] == 'RUNNING' for e in events),
            'TRIAL_EVENT_CHRONOLOGY_INVALID')
    previous = events[0]
    transitions = {'QUEUED': {'RUNNING'}, 'RUNNING': {'COMPLETED', 'FAILED', 'REJECTED', 'INTERRUPTED'},
                   'INTERRUPTED': {'RUNNING', 'FAILED'}}
    for event in events[1:]:
        require(event['state'] in transitions.get(previous['state'], set())
                and event['attempt'] == previous['attempt'] + int(event['state'] == 'RUNNING'),
                'TRIAL_EVENT_CHAIN_MISMATCH')
        previous = event


def audit_path(row, result, config, calendar, warmup):
    state, reason = row['state'], row['reason']
    if state != 'COMPLETED':
        require(result is None and row['result_hash'] is None, 'NONCOMPLETED_RESULT_CONFLICT')
        return TrialPath(state, reason), {}
    require(isinstance(result, dict) and digest(result) == row['result_hash'], 'TRIAL_RESULT_INTEGRITY')
    family = config['genome']['family']
    require(result['kind'] == 'MARKET_RETROSPECTIVE' and result['acceptance'] == 'EXPLORATORY_ONLY'
            and result['manifest_id'] == MANIFEST and result['protocol_sha256'] == PROTOCOL_SHA256
            and result['family'] == family and result['unit'] == config['unit']
            and result['execution_ready'] is False and result['oos_reserved'] is False
            and result['point_in_time_claim'] is False and result['warmup_sessions'] == warmup
            and result['evaluation_sessions'] == len(calendar) - warmup
            and instant(result['evaluation_start']) == instant(calendar[warmup]['open']),
            'TRIAL_SCOPE_MISMATCH')
    decisions, curve, fills = (result[key] for key in ('decisions', 'curve', 'fills'))
    require(len(decisions) == len(curve) == len(calendar), 'UNALIGNED_SESSION_SERIES')
    initial = Decimal(config['initial_cash'])
    require(Decimal(result['initial_cash']) == initial, 'STARTING_CAPITAL_MISMATCH')
    expected_fills, equity, positions = [], [], []
    for idx, (day, decision, mark) in enumerate(zip(calendar, decisions, curve)):
        opened, closed = instant(day['open']), instant(day['close'])
        require(instant(decision['execution_at']) == opened and instant(mark['at']) == closed
                and opened < closed and (not idx or instant(calendar[idx - 1]['close']) < opened),
                'SESSION_TIMING_MISMATCH')
        known = decision['known_at']
        if idx < warmup:
            require(known is None and decision['signal'] == 'WARMUP' and decision['target'] == 0
                    and decision['outcome'] == 'HOLD' and mark['shares'] == 0
                    and Decimal(mark['equity']) == Decimal(mark['cash']) == initial, 'WARMUP_LEAK')
        elif family == 'SMA_LONG_CASH':
            require(known is not None and instant(known) == instant(calendar[idx - 1]['close'])
                    and instant(known) < opened, 'LOOKAHEAD_OR_UNKNOWN_SIGNAL_TIME')
        else:
            signal = 'CASH_CONTROL' if family == 'CASH' else 'PRECOMMITTED_BUY_HOLD'
            require(known is None and decision['signal'] == signal, 'CONTROL_TIMING_MISMATCH')
        if decision['outcome'] in ('BUY', 'SELL'):
            expected_fills.append((opened, known, decision['outcome']))
        equity.append(Decimal(mark['equity']))
        positions.append(mark['shares'])
    require([(instant(f['at']), f['known_at'], f['side']) for f in fills] == expected_fills,
            'FILL_TIMING_OR_DECISION_MISMATCH')
    path = TrialPath(state, reason, initial, tuple(equity), tuple(positions))
    net, drawdown = performance(path, warmup, len(calendar) - 1)
    require(net == Decimal(result['return_fraction']) and drawdown == Decimal(result['max_drawdown_fraction'])
            and equity[-1] == Decimal(result['final_equity']), 'NAV_AGGREGATE_MISMATCH')
    return path, dict(**{k: result[k] for k in SUMMARY_FIELDS}, fill_count=len(fills),
                      gross_turnover_over_initial=str(sum((Decimal(f['price']) * f['quantity'] for f in fills),
                                                          Decimal(0)) / initial))


def instrument_keys(candidate):
    return ('listing:' + candidate['listing_id'], 'identity:' + candidate['identity_hash'],
            'symbol-venue:' + candidate['symbol'] + '@' + candidate['venue'])


def exposure_inventory(db, subject):
    matched, refs = [], []
    keys = set(instrument_keys(subject))
    # Collate by dataset and stable instrument identity across campaigns, even
    # if trial names, parameters or the dataset's own content hash changed.
    for row in db.execute("""
        SELECT d.hash, json_extract(d.payload,'$.candidate.listing_id') listing,
               json_extract(d.payload,'$.candidate.identity_hash') identity_hash,
               json_extract(d.payload,'$.candidate.symbol') symbol, json_extract(d.payload,'$.candidate.venue') venue,
               json_extract(d.payload,'$.candidate.start') first_day, json_extract(d.payload,'$.candidate.end') last_day,
               t.id FROM quant_datasets d JOIN quant_trials t ON t.dataset_hash=d.hash
        WHERE json_extract(d.payload,'$.candidate.domain')='MARKET_DATA' ORDER BY d.hash,t.id
    """):
        instruments = instrument_keys(dict(listing_id=row['listing'], identity_hash=row['identity_hash'],
                                          symbol=row['symbol'], venue=row['venue']))
        if keys.intersection(instruments):
            span = Exposure('quant-dataset:' + row['hash'], instruments, Span(row['first_day'], row['last_day']))
            if not matched or matched[-1] != span:
                matched.append(span)
            refs.append(row['id'])
    return tuple(matched), refs


def read_search(db, protocol, report, manifest, review):
    prefix = RUN + '.'
    grid = dict(planned_configs())
    events = ledger_events(db, prefix)
    trial_names = {prefix + name for name in grid}
    recorded = {r['id'] for r in db.execute('SELECT id FROM quant_trials WHERE substr(id,1,?)=?',
                                             (len(prefix), prefix))}
    require(recorded == trial_names, 'SEARCH_GRID_MISSING_OR_EXTRA_TRIALS')
    require(set(events) == trial_names, 'CAMPAIGN_EVENT_GRID_MISMATCH')
    starts = [e['sequence'] for chain in events.values() for e in chain if e['state'] == 'RUNNING']
    require(bool(starts), 'CAMPAIGN_NOT_STARTED')
    first_run = min(starts)
    require(all(chain[0]['sequence'] < first_run for chain in events.values()), 'GRID_REGISTERED_AFTER_START')
    archived = {t['name']: t for t in report['trials']}
    require(len(archived) == len(report['trials']) == protocol['planned_trial_count']
            and set(archived) == set(grid), 'SEALED_GRID_MISMATCH')
    data = db.execute('SELECT d.payload,d.hash FROM quant_datasets d JOIN quant_trials t ON d.hash=t.dataset_hash '
                      'WHERE t.id=?', (prefix + next(iter(grid)),)).fetchone()
    require(data is not None, 'CAMPAIGN_DATASET_MISSING')
    dataset = json.loads(data['payload'])
    require(digest(dataset) == data['hash'] and dataset['manifest_id'] == manifest['manifest_id']
            and dataset['protocol_sha256'] == PROTOCOL_SHA256 and dataset['kind'] == 'MARKET_RETROSPECTIVE',
            'DATASET_INTEGRITY')
    candidate = validate_candidate(dataset['candidate'])
    require(fingerprint(candidate) == manifest['candidate_hash'] == review['candidate_hash']
            and candidate['listing_id'] == protocol['candidate']['listing_id'], 'CANDIDATE_INTEGRITY')
    calendar = next(r['payload']['sessions'] for r in review['evidence']['records'] if r['kind'] == 'calendar')
    sessions = tuple(d['session'] for d in calendar)
    warmup = protocol['window']['common_warmup_sessions']
    require(sessions == tuple(b['session'] for b in candidate['bars'])
            and len(sessions) == protocol['window']['total_sessions'], 'CALENDAR_NOT_ALIGNED')
    history, exposure_trials = exposure_inventory(db, candidate)
    require(trial_names.issubset(exposure_trials), 'MISSING_INHERITED_EXPOSURE')
    study = Study(sessions, instrument_keys(candidate), (), history, Span(sessions[warmup], sessions[-1]),
                  search_protocol_ref=PROTOCOL_SHA256)
    paths, receipts = {}, {}
    engine_hash = code_hash()
    query = 'SELECT * FROM quant_trials WHERE substr(id,1,?)=? ORDER BY id'
    for row in db.execute(query, (len(prefix), prefix)):
        name = row['id'][len(prefix):]
        require(name in grid and name not in receipts, 'UNPLANNED_TRIAL')
        config = json.loads(row['config'])
        require(row['dataset_hash'] == data['hash'] and config == grid[name] and digest(config) == row['config_hash']
                and digest(dict(dataset=dataset, config=config)) == row['request_hash']
                and row['code_hash'] == engine_hash, 'TRIAL_INPUT_INTEGRITY')
        chain = events[row['id']]
        verify_registration(row, chain)
        result = json.loads(row['result']) if row['result'] is not None else None
        # Compare the full result digest and B3.2's independently sealed list of all ten outcomes.
        path, metrics = audit_path(row, result, config, calendar, warmup)
        runtime = json.loads(row['runtime'])
        require(runtime['seed'] == config['seed'] and (not result or runtime['engine'] == result['engine_version']),
                'TRIAL_RUNTIME_MISMATCH')
        old = archived[name]
        require(old['trial_id'] == row['id'] and old['state'] == path.state and old['reason'] == path.reason
                and old['result_hash'] == row['result_hash']
                and all(old[key] == metrics.get(key) for key in SUMMARY_FIELDS)
                and old['fill_count'] == metrics.get('fill_count', 0), 'SEALED_TRIAL_MISMATCH')
        paths[tuple(name.rsplit('-', 1))] = path
        receipts[name] = dict(trial_id=row['id'], config_hash=row['config_hash'], request_hash=row['request_hash'],
                              result_hash=row['result_hash'], engine_hash=row['code_hash'], state=path.state,
                              reason=path.reason, attempts=row['attempt'], events_hash=digest(chain),
                              event_count=len(chain), registered_at=row['created_at'], finished_at=row['updated_at'],
                              runtime=runtime, metrics=metrics)
    hypotheses = [dict(**v, mechanism=grid[v['id'] + '-base']['genome']['mechanism'],
                       falsification=grid[v['id'] + '-base']['genome']['falsification'])
                  for v in protocol['variants'] if v['family'] not in {'CASH', 'BUY_HOLD'}]
    selection = validate_search(hypotheses, protocol['cost_scenarios'], paths, study)
    require({h['id']: h['economic_screen_passed'] for h in selection['hypotheses']} == report['exploratory_support'],
            'EXPLORATORY_DECISION_MISMATCH')
    return dict(version='b4-validation-dossier-v1', implementation_hash=implementation_hash(),
                run_id=RUN, source=dict(campaign_hash=CAMPAIGN, protocol_sha256=PROTOCOL_SHA256,
                    manifest_id=MANIFEST, review_sha256=REVIEW_SHA256, dataset_hash=data['hash'],
                    candidate_hash=manifest['candidate_hash'], universe_hash=candidate['universe_hash'],
                    provider=candidate['provider'], feed=candidate['feed'], symbol=candidate['symbol'],
                    unit=candidate['currency'], review_expires_at=manifest['scope']['review_expires_at'],
                    limitations=protocol['limitations']),
                costs=protocol['cost_scenarios'], warmup=dict(first=sessions[0], last=sessions[warmup - 1],
                    sessions=warmup), evaluated_sessions=len(sessions) - warmup, reserved_oos_sessions=0,
                exposure_inventory=dict(scope='LOCAL_QUANT_REGISTRY_MATCHING_INSTRUMENT',
                    trial_ids=exposure_trials, calendar_hash=digest(calendar)),
                trials=list(receipts.values()), **selection)


def validate_archived_campaign(db_path, storage, now=None):
    manifest = ManifestStore(storage).read(MANIFEST)
    report = campaign_receipt(storage)
    review = reviewed_bundle()
    protocol = json.loads(checked_file(PROTOCOL_PATH, PROTOCOL_SHA256))
    now = now or datetime.now(timezone.utc)
    require(now.utcoffset() is not None and datetime.fromisoformat(manifest['as_of']) <= now
            <= datetime.fromisoformat(manifest['scope']['review_expires_at']), 'DATASET_REVIEW_EXPIRED_OR_CLOCK_INVALID')
    require(manifest['readiness']['backtest'] == 'BACKTEST_READY_EXPLORATORY'
            and manifest['scope']['oos_reserved'] is False and not manifest['scope']['point_in_time_claim']
            and report['run_id'] == RUN and report['manifest_id'] == MANIFEST
            and report['protocol_sha256'] == PROTOCOL_SHA256, 'SEALED_CAMPAIGN_SCOPE_MISMATCH')
    with closing(sqlite3.connect(Path(db_path).resolve().as_uri() + '?mode=ro', uri=True)) as db, localcontext() as ctx:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        ctx.prec, ctx.rounding = 40, ROUND_HALF_UP
        return read_search(db, protocol, report, manifest, review)

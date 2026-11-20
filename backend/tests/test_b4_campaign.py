"""End-to-end B4 against a temporary B3 registry and sealed fixture receipts."""
from contextlib import closing
from datetime import timedelta
import json
import shutil
import sqlite3

import pytest
from sqlalchemy import create_engine
from app import b4_campaign as b4
from app.b32_review import PROTOCOL_PATH, PROTOCOL_SHA256, checked_file
from app.database import Base
from app.dataset_manifests import ManifestStore, canonical
from app.quant_real import planned_configs
from app.quant_store import DATASETS, EVENTS, TRIALS, TrialRegistry, digest
from app.storage_budget import StorageGovernor
from app.validation_store import ValidationStore
from test_quant_real import NOW, request


@pytest.fixture(scope='module')
def archived(tmp_path_factory):
    directory = tmp_path_factory.mktemp('b4-engineering')
    db = directory / 'fixture.db'
    engine = create_engine('sqlite:///' + db.as_posix())
    try:
        Base.metadata.create_all(engine, tables=[DATASETS, TRIALS, EVENTS])
        storage = StorageGovernor.for_engine(engine)
        with pytest.MonkeyPatch.context() as patch:
            dataset, evidence, manifest, _ = request(patch)
            ManifestStore(storage).publish(manifest)
            registry = TrialRegistry(engine, clock=lambda: NOW)
            run = 'b4-engineering-only'
            configs = planned_configs()
            for name, config in configs:
                registry.submit(run + '.' + name, dataset, config)
            receipts = []
            for name, _ in configs:
                row = registry.run(run + '.' + name)
                assert row['state'] == 'COMPLETED'
                result = row['result']
                receipts.append(dict(name=name, trial_id=row['id'], state=row['state'], reason=row['reason'],
                                     result_hash=row['result_hash'], fill_count=len(result['fills']),
                                     **{k: result[k] for k in b4.SUMMARY_FIELDS}))
        protocol = json.loads(checked_file(PROTOCOL_PATH, PROTOCOL_SHA256))
        protocol['candidate']['listing_id'] = dataset['candidate']['listing_id']
        report = dict(run_id=run, manifest_id=manifest['manifest_id'], protocol_sha256=PROTOCOL_SHA256,
                      trials=receipts, exploratory_support={name: False for name in ('sma20', 'sma40', 'sma60')})
        folder = storage.output_root / 'quant-campaigns' / run
        folder.mkdir(parents=True)
        campaign_hash = digest(report)
        (folder / (campaign_hash + '.json')).write_bytes(canonical(report))
        review = dict(candidate_hash=manifest['candidate_hash'], evidence=evidence)
        return db, storage, run, manifest, campaign_hash, protocol, review
    finally:
        engine.dispose()


@pytest.fixture
def package(archived, monkeypatch):
    db, storage, run, manifest, campaign, protocol, review = archived
    monkeypatch.setattr(b4, 'RUN', run)
    monkeypatch.setattr(b4, 'MANIFEST', manifest['manifest_id'])
    monkeypatch.setattr(b4, 'CAMPAIGN', campaign)
    monkeypatch.setattr(b4, 'checked_file', lambda *_: canonical(protocol))
    monkeypatch.setattr(b4, 'reviewed_bundle', lambda: review)
    return db, storage, run


def test_reproducible_private_read_only_handoff(package):
    db, storage, _ = package
    before = db.read_bytes()
    full = b4.validate_archived_campaign(db, storage, NOW)
    assert len(full['trials']) == 10 and full['search']['trial_states'] == dict(COMPLETED=10)
    assert full['search']['hypotheses'] == 3 and full['reserved_oos_sessions'] == 0
    assert full['decision']['status'] == 'NO_CANDIDATES'
    assert all(row['event_count'] == 3 for row in full['trials'])
    assert full['prior_exposure'][0]['period']['first'] == full['warmup']['first']
    assert full['prior_exposure'][0]['period']['last'] == full['evaluation']['last']
    store = ValidationStore(storage)
    first = store.publish(full)
    assert store.publish(b4.validate_archived_campaign(db, storage, NOW + timedelta(days=1))) == first
    assert store.read(first)['decision']['next_action'] == 'OBSERVE'
    assert db.read_bytes() == before and not any(k in store.path(first).read_bytes() for k in
                                                (b'"curve":', b'"bars":', b'"fills":', b'"reference_open":'))


@pytest.mark.parametrize('fault,reason', [
    ('result_hash', 'TRIAL_RESULT_INTEGRITY'), ('request_hash', 'TRIAL_INPUT_INTEGRITY'),
    ('missing_trial', 'SEARCH_GRID'), ('late_registration', 'GRID_REGISTERED_AFTER_START'),
    ('missing_event', 'EVENT_CHAIN'), ('event_attempt', 'EVENT_CHAIN'), ('extra', 'SEARCH_GRID'),
    ('future_signal', 'LOOKAHEAD'), ('null_signal', 'LOOKAHEAD'), ('warmup_fill', 'WARMUP_LEAK'),
    ('curve_day', 'SESSION_TIMING'), ('missing_day', 'UNALIGNED_SESSION'), ('fill_shift', 'FILL_TIMING'),
    ('changed_net', 'NAV_AGGREGATE'), ('changed_summary', 'SEALED_TRIAL'), ('wrong_runtime', 'TRIAL_RUNTIME'),
])
def test_tampered_source_fails_closed(package, tmp_path, fault, reason):
    origin, storage, run = package
    db = tmp_path / 'engineering-copy.db'
    shutil.copyfile(origin, db)
    trial_id = run + ('.buy_hold-base' if fault == 'fill_shift' else '.sma20-base')
    with closing(sqlite3.connect(db)) as connection, connection:
        if fault in ('result_hash', 'request_hash'):
            connection.execute('UPDATE quant_trials SET ' + fault + "='bad' WHERE id=?", (trial_id,))
        elif fault == 'missing_trial':
            connection.execute('DELETE FROM quant_trials WHERE id=?', (trial_id,))
        elif fault == 'late_registration':
            connection.execute("UPDATE quant_trial_events SET sequence=99 WHERE trial_id=? AND state='QUEUED'", (trial_id,))
        elif fault == 'missing_event':
            connection.execute("DELETE FROM quant_trial_events WHERE trial_id=? AND state='COMPLETED'", (trial_id,))
        elif fault == 'event_attempt':
            connection.execute("UPDATE quant_trial_events SET attempt=2 WHERE trial_id=? AND state='RUNNING'", (trial_id,))
        elif fault == 'extra':
            connection.execute("UPDATE quant_trials SET id=? WHERE id=?", (run + '.a-unplanned', run + '.sma60-base'))
        elif fault == 'wrong_runtime':
            connection.execute("UPDATE quant_trials SET runtime=json_set(runtime,'$.engine','unexpected') WHERE id=?", (trial_id,))
        else:
            r = json.loads(connection.execute('SELECT result FROM quant_trials WHERE id=?', (trial_id,)).fetchone()[0])
            if fault == 'future_signal':
                r['decisions'][70]['known_at'] = r['decisions'][70]['execution_at']
            elif fault == 'null_signal':
                r['decisions'][70]['known_at'] = None
            elif fault == 'warmup_fill':
                r['decisions'][59]['outcome'] = 'BUY'
            elif fault == 'curve_day':
                r['curve'][62]['at'] = r['curve'][63]['at']
            elif fault == 'missing_day':
                r['decisions'].pop()
            elif fault == 'fill_shift':
                r['fills'][0]['at'] = r['decisions'][65]['execution_at']
            elif fault == 'changed_net':
                r['return_fraction'] = '0.05'
            else:
                r['commission'] = '75.00'
            connection.execute('UPDATE quant_trials SET result=?, result_hash=? WHERE id=?',
                               (json.dumps(r), digest(r), trial_id))
    with pytest.raises(ValueError, match=reason):
        b4.validate_archived_campaign(db, storage, NOW)


def test_dataset_exposure_follows_trials_into_another_campaign(package, tmp_path):
    source, storage, run = package
    db = tmp_path / 'exposure.db'
    shutil.copyfile(source, db)
    with closing(sqlite3.connect(db)) as connection, connection:
        columns = [r[1] for r in connection.execute('PRAGMA table_info(quant_trials)') if r[1] != 'id']
        cols = ','.join(columns)
        connection.execute(f'INSERT INTO quant_trials (id,{cols}) SELECT ?,{cols} FROM quant_trials WHERE id=?',
                           ('renamed-hypothesis', run + '.sma20-base'))
    result = b4.validate_archived_campaign(db, storage, NOW)
    assert len(result['trials']) == 10
    assert 'renamed-hypothesis' in result['exposure_inventory']['trial_ids']


def test_internal_review_expiry_blocks_new_calculations(package):
    db, storage, _ = package
    with pytest.raises(ValueError, match='REVIEW_EXPIRED'):
        b4.validate_archived_campaign(db, storage, NOW + timedelta(days=60))


def test_corrupt_private_artifact_cannot_be_read_or_silently_replaced(package, tmp_path):
    db, storage, _ = package
    dossier = b4.validate_archived_campaign(db, storage, NOW)
    store = ValidationStore(StorageGovernor(tmp_path / 'data', tmp_path / 'output'))
    ident = store.publish(dossier)
    edited = json.loads(store.path(ident).read_bytes())
    edited['trials'][0]['events_hash'] = '0' * 64
    store.path(ident).write_bytes(canonical(edited))
    with pytest.raises(ValueError, match='DOSSIER_INTEGRITY'):
        store.read(ident)
    with pytest.raises(ValueError, match='DOSSIER_INTEGRITY'):
        store.publish(dossier)
    with pytest.raises(ValueError, match='INVALID_DOSSIER_ID'):
        store.read('../invalid')


def test_order_capability_is_never_a_valid_b4_handoff(package):
    db, storage, _ = package
    report = b4.validate_archived_campaign(db, storage, NOW)
    report['decision']['orders_enabled'] = True
    with pytest.raises(ValueError, match='INVALID_VALIDATION_HANDOFF'):
        ValidationStore.verify(report)

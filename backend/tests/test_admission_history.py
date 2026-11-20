"""D3 source integrity tests; isolated synthetic SQLite and no external network."""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine, select, update
from app.database import Base
from app.history_service import HistoryService, fixture_request
from app.history_store import BATCHES, UNITS, SNAPSHOTS
from app.admission_history import load_history_candidate, batch_targets
from app.data_identity import fingerprint

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


class Guard:
    @contextmanager
    def admission(self, **kwargs):
        yield


@pytest.fixture
def source(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'isolated.db'))
    Base.metadata.create_all(engine)
    service = HistoryService(engine, storage=Guard(), clock=lambda: NOW)
    service.enqueue('source-test', fixture_request(2))
    for _ in range(5):
        if not service.step('source-test')['worked']:
            break
    yield engine
    engine.dispose()


def load(engine, cutoff=NOW):
    return load_history_candidate(engine, 'source-test', 'TEST_00000', cutoff)


def test_complete_windows_read_only_and_pagination(source):
    with source.connect() as c:
        before = {t.name: list(c.execute(select(t))) for t in Base.metadata.sorted_tables}
    result = load(source)
    assert not result['source_errors'] and len(result['bars']) == 33 and len(result['sources']) == 2
    assert result['domain'] == 'SYNTHETIC_TEST'
    assert batch_targets(source, 'source-test', offset=1, limit=1) == (['TEST_00001'], 2)
    with source.connect() as c:
        assert before == {t.name: list(c.execute(select(t))) for t in Base.metadata.sorted_tables}


def test_missing_window_is_not_silently_skipped(source):
    with source.begin() as c:
        c.execute(UNITS.delete().where(UNITS.c.sequence == 1))
    assert 'WINDOW_COUNT_MISMATCH' in load(source)['source_errors']


def test_failed_window_cannot_be_replaced_by_only_successes(source):
    with source.begin() as c:
        c.execute(update(UNITS).where(UNITS.c.sequence == 1).values(state='FAILED'))
    assert 'WINDOW_NOT_COMPLETE' in load(source)['source_errors']


def test_tampered_snapshot_and_matching_rehash_wrong_request(source):
    with source.begin() as c:
        row = c.execute(select(SNAPSHOTS)).mappings().first()
        bad = dict(row['payload'], feed='fake')
        c.execute(update(SNAPSHOTS).where(SNAPSHOTS.c.hash == row['hash']).values(payload=bad))
    assert 'SNAPSHOT_HASH_MISMATCH' in load(source)['source_errors']
    with source.begin() as c:
        bad = dict(row['payload'], request=dict(row['payload']['request'], listing_id='TEST_OTHER'))
        digest = fingerprint(bad)
        c.execute(SNAPSHOTS.insert().values(hash=digest, payload=bad))
        c.execute(update(UNITS).where(UNITS.c.snapshot_hash == row['hash']).values(snapshot_hash=digest))
    assert 'SNAPSHOT_REQUEST_MISMATCH' in load(source)['source_errors']


def test_cutoff_never_accepts_later_receipts(source):
    result = load(source, NOW - timedelta(seconds=1))
    assert 'RECEIPT_OUTSIDE_CUTOFF' in result['source_errors']
    assert result['sources'] == [] and result['bars'] == []


def test_untrusted_coverage_boolean_does_not_change_candidate(source):
    before = load(source)
    with source.begin() as c:
        c.execute(update(UNITS).values(coverage={'backtest_ready': True, 'execution_ready': True}))
    assert load(source) == before


def test_later_normalization_cannot_backdate_receipt(source):
    with source.begin() as c:
        c.execute(update(UNITS).values(updated_at=(NOW+timedelta(seconds=1)).isoformat()))
    result = load(source)
    assert 'RECEIPT_OUTSIDE_CUTOFF' in result['source_errors']
    assert result['bars'] == [] and result['sources'] == []


def test_batch_hash_and_missing_listing_are_detected(source):
    with source.begin() as c:
        c.execute(update(BATCHES).values(request_hash='0'*64))
    assert 'BATCH_HASH_MISMATCH' in load(source)['source_errors']
    with pytest.raises(KeyError):
        load_history_candidate(source, 'source-test', 'TEST_NONEXISTENT', NOW)


def test_invalid_page_and_cutoff_rejected(source):
    with pytest.raises(ValueError):
        batch_targets(source, 'source-test', limit=101)
    with pytest.raises(ValueError):
        load(source, NOW.replace(tzinfo=None))

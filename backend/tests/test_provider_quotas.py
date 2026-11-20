"""Shared quota regressions. Synthetic settings/responses; no external network."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.alpaca_quota import reserve as reserve_alpaca, backoff as backoff_alpaca
from app.data_catalog import CATALOG
from app.data_config import DataSettings
from app.data_contracts import DataResult
from app.data_http import FetchError
from app.data_service import DataService, cache_key
from app.database import DataQuota, DataRecord
from app.sec_quota import reserve as reserve_sec, backoff as backoff_sec


NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


class FakeHttp:
    real = False

    def __init__(self, before_fetch=None):
        self.calls = 0
        self.before_fetch = before_fetch

    def fetch(self, source):
        self.calls += 1
        if self.before_fetch:
            self.before_fetch(source)
        return b'{}', 200


@pytest.fixture
def quota_engine(tmp_path):
    engine = create_engine('sqlite:///' + (tmp_path / 'quotas.db').as_posix())
    DataQuota.__table__.create(engine)
    DataRecord.__table__.create(engine)
    yield engine
    engine.dispose()


def make_service(engine, monkeypatch, now, before_fetch=None):
    monkeypatch.setattr('app.data_service.parse', lambda *_: [])
    settings = DataSettings(_env_file=None, data_public_enabled=True,
                            sec_contact='JAIME TEST_ONLY test@example.test',
                            alpaca_api_key='TEST_ONLY', alpaca_secret_key='TEST_ONLY')
    http = FakeHttp(before_fetch)
    return DataService(engine, settings, http=http, clock=lambda: now[0]), http


def quota_state(engine, provider):
    with Session(engine) as session:
        row = session.get(DataQuota, provider)
        return None if row is None else (row.window_start, row.used, row.blocked_until, row.failures)


def test_quality_is_read_only_even_when_sec_and_alpaca_are_blocked(quota_engine, monkeypatch):
    with Session(quota_engine) as session, session.begin():
        for provider in ('SEC', 'ALPACA'):
            session.add(DataQuota(key=provider, window_start=NOW.isoformat(), used=9,
                                  blocked_until=(NOW + timedelta(minutes=5)).isoformat(), failures=2))
    before = {key: quota_state(quota_engine, key) for key in ('SEC', 'ALPACA')}
    statements = []
    event.listen(quota_engine, 'before_cursor_execute',
                 lambda _c, _cursor, statement, _params, _context, _many: statements.append(statement))
    data, http = make_service(quota_engine, monkeypatch, [NOW])
    for _ in range(2):
        result = data.quality()
        assert isinstance(result, dict) and len(result['sources']) == len(CATALOG)
        assert result['counts']['candidate_access_modes'] == len(CATALOG)
        assert next(row for row in result['sources'] if row['access_id'] == 'A09')['quota_used'] == 9
    assert http.calls == 0
    assert all(statement.lstrip().upper().startswith('SELECT') for statement in statements)
    assert before == {key: quota_state(quota_engine, key) for key in ('SEC', 'ALPACA')}


def test_quality_does_not_create_a_quota_for_an_unqueried_provider(quota_engine, monkeypatch):
    data, http = make_service(quota_engine, monkeypatch, [NOW])
    assert isinstance(data.quality(), dict)
    with Session(quota_engine) as session:
        assert list(session.scalars(select(DataQuota))) == []
    assert http.calls == 0


@pytest.mark.parametrize('source_id,provider,reserve', [
    ('A09', 'SEC', reserve_sec), ('B04', 'ALPACA', reserve_alpaca),
])
def test_legacy_and_worker_share_committed_budget_without_double_count_or_reset(
        quota_engine, monkeypatch, source_id, provider, reserve):
    # A preset's unrelated limit/window must never replace the provider budget.
    monkeypatch.setitem(CATALOG, source_id, replace(CATALOG[source_id], limit=1, window=1))
    with Session(quota_engine) as session, session.begin():
        session.add(DataQuota(key=provider, window_start=(NOW - timedelta(seconds=2)).isoformat(),
                              used=4, failures=0))
    now = [NOW]
    reservations_seen_by_http = []
    data, http = make_service(quota_engine, monkeypatch, now,
                             lambda _: reservations_seen_by_http.append(quota_state(quota_engine, provider)[1]))
    assert data.query(source_id).state == 'NO_DATA'
    assert reservations_seen_by_http == [5]
    assert data.query(source_id).state == 'RATE_LIMITED' and http.calls == 1
    now[0] += timedelta(seconds=2)
    # Simulates the independent market/issuer worker against the same SQLite row.
    with Session(quota_engine) as session, session.begin():
        session.connection().exec_driver_sql('BEGIN IMMEDIATE')
        assert reserve(session, now[0]) is None
    assert data.query(source_id).state == 'RATE_LIMITED' and http.calls == 1
    now[0] += timedelta(seconds=2)
    assert data.query(source_id).state == 'NO_DATA'
    assert reservations_seen_by_http == [5, 7]


@pytest.mark.parametrize('source_id,provider,limit', [('A09', 'SEC', 60), ('B04', 'ALPACA', 180)])
def test_shared_window_exhaustion_blocks_legacy_http(quota_engine, monkeypatch, source_id, provider, limit):
    with Session(quota_engine) as session, session.begin():
        session.add(DataQuota(key=provider, window_start=NOW.isoformat(), used=limit, failures=0))
    now = [NOW]
    data, http = make_service(quota_engine, monkeypatch, now)
    assert data.query(source_id).state == 'RATE_LIMITED' and http.calls == 0
    assert quota_state(quota_engine, provider)[1] == limit
    now[0] += timedelta(seconds=60)
    assert data.query(source_id).state == 'NO_DATA' and http.calls == 1
    assert quota_state(quota_engine, provider)[1] == 1


@pytest.mark.parametrize('source_id,provider,backoff', [
    ('A09', 'SEC', backoff_sec), ('B04', 'ALPACA', backoff_alpaca),
])
def test_legacy_remote_backoff_cannot_shorten_a_workers_existing_pause(
        quota_engine, monkeypatch, source_id, provider, backoff):
    def limited(_):
        with Session(quota_engine) as session, session.begin():
            session.connection().exec_driver_sql('BEGIN IMMEDIATE')
            backoff(session, NOW, 600)
        raise FetchError('RATE_LIMITED', status=429, retry_after=120)
    data, http = make_service(quota_engine, monkeypatch, [NOW], limited)
    assert data.query(source_id).state == 'RATE_LIMITED'
    assert quota_state(quota_engine, provider)[2] == (NOW + timedelta(seconds=600)).isoformat()
    assert data.query(source_id).state == 'RATE_LIMITED' and http.calls == 1


def test_alpaca_backoff_is_bounded_and_prevents_initial_reservation(quota_engine):
    with Session(quota_engine) as session, session.begin():
        session.connection().exec_driver_sql('BEGIN IMMEDIATE')
        backoff_alpaca(session, NOW, 10**9)
    assert quota_state(quota_engine, 'ALPACA')[2] == (NOW + timedelta(days=1)).isoformat()
    with Session(quota_engine) as session, session.begin():
        session.connection().exec_driver_sql('BEGIN IMMEDIATE')
        assert reserve_alpaca(session, NOW) == (NOW + timedelta(days=1)).isoformat()
    assert quota_state(quota_engine, 'ALPACA')[1] == 0


def test_cached_data_does_not_consume_a_shared_network_budget(quota_engine, monkeypatch):
    source = CATALOG['A09']
    with Session(quota_engine) as session, session.begin():
        payload = DataResult(access_id='A09', state='NO_DATA', reason='TEST_ONLY').model_dump(mode='json')
        session.add(DataRecord(key=cache_key(source), payload=payload, updated_at=NOW.isoformat(),
                               expires_at=(NOW + timedelta(seconds=source.ttl)).isoformat()))
        session.add(DataQuota(key='SEC', window_start=NOW.isoformat(), used=60, failures=0,
                              blocked_until=(NOW + timedelta(minutes=5)).isoformat()))
    before = quota_state(quota_engine, 'SEC')
    data, http = make_service(quota_engine, monkeypatch, [NOW])
    assert data.query('A09').cache_hit and http.calls == 0
    assert quota_state(quota_engine, 'SEC') == before

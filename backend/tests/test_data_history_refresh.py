"""TEST_ONLY isolated SQLite fixtures; no live connection claims or user DB."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.database import create_db_engine, DataRecord, DataObservation, DataRefresh
from app.data_catalog import CATALOG
from app.data_config import DataSettings
from app.data_contracts import DataResult
from app.data_history import archive, read_source
from app.data_parsers import parse
from app.data_refresh import DataRefresher
from app.data_service import DataService, cache_key
from app.data_windows import request_window

NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)


def setup(migrated):
    data = DataService(create_db_engine(migrated.database_url), DataSettings(_env_file=None), clock=lambda: NOW)
    data.http.real = False
    return data


def observation(source, day, value):
    raw = f'KEY,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,UNIT_MULT\nTEST_ONLY,{day},{value},index,0\n'.encode()
    return parse(source, raw, NOW)[0]


def test_archive_survives_cache_replacement_restart_and_retains_revisions(migrated):
    data = setup(migrated); source = CATALOG['A01']
    rows = [observation(source, '2026-10-19', '1.1'), observation(source, '2026-10-19', '1.2'),
            observation(source, '2026-10-20', '1.3')]
    with Session(data.engine) as s, s.begin():
        archive(s, source, cache_key(source), rows)
    data.engine.dispose()
    data = setup(migrated)
    with Session(data.engine) as s, s.begin():
        s.execute(delete(DataRecord))
        archive(s, source, cache_key(source), rows)
    with Session(data.engine) as s:
        restored = read_source(s, data, source)
        assert {o.id for o in restored} == {o.id for o in rows}
        assert len(list(s.scalars(select(DataObservation)))) == 3
    # Catalog rights or identity changes hide previously stored data immediately.
    restricted = replace(source, rights=source.rights.model_copy(update={'redistribution_allowed': False}))
    with Session(data.engine) as s:
        assert read_source(s, data, restricted) == []
        assert read_source(s, data, replace(source, feed='OTHER_FEED')) == []
        s.add(DataRecord(key='status:A01', payload={'http_status': 410},
            expires_at=NOW.isoformat(), updated_at=NOW.isoformat()))
        s.commit()
        assert read_source(s, data, source) == []


def test_archive_never_stores_prohibited_source(migrated):
    data = setup(migrated); source = CATALOG['A01']
    denied = replace(source, rights=source.rights.model_copy(update={'storage_allowed': False}))
    with Session(data.engine) as s, s.begin():
        archive(s, denied, cache_key(denied), [observation(source, '2026-10-19', '1')])
    with Session(data.engine) as s:
        assert list(s.scalars(select(DataObservation))) == []


def test_refetch_old_spot_is_stale_but_statistical_period_is_not_realtime():
    import json
    source = CATALOG['A18']
    raw = json.dumps({'time': '2026-10-19T00:00:00Z', 'price': '1.5', 'bid': '1.4', 'ask': '1.6'}).encode()
    assert parse(source, raw, NOW)[0].stale(NOW)
    macro = observation(CATALOG['A01'], '2026-10-19', '1.1')
    assert not macro.stale(NOW)
    assert macro.period_precision == 'day' and macro.observed_at < macro.received_at
    assert macro.stale(NOW + timedelta(days=2))


def test_refresh_due_times_survive_restart_without_automatic_brokers(migrated):
    data = setup(migrated); calls = []
    # Simulated success is confined to this isolated scheduler fixture.
    def query(access):
        calls.append(access)
        return DataResult(access_id=access, state='AVAILABLE_VERIFIED', reason='TEST_ONLY',
            real_connection=True, checked_at=NOW)
    data.query = query
    worker = DataRefresher(data)
    worker.tick()
    assert 'A01' in calls
    assert not set(calls) & {'A13', 'A14', 'A18', 'B04', 'B05', 'B01', 'A20'}
    count = len(calls)
    DataRefresher(data).tick()
    assert len(calls) == count
    states = DataRefresher(data).status()
    assert next(s for s in states['sources'] if s['access_id'] == 'A01')['succeeded_at'] == NOW.isoformat()
    assert not worker.thread
    data.clock = lambda: NOW + timedelta(days=2)
    worker.tick()
    assert len(calls) > count


def test_refresh_failure_backoff_and_persisted_lease(migrated):
    data = setup(migrated); calls = []
    data.query = lambda access: (calls.append(access) or DataResult(access_id=access, state='OFFLINE', reason='TEST_ONLY'))
    worker = DataRefresher(data)
    worker.tick()
    with Session(data.engine) as s:
        row = s.get(DataRefresh, 'A01')
        assert row.failures == 1 and row.succeeded_at is None
        assert datetime.fromisoformat(row.next_due_at) == NOW + timedelta(seconds=300)
    worker.tick()
    assert calls.count('A01') == 1
    data.clock = lambda: NOW + timedelta(seconds=301)
    worker.tick()
    with Session(data.engine) as s:
        row = s.get(DataRefresh, 'A01')
        assert row.failures == 2
        assert datetime.fromisoformat(row.next_due_at) == NOW + timedelta(seconds=901)
    worker.stop()


def test_cache_hit_does_not_extend_ttl_on_restart(migrated):
    data = setup(migrated); source = CATALOG['A21']
    checked = NOW - timedelta(minutes=20)
    data.query = lambda access: DataResult(access_id=access, state='DELAYED', reason='TEST_ONLY',
        real_connection=True, cache_hit=True, checked_at=checked)
    worker = DataRefresher(data)
    worker.eligible = lambda s: s.id == source.id
    worker.tick()
    with Session(data.engine) as s, s.begin():
        row = s.get(DataRefresh, source.id)
        assert datetime.fromisoformat(row.next_due_at) == checked + timedelta(seconds=source.ttl)
        # Repair a persisted schedule from an older backend that extended cache lifetime.
        row.next_due_at = (NOW + timedelta(days=1)).isoformat()
    worker.tick()
    with Session(data.engine) as s:
        assert datetime.fromisoformat(s.get(DataRefresh, source.id).next_due_at) == checked + timedelta(seconds=source.ttl)


def test_rolling_dates_are_generated_not_supplied_and_do_not_mutate_catalog():
    params, _ = request_window(CATALOG['A08'], NOW)
    assert params['field_tdr_date_value_month'] == '202610'
    assert CATALOG['A08'].params['field_tdr_date_value_month'] == '202609'
    params, _ = request_window(CATALOG['A05'], NOW)
    assert params['startPeriod'] == '2026-04' and params['endPeriod'] == '2026-10'
    _, payload = request_window(CATALOG['B03'], NOW)
    assert payload['startyear'] == '2025' and payload['endyear'] == '2026'
    assert CATALOG['B03'].payload['endyear'] == '2025'


def test_refresh_endpoint_reports_disabled_worker_without_network(client):
    response = client.get('/api/data/refresh')
    assert response.status_code == 200
    assert not response.json()['enabled'] and not response.json()['running']
    assert len(response.json()['sources']) == 36
    assert client.post('/api/orders').status_code == 403


def test_coinbase_ai_terms_block_query_before_network(migrated):
    data = setup(migrated)
    data.http.fetch = lambda source: (_ for _ in ()).throw(AssertionError('No network permitted'))
    result = data.query('A18')
    assert result.state == 'RIGHTS_RESTRICTED' and not result.real_connection
    assert not result.observations
    assert not DataRefresher(data).eligible(CATALOG['A18'])

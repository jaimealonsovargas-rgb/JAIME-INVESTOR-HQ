"""TEST_ONLY: isolated migrated SQLite, mocked P2 responses, no live verification.

The real unattended acceptance run is a separate operational evidence artifact.
These tests exercise the actual router, persistent scheduler and Python workers.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import threading

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.autonomy_contracts import AutonomyEvent, AutonomySettings, ResearchTask, ROLES, TERMINAL
from app.autonomy_scheduler import AutonomyScheduler
from app.autonomy_store import AutonomyStore
from app.data_catalog import CATALOG
from app.data_config import DataSettings
from app.data_contracts import DataResult
from app.data_history import archive
from app.data_parsers import parse
from app.data_registry import ingest
from app.data_service import DataService, cache_key
from app.database import create_db_engine
from app.local_llm import LocalLLM
from app.portfolio_service import PortfolioService
from app.portfolio_store import initialize_master
from app.research_service import ResearchService


class Clock:
    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


def policy(**changes):
    return AutonomySettings(_env_file=None, autonomy_enabled=True,
                            autonomy_startup_delay_seconds=1, **changes)


def setup(migrated, count=5):
    engine = create_db_engine(migrated.database_url)
    clock = Clock()
    settings = policy()
    data = DataService(engine, DataSettings(_env_file=None), clock=clock)
    source = CATALOG['A21']
    calls = []

    def query(access):
        assert access == 'A21'  # A new source cannot silently broaden the route.
        calls.append(access)
        raw = json.dumps([
            {'timestamp': (clock.now - timedelta(days=i + 1)).strftime('%Y-%m-%dT00:00:00Z'),
             'price': str(100 + i * 2)} for i in range(count)
        ]).encode()
        rows = tuple(o.model_copy(update={'series_id': 'TEST_ONLY',
                     'metadata': {'fixture': 'TEST_ONLY simulated provider response'}})
                     for o in parse(source, raw, clock.now))
        # Explicit test-only simulation of P2's verified transport/ingestion boundary.
        with Session(engine) as session, session.begin():
            ingest(session, rows)
            archive(session, source, cache_key(source), rows)
        return DataResult(access_id='A21', state='DELAYED' if rows else 'NO_DATA',
                          reason='TEST_ONLY', checked_at=clock.now, latency_ms=1,
                          real_connection=bool(rows), usable=bool(rows),
                          normalized_count=len(rows), observations=rows)

    data.query = query
    llm = LocalLLM(transport=httpx.MockTransport(lambda request: httpx.Response(503)))

    async def no_inference(*args, **kwargs):
        raise AssertionError('Autonomous descriptive route must never call an LLM')

    llm.chat = no_inference
    initialize_master(engine)
    portfolio = PortfolioService(engine, data)
    service = ResearchService(engine, data, portfolio, llm)
    service.store.initialize()
    scheduler = AutonomyScheduler(service, settings, clock)
    scheduler.prepare_start()
    return engine, clock, service, scheduler, calls


def due(clock, scheduler):
    clock.advance(seconds=2)
    task = scheduler.store.reserve_due(scheduler.settings)
    assert task is not None
    return task


def test_contracts_disallow_unapproved_route_and_aggressive_timer():
    for interval in (0, 1, 3599, 604801):
        with pytest.raises(ValidationError):
            policy(autonomy_interval_seconds=interval)
    for source in ('A18', 'B05', 'https://broker.invalid/orders'):
        with pytest.raises(ValidationError):
            policy(autonomy_source=source)
    now = datetime.now(timezone.utc).isoformat()
    event = dict(id='test', created_at=now, due_at=now, idempotency_key='test')
    with pytest.raises(ValidationError):
        AutonomyEvent(**event, trigger_type='BUY')
    task = dict(id='test', event_id='test', created_at=now, deadline_at=now, run_key='test')
    with pytest.raises(ValidationError):
        ResearchTask(**task, objective='BACKTEST')
    with pytest.raises(ValidationError):
        ResearchTask(**task, shell='echo forbidden')
    assert ResearchTask(**task).role_ids == list(ROLES)
    assert ResearchTask(**task).budget['llm_calls_max'] == 0


@pytest.mark.parametrize('timestamp', ['not-a-date', '2026-10-25T10:00:00', '2026-10-25T10:00:00+01:00'])
def test_contract_timestamps_require_real_utc(timestamp):
    now = datetime.now(timezone.utc).isoformat()
    with pytest.raises(ValidationError):
        AutonomyEvent(id='test', created_at=now, due_at=timestamp, idempotency_key='test')
    for field in ('created_at', 'deadline_at', 'started_at', 'finished_at'):
        task = dict(id='test', event_id='test', created_at=now, deadline_at=now, run_key='test')
        with pytest.raises(ValidationError):
            ResearchTask(**{**task, field: timestamp})


@pytest.mark.parametrize('changes', [
    {'role_ids': ['bull_advocate']}, {'role_ids': list(reversed(ROLES))},
    {'role_ids': [*ROLES, 'cio_chair']}, {'phase': 'INFER'},
    {'budget': {'llm_calls_max': 1, 'deadline_seconds': 90, 'fetches_max': 1, 'attempts_max': 1}},
    {'budget': {'llm_calls_max': 0, 'deadline_seconds': 9000, 'fetches_max': 1, 'attempts_max': 1}},
    {'budget': {'llm_calls_max': 0, 'deadline_seconds': 90, 'fetches_max': 2, 'attempts_max': 1}},
    {'budget': {'llm_calls_max': 0, 'deadline_seconds': 90, 'fetches_max': 1, 'attempts_max': 2}},
])
def test_task_contract_cannot_expand_roles_budget_or_phase(changes):
    now = datetime.now(timezone.utc).isoformat()
    with pytest.raises(ValidationError):
        ResearchTask(id='test', event_id='test', created_at=now, deadline_at=now, run_key='test', **changes)


def test_due_reservation_is_atomic_and_coalesces_missed_days(migrated):
    engine, clock, service, scheduler, calls = setup(migrated)
    try:
        assert scheduler.store.reserve_due(scheduler.settings) is None
        clock.advance(days=10)
        barrier = threading.Barrier(2)

        def reserve():
            barrier.wait()
            return AutonomyStore(engine, clock).reserve_due(scheduler.settings)

        with ThreadPoolExecutor(max_workers=2) as pool:
            reservations = list(pool.map(lambda _: reserve(), range(2)))
        assert sum(task is not None for task in reservations) == 1
        task = next(task for task in reservations if task)
        with scheduler.store.connection() as connection:
            assert connection.execute('SELECT count(*) FROM autonomy_events').fetchone()[0] == 1
            assert connection.execute('SELECT count(*) FROM research_tasks').fetchone()[0] == 1
        assert datetime.fromisoformat(scheduler.store.control()['next_due_at']) == clock.now + timedelta(days=1)
        scheduler.cancel(task['id'])
        assert scheduler.store.reserve_due(scheduler.settings) is None
        restarted = AutonomyScheduler(service, scheduler.settings, clock)
        restarted.prepare_start()
        assert restarted.store.reserve_due(scheduler.settings) is None
        assert calls == []
    finally:
        engine.dispose()


def test_fetching_restart_blocks_without_repeating_provider_call(migrated):
    engine, clock, service, scheduler, calls = setup(migrated)
    try:
        task = due(clock, scheduler)
        scheduler.store.update(task['id'], state='RUNNING', phase='FETCHING')
        restarted = AutonomyScheduler(service, scheduler.settings, clock)
        restarted.prepare_start()
        saved = restarted.store.get(task['id'])
        assert saved['state'] == 'BLOCKED'
        assert saved['result']['reason'] == 'RESTART_INTERRUPTED'
        assert saved['finished_at'] and calls == []
    finally:
        engine.dispose()


def test_second_process_lock_rejects_before_autonomy_restart_callback(migrated):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated)
        second = ResearchService(engine, service.data, service.portfolio, service.llm)
        callback_calls = []
        try:
            task = due(clock, scheduler)
            original = scheduler.store.update(task['id'], state='RUNNING', phase='FETCHING')
            await service.start()

            def callback():
                callback_calls.append('called')
                scheduler.prepare_start()

            with pytest.raises(RuntimeError, match='RESEARCH_SCHEDULER_ALREADY_RUNNING'):
                await second.start(callback)
            assert callback_calls == []
            assert scheduler.store.get(task['id']) == original
            assert second.lock_file is None and second.workers == []
            assert calls == []
        finally:
            await second.stop()
            await service.stop()
            engine.dispose()
    asyncio.run(scenario())


def test_expired_jobs_are_cancelled_before_restart_workers_can_claim(migrated):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated)
        try:
            task = due(clock, scheduler)
            await scheduler.advance(task)
            task = scheduler.store.get(task['id'])
            assert task['phase'] == 'JOBS'
            assert all(job['state'] == 'QUEUED' for job in scheduler.jobs(task))
            clock.advance(seconds=91)
            await service.start(scheduler.prepare_start)
            await asyncio.sleep(0.02)
            saved = scheduler.store.get(task['id'])
            assert saved['state'] == 'BLOCKED' and saved['result']['reason'] == 'DEADLINE_EXCEEDED'
            assert all(job['state'] == 'CANCELLED' and job['attempts'] == 0 for job in scheduler.jobs(task))
            assert calls == ['A21'] and service.active == {}
        finally:
            await service.stop()
            engine.dispose()
    asyncio.run(scenario())


@pytest.mark.parametrize('finish_offset,expected', [(-1, 'SUCCEEDED'), (1, 'BLOCKED')])
def test_reconcile_uses_job_finish_deadline_not_delayed_observation(migrated, finish_offset, expected):
    async def scenario():
        engine, clock, service, scheduler, _ = setup(migrated)
        try:
            task = due(clock, scheduler)
            await scheduler.advance(task)
            task = scheduler.store.get(task['id'])
            for kind in ('fetch', 'quant', 'quant'):
                job = service.store.claim(kind)
                assert job is not None
                await service.execute(job)
            jobs = scheduler.jobs(task)
            assert all(job['state'] == 'SUCCEEDED' for job in jobs)
            # Simulate persisted finish timestamps, independent of callback delay.
            finish = (datetime.fromisoformat(task['deadline_at']) + timedelta(seconds=finish_offset)).isoformat()
            with service.store.connection(True) as connection:
                for job in jobs:
                    job['finished_at'] = finish
                    connection.execute('UPDATE agent_jobs SET payload=? WHERE id=?', (json.dumps(job), job['id']))
            clock.advance(seconds=100)
            saved = scheduler.reconcile(task)
            assert saved['state'] == expected
            if expected == 'BLOCKED':
                assert saved['result']['reason'] == 'DEADLINE_EXCEEDED'
            else:
                assert saved['result']['quality_state'] == 'VERIFIED_DATA'
                assert saved['case_id'] == task['case_id']
        finally:
            engine.dispose()
    asyncio.run(scenario())


def test_prepared_restart_reuses_existing_case_and_jobs(migrated):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated)
        try:
            task = due(clock, scheduler)
            subject, result = scheduler.router.prepare(task)
            task = scheduler.store.update(task['id'], state='RUNNING', phase='PREPARED', subject=subject, result=result)
            case_id, jobs = scheduler.router.enqueue(task)
            # Crash after enqueue, before writing phase=JOBS.
            restarted = AutonomyScheduler(service, scheduler.settings, clock)
            restarted.prepare_start()
            await restarted.advance(restarted.store.get(task['id']))
            saved = restarted.store.get(task['id'])
            assert saved['phase'] == 'JOBS' and saved['case_id'] == case_id
            assert {j['id'] for j in restarted.jobs(saved)} == {j['id'] for j in jobs}
            assert len(service.store.list('research_cases')) == 1
            assert len(service.store.list('agent_jobs')) == 3
            assert calls == ['A21']
        finally:
            engine.dispose()
    asyncio.run(scenario())


def test_pause_cancels_persistently_and_control_replays_do_not_change_state(migrated):
    engine, clock, service, scheduler, calls = setup(migrated)
    try:
        task = due(clock, scheduler)
        subject, result = scheduler.router.prepare(task)
        task = scheduler.store.update(task['id'], state='RUNNING', phase='PREPARED', subject=subject, result=result)
        scheduler.router.enqueue(task)
        scheduler.control('pause', 'test-pause')
        assert scheduler.store.get(task['id'])['state'] == 'CANCELLED'
        assert all(j['state'] == 'CANCELLED' for j in scheduler.jobs(task))
        restarted = AutonomyScheduler(service, scheduler.settings, clock)
        restarted.prepare_start()
        assert restarted.status()['paused']
        clock.advance(days=2)
        assert restarted.store.reserve_due(scheduler.settings) is None
        restarted.control('resume', 'test-resume')
        restarted.control('pause', 'test-pause')  # replay must not overwrite newer command
        assert not restarted.status()['paused']
        with pytest.raises(ValueError, match='IDEMPOTENCY_CONFLICT'):
            restarted.control('resume', 'test-pause')
        assert restarted.cancel(task['id']) == restarted.cancel(task['id'])
    finally:
        engine.dispose()


@pytest.mark.parametrize('table', ['portfolios', 'ledger_events', 'ledger_entries', 'valuation_snapshots', 'instruments', 'agent_jobs'])
def test_autonomy_store_cannot_mutate_financial_or_worker_domain(migrated, table):
    engine, _, _, scheduler, _ = setup(migrated)
    try:
        with pytest.raises(sqlite3.DatabaseError, match='not authorized'):
            with scheduler.store.connection(True) as connection:
                connection.execute(f'DELETE FROM {table}')
        with engine.connect() as connection:
            assert connection.execute(text('SELECT count(*) FROM ledger_events')).scalar_one() == 1
    finally:
        engine.dispose()


@pytest.mark.parametrize('count,expected', [(5, 'SUCCEEDED'), (1, 'ABSTAINED'), (0, 'ABSTAINED')])
def test_unattended_python_pipeline_without_local_model(migrated, count, expected):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated, count)
        before = service.portfolio.summary()
        clock.advance(seconds=2)
        try:
            await service.start()
            assert service.llm.status['state'] == 'NO_LOCAL_MODEL'
            scheduler.start()  # no case/question endpoint and no UI interaction
            async with asyncio.timeout(8):
                while not scheduler.store.tasks() or scheduler.store.tasks()[0]['state'] not in TERMINAL:
                    await asyncio.sleep(0.02)
            task = scheduler.store.tasks()[0]
            assert task['state'] == expected
            assert task['result']['reason'] and task['finished_at']
            assert calls == ['A21']
            if count:
                jobs = scheduler.jobs(task)
                assert {j['role_id'] for j in jobs} == set(ROLES)
                assert all(j['state'] == 'SUCCEEDED' and j['runtime'] == 'python-decimal' for j in jobs)
                dossier = service.dossier(task['case_id'], task['run_key'])
                assert dossier['origin']['autonomy_task_id'] == task['id']
                assert dossier['quality']['state'] == ('VERIFIED_DATA' if count >= 3 else 'ABSTAINED')
                assert all(e['provider'] in {'COINPAPRIKA', 'HQ_DERIVED', 'HQ_MASTER'} for e in dossier['evidence'])
                assert task['result']['dossier_hash'] and task['result']['output_hashes']
                if count >= 3:
                    quant = next(r for r in dossier['results'] if r['role_id'] == 'momentum_trend')['features']
                    assert quant['sample_size'] == count
                    assert quant['input_hash'] and all(m['evidence_ids'] for m in quant['items'])
            else:
                assert service.store.list('agent_jobs') == []
            after = service.portfolio.summary()
            assert all(after[k] == before[k] for k in ('ledger_hash', 'cash_eur', 'nav_eur', 'positions_count'))
            assert after['cash_eur'] == after['nav_eur'] == '10000.00'
            assert len(service.store.list('agents')) == 30
            await scheduler.stop()
            await service.stop()
            restarted = AutonomyScheduler(service, scheduler.settings, clock)
            restarted.prepare_start()
            await service.start()
            restarted.start()
            await asyncio.sleep(0.1)
            assert len(restarted.store.tasks()) == 1 and calls == ['A21']
            await restarted.stop()
        finally:
            await scheduler.stop()
            await service.stop()
            engine.dispose()
    asyncio.run(scenario())


def test_expired_task_abstains_without_fetch_and_cannot_revive_cancelled_task(migrated):
    async def scenario():
        engine, clock, _, scheduler, calls = setup(migrated)
        try:
            task = due(clock, scheduler)
            clock.advance(seconds=91)
            await scheduler.advance(task)
            saved = scheduler.store.get(task['id'])
            assert saved['state'] == 'BLOCKED' and saved['result']['reason'] == 'DEADLINE_EXCEEDED'
            assert scheduler.store.update(task['id'], state='RUNNING') == saved
            assert calls == []
        finally:
            engine.dispose()
    asyncio.run(scenario())


def test_cancel_during_fetch_never_publishes_late_result_or_starts_jobs(migrated):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated)
        entered, release = threading.Event(), threading.Event()
        original = scheduler.router.prepare

        def delayed_prepare(task):
            entered.set()
            assert release.wait(timeout=3)
            return original(task)

        scheduler.router.prepare = delayed_prepare
        worker = None
        try:
            task = due(clock, scheduler)
            worker = asyncio.create_task(scheduler.advance(task))
            assert await asyncio.to_thread(entered.wait, 2)
            assert scheduler.store.get(task['id'])['phase'] == 'FETCHING'
            scheduler.cancel(task['id'])
            release.set()
            await asyncio.wait_for(worker, 3)
            assert scheduler.store.get(task['id'])['state'] == 'CANCELLED'
            assert service.store.list('agent_jobs') == []
            assert service.store.list('research_cases') == []
            assert calls == ['A21']  # Bounded in-flight fetch may finish; no retry/inference.
        finally:
            release.set()
            if worker:
                await asyncio.gather(worker, return_exceptions=True)
            engine.dispose()
    asyncio.run(scenario())


def test_disabled_config_cancels_pending_jobs_before_research_worker_start(migrated):
    engine, clock, service, scheduler, _ = setup(migrated)
    try:
        task = due(clock, scheduler)
        subject, result = scheduler.router.prepare(task)
        task = scheduler.store.update(task['id'], state='RUNNING', phase='PREPARED', subject=subject, result=result)
        scheduler.router.enqueue(task)
        disabled = scheduler.settings.model_copy(update={'autonomy_enabled': False})
        restarted = AutonomyScheduler(service, disabled, clock)
        restarted.prepare_start()
        assert restarted.store.get(task['id'])['state'] == 'CANCELLED'
        assert all(j['state'] == 'CANCELLED' for j in restarted.jobs(task))
        assert restarted.store.reserve_due(disabled) is None
        with pytest.raises(ValueError, match='AUTONOMY_DISABLED_BY_CONFIG'):
            restarted.control('resume', 'disabled-cannot-resume')
    finally:
        engine.dispose()


def test_router_denies_unknown_route_and_restricted_rights_before_network(migrated, monkeypatch):
    engine, clock, _, scheduler, calls = setup(migrated)
    try:
        task = due(clock, scheduler)
        subject, result = scheduler.router.prepare({**task, 'source_access_id': 'B05'})
        assert subject is None and result['reason'] == 'ROUTE_DENIED'
        source = CATALOG['A21']
        monkeypatch.setitem(CATALOG, 'A21', replace(source,
            rights=source.rights.model_copy(update={'local_research_allowed': False})))
        subject, result = scheduler.router.prepare(task)
        assert subject is None and result['reason'] == 'RIGHTS_RESTRICTED'
        assert calls == []
    finally:
        engine.dispose()


def test_busy_p2_lane_has_bounded_wait_and_abstains_without_query(migrated):
    engine, clock, service, scheduler, calls = setup(migrated)
    timeouts = []

    class BusyLock:
        def acquire(self, *, timeout):
            timeouts.append(timeout)
            return False

        def release(self):
            raise AssertionError('A failed acquisition cannot release another owner\'s lock')

    service.data.lock = BusyLock()
    try:
        task = due(clock, scheduler)
        subject, result = scheduler.router.prepare(task)
        assert subject is None
        assert result == {'quality_state': 'ABSTAINED', 'reason': 'DATA_LANE_BUSY'}
        assert timeouts == [5] and calls == []
    finally:
        engine.dispose()


@pytest.mark.parametrize('state', ['OFFLINE', 'RATE_LIMITED', 'NO_CREDENTIALS'])
def test_provider_failure_abstains_and_waits_for_next_conservative_slot(migrated, state):
    async def scenario():
        engine, clock, service, scheduler, calls = setup(migrated)
        calls.clear()

        def unavailable(access):
            calls.append(access)
            return DataResult(access_id=access, state=state, reason='TEST_ONLY', checked_at=clock.now)

        service.data.query = unavailable
        try:
            clock.advance(seconds=2)
            scheduler.start()
            async with asyncio.timeout(3):
                while not scheduler.store.tasks() or scheduler.store.tasks()[0]['state'] not in TERMINAL:
                    await asyncio.sleep(0.01)
            task = scheduler.store.tasks()[0]
            assert task['state'] == 'ABSTAINED' and task['result']['reason'] == state
            await asyncio.sleep(0.1)
            assert calls == ['A21'] and service.store.list('agent_jobs') == []
            assert datetime.fromisoformat(scheduler.store.control()['next_due_at']) >= clock.now + timedelta(hours=1)
        finally:
            await scheduler.stop()
            engine.dispose()
    asyncio.run(scenario())


def test_api_origin_idempotency_configuration_and_orders(client):
    path = '/api/research/autonomy'
    headers = {'X-HQ-Research': '1', 'Idempotency-Key': 'test-autonomy-pause'}
    assert client.get(path).status_code == 200
    assert not client.get(path).json()['enabled']
    assert client.post(path + '/control', json={'action': 'pause'}).status_code == 403
    assert client.post(path + '/control', json={'action': 'pause'}, headers={**headers, 'Origin': 'https://evil.example'}).status_code == 403
    assert client.post(path + '/control', json={'action': 'pause'}, headers={'X-HQ-Research': '1'}).status_code == 400
    assert client.post(path + '/control', json={'action': 'pause'}, headers=headers).status_code == 200
    disabled = client.post(path + '/control', json={'action': 'resume'}, headers={**headers, 'Idempotency-Key': 'test-autonomy-resume'})
    assert disabled.status_code == 409 and disabled.json()['detail'] == 'AUTONOMY_DISABLED_BY_CONFIG'
    assert client.post(path + '/control', json={'action': 'buy'}, headers=headers).status_code == 422
    assert client.post(path + '/tasks/missing/cancel', headers=headers).status_code == 404
    assert client.post('/api/orders').status_code == 403
    assert len(client.get('/api/agents').json()) == 30

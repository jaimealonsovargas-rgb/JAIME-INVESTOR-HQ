"""B2.5 integration against the actual SEC queue and accounting builder, isolated SQLite only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from sqlalchemy import select, func
from app.cycle_contracts import CycleRequest, CycleSettings, Budget, AGENDA, TERMINAL, window, event_for
from app.cycle_service import CycleService, CYCLES
from app.cycle_api import router
from app.sec_store import JOBS, TASKS
from app.company_service import CompanyService, MODELS
from test_sec_financials import service, CIK
from test_company_models import imported

TOKEN = 'test-only-no-secret-'+'x'*32


def request_for(now, correlation='test-delivery'):
    start,end = window(now)
    return CycleRequest(schema_version=1,agenda=AGENDA,objective='SEC_COMPANY_REVIEW',mode='shadow',
        event_id=event_for(start),correlation_id=correlation,window_start=start,window_end=end,budget=Budget())


@pytest.fixture
def cycles(service,monkeypatch):
    imported(service)
    original_fetch = service.http.fetch
    service.calls = []
    def observed(cik,kind):
        service.calls.append((cik,kind))
        return original_fetch(cik,kind)
    service.http.fetch = observed
    monkeypatch.setattr('app.cycle_service.PILOT_CIKS',(CIK,))
    cycles = CycleService(service,CycleSettings(_env_file=None,jaime_cycle_token=TOKEN))
    service.cycle_coordinator = cycles
    cycles.set_owner('n8n')
    return cycles


def drain_cycle(cycles,ident):
    for _ in range(45):
        cycles.sec.step()
        cycles.sec.clock[0] += timedelta(seconds=2)
        result = cycles.get(ident)
        if result['state'] in TERMINAL:
            return result
    pytest.fail('Cycle did not terminate')


def count(cycles,table):
    with cycles.engine.connect() as c:
        return c.scalar(select(func.count()).select_from(table))


def test_duplicate_deliveries_and_concurrent_submissions_share_one_cycle(cycles):
    body = request_for(cycles.clock())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: cycles.submit(body),range(8)))
    assert len({r[0]['id'] for r in results})==1
    assert sum(not r[1] for r in results)==1
    assert count(cycles,CYCLES)==1
    calls = len(cycles.sec.calls)
    result = drain_cycle(cycles,results[0][0]['id'])
    assert result['state']=='PARTIAL' and result['result']['reason']=='ACCOUNTING_REVIEW_COMPLETE'
    assert len(cycles.sec.calls)-calls==2
    assert len(result['result']['models'])==1 and result['result']['models'][0]['version']==1
    assert cycles.submit(request_for(cycles.clock(),'n8n-retry'))[1]
    assert count(cycles,MODELS)==1


def test_enqueue_and_cycle_acknowledgement_are_one_transaction(cycles,monkeypatch):
    cycle,_ = cycles.submit(request_for(cycles.clock()))
    before = count(cycles,JOBS)
    original = cycles.sec.store.enqueue
    def interrupted(*args,**kwargs):
        original(*args,**kwargs)
        raise RuntimeError('Simulated crash before transaction commits')
    monkeypatch.setattr(cycles.sec.store,'enqueue',interrupted)
    with pytest.raises(RuntimeError):
        cycles.step()
    assert count(cycles,JOBS)==before and cycles.get(cycle['id'])['state']=='QUEUED'
    monkeypatch.setattr(cycles.sec.store,'enqueue',original)
    assert drain_cycle(cycles,cycle['id'])['state']=='PARTIAL'
    assert count(cycles,JOBS)==before+1


def test_restart_after_model_commit_recovers_without_fetching_or_building_twice(cycles,monkeypatch):
    cycle,_ = cycles.submit(request_for(cycles.clock()))
    for _ in range(25):
        cycles.sec.step(); cycles.sec.clock[0]+=timedelta(seconds=2)
        if cycles.get(cycle['id'])['state']=='REVIEWING':
            break
    original = CompanyService.build
    def interrupted(*args,**kwargs):
        original(*args,**kwargs)
        raise RuntimeError('Simulated crash after durable model commit')
    monkeypatch.setattr(CompanyService,'build',interrupted)
    with pytest.raises(RuntimeError):
        cycles.step()
    assert count(cycles,MODELS)==1
    calls = len(cycles.sec.calls)
    monkeypatch.setattr(CompanyService,'build',original)
    recovered = CycleService(cycles.sec,cycles.settings)
    cycles.sec.cycle_coordinator = recovered
    assert drain_cycle(recovered,cycle['id'])['result']['models'][0]['version']==1
    assert count(cycles,MODELS)==1 and len(cycles.sec.calls)==calls


def test_cancellation_fences_a_leased_download_and_is_idempotent(cycles):
    cycle,_ = cycles.submit(request_for(cycles.clock()))
    cycles.step()
    task = cycles.sec.store.claim(cycles.clock())
    assert task['job_id']==cycle['id']
    cycles.cancel(cycle['id'])
    # The HTTP cancel handler fences the task immediately, even while the SEC worker is inside GET.
    assert cycles.sec.store.accept(task,[],{},'x'*64,'test-only',cycles.clock(),cycles.clock()) is False
    cycles.step()
    assert cycles.get(cycle['id'])['state']=='CANCELLED'
    assert cycles.sec.store.job(cycle['id'])['state']=='CANCELLED'
    assert cycles.cancel(cycle['id'])['state']=='CANCELLED'
    assert count(cycles,MODELS)==0


def test_deadline_cancels_only_owned_job_and_prevents_new_calls(cycles):
    cycle,_ = cycles.submit(request_for(cycles.clock())); cycles.step()
    calls = len(cycles.sec.calls)
    cycles.sec.clock[0]+=timedelta(minutes=21)
    cycles.sec.step()
    assert cycles.get(cycle['id'])['state']=='TIMED_OUT'
    assert len(cycles.sec.calls)==calls and count(cycles,MODELS)==0


def test_busy_import_waits_without_duplicates_and_expiration_preserves_manual_job(cycles):
    cycles.sec.enqueue('manual-existing-import',[CIK])
    cycle,_ = cycles.submit(request_for(cycles.clock()))
    assert not cycles.step()
    assert cycles.get(cycle['id'])['result']['reason']=='WAITING_FOR_SEC_QUEUE'
    cycles.sec.clock[0]+=timedelta(minutes=21)
    cycles.step()
    assert cycles.get(cycle['id'])['state']=='TIMED_OUT'
    assert cycles.sec.store.job('manual-existing-import')['state']=='QUEUED'


def test_disabled_agenda_blocks_new_requests_but_allows_receipt_replay(cycles):
    body = request_for(cycles.clock()); prior,_ = cycles.submit(body)
    cycles.set_owner('disabled')
    assert cycles.submit(body)[1]
    cycles.cancel(prior['id']); cycles.step()
    cycles.sec.clock[0]+=timedelta(hours=6)
    with pytest.raises(ValueError,match='SCHEDULE_DISABLED'):
        cycles.submit(request_for(cycles.clock()))
    assert cycles.submit(body)[0]['state']=='CANCELLED'
    with pytest.raises(ValueError,match='OWNER_DENIED'):
        cycles.set_owner('internal')


def test_stale_future_overlap_and_mutated_payload_rejected(cycles):
    for offset in (-6,6):
        with pytest.raises(ValueError,match='STALE_OR_FUTURE_WINDOW'):
            cycles.submit(request_for(cycles.clock()+timedelta(hours=offset)))
    body = request_for(cycles.clock()); cycles.submit(body)
    # Boundary test of service defence, bypassing Pydantic only inside this isolated test.
    with pytest.raises(ValueError,match='IDEMPOTENCY_CONFLICT'):
        cycles.submit(body.model_copy(update={'objective':'UNAUTHORIZED'}))
    cycles.sec.clock[0]+=timedelta(hours=6)
    with pytest.raises(ValueError,match='CYCLE_ALREADY_ACTIVE'):
        cycles.submit(request_for(cycles.clock()))


@pytest.mark.parametrize('change',[
    {'mode':'live'}, {'objective':'PLACE_ORDER'}, {'url':'https://example.invalid'}, {'ciks':['ANY']},
    {'budget':{'max_llm_calls':1}}, {'window_start':'2026-10-28T12:00:00'}, {'event_id':'new-random-event'},
])
def test_contract_rejects_expanded_permissions_and_ambiguous_time(cycles,change):
    body = request_for(cycles.clock()).model_dump(mode='json')
    with pytest.raises(ValidationError):
        CycleRequest.model_validate({**body,**change})


def test_source_disabled_abstains_without_downloads(cycles):
    cycle,_ = cycles.submit(request_for(cycles.clock()))
    calls = len(cycles.sec.calls)
    cycles.sec.data.settings.data_public_enabled=False
    cycles.sec.step()
    assert cycles.get(cycle['id'])['state']=='BLOCKED' and len(cycles.sec.calls)==calls


def test_api_auth_origin_payload_size_and_redacted_status(cycles):
    app = FastAPI(); app.include_router(router(cycles))
    body = request_for(cycles.clock()).model_dump(mode='json')
    headers = {'authorization':'Bearer '+TOKEN}
    with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
        assert client.post('/api/cycles',json=body).status_code==403
        assert client.post('/api/cycles',json=body,headers={**headers,'origin':'http://127.0.0.1:5173'}).status_code==403
        assert client.post('/api/cycles',content=' '*4097,headers=headers).status_code==413
        assert client.post('/api/cycles',json={**body,'secret':'not-echoed'},headers=headers).json()=={'detail':'INVALID_CYCLE_REQUEST'}
        accepted = client.post('/api/cycles',json=body,headers=headers)
        assert accepted.status_code==202 and not accepted.json()['duplicate']
        assert client.post('/api/cycles',json=body,headers=headers).status_code==200
        ident = accepted.json()['cycle']['id']
        assert client.get('/api/cycles/'+ident).status_code==403
        assert client.get('/api/cycles/'+ident,headers=headers).status_code==200
        assert TOKEN not in client.get('/api/automation/status').text
        assert client.post('/api/universe/automation/control',json={'owner':'disabled'}).status_code==403
        assert client.post('/api/universe/automation/control',json={'owner':'disabled'},headers={'x-hq-universe':'1'}).status_code==200
    with TestClient(app,client=('192.168.1.22',50000)) as remote:
        assert remote.post('/api/cycles',json=body,headers=headers).status_code==403

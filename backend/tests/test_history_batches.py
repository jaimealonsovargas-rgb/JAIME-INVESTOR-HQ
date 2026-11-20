"""D2 engineering acceptance: wide synthetic universe, recovery, rights and storage."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import time
import pytest
from sqlalchemy import select,func,update,text
from app.database import create_db_engine
from app.data_identity import fingerprint
from app.history_contracts import BatchRequest
from app.history_rights import require_ibkr_archive_rights
from app.history_service import HistoryService,SyntheticHistoryTransport,fixture_request
from app.history_store import HistoryStore,UNITS,SNAPSHOTS,BUDGET,EVENTS
from app.storage_budget import StorageBlocked


class Guard:
    def __init__(self):self.block=None;self.calls=0
    @contextmanager
    def admission(self,**kwargs):
        self.calls+=1
        if self.block:raise StorageBlocked(self.block)
        yield


@pytest.fixture
def service(migrated):
    engine=create_db_engine(migrated.database_url)
    clock=[datetime(2026,11,17,tzinfo=timezone.utc)]
    s=HistoryService(engine,clock=lambda:clock[0],storage=Guard())
    s.time=clock
    yield s
    engine.dispose()


def one():
    request=fixture_request(1);request['end']='2000-01-03';return request


def count(service,table):
    with service.engine.connect() as c:return c.scalar(select(func.count()).select_from(table))


def drain(service,key,max_steps=2500):
    for _ in range(max_steps):
        if not service.step(key)['worked']:break
    return service.store.status(key)


def test_wide_universe_checkpoint_and_pagination(service):
    body=fixture_request(1000);body['end']='2000-01-03'
    started=time.perf_counter()
    service.enqueue('wide',body)
    for _ in range(7):assert service.step('wide')['worked']
    restarted=HistoryService(service.engine,clock=service.clock,storage=service.storage)
    report=drain(restarted,'wide')
    assert report['targets']==1000 and report['total_units']==1000
    assert report['counts']=={'SUCCEEDED':1000} and report['state']=='COMPLETED'
    assert report['next_offset']==100
    assert len(restarted.store.status('wide',offset=900,limit=100)['units'])==100
    assert count(service,SNAPSHOTS)==1000
    assert not report['backtest_ready']
    print(json.dumps(dict(synthetic_targets=1000,units=1000,elapsed_seconds=round(time.perf_counter()-started,3))))


def test_windows_are_inclusive_nonoverlapping_with_no_gaps():
    units=list(BatchRequest.model_validate(fixture_request(1)).units())
    assert [(x['start'],x['end']) for x in units]==[('2000-01-01','2000-01-31'),('2000-02-01','2000-02-02')]


def test_duplicate_concurrent_submissions_single_batch(service):
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _:service.enqueue('same',one()),range(8)))
    assert count(service,UNITS)==1
    with pytest.raises(ValueError,match='IDEMPOTENCY_CONFLICT'):service.enqueue('same',one()|{'revision':'changed'})


def test_metadata_and_snapshot_dedup_without_duplicate_receipt_time(service):
    service.enqueue('a',one());drain(service,'a')
    first=service.store.status('a')['units'][0]
    service.time[0]+=timedelta(hours=1)
    service.enqueue('b',one());drain(service,'b')
    second=service.store.status('b')['units'][0]
    assert second['reason']=='CACHE_REUSED' and second['attempts']==0
    assert second['received_at']==first['received_at'] and count(service,SNAPSHOTS)==1
    service.time[0]+=timedelta(days=2)
    service.enqueue('c',one());drain(service,'c')
    third=service.store.status('c')['units'][0]
    assert third['attempts']==1 and third['received_at']!=first['received_at']
    assert count(service,SNAPSHOTS)==1  # cache expiry never deletes evidence
    assert third['coverage']['calendar']=='NOT_VALIDATED'
    assert third['coverage']['corporate_actions']=='NOT_VERIFIED'


def test_identity_revision_changes_never_use_wrong_cache(service):
    service.enqueue('a',one());drain(service,'a')
    changed=one();changed['targets'][0]['identity_hash']='f'*64
    service.enqueue('b',changed);drain(service,'b')
    assert service.store.status('b')['units'][0]['attempts']==1
    assert count(service,SNAPSHOTS)==2
    service.enqueue('c',one()|{'revision':'refresh'});drain(service,'c')
    assert service.store.status('c')['units'][0]['attempts']==1 and count(service,SNAPSHOTS)==2


def test_crash_after_claim_is_bounded_and_preserves_events(service):
    class Crash:
        provider='SYNTHETIC_TEST'
        def fetch(self,request):raise SystemExit('crash')
    service.transport=Crash();service.enqueue('crash',one())
    for _ in range(3):
        with pytest.raises(SystemExit):service.step('crash')
        service.time[0]+=timedelta(seconds=101)
    service.step('crash')
    row=service.store.status('crash')['units'][0]
    assert row['state']=='FAILED' and row['attempts']==3
    assert row['reason']=='ATTEMPT_LIMIT' and count(service,SNAPSHOTS)==0
    with service.engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(EVENTS).where(EVENTS.c.state=='INTERRUPTED'))==3


def test_recover_interrupted_same_unit_once(service):
    service.enqueue('a',one());job=service.store.claim('a',service.clock())
    assert job['attempts']==1
    service.time[0]+=timedelta(seconds=101)
    assert service.step('a')['state']=='COLLECTED'
    assert service.store.status('a')['units'][0]['attempts']==2 and count(service,SNAPSHOTS)==1


@pytest.mark.parametrize('action',['pause','cancel'])
def test_control_during_fetch_fences_publication(service,action):
    original=SyntheticHistoryTransport(service.clock)
    class During:
        provider='SYNTHETIC_TEST'
        def fetch(self,request):
            service.store.control('a',action,service.clock())
            return original.fetch(request)
    service.transport=During();service.enqueue('a',one())
    assert service.step('a')['state']=='CLAIM_LOST' and count(service,SNAPSHOTS)==0
    assert not service.step('a')['worked']
    if action=='pause':
        service.control('a','resume');service.transport=original
        assert service.step('a')['state']=='COLLECTED'
        assert service.store.status('a')['units'][0]['attempts']==2
    else:
        service.control('a','resume');assert service.store.status('a')['state']=='CANCELLED'


def test_old_worker_cannot_override_new_result(service):
    service.enqueue('a',one());old=service.store.claim('a',service.clock())
    service.time[0]+=timedelta(seconds=101)
    assert service.step('a')['state']=='COLLECTED'
    assert not service.store.accept(old,{'bars':[]},{},service.clock(),service.clock())
    assert count(service,SNAPSHOTS)==1 and service.store.status('a')['units'][0]['state']=='SUCCEEDED'


def test_shared_lease_and_quota_survive_restart(service,monkeypatch):
    # Test a hypothetical reviewed entitlement using fake DB state only; no SDK.
    monkeypatch.setattr('app.history_store.require_rights',lambda provider:None)
    req=one();req['provider']='IBKR_TWS';req['targets'][0]['listing_id']='real-id';req['targets'][0]['contract']['symbol']='ABC'
    service.store.enqueue('a',BatchRequest.model_validate(req),service.clock())
    service.store.enqueue('b',BatchRequest.model_validate(req|{'revision':'b'}),service.clock())
    first=service.store.claim('a',service.clock())
    assert first and service.store.claim('b',service.clock()) is None
    service.store.fail(first,'PACING_LIMIT',service.clock())
    restarted=HistoryStore(service.engine)
    service.time[0]+=timedelta(seconds=599)
    assert restarted.claim('b',service.clock()) is None
    service.time[0]+=timedelta(seconds=1)
    assert restarted.claim('b',service.clock()) is not None


def test_rights_gate_before_transport_and_rejects_flags(service):
    req=one();req['provider']='IBKR_TWS';req['targets'][0]['listing_id']='real-id';req['targets'][0]['contract']['symbol']='AAPL'
    report=service.enqueue('blocked',req)
    assert report['state']=='BLOCKED' and report['reason']=='RIGHTS_UNVERIFIED'
    assert not service.step('blocked')['worked'] and count(service,SNAPSHOTS)==0 and count(service,BUDGET)==0
    with pytest.raises(ValueError):require_ibkr_archive_rights()
    with pytest.raises(ValueError):service.enqueue('bypass',req|{'rights_approved':True})


@pytest.mark.parametrize('mutation',['future','negative','missing','wrong_provider','duplicate','huge_exponent'])
def test_bad_response_never_persists_and_error_is_safe(service,mutation):
    original=SyntheticHistoryTransport(service.clock)
    class Bad:
        provider='SYNTHETIC_TEST'
        def fetch(self,request):
            response=original.fetch(request)
            if mutation=='future':response['received_at']=(service.clock()+timedelta(days=1)).isoformat()
            if mutation=='negative':response['bars'][0]['open']='-1'
            if mutation=='missing':response['completed']=False
            if mutation=='wrong_provider':response['provider']='IBKR_TWS'
            if mutation=='duplicate':response['bars'].append(response['bars'][0])
            if mutation=='huge_exponent':response['bars'][0]['open']='1e-1000000'
            return response
    service.transport=Bad();service.enqueue('bad',one());service.step('bad')
    assert service.store.status('bad')['units'][0]['state']=='FAILED'
    assert count(service,SNAPSHOTS)==0


def test_storage_block_does_not_consume_attempt_or_fetch(service):
    service.enqueue('a',one());service.storage.block='DATA_LIMIT'
    assert service.step('a')==dict(worked=False,state='STORAGE_DATA_LIMIT')
    assert service.store.status('a')['units'][0]['attempts']==0 and count(service,BUDGET)==0
    service.storage.block=None;assert service.step('a')['state']=='COLLECTED'


def test_future_and_fake_real_targets_cannot_be_enqueued(service):
    with pytest.raises(ValueError):service.enqueue('future',one()|{'end':str(service.clock().date())})
    req=one();req['provider']='IBKR_TWS'
    with pytest.raises(ValueError):service.enqueue('fake',req)


def test_master_models_and_quant_are_untouched(client):
    engine=client.app.state.engine
    tables=['portfolios','ledger_events','ledger_entries','valuation_snapshots','company_models','quant_trials']
    def snapshot():
        with engine.connect() as c:return {t:[tuple(r) for r in c.execute(text('SELECT * FROM '+t))] for t in tables}
    before=snapshot();service=HistoryService(engine,storage=Guard())
    service.enqueue('test-master',one());drain(service,'test-master')
    assert snapshot()==before
    assert client.post('/api/orders',json={'mode':'paper'}).status_code==403


def test_populated_batch_migration_refuses_drop(service):
    from alembic import command
    from alembic.config import Config
    from app.config import ROOT
    service.enqueue('keep',one())
    with pytest.raises(RuntimeError,match='Preservar'):
        command.downgrade(Config(str(ROOT/'alembic.ini')),'0014_quant_lab')
    assert count(service,UNITS)==1


def test_numeric_equivalence_shares_one_snapshot(service):
    original=SyntheticHistoryTransport(service.clock)
    class Equivalent:
        provider='SYNTHETIC_TEST'
        variant=False
        def fetch(self,request):
            result=original.fetch(request)
            for bar in result['bars']:
                bar['volume']='-0.00' if self.variant else '0'
                if self.variant:
                    for key in ('open','high','low','close'):bar[key]+='.000'
            return result
    adapter=Equivalent();service.transport=adapter
    service.enqueue('a',one());drain(service,'a')
    adapter.variant=True
    service.enqueue('b',one()|{'revision':'refresh'});drain(service,'b')
    assert service.store.status('b')['units'][0]['state']=='SUCCEEDED'
    assert count(service,SNAPSHOTS)==1


def test_pause_before_fetch_releases_unused_provider_lease(service,monkeypatch):
    service.enqueue('a',one())
    owned=service.store.owned
    def pause_first(c,job,now):
        service.store.control('a','pause',now)
        return owned(c,job,now)
    monkeypatch.setattr(service.store,'owned',pause_first)
    assert service.step('a')['state']=='CLAIM_LOST'
    with service.engine.connect() as c:
        assert c.scalar(select(BUDGET.c.token)) is None
    monkeypatch.setattr(service.store,'owned',owned)
    service.control('a','resume')
    assert service.step('a')['state']=='COLLECTED'

"""Synthetic disk budgets and queue recovery. Never fill or prune the user's disk."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from types import SimpleNamespace
import threading
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import DataQuota
from app.storage_budget import StorageGovernor, StorageSettings, StorageBlocked, scan_tree, MIB, GIB
from app.market_store import JOBS, RECEIPTS
from app.sec_store import TASKS
from app.universe_service import UniverseService
from app.company_service import CompanyService
from test_market_data import market
from test_sec_financials import service


def policy(**changes):
    return StorageSettings(_env_file=None, **changes)


def guard(tmp_path, **changes):
    return StorageGovernor(tmp_path/'data', tmp_path/'output', policy(**changes),
                           disk_usage=lambda _:SimpleNamespace(free=100*GIB))


def test_counts_sqlite_wal_originals_models_backups_once(tmp_path):
    g = guard(tmp_path)
    for path,size in [(g.data_root/'hq.db',31),(g.data_root/'hq.db-wal',7),
                      (g.data_root/'sec/raw/one.gz',11),(g.output_root/'backup.db',41),
                      (g.output_root/'models/test.gguf',23)]:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x'*size)
    status = g.status()
    assert status['data']['bytes']==49 and status['output']['bytes']==64
    assert status['total_bytes']==113 and status['automatic_deletion'] is False
    assert len(scan_tree(g.output_root, entries=True)['entries'])==2


@pytest.mark.parametrize('changes,expected',[
    ({'storage_data_limit_mib':1},'DATA_LIMIT'),
    ({'storage_total_limit_mib':1},'TOTAL_LIMIT')])
def test_checks_reserve_before_writing_and_releases_on_refusal(tmp_path,changes,expected):
    g = guard(tmp_path,**changes)
    with pytest.raises(StorageBlocked, match=expected):
        with g.admission():pytest.fail('must not admit')
    g.policy = policy()
    with g.admission():pass
    assert g.status()['acquisition_allowed']


def test_output_pressure_also_blocks_financial_captures(tmp_path):
    g = guard(tmp_path,storage_output_limit_mib=1)
    g.output_root.mkdir();(g.output_root/'old-evidence.bin').write_bytes(b'x'*(MIB+1))
    assert g.status()['reason']=='OUTPUT_LIMIT'
    with pytest.raises(StorageBlocked):
        with g.admission():pass
    assert (g.output_root/'old-evidence.bin').stat().st_size==MIB+1


def test_free_space_floor_includes_reserve_and_exact_boundary(tmp_path):
    g = guard(tmp_path)
    g.disk_usage=lambda _:SimpleNamespace(free=(5120+512)*MIB-1)
    assert g.status()['reason']=='FREE_SPACE'
    g.disk_usage=lambda _:SimpleNamespace(free=(5120+512)*MIB)
    assert g.status()['acquisition_allowed']


def test_scan_error_is_not_an_empty_disk(tmp_path,monkeypatch):
    g=guard(tmp_path);g.data_root.mkdir()
    monkeypatch.setattr('app.storage_budget.os.scandir',lambda _:(_ for _ in ()).throw(PermissionError()))
    assert g.status()['reason']=='INVENTORY_UNAVAILABLE'


def test_nested_and_competing_governors_cannot_spend_same_reserve(tmp_path):
    g=guard(tmp_path);other=guard(tmp_path)
    with g.admission():
        with g.admission():pass
        with pytest.raises(StorageBlocked,match='BUSY'):
            with other.admission():pass
    with other.admission():pass


def test_exception_releases_os_lease(tmp_path):
    g=guard(tmp_path)
    with pytest.raises(RuntimeError):
        with g.admission():raise RuntimeError('synthetic')
    with guard(tmp_path).admission():pass


def test_domain_permission_error_is_not_relabelled_as_disk_error(tmp_path):
    with pytest.raises(PermissionError,match='SOURCE_UNAVAILABLE'):
        with guard(tmp_path).admission():raise PermissionError('SOURCE_UNAVAILABLE')


def test_unknown_reference_is_blocked_known_runtime_is_not_double_counted(tmp_path):
    target=tmp_path/'dependencies';target.mkdir();(target/'file').write_bytes(b'x'*8)
    folder=tmp_path/'evidence';folder.mkdir()
    if __import__('os').name=='nt':
        import subprocess
        # Only creates a junction in pytest's temporary directory; never deletes/moves a target.
        subprocess.run(['cmd','/c','mklink','/J',str(folder/'link'),str(target)],check=True,capture_output=True)
    else:
        (folder/'link').symlink_to(target,target_is_directory=True)
    assert scan_tree(folder)['errors']==1
    result=scan_tree(folder,runtime_roots=(target,),entries=True)
    assert result['bytes']==0 and result['runtime_links']==1 and result['errors']==0
    assert result['entries'][0]['runtime_reference'] is True


def test_serialized_threads_recheck_consumed_budget(tmp_path):
    g=guard(tmp_path,storage_data_limit_mib=129,storage_unit_reserve_mib=128)
    entered=threading.Event();release=threading.Event()
    def first():
        with g.admission():
            entered.set();assert release.wait(5)
            (g.data_root/'evidence').write_bytes(b'x'*(2*MIB))
    def second():
        with pytest.raises(StorageBlocked,match='DATA_LIMIT'):
            with g.admission():pytest.fail('stale budget')
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(first);assert entered.wait(5);b=pool.submit(second)
        release.set();a.result();b.result()


def test_market_pause_survives_new_governor_and_preserves_attempts(market):
    s=market;s.enqueue('storage-pending-market',dict(kind='catalogue'))
    g=s.data.storage;g.policy=policy(storage_data_limit_mib=1)
    for _ in range(3):assert s.step() is False
    assert not s.http.calls
    with s.data.engine.connect() as c:
        row=c.execute(select(JOBS)).mappings().one()
        assert row['state']=='QUEUED' and row['attempts']==0
        assert c.scalar(select(func.count()).select_from(RECEIPTS))==0
        assert c.scalar(select(func.count()).select_from(DataQuota))==0
    s.data.storage=StorageGovernor(g.data_root,g.output_root,policy())
    assert s.step() and len(s.http.calls)==1
    assert s.store.job('storage-pending-market')['state']=='SUCCEEDED'


def test_sec_pause_and_recovery_do_not_lose_pending_tasks(service):
    s=service;s.enqueue('storage-pending-sec',['0000000001'])
    g=s.data.storage;g.policy=policy(storage_data_limit_mib=1)
    for _ in range(2):assert not s.step()
    assert not s.calls
    with s.data.engine.connect() as c:
        rows=list(c.execute(select(TASKS)).mappings())
        assert all(r['state']=='PENDING' and r['attempts']==0 for r in rows)
    g.policy=policy();assert s.step() and len(s.calls)==1


def test_new_catalogue_models_and_imports_fail_before_network(service):
    s=service;s.data.storage.policy=policy(storage_data_limit_mib=1)
    universe=UniverseService(s.data,SimpleNamespace(fetch_sec=lambda:pytest.fail('network')))
    for action in [lambda:universe.sync('storage-catalogue'),
                   lambda:s.enqueue('storage-sec',['0000000001']),
                   lambda:CompanyService(s).build('0000000001','storage-model')]:
        with pytest.raises(StorageBlocked):action()
    assert not s.calls


def test_generic_sources_do_not_fetch_or_charge_quota_when_blocked(service):
    data=service.data;data.storage.policy=policy(storage_data_limit_mib=1)
    data.http=SimpleNamespace(real=True,fetch=lambda _:pytest.fail('network'))
    with Session(data.engine) as s:before=[(r.key,r.used) for r in s.scalars(select(DataQuota))]
    result=data.query('A21')
    assert not result.usable and result.state=='ERROR' and 'presupuesto' in result.reason
    with Session(data.engine) as s:assert before==[(r.key,r.used) for r in s.scalars(select(DataQuota))]


def test_local_status_is_read_only_and_orders_stay_forbidden(client):
    response=client.get('/api/storage/status')
    assert response.status_code==200
    body=response.json()
    assert body['automatic_deletion'] is False and body['policy']=='local-storage-v1'
    assert 'secret' not in json.dumps(body).lower()
    assert client.post('/api/orders',json={}).status_code==403

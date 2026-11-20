"""Parent resource/timeout boundaries with no SDK, network or live settings."""
from contextlib import nullcontext
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import pytest
from app.config import ROOT
from app.storage_budget import StorageBlocked


@pytest.fixture
def parent(tmp_path,monkeypatch,settings):
    spec=importlib.util.spec_from_file_location('d1_parent_test',ROOT/'scripts/ibkr_data_probe.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    config=tmp_path/'.tools/ibkr/pilot.json'
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(dict(host='127.0.0.1',port=7497,client_id=27,
        read_only_confirmed_in_tws=True,paper_account_sha256=sha256(b'DU123456').hexdigest())))
    target=tmp_path/'output/probe.json'
    monkeypatch.setattr(sys,'argv',['probe','--output',str(target)])
    class Guard:
        def __init__(self,*args): pass
        def admission(self,**kwargs): return nullcontext()
    monkeypatch.setattr('app.storage_budget.StorageGovernor',Guard)
    return module,target


@pytest.mark.parametrize('case,state',[('timeout','PROBE_TIMEOUT'),('large','WORKER_FAILED'),
    ('failure','WORKER_FAILED'),('malformed','WORKER_FAILED'),('array','WORKER_PROTOCOL_ERROR')])
def test_worker_failures_are_bounded_and_recorded(parent,monkeypatch,case,state):
    module,target=parent
    def run(*args,**kwargs):
        assert kwargs['timeout']==70
        if case=='timeout': raise subprocess.TimeoutExpired('worker',70)
        payload={'large':b'x'*(module.MAX_REPORT_BYTES+1),'malformed':b'secret text',
                 'array':b'[]','failure':b'private failure'}[case]
        return SimpleNamespace(returncode=1 if case=='failure' else 0,stdout=payload)
    monkeypatch.setattr(module.subprocess,'run',run)
    with pytest.raises(SystemExit) as exc: module.main()
    assert exc.value.code==2
    report=json.loads(target.read_text(encoding='utf-8'))
    assert report==dict(state=state,orders_enabled=False)


def test_storage_busy_never_starts_worker_or_writes_report(parent,monkeypatch):
    module,target=parent
    class Busy:
        def __init__(self,*args): pass
        def admission(self,**kwargs): raise StorageBlocked('BUSY')
    monkeypatch.setattr('app.storage_budget.StorageGovernor',Busy)
    def forbidden(*args,**kwargs): pytest.fail('worker started before storage admission')
    monkeypatch.setattr(module.subprocess,'run',forbidden)
    with pytest.raises(SystemExit) as exc: module.main()
    assert exc.value.code==2 and not target.exists()

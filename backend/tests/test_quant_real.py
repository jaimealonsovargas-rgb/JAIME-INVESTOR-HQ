from copy import deepcopy
from datetime import datetime,timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from app.admission_contracts import fingerprint
from app.b32_review import PROTOCOL,PROTOCOL_SHA256
from app.dataset_admission import evaluate
from app.quant_engine import ExperimentRejected
from app.quant_real import planned_configs,run_retrospective,admitted_replay,RetrospectiveDataset
from app.quant_store import TrialRegistry
from app.database import create_db_engine
from app.storage_budget import StorageGovernor
from app.dataset_manifests import ManifestStore
from test_retrospective_admission import retro_bundle,reseal

NOW=datetime(2024,2,1,tzinfo=timezone.utc)


def request(monkeypatch):
    c,e=retro_bundle(monkeypatch)
    m=evaluate(c,e,protocol=PROTOCOL)
    data=dict(kind='MARKET_RETROSPECTIVE',candidate=c,manifest_id=m['manifest_id'],protocol_sha256=PROTOCOL_SHA256)
    return data,e,m,SimpleNamespace(read=lambda _:m)


def test_real_controls_manual_arithmetic_and_common_warmup(monkeypatch):
    data,_,m,store=request(monkeypatch)
    for name,cfg in planned_configs():
        r=run_retrospective(data,cfg,store,NOW)
        assert r['kind']=='MARKET_RETROSPECTIVE' and r['unit']=='USD'
        assert r['acceptance']=='EXPLORATORY_ONLY' and not r['execution_ready']
        assert r['warmup_sessions']==60 and r['evaluation_sessions']==192
        assert all(p['shares']==0 and Decimal(p['equity'])==10000 for p in r['curve'][:60])
        assert all(f['at']>=r['evaluation_start'] for f in r['fills'])
        if name=='buy_hold-base':
            assert r['fills'][0]['at']==r['evaluation_start']
            assert r['final_shares']==99
            assert Decimal(r['commission'])==Decimal('.99')
            assert Decimal(r['final_cash'])==Decimal('94.06')
            assert Decimal(r['final_equity'])==Decimal('10093.06')
            assert len(r['fills'])==1  # No terminal fictitious liquidation.
        if name.startswith(('cash','sma')):
            assert not r['fills']  # Flat closes equal their SMA => cash.


def test_real_future_close_cannot_change_previous_or_same_day_decision(monkeypatch):
    data,e,_,store=request(monkeypatch)
    cfg=dict(planned_configs())['sma20-base']
    original=run_retrospective(data,cfg,store,NOW)
    data['candidate']['bars'][80].update(close='110',high='111')
    reseal(data['candidate'],e)
    m=evaluate(data['candidate'],e,protocol=PROTOCOL)
    data['manifest_id']=m['manifest_id']
    changed=run_retrospective(data,cfg,SimpleNamespace(read=lambda _:m),NOW)
    assert changed['decisions'][:81]==original['decisions'][:81]
    assert changed['decisions'][81]['outcome']=='BUY'


@pytest.mark.parametrize('case',['expired','clock_before_review','missing_manifest','changed_manifest','changed_bars','grid','protocol','unreviewed','wrong_kind'])
def test_real_run_rejects_missing_or_changed_admission(monkeypatch,case):
    data,e,m,store=request(monkeypatch)
    cfg=deepcopy(planned_configs()[0][1]);now=NOW
    if case=='expired': now=datetime(2024,3,2,tzinfo=timezone.utc)
    if case=='clock_before_review': now=datetime(2024,1,31,tzinfo=timezone.utc)
    if case=='missing_manifest':
        def missing(_): raise FileNotFoundError()
        store=SimpleNamespace(read=missing)
    if case=='changed_manifest': data['manifest_id']='0'*64
    if case=='changed_bars': data['candidate']['bars'][0]['close']='99'
    if case=='grid': cfg['costs']['slippage_bps']='0'
    if case=='protocol': data['protocol_sha256']='0'*64
    if case=='unreviewed':
        from app import dataset_evidence
        monkeypatch.setattr(dataset_evidence,'trusted_registry',lambda:{})
    if case=='wrong_kind': data['kind']='SYNTHETIC_TEST'
    with pytest.raises((ExperimentRejected,ValidationError)):
        run_retrospective(data,cfg,store,now)


def test_real_registry_persists_once_and_rechecks_review(migrated,monkeypatch):
    data,e,m,_=request(monkeypatch)
    engine=create_db_engine(migrated.database_url)
    store=ManifestStore(StorageGovernor.for_engine(engine));store.publish(m)
    registry=TrialRegistry(engine,clock=lambda:NOW)
    cfg=dict(planned_configs())['buy_hold-base']
    row=registry.submit('real-unit',data,cfg)
    assert row['state']=='QUEUED' and row['result'] is None
    result=registry.run('real-unit')
    assert result['state']=='COMPLETED' and result['result']['acceptance']=='EXPLORATORY_ONLY'
    assert registry.run('real-unit')==result
    assert [e['state'] for e in registry.events('real-unit')]==['QUEUED','RUNNING','COMPLETED']
    registry.submit('real-expired',data,cfg)
    registry.clock=lambda:datetime(2024,3,2,tzinfo=timezone.utc)
    rejected=registry.run('real-expired')
    assert rejected['state']=='REJECTED' and rejected['reason']=='DATASET_REVIEW_EXPIRED_OR_CLOCK_INVALID'
    engine.dispose()

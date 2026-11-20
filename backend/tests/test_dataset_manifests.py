"""Immutable publication, integrity, quota and crash behavior in private temp paths."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest
from app.data_identity import fingerprint
from app.dataset_manifests import ManifestStore, canonical
from app.storage_budget import StorageGovernor, StorageSettings, StorageBlocked


@pytest.fixture
def store(tmp_path):
    policy = StorageSettings(_env_file=None, storage_min_free_mib=1024)
    return ManifestStore(StorageGovernor(tmp_path/'data', tmp_path/'output', policy=policy))


def manifest():
    value = dict(version='admission-manifest-v1', candidate_hash='a'*64,
                 checks=[{'code': 'SOURCE', 'state': 'BLOCKED'}], readiness={'backtest': 'BLOCKED'}, source_refs=[])
    return dict(value, manifest_id=fingerprint(value))


def test_immutable_idempotent_canonical_record(store):
    value = manifest()
    key = store.publish(value)
    before = (store.root/(key+'.json')).stat().st_mtime_ns
    assert store.publish(value) == key and store.read(key) == value
    assert (store.root/(key+'.json')).stat().st_mtime_ns == before
    assert list(store.root.glob('*.tmp')) == []


def test_modified_manifest_never_replaced(store):
    value = manifest(); key = store.publish(value)
    path = store.root/(key+'.json')
    bad = dict(value, readiness={'backtest': 'BACKTEST_READY'})
    path.write_bytes(canonical(bad))
    with pytest.raises(ValueError, match='HASH_MISMATCH'):
        store.read(key)
    with pytest.raises(ValueError, match='HASH_MISMATCH'):
        store.publish(value)
    assert json.loads(path.read_bytes()) == bad


def test_path_traversal_rejected(store):
    for key in ('../outside', 'x'*64, 'a'*65):
        with pytest.raises(ValueError, match='INVALID_MANIFEST_ID'):
            store.read(key)


def test_storage_denial_no_record_or_partial_file(store, monkeypatch):
    monkeypatch.setattr(store.storage, 'status', lambda **kw: {'acquisition_allowed': False, 'reason': 'OUTPUT_LIMIT'})
    with pytest.raises(StorageBlocked):
        store.publish(manifest())
    assert not store.root.exists()


def test_crash_before_publish_leaves_no_complete_manifest(store, monkeypatch):
    def fail(*args):
        raise OSError('simulated publish failure')
    monkeypatch.setattr('app.dataset_manifests.publish_no_replace', fail)
    with pytest.raises(OSError):
        store.publish(manifest())
    assert list(store.root.iterdir()) == []


def test_concurrent_publication_same_record(store):
    value = manifest()
    with ThreadPoolExecutor(max_workers=3) as pool:
        keys = list(pool.map(lambda _: store.publish(value), range(6)))
    assert len(set(keys)) == 1 and store.read(keys[0]) == value
    assert len(list(store.root.glob('*.json'))) == 1


def test_noncanonical_and_oversized_records_rejected(store):
    value = manifest(); key = store.publish(value)
    path = store.root/(key+'.json')
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')
    with pytest.raises(ValueError, match='CONTENT_MISMATCH'):
        store.read(key)
    huge = dict(value, extra='x'*(1024*1024))
    huge['manifest_id'] = fingerprint({k:v for k,v in huge.items() if k != 'manifest_id'})
    with pytest.raises(ValueError, match='TOO_LARGE'):
        store.publish(huge)

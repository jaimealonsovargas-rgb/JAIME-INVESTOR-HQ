"""Content-addressed, immutable admission records. No bars or database writes."""
import json
import os
from pathlib import Path
import re
import stat
from uuid import uuid4
from app.data_identity import fingerprint
from app.storage_budget import MIB

MAX_MANIFEST_BYTES = MIB


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def publish_no_replace(source, target):
    if os.name == 'nt':
        # Windows rename is atomic on this volume and refuses an existing target.
        os.rename(source, target)
    else:
        os.link(source, target)


class ManifestStore:
    def __init__(self, storage):
        self.storage = storage
        self.root = Path(storage.output_root).absolute() / 'dataset-manifests'

    def _safe_root(self, create=False):
        # Reject directory links/junctions, including any redirected ancestor.
        if self.root.resolve() != self.root.absolute():
            raise ValueError('MANIFEST_PATH_REDIRECTED')
        if create:
            self.root.mkdir(parents=True, exist_ok=True)
        if self.root.exists() and not self.root.is_dir():
            raise ValueError('MANIFEST_PATH_INVALID')

    def _path(self, manifest_id):
        if not isinstance(manifest_id, str) or not re.fullmatch('[a-f0-9]{64}', manifest_id):
            raise ValueError('INVALID_MANIFEST_ID')
        path = self.root / (manifest_id + '.json')
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('MANIFEST_PATH_REDIRECTED')
        return path

    @staticmethod
    def verify(manifest):
        if not isinstance(manifest, dict):
            raise ValueError('INVALID_MANIFEST')
        ident = manifest.get('manifest_id')
        if fingerprint({k: v for k, v in manifest.items() if k != 'manifest_id'}) != ident:
            raise ValueError('MANIFEST_HASH_MISMATCH')
        if not all(k in manifest for k in ('version', 'candidate_hash', 'checks', 'readiness', 'source_refs')):
            raise ValueError('MANIFEST_FIELDS_MISSING')
        return ident

    def read(self, manifest_id):
        self._safe_root()
        path = self._path(manifest_id)
        with path.open('rb') as stream:
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError('MANIFEST_TOO_LARGE')
        result = json.loads(raw)
        if self.verify(result) != manifest_id or raw != canonical(result):
            raise ValueError('MANIFEST_CONTENT_MISMATCH')
        return result

    def publish(self, manifest):
        manifest_id = self.verify(manifest)
        raw = canonical(manifest)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError('MANIFEST_TOO_LARGE')
        with self.storage.admission(reserve=2 * MAX_MANIFEST_BYTES, destination='output'):
            self._safe_root(create=True)
            target = self._path(manifest_id)
            if target.exists():
                if canonical(self.read(manifest_id)) != raw:
                    raise ValueError('MANIFEST_CONTENT_MISMATCH')
                return manifest_id
            temporary = self.root / ('.' + uuid4().hex + '.tmp')
            try:
                with temporary.open('xb') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                # Atomic no-replace publication on the same local filesystem.
                try:
                    publish_no_replace(temporary, target)
                except FileExistsError:
                    if canonical(self.read(manifest_id)) != raw:
                        raise ValueError('MANIFEST_CONTENT_MISMATCH') from None
                if canonical(self.read(manifest_id)) != raw:
                    raise ValueError('MANIFEST_CONTENT_MISMATCH')
            finally:
                temporary.unlink(missing_ok=True)
        return manifest_id

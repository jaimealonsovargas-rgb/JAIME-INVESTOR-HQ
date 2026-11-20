"""Admission for local acquisition; no automatic deletion or filesystem quota.

One OS lease covers network, archive and commit across cooperating processes.
The OS releases it on crash. Pending work and evidence remain intact.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
import os
from pathlib import Path
import shutil
import stat
import threading
from typing import Literal

from pydantic import BaseModel, Field, AwareDatetime
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from app.config import ROOT

MIB = 1024 ** 2
GIB = 1024 ** 3
POLICY_VERSION = 'local-storage-v1'
REASONS = {
    'READY': 'Hay margen para otra unidad de captación.',
    'DATA_LIMIT': 'El presupuesto de datos no admite otra unidad de captación.',
    'OUTPUT_LIMIT': 'Resultados y copias han alcanzado su presupuesto.',
    'TOTAL_LIMIT': 'El presupuesto conjunto no admite otra unidad de captación.',
    'FREE_SPACE': 'Se preserva el margen libre del disco para Windows y otras aplicaciones.',
    'INVENTORY_UNAVAILABLE': 'No se puede verificar el consumo; captación detenida.',
    'BUSY': 'Otra unidad de captación conserva la reserva de escritura.',
}


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT/'.env', extra='ignore', frozen=True,
                                     hide_input_in_errors=True)
    storage_data_limit_mib: int = Field(4096, ge=1, le=1048576)
    storage_output_limit_mib: int = Field(12288, ge=1, le=1048576)
    storage_total_limit_mib: int = Field(16384, ge=1, le=1048576)
    storage_min_free_mib: int = Field(5120, ge=1024, le=1048576)
    storage_unit_reserve_mib: int = Field(512, ge=128, le=4096)


class StorageBlocked(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__('STORAGE_'+reason)


class StorageUsage(BaseModel):
    bytes: int = Field(ge=0)
    files: int = Field(ge=0)
    errors: int = Field(ge=0)
    runtime_links: int = Field(ge=0)
    limit_bytes: int = Field(gt=0)


class StorageStatus(BaseModel):
    policy: Literal['local-storage-v1']
    measured_at: AwareDatetime
    state: Literal['READY','WARNING','BLOCKED']
    reason: Literal['READY','DATA_LIMIT','OUTPUT_LIMIT','TOTAL_LIMIT','FREE_SPACE','INVENTORY_UNAVAILABLE']
    message: str
    acquisition_allowed: bool
    data: StorageUsage
    output: StorageUsage
    total_bytes: int = Field(ge=0)
    total_limit_bytes: int = Field(gt=0)
    free_bytes: int | None = Field(ge=0)
    min_free_bytes: int = Field(ge=0)
    reserve_bytes: int = Field(ge=0)
    automatic_deletion: Literal[False]
    scope: str
    recovery: str


def scan_tree(root, *, exclude=(), entries=False, runtime_roots=()):
    """Logical file sizes; never follow links/junctions or hide incomplete scans."""
    root = Path(root)
    excluded = {Path(p).absolute() for p in exclude}
    runtime_roots = {Path(p).resolve() for p in runtime_roots}
    result = dict(bytes=0, files=0, errors=0, runtime_links=0, entries=[])
    def visit(folder):
        try:
            with os.scandir(folder) as stream:
                for item in stream:
                    path = Path(item.path)
                    if path.absolute() in excluded:
                        continue
                    try:
                        info = item.stat(follow_symlinks=False)
                        if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                            if path.resolve(strict=True) in runtime_roots:
                                result['runtime_links'] += 1
                                if entries:
                                    result['entries'].append(dict(path=path.relative_to(root).as_posix(),
                                        bytes=0, modified_ns=info.st_mtime_ns, runtime_reference=True))
                            else:
                                result['errors'] += 1
                        elif stat.S_ISDIR(info.st_mode):
                            visit(path)
                        elif stat.S_ISREG(info.st_mode):
                            result['bytes'] += info.st_size
                            result['files'] += 1
                            if entries:
                                result['entries'].append(dict(path=path.relative_to(root).as_posix(),
                                    bytes=info.st_size, modified_ns=info.st_mtime_ns))
                    except OSError:
                        result['errors'] += 1
        except OSError:
            result['errors'] += 1
    try:
        root.lstat()
        if root.is_symlink() or (hasattr(root, 'is_junction') and root.is_junction()):
            result['errors'] += 1
        else:
            visit(root)
    except FileNotFoundError:
        pass
    except OSError:
        result['errors'] += 1
    if not entries:
        result.pop('entries')
    return result


class StorageGovernor:
    def __init__(self, data_root, output_root, policy=None, disk_usage=shutil.disk_usage):
        self.data_root, self.output_root = Path(data_root), Path(output_root)
        self.policy = policy or StorageSettings()
        self.disk_usage = disk_usage
        # The saved visual reference links the same frontend dependencies. Count them once,
        # in the separate runtime inventory, never as downloaded financial evidence.
        self.runtime_roots = (ROOT/'frontend/node_modules',)
        self._lock, self._local = threading.RLock(), threading.local()

    @classmethod
    def for_engine(cls, engine):
        path = make_url(str(engine.url)).database
        if not path or path == ':memory:':
            import tempfile
            data = Path(tempfile.mkdtemp(prefix='jaime-storage-'))
        else:
            data = Path(path).resolve().parent
        output = ROOT/'output' if data == (ROOT/'data').resolve() else data/'storage-output'
        return cls(data, output)

    def status(self, *, reserve=None, destination='data'):
        reserve = self.policy.storage_unit_reserve_mib*MIB if reserve is None else reserve
        data = scan_tree(self.data_root, exclude=(self.output_root,), runtime_roots=self.runtime_roots)
        output = scan_tree(self.output_root, runtime_roots=self.runtime_roots)
        volumes, errors = [], data['errors']+output['errors']
        for root in (self.data_root, self.output_root):
            try:
                path = root
                while not path.exists():
                    path = path.parent
                volumes.append(self.disk_usage(path).free)
            except OSError:
                errors += 1
        p = self.policy
        total = data['bytes']+output['bytes']
        reason = 'READY'
        if errors:
            reason = 'INVENTORY_UNAVAILABLE'
        elif min(volumes) < p.storage_min_free_mib*MIB+reserve:
            reason = 'FREE_SPACE'
        elif data['bytes']+(reserve if destination=='data' else 0) > p.storage_data_limit_mib*MIB:
            reason = 'DATA_LIMIT'
        elif output['bytes']+(reserve if destination=='output' else 0) > p.storage_output_limit_mib*MIB:
            reason = 'OUTPUT_LIMIT'
        elif total+reserve > p.storage_total_limit_mib*MIB:
            reason = 'TOTAL_LIMIT'
        warning = (data['bytes'] >= p.storage_data_limit_mib*MIB*.8
                   or output['bytes'] >= p.storage_output_limit_mib*MIB*.8
                   or total >= p.storage_total_limit_mib*MIB*.8)
        return dict(policy=POLICY_VERSION, measured_at=datetime.now(timezone.utc).isoformat(),
            state='BLOCKED' if reason!='READY' else 'WARNING' if warning else 'READY',
            reason=reason, message=REASONS[reason], acquisition_allowed=reason=='READY',
            data=dict(**data, limit_bytes=p.storage_data_limit_mib*MIB),
            output=dict(**output, limit_bytes=p.storage_output_limit_mib*MIB),
            total_bytes=total, total_limit_bytes=p.storage_total_limit_mib*MIB,
            free_bytes=min(volumes) if volumes else None, min_free_bytes=p.storage_min_free_mib*MIB,
            reserve_bytes=reserve, automatic_deletion=False,
            scope='Datos, SQLite/WAL, originales, n8n local, resultados y copias. Entornos y herramientas se inventarían aparte.',
            recovery='Al recuperar margen, las tareas pendientes reanudan sin gastar intentos. Los ciclos vencidos conservan su plazo original.')

    @contextmanager
    def admission(self, *, reserve=None, destination='data'):
        with self._lock:
            if getattr(self._local, 'active', False):
                yield
                return
            stream = None
            locked = False
            try:
                self.data_root.mkdir(parents=True, exist_ok=True)
                stream = (self.data_root/'.storage-admission.lock').open('a+b')
                if stream.tell() == 0:
                    stream.write(b'0'); stream.flush()
                stream.seek(0)
                try:
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                except OSError:
                    raise StorageBlocked('BUSY') from None
                report = self.status(reserve=reserve, destination=destination)
                if not report['acquisition_allowed']:
                    raise StorageBlocked(report['reason'])
                self._local.active = True
                yield
            except OSError:
                if getattr(self._local, 'active', False):
                    raise  # Preserve domain PermissionError and write failures from the guarded operation.
                raise StorageBlocked('INVENTORY_UNAVAILABLE') from None
            finally:
                self._local.active = False
                if locked:
                    stream.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream, fcntl.LOCK_UN)
                if stream:
                    stream.close()


def admitted(fn):
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        with self.data.storage.admission():
            return fn(self, *args, **kwargs)
    return wrapped

"""Drains explicitly requested SEC imports; no schedule, agents or trading tools."""
import json
import threading
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.data_catalog import CATALOG
from app.data_http import FetchError
from app.sec_http import SecHttp, source_url, archive_raw
from app.sec_normalize import parse_companyfacts, parse_submissions
from app.sec_quota import reserve, backoff
from app.sec_store import SecStore
from app.universe_service import valid_sec_contact
from app.universe_store import utc_text
from app.storage_budget import admitted, StorageBlocked


class SecService:
    def __init__(self, data, http=None, raw_root=None):
        self.data = data
        self.store = SecStore(data.engine)
        self.http = http or SecHttp(data.settings)
        self.raw_root = Path(raw_root) if raw_root else Path(make_url(str(data.engine.url)).database).parent / 'sec' / 'raw'
        self._stop = threading.Event()
        self._thread = None
        self.worker_error = None
        self.cycle_coordinator = None

    def access(self):
        settings = self.data.settings
        if not settings.data_public_enabled or self.data.initial(CATALOG['A09']).state == 'DISABLED':
            return 'DISABLED'
        if not all((CATALOG['A09'].rights.access_allowed, CATALOG['A09'].rights.storage_allowed, CATALOG['A09'].rights.display_allowed)):
            return 'RIGHTS_RESTRICTED'
        if not valid_sec_contact(settings):
            return 'CONFIG_REQUIRED'
        return 'READY'

    @admitted
    def enqueue(self, key, ciks=None):
        state = self.access()
        if state != 'READY':
            raise ValueError(state)
        ident = self.store.enqueue(key, ciks, self.data.clock())
        return self.store.job(ident)

    def summary(self):
        return {**self.store.summary(), 'access': self.access(),
                'worker_running': bool(self._thread and self._thread.is_alive()), 'worker_error': self.worker_error}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name='sec-import-worker', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=55)

    def _run(self):
        while not self._stop.is_set():
            try:
                worked = self.step()
                self.worker_error = None
            except Exception:
                # No response bodies, credentials or untrusted exception text in logs/UI.
                self.worker_error = 'LOCAL_WORKER_ERROR'
                worked = False
            self._stop.wait(0.1 if worked else 1)

    def step(self):
        if self.cycle_coordinator and self.cycle_coordinator.step():
            return True
        try:
            result = self._admitted_step()
            self.storage_block = None
            return result
        except StorageBlocked as error:
            self.storage_block = str(error)
            return False

    @admitted
    def _admitted_step(self):
        now = self.data.clock()
        # Pause acquisition automatically while configuration/rights disallow it.
        if self.access() != 'READY':
            return False
        from app.company_updates import process_update
        if process_update(self):
            return True
        task = self.store.claim(now)
        if task is None:
            return False
        with Session(self.data.engine) as s, s.begin():
            s.connection().exec_driver_sql('BEGIN IMMEDIATE')
            blocked = reserve(s, now)
        if blocked:
            self.store.defer(task, blocked, 'RATE_LIMITED', now)
            return False
        try:
            raw = self.http.fetch(task['cik'], task['kind'])
            received = self.data.clock()
            body = json.loads(raw, parse_float=Decimal)
            parser = parse_companyfacts if task['kind'] == 'companyfacts' else parse_submissions
            rows, metadata = parser(body, task['cik'])
            digest = archive_raw(self.raw_root, raw)
            self.store.accept(task, rows, metadata, digest, source_url(task['cik'], task['kind']), received, self.data.clock())
        except FetchError as error:
            now = self.data.clock()
            delay = max(60, error.retry_after) if error.state == 'RATE_LIMITED' else min(60, 5 * 3 ** task['attempts'])
            if error.state in ('RATE_LIMITED', 'RIGHTS_RESTRICTED'):
                with Session(self.data.engine) as s, s.begin():
                    s.connection().exec_driver_sql('BEGIN IMMEDIATE')
                    backoff(s, now, delay)
            self.store.defer(task, utc_text(now + timedelta(seconds=delay)), error.state, now, attempted=True,
                terminal=error.state in ('NOT_FOUND', 'AUTH_FAILED', 'RIGHTS_RESTRICTED', 'INVALID_PAYLOAD', 'CONFIG_REQUIRED'))
            if error.state in ('AUTH_FAILED', 'RIGHTS_RESTRICTED'):
                # A provider-wide rejection must not generate one failed call per issuer.
                self.store.control(task['job_id'], 'pause', now)
        except (ValueError, KeyError, TypeError, IndexError, InvalidOperation, OverflowError, AttributeError):
            self.store.defer(task, utc_text(self.data.clock()), 'INVALID_PAYLOAD', self.data.clock(), attempted=True, terminal=True)
        except OSError:
            self.store.defer(task, utc_text(self.data.clock() + timedelta(seconds=30)), 'LOCAL_STORAGE_ERROR', self.data.clock(), attempted=True)
        return True

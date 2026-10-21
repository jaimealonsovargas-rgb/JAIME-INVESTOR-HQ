"""One bounded public-data worker; durable due times, no LLM or broker calls."""
import threading
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import DataRefresh
from app.data_catalog import CATALOG
from app.data_rights import readable

# Explicit exclusions remain even if credentials are configured in .env.
BROKER_SOURCES = frozenset({'B04', 'B05'})


def interval(source):
    # Polling cadence is not publication frequency or a promise of real-time data.
    return max(300, source.ttl)


def next_success_at(source, checked_at, attempted_at):
    # A cache hit retains the original check: restarting must not extend its life.
    return max(checked_at + timedelta(seconds=interval(source)),
               attempted_at + timedelta(seconds=300))


class DataRefresher:
    def __init__(self, data):
        self.data = data
        self.stop_event = threading.Event()
        self.thread = None
        self.last_error = None

    def eligible(self, source):
        return (source.id not in BROKER_SOURCES and source.implemented
                and self.data.initial(source).state == 'NOT_VERIFIED'
                and readable(source.rights, local_research=True))

    def tick(self):
        for source in CATALOG.values():
            if self.stop_event.is_set():
                break
            if not self.eligible(source):
                continue
            now = self.data.clock()
            with Session(self.data.engine) as session, session.begin():
                session.connection().exec_driver_sql('BEGIN IMMEDIATE')
                row = session.get(DataRefresh, source.id)
                if row and not row.failures and row.succeeded_at and row.attempted_at and row.state in ('AVAILABLE_VERIFIED', 'DELAYED', 'STALE'):
                    capped = next_success_at(source, datetime.fromisoformat(row.succeeded_at), datetime.fromisoformat(row.attempted_at))
                    row.next_due_at = min(datetime.fromisoformat(row.next_due_at), capped).isoformat()
                if row and datetime.fromisoformat(row.next_due_at) > now:
                    continue
                # Lease exceeds transport deadline and prevents overlapping backend instances.
                lease = (now + timedelta(seconds=120)).isoformat()
                if row is None:
                    row = DataRefresh(access_id=source.id, next_due_at=lease, failures=0, state='RUNNING')
                    session.add(row)
                row.next_due_at, row.attempted_at, row.state = lease, now.isoformat(), 'RUNNING'
            result = self.data.query(source.id)
            now = self.data.clock()
            with Session(self.data.engine) as session, session.begin():
                row = session.get(DataRefresh, source.id)
                success = result.real_connection and result.state in ('AVAILABLE_VERIFIED', 'DELAYED', 'STALE')
                row.failures = 0 if success else min(row.failures + 1, 8)
                row.state = result.state
                if success:
                    row.succeeded_at = result.checked_at.isoformat()
                delay = interval(source) if success else min(86400, 300 * 2 ** (row.failures - 1))
                row.next_due_at = (next_success_at(source, result.checked_at, now)
                                   if success else now + timedelta(seconds=delay)).isoformat()

    def status(self):
        with Session(self.data.engine) as session:
            rows = {r.access_id: r for r in session.scalars(select(DataRefresh))}
            sources = []
            for source in CATALOG.values():
                row = rows.get(source.id)
                sources.append(dict(access_id=source.id, eligible=self.eligible(source),
                    cadence_seconds=interval(source), state=row.state if row else 'NOT_STARTED',
                    attempted_at=row.attempted_at if row else None,
                    succeeded_at=row.succeeded_at if row else None,
                    next_due_at=row.next_due_at if row else None, failures=row.failures if row else 0))
        return dict(enabled=self.data.settings.data_auto_refresh_enabled,
            running=bool(self.thread and self.thread.is_alive()), concurrency=1,
            last_error=self.last_error, sources=sources,
            note='Solo con backend encendido. Cadencia de consulta, no calendario de publicación ni tiempo real.')

    def start(self):
        if not self.data.settings.data_auto_refresh_enabled or not self.data.http.real or (self.thread and self.thread.is_alive()):
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name='hq-public-data', daemon=True)
        self.thread.start()

    def _loop(self):
        # Let the office and local API finish startup before network work.
        if self.stop_event.wait(30):
            return
        while not self.stop_event.is_set():
            try:
                self.tick()
                self.last_error = None
            except Exception:
                # Do not expose payloads, headers or credentials. Lease persists across recovery.
                self.last_error = 'REFRESH_FAILED'
            if self.stop_event.wait(60):
                return

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()  # Transport deadlines bound in-flight work before engine disposal.

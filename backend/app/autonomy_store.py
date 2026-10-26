"""Atomic due-slot reservation and durable routing checkpoints, outside the ledger."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from app.autonomy_contracts import AutonomyEvent, ResearchTask, POLICY_ID, TERMINAL
from app.autonomy_schema import TABLES
from app.research_contracts import canonical, digest, utc
from app.research_store import ResearchStore, write_policy


def autonomy_write_policy(action, table, column, database, trigger):
    if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE):
        return sqlite3.SQLITE_OK if table in (*TABLES, 'audit_events') else sqlite3.SQLITE_DENY
    return write_policy(action, table, column, database, trigger)


class AutonomyStore:
    def __init__(self, engine, clock=None):
        self.engine = engine
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.research = ResearchStore(engine)

    @contextmanager
    def connection(self, write=False):
        connection = self.engine.raw_connection()
        raw = connection.driver_connection
        raw.set_authorizer(autonomy_write_policy)
        try:
            if write:
                raw.execute('BEGIN IMMEDIATE')
            yield raw
            if write:
                raw.commit()
        except BaseException:
            raw.rollback()
            raise
        finally:
            raw.set_authorizer(None)
            connection.close()

    def initialize(self, settings):
        with self.connection(True) as c:
            row = c.execute('SELECT payload FROM autonomy_control WHERE id=?', (POLICY_ID,)).fetchone()
            if row:
                control = json.loads(row[0])
                # An interval change cannot bring an already reserved due slot forward.
                control['interval_seconds'] = settings.autonomy_interval_seconds
            else:
                control = dict(paused=False, interval_seconds=settings.autonomy_interval_seconds,
                               next_due_at=(self.clock() + timedelta(seconds=settings.autonomy_startup_delay_seconds)).isoformat())
            c.execute('INSERT INTO autonomy_control VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (POLICY_ID, canonical(control)))

    def control(self):
        with self.connection() as c:
            row = c.execute('SELECT payload FROM autonomy_control WHERE id=?', (POLICY_ID,)).fetchone()
            return json.loads(row[0]) if row else None

    def tasks(self, active=False):
        with self.connection() as c:
            where = " WHERE state IN ('QUEUED','RUNNING')" if active else ''
            return [json.loads(r[0]) for r in c.execute('SELECT payload FROM research_tasks' + where + ' ORDER BY rowid DESC LIMIT 50')]

    def get(self, task_id):
        with self.connection() as c:
            row = c.execute('SELECT payload FROM research_tasks WHERE id=?', (task_id,)).fetchone()
            if not row:
                raise KeyError('NOT_FOUND')
            return json.loads(row[0])

    def reserve_due(self, settings):
        with self.connection(True) as c:
            control = json.loads(c.execute('SELECT payload FROM autonomy_control WHERE id=?', (POLICY_ID,)).fetchone()[0])
            now = self.clock()
            if not settings.autonomy_enabled or control['paused'] or datetime.fromisoformat(control['next_due_at']) > now:
                return None
            if c.execute("SELECT 1 FROM research_tasks WHERE state IN ('QUEUED','RUNNING') LIMIT 1").fetchone():
                return None
            key = digest({'policy': POLICY_ID, 'due_at': control['next_due_at'], 'source': settings.autonomy_source})
            event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, key))
            event = AutonomyEvent(id=event_id, created_at=now.isoformat(), due_at=control['next_due_at'], idempotency_key=key).model_dump()
            task = ResearchTask(id=event_id, event_id=event_id, created_at=now.isoformat(),
                                deadline_at=(now + timedelta(seconds=90)).isoformat(), run_key='autonomy-' + event_id).model_dump()
            c.execute('INSERT INTO autonomy_events VALUES (?,?,?)', (event_id, key, canonical(event)))
            c.execute('INSERT INTO research_tasks VALUES (?,?,?,?)', (task['id'], event_id, task['state'], canonical(task)))
            # Missed days coalesce into one run; never catch up in a burst.
            control['next_due_at'] = (now + timedelta(seconds=control['interval_seconds'])).isoformat()
            c.execute('UPDATE autonomy_control SET payload=? WHERE id=?', (canonical(control), POLICY_ID))
            self.research.audit(c, 'AUTONOMY_EVENT_RESERVED', event_id=event_id, task_id=task['id'], source_access_id=settings.autonomy_source)
            return task

    def update(self, task_id, **changes):
        with self.connection(True) as c:
            task = json.loads(c.execute('SELECT payload FROM research_tasks WHERE id=?', (task_id,)).fetchone()[0])
            if task['state'] in TERMINAL:
                return task  # A late HTTP result cannot revive cancellation.
            task.update(changes)
            if task['state'] in TERMINAL:
                task['finished_at'] = self.clock().isoformat()
            task = ResearchTask.model_validate(task).model_dump()
            c.execute('UPDATE research_tasks SET state=?,payload=? WHERE id=?', (task['state'], canonical(task), task_id))
            self.research.audit(c, 'AUTONOMY_TASK_UPDATED', task_id=task_id, state=task['state'], phase=task['phase'], result_hash=digest(task['result']) if task['result'] else None)
            return task

    def set_paused(self, paused, key):
        with self.connection(True) as c:
            audit_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'autonomy-control:' + key))
            previous = c.execute('SELECT payload FROM audit_events WHERE id=?', (audit_id,)).fetchone()
            if previous:
                if json.loads(previous[0])['paused'] != paused:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return False
            control = json.loads(c.execute('SELECT payload FROM autonomy_control WHERE id=?', (POLICY_ID,)).fetchone()[0])
            control['paused'] = paused
            c.execute('UPDATE autonomy_control SET payload=? WHERE id=?', (canonical(control), POLICY_ID))
            c.execute('INSERT INTO audit_events VALUES (?,?)', (audit_id, canonical(dict(id=audit_id, event='AUTONOMY_CONTROL', at=utc(), paused=paused))))
            return True

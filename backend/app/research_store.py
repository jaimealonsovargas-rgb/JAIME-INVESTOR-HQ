"""P4 connections enforce a SQLite write allowlist independently of model output."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from app.research_schema import TABLES
from app.research_contracts import canonical, digest, utc
from app.research_roles import ROLES, pipeline, TEMPLATE_VERSION
from app.research_planning import research_goal, planned_roles

TERMINAL = {'SUCCEEDED', 'FAILED', 'CANCELLED', 'BLOCKED', 'NO_LOCAL_MODEL'}


def write_policy(action, table, column, database, trigger):
    if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE) and table not in TABLES:
        return sqlite3.SQLITE_DENY
    if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_CREATE_TABLE):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


class ResearchStore:
    def __init__(self, engine):
        self.engine = engine

    @contextmanager
    def connection(self, write=False):
        conn = self.engine.raw_connection()
        raw = conn.driver_connection
        raw.set_authorizer(write_policy)
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
            conn.close()

    def initialize(self):
        with self.connection(True) as c:
            for role in ROLES.values():
                c.execute('INSERT INTO agents VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (role['role_id'], canonical(role)))

    def list(self, table, case_id=None):
        if table not in TABLES:
            raise PermissionError('TABLE_DENIED')
        with self.connection() as c:
            sql = f'SELECT payload FROM {table}' + (' WHERE case_id=?' if case_id else '') + ' ORDER BY rowid DESC LIMIT 500'
            return [json.loads(r[0]) for r in c.execute(sql, (case_id,) if case_id else ())]

    def get(self, table, key):
        if table not in TABLES:
            raise PermissionError('TABLE_DENIED')
        with self.connection() as c:
            row = c.execute(f'SELECT payload FROM {table} WHERE id=?', (key,)).fetchone()
            if not row:
                raise KeyError('NOT_FOUND')
            return json.loads(row[0])

    def audit(self, c, event, **fields):
        row = {'id': str(uuid.uuid4()), 'event': event, 'at': utc(), **fields}
        c.execute('INSERT INTO audit_events VALUES (?,?)', (row['id'], canonical(row)))

    def create_case(self, instrument, question, key, goal=None, origin=None):
        payload = {'id': str(uuid.uuid4()), 'instrument': instrument, 'question': question, 'created_at': utc(), 'thesis_version': 1}
        if goal is not None: payload['research_goal'] = goal
        if origin is not None: payload['origin'] = origin
        request_hash = digest({'instrument_id': instrument['id'], 'question': question, **({'research_goal': goal} if goal else {}), **({'origin': origin} if origin else {})})
        payload['request_hash'] = request_hash
        with self.connection(True) as c:
            old = c.execute('SELECT payload FROM research_cases WHERE request_key=?', (key,)).fetchone()
            if old:
                result = json.loads(old[0])
                if result['request_hash'] != request_hash:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return result
            c.execute('INSERT INTO research_cases VALUES (?,?,?,?)', (payload['id'], instrument['id'], key, canonical(payload)))
            self.audit(c, 'CASE_CREATED', case_id=payload['id'])
        return payload

    def enqueue(self, case_id, key, priority, refresh, depth=None, summary=False):
        case = self.get('research_cases', case_id)
        if depth not in (None, 'ordinary', 'deep') or (depth != 'ordinary' and summary):
            raise ValueError('INVALID_RESEARCH_PLAN')
        with self.connection(True) as c:
            old = c.execute('SELECT payload FROM agent_jobs WHERE case_id=? AND run_key=? ORDER BY rowid', (case_id, key)).fetchall()
            if old:
                jobs = [json.loads(r[0]) for r in old]
                if (jobs[0]['priority'] != priority or jobs[0]['refresh_public'] != refresh
                    or jobs[0].get('analysis_depth') != depth or jobs[0].get('include_local_summary', False) != summary):
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return jobs
            if c.execute("SELECT 1 FROM agent_jobs WHERE case_id=? AND state IN ('QUEUED','RUNNING')", (case_id,)).fetchone():
                raise ValueError('CASE_ALREADY_RUNNING')
            jobs = []; previous = None
            goal = (research_goal(case) if depth is None else
                    'investable_thesis' if depth == 'deep' else
                    research_goal(case) if research_goal(case) in ('data_quality', 'macro_reference') else 'descriptive_research')
            roles = (pipeline(case['instrument']['asset_class']) if goal=='investable_thesis'
                     else ['data_quality','momentum_trend','volatility_regime','macro_global']) if depth is None else planned_roles(case['instrument']['asset_class'], depth, summary)
            plan_hash = digest({'case_request_hash': case['request_hash'], 'depth': depth, 'summary': summary,
                                'goal': goal, 'roles': roles, 'priority': priority, 'refresh_public': refresh})
            for role in roles:
                kind = 'llm' if (ROLES[role]['llm_required'] and goal=='investable_thesis') or (depth == 'ordinary' and role == 'reporting_postmortem') else 'fetch' if role == 'data_quality' else 'quant'
                job = {'id': str(uuid.uuid4()), 'role_id': role, 'case_id': case_id, 'run_key': key, 'state': 'QUEUED',
                       'kind': kind, 'priority': priority, 'depends_on': previous, 'queued_at': utc(), 'started_at': None,
                       'finished_at': None, 'input_hash': None, 'output_hash': None, 'error': None, 'runtime': None,
                       'model': None, 'research_goal': goal, 'template_version': TEMPLATE_VERSION, 'attempts': 0, 'refresh_public': refresh, 'duration_ms': None,
                       'analysis_depth': depth, 'include_local_summary': summary, 'plan_hash': plan_hash,
                       'max_attempts': 2 if depth is None else 1,
                       'timeout_seconds': 300 if depth is None else 90 if kind == 'llm' else 60,
                       'llm_max_tokens': 1400 if depth is None else 384 if depth == 'deep' else 256,
                       'case_budget_seconds': None if depth is None else 270 if depth == 'deep' else 90}
                c.execute('INSERT INTO agent_jobs VALUES (?,?,?,?,?,?,?,?,?)', (job['id'], case_id, role, key, kind, 'QUEUED', priority, previous, canonical(job)))
                jobs.append(job); previous = job['id']
            self.audit(c, 'RUN_QUEUED', case_id=case_id, run_key=key, plan_hash=plan_hash, jobs=[j['id'] for j in jobs])
        return jobs

    def update(self, c, job):
        c.execute('UPDATE agent_jobs SET state=?,payload=? WHERE id=?', (job['state'], canonical(job), job['id']))

    def claim(self, kind):
        with self.connection(True) as c:
            rows = c.execute("SELECT j.payload FROM agent_jobs j LEFT JOIN agent_jobs p ON j.depends_on=p.id WHERE j.state='QUEUED' AND j.kind=? AND (p.id IS NULL OR p.state NOT IN ('RUNNING','QUEUED')) ORDER BY j.priority DESC,j.rowid", (kind,)).fetchall()
            for row in rows:
                job = json.loads(row[0])
                job.update(state='RUNNING', started_at=utc(), attempts=job['attempts'] + 1)
                self.update(c, job); self.audit(c, 'JOB_STARTED', job_id=job['id'])
                return job
        return None

    def finish(self, job, state, error=None, result=None, evidence=(), claims=()):
        with self.connection(True) as c:
            current = json.loads(c.execute('SELECT payload FROM agent_jobs WHERE id=?', (job['id'],)).fetchone()[0])
            if current['state'] == 'CANCELLED':
                return
            job.update(state=state, error=error, finished_at=utc())
            if result:
                job['output_hash'] = digest(result)
                c.execute('INSERT INTO agent_results VALUES (?,?,?,?)', (job['id'], job['case_id'], job['id'], canonical(result)))
                for claim in claims:
                    cid = digest({'job': job['id'], 'claim': claim})
                    c.execute('INSERT INTO research_claims VALUES (?,?,?,?)', (cid, job['case_id'], job['id'], canonical({**claim, 'result_id': job['id']})))
            for item in evidence:
                c.execute('INSERT OR IGNORE INTO evidence VALUES (?,?,?,?)', (item['id'], job['case_id'], job['id'], canonical(item)))
            self.update(c, job); self.audit(c, 'JOB_FINISHED', job_id=job['id'], state=state, error=error, output_hash=job['output_hash'])

    def cancel(self, job_id):
        with self.connection(True) as c:
            row = c.execute('SELECT payload FROM agent_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                raise KeyError('NOT_FOUND')
            job = json.loads(row[0])
            # Cancel downstream jobs in the same run; no partial debate masquerades as complete.
            for row in c.execute('SELECT payload FROM agent_jobs WHERE case_id=? AND run_key=?', (job['case_id'], job['run_key'])).fetchall():
                item = json.loads(row[0])
                if item['state'] not in TERMINAL:
                    item.update(state='CANCELLED', finished_at=utc(), error='USER_CANCELLED')
                    self.update(c, item)
            self.audit(c, 'RUN_CANCELLED', job_id=job_id)
        return self.get('agent_jobs', job_id)

    def recover(self):
        with self.connection(True) as c:
            for row in c.execute("SELECT payload FROM agent_jobs WHERE state='RUNNING'").fetchall():
                job = json.loads(row[0])
                job.update(state='QUEUED' if job['attempts'] < job.get('max_attempts', 2) else 'FAILED', error='RESTART_INTERRUPTED')
                self.update(c, job)
            self.audit(c, 'SCHEDULER_RECOVERY')

    def retry(self, job, error):
        with self.connection(True) as c:
            current = json.loads(c.execute('SELECT payload FROM agent_jobs WHERE id=?', (job['id'],)).fetchone()[0])
            if current['state'] == 'CANCELLED': return
            job.update(state='QUEUED', error=error)
            self.update(c, job); self.audit(c, 'RETRY_QUEUED', job_id=job['id'], attempt=job['attempts'], error=error)

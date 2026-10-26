"""One conservative due timer, completion notifications, no model or busy polling."""
import asyncio
import json
from datetime import datetime
from app.autonomy_contracts import AutonomySettings, TERMINAL
from app.autonomy_store import AutonomyStore
from app.research_router import ResearchRouter
from app.research_contracts import digest
from app.research_service import bounded_thread
from app.research_store import TERMINAL as JOB_TERMINAL


class AutonomyScheduler:
    def __init__(self, research, settings=None, clock=None):
        self.research = research
        self.settings = settings or AutonomySettings()
        self.store = AutonomyStore(research.store.engine, clock)
        self.router = ResearchRouter(research)
        self.wake = asyncio.Event()
        self.worker = None
        self.last_error = None

    def prepare_start(self):
        self.store.initialize(self.settings)
        # Before research workers start: pause/off also covers persisted queued jobs.
        for task in self.store.tasks(active=True):
            if not self.settings.autonomy_enabled or self.store.control()['paused']:
                self.cancel(task['id'])
            elif task['phase'] == 'FETCHING':
                self.store.update(task['id'], state='BLOCKED', result={'quality_state': 'ABSTAINED', 'reason': 'RESTART_INTERRUPTED'})
            elif datetime.fromisoformat(task['deadline_at']) <= self.store.clock():
                self.reconcile(task)

    def start(self):
        if self.worker and not self.worker.done():
            return
        self.research.completion_events.add(self.wake)
        self.worker = asyncio.create_task(self._loop(), name='hq-autonomy')

    async def stop(self):
        self.research.completion_events.discard(self.wake)
        if self.worker:
            self.worker.cancel()
            await asyncio.gather(self.worker, return_exceptions=True)
            self.worker = None

    def status(self):
        control = self.store.control()
        return dict(enabled=self.settings.autonomy_enabled, paused=control['paused'] if control else False,
                    running=bool(self.worker and not self.worker.done()),
                    interval_seconds=self.settings.autonomy_interval_seconds,
                    next_due_at=control['next_due_at'] if control else None,
                    last_error=self.last_error, llm_calls_max=0, tasks=self.store.tasks(),
                    note='Solo con backend encendido. Resultado histórico al completarse; vigencia actual en el dossier. P4 PARTIAL.')

    def jobs(self, task):
        # No global LIMIT 500: old tasks must reconcile even with a long history.
        with self.research.store.connection() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT payload FROM agent_jobs WHERE run_key=? ORDER BY rowid', (task['run_key'],))]

    def cancel(self, task_id, reason='USER_CANCELLED'):
        task = self.store.get(task_id)
        if task['state'] in TERMINAL:
            return task
        jobs = self.jobs(task)
        if jobs:
            self.research.cancel(jobs[0]['id'])
        result = self.store.update(task_id, state='CANCELLED', result={'quality_state': 'ABSTAINED', 'reason': reason})
        self.wake.set()
        return result

    def control(self, action, key):
        if action == 'resume' and not self.settings.autonomy_enabled:
            raise ValueError('AUTONOMY_DISABLED_BY_CONFIG')
        if action not in ('pause', 'resume'):
            raise ValueError('INVALID_CONTROL')
        changed = self.store.set_paused(action == 'pause', key)
        if changed and action == 'pause':
            for task in self.store.tasks(active=True):
                self.cancel(task['id'], 'AUTOMATION_PAUSED')
        self.wake.set()
        return self.status()

    def reconcile(self, task):
        jobs = self.jobs(task)
        if jobs and all(j['state'] in JOB_TERMINAL for j in jobs):
            if any(j.get('finished_at') and datetime.fromisoformat(j['finished_at']) > datetime.fromisoformat(task['deadline_at']) for j in jobs):
                return self.store.update(task['id'], state='BLOCKED', result={'quality_state': 'ABSTAINED', 'reason': 'DEADLINE_EXCEEDED'})
            if any(j['state'] != 'SUCCEEDED' for j in jobs):
                return self.store.update(task['id'], state='FAILED', result={'quality_state': 'ABSTAINED', 'reason': 'JOB_INCOMPLETE', 'job_states': {j['role_id']: j['state'] for j in jobs}})
            dossier = self.research.dossier(task['case_id'] or jobs[0]['case_id'], task['run_key'])
            quality = dossier['quality']
            evidence = dossier['evidence']
            result = dict(quality_state=quality['state'], reason=quality['reason'], evidence_count=len(evidence),
                          evidence_ids=[e['id'] for e in evidence],
                          output_hashes={j['id']: j['output_hash'] for j in jobs},
                          dossier_hash=digest(dossier), source_receipt=(task['result'] or {}).get('source_receipt'),
                          elapsed_seconds=round((self.store.clock() - datetime.fromisoformat(task['created_at'])).total_seconds(), 3))
            return self.store.update(task['id'], case_id=dossier['id'], state='SUCCEEDED' if quality['state'] == 'VERIFIED_DATA' else 'ABSTAINED', result=result)
        if datetime.fromisoformat(task['deadline_at']) <= self.store.clock():
            if jobs:
                self.research.cancel(jobs[0]['id'])
            return self.store.update(task['id'], state='BLOCKED', result={'quality_state': 'ABSTAINED', 'reason': 'DEADLINE_EXCEEDED'})
        return task

    async def advance(self, task):
        task = self.reconcile(task)
        if task['state'] in TERMINAL or task['phase'] == 'JOBS':
            return
        if task['phase'] == 'NEW':
            task = self.store.update(task['id'], state='RUNNING', phase='FETCHING', started_at=self.store.clock().isoformat())
            remaining = max(0.001, (datetime.fromisoformat(task['deadline_at']) - self.store.clock()).total_seconds())
            try:
                async with asyncio.timeout(remaining):
                    subject, result = await bounded_thread(self.router.prepare, task)
            except TimeoutError:
                self.store.update(task['id'], state='BLOCKED', result={'quality_state': 'ABSTAINED', 'reason': 'DEADLINE_EXCEEDED'})
                return
            if self.store.get(task['id'])['state'] in TERMINAL:
                return
            if not subject:
                self.store.update(task['id'], state='ABSTAINED', result=result)
                return
            task = self.store.update(task['id'], phase='PREPARED', subject=subject, result=result)
        if task['phase'] == 'PREPARED':
            # Both calls are independently idempotent using the durable task key.
            # A crash between them resumes the same case and the same job identities.
            case_id, _jobs = self.router.enqueue(task)
            self.store.update(task['id'], phase='JOBS', case_id=case_id)

    async def _loop(self):
        while True:
            self.wake.clear()
            try:
                active = self.store.tasks(active=True)
                for task in active:
                    await self.advance(task)
                if not self.store.tasks(active=True):
                    task = self.store.reserve_due(self.settings)
                    if task:
                        await self.advance(task)
                self.last_error = None
            except asyncio.CancelledError:
                raise
            except Exception:
                # A routing error must not schedule unlimited retries or disclose payloads.
                self.last_error = 'AUTONOMY_FAILED'
                for task in self.store.tasks(active=True):
                    for job in self.jobs(task)[:1]:
                        self.research.cancel(job['id'])
                    self.store.update(task['id'], state='FAILED', result={'quality_state': 'ABSTAINED', 'reason': 'AUTONOMY_FAILED'})
            control = self.store.control()
            active = self.store.tasks(active=True)
            dates = [datetime.fromisoformat(t['deadline_at']) for t in active]
            if not active and self.settings.autonomy_enabled and not control['paused']:
                dates.append(datetime.fromisoformat(control['next_due_at']))
            delay = max(0.05, min((d - self.store.clock()).total_seconds() for d in dates)) if dates else 86400
            try:
                await asyncio.wait_for(self.wake.wait(), timeout=delay)
            except TimeoutError:
                pass

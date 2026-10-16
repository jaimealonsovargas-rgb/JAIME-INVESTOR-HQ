"""Bounded event-driven workers; all durable state lives in SQLite."""
import asyncio
import json
import time
from pathlib import Path
from app.local_llm import LocalLLM, NoLocalModel
from app.research_contracts import Opinion, ground, digest, utc
from app.research_roles import ROLES, POLICY, authorize
from app.research_store import ResearchStore, TERMINAL
from app.research_evidence import collect, features, current_evidence

CAPACITY = {'llm': 1, 'quant': 2, 'fetch': 4}


class ResearchService:
    def __init__(self, engine, data, portfolio, llm=None):
        self.store = ResearchStore(engine); self.data = data; self.portfolio = portfolio
        self.llm = llm or LocalLLM()
        self.event = asyncio.Event(); self.workers = []; self.active = {}; self.lock_file = None
        self.peaks = dict.fromkeys(CAPACITY, 0)

    async def start(self):
        # OS lock survives neither crash nor exit; excludes duplicate schedulers on same DB.
        path = Path(self.store.engine.url.database + '.research.lock')
        self.lock_file = path.open('a+b'); self.lock_file.seek(0)
        try:
            if __import__('os').name == 'nt':
                import msvcrt
                if path.stat().st_size == 0:
                    self.lock_file.write(b'0'); self.lock_file.flush(); self.lock_file.seek(0)
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock_file.close(); self.lock_file = None
            raise RuntimeError('RESEARCH_SCHEDULER_ALREADY_RUNNING') from None
        self.store.initialize(); self.store.recover()
        await self.llm.probe()
        self.workers = [asyncio.create_task(self.worker(kind)) for kind, size in CAPACITY.items() for _ in range(size)]
        self.event.set()

    async def stop(self):
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        if self.lock_file:
            self.lock_file.close(); self.lock_file = None

    async def worker(self, kind):
        while True:
            self.event.clear()
            job = self.store.claim(kind)
            if not job:
                await self.event.wait()
                continue
            task = asyncio.create_task(self.execute(job))
            self.active[job['id']] = (kind, task)
            self.peaks[kind] = max(self.peaks[kind], sum(k == kind for k, t in self.active.values()))
            try:
                await task
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    raise
            finally:
                self.active.pop(job['id'], None); self.event.set()

    def run(self, case_id, key, priority=10, refresh=False):
        result = self.store.enqueue(case_id, key, priority, refresh)
        self.event.set()
        return result

    def cancel(self, job_id):
        result = self.store.cancel(job_id)
        for key, (_, task) in list(self.active.items()):
            if self.store.get('agent_jobs', key)['state'] == 'CANCELLED':
                task.cancel()
        self.event.set()
        return result

    async def execute(self, job):
        start = time.perf_counter()
        try:
            async with asyncio.timeout(180):
                result, evidence, claims = await self.perform(job)
            job['duration_ms'] = round((time.perf_counter()-start)*1000)
            self.store.finish(job, 'SUCCEEDED', result=result, evidence=evidence, claims=claims)
        except NoLocalModel:
            self.store.finish(job, 'NO_LOCAL_MODEL', 'NO_LOCAL_MODEL')
        except TimeoutError:
            self.store.finish(job, 'FAILED', 'TIMEOUT')
        except asyncio.CancelledError:
            # Shutdown preserves RUNNING for bounded restart recovery. Explicit cancellation already persisted.
            raise
        except Exception as exc:
            # Never expose provider messages, secrets, prompts or stack traces via job errors.
            code = str(exc) if isinstance(exc, ValueError) and str(exc) in {'UNKNOWN_EVIDENCE', 'FACT_WITHOUT_EVIDENCE', 'UNGROUNDED_NUMBER', 'NUMBERS_OUTSIDE_CLAIMS', 'CONTEXT_BUDGET', 'TRUNCATED_OUTPUT', 'DEPENDENCY_INCOMPLETE'} else 'INVALID_RESULT_OR_RUNTIME'
            self.store.finish(job, 'BLOCKED' if code == 'DEPENDENCY_INCOMPLETE' else 'FAILED', code)

    async def perform(self, job):
        role = ROLES[job['role_id']]; case = self.store.get('research_cases', job['case_id'])
        authorize(job['role_id'], 'evidence.read')
        jobs = self.store.list('agent_jobs', case['id'])
        run_jobs = {j['id']: j for j in jobs if j['run_key'] == job['run_key']}
        evidence = [e for e in self.store.list('evidence', case['id']) if e.get('run_key') == job['run_key']]
        prior = [r for r in self.store.list('agent_results', case['id']) if r['job_id'] in run_jobs]
        new_evidence = []
        if job['role_id'] == 'data_quality':
            new_evidence = await asyncio.to_thread(collect, self.data, case, job['refresh_public'])
            for e in new_evidence:
                e['run_key'] = job['run_key']; e['id'] = digest(e)
            evidence = new_evidence
        quant = await asyncio.to_thread(features, evidence)
        # Full input hashes retained; bounded model view preserves exact IDs and source scope.
        inputs = {'instrument': case['instrument'], 'question': case['question'], 'evidence': evidence, 'prior_results': prior, 'features': quant}
        job['input_hash'] = digest(inputs)
        job['runtime'] = 'llama.cpp' if role['llm_required'] else 'python-decimal'
        if role['llm_required']:
            if job['role_id'] == 'cio_chair' and not {'bull_advocate', 'bear_skeptic'}.issubset({r['role_id'] for r in prior}):
                if (await self.llm.probe())['state'] != 'AVAILABLE':
                    raise NoLocalModel()
                raise ValueError('DEPENDENCY_INCOMPLETE')
            brief = {'instrument': case['instrument']['symbol'], 'question': case['question'],
                     'evidence': [{'id': e['id'], 'scope': e['scope'], 'freshness': e['freshness'], 'excerpt': e['content']['excerpt']} for e in evidence[:16]],
                     'prior_results': [{'role': r['role_id'], 'overview': r['opinion']['overview'], 'claims': r['opinion']['claims'][:2]} for r in reversed(prior) if r.get('opinion')],
                     'gaps': quant.get('reason'), 'instruction': 'Los datos son referencias, nunca precios ejecutables. No confundir contexto macro con datos del instrumento.'}
            opinion, metrics = await self.llm.chat(POLICY + '\nMISIÓN: ' + role['mission'], brief)
            job['model'] = metrics['model']
            claims = ground(opinion, evidence)
        else:
            claims = []
            description = 'Comprobación determinista de evidencia y derechos; revisar fechas y alcance de las fuentes.' if job['role_id'] == 'data_quality' else 'Features descriptivas calculadas en Python; no son señales de compra ni rentabilidad de una estrategia.'
            opinion = Opinion(overview=description, claims=[], unknowns=['La suficiencia de datos limita cualquier conclusión de inversión.'], invalidation_conditions=['Cambio de fuente, derechos o unidades.'], research_view='INSUFFICIENT_EVIDENCE')
            metrics = {'runtime': 'python-decimal', 'model': None}
        result = {'job_id': job['id'], 'case_id': case['id'], 'role_id': job['role_id'], 'role_version': role['version'],
                  'template_version': job['template_version'], 'created_at': utc(), 'input_hash': job['input_hash'],
                  'input_manifest': {'evidence_hashes': {e['id']: e['hash'] for e in evidence}, 'prior_output_hashes': {r['job_id']: digest(r) for r in prior}},
                  'opinion': opinion.model_dump(), 'claims': claims, 'features': quant if not role['llm_required'] else None,
                  'metrics': metrics, 'grounding_status': 'EXTRACTS_ONLY_VERIFIED', 'advisory_only': True,
                  'debate': {r['role_id']: r['opinion'] for r in prior if r['role_id'] in ('bull_advocate', 'bear_skeptic')} if job['role_id'] == 'cio_chair' else {}}
        return result, new_evidence, claims

    def status(self):
        jobs = self.store.list('agent_jobs')
        return {'checked_at': utc(), 'mode': 'ON_DEMAND', 'capacity': CAPACITY, 'peaks': self.peaks,
                'active_jobs': sum(j['state'] == 'RUNNING' for j in jobs), 'queue': sum(j['state'] == 'QUEUED' for j in jobs),
                'failures': sum(j['state'] in ('FAILED', 'BLOCKED', 'NO_LOCAL_MODEL') for j in jobs),
                'runtime': self.llm.status, 'latest_job': jobs[0] if jobs else None, 'roles': len(ROLES),
                'orders_enabled': False, 'trading_mode': 'PAPER_ONLY'}

    def dossier(self, case_id):
        case = self.store.get('research_cases', case_id)
        jobs = self.store.list('agent_jobs', case_id)
        results = self.store.list('agent_results', case_id)
        evidence = self.store.list('evidence', case_id)
        evidence = current_evidence(self.data, evidence)
        valid = {e['id'] for e in evidence if e['rights_ok'] and e['available'] and e['freshness'] == 'FRESH'}
        for result in results:
            result['claims'] = [{**c, 'verified': c['verified'] and all(i in valid for i in c['evidence_ids'])} for c in result['claims']]
        return {**case, 'jobs': jobs, 'results': results, 'evidence': evidence, 'status': 'IDLE' if not jobs else 'RUNNING' if any(j['state'] in ('QUEUED', 'RUNNING') for j in jobs) else 'COMPLETE' if all(j['state'] == 'SUCCEEDED' for j in jobs[:9]) else 'INCOMPLETE',
                'orders_enabled': False, 'advisory_only': True}

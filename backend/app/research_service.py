"""Bounded event-driven workers; all durable state lives in SQLite."""
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from app.local_llm import LocalLLM, NoLocalModel
from app.research_contracts import Opinion, ground, digest, utc, withhold_unsupported_narrative
from app.research_roles import ROLES, POLICY, authorize, TEMPLATE_VERSION
from app.research_store import ResearchStore, TERMINAL
from app.research_evidence import collect, features, current_evidence

CAPACITY = {'llm': 1, 'quant': 2, 'fetch': 4}


async def bounded_thread(fn, *args):
    # Python cannot cancel a running HTTP/CPU thread. Keep its lane occupied until
    # it finishes, even when the job is cancelled, so concurrency never overshoots.
    task = asyncio.create_task(asyncio.to_thread(fn, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await task
        raise


class ResearchService:
    def __init__(self, engine, data, portfolio, llm=None):
        self.store = ResearchStore(engine); self.data = data; self.portfolio = portfolio
        self.llm = llm or LocalLLM()
        self.event = asyncio.Event(); self.workers = []; self.active = {}; self.lock_file = None
        self.peaks = dict.fromkeys(CAPACITY, 0)
        self.timeout_seconds = 180
        self.quant_slots = asyncio.Semaphore(CAPACITY['quant'])

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
            async with asyncio.timeout(self.timeout_seconds):
                result, evidence, claims = await self.perform(job)
            job['duration_ms'] = round((time.perf_counter()-start)*1000)
            self.store.finish(job, 'SUCCEEDED', result=result, evidence=evidence, claims=claims)
        except NoLocalModel:
            self.store.finish(job, 'NO_LOCAL_MODEL', 'NO_LOCAL_MODEL')
        except TimeoutError:
            if job['attempts'] < 2: self.store.retry(job, 'TIMEOUT')
            else: self.store.finish(job, 'FAILED', 'TIMEOUT')
        except asyncio.CancelledError:
            # Shutdown preserves RUNNING for bounded restart recovery. Explicit cancellation already persisted.
            raise
        except Exception as exc:
            # Never expose provider messages, secrets, prompts or stack traces via job errors.
            code = str(exc) if isinstance(exc, ValueError) and str(exc) in {'UNKNOWN_EVIDENCE', 'FACT_WITHOUT_EVIDENCE', 'UNGROUNDED_NUMBER', 'NUMBERS_OUTSIDE_CLAIMS', 'CONTEXT_BUDGET', 'TRUNCATED_OUTPUT', 'DEPENDENCY_INCOMPLETE'} else 'INVALID_RESULT_OR_RUNTIME'
            if job['kind'] == 'llm' and job['attempts'] < 2 and code != 'DEPENDENCY_INCOMPLETE': self.store.retry(job, code)
            else: self.store.finish(job, 'BLOCKED' if code == 'DEPENDENCY_INCOMPLETE' else 'FAILED', code)

    async def perform(self, job):
        job['template_version'] = TEMPLATE_VERSION
        role = ROLES[job['role_id']]; case = self.store.get('research_cases', job['case_id'])
        authorize(job['role_id'], 'evidence.read')
        jobs = self.store.list('agent_jobs', case['id'])
        run_jobs = {j['id']: j for j in jobs if j['run_key'] == job['run_key']}
        evidence = current_evidence(self.data, [e for e in self.store.list('evidence', case['id']) if e.get('run_key') == job['run_key']])
        prior = [r for r in self.store.list('agent_results', case['id']) if r['job_id'] in run_jobs]
        new_evidence = []
        withheld = []
        if job['role_id'] == 'data_quality':
            new_evidence = await bounded_thread(collect, self.data, case, job['refresh_public'])
            if self.portfolio is not None:
                authorize(job['role_id'], 'p3.read')
                summary = self.portfolio.summary()
                content = {key: summary[key] for key in ('ledger_hash','nav_eur','cash_eur','positions_count','valuation_status')}
                content.update(excerpt=f"MASTER virtual: NAV {summary['nav_eur']} EUR; caja {summary['cash_eur']} EUR; posiciones {summary['positions_count']}.", stale_after_seconds=3600)
                new_evidence.append({'case_id': case['id'], 'provider': 'HQ_MASTER', 'source': 'Ledger MASTER P3', 'url': 'local:/api/portfolio/master/summary', 'retrieved_at': utc(), 'observed_at': summary['as_of'], 'rights': {'license': 'Contabilidad virtual propia'}, 'rights_ok': True, 'freshness': 'FRESH' if summary['valuation_status']=='FRESH' else 'STALE', 'trust_class': 'LOCAL_VERIFIED_LEDGER', 'content': content, 'hash': digest(content), 'provenance': summary['ledger_hash'], 'scope': 'PORTFOLIO_CONTEXT', 'available': True})
            for e in new_evidence:
                e['run_key'] = job['run_key']; e['id'] = digest(e)
            evidence = new_evidence
        async with self.quant_slots:
            quant = await bounded_thread(features, evidence)
        if job['role_id'] in ('momentum_trend', 'volatility_regime') and quant['items']:
            for metric in quant['items']:
                content = {'excerpt': f"{metric['name']}: {metric['value']}", 'value': metric['value'], 'method': quant['method_version'], 'inputs': metric['evidence_ids'], 'stale_after_seconds': 3600}
                item = {'case_id': case['id'], 'run_key': job['run_key'], 'provider': 'HQ_DERIVED', 'source': quant['method_version'], 'url': 'local:research_evidence.features', 'retrieved_at': utc(), 'observed_at': utc(), 'rights': {'license': 'Cálculo propio sobre datos autorizados'}, 'rights_ok': True, 'freshness': 'FRESH' if quant['state'] == 'AVAILABLE' else 'STALE', 'trust_class': 'DETERMINISTIC_DERIVATION', 'content': content, 'hash': digest(content), 'provenance': quant['input_hash'], 'scope': 'DERIVED_FEATURE', 'available': True}
                item['id'] = digest(item); new_evidence.append(item)
            evidence = evidence + new_evidence
        # Full input hashes retained; bounded model view preserves exact IDs and source scope.
        inputs = {'instrument': case['instrument'], 'question': case['question'], 'evidence': evidence, 'prior_results': prior, 'features': quant}
        job['input_hash'] = digest(inputs)
        job['runtime'] = 'llama.cpp' if role['llm_required'] else 'python-decimal'
        if role['llm_required']:
            if job['role_id'] == 'cio_chair' and not {'bull_advocate', 'bear_skeptic'}.issubset({r['role_id'] for r in prior}):
                if (await self.llm.probe())['state'] != 'AVAILABLE':
                    raise NoLocalModel()
                raise ValueError('DEPENDENCY_INCOMPLETE')
            direct = sorted((e for e in evidence if e['scope'] == 'INSTRUMENT'), key=lambda e: e['observed_at'])
            selection = {e['id']: e for e in (direct[:1] + direct[-2:] + [e for e in evidence if e['scope'] == 'DERIVED_FEATURE'][:2] + [e for e in evidence if e['scope'] in ('MACRO_CONTEXT','GENERAL_NEWS')][:2] + [e for e in evidence if e['scope']=='PORTFOLIO_CONTEXT'][:1])}
            brief = {'instrument': case['instrument']['symbol'], 'question': case['question'],
                     'evidence': [{'id': e['id'], 'scope': e['scope'], 'freshness': e['freshness'], 'excerpt': e['content']['excerpt']} for e in selection.values()],
                     'prior_results': [{'role': r['role_id'], 'overview': r['opinion']['overview'][:240], 'claims': r['opinion']['claims'][:1] if r['role_id'] in ('bull_advocate', 'bear_skeptic') else []} for r in reversed(prior) if r.get('opinion')],
                     'gaps': quant.get('reason'), 'instruction': 'Los datos son referencias, nunca precios ejecutables. No confundir contexto macro con datos del instrumento.'}
            prior_error = (' Corrige el contrato del intento anterior: ' + job['error']) if job.get('error') else ''
            job['prompt_input_hash'] = digest(brief)
            job['selected_evidence_ids'] = list(selection)
            opinion, metrics = await self.llm.chat(POLICY + '\nMISIÓN: ' + role['mission'] + prior_error, brief, max_tokens=900)
            job['model'] = metrics['model']
            job['candidate_output_hash'] = digest(opinion.model_dump())
            opinion, withheld = withhold_unsupported_narrative(opinion, evidence)
            claims = ground(opinion, evidence)
        else:
            claims = []
            description = 'Comprobación determinista de evidencia y derechos; revisar fechas y alcance de las fuentes.' if job['role_id'] == 'data_quality' else 'Features descriptivas calculadas en Python; no son señales de compra ni rentabilidad de una estrategia.'
            opinion = Opinion(overview=description, claims=[], unknowns=['La suficiencia de datos limita cualquier conclusión de inversión.'], invalidation_conditions=['Cambio de fuente, derechos o unidades.'], research_view='INSUFFICIENT_EVIDENCE')
            metrics = {'runtime': 'python-decimal', 'model': None}
        result = {'job_id': job['id'], 'case_id': case['id'], 'role_id': job['role_id'], 'role_version': role['version'],
                  'template_version': job['template_version'], 'created_at': utc(), 'input_hash': job['input_hash'],
                  'input_manifest': {'evidence_hashes': {e['id']: e['hash'] for e in evidence}, 'evidence_order': [e['id'] for e in evidence], 'evaluated_flags': {e['id']: {k:e[k] for k in ('freshness','rights_ok','available')} for e in evidence}, 'prior_output_hashes': {r['job_id']: digest(r) for r in prior}, 'prior_order': [r['job_id'] for r in prior], 'case_request_hash': case['request_hash'], 'features_hash': digest(quant), 'selected_evidence_ids': job.get('selected_evidence_ids',[]), 'prompt_input_hash': job.get('prompt_input_hash')},
                  'opinion': opinion.model_dump(), 'claims': claims, 'features': quant if not role['llm_required'] else None,
                  'metrics': metrics, 'grounding_status': 'EXTRACTS_ONLY_VERIFIED', 'advisory_only': True,
                  'validation': {'raw_output_hash': job.get('candidate_output_hash'), 'withheld_passages': withheld},
                  'narrative_evidence_ids': sorted({i for c in claims if c['verified'] for i in c['evidence_ids']}),
                  'debate': {r['role_id']: r['opinion'] for r in prior if r['role_id'] in ('bull_advocate', 'bear_skeptic')} if job['role_id'] == 'cio_chair' else {}}
        return result, new_evidence, claims

    def status(self):
        jobs = self.store.list('agent_jobs')
        with self.store.connection() as conn:
            counts = dict(conn.execute('SELECT state,COUNT(*) FROM agent_jobs GROUP BY state').fetchall())
        runtime = dict(self.llm.status)
        if runtime.get('last_checked_at') and (datetime.now(timezone.utc)-datetime.fromisoformat(runtime['last_checked_at'])).total_seconds() > 60:
            runtime['state'] = 'STALE'
        latest = next((j for j in jobs if j['state'] == 'SUCCEEDED'), None)
        return {'checked_at': utc(), 'mode': 'ON_DEMAND', 'capacity': CAPACITY, 'peaks': self.peaks,
                'active_jobs': counts.get('RUNNING', 0), 'queue': counts.get('QUEUED', 0),
                'failures': sum(counts.get(s, 0) for s in ('FAILED', 'BLOCKED', 'NO_LOCAL_MODEL')),
                'runtime': runtime, 'latest_job': jobs[0] if jobs else None, 'last_completed': latest, 'roles': len(ROLES),
                'department_states': {team: 'ANALYZING' if any(j['state'] == 'RUNNING' for j in jobs if ROLES[j['role_id']]['team'] == team) else 'WAITING_DATA' if any(j['state'] == 'QUEUED' for j in jobs if ROLES[j['role_id']]['team'] == team) else 'DONE' if next((j['state'] for j in jobs if ROLES[j['role_id']]['team'] == team), 'IDLE') == 'SUCCEEDED' else 'ERROR' if any(j['state'] in ('FAILED','BLOCKED','NO_LOCAL_MODEL') for j in jobs if ROLES[j['role_id']]['team'] == team) else 'IDLE' for team in {r['team'] for r in ROLES.values()}},
                'orders_enabled': False, 'trading_mode': 'PAPER_ONLY'}

    def dossier(self, case_id, run_key=None):
        case = self.store.get('research_cases', case_id)
        jobs = self.store.list('agent_jobs', case_id)
        runs = list(dict.fromkeys(j['run_key'] for j in jobs))
        active_run = run_key or (runs[0] if runs else None)
        if run_key and run_key not in runs: raise KeyError('NOT_FOUND')
        selected_jobs = [j for j in jobs if j['run_key'] == active_run]
        selected_ids = {j['id'] for j in selected_jobs}
        results = self.store.list('agent_results', case_id)
        results = [r for r in results if r['job_id'] in selected_ids]
        evidence = self.store.list('evidence', case_id)
        evidence = [e for e in evidence if e.get('run_key') == active_run]
        evidence = current_evidence(self.data, evidence)
        valid = {e['id'] for e in evidence if e['rights_ok'] and e['available'] and e['freshness'] == 'FRESH'}
        for result in results:
            result['claims'] = [{**c, 'verified': c['verified'] and all(i in valid for i in c['evidence_ids'])} for c in result['claims']]
            restricted = {e['id'] for e in evidence if not e['rights_ok']}
            referenced = set(result['input_manifest']['evidence_hashes'])
            if restricted & referenced:
                result.update(opinion=Opinion(overview='RIGHTS_RESTRICTED: evidencia retirada.', claims=[], unknowns=['No se muestran derivados de fuentes restringidas.'], invalidation_conditions=[], research_view='INSUFFICIENT_EVIDENCE').model_dump(), claims=[], features=None, debate={})
        return {**case, 'thesis_version': len(runs)-runs.index(active_run) if active_run else 0, 'runs': runs, 'active_run_key': active_run, 'jobs': selected_jobs, 'results': results, 'evidence': evidence, 'status': 'IDLE' if not selected_jobs else 'RUNNING' if any(j['state'] in ('QUEUED', 'RUNNING') for j in selected_jobs) else 'COMPLETE' if all(j['state'] == 'SUCCEEDED' for j in selected_jobs) else 'INCOMPLETE',
                'orders_enabled': False, 'advisory_only': True}

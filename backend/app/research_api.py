import re
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import InstrumentRegistry
from app.research_contracts import CreateCase, RunCase, sanitize
from app.research_roles import ROLES


def router(service):
    api = APIRouter()

    def mutation(request):
        if request.headers.get('x-hq-research') != '1' or request.headers.get('origin') not in (None, 'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:5174', 'http://localhost:5174'):
            raise HTTPException(403, 'RESEARCH_ORIGIN_DENIED')
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,128}', key):
            raise HTTPException(400, 'IDEMPOTENCY_KEY_REQUIRED')
        return key

    def call(fn, *args):
        try:
            return fn(*args)
        except KeyError:
            raise HTTPException(404, 'NOT_FOUND') from None
        except ValueError as e:
            raise HTTPException(409, str(e)) from None

    @api.get('/api/agents')
    def agents():
        jobs = service.store.list('agent_jobs')
        return [{**role, 'state': next((j['state'] for j in jobs if j['role_id'] == role['role_id']), 'IDLE')} for role in ROLES.values()]

    @api.get('/api/agents/status')
    def status():
        return service.status()

    @api.get('/api/research/cases')
    def cases():
        return service.store.list('research_cases')

    @api.post('/api/research/cases')
    async def create(body: CreateCase, request: Request):
        key = mutation(request)
        with Session(service.store.engine) as session:
            instrument = next((x for x in InstrumentRegistry(session).list() if str(x.id) == body.instrument_id), None)
        if not instrument:
            raise HTTPException(422, 'UNKNOWN_INSTRUMENT')
        return call(service.store.create_case, instrument.model_dump(mode='json'), sanitize(body.question), key)

    @api.get('/api/research/cases/{case_id}')
    def detail(case_id: str):
        return call(service.dossier, case_id)

    @api.post('/api/research/cases/{case_id}/run')
    async def run(case_id: str, body: RunCase, request: Request):
        return call(service.run, case_id, mutation(request), body.priority, body.refresh_public)

    @api.get('/api/agent-jobs/{job_id}')
    def job(job_id: str):
        return call(service.store.get, 'agent_jobs', job_id)

    @api.post('/api/agent-jobs/{job_id}/cancel')
    async def cancel(job_id: str, request: Request):
        mutation(request)
        return call(service.cancel, job_id)

    @api.get('/api/research/cases/{case_id}/evidence')
    def evidence(case_id: str):
        return call(service.dossier, case_id)['evidence']

    @api.get('/api/research/cases/{case_id}/results')
    def results(case_id: str):
        return call(service.dossier, case_id)['results']

    return api

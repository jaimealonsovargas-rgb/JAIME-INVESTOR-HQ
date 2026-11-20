"""Durable shadow cycles, advanced by the existing single SEC worker, not a new timer."""
from datetime import datetime, timedelta
from sqlalchemy import select, insert, update, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import Base
from app.data_identity import fingerprint
from app.universe_store import utc_text
from app.sec_store import JOBS, TASKS, TERMINAL as SEC_TERMINAL
from app.company_service import CompanyService
from app.cycle_contracts import AGENDA, PILOT_CIKS, TERMINAL, window, CycleSettings
from app.storage_budget import StorageBlocked, admitted
from app.risk_review import RiskReview
from app.risk_engine import POLICY, POLICY_HASH

AGENDAS = Base.metadata.tables['cycle_agendas']
CYCLES = Base.metadata.tables['automation_cycles']


class CycleService:
    def __init__(self, sec, settings=None, risk=None):
        self.sec, self.engine = sec, sec.data.engine
        self.data = sec.data
        self.clock = sec.data.clock
        self.settings = settings or CycleSettings()
        self.risk = risk or RiskReview(self.data.storage)

    def owner(self):
        with self.engine.connect() as c:
            return c.scalar(select(AGENDAS.c.owner).where(AGENDAS.c.id==AGENDA)) or 'disabled'

    def set_owner(self, owner):
        if owner not in ('disabled', 'n8n'):
            raise ValueError('SCHEDULE_OWNER_DENIED')
        if owner=='n8n' and not self.settings.token():
            raise ValueError('CYCLE_AUTH_NOT_CONFIGURED')
        with self.engine.begin() as c:
            c.execute(sqlite_insert(AGENDAS).values(id=AGENDA,owner=owner,updated_at=utc_text(self.clock()))
                .on_conflict_do_update(index_elements=['id'],set_=dict(owner=owner,updated_at=utc_text(self.clock()))))
        return self.status()

    @admitted
    def submit(self, request):
        payload = request.model_dump(mode='json')
        # Correlation identifies a delivery, not the business intent. A workflow retry may have a new execution ID.
        digest = fingerprint({k:v for k,v in payload.items() if k!='correlation_id'})
        ident = fingerprint([AGENDA,payload['window_start']])
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            prior = c.execute(select(CYCLES).where(CYCLES.c.event_id==request.event_id)).mappings().first()
            if prior:
                if prior['request_hash']!=digest:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return self.public(prior), True
            now = self.clock()
            if request.window_start != window(now)[0]:
                raise ValueError('STALE_OR_FUTURE_WINDOW')
            if c.scalar(select(AGENDAS.c.owner).where(AGENDAS.c.id==AGENDA))!='n8n':
                raise ValueError('SCHEDULE_DISABLED')
            if c.scalar(select(func.count()).select_from(CYCLES).where(CYCLES.c.state.not_in(TERMINAL))):
                raise ValueError('CYCLE_ALREADY_ACTIVE')
            if c.scalar(select(func.count()).select_from(CYCLES))>=10000:
                raise ValueError('CYCLE_STORAGE_LIMIT')
            stamp = utc_text(now)
            row = dict(id=ident,event_id=request.event_id,agenda=AGENDA,window_start=utc_text(request.window_start),
                request_hash=digest,request=payload,state='QUEUED',created_at=stamp,updated_at=stamp,
                deadline_at=utc_text(now+timedelta(seconds=request.budget.timeout_seconds)),next_at=stamp,
                review_cutoff=None,result=dict(models=[],reason='QUEUED',mode='shadow',llm_calls=0,orders=0))
            # Check and persist the B4 decision once under the same claim as the n8n window.
            # A crash before commit rolls both back; retries after commit return this exact receipt.
            row['result']['risk'] = self.risk.run(ident, now, request.window_end)
            c.execute(insert(CYCLES).values(**row))
        return self.public(row), False

    @staticmethod
    def public(row):
        return {k:row[k] for k in ('id','event_id','agenda','window_start','state','created_at','updated_at',
                                   'deadline_at','result')}

    def get(self, ident):
        with self.engine.connect() as c:
            row = c.execute(select(CYCLES).where(CYCLES.c.id==ident)).mappings().first()
        if not row:
            raise KeyError(ident)
        return self.public(row)

    def status(self):
        with self.engine.connect() as c:
            latest = list(c.execute(select(CYCLES).order_by(CYCLES.c.created_at.desc(),CYCLES.c.id).limit(10)).mappings())
        return dict(agenda=AGENDA,owner=self.owner(),mode='shadow',auth_configured=bool(self.settings.token()),
            risk_policy=dict(version=POLICY.version, policy_hash=POLICY_HASH),
            worker_running=bool(self.sec._thread and self.sec._thread.is_alive()),worker_error=self.sec.worker_error,
            interval_hours=6,next_window_at=utc_text(window(self.clock())[1]),issuers=list(PILOT_CIKS),
            cycles=[self.public(r) for r in latest],
            note='Revisión de riesgo PAPER, captación SEC y revisión contable. P4 PARTIAL.')

    def cancel(self, ident):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = c.execute(select(CYCLES).where(CYCLES.c.id==ident)).mappings().first()
            if row is None:
                raise KeyError(ident)
            if row['state'] not in TERMINAL:
                self._cancel_import(c,ident)
                c.execute(update(CYCLES).where(CYCLES.c.id==ident).values(state='CANCEL_REQUESTED',
                    next_at=utc_text(self.clock()),updated_at=utc_text(self.clock())))
        return self.get(ident)

    def _finish(self,c,row,state,reason):
        result = {**row['result'],'reason':reason}
        c.execute(update(CYCLES).where(CYCLES.c.id==row['id']).values(state=state,result=result,updated_at=utc_text(self.clock())))

    def _cancel_import(self,c,ident):
        # Only this cycle's job. Fencing invalidates any in-flight SEC task at its commit boundary.
        c.execute(update(TASKS).where(TASKS.c.job_id==ident,TASKS.c.state.not_in(SEC_TERMINAL))
            .values(state='CANCELLED',token=None,lease_until=None))
        c.execute(update(JOBS).where(JOBS.c.id==ident,JOBS.c.state.in_(('QUEUED','RUNNING','PAUSED')))
            .values(state='CANCELLED',updated_at=utc_text(self.clock())))

    def step(self):
        now, review = self.clock(), None
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = c.execute(select(CYCLES).where(CYCLES.c.state.not_in(TERMINAL),CYCLES.c.next_at<=utc_text(now))
                .order_by(CYCLES.c.created_at).limit(1)).mappings().first()
            if row is None:
                return False
            if row['state']=='CANCEL_REQUESTED' or datetime.fromisoformat(row['deadline_at'])<=now:
                cancelled = row['state']=='CANCEL_REQUESTED'
                self._cancel_import(c,row['id'])
                self._finish(c,row,'CANCELLED' if cancelled else 'TIMED_OUT','USER_CANCELLED' if cancelled else 'DEADLINE_EXCEEDED')
                return True
            access = self.sec.access()
            if access!='READY':
                self._cancel_import(c,row['id'])
                self._finish(c,row,'BLOCKED',access)
                return True
            if row['state']=='QUEUED':
                try:
                    self.sec.store.enqueue(row['id'],list(PILOT_CIKS),now,connection=c)
                except ValueError as error:
                    if str(error)=='IMPORT_ALREADY_ACTIVE':
                        c.execute(update(CYCLES).where(CYCLES.c.id==row['id']).values(next_at=utc_text(now+timedelta(seconds=15)),
                            result={**row['result'],'reason':'WAITING_FOR_SEC_QUEUE'}))
                        return False
                    self._finish(c,row,'BLOCKED','SEC_ENQUEUE_REJECTED')
                    return True
                # Queue insertion and state transition commit together: no dispatch/acknowledgement gap.
                c.execute(update(CYCLES).where(CYCLES.c.id==row['id']).values(state='FETCHING',
                    updated_at=utc_text(now),result={**row['result'],'reason':'SEC_IMPORT','sec_job_id':row['id']}))
                return True
            if row['state']=='FETCHING':
                state = c.scalar(select(JOBS.c.state).where(JOBS.c.id==row['id']))
                if state in ('QUEUED','RUNNING'):
                    return False
                if state!='SUCCEEDED':
                    self._cancel_import(c,row['id'])
                    self._finish(c,row,'PARTIAL','SEC_IMPORT_'+str(state or 'MISSING'))
                    return True
                c.execute(update(CYCLES).where(CYCLES.c.id==row['id']).values(state='REVIEWING',
                    review_cutoff=utc_text(now),updated_at=utc_text(now)))
                return True
            if row['state']=='REVIEWING':
                models = row['result']['models']
                pending = [cik for cik in PILOT_CIKS if cik not in {m['cik'] for m in models}]
                if not pending:
                    self._finish(c,row,'SUCCEEDED' if all(m.get('state')=='PASSED' for m in models) else 'PARTIAL','ACCOUNTING_REVIEW_COMPLETE')
                    return True
                cik = pending[0]
                snapshot = c.scalar(select(TASKS.c.snapshot_id).where(TASKS.c.job_id==row['id'],
                    TASKS.c.cik==cik,TASKS.c.kind=='companyfacts',TASKS.c.state=='SUCCEEDED'))
                review = dict(row), cik, snapshot
        # Existing builder is independently idempotent. If interrupted before checkpoint, retry returns the same model.
        if review:
            row,cik,snapshot = review
            try:
                if not snapshot:
                    raise ValueError('SOURCE_UNAVAILABLE')
                model = CompanyService(self.sec).build(cik,fingerprint(['cycle-model-v1',row['id'],cik]),
                    datetime.fromisoformat(row['review_cutoff']),snapshot_id=snapshot)
                result = dict(cik=cik,id=model['id'],version=model['version'],state=model['payload']['review']['state'])
            except StorageBlocked:
                # Preserve the pending review and its original deadline; retry after recovery.
                return False
            except (ValueError,PermissionError):
                result = dict(cik=cik,state='BLOCKED',reason='MODEL_REVIEW_REJECTED')
            with self.engine.begin() as c:
                c.execute(update(CYCLES).where(CYCLES.c.id==row['id'],CYCLES.c.state=='REVIEWING',CYCLES.c.result==row['result'])
                    .values(result={**row['result'],'models':[*row['result']['models'],result]},updated_at=utc_text(self.clock())))
            return True
        return False

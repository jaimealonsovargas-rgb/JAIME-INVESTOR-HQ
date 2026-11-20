"""Transactional batch checkpoints, shared quotas and fenced publication."""
from datetime import datetime,timedelta
from uuid import uuid4
from sqlalchemy import select,update,func,or_
from sqlalchemy.dialects.sqlite import insert
from app.database import Base
from app.data_identity import fingerprint
from app.universe_store import utc_text
from app.history_rights import rights,require_rights

BATCHES,UNITS,SNAPSHOTS,BUDGET,EVENTS=(Base.metadata.tables['history_'+name] for name in
    ('batches','units','snapshots','provider_budget','events'))
PENDING=('QUEUED','WAITING','RUNNING')
TERMINAL=('SUCCEEDED','EMPTY','FAILED','BLOCKED','CANCELLED')


class HistoryStore:
    def __init__(self,engine): self.engine=engine

    @staticmethod
    def event(c,row,state,reason,now):
        c.execute(EVENTS.insert().values(unit_id=row['id'],at=utc_text(now),state=state,reason=reason,attempt=row['attempts']))

    def enqueue(self,key,body,now):
        saved=body.model_dump(mode='json'); digest=fingerprint(saved); stamp=utc_text(now)
        try: require_rights(body.provider); blocked=False
        except ValueError: blocked=True
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            previous=c.execute(select(BATCHES).where(BATCHES.c.id==key)).mappings().first()
            if previous:
                if previous['request_hash']!=digest: raise ValueError('IDEMPOTENCY_CONFLICT')
                return key
            c.execute(BATCHES.insert().values(id=key,request_hash=digest,request=saved,rights=rights(body.provider),
                state='BLOCKED' if blocked else 'ACTIVE',reason='RIGHTS_UNVERIFIED' if blocked else 'COLLECTION_ONLY',created_at=stamp))
            rows=[]
            for index,request in enumerate(body.units()):
                row=dict(id=fingerprint([key,index]),batch_id=key,sequence=index,request_hash=fingerprint(request),request=request,
                    state='BLOCKED' if blocked else 'QUEUED',reason='RIGHTS_UNVERIFIED' if blocked else 'REGISTERED',attempts=0,
                    next_at=stamp,updated_at=stamp,token=None,lease_until=None,snapshot_hash=None,received_at=None,cache_until=None,
                    coverage=dict(backtest_ready=False,execution_ready=False,identity='PINNED_REQUEST_NOT_VERIFIED',
                                  calendar='NOT_VALIDATED',corporate_actions='NOT_VERIFIED',gaps='NOT_ASSESSED'))
                rows.append(row)
                if len(rows)==500: c.execute(UNITS.insert(),rows); rows=[]
            if rows: c.execute(UNITS.insert(),rows)
        return key

    def status(self,key,offset=0,limit=100):
        if not 0<=offset or not 1<=limit<=500: raise ValueError('INVALID_PAGE')
        with self.engine.connect() as c:
            batch=c.execute(select(BATCHES).where(BATCHES.c.id==key)).mappings().one()
            counts=dict(c.execute(select(UNITS.c.state,func.count()).where(UNITS.c.batch_id==key).group_by(UNITS.c.state)).all())
            rows=c.execute(select(UNITS).where(UNITS.c.batch_id==key).order_by(UNITS.c.sequence).offset(offset).limit(limit)).mappings()
            units=[dict(id=r['id'],listing_id=r['request']['listing_id'],start=r['request']['start'],end=r['request']['end'],
                        state=r['state'],reason=r['reason'],attempts=r['attempts'],next_at=r['next_at'],
                        snapshot_hash=r['snapshot_hash'],received_at=r['received_at'],cache_until=r['cache_until'],coverage=r['coverage']) for r in rows]
            state=batch['state']
            if state=='ACTIVE' and not any(counts.get(s,0) for s in PENDING):
                state='COMPLETED' if not any(counts.get(s,0) for s in ('FAILED','BLOCKED','CANCELLED')) else 'PARTIAL'
            return dict(id=key,state=state,reason=batch['reason'],provider=batch['request']['provider'],rights=batch['rights'],
                counts=counts,total_units=sum(counts.values()),targets=len(batch['request']['targets']),units=units,
                offset=offset,next_offset=offset+len(units) if offset+len(units)<sum(counts.values()) else None,
                backtest_ready=False,execution_ready=False)

    def control(self,key,action,now):
        if action not in ('pause','resume','cancel'): raise ValueError('INVALID_ACTION')
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            batch=c.execute(select(BATCHES).where(BATCHES.c.id==key)).mappings().one()
            if action=='resume' and batch['state']=='PAUSED':
                require_rights(batch['request']['provider'])
                c.execute(update(BATCHES).where(BATCHES.c.id==key).values(state='ACTIVE',reason='RESUMED'))
            elif action=='pause' and batch['state']=='ACTIVE':
                # An in-flight result is not published after pause. Provider lease
                # remains until its worker exits/lease expires, preventing overlap.
                c.execute(update(BATCHES).where(BATCHES.c.id==key).values(state='PAUSED',reason='USER_PAUSED'))
                rows=list(c.execute(select(UNITS).where(UNITS.c.batch_id==key,UNITS.c.state=='RUNNING')).mappings())
                for row in rows:
                    c.execute(update(UNITS).where(UNITS.c.id==row['id']).values(state='WAITING',token=None,lease_until=None,
                        updated_at=utc_text(now),reason='PAUSED_IN_FLIGHT'))
                    self.event(c,row,'WAITING','PAUSED_IN_FLIGHT',now)
            elif action=='cancel' and batch['state'] not in ('CANCELLED','BLOCKED'):
                c.execute(update(BATCHES).where(BATCHES.c.id==key).values(state='CANCELLED',reason='USER_CANCELLED'))
                rows=c.execute(select(UNITS).where(UNITS.c.batch_id==key,UNITS.c.state.in_(PENDING))).mappings().all()
                for row in rows:
                    c.execute(update(UNITS).where(UNITS.c.id==row['id']).values(state='CANCELLED',reason='USER_CANCELLED',
                        token=None,lease_until=None,updated_at=utc_text(now)))
                    self.event(c,row,'CANCELLED','USER_CANCELLED',now)

    def claim(self,key,now):
        stamp=utc_text(now)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            batch=c.execute(select(BATCHES).where(BATCHES.c.id==key)).mappings().one()
            if batch['state']!='ACTIVE': return None
            provider=batch['request']['provider']
            # Check current policy again, not only the policy saved at enqueue.
            try: require_rights(provider)
            except ValueError:
                c.execute(update(BATCHES).where(BATCHES.c.id==key).values(state='BLOCKED',reason='RIGHTS_UNVERIFIED'))
                c.execute(update(UNITS).where(UNITS.c.batch_id==key,UNITS.c.state.in_(PENDING)).values(
                    state='BLOCKED',reason='RIGHTS_UNVERIFIED',token=None,lease_until=None,updated_at=stamp))
                return None
            row=c.execute(select(UNITS).where(UNITS.c.batch_id==key,or_(
                UNITS.c.state.in_(('QUEUED','WAITING')) & (UNITS.c.next_at<=stamp),
                (UNITS.c.state=='RUNNING') & (UNITS.c.lease_until<=stamp))).order_by(UNITS.c.sequence).limit(1)).mappings().first()
            if row is None:return None
            row=dict(row)
            if row['state']=='RUNNING': self.event(c,row,'INTERRUPTED','LEASE_EXPIRED',now)
            if row['attempts']>=3:
                c.execute(update(UNITS).where(UNITS.c.id==row['id']).values(state='FAILED',reason='ATTEMPT_LIMIT',
                    token=None,lease_until=None,updated_at=stamp))
                self.event(c,row,'FAILED','ATTEMPT_LIMIT',now)
                return dict(row,terminal=True)
            cached=c.execute(select(UNITS).where(UNITS.c.request_hash==row['request_hash'],UNITS.c.state=='SUCCEEDED',
                UNITS.c.cache_until>stamp).order_by(UNITS.c.received_at.desc()).limit(1)).mappings().first()
            if cached:
                payload=c.execute(select(SNAPSHOTS.c.payload).where(SNAPSHOTS.c.hash==cached['snapshot_hash'])).scalar_one()
                if fingerprint(payload)!=cached['snapshot_hash']: raise ValueError('SNAPSHOT_INTEGRITY')
                coverage=dict(cached['coverage'],cache_from_unit=cached['id'])
                c.execute(update(UNITS).where(UNITS.c.id==row['id']).values(state='SUCCEEDED',reason='CACHE_REUSED',
                    snapshot_hash=cached['snapshot_hash'],received_at=cached['received_at'],cache_until=cached['cache_until'],
                    coverage=coverage,updated_at=stamp,token=None,lease_until=None))
                self.event(c,row,'SUCCEEDED','CACHE_REUSED',now)
                return dict(row,terminal=True)
            c.execute(insert(BUDGET).values(provider=provider,next_at=stamp,token=None,lease_until=None,
                unit_id=None,window_start=stamp,used=0).on_conflict_do_nothing())
            budget=c.execute(select(BUDGET).where(BUDGET.c.provider==provider)).mappings().one()
            if (budget['lease_until'] and budget['lease_until']>stamp) or budget['next_at']>stamp:return None
            used=budget['used']; window=budget['window_start']
            if datetime.fromisoformat(window)+timedelta(minutes=10)<=now: used=0; window=stamp
            # Conservative local quota shared by every D2 batch/process; no claim
            # that this is a provider entitlement. Fixtures use the same lease, no pacing delay.
            if provider=='IBKR_TWS' and used>=30:
                c.execute(update(BUDGET).where(BUDGET.c.provider==provider).values(
                    next_at=utc_text(datetime.fromisoformat(window)+timedelta(minutes=10))))
                return None
            token=str(uuid4()); lease=utc_text(now+timedelta(seconds=100))
            row.update(token=token,lease_until=lease,state='RUNNING',attempts=row['attempts']+1)
            c.execute(update(BUDGET).where(BUDGET.c.provider==provider).values(token=token,lease_until=lease,
                unit_id=row['id'],next_at=utc_text(now+timedelta(seconds=20 if provider=='IBKR_TWS' else 0)),
                window_start=window,used=used+1))
            c.execute(update(UNITS).where(UNITS.c.id==row['id']).values(token=token,lease_until=lease,
                state='RUNNING',attempts=row['attempts'],reason='FETCH_RESERVED',updated_at=stamp))
            self.event(c,row,'RUNNING','FETCH_RESERVED',now)
            return row

    def owned(self,c,job,now):
        return c.execute(select(UNITS).join(BATCHES,BATCHES.c.id==UNITS.c.batch_id).where(
            UNITS.c.id==job['id'],UNITS.c.token==job['token'],UNITS.c.lease_until>utc_text(now),
            UNITS.c.state=='RUNNING',BATCHES.c.state=='ACTIVE')).mappings().first()

    def release(self,c,job):
        c.execute(update(BUDGET).where(BUDGET.c.provider==job['request']['provider'],BUDGET.c.token==job['token']).values(
            token=None,lease_until=None,unit_id=None))

    def accept(self,job,payload,coverage,received,now):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row=self.owned(c,job,now)
            if row is None:
                self.release(c,job); return False
            require_rights(job['request']['provider'])
            digest=fingerprint(payload)
            c.execute(insert(SNAPSHOTS).values(hash=digest,payload=payload).on_conflict_do_nothing())
            prior=c.execute(select(SNAPSHOTS.c.payload).where(SNAPSHOTS.c.hash==digest)).scalar_one()
            if fingerprint(prior)!=digest:raise ValueError('SNAPSHOT_INTEGRITY')
            state='SUCCEEDED' if payload['bars'] else 'EMPTY'
            c.execute(update(UNITS).where(UNITS.c.id==job['id']).values(state=state,reason='COLLECTED_NOT_ADMITTED',
                snapshot_hash=digest,received_at=utc_text(received),cache_until=utc_text(received+timedelta(hours=24)),
                coverage=coverage,updated_at=utc_text(now),token=None,lease_until=None))
            self.event(c,row,state,'COLLECTED_NOT_ADMITTED',now); self.release(c,job)
        return True

    def fail(self,job,reason,now):
        permanent=reason in {'RIGHTS_UNVERIFIED','DATA_ENTITLEMENT_REQUIRED','INVALID_RESPONSE','IDENTITY_CHANGED','NO_DATA'}
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row=self.owned(c,job,now)
            if row is None:self.release(c,job);return
            state=('BLOCKED' if reason in {'RIGHTS_UNVERIFIED','DATA_ENTITLEMENT_REQUIRED'} else 'FAILED') if permanent or row['attempts']>=3 else 'WAITING'
            delay=600 if reason=='PACING_LIMIT' else min(300,5*3**(row['attempts']-1))
            c.execute(update(UNITS).where(UNITS.c.id==job['id']).values(state=state,reason=reason,token=None,lease_until=None,
                updated_at=utc_text(now),next_at=utc_text(now+timedelta(seconds=delay))))
            if reason=='PACING_LIMIT':
                c.execute(update(BUDGET).where(BUDGET.c.provider==job['request']['provider'],BUDGET.c.token==job['token']).values(
                    next_at=utc_text(now+timedelta(seconds=delay))))
            self.event(c,row,state,reason,now);self.release(c,job)

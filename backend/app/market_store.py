"""Resumable, fenced market imports. Nothing here writes portfolio tables."""
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select, insert, update, func, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import Base
from app.data_identity import fingerprint
from app.universe_store import LISTINGS, IMPORTS, UniverseStore, utc_text

JOBS, RECEIPTS, BARS, ENDPOINTS = (Base.metadata.tables['market_' + name]
    for name in ('jobs', 'receipts', 'bars', 'endpoint_status'))
ACTIVE = ('QUEUED', 'RUNNING', 'WAITING', 'PAUSED')


class MarketStore:
    def __init__(self, engine):
        self.engine = engine

    def target(self, ident, connection=None):
        if connection is None:
            with self.engine.connect() as c:
                return self.target(ident, c)
        row = connection.execute(select(LISTINGS).where(LISTINGS.c.id == ident)).mappings().first()
        if not row:
            raise KeyError(ident)
        if row['provider'] != 'ALPACA' or row['state'] != 'IDENTIFIED' or row['payload'].get('category') != 'US_EQUITY':
            raise ValueError('ALPACA_IDENTITY_REQUIRED')
        count = connection.execute(select(func.count()).select_from(LISTINGS).where(
            LISTINGS.c.provider == 'ALPACA', LISTINGS.c.symbol == row['symbol'],
            LISTINGS.c.state != 'NOT_OBSERVED')).scalar_one()
        if count != 1 or row['payload'].get('provider_status') != 'active':
            raise ValueError('AMBIGUOUS_OR_INACTIVE_ASSET')
        return dict(row)

    def enqueue(self, key, request, now):
        stamp, request_hash = utc_text(now), fingerprint(request)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            prior = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if prior:
                if prior['request_hash'] != request_hash:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return key
            if c.execute(select(JOBS.c.id).where(JOBS.c.state.in_(ACTIVE))).first():
                raise ValueError('IMPORT_ALREADY_ACTIVE')
            saved = dict(request)
            if request.get('listing_id'):
                row = self.target(request['listing_id'], c)
                saved.update(symbol=row['symbol'], asset_id=row['provider_key'],
                    identity_hash=fingerprint(row['payload']), catalogue_seen_at=row['last_seen_at'])
            steps = {'connection': ['clock', 'account', 'positions'], 'catalogue': ['assets'],
                'snapshot': ['clock', 'snapshot'], 'history': ['calendar', 'bars', 'corporate_actions']}[request['kind']]
            c.execute(insert(JOBS).values(id=key, request_hash=request_hash, kind=request['kind'],
                listing_id=request.get('listing_id'), state='QUEUED', created_at=stamp, updated_at=stamp,
                next_at=stamp, attempts=0, request=saved,
                progress=dict(step=0, steps=steps, pages=0, bars=0, next_token=None, seen_tokens=[], errors=[])))
        return key

    @staticmethod
    def public(row):
        return {k: row[k] for k in ('id', 'kind', 'listing_id', 'state', 'created_at', 'updated_at')} | {
            'reason': row['error'] or ('Consulta finalizada.' if row['state'] == 'SUCCEEDED' else ''),
            'progress': {k: row['progress'].get(k, 0) for k in ('pages', 'bars')},
            'next_at': row['next_at'], 'errors': row['progress'].get('errors', [])}

    def job(self, key):
        with self.engine.connect() as c:
            row = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if row is None:
                raise KeyError(key)
            return self.public(row)

    def claim(self, now):
        stamp = utc_text(now)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = c.execute(select(JOBS).where(or_(
                JOBS.c.state.in_(('QUEUED', 'WAITING')) & (JOBS.c.next_at <= stamp),
                (JOBS.c.state == 'RUNNING') & (JOBS.c.lease_until <= stamp)))
                .order_by(JOBS.c.created_at).limit(1)).mappings().first()
            if row is None:
                return None
            token, lease = str(uuid4()), utc_text(now + timedelta(minutes=2))
            c.execute(update(JOBS).where(JOBS.c.id == row['id']).values(
                state='RUNNING', token=token, lease_until=lease, updated_at=stamp))
            return dict(row) | dict(token=token, lease_until=lease, state='RUNNING')

    def owned(self, c, job, now):
        return c.execute(select(JOBS).where(JOBS.c.id == job['id'], JOBS.c.token == job['token'],
            JOBS.c.state == 'RUNNING', JOBS.c.lease_until > utc_text(now))).mappings().first()

    def control(self, key, action, now):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if row is None:
                raise KeyError(key)
            if action == 'cancel' and row['state'] in ACTIVE:
                c.execute(update(JOBS).where(JOBS.c.id == key).values(
                    state='CANCELLED', token=None, lease_until=None, updated_at=utc_text(now)))
            elif action == 'resume' and row['state'] in ('FAILED', 'PAUSED'):
                if c.execute(select(JOBS.c.id).where(JOBS.c.id != key, JOBS.c.state.in_(ACTIVE))).first():
                    raise ValueError('IMPORT_ALREADY_ACTIVE')
                c.execute(update(JOBS).where(JOBS.c.id == key).values(state='QUEUED', attempts=0,
                    error=None, token=None, lease_until=None, next_at=utc_text(now), updated_at=utc_text(now)))
        return self.job(key)

    @staticmethod
    def endpoint(c, kind, state, now, reason):
        c.execute(sqlite_insert(ENDPOINTS).values(id=kind, state=state, checked_at=utc_text(now), reason=reason)
            .on_conflict_do_update(index_elements=['id'], set_=dict(state=state, checked_at=utc_text(now), reason=reason)))

    def defer(self, job, error, now, delay=5, attempted=True, terminal=False, optional=False):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = self.owned(c, job, now)
            if row is None:
                return
            p = dict(row['progress'])
            kind = p['steps'][p['step']]
            attempts = row['attempts'] + int(attempted)
            done = terminal or attempts >= 3
            if attempted:
                self.endpoint(c, kind, error, now, 'Consulta no disponible; evidencia anterior conservada.')
            state = 'FAILED' if done else 'WAITING'
            if done and optional:
                p['errors'] = [*p['errors'], {'endpoint': kind, 'state': error}]
                p.update(step=p['step'] + 1, next_token=None, seen_tokens=[])
                state = 'PARTIAL' if p['step'] == len(p['steps']) else 'QUEUED'
                attempts = 0
            elif done and error in ('AUTH_FAILED', 'RIGHTS_RESTRICTED'):
                state = 'PAUSED'
            c.execute(update(JOBS).where(JOBS.c.id == row['id']).values(state=state,
                error=error, attempts=attempts, progress=p, token=None, lease_until=None,
                updated_at=utc_text(now), next_at=utc_text(now + timedelta(seconds=delay))))

    def accept(self, job, kind, payload, digest, source, params, received, now, *, bars=None, next_token=None, catalogue=None):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = self.owned(c, job, now)
            if row is None:
                return False
            p = dict(row['progress'])
            if p['steps'][p['step']] != kind:
                raise ValueError('STEP_MISMATCH')
            if next_token and (next_token in p['seen_tokens'] or len(p['seen_tokens']) >= 11):
                raise ValueError('PAGINATION_CYCLE_OR_LIMIT')
            if job['listing_id']:
                current = self.target(job['listing_id'], c)
                if fingerprint(current['payload']) != job['request']['identity_hash']:
                    raise ValueError('IDENTITY_CHANGED')
            if catalogue is not None:
                catalogue_key = 'market-' + fingerprint([job['id'], 'catalogue'])
                c.execute(insert(IMPORTS).values(id=catalogue_key, provider='ALPACA', state='RUNNING',
                    started_at=utc_text(received), payload={}))
                UniverseStore(self.engine).apply_snapshot(catalogue_key, 'ALPACA', catalogue, source, digest, received, connection=c)
            if bars is not None:
                existing = {r['timestamp']: r['payload'] for r in c.execute(select(BARS).where(BARS.c.job_id == job['id'])).mappings()}
                fresh = []
                for bar in bars:
                    timestamp = bar['timestamp']
                    if timestamp in existing:
                        if existing[timestamp] != bar:
                            raise ValueError('CONTRADICTORY_BAR')
                    else:
                        fresh.append(dict(job_id=job['id'], timestamp=timestamp, payload=bar))
                        existing[timestamp] = bar
                if c.execute(select(func.count()).select_from(BARS)).scalar_one() + len(fresh) > 500000:
                    raise ValueError('LOCAL_STORAGE_LIMIT')
                if fresh:
                    c.execute(insert(BARS), fresh)
                p['bars'] += len(fresh)
                if not next_token:
                    p['bars_complete'] = True
            c.execute(insert(RECEIPTS).values(id=fingerprint([job['id'], kind, params, digest]),
                job_id=job['id'], listing_id=job['listing_id'], kind=kind, received_at=utc_text(received),
                payload_hash=digest, source=source, params=params, payload=payload))
            self.endpoint(c, kind, 'AVAILABLE' if payload.get('real_connection') else 'TEST_ONLY', received, 'Respuesta validada; acceso comprobado para esta consulta.')
            p['pages'] += 1
            if next_token:
                p.update(next_token=next_token, seen_tokens=[*p['seen_tokens'], next_token])
            else:
                p[kind + '_complete'] = True
                p.update(step=p['step'] + 1, next_token=None, seen_tokens=[])
            state = ('PARTIAL' if p['errors'] else 'SUCCEEDED') if p['step'] == len(p['steps']) else 'QUEUED'
            c.execute(update(JOBS).where(JOBS.c.id == job['id']).values(state=state, progress=p, attempts=0,
                token=None, lease_until=None, error=None, updated_at=utc_text(now), next_at=utc_text(now)))
            return True

    def latest(self, kind, listing_id=None, as_of=None, identity_hash=None):
        query = select(RECEIPTS).where(RECEIPTS.c.kind == kind)
        if listing_id is not None:
            query = query.where(RECEIPTS.c.listing_id == listing_id)
        if as_of is not None:
            query = query.where(RECEIPTS.c.received_at <= utc_text(as_of))
        if identity_hash is not None:
            query = query.join(JOBS, JOBS.c.id == RECEIPTS.c.job_id).where(
                func.json_extract(JOBS.c.request, '$.identity_hash') == identity_hash)
        with self.engine.connect() as c:
            row = c.execute(query.order_by(RECEIPTS.c.received_at.desc(), RECEIPTS.c.id).limit(1)).mappings().first()
            return dict(row) if row else None

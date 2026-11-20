"""Atomic endpoint commits, fencing leases and immutable financial provenance."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from contextlib import nullcontext
from sqlalchemy import select, insert, update, func, or_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import Base
from app.data_identity import fingerprint
from app.sec_normalize import PARSER_VERSION, METRICS, annual_view
from app.sec_pilot import PILOT_VERSION, select_pilot
from app.universe_store import LISTINGS, utc_text

JOBS, TASKS, SNAPSHOTS, RECEIPTS, FACTS, FILINGS = (Base.metadata.tables['sec_' + name]
    for name in ('jobs', 'tasks', 'snapshots', 'receipts', 'facts', 'filings'))
TERMINAL = ('SUCCEEDED', 'NO_DATA', 'FAILED', 'CANCELLED')


class SecStore:
    def __init__(self, engine):
        self.engine = engine

    def enqueue(self, key, ciks, now, *, connection=None):
        stamp = utc_text(now)
        request_hash = fingerprint(['issuer-import-v1', sorted(ciks) if ciks else PILOT_VERSION])
        with self.engine.begin() if connection is None else nullcontext(connection) as c:
            if connection is None:
                c.exec_driver_sql('BEGIN IMMEDIATE')
            prior = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if prior:
                if prior['request_hash'] != request_hash:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return key
            # One active import, including pauses; callers see the existing work.
            active = c.execute(select(JOBS.c.id).where(JOBS.c.state.in_(['QUEUED', 'RUNNING', 'PAUSED']))).scalar()
            if active:
                raise ValueError('IMPORT_ALREADY_ACTIVE')
            if ciks:
                rows = c.execute(select(LISTINGS).where(LISTINGS.c.provider == 'SEC', LISTINGS.c.cik.in_(ciks),
                    LISTINGS.c.state == 'IDENTIFIED').order_by(LISTINGS.c.symbol)).mappings().all()
                by_cik = {}
                for row in rows:
                    by_cik.setdefault(row['cik'], dict(cik=row['cik'], symbol=row['symbol'], name=row['name'],
                        listing_id=row['id'], catalogue_seen_at=row['last_seen_at']))
                if set(by_cik) != set(ciks):
                    raise ValueError('ISSUER_NOT_IDENTIFIED')
                entities = [by_cik[cik] for cik in ciks]
            else:
                entities = select_pilot(c)
            manifest = dict(version=PILOT_VERSION if not ciks else 'explicit-issuers-v1', issuers=entities,
                parser_version=PARSER_VERSION, metric_denominator=len(METRICS), created_at=stamp,
                selection='Muestra técnica por conveniencia; no es un índice ni una recomendación de inversión.',
                temporal_scope='Conocimiento local desde la descarga; no universo histórico de mercado.')
            c.execute(insert(JOBS).values(id=key, request_hash=request_hash, state='QUEUED', created_at=stamp,
                                         updated_at=stamp, manifest=manifest))
            c.execute(insert(TASKS), [dict(id=fingerprint([key, row['cik'], kind]), job_id=key, cik=row['cik'],
                kind=kind, ordinal=i * 2 + j, state='PENDING', attempts=0, next_at=stamp)
                for i, row in enumerate(entities) for j, kind in enumerate(('submissions', 'companyfacts'))])
        return key

    def job(self, key):
        with self.engine.connect() as c:
            job = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if job is None:
                raise KeyError(key)
            tasks = [dict(row) for row in c.execute(select(TASKS).where(TASKS.c.job_id == key)
                .order_by(TASKS.c.ordinal)).mappings()]
        counts = {state: sum(t['state'] == state for t in tasks) for state in
                  ('PENDING', 'RUNNING', 'WAITING', *TERMINAL)}
        return dict(id=key, state=job['state'], created_at=job['created_at'], updated_at=job['updated_at'],
            manifest=job['manifest'], total=len(tasks), completed=sum(counts[s] for s in TERMINAL), counts=counts,
            current=[dict(cik=t['cik'], kind=t['kind'], state=t['state'], error=t['error'], next_at=t['next_at'])
                     for t in tasks if t['state'] in ('RUNNING', 'WAITING')][:5],
            errors=[dict(cik=t['cik'], kind=t['kind'], state=t['state'], error=t['error'])
                    for t in tasks if t['error'] and t['state'] in ('FAILED', 'NO_DATA')][:100])

    def control(self, key, action, now):
        stamp = utc_text(now)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            job = c.execute(select(JOBS).where(JOBS.c.id == key)).mappings().first()
            if job is None:
                raise KeyError(key)
            if action == 'pause' and job['state'] in ('QUEUED', 'RUNNING'):
                c.execute(update(JOBS).where(JOBS.c.id == key).values(state='PAUSED', updated_at=stamp))
            elif action == 'resume' and job['state'] in ('PAUSED', 'PARTIAL'):
                active = c.execute(select(JOBS.c.id).where(JOBS.c.id != key, JOBS.c.state.in_(['QUEUED', 'RUNNING', 'PAUSED']))).scalar()
                if active:
                    raise ValueError('IMPORT_ALREADY_ACTIVE')
                c.execute(update(TASKS).where(TASKS.c.job_id == key, TASKS.c.state.in_(['FAILED', 'NO_DATA']))
                    .values(state='PENDING', attempts=0, error=None, next_at=stamp))
                c.execute(update(JOBS).where(JOBS.c.id == key).values(state='QUEUED', updated_at=stamp))
            elif action == 'cancel' and job['state'] in ('QUEUED', 'RUNNING', 'PAUSED'):
                c.execute(update(TASKS).where(TASKS.c.job_id == key, TASKS.c.state.not_in(TERMINAL))
                    .values(state='CANCELLED', token=None, lease_until=None))
                c.execute(update(JOBS).where(JOBS.c.id == key).values(state='CANCELLED', updated_at=stamp))
        return self.job(key)

    def claim(self, now):
        stamp = utc_text(now)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = c.execute(select(TASKS).join(JOBS, JOBS.c.id == TASKS.c.job_id).where(
                JOBS.c.state.in_(['QUEUED', 'RUNNING']),
                or_((TASKS.c.state.in_(['PENDING', 'WAITING'])) & (TASKS.c.next_at <= stamp),
                    (TASKS.c.state == 'RUNNING') & (TASKS.c.lease_until <= stamp)))
                .order_by(JOBS.c.created_at, TASKS.c.ordinal).limit(1)).mappings().first()
            if not row:
                return None
            token = str(uuid4())
            c.execute(update(TASKS).where(TASKS.c.id == row['id']).values(state='RUNNING', token=token,
                lease_until=utc_text(now + timedelta(minutes=3))))
            c.execute(update(JOBS).where(JOBS.c.id == row['job_id']).values(state='RUNNING', updated_at=stamp))
            return {**row, 'token': token}

    def _owned(self, c, task):
        return c.execute(select(TASKS).where(TASKS.c.id == task['id'], TASKS.c.token == task['token'],
                                            TASKS.c.state == 'RUNNING')).mappings().first()

    def defer(self, task, next_at, error, now, *, attempted=False, terminal=False):
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = self._owned(c, task)
            if row is None:
                return
            attempts = row['attempts'] + int(attempted)
            state = 'NO_DATA' if error == 'NOT_FOUND' else 'FAILED' if terminal or attempts >= 3 else 'WAITING'
            c.execute(update(TASKS).where(TASKS.c.id == task['id']).values(state=state, attempts=attempts,
                next_at=next_at, error=error, token=None, lease_until=None))
            self._finish_job(c, task['job_id'], now)

    def _finish_job(self, c, key, now):
        current = c.execute(select(JOBS.c.state).where(JOBS.c.id == key)).scalar_one()
        if current == 'CANCELLED':
            return
        states = list(c.execute(select(TASKS.c.state).where(TASKS.c.job_id == key)).scalars())
        state = current
        if all(s in TERMINAL for s in states):
            state = 'SUCCEEDED' if all(s == 'SUCCEEDED' for s in states) else 'PARTIAL'
        c.execute(update(JOBS).where(JOBS.c.id == key).values(state=state, updated_at=utc_text(now)))

    def accept(self, task, rows, metadata, payload_hash, source, received_at, now):
        ident = fingerprint([task['cik'], task['kind'], payload_hash, PARSER_VERSION])
        stamp = utc_text(received_at)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            owned = self._owned(c, task)
            if owned is None:
                return False
            exists = c.execute(select(SNAPSHOTS.c.id).where(SNAPSHOTS.c.id == ident)).scalar()
            if exists is None:
                c.execute(insert(SNAPSHOTS).values(id=ident, cik=task['cik'], kind=task['kind'],
                    payload_hash=payload_hash, parser_version=PARSER_VERSION, source=source,
                    first_received_at=stamp, metadata=metadata))
                if task['kind'] == 'companyfacts':
                    records = [dict(snapshot_id=ident, id=r['id'], metric=r['metric'], period_end=r['end'],
                                    filed=r['filed'], payload=r) for r in rows]
                    table = FACTS
                else:
                    records = [dict(snapshot_id=ident, accession=r['accession'], filed=r['filed'], form=r['form'], payload=r) for r in rows]
                    table = FILINGS
                for offset in range(0, len(records), 500):
                    c.execute(insert(table), records[offset:offset + 500])
            c.execute(sqlite_insert(RECEIPTS).values(id=fingerprint([task['id'], ident, stamp]),
                task_id=task['id'], snapshot_id=ident, cik=task['cik'], kind=task['kind'], received_at=stamp)
                .on_conflict_do_nothing())
            if task['kind'] == 'companyfacts' and rows:
                from app.company_updates import enqueue_update
                enqueue_update(c, task['cik'], ident, payload_hash, stamp)
            c.execute(update(TASKS).where(TASKS.c.id == task['id']).values(state='SUCCEEDED' if rows else 'NO_DATA',
                error=None if rows else 'EMPTY_RESPONSE', snapshot_id=ident, attempts=owned['attempts'] + 1,
                token=None, lease_until=None))
            self._finish_job(c, task['job_id'], now)
        return True

    def summary(self):
        with self.engine.connect() as c:
            latest = c.execute(select(JOBS.c.id).order_by(JOBS.c.created_at.desc()).limit(1)).scalar()
            counts = {}
            for kind, label, field in [('companyfacts', 'issuers_with_facts', 'fact_count'), ('submissions', 'issuers_with_documents', 'document_count')]:
                counts[label] = c.execute(select(func.count(func.distinct(SNAPSHOTS.c.cik))).where(
                    SNAPSHOTS.c.kind == kind, func.json_extract(SNAPSHOTS.c.metadata, '$.' + field) > 0)).scalar_one()
            counts['snapshots'] = c.execute(select(func.count()).select_from(SNAPSHOTS)).scalar_one()
            counts['receipts'] = c.execute(select(func.count()).select_from(RECEIPTS)).scalar_one()
        return dict(counts=counts, latest_job=self.job(latest) if latest else None,
                    metric_denominator=len(METRICS), temporal_scope='LOCAL_KNOWLEDGE_ONLY')

    def _snapshot(self, c, cik, kind, as_of):
        stamp = utc_text(as_of)
        return c.execute(select(SNAPSHOTS, RECEIPTS.c.received_at).join(RECEIPTS, RECEIPTS.c.snapshot_id == SNAPSHOTS.c.id)
            .where(RECEIPTS.c.cik == cik, RECEIPTS.c.kind == kind, RECEIPTS.c.received_at <= stamp)
            .order_by(RECEIPTS.c.received_at.desc(), RECEIPTS.c.id.desc()).limit(1)).mappings().first()

    def financials(self, cik, as_of):
        with self.engine.connect() as c:
            facts_snapshot = self._snapshot(c, cik, 'companyfacts', as_of)
            profile_snapshot = self._snapshot(c, cik, 'submissions', as_of)
            facts = list(c.execute(select(FACTS.c.payload).where(FACTS.c.snapshot_id == facts_snapshot['id'])).scalars()) if facts_snapshot else []
            # Both receipt and conservative publication bound must precede as_of.
            facts = [f for f in facts if datetime.fromisoformat(f['published_bound']) <= as_of]
            revisions = {}
            for fact in facts:
                key = (fact['taxonomy'], fact['concept'], fact['unit'], fact['start'], fact['end'])
                revisions.setdefault(key, set()).add(Decimal(fact['value']))
            changed = sum(len(values) > 1 for values in revisions.values())
            annual = annual_view(facts)
            if annual:
                annual['age_days'] = (as_of.date() - datetime.fromisoformat(annual['end']).date()).days
                annual['stale'] = annual['age_days'] > 550
            docs = self.documents(cik, as_of, 0, 10, connection=c)
        sources = [dict(id=s['id'], kind=s['kind'], source=s['source'], payload_hash=s['payload_hash'],
            parser_version=s['parser_version'], received_at=s['received_at'], first_received_at=s['first_received_at'])
            for s in (facts_snapshot, profile_snapshot) if s]
        return dict(cik=cik, as_of=utc_text(as_of), annual=annual, sources=sources,
            profile=profile_snapshot['metadata'] if profile_snapshot else None, documents=docs,
            coverage=dict(facts=len(facts), metrics=len({f['metric'] for f in facts}), metric_denominator=len(METRICS),
                periods=len({(f['start'], f['end']) for f in facts}), changed_value_groups=changed,
                quarantined_facts=sum(bool(f.get('quality_flags')) for f in facts),
                oldest_period=min((f['end'] for f in facts), default=None), newest_period=max((f['end'] for f in facts), default=None)),
            readiness=[dict(use='FINANCIAL_RESEARCH', state='STALE' if annual and annual['stale'] else 'DESCRIPTIVE_AVAILABLE' if annual and annual['state'] == 'DESCRIPTIVE_COMPLETE' else 'PARTIAL' if facts else 'NO_DATA',
                reason='Cuentas descriptivas por documento y periodo; requieren revisión para modelos o recomendaciones.'),
                dict(use='BACKTEST', state='BLOCKED', reason='Sin históricos de precios, universo histórico ni ajustes certificados.'),
                dict(use='PAPER', state='BLOCKED', reason='Sin cotización vinculada, controles de riesgo ni ejecución habilitada.')],
            limitations=['Datos de conceptos estándar de toda la entidad; no cubren etiquetas propias ni segmentos.',
                'Las cifras comparativas pueden variar por revisiones, reclasificaciones o ajustes; no se interpreta automáticamente su causa.',
                'La fecha fiscal de la presentación no se usa como año del dato comparativo.',
                'Conocimiento local desde la descarga; no acredita disponibilidad histórica de mercado.'])

    def documents(self, cik, as_of, offset, limit, connection=None):
        if connection is None:
            with self.engine.connect() as c:
                return self.documents(cik, as_of, offset, limit, c)
        snapshot = self._snapshot(connection, cik, 'submissions', as_of)
        if not snapshot:
            return dict(items=[], total=0, offset=offset, limit=limit, older_history_pending=False)
        conditions = [FILINGS.c.snapshot_id == snapshot['id'],
            func.json_extract(FILINGS.c.payload, '$.published_bound') <= as_of.isoformat()]
        total = connection.execute(select(func.count()).select_from(FILINGS).where(*conditions)).scalar_one()
        rows = list(connection.execute(select(FILINGS.c.payload).where(*conditions).order_by(
            FILINGS.c.filed.desc(), FILINGS.c.accession.desc()).offset(offset).limit(limit)).scalars())
        return dict(items=rows, total=total, offset=offset, limit=limit,
                    older_history_pending=bool(snapshot['metadata']['older_files']))

    def fact_history(self, cik, metric, as_of, offset, limit):
        with self.engine.connect() as c:
            snapshot = self._snapshot(c, cik, 'companyfacts', as_of)
            if not snapshot:
                return dict(items=[], total=0, offset=offset, limit=limit)
            conditions = [FACTS.c.snapshot_id == snapshot['id'], FACTS.c.metric == metric,
                func.json_extract(FACTS.c.payload, '$.published_bound') <= as_of.isoformat()]
            total = c.execute(select(func.count()).select_from(FACTS).where(*conditions)).scalar_one()
            rows = list(c.execute(select(FACTS.c.payload).where(*conditions).order_by(
                FACTS.c.period_end.desc(), FACTS.c.filed.desc(), FACTS.c.id).offset(offset).limit(limit)).scalars())
        return dict(items=rows, total=total, offset=offset, limit=limit)

"""Bounded synchronous builds from pinned local SEC evidence. No HTTP or LLM calls."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
import re
from decimal import Decimal
from sqlalchemy import select, insert, func
from app.database import Base
from app.data_identity import fingerprint
from app.sec_store import SecStore, SNAPSHOTS, RECEIPTS, FACTS, FILINGS
from app.sec_normalize import cik_text, PARSER_VERSION, parse_companyfacts, ANNUAL_FORMS
from app.sec_http import MAX_BYTES
from app.universe_store import utc_text
from app.company_model import build_model, TEMPLATE
from app.company_review import review_model
from app.filing_archive import read_filing
from app.storage_budget import admitted

MODELS, REQUESTS = (Base.metadata.tables[n] for n in ('company_models', 'company_model_requests'))


class CompanyService:
    def __init__(self, sec):
        self.sec, self.data, self.engine = sec, sec.data, sec.data.engine

    def readable(self):
        if self.sec.access() in ('DISABLED', 'RIGHTS_RESTRICTED'):
            raise PermissionError('SOURCE_UNAVAILABLE')

    def source(self, c, cik, cutoff, snapshot_id=None):
        snap = SecStore(self.engine)._snapshot(c, cik, 'companyfacts', cutoff)
        if snapshot_id:
            snap = c.execute(select(SNAPSHOTS).where(SNAPSHOTS.c.id == snapshot_id,
                SNAPSHOTS.c.cik == cik, SNAPSHOTS.c.kind == 'companyfacts',
                SNAPSHOTS.c.first_received_at <= utc_text(cutoff))).mappings().first()
        if not snap:
            raise ValueError('NO_FINANCIAL_DATA')
        receipt = c.execute(select(RECEIPTS).where(RECEIPTS.c.snapshot_id == snap['id'],
            RECEIPTS.c.received_at <= utc_text(cutoff)).order_by(RECEIPTS.c.received_at, RECEIPTS.c.id).limit(1)).mappings().one()
        facts = list(c.execute(select(FACTS.c.payload).where(FACTS.c.snapshot_id == snap['id']).limit(150001)).scalars())
        if len(facts) > 150000:
            raise ValueError('MODEL_INPUT_LIMIT')
        reparsed = snap['parser_version'] != PARSER_VERSION
        if reparsed:
            digest = snap['payload_hash']
            if not re.fullmatch('[a-f0-9]{64}', digest):
                raise ValueError('INVALID_ARCHIVE_HASH')
            try:
                with gzip.open(self.sec.raw_root / (digest + '.json.gz'), 'rb') as archived:
                    raw = archived.read(MAX_BYTES + 1)
            except (OSError, EOFError):
                raise ValueError('ORIGINAL_UNAVAILABLE') from None
            if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('ORIGINAL_INTEGRITY_FAILED')
            facts, _ = parse_companyfacts(json.loads(raw, parse_float=Decimal), cik)
        facts = [f for f in facts if datetime.fromisoformat(f['published_bound']) <= cutoff
                 and f['end'] <= cutoff.date().isoformat() and not f.get('quality_flags')]
        source = dict(snapshot_id=snap['id'], receipt_id=receipt['id'], received_at=receipt['received_at'],
            payload_hash=snap['payload_hash'], parser_version=PARSER_VERSION,
            snapshot_parser_version=snap['parser_version'], normalization='SAVED_ORIGINAL' if reparsed else 'STORED_FACTS',
            url=snap['source'], name=snap['metadata']['name'])
        return facts, source

    @admitted
    def build(self, cik, key, as_of=None, *, snapshot_id=None):
        self.readable()
        cik = cik_text(cik)
        now = self.data.clock()
        if as_of is not None and (as_of.utcoffset() is None or as_of > now):
            raise ValueError('INVALID_KNOWLEDGE_CUTOFF')
        cutoff = (as_of or now).astimezone(timezone.utc)
        request_hash = fingerprint([cik, as_of.isoformat() if as_of else 'LATEST', TEMPLATE])
        if snapshot_id:
            request_hash = fingerprint([request_hash, snapshot_id])
        # Source pin, CPU calculation and version assignment share one short transaction.
        # No network, sleeps or inference while holding SQLite's write lock.
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            request = c.execute(select(REQUESTS).where(REQUESTS.c.id == key)).mappings().first()
            if request:
                if request['request_hash'] != request_hash:
                    original = c.execute(select(MODELS.c.payload).where(MODELS.c.id==request['model_id'],MODELS.c.cik==cik)).scalar()
                    if original is None:
                        raise ValueError('IDEMPOTENCY_CONFLICT')
                    prior_hash = fingerprint([cik,as_of.isoformat() if as_of else 'LATEST',original['template_version']])
                    if snapshot_id:
                        prior_hash = fingerprint([prior_hash,snapshot_id])
                    if prior_hash!=request['request_hash']:
                        raise ValueError('IDEMPOTENCY_CONFLICT')
                return self._get(c, request['model_id'], cik)
            facts, source = self.source(c, cik, cutoff, snapshot_id)
            payload = build_model(cik, facts, source)
            payload['annual_filing_coverage'] = self.filing_coverage(c,cik,payload['annual'],cutoff)
            filing = read_filing(self.sec,payload,cutoff)
            if filing:
                payload['filing_statement'] = filing
            payload['review'] = review_model(payload)
            input_hash = fingerprint(payload)
            ident = fingerprint([cik, TEMPLATE, input_hash])
            existing = c.execute(select(MODELS.c.id).where(MODELS.c.id == ident)).scalar()
            if not existing:
                count = c.execute(select(func.count()).select_from(MODELS)).scalar_one()
                if count >= 10000:
                    raise ValueError('MODEL_STORAGE_LIMIT')
                prior = c.execute(select(MODELS).where(MODELS.c.cik == cik).order_by(MODELS.c.version.desc()).limit(1)).mappings().first()
                if snapshot_id and prior and (payload['annual']['end'], payload['annual']['filed']) < (prior['payload']['annual']['end'], prior['payload']['annual']['filed']):
                    raise ValueError('OLDER_FINANCIAL_REPORT')
                payload['update'] = self.difference(payload, prior['payload'] if prior else None)
                c.execute(insert(MODELS).values(id=ident, cik=cik, version=prior['version']+1 if prior else 1,
                    created_at=utc_text(now), as_of=utc_text(cutoff), previous_id=prior['id'] if prior else None,
                    input_hash=input_hash, payload_hash=fingerprint(payload), payload=payload))
            c.execute(insert(REQUESTS).values(id=key, request_hash=request_hash, model_id=ident, created_at=utc_text(now)))
            return self._get(c, ident, cik)

    def filing_coverage(self,c,cik,annual,cutoff):
        snapshot = self.sec.store._snapshot(c,cik,'submissions',cutoff)
        if snapshot is None:
            return dict(state='BLOCKED',reason='Falta el catálogo local de informes para contrastar este ejercicio.')
        reports = c.scalars(select(FILINGS.c.payload).where(FILINGS.c.snapshot_id==snapshot['id'],
                            FILINGS.c.form.in_(ANNUAL_FORMS)))
        eligible = [r for r in reports if r.get('report_date') and datetime.fromisoformat(r['published_bound'])<=cutoff]
        if not eligible:
            return dict(state='BLOCKED',reason='El catálogo local carece de un informe anual comparable.')
        latest = max(eligible,key=lambda r:(r['report_date'],r['filed'],r['accession']))
        pending = (latest['report_date'],latest['filed'])>=(annual['end'],annual['filed']) and latest['accession']!=annual['accession']
        return dict(state='BLOCKED' if pending else 'PASS',
            reason='Existe un informe anual posterior pendiente de incorporar al modelo.' if pending else
                   'El modelo cubre el informe anual más reciente del catálogo local consultado.',
            catalogue_received_at=snapshot['first_received_at'],accession=latest['accession'],url=latest['url'],
            report_date=latest['report_date'],filed=latest['filed'])

    @staticmethod
    def difference(current, previous):
        if previous is None:
            return dict(reason='FIRST_MODEL', changes=[])
        if (current['annual']['start'], current['annual']['end']) != (previous['annual']['start'], previous['annual']['end']):
            return dict(reason='NEW_PERIOD', changes=[])
        old = {m['metric']: m['fact'] for m in previous['annual']['metrics']}
        changes = []
        for m in current['annual']['metrics']:
            a, b = m['fact'], old.get(m['metric'])
            signature = lambda f: (f['value'], f['unit'], f['taxonomy'], f['concept']) if f else None
            if signature(a) != signature(b):
                changes.append(dict(metric=m['metric'], label=m['label'], before=b, after=a))
        mapping_changed = current['template_version'] != previous['template_version'] or current['source'].get('parser_version') != previous['source'].get('parser_version')
        return dict(reason='MAPPING_UPDATED' if mapping_changed else 'REPORTED_VALUES_CHANGED' if changes else 'NEW_EVIDENCE', changes=changes)

    @staticmethod
    def _get(c, ident, cik):
        row = c.execute(select(MODELS).where(MODELS.c.id == ident, MODELS.c.cik == cik)).mappings().first()
        if not row:
            raise KeyError(ident)
        return dict(row)

    def get(self, cik, ident):
        self.readable()
        with self.engine.connect() as c:
            return self._get(c, ident, cik_text(cik))

    def versions(self, cik, offset=0, limit=20):
        self.readable()
        cik = cik_text(cik)
        with self.engine.connect() as c:
            total = c.execute(select(func.count()).select_from(MODELS).where(MODELS.c.cik == cik)).scalar_one()
            rows = c.execute(select(MODELS).where(MODELS.c.cik == cik).order_by(MODELS.c.version.desc()).offset(offset).limit(limit)).mappings()
            items = [self.brief(r) for r in rows]
        return dict(items=items, total=total, offset=offset, limit=limit)

    @staticmethod
    def brief(row):
        p = row['payload']
        return dict(id=row['id'], cik=row['cik'], name=p['source']['name'], version=row['version'], created_at=row['created_at'],
            as_of=row['as_of'], period_end=p['annual']['end'], state=p['review']['state'],
            reason=p['update']['reason'], evidence_count=len(p['evidence']))

    def recent(self):
        self.readable()
        with self.engine.connect() as c:
            rows = c.execute(select(MODELS).order_by(MODELS.c.created_at.desc(), MODELS.c.id).limit(5)).mappings()
            return [self.brief(r) for r in rows]

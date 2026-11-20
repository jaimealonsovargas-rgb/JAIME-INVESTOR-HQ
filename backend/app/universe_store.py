"""Local knowledge intervals; a missing listing is never inferred to be delisted."""
from collections import defaultdict
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, or_, update, insert
from app.database import Base
from app.data_identity import fingerprint

ENTITIES, LISTINGS, VERSIONS, IMPORTS = (Base.metadata.tables['universe_' + name]
    for name in ('entities', 'listings', 'versions', 'imports'))


def utc_text(value):
    return value.isoformat(timespec='microseconds')


def literal_search(query):
    return '%' + query.upper().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


class UniverseStore:
    def __init__(self, engine):
        self.engine = engine

    def claim(self, key, provider, now):
        """One import per provider; interrupted requests may resume after the lease."""
        stamp = utc_text(now)
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            prior = c.execute(select(IMPORTS).where(IMPORTS.c.id == key)).mappings().first()
            if prior and prior['provider'] != provider:
                raise ValueError('IDEMPOTENCY_CONFLICT')
            if prior and prior['state'] != 'RUNNING':
                return False, self.public_import(prior)
            active = list(c.execute(select(IMPORTS).where(IMPORTS.c.provider == provider,
                                                         IMPORTS.c.state == 'RUNNING')).mappings())
            for row in active:
                if datetime.fromisoformat(row['started_at']) + timedelta(minutes=3) > now:
                    return False, self.public_import(row)
                c.execute(update(IMPORTS).where(IMPORTS.c.id == row['id']).values(
                    state='INTERRUPTED', finished_at=stamp, payload={'reason': 'Importación interrumpida; puede repetirse.'}))
            values = dict(provider=provider, state='RUNNING', started_at=stamp, finished_at=None, payload={})
            if prior:
                c.execute(update(IMPORTS).where(IMPORTS.c.id == key).values(**values))
            else:
                c.execute(insert(IMPORTS).values(id=key, **values))
            return True, {'id': key, **values}

    @staticmethod
    def public_import(row):
        return {k: row[k] for k in ('id', 'provider', 'state', 'started_at', 'finished_at')} | dict(row['payload'])

    def finish(self, key, state, now, **payload):
        with self.engine.begin() as c:
            c.execute(update(IMPORTS).where(IMPORTS.c.id == key, IMPORTS.c.state == 'RUNNING')
                      .values(state=state, finished_at=utc_text(now), payload=payload))
        return self.get_import(key)

    def get_import(self, key):
        with self.engine.connect() as c:
            row = c.execute(select(IMPORTS).where(IMPORTS.c.id == key)).mappings().first()
            if not row:
                raise KeyError(key)
            return self.public_import(row)

    def apply_snapshot(self, key, provider, rows, source, payload_hash, received, connection=None):
        stamp = utc_text(received)
        if not rows or any(row.provider != provider for row in rows):
            raise ValueError('INVALID_CATALOGUE_SNAPSHOT')
        groups = defaultdict(set)
        for row in rows:
            groups[(row.symbol, row.venue)].add(row.provider_key)
        conflicts = {alias for alias, ids in groups.items() if len(ids) > 1}
        with (nullcontext(connection) if connection is not None else self.engine.begin()) as c:
            if connection is None:
                c.exec_driver_sql('BEGIN IMMEDIATE')
            job = c.execute(select(IMPORTS).where(IMPORTS.c.id == key)).mappings().one()
            if job['state'] != 'RUNNING' or job['provider'] != provider:
                raise ValueError('IMPORT_LEASE_LOST')
            old = {r['id']: dict(r) for r in c.execute(select(LISTINGS).where(LISTINGS.c.provider == provider)).mappings()}
            if any(r['last_seen_at'] > stamp for r in old.values()):
                raise ValueError('CATALOGUE_CLOCK_REVERSED')
            known_entities = {r['cik']: dict(r) for r in c.execute(select(ENTITIES)).mappings()}
            entities = {}
            for row in rows:
                if row.cik:
                    entities.setdefault(row.cik, row.name)
            for cik, name in entities.items():
                if cik not in known_entities:
                    c.execute(insert(ENTITIES).values(cik=cik, name=name, first_seen_at=stamp, last_seen_at=stamp))
                else:
                    c.execute(update(ENTITIES).where(ENTITIES.c.cik == cik).values(name=name, last_seen_at=stamp))
            incoming, changed, created = set(), 0, 0
            for row in rows:
                ident = fingerprint([provider, row.provider_key])
                incoming.add(ident)
                state = 'CONFLICT' if (row.symbol, row.venue) in conflicts else 'INCOMPLETE' if row.venue == 'UNKNOWN' else 'IDENTIFIED'
                payload = row.model_dump(mode='json')
                data = dict(provider=provider, provider_key=row.provider_key, cik=row.cik,
                            name=row.name, symbol=row.symbol, venue=row.venue, state=state, payload=payload)
                prior = old.get(ident)
                if not prior:
                    c.execute(insert(LISTINGS).values(id=ident, first_seen_at=stamp, last_seen_at=stamp, **data))
                    created += 1
                else:
                    c.execute(update(LISTINGS).where(LISTINGS.c.id == ident).values(last_seen_at=stamp, **data))
                if not prior or prior['payload'] != payload or prior['state'] != state:
                    self._version(c, ident, stamp, {**payload, 'state': state}, payload_hash, source, key)
                    changed += 1
            missing = set(old) - incoming
            for ident in missing:
                if old[ident]['state'] == 'NOT_OBSERVED':
                    continue
                c.execute(update(LISTINGS).where(LISTINGS.c.id == ident).values(state='NOT_OBSERVED'))
                self._version(c, ident, stamp, {**old[ident]['payload'], 'state': 'NOT_OBSERVED'}, payload_hash, source, key)
                changed += 1
            result = dict(source=source, payload_hash=payload_hash, received_at=stamp,
                          listings=len(rows), entities=len(entities), created=created, changed=changed,
                          conflicts=len(conflicts), not_observed=len(missing),
                          reason='Catálogo registrado; no acredita precios, históricos ni elegibilidad de inversión.')
            c.execute(update(IMPORTS).where(IMPORTS.c.id == key).values(state='SUCCEEDED', finished_at=stamp, payload=result))
        return {'id': key, 'state': 'SUCCEEDED', **result} if connection is not None else self.get_import(key)

    @staticmethod
    def _version(c, ident, stamp, payload, payload_hash, source, key):
        c.execute(update(VERSIONS).where(VERSIONS.c.listing_id == ident, VERSIONS.c.known_until.is_(None)).values(known_until=stamp))
        c.execute(insert(VERSIONS).values(id=fingerprint([key, ident, stamp]), listing_id=ident,
                  known_from=stamp, known_until=None, payload=payload, payload_hash=payload_hash, source=source))

    def search(self, query='', provider=None, state=None, offset=0, limit=50):
        statement = select(LISTINGS)
        if query.strip():
            needle = literal_search(query.strip())
            statement = statement.where(or_(*(func.upper(col).like(needle, escape='\\') for col in
                                         (LISTINGS.c.name, LISTINGS.c.symbol, LISTINGS.c.cik, LISTINGS.c.provider_key))))
        if provider:
            statement = statement.where(LISTINGS.c.provider == provider)
        if state:
            statement = statement.where(LISTINGS.c.state == state)
        with self.engine.connect() as c:
            total = c.execute(select(func.count()).select_from(statement.subquery())).scalar_one()
            rows = c.execute(statement.order_by(LISTINGS.c.symbol, LISTINGS.c.id).offset(offset).limit(limit)).mappings()
            items = [self.public_listing(row) for row in rows]
        return dict(items=items, total=total, offset=offset, limit=limit)

    @staticmethod
    def public_listing(row):
        return {k: row[k] for k in ('id', 'provider', 'cik', 'name', 'symbol', 'venue', 'state', 'first_seen_at', 'last_seen_at')} | {
            'currency': row['payload'].get('currency'), 'category': row['payload']['category']}

    def detail(self, ident, as_of=None):
        with self.engine.connect() as c:
            row = c.execute(select(LISTINGS).where(LISTINGS.c.id == ident)).mappings().first()
            if not row:
                raise KeyError(ident)
            query = select(VERSIONS).where(VERSIONS.c.listing_id == ident)
            if as_of is not None:
                stamp = utc_text(as_of.astimezone(timezone.utc))
                query = query.where(VERSIONS.c.known_from <= stamp)
            versions = [dict(v) for v in c.execute(query.order_by(VERSIONS.c.known_from.desc(), VERSIONS.c.id).limit(100)).mappings()]
            if not versions:
                raise KeyError(ident)
            public = self.public_listing(row)
            if as_of is not None:
                # A past view must not disclose current name/state or future interval closure.
                public.update({k: versions[0]['payload'].get(k) for k in ('name', 'symbol', 'venue', 'cik', 'currency', 'category', 'state')})
                public['last_seen_at'] = versions[0]['known_from']
                versions = [{**v, 'known_until': v['known_until'] if v['known_until'] and v['known_until'] <= stamp else None} for v in versions]
            return {**public, 'versions': versions, 'as_of': as_of.isoformat() if as_of else None,
                    'readiness': [dict(use=use, state='BLOCKED', reason=reason) for use, reason in (
                        ('RESEARCH', 'Falta vincular el instrumento con datos de mercado; las cuentas se evalúan por emisor.'),
                        ('BACKTEST', 'Faltan precios, universo histórico y acciones corporativas verificadas.'),
                        ('PAPER', 'Faltan datos de mercado, riesgo y conciliación. Órdenes deshabilitadas.'))]}

    def summary(self):
        with self.engine.connect() as c:
            counts = {name: c.execute(select(func.count()).select_from(table)).scalar_one() for name, table in
                      (('entities', ENTITIES), ('listings', LISTINGS), ('versions', VERSIONS))}
            counts['conflicts'] = c.execute(select(func.count()).select_from(LISTINGS).where(LISTINGS.c.state == 'CONFLICT')).scalar_one()
            counts['current_listings'] = c.execute(select(func.count()).select_from(LISTINGS).where(LISTINGS.c.state != 'NOT_OBSERVED')).scalar_one()
            imports = [self.public_import(row) for row in c.execute(select(IMPORTS).order_by(IMPORTS.c.started_at.desc()).limit(10)).mappings()]
        return {'counts': counts, 'imports': imports, 'temporal_scope': 'LOCAL_KNOWLEDGE_ONLY'}

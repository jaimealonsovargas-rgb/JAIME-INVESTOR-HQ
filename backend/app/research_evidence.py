"""Explicit P2 evidence bridge; no arbitrary URLs, instruments or invented OHLC."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import DataRecord, InstrumentAlias
from app.data_catalog import CATALOG
from app.data_contracts import DataResult
from app.data_service import cache_key
from app.research_contracts import digest, utc, sanitize


def collect(data, case, refresh=False):
    with Session(data.engine) as s:
        aliases = list(s.scalars(select(InstrumentAlias).where(InstrumentAlias.instrument_id == case['instrument']['id'])))
    identifiers = {(a.provider, a.symbol) for a in aliases}
    sources = {key for key, source in CATALOG.items() if any(provider == source.provider for provider, symbol in identifiers)}
    # Macro reference and already audited public RSS are supplementary, not instrument news.
    sources |= {'A01', 'A20'}
    if refresh:
        for access in sorted(sources):
            source = CATALOG[access]
            if not source.credentials and all((source.rights.access_allowed, source.rights.display_allowed, source.rights.storage_allowed, source.rights.redistribution_allowed)):
                data.query(access)  # P2 retains quota, caching, exact host/path and HTTP policy.
    evidence = []
    with Session(data.engine) as s:
        for access in sorted(sources):
            source = CATALOG[access]
            if data.initial(source).state != 'NOT_VERIFIED' or not all((source.rights.access_allowed, source.rights.display_allowed, source.rights.storage_allowed, source.rights.redistribution_allowed)):
                continue
            row = s.get(DataRecord, cache_key(source))
            if not row:
                continue
            result = DataResult.model_validate(row.payload)
            if not result.real_connection:
                continue
            for obs in result.observations:
                if not all((obs.rights.access_allowed, obs.rights.display_allowed, obs.rights.storage_allowed, obs.rights.redistribution_allowed)):
                    continue
                direct = (obs.provider, obs.series_id) in identifiers or (obs.provider, obs.series_id) == (case['instrument'].get('provider'), case['instrument']['symbol'])
                if not direct and access not in ('A01', 'A20'):
                    continue
                content = obs.model_dump(mode='json')
                content['metadata'] = {k: sanitize(v) for k, v in content['metadata'].items()}
                content['excerpt'] = (f"{obs.series_id}: {obs.value} {obs.unit}; período {obs.period}." if obs.value is not None else sanitize(obs.metadata.get('title', obs.series_id)))
                item = {'case_id': case['id'], 'provider': obs.provider, 'source': obs.feed, 'url': obs.source_ref,
                        'retrieved_at': obs.received_at.isoformat(), 'observed_at': obs.observed_at.isoformat(), 'rights': obs.rights.model_dump(mode='json'),
                        'rights_ok': True, 'freshness': 'STALE' if obs.stale(datetime.now(timezone.utc)) else 'FRESH', 'trust_class': 'UNTRUSTED_CONTENT',
                        'content': content, 'hash': digest(content), 'provenance': obs.payload_hash, 'scope': 'INSTRUMENT' if direct else 'MACRO_CONTEXT' if access == 'A01' else 'GENERAL_NEWS', 'available': True}
                item['id'] = digest(item)
                evidence.append(item)
    return evidence[:60]


def features(evidence):
    """No annualization or mixing units/venues; deterministic Decimal observations."""
    groups = {}
    for e in evidence:
        c = e['content']
        if e['scope'] == 'INSTRUMENT' and c.get('value') is not None and e['rights_ok']:
            groups.setdefault((e['provider'], c['feed'], c['series_id'], c['unit'], c['venue']), []).append(e)
    if not groups:
        return {'state': 'NO_DATA', 'reason': 'No hay serie comparable del instrumento.', 'items': []}
    rows = max(groups.values(), key=len)
    rows = sorted({e['observed_at']: e for e in rows}.values(), key=lambda e: e['observed_at'])
    if len(rows) < 3:
        return {'state': 'NO_DATA', 'reason': 'Muestra insuficiente; no se inventa historia.', 'items': []}
    with localcontext() as ctx:
        ctx.prec = 40
        values = [Decimal(e['content']['value']) for e in rows]
        if any(v <= 0 for v in values):
            return {'state': 'NO_DATA', 'reason': 'Serie no positiva; ratios no aplicables.', 'items': []}
        changes = [b/a-1 for a, b in zip(values, values[1:])]
        mean = sum(values)/len(values); avg = sum(changes)/len(changes)
        sd = (sum((x-avg)**2 for x in changes)/(len(changes)-1)).sqrt()
        level_sd = (sum((x-mean)**2 for x in values)/(len(values)-1)).sqrt()
        metrics = {'period_return': values[-1]/values[0]-1, 'mean_level': mean, 'sample_volatility': sd,
                   'last_change': changes[-1], 'range': max(values)-min(values), 'min_level': min(values), 'max_level': max(values),
                   'z_score': (values[-1]-mean)/level_sd if level_sd else Decimal(0)}
        return {'state': 'STALE' if any(e['freshness'] != 'FRESH' for e in rows) else 'AVAILABLE', 'frequency': 'observed intervals; not annualized',
                'sample_size': len(rows), 'items': [{'name': k, 'value': str(v), 'evidence_ids': [e['id'] for e in rows]} for k, v in metrics.items()],
                'method_version': 'hq.descriptive.1', 'input_hash': digest([e['hash'] for e in rows])}


def current_evidence(data, items):
    """Immutable snapshot + current usability; stale/deleted/restricted evidence degrades claims."""
    checked = []
    with Session(data.engine) as session:
        for e in items:
            item = {**e}; content = e['content']; source = CATALOG.get(content.get('access_id'))
            row = session.get(DataRecord, cache_key(source)) if source else None
            allowed = bool(source and all((source.rights.access_allowed, source.rights.display_allowed, source.rights.storage_allowed, source.rights.redistribution_allowed)))
            item['rights_ok'] = allowed
            item['available'] = bool(row) and digest(content) == e['hash']
            received = datetime.fromisoformat(e['retrieved_at'])
            item['freshness'] = 'FRESH' if (datetime.now(timezone.utc)-received).total_seconds() <= content.get('stale_after_seconds', 0) else 'STALE'
            if not allowed:
                item['content'] = {'excerpt': 'RIGHTS_RESTRICTED'}
            checked.append(item)
    return checked

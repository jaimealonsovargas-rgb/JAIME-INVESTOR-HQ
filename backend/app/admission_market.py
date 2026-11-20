"""Read-only Alpaca archive adapter; this supplies observations, never usage rights.

The universe hash describes the current catalogue, selected ex post, not a PIT universe.
Session dates are extracted in New York time; they are not calendar evidence.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.data_identity import fingerprint
from app.dataset_assessment import verified_history
from app.market_store import JOBS, RECEIPTS, BARS
from app.universe_store import LISTINGS, utc_text


def load_market_candidate(service, listing_id, cutoff):
    """Load the latest known request without falling back to a more convenient job."""
    if (not isinstance(cutoff, datetime) or cutoff.utcoffset() is None
            or cutoff > service.data.clock()):
        raise ValueError('INVALID_KNOWLEDGE_CUTOFF')
    cutoff = cutoff.astimezone(timezone.utc)
    stamp = utc_text(cutoff)
    errors = []
    with service.data.engine.connect() as connection:
        connection.exec_driver_sql('BEGIN')
        target = connection.execute(select(LISTINGS).where(LISTINGS.c.id == listing_id)).mappings().first()
        if target is None:
            raise KeyError(listing_id)
        catalogue = [dict(row) for row in connection.execute(select(LISTINGS).where(
            LISTINGS.c.provider == 'ALPACA').order_by(LISTINGS.c.id)).mappings()]
        jobs = connection.execute(select(JOBS).where(JOBS.c.listing_id == listing_id,
            JOBS.c.kind == 'history', JOBS.c.created_at <= stamp).order_by(
                JOBS.c.created_at.desc(), JOBS.c.id.desc()).limit(1)).mappings()
        job = next((dict(row) for row in jobs), None)
        receipts, rows = [], []
        if job:
            # Include late receipts so a partially visible job cannot pass by truncation.
            receipts = [dict(row) for row in connection.execute(select(RECEIPTS).where(
                RECEIPTS.c.job_id == job['id']).order_by(RECEIPTS.c.received_at,
                RECEIPTS.c.id).limit(38)).mappings()]
            rows = list(connection.scalars(select(BARS.c.payload).where(
                BARS.c.job_id == job['id']).order_by(BARS.c.timestamp).limit(5001)))
    req = job['request'] if job else {}
    candidate = dict(version='admission-candidate-v1', domain='MARKET_DATA', provider='ALPACA',
        listing_id=listing_id, identity_hash=fingerprint(target['payload']), symbol=target['symbol'],
        venue=target['venue'], currency=target['payload'].get('currency'),
        start=req.get('start', cutoff.date().isoformat()), end=req.get('end', cutoff.date().isoformat()),
        frequency='1 day', adjustment=req.get('adjustment', 'raw'), feed='iex', unit='PRICE_PER_SHARE',
        universe_hash=fingerprint(catalogue), bars=[], sources=[], source_errors=errors, cutoff=stamp)
    if service.access() == 'DISABLED':
        errors.append('SOURCE_DISABLED')
    if target['provider'] != 'ALPACA':
        errors.append('ALPACA_IDENTITY_REQUIRED')
    if not job:
        errors.append('NO_HISTORY')
        return candidate
    if job['updated_at'] > stamp or any(r['received_at'] > stamp for r in receipts):
        errors.append('HISTORY_AFTER_CUTOFF')
    candidate['sources'] = [dict(id=r['id'], hash=r['payload_hash'], received_at=r['received_at'])
        for r in receipts if r['received_at'] <= stamp]
    if len(rows) > 5000 or len(receipts) > 37:
        errors.append('DIAGNOSTIC_LIMIT')
    if job['state'] != 'SUCCEEDED' or not all(job['progress'].get(k + '_complete')
            for k in ('bars', 'calendar', 'corporate_actions')):
        errors.append('IMPORT_INCOMPLETE')
    if (req.get('identity_hash') != candidate['identity_hash'] or req.get('listing_id') != listing_id
            or req.get('symbol') != target['symbol'] or req.get('asset_id') != target['provider_key']):
        errors.append('DATASET_IDENTITY_MISMATCH')
    if 'DIAGNOSTIC_LIMIT' not in errors:
        try:
            verified_history(job, receipts, rows, service.raw_root)
        except (OSError, EOFError, ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
            # Preserve stable validator codes, never filesystem paths or raw provider content.
            code = str(exc)
            errors.append(code if code.isupper() and code.replace('_', '').isalnum()
                else 'ORIGINAL_INTEGRITY_FAILED')
    if errors:
        return candidate
    try:
        for row in rows:
            when = datetime.fromisoformat(row['timestamp'])
            if when.utcoffset() is None or when > cutoff:
                raise ValueError('BAR_AFTER_CUTOFF_OR_NAIVE')
            candidate['bars'].append(dict(session=when.astimezone(ZoneInfo('America/New_York')).date().isoformat(),
                **{key: str(row[key]) for key in ('open', 'high', 'low', 'close', 'volume')}))
    except (KeyError, ValueError, TypeError):
        candidate['bars'] = []
        errors.append('BAR_TIMESTAMP_INVALID')
    return candidate

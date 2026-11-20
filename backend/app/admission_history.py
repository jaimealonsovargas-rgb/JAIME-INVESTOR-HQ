"""Read-only, cutoff-aware bridge from D2 snapshots to admission candidates."""
from datetime import datetime, timezone
import json
from sqlalchemy import select
from app.data_identity import fingerprint
from app.history_contracts import BatchRequest
from app.history_store import BATCHES, UNITS, SNAPSHOTS


def cutoff_text(cutoff):
    if not isinstance(cutoff, datetime) or cutoff.utcoffset() is None:
        raise ValueError('AWARE_CUTOFF_REQUIRED')
    if cutoff > datetime.now(timezone.utc):
        raise ValueError('FUTURE_CUTOFF')
    return cutoff.astimezone(timezone.utc).isoformat()


def load_history_candidate(engine, batch_id, listing_id, cutoff):
    stamp = cutoff_text(cutoff)
    errors, bars, sources, feeds = set(), [], [], set()
    with engine.connect() as c:
        c.exec_driver_sql('BEGIN')
        batch = c.execute(select(BATCHES).where(BATCHES.c.id == batch_id)).mappings().one()
        body = BatchRequest.model_validate(batch['request'])
        target = next((t for t in body.targets if t.listing_id == listing_id), None)
        if target is None:
            raise KeyError('LISTING_NOT_IN_BATCH')
        if fingerprint(batch['request']) != batch['request_hash']:
            errors.add('BATCH_HASH_MISMATCH')
        if datetime.fromisoformat(batch['created_at']) > cutoff:
            errors.add('BATCH_AFTER_CUTOFF')
        if batch['state'] != 'ACTIVE':
            errors.add('BATCH_NOT_ACTIVE')
        expected = [r for r in body.units() if r['listing_id'] == listing_id]
        sequence_start = next(i for i, t in enumerate(body.targets) if t.listing_id == listing_id) * len(expected)
        units = c.execute(select(UNITS).where(UNITS.c.batch_id == batch_id,
            UNITS.c.request['listing_id'].as_string() == listing_id).order_by(UNITS.c.sequence).limit(121)).mappings().all()
        if len(units) != len(expected):
            errors.add('WINDOW_COUNT_MISMATCH')
        for index, unit in enumerate(units):
            if index >= len(expected):
                errors.add('UNEXPECTED_WINDOW')
                continue
            request = expected[index]
            sequence = sequence_start + index
            if unit['sequence'] != sequence or unit['id'] != fingerprint([batch_id, sequence]):
                errors.add('UNIT_IDENTITY_MISMATCH')
            if unit['request'] != request or unit['request_hash'] != fingerprint(request):
                errors.add('UNIT_REQUEST_MISMATCH')
                continue
            if unit['state'] not in ('SUCCEEDED', 'EMPTY') or not unit['snapshot_hash']:
                errors.add('WINDOW_NOT_COMPLETE')
                continue
            try:
                received = datetime.fromisoformat(unit['received_at'])
                updated = datetime.fromisoformat(unit['updated_at'])
                if (received.utcoffset() is None or received > cutoff
                        or updated.utcoffset() is None or updated > cutoff):
                    raise ValueError()
            except (ValueError, TypeError):
                errors.add('RECEIPT_OUTSIDE_CUTOFF')
                continue
            payload = c.execute(select(SNAPSHOTS.c.payload).where(SNAPSHOTS.c.hash == unit['snapshot_hash'])).scalar_one_or_none()
            if payload is None or len(json.dumps(payload)) > 512 * 1024 or fingerprint(payload) != unit['snapshot_hash']:
                errors.add('SNAPSHOT_HASH_MISMATCH')
                continue
            if (payload.get('version') != 'history-normalized-v1'
                    or payload.get('request') != {k: v for k, v in request.items() if k != 'revision'}):
                errors.add('SNAPSHOT_REQUEST_MISMATCH')
                continue
            allowed = {'SYNTHETIC_TEST'} if body.provider == 'SYNTHETIC_TEST' else {'DELAYED_HISTORY_ADVISORY_2188', 'HISTORICAL_UNCONFIRMED'}
            if payload.get('feed') not in allowed:
                errors.add('FEED_MISMATCH')
                continue
            rows = payload.get('bars')
            if not isinstance(rows, list) or len(rows) > 64:
                errors.add('SNAPSHOT_ROWS_INVALID')
                continue
            if any(not isinstance(r, dict) or not isinstance(r.get('session'), str)
                   or not request['start'] <= r['session'] <= request['end'] for r in rows):
                errors.add('ROW_OUTSIDE_WINDOW')
            if (unit['state'] == 'EMPTY') != (not rows):
                errors.add('STATE_ROWS_MISMATCH')
            sources.append(dict(id=unit['id'], hash=unit['snapshot_hash'], received_at=received.astimezone(timezone.utc).isoformat()))
            feeds.add(payload['feed'])
            bars.extend(rows)
        if len(feeds) > 1:
            errors.add('MIXED_FEEDS')
    contract = target.contract
    return dict(version='admission-candidate-v1',
        domain='SYNTHETIC_TEST' if body.provider == 'SYNTHETIC_TEST' else 'MARKET_DATA', provider=body.provider,
        listing_id=listing_id, identity_hash=target.identity_hash, symbol=contract.symbol,
        venue=contract.primaryExchange, currency=contract.currency, start=body.start.isoformat(), end=body.end.isoformat(),
        frequency=body.frequency, adjustment=body.adjustment, feed=next(iter(feeds)) if len(feeds) == 1 else 'UNCONFIRMED',
        unit='PRICE_PER_SHARE', universe_hash=fingerprint([t.model_dump(mode='json') for t in body.targets]),
        bars=bars, sources=sources, source_errors=sorted(errors), cutoff=stamp)


def batch_targets(engine, batch_id, *, offset=0, limit=20):
    if not 0 <= offset <= 5000 or not 1 <= limit <= 100:
        raise ValueError('INVALID_PAGE')
    with engine.connect() as c:
        request = c.scalar(select(BATCHES.c.request).where(BATCHES.c.id == batch_id))
    if request is None:
        raise KeyError('UNKNOWN_BATCH')
    body = BatchRequest.model_validate(request)
    return [t.listing_id for t in body.targets[offset:offset+limit]], len(body.targets)

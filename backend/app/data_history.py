"""Persistent P2 history. Readers recheck current configuration and rights."""
from sqlalchemy import select
from app.database import DataObservation, DataRecord
from app.data_contracts import DataResult, Observation


def archive(session, source, identity, observations):
    if not all((source.rights.access_allowed, source.rights.storage_allowed, source.rights.display_allowed)):
        return
    for obs in observations:
        if not all((obs.rights.access_allowed, obs.rights.storage_allowed, obs.rights.display_allowed)):
            continue
        row = session.get(DataObservation, obs.id)
        if row is None:
            session.add(DataObservation(id=obs.id, access_id=source.id, source_identity=identity,
                observed_at=obs.observed_at.isoformat(), received_at=obs.received_at.isoformat(),
                payload=obs.model_dump(mode='json')))
        elif obs.received_at.isoformat() > row.received_at:
            # A fresh retrieval may reconfirm the same payload, not a new market timestamp.
            row.received_at = obs.received_at.isoformat()
            row.payload = obs.model_dump(mode='json')


def read_source(session, data, source, *, limit=500):
    from app.data_service import cache_key
    if data.initial(source).state != 'NOT_VERIFIED' or not all((
        source.rights.access_allowed, source.rights.display_allowed, source.rights.storage_allowed,
        source.rights.redistribution_allowed)):
        return []
    key = cache_key(source)
    latest = session.get(DataRecord, 'status:' + source.id)
    if latest and latest.payload.get('http_status') in (403, 404, 410):
        return []
    rows = session.scalars(select(DataObservation).where(
        DataObservation.access_id == source.id, DataObservation.source_identity == key
    ).order_by(DataObservation.observed_at.desc(), DataObservation.received_at.desc()).limit(limit))
    observations = {row.id: Observation.model_validate(row.payload) for row in rows}
    # Existing verified caches remain readable without retroactively calling them archived.
    cached = session.get(DataRecord, key)
    if cached:
        result = DataResult.model_validate(cached.payload)
        if result.real_connection:
            for obs in result.observations:
                old = observations.get(obs.id)
                if old is None or obs.received_at > old.received_at:
                    observations[obs.id] = obs
    return sorted((o for o in observations.values() if all((
        o.rights.access_allowed, o.rights.display_allowed, o.rights.storage_allowed,
        o.rights.redistribution_allowed))), key=lambda o: (o.observed_at, o.received_at), reverse=True)[:limit]

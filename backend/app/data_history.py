"""Immutable revisions + receipts; local as-of, current rights, semantic windows."""
from datetime import datetime
from sqlalchemy import select
from app.database import DataObservation, DataRecord, DataDownload
from app.data_contracts import DataResult, Observation
from app.data_identity import fingerprint, observation_key, publication_bound
from app.data_rights import readable


def archive(session, source, identity, observations):
    if not all((source.rights.access_allowed, source.rights.storage_allowed, source.rights.display_allowed)):
        return
    batches = {}
    for obs in observations:
        if not all((obs.rights.access_allowed, obs.rights.storage_allowed, obs.rights.display_allowed)):
            continue
        if session.get(DataObservation, obs.id) is None:
            session.add(DataObservation(id=obs.id, access_id=source.id, source_identity=identity,
                observed_at=obs.observed_at.isoformat(), received_at=obs.received_at.isoformat(),
                payload=obs.model_dump(mode='json')))
        batches.setdefault((obs.received_at.isoformat(), obs.payload_hash), set()).add(obs.id)
    for (received, payload_hash), ids in batches.items():
        ident = fingerprint([identity, received, payload_hash, sorted(ids)])
        if session.get(DataDownload, ident) is None:
            session.add(DataDownload(id=ident, source_identity=identity, received_at=received,
                payload_hash=payload_hash, observation_ids=sorted(ids)))


def read_source(session, data, source, *, limit=500, local_research=False, as_of=None, revisions=False):
    """as_of = known locally by this instant; not reconstructed market PIT.

    Deduplicate before limiting. Legacy IDs remain intact in storage.
    """
    from app.data_service import cache_key
    if limit <= 0:
        return []
    if as_of is not None and as_of.utcoffset() is None:
        raise ValueError('as_of requiere zona horaria.')
    if data.initial(source).state != 'NOT_VERIFIED' or not readable(source.rights, local_research=local_research):
        return []
    key = cache_key(source)
    latest = session.get(DataRecord, 'status:' + source.id)
    if latest and latest.payload.get('http_status') in (403, 404, 410):
        return []
    receipts = {}
    for receipt in session.scalars(select(DataDownload).where(DataDownload.source_identity == key)):
        when = datetime.fromisoformat(receipt.received_at)
        if as_of is not None and when > as_of:
            continue
        for ident in receipt.observation_ids:
            if ident not in receipts or when > receipts[ident][0]:
                receipts[ident] = (when, receipt.payload_hash)
    observations = []
    for row in session.scalars(select(DataObservation).where(
            DataObservation.access_id == source.id, DataObservation.source_identity == key)):
        obs = Observation.model_validate(row.payload)
        if as_of is not None and obs.received_at > as_of:
            continue
        if obs.id in receipts:
            received, payload_hash = receipts[obs.id]
            obs = obs.model_copy(update={'received_at': received, 'payload_hash': payload_hash})
        observations.append(obs)
    cached = session.get(DataRecord, key)
    if cached:
        result = DataResult.model_validate(cached.payload)
        if result.real_connection:
            observations.extend(result.observations)
    selected = {}
    for obs in observations:
        published = publication_bound(obs)
        if not readable(obs.rights, local_research=local_research):
            continue
        if as_of is not None and (obs.received_at > as_of or (published and published > as_of)):
            continue
        identity = obs.id if revisions else observation_key(obs)
        # An old filing fetched later cannot supersede a restatement.
        rank = (published or obs.received_at, obs.received_at, obs.id)
        old = selected.get(identity)
        if old is None or rank > old[0]:
            selected[identity] = (rank, obs)
    return sorted((item[1] for item in selected.values()),
                  key=lambda o: (o.observed_at, o.received_at, o.id), reverse=True)[:limit]

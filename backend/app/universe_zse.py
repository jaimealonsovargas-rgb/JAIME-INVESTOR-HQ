"""Project official HT history into its own searchable listing and local detail."""
from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session
from app import zse
from app.data_catalog import CATALOG
from app.data_history import read_source
from app.data_identity import fingerprint
from app.universe_store import LISTINGS, UniverseStore, utc_text


def register_listing(session, observation):
    key = observation.metadata['isin']
    ident = fingerprint(['ZSE', key])
    stamp = utc_text(observation.received_at)
    payload = dict(provider='ZSE', provider_key=key, cik=None, name=zse.NAME, symbol=zse.SYMBOL,
                   venue=zse.MIC, currency='EUR', category='EU_EQUITY', isin=key, state='IDENTIFIED')
    table_fields = {k: payload[k] for k in ('provider','provider_key','cik','name','symbol','venue','state')}
    c = session.connection()
    prior = c.execute(select(LISTINGS.c.payload).where(LISTINGS.c.id == ident)).scalar_one_or_none()
    if prior is None:
        c.execute(insert(LISTINGS).values(id=ident, first_seen_at=stamp, last_seen_at=stamp,
                                          payload=payload, **table_fields))
    else:
        c.execute(update(LISTINGS).where(LISTINGS.c.id == ident).values(
            last_seen_at=stamp, payload=payload, **table_fields))
    if prior != payload:
        UniverseStore._version(c, ident, stamp, payload, observation.payload_hash, zse.IDENTITY, observation.id)


def close_detail(data, listing, as_of):
    source = CATALOG['A22']
    expected = fingerprint(['ZSE', zse.ISIN])
    if (listing['id'],listing['symbol'],listing['venue'],listing['currency']) != (expected,zse.SYMBOL,zse.MIC,'EUR'):
        return None
    with Session(data.engine) as session:
        observations = read_source(session, data, source, limit=1, local_research=True, as_of=as_of)
    if not observations:
        return None
    obs = observations[0]
    if (obs.metadata.get('isin'),obs.venue,obs.currency,obs.unit) != (zse.ISIN,zse.MIC,'EUR','EUR/share'):
        return None
    return dict(price=format(obs.value,'f'),currency=obs.currency,isin=zse.ISIN,session=obs.period,
                received_at=obs.received_at.isoformat(),stale=obs.stale(as_of or data.clock()),
                source=zse.IDENTITY, observation_id=obs.id, payload_hash=obs.payload_hash)

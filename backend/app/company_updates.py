"""One durable event per changed SEC payload, drained by the existing SEC worker."""
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from app.database import Base
from app.data_identity import fingerprint
from app.universe_store import utc_text

EVENTS = Base.metadata.tables['company_update_events']
MODELS = Base.metadata.tables['company_models']


def enqueue_update(c, cik, snapshot_id, payload_hash, received_at):
    prior = c.execute(select(MODELS.c.payload).where(MODELS.c.cik == cik)
                      .order_by(MODELS.c.version.desc()).limit(1)).scalar()
    if not prior or prior['source']['payload_hash'] == payload_hash:
        return
    ident = fingerprint(['sec-company-update-v1', cik, payload_hash])
    c.execute(insert(EVENTS).values(id=ident, cik=cik, snapshot_id=snapshot_id,
        received_at=received_at, state='PENDING').on_conflict_do_nothing())


def process_update(sec):
    from app.company_service import CompanyService
    with sec.data.engine.connect() as c:
        event = c.execute(select(EVENTS).where(EVENTS.c.state == 'PENDING')
                          .order_by(EVENTS.c.received_at, EVENTS.c.id).limit(1)).mappings().first()
    if not event:
        return False
    try:
        model = CompanyService(sec).build(event['cik'], 'sec-event-'+event['id'],
            datetime.fromisoformat(event['received_at']), snapshot_id=event['snapshot_id'])
        result = dict(state='SUCCEEDED', model_id=model['id'], reason=model['payload']['update']['reason'])
    except (ValueError, PermissionError) as error:
        known = {'OLDER_FINANCIAL_REPORT','NO_ANNUAL_ACCOUNTS','NO_FINANCIAL_DATA','AMBIGUOUS_CURRENCY',
                 'MODEL_STORAGE_LIMIT','ORIGINAL_UNAVAILABLE','ORIGINAL_INTEGRITY_FAILED','SOURCE_UNAVAILABLE'}
        result = dict(state='BLOCKED', reason=str(error) if str(error) in known else 'MODEL_UPDATE_REJECTED')
    with sec.data.engine.begin() as c:
        c.execute(update(EVENTS).where(EVENTS.c.id == event['id'], EVENTS.c.state == 'PENDING')
                  .values(**result, completed_at=utc_text(sec.data.clock())))
    return True

"""Serialized append transaction, hash chain and derived postings verification."""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import text
from app.portfolio_domain import PortfolioEvent, rebuild

SEED_REF = 'MASTER:DEPOSIT_VIRTUAL:v1'
GENESIS = '0' * 64


class JournalIntegrityError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def read_journal(connection, portfolio='MASTER'):
    rows = connection.execute(text('SELECT * FROM ledger_events WHERE portfolio_id=:p ORDER BY sequence'), {'p': portfolio}).mappings().all()
    events, previous = [], GENESIS
    for row in rows:
        if row['previous_hash'] != previous or row['hash'] != digest(previous + row['payload']):
            raise JournalIntegrityError('Journal hash chain integrity failure.')
        event = PortfolioEvent.model_validate_json(row['payload'])
        if event.source_ref != row['source_ref'] or event.occurred_at.isoformat() != row['occurred_at']:
            raise JournalIntegrityError('Journal envelope integrity failure.')
        events.append(event)
        previous = row['hash']
    state = rebuild(events)
    for row, event in zip(rows, events):
        entries = [dict(p) for p in connection.execute(text('SELECT account,currency,debit,credit FROM ledger_entries WHERE event_id=:e ORDER BY id'), {'e': row['sequence']}).mappings()]
        if entries != state.postings[event.source_ref]:
            raise JournalIntegrityError('Journal postings differ from deterministic replay.')
    return events, state, previous


def append_event(engine, event: PortfolioEvent, portfolio='MASTER'):
    """Internal service only. MASTER can receive only its fixed seed during P3."""
    if portfolio == 'MASTER' and (event.kind != 'DEPOSIT_VIRTUAL' or event.source_ref != SEED_REF
            or event.currency != 'EUR' or event.amount != 10000 or event.actor != 'P3_INITIALIZER'):
        raise ValueError('P3 MASTER accepts only the initial virtual deposit.')
    with engine.connect() as connection:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
        try:
            connection.execute(text("INSERT OR IGNORE INTO portfolios(id,base_currency,status) VALUES(:p,'EUR','PAPER_ONLY')"), {'p': portfolio})
            events, _, previous = read_journal(connection, portfolio)
            existing = next((e for e in events if e.source_ref == event.source_ref), None)
            if existing:
                if existing != event:
                    raise ValueError('Idempotency key reused with different event.')
                connection.rollback()
                return False
            state = rebuild([*events, event])
            payload = canonical(event.model_dump(mode='json'))
            cursor = connection.execute(text('INSERT INTO ledger_events(portfolio_id,source_ref,occurred_at,payload,previous_hash,hash) VALUES(:p,:r,:t,:v,:previous,:hash)'),
                dict(p=portfolio, r=event.source_ref, t=event.occurred_at.isoformat(), v=payload, previous=previous, hash=digest(previous+payload)))
            for entry in state.postings[event.source_ref]:
                connection.execute(text('INSERT INTO ledger_entries(event_id,account,currency,debit,credit) VALUES(:id,:account,:currency,:debit,:credit)'), dict(id=cursor.lastrowid, **entry))
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise


def initialize_master(engine):
    # Reuse the stored timestamp on repeat invocation; other content must still match.
    with engine.connect() as connection:
        existing = connection.execute(text('SELECT occurred_at FROM ledger_events WHERE portfolio_id=:p AND source_ref=:r'), dict(p='MASTER', r=SEED_REF)).scalar_one_or_none()
    event = PortfolioEvent(kind='DEPOSIT_VIRTUAL', source_ref=SEED_REF, actor='P3_INITIALIZER',
        occurred_at=existing or datetime.now(timezone.utc), amount='10000.00')
    try:
        return append_event(engine, event)
    except ValueError:
        # Two concurrent initializers may have chosen different timestamps. Verify winner.
        with engine.connect() as connection:
            events, _, _ = read_journal(connection)
        if len(events) == 1 and events[0].model_copy(update={'occurred_at': event.occurred_at}) == event:
            return False
        raise

"""SQLAlchemy metadata mirrors the P3 migration; financial columns are TEXT."""
from sqlalchemy import Table, Column, String, Text, Integer, ForeignKey, UniqueConstraint, Index


def register(metadata):
    Table('portfolios', metadata, Column('id', String(40), primary_key=True), Column('base_currency', String(3), nullable=False), Column('status', String(20), nullable=False))
    events = Table('ledger_events', metadata, Column('sequence', Integer, primary_key=True, autoincrement=True),
        Column('portfolio_id', String(40), ForeignKey('portfolios.id'), nullable=False), Column('source_ref', String(200), nullable=False),
        Column('occurred_at', String(40), nullable=False), Column('payload', Text, nullable=False), Column('previous_hash', String(64), nullable=False),
        Column('hash', String(64), nullable=False), UniqueConstraint('portfolio_id', 'source_ref'))
    Index('ix_ledger_portfolio_time', events.c.portfolio_id, events.c.occurred_at, events.c.sequence)
    entries = Table('ledger_entries', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
        Column('event_id', Integer, ForeignKey('ledger_events.sequence'), nullable=False), Column('account', String(200), nullable=False),
        Column('currency', String(3), nullable=False), Column('debit', Text, nullable=False), Column('credit', Text, nullable=False))
    Index('ix_entries_event', entries.c.event_id)
    snapshots = Table('valuation_snapshots', metadata, Column('id', Integer, primary_key=True, autoincrement=True),
        Column('portfolio_id', String(40), ForeignKey('portfolios.id'), nullable=False), Column('as_of', String(40), nullable=False),
        Column('ledger_hash', String(64), nullable=False), Column('fingerprint', String(64), nullable=False, unique=True), Column('payload', Text, nullable=False))
    Index('ix_snapshots_portfolio_time', snapshots.c.portfolio_id, snapshots.c.as_of)

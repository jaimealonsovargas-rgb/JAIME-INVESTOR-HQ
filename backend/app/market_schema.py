"""Private market evidence, isolated from the MASTER ledger and SEC accounts."""
from sqlalchemy import Table, Column, String, JSON, Integer, ForeignKey, Index


def register(metadata):
    jobs = Table('market_jobs', metadata,
        Column('id', String(128), primary_key=True), Column('request_hash', String(64), nullable=False),
        Column('kind', String(24), nullable=False), Column('listing_id', String(64)),
        Column('state', String(24), nullable=False), Column('created_at', String(40), nullable=False),
        Column('updated_at', String(40), nullable=False), Column('next_at', String(40), nullable=False),
        Column('lease_until', String(40)), Column('token', String(36)),
        Column('attempts', Integer, nullable=False), Column('error', String(64)),
        Column('request', JSON, nullable=False), Column('progress', JSON, nullable=False))
    Index('ix_market_job_queue', jobs.c.state, jobs.c.next_at)
    receipts = Table('market_receipts', metadata,
        Column('id', String(64), primary_key=True), Column('job_id', ForeignKey('market_jobs.id'), nullable=False),
        Column('listing_id', String(64)), Column('kind', String(24), nullable=False),
        Column('received_at', String(40), nullable=False), Column('payload_hash', String(64), nullable=False),
        Column('source', String(500), nullable=False), Column('params', JSON, nullable=False),
        Column('payload', JSON, nullable=False))
    Index('ix_market_receipt_lookup', receipts.c.listing_id, receipts.c.kind, receipts.c.received_at)
    bars = Table('market_bars', metadata,
        Column('job_id', ForeignKey('market_jobs.id'), primary_key=True),
        Column('timestamp', String(40), primary_key=True), Column('payload', JSON, nullable=False))
    Table('market_endpoint_status', metadata,
        Column('id', String(32), primary_key=True), Column('state', String(32), nullable=False),
        Column('checked_at', String(40), nullable=False), Column('reason', String(300), nullable=False))

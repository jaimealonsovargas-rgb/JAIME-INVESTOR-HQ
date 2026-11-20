"""Durable multi-issuer SEC jobs and immutable financial snapshots."""
from alembic import op
import sqlalchemy as sa
revision = '0009_sec_financials'
down_revision = '0008_universe_catalogue'
branch_labels = depends_on = None


def upgrade():
    metadata = sa.MetaData()
    register(metadata)
    metadata.create_all(op.get_bind())


def downgrade():
    names = ('sec_filings', 'sec_facts', 'sec_receipts', 'sec_snapshots', 'sec_tasks', 'sec_jobs')
    for name in names:
        if op.get_bind().execute(sa.text(f'SELECT COUNT(*) FROM {name}')).scalar():
            raise RuntimeError('Evidencia SEC presente: preservar antes de retirar la migración.')
    for name in names:
        op.drop_table(name)


# Frozen schema; never imports the application's future models.
from sqlalchemy import Table, Column, String, JSON, Integer, ForeignKey, Index


def register(metadata):
    Table('sec_jobs', metadata,
          Column('id', String(128), primary_key=True), Column('request_hash', String(64), nullable=False),
          Column('state', String(24), nullable=False), Column('created_at', String(40), nullable=False),
          Column('updated_at', String(40), nullable=False), Column('manifest', JSON, nullable=False))
    tasks = Table('sec_tasks', metadata,
          Column('id', String(64), primary_key=True), Column('job_id', ForeignKey('sec_jobs.id'), nullable=False),
          Column('cik', String(10), nullable=False), Column('kind', String(20), nullable=False),
          Column('ordinal', Integer, nullable=False), Column('state', String(24), nullable=False),
          Column('attempts', Integer, nullable=False), Column('next_at', String(40), nullable=False),
          Column('lease_until', String(40)), Column('token', String(36)), Column('error', String(40)),
          Column('snapshot_id', String(64)))
    Index('ix_sec_task_queue', tasks.c.state, tasks.c.next_at, tasks.c.ordinal)
    Index('ix_sec_task_job', tasks.c.job_id)
    snapshots = Table('sec_snapshots', metadata,
          Column('id', String(64), primary_key=True), Column('cik', String(10), nullable=False),
          Column('kind', String(20), nullable=False), Column('payload_hash', String(64), nullable=False),
          Column('parser_version', String(32), nullable=False), Column('source', String(500), nullable=False),
          Column('first_received_at', String(40), nullable=False), Column('metadata', JSON, nullable=False))
    Index('ix_sec_snapshot_issuer', snapshots.c.cik, snapshots.c.kind)
    receipts = Table('sec_receipts', metadata,
          Column('id', String(64), primary_key=True), Column('task_id', ForeignKey('sec_tasks.id'), nullable=False),
          Column('snapshot_id', ForeignKey('sec_snapshots.id'), nullable=False),
          Column('cik', String(10), nullable=False), Column('kind', String(20), nullable=False),
          Column('received_at', String(40), nullable=False))
    Index('ix_sec_receipt_asof', receipts.c.cik, receipts.c.kind, receipts.c.received_at)
    facts = Table('sec_facts', metadata,
          Column('snapshot_id', ForeignKey('sec_snapshots.id'), primary_key=True),
          Column('id', String(64), primary_key=True), Column('metric', String(50), nullable=False),
          Column('period_end', String(10), nullable=False), Column('filed', String(10), nullable=False),
          Column('payload', JSON, nullable=False))
    Index('ix_sec_facts_snapshot_metric', facts.c.snapshot_id, facts.c.metric, facts.c.period_end)
    filings = Table('sec_filings', metadata,
          Column('snapshot_id', ForeignKey('sec_snapshots.id'), primary_key=True),
          Column('accession', String(24), primary_key=True), Column('filed', String(10), nullable=False),
          Column('form', String(20), nullable=False), Column('payload', JSON, nullable=False))
    Index('ix_sec_filings_date', filings.c.snapshot_id, filings.c.filed)

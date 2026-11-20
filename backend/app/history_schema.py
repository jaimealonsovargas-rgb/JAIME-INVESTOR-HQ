"""Provider-neutral collection queue; no reference to MASTER or quant accounting."""
from sqlalchemy import Table,Column,String,Integer,JSON,ForeignKey,Index,UniqueConstraint


def register(metadata):
    Table('history_batches',metadata,
        Column('id',String(128),primary_key=True),Column('request_hash',String(64),nullable=False),
        Column('request',JSON,nullable=False),Column('rights',JSON,nullable=False),
        Column('state',String(24),nullable=False),Column('reason',String(80),nullable=False),
        Column('created_at',String(40),nullable=False))
    Table('history_snapshots',metadata,
        Column('hash',String(64),primary_key=True),Column('payload',JSON,nullable=False))
    units=Table('history_units',metadata,
        Column('id',String(64),primary_key=True),Column('batch_id',ForeignKey('history_batches.id'),nullable=False),
        Column('sequence',Integer,nullable=False),Column('request_hash',String(64),nullable=False),Column('request',JSON,nullable=False),
        Column('state',String(24),nullable=False),Column('reason',String(80),nullable=False),Column('attempts',Integer,nullable=False),
        Column('next_at',String(40),nullable=False),Column('updated_at',String(40),nullable=False),
        Column('token',String(36)),Column('lease_until',String(40)),
        Column('snapshot_hash',ForeignKey('history_snapshots.hash')),Column('received_at',String(40)),
        Column('cache_until',String(40)),Column('coverage',JSON,nullable=False),
        UniqueConstraint('batch_id','sequence',name='uq_history_batch_sequence'))
    Index('ix_history_queue',units.c.state,units.c.next_at)
    Index('ix_history_cache',units.c.request_hash,units.c.cache_until)
    Table('history_provider_budget',metadata,
        Column('provider',String(32),primary_key=True),Column('next_at',String(40),nullable=False),
        Column('token',String(36)),Column('lease_until',String(40)),Column('unit_id',String(64)),
        Column('window_start',String(40),nullable=False),Column('used',Integer,nullable=False))
    Table('history_events',metadata,
        Column('sequence',Integer,primary_key=True,autoincrement=True),
        Column('unit_id',ForeignKey('history_units.id'),nullable=False),Column('at',String(40),nullable=False),
        Column('state',String(24),nullable=False),Column('reason',String(80),nullable=False),Column('attempt',Integer,nullable=False))

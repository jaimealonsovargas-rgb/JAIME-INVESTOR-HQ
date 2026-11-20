"""Immutable derived accounting models, separate from research and portfolio ledgers."""
from sqlalchemy import Table, Column, String, JSON, Integer, ForeignKey, Index, UniqueConstraint


def register(metadata):
    models = Table('company_models', metadata,
        Column('id', String(64), primary_key=True), Column('cik', String(10), nullable=False),
        Column('version', Integer, nullable=False), Column('created_at', String(40), nullable=False),
        Column('as_of', String(40), nullable=False), Column('previous_id', String(64)),
        Column('input_hash', String(64), nullable=False), Column('payload_hash', String(64), nullable=False),
        Column('payload', JSON, nullable=False), UniqueConstraint('cik', 'version', name='uq_company_version'))
    Index('ix_company_models_issuer', models.c.cik, models.c.version)
    Table('company_model_requests', metadata,
        Column('id', String(128), primary_key=True), Column('request_hash', String(64), nullable=False),
        Column('model_id', ForeignKey('company_models.id'), nullable=False), Column('created_at', String(40), nullable=False))
    Table('company_update_events', metadata,
        Column('id', String(64), primary_key=True), Column('cik', String(10), nullable=False),
        Column('snapshot_id', ForeignKey('sec_snapshots.id'), nullable=False),
        Column('received_at', String(40), nullable=False), Column('state', String(20), nullable=False),
        Column('model_id', ForeignKey('company_models.id')), Column('reason', String(80)),
        Column('completed_at', String(40)))

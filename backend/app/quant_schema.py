"""Experiment-only tables; no foreign key or write into portfolio accounting."""
from sqlalchemy import Table, Column, String, Integer, JSON, ForeignKey, Index


def register(metadata):
    Table('quant_datasets', metadata,
          Column('hash', String(64), primary_key=True), Column('payload', JSON, nullable=False))
    trials = Table('quant_trials', metadata,
          Column('id', String(100), primary_key=True), Column('request_hash', String(64), nullable=False),
          Column('dataset_hash', ForeignKey('quant_datasets.hash'), nullable=False),
          Column('config_hash', String(64), nullable=False), Column('code_hash', String(64), nullable=False),
          Column('config', JSON, nullable=False), Column('runtime', JSON, nullable=False),
          Column('state', String(24), nullable=False), Column('reason', String(80), nullable=False),
          Column('created_at', String(40), nullable=False), Column('updated_at', String(40), nullable=False),
          Column('attempt', Integer, nullable=False), Column('lease_token', String(36)),
          Column('lease_until', String(40)), Column('result', JSON), Column('result_hash', String(64)))
    Index('ix_quant_trials_state', trials.c.state)
    Table('quant_trial_events', metadata,
          Column('sequence', Integer, primary_key=True, autoincrement=True),
          Column('trial_id', ForeignKey('quant_trials.id'), nullable=False),
          Column('at', String(40), nullable=False), Column('state', String(24), nullable=False),
          Column('reason', String(80), nullable=False), Column('attempt', Integer, nullable=False))

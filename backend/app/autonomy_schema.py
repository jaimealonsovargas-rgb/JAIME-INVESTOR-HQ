from sqlalchemy import Table, Column, String, Text, ForeignKey, Index

TABLES = ('autonomy_control', 'autonomy_events', 'research_tasks')


def register(metadata):
    Table('autonomy_control', metadata, Column('id', String(64), primary_key=True), Column('payload', Text, nullable=False))
    Table('autonomy_events', metadata, Column('id', String(36), primary_key=True),
          Column('idempotency_key', String(64), unique=True, nullable=False), Column('payload', Text, nullable=False))
    tasks = Table('research_tasks', metadata, Column('id', String(36), primary_key=True),
          Column('event_id', String(36), ForeignKey('autonomy_events.id'), unique=True, nullable=False),
          Column('state', String(32), nullable=False), Column('payload', Text, nullable=False))
    Index('ix_research_tasks_state', tasks.c.state)

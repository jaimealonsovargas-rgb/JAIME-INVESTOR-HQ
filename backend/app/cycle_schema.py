from sqlalchemy import Table, Column, String, JSON, UniqueConstraint, Index


def register(metadata):
    Table('cycle_agendas', metadata,
          Column('id', String(64), primary_key=True), Column('owner', String(16), nullable=False),
          Column('updated_at', String(40), nullable=False))
    cycles = Table('automation_cycles', metadata,
        Column('id', String(64), primary_key=True), Column('event_id', String(100), unique=True, nullable=False),
        Column('agenda', String(64), nullable=False), Column('window_start', String(40), nullable=False),
        Column('request_hash', String(64), nullable=False), Column('request', JSON, nullable=False),
        Column('state', String(24), nullable=False), Column('created_at', String(40), nullable=False),
        Column('updated_at', String(40), nullable=False), Column('deadline_at', String(40), nullable=False),
        Column('next_at', String(40), nullable=False), Column('review_cutoff', String(40)),
        Column('result', JSON, nullable=False),
        UniqueConstraint('agenda', 'window_start', name='uq_cycle_agenda_window'))
    Index('ix_automation_cycles_state', cycles.c.state)

from sqlalchemy import Table, Column, String, Text, Integer, ForeignKey, UniqueConstraint, Index

TABLES = ('agents', 'research_cases', 'agent_jobs', 'evidence', 'agent_results', 'research_claims', 'audit_events')


def register(metadata):
    Table('agents', metadata, Column('id', String(64), primary_key=True), Column('payload', Text, nullable=False))
    Table('research_cases', metadata, Column('id', String(36), primary_key=True), Column('instrument_id', String(64), nullable=False),
          Column('request_key', String(128), unique=True, nullable=False), Column('payload', Text, nullable=False))
    jobs = Table('agent_jobs', metadata, Column('id', String(36), primary_key=True),
          Column('case_id', String(36), ForeignKey('research_cases.id'), nullable=False), Column('role_id', String(64), ForeignKey('agents.id'), nullable=False),
          Column('run_key', String(128), nullable=False), Column('kind', String(16), nullable=False), Column('state', String(32), nullable=False),
          Column('priority', Integer, nullable=False), Column('depends_on', String(36)), Column('payload', Text, nullable=False), UniqueConstraint('case_id', 'run_key', 'role_id'))
    Index('ix_jobs_dispatch', jobs.c.state, jobs.c.kind, jobs.c.priority)
    for name in ('evidence', 'agent_results', 'research_claims'):
        Table(name, metadata, Column('id', String(64), primary_key=True), Column('case_id', String(36), ForeignKey('research_cases.id'), nullable=False),
              Column('job_id', String(36), ForeignKey('agent_jobs.id')), Column('payload', Text, nullable=False))
    Table('audit_events', metadata, Column('id', String(36), primary_key=True), Column('payload', Text, nullable=False))

"""Persistent P4 research domain. No financial mutation."""
from alembic import op
from sqlalchemy import MetaData, text
from app.research_schema import register, TABLES

revision = '0004_research'
down_revision = '0003_portfolio'
branch_labels = depends_on = None


def upgrade():
    metadata = MetaData()
    register(metadata)
    metadata.create_all(op.get_bind())
    for table in ('evidence', 'agent_results', 'research_claims', 'audit_events'):
        for verb in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER {table}_no_{verb.lower()} BEFORE {verb} ON {table} BEGIN SELECT RAISE(ABORT, 'P4 immutable evidence'); END")


def downgrade():
    if op.get_bind().execute(text('SELECT COUNT(*) FROM research_cases')).scalar():
        raise RuntimeError('P4 contiene research; restaurar backup, no destruir evidencia.')
    for table in reversed(TABLES):
        op.drop_table(table)

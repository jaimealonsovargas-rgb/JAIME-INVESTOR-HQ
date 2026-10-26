"""P4 autonomous descriptive events; isolated from financial records."""
from alembic import op
from sqlalchemy import MetaData, text
from app.autonomy_schema import register, TABLES

revision = '0006_autonomy'
down_revision = '0005_data_history'
branch_labels = depends_on = None


def upgrade():
    metadata = MetaData()
    register(metadata)
    metadata.create_all(op.get_bind())
    for verb in ('UPDATE', 'DELETE'):
        op.execute(f"CREATE TRIGGER autonomy_events_no_{verb.lower()} BEFORE {verb} ON autonomy_events BEGIN SELECT RAISE(ABORT, 'P4 immutable event'); END")


def downgrade():
    if op.get_bind().execute(text('SELECT COUNT(*) FROM autonomy_events')).scalar():
        raise RuntimeError('Autonomía contiene evidencia; no destruir el historial.')
    for table in reversed(TABLES):
        op.drop_table(table)

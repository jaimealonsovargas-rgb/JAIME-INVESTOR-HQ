"""Durable SEC model-update outbox; no changes to historical models or ledger."""
from alembic import op
import sqlalchemy as sa

revision = '0012_company_updates'
down_revision = '0011_company_models'
branch_labels = depends_on = None


def upgrade():
    op.create_table('company_update_events',
        sa.Column('id', sa.String(64), primary_key=True), sa.Column('cik', sa.String(10), nullable=False),
        sa.Column('snapshot_id', sa.String(64), sa.ForeignKey('sec_snapshots.id'), nullable=False),
        sa.Column('received_at', sa.String(40), nullable=False), sa.Column('state', sa.String(20), nullable=False),
        sa.Column('model_id', sa.String(64), sa.ForeignKey('company_models.id')),
        sa.Column('reason', sa.String(80)), sa.Column('completed_at', sa.String(40)))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM company_update_events')).scalar():
        raise RuntimeError('Preservar eventos antes de retirar la migración.')
    op.drop_table('company_update_events')

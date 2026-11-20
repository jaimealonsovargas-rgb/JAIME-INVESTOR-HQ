"""Add the B2.5 shadow coordinator; preserve all existing domain tables."""
from alembic import op
import sqlalchemy as sa

revision = '0013_shadow_cycles'
down_revision = '0012_company_updates'
branch_labels = depends_on = None


def upgrade():
    op.create_table('cycle_agendas', sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('owner', sa.String(16), nullable=False), sa.Column('updated_at', sa.String(40), nullable=False))
    op.create_table('automation_cycles',
        sa.Column('id', sa.String(64), primary_key=True), sa.Column('event_id', sa.String(100), nullable=False, unique=True),
        sa.Column('agenda', sa.String(64), nullable=False), sa.Column('window_start', sa.String(40), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False), sa.Column('request', sa.JSON(), nullable=False),
        sa.Column('state', sa.String(24), nullable=False), sa.Column('created_at', sa.String(40), nullable=False),
        sa.Column('updated_at', sa.String(40), nullable=False), sa.Column('deadline_at', sa.String(40), nullable=False),
        sa.Column('next_at', sa.String(40), nullable=False), sa.Column('review_cutoff', sa.String(40)),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.UniqueConstraint('agenda', 'window_start', name='uq_cycle_agenda_window'))
    op.create_index('ix_automation_cycles_state', 'automation_cycles', ['state'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM automation_cycles')).scalar():
        raise RuntimeError('Preservar ciclos antes de retirar la migración.')
    op.drop_table('automation_cycles')
    op.drop_table('cycle_agendas')

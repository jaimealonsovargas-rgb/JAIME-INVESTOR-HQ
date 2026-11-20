"""Add isolated synthetic experiment registry. Never modify MASTER."""
from alembic import op
import sqlalchemy as sa

revision = '0014_quant_lab'
down_revision = '0013_shadow_cycles'
branch_labels = depends_on = None


def upgrade():
    op.create_table('quant_datasets', sa.Column('hash', sa.String(64), primary_key=True),
                    sa.Column('payload', sa.JSON(), nullable=False))
    op.create_table('quant_trials',
        sa.Column('id', sa.String(100), primary_key=True), sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('dataset_hash', sa.String(64), sa.ForeignKey('quant_datasets.hash'), nullable=False),
        sa.Column('config_hash', sa.String(64), nullable=False), sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False), sa.Column('runtime', sa.JSON(), nullable=False),
        sa.Column('state', sa.String(24), nullable=False), sa.Column('reason', sa.String(80), nullable=False),
        sa.Column('created_at', sa.String(40), nullable=False), sa.Column('updated_at', sa.String(40), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False), sa.Column('lease_token', sa.String(36)),
        sa.Column('lease_until', sa.String(40)), sa.Column('result', sa.JSON()), sa.Column('result_hash', sa.String(64)))
    op.create_index('ix_quant_trials_state', 'quant_trials', ['state'])
    op.create_table('quant_trial_events',
        sa.Column('sequence', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trial_id', sa.String(100), sa.ForeignKey('quant_trials.id'), nullable=False),
        sa.Column('at', sa.String(40), nullable=False), sa.Column('state', sa.String(24), nullable=False),
        sa.Column('reason', sa.String(80), nullable=False), sa.Column('attempt', sa.Integer(), nullable=False))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM quant_trials')).scalar():
        raise RuntimeError('Preservar los ensayos antes de retirar la migración.')
    for name in ('quant_trial_events', 'quant_trials', 'quant_datasets'):
        op.drop_table(name)

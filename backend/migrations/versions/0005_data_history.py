"""P2 observation archive and restart-safe refresh schedule. No financial writes."""
from alembic import op
import sqlalchemy as sa

revision = '0005_data_history'
down_revision = '0004_research'
branch_labels = depends_on = None


def upgrade():
    op.create_table('data_observations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('access_id', sa.String(8), nullable=False),
        sa.Column('source_identity', sa.String(120), nullable=False),
        sa.Column('observed_at', sa.String(40), nullable=False),
        sa.Column('received_at', sa.String(40), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False))
    op.create_index('ix_data_observations_access_id', 'data_observations', ['access_id'])
    op.create_index('ix_data_observations_observed_at', 'data_observations', ['observed_at'])
    op.create_table('data_refresh',
        sa.Column('access_id', sa.String(8), primary_key=True),
        sa.Column('next_due_at', sa.String(40), nullable=False),
        sa.Column('attempted_at', sa.String(40)),
        sa.Column('succeeded_at', sa.String(40)),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('failures', sa.Integer(), nullable=False))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM data_observations')).scalar():
        raise RuntimeError('El histórico P2 contiene observaciones; conservar backup antes de retirar la migración.')
    op.drop_table('data_refresh')
    op.drop_table('data_observations')

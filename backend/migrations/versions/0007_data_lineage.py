"""Add receipts without rewriting legacy observations or financial records."""
from alembic import op
import sqlalchemy as sa

revision = '0007_data_lineage'
down_revision = '0006_autonomy'
branch_labels = depends_on = None


def upgrade():
    op.create_table('data_downloads',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('source_identity', sa.String(120), nullable=False),
        sa.Column('received_at', sa.String(40), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('observation_ids', sa.JSON(), nullable=False))
    op.create_index('ix_data_downloads_source_identity', 'data_downloads', ['source_identity'])
    # No invented first-seen times or lost filings. Legacy rows stay intact.


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM data_downloads')).scalar():
        raise RuntimeError('Descargas con trazabilidad: conservar backup antes de retirar la migración.')
    op.drop_table('data_downloads')

"""Add immutable accounting artifacts; do not change evidence or portfolio tables."""
from alembic import op
import sqlalchemy as sa

revision = '0011_company_models'
down_revision = '0010_market_data'
branch_labels = depends_on = None


def upgrade():
    op.create_table('company_models',
        sa.Column('id', sa.String(64), primary_key=True), sa.Column('cik', sa.String(10), nullable=False),
        sa.Column('version', sa.Integer, nullable=False), sa.Column('created_at', sa.String(40), nullable=False),
        sa.Column('as_of', sa.String(40), nullable=False), sa.Column('previous_id', sa.String(64)),
        sa.Column('input_hash', sa.String(64), nullable=False), sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False), sa.UniqueConstraint('cik','version',name='uq_company_version'))
    op.create_index('ix_company_models_issuer','company_models',['cik','version'])
    op.create_table('company_model_requests',
        sa.Column('id',sa.String(128),primary_key=True),sa.Column('request_hash',sa.String(64),nullable=False),
        sa.Column('model_id',sa.String(64),sa.ForeignKey('company_models.id'),nullable=False),
        sa.Column('created_at',sa.String(40),nullable=False))


def downgrade():
    for name in ('company_model_requests','company_models'):
        if op.get_bind().execute(sa.text(f'SELECT COUNT(*) FROM {name}')).scalar():
            raise RuntimeError('Modelos presentes: preservar evidencia antes de retirar la migración.')
    op.drop_table('company_model_requests')
    op.drop_table('company_models')

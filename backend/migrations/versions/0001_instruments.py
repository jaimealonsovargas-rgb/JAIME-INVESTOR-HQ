"""Registro vacío: no se cargan instrumentos, precios ni saldos ficticios."""
from alembic import op
import sqlalchemy as sa

revision = "0001_instruments"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "instruments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(120), nullable=False),
        sa.Column("venue", sa.String(120), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("symbol", "venue", "currency", name="uq_instrument_market"),
    )


def downgrade():
    op.drop_table("instruments")

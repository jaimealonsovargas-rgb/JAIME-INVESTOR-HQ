"""P3 append-only journal and reproducible valuation snapshots. No financial seed."""
from alembic import op
import sqlalchemy as sa

revision = '0003_portfolio'
down_revision = '0002_data'
branch_labels = depends_on = None


def upgrade():
    op.create_table('portfolios', sa.Column('id', sa.String(40), primary_key=True),
        sa.Column('base_currency', sa.String(3), nullable=False), sa.Column('status', sa.String(20), nullable=False))
    op.create_table('ledger_events', sa.Column('sequence', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('portfolio_id', sa.String(40), sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('source_ref', sa.String(200), nullable=False), sa.Column('occurred_at', sa.String(40), nullable=False),
        sa.Column('payload', sa.Text, nullable=False), sa.Column('previous_hash', sa.String(64), nullable=False),
        sa.Column('hash', sa.String(64), nullable=False), sa.UniqueConstraint('portfolio_id', 'source_ref'))
    op.create_index('ix_ledger_portfolio_time', 'ledger_events', ['portfolio_id', 'occurred_at', 'sequence'])
    op.create_table('ledger_entries', sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('ledger_events.sequence'), nullable=False),
        sa.Column('account', sa.String(200), nullable=False), sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('debit', sa.Text, nullable=False), sa.Column('credit', sa.Text, nullable=False))
    op.create_index('ix_entries_event', 'ledger_entries', ['event_id'])
    op.create_table('valuation_snapshots', sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('portfolio_id', sa.String(40), sa.ForeignKey('portfolios.id'), nullable=False),
        sa.Column('as_of', sa.String(40), nullable=False), sa.Column('ledger_hash', sa.String(64), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False, unique=True), sa.Column('payload', sa.Text, nullable=False))
    op.create_index('ix_snapshots_portfolio_time', 'valuation_snapshots', ['portfolio_id', 'as_of'])
    for table in ('ledger_events', 'ledger_entries', 'valuation_snapshots', 'portfolios'):
        for verb in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER {table}_no_{verb.lower()} BEFORE {verb} ON {table} BEGIN SELECT RAISE(ABORT, 'P3 append-only: mutation forbidden'); END")


def downgrade():
    # Never destroy a populated financial history through an accidental downgrade.
    if op.get_bind().execute(sa.text('SELECT 1 FROM ledger_events LIMIT 1')).first():
        raise RuntimeError('P3 contains immutable history. Restore the verified pre-P3 backup instead.')
    for table in ('valuation_snapshots', 'ledger_entries', 'ledger_events', 'portfolios'):
        op.drop_table(table)

"""P2 incremental: identidad ampliada, alias, cache y cuotas; ningún seed."""
import json
from alembic import op
import sqlalchemy as sa

revision = '0002_data'
down_revision = '0001_instruments'
branch_labels = depends_on = None

def upgrade():
    connection=op.get_bind()
    op.add_column('instruments',sa.Column('asset_class',sa.String(32),nullable=False,server_default='EQUITY'))
    for row in connection.execute(sa.text('SELECT id, payload FROM instruments')).mappings():
        data=json.loads(row['payload']) if isinstance(row['payload'],str) else row['payload']
        connection.execute(sa.text('UPDATE instruments SET asset_class=:asset WHERE id=:id'),{'asset':data['asset_class'],'id':row['id']})
    with op.batch_alter_table('instruments') as batch:
        batch.drop_constraint('uq_instrument_market',type_='unique')
        batch.alter_column('currency',existing_type=sa.String(3),type_=sa.String(12))
        batch.alter_column('asset_class',server_default=None)
        batch.create_unique_constraint('uq_instrument_identity',['symbol','venue','currency','asset_class'])
    op.create_table('instrument_aliases',sa.Column('id',sa.String(36),primary_key=True),sa.Column('instrument_id',sa.String(36),sa.ForeignKey('instruments.id'),nullable=False),*[sa.Column(k,sa.String(n),nullable=False) for k,n in [('provider',100),('symbol',120),('venue',120),('currency',12),('source',500),('verified_at',40)]],sa.Column('expires_at',sa.String(40)),sa.UniqueConstraint('provider','symbol','venue','currency',name='uq_alias_identity'))
    op.create_table('data_records',sa.Column('key',sa.String(120),primary_key=True),sa.Column('payload',sa.JSON,nullable=False),sa.Column('expires_at',sa.String(40),nullable=False),sa.Column('updated_at',sa.String(40),nullable=False))
    op.create_table('data_quotas',sa.Column('key',sa.String(120),primary_key=True),sa.Column('window_start',sa.String(40),nullable=False),sa.Column('used',sa.Integer,nullable=False),sa.Column('blocked_until',sa.String(40)),sa.Column('failures',sa.Integer,nullable=False))

def downgrade():
    # Solo reversible si el registro sigue siendo representable por P0; fallar sin borrar.
    connection=op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM instruments WHERE length(currency)>3 OR currency='' LIMIT 1")).first() or connection.execute(sa.text('SELECT 1 FROM instruments GROUP BY symbol,venue,currency HAVING count(*)>1 LIMIT 1')).first():
        raise RuntimeError('Rollback incompatible: exportar instrumentos P2 antes de volver a P0.')
    op.drop_table('data_quotas');op.drop_table('data_records');op.drop_table('instrument_aliases')
    with op.batch_alter_table('instruments') as batch:
        batch.drop_constraint('uq_instrument_identity',type_='unique')
        batch.drop_column('asset_class')
        batch.alter_column('currency',existing_type=sa.String(12),type_=sa.String(3))
        batch.create_unique_constraint('uq_instrument_market',['symbol','venue','currency'])

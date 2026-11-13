"""Identificador público estável e campos opcionais, preservando o histórico."""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
revision = '0002'
down_revision = '0001'
def upgrade():
    op.add_column('equipamentos', sa.Column('public_id', sa.String(36), nullable=True))
    op.add_column('equipamentos', sa.Column('descricao', sa.Text, nullable=True))
    op.add_column('equipamentos', sa.Column('criado_em', sa.String, nullable=True))
    connection = op.get_bind()
    for id in connection.execute(sa.text('SELECT id FROM equipamentos')).scalars():
        connection.execute(sa.text('UPDATE equipamentos SET public_id=:public_id WHERE id=:id'), {'public_id': str(uuid4()), 'id': id})
    op.create_index('uq_equipment_public_id', 'equipamentos', ['public_id'], unique=True)
def downgrade():
    raise RuntimeError('Downgrade não remove identificadores públicos já emitidos.')

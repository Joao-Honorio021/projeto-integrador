"""Identificador público estável; adota colunas existentes sem trocar etiquetas."""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
revision = '0002'
down_revision = '0001'


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = {column['name'] for column in inspector.get_columns('equipamentos')}
    for column in (
        sa.Column('public_id', sa.String(36), nullable=True),
        sa.Column('descricao', sa.Text, nullable=True),
        sa.Column('criado_em', sa.String, nullable=True),
    ):
        if column.name not in columns:
            op.add_column('equipamentos', column)
    # Nunca substituir um UUID já usado por uma etiqueta.
    for id in connection.execute(sa.text('SELECT id FROM equipamentos WHERE public_id IS NULL')).scalars():
        connection.execute(sa.text('UPDATE equipamentos SET public_id=:public_id WHERE id=:id'), {'public_id': str(uuid4()), 'id': id})
    unique_columns = [item['column_names'] for item in inspector.get_unique_constraints('equipamentos')]
    unique_columns += [item['column_names'] for item in inspector.get_indexes('equipamentos') if item['unique']]
    if ['public_id'] not in unique_columns:
        op.create_index('uq_equipment_public_id', 'equipamentos', ['public_id'], unique=True)


def downgrade():
    raise RuntimeError('Downgrade não remove identificadores públicos já emitidos.')

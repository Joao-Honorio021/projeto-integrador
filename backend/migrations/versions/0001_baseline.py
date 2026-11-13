"""Adota tabelas existentes sem apagar registros e cria tabelas ausentes."""
from alembic import op
import sqlalchemy as sa
from pathlib import Path
revision = '0001'
down_revision = None

def upgrade():
    # Snapshot congelado das entidades originais; sem dependência dos models futuros.
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase): pass
    source = (Path(__file__).parents[1] / 'baseline_models.txt').read_text()
    source = source.replace('from .database import Base', '')
    namespace = {'Base': Base}
    exec(compile(source, 'baseline_models', 'exec'), namespace)
    for table in Base.metadata.sorted_tables:
        if not sa.inspect(op.get_bind()).has_table(table.name):
            table.create(op.get_bind())
    if not sa.inspect(op.get_bind()).has_table('seed_versions'):
        op.create_table('seed_versions', sa.Column('version', sa.String, primary_key=True), sa.Column('aplicado_em', sa.String, nullable=False))

def downgrade():
    raise RuntimeError('Downgrade destrutivo não autorizado. Restaure um backup revisado.')

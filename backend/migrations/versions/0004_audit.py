"""Auditoria administrativa, prazo de OS e deduplicação de lembretes."""
from alembic import op
import sqlalchemy as sa
revision = '0004'
down_revision = '0003'

def upgrade():
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table('auditoria'):
        op.create_table('auditoria', sa.Column('id',sa.Integer,primary_key=True), sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False), sa.Column('entidade',sa.String,nullable=False), sa.Column('registro_id',sa.Integer,nullable=False), sa.Column('tipo',sa.String,nullable=False), sa.Column('descricao',sa.Text,nullable=False), sa.Column('criado_em',sa.String,nullable=False))
    if 'ix_auditoria_entidade' not in {i['name'] for i in inspector.get_indexes('auditoria')}:
        op.create_index('ix_auditoria_entidade','auditoria',['entidade','registro_id'])
    if 'prazo' not in {c['name'] for c in inspector.get_columns('ordens')}:
        op.add_column('ordens',sa.Column('prazo',sa.String,nullable=True))
    if 'evento' not in {c['name'] for c in inspector.get_columns('notificacoes')}:
        op.add_column('notificacoes',sa.Column('evento',sa.String,nullable=True))
    if 'uq_notificacao_evento' not in {i['name'] for i in inspector.get_indexes('notificacoes')}:
        op.create_index('uq_notificacao_evento','notificacoes',['usuario_id','evento'],unique=True)

def downgrade():
    raise RuntimeError('Downgrade destrutivo não autorizado')

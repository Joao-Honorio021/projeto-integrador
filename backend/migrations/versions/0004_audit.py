"""Auditoria administrativa, prazo de OS e deduplicação de lembretes."""
from alembic import op
import sqlalchemy as sa
revision = '0004'
down_revision = '0003'

def upgrade():
    op.create_table('auditoria', sa.Column('id',sa.Integer,primary_key=True), sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False), sa.Column('entidade',sa.String,nullable=False), sa.Column('registro_id',sa.Integer,nullable=False), sa.Column('tipo',sa.String,nullable=False), sa.Column('descricao',sa.Text,nullable=False), sa.Column('criado_em',sa.String,nullable=False))
    op.create_index('ix_auditoria_entidade','auditoria',['entidade','registro_id'])
    op.add_column('ordens',sa.Column('prazo',sa.String,nullable=True))
    op.add_column('notificacoes',sa.Column('evento',sa.String,nullable=True))
    op.create_index('uq_notificacao_evento','notificacoes',['usuario_id','evento'],unique=True)

def downgrade():
    raise RuntimeError('Downgrade destrutivo não autorizado')

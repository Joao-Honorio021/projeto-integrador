from alembic import op
import sqlalchemy as sa
revision='0003'
down_revision='0002'
def upgrade():
    op.create_table('preventivas', sa.Column('id',sa.Integer,primary_key=True),sa.Column('equipamento_id',sa.Integer,sa.ForeignKey('equipamentos.id'),nullable=False),sa.Column('responsavel_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('atividade',sa.String,nullable=False),sa.Column('descricao',sa.Text,nullable=False),sa.Column('frequencia_dias',sa.Integer,nullable=False),sa.Column('proxima_execucao',sa.String,nullable=False))
    op.create_table('execucoes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('plano_id',sa.Integer,sa.ForeignKey('preventivas.id'),nullable=False),sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('executado_em',sa.String,nullable=False),sa.Column('observacoes',sa.Text,nullable=False))
    op.create_table('notificacoes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('mensagem',sa.String,nullable=False),sa.Column('destino',sa.String,nullable=False),sa.Column('criado_em',sa.String,nullable=False),sa.Column('lida',sa.Boolean,nullable=False))
    op.create_index('ix_notifications_user','notificacoes',['usuario_id','lida'])
def downgrade():
    raise RuntimeError('Downgrade destrutivo não autorizado')

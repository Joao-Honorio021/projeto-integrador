from alembic import op
import sqlalchemy as sa
revision='0003'
down_revision='0002'
def upgrade():
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table('preventivas'):
        op.create_table('preventivas', sa.Column('id',sa.Integer,primary_key=True),sa.Column('equipamento_id',sa.Integer,sa.ForeignKey('equipamentos.id'),nullable=False),sa.Column('responsavel_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('atividade',sa.String,nullable=False),sa.Column('descricao',sa.Text,nullable=False),sa.Column('frequencia_dias',sa.Integer,nullable=False),sa.Column('proxima_execucao',sa.String,nullable=False))
    if not inspector.has_table('execucoes'):
        op.create_table('execucoes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('plano_id',sa.Integer,sa.ForeignKey('preventivas.id'),nullable=False),sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('executado_em',sa.String,nullable=False),sa.Column('observacoes',sa.Text,nullable=False))
    if not inspector.has_table('notificacoes'):
        op.create_table('notificacoes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('usuario_id',sa.Integer,sa.ForeignKey('usuarios.id'),nullable=False),sa.Column('mensagem',sa.String,nullable=False),sa.Column('destino',sa.String,nullable=False),sa.Column('criado_em',sa.String,nullable=False),sa.Column('lida',sa.Boolean,nullable=False))
    if 'ix_notifications_user' not in {i['name'] for i in inspector.get_indexes('notificacoes')}:
        op.create_index('ix_notifications_user','notificacoes',['usuario_id','lida'])
def downgrade():
    raise RuntimeError('Downgrade destrutivo não autorizado')

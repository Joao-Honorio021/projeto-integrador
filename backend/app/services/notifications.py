from sqlalchemy import text
from ..models import now

def notify(db,user_id,message,destination):
    db.execute(text('INSERT INTO notificacoes (usuario_id,mensagem,destino,criado_em,lida) VALUES (:user,:message,:destination,:now,:read)'),{'user':user_id,'message':message,'destination':destination,'now':now(),'read':False})

def managers(db,message,destination):
    for id in db.execute(text("SELECT id FROM usuarios WHERE ativo=:active AND perfil IN ('administrador','supervisor')"),{'active':True}).scalars():
        notify(db,id,message,destination)

def preventive_reminders(db, user):
    """Atualização sob demanda: uma mensagem por plano, vencimento e estágio."""
    from datetime import date, timedelta
    if user.perfil not in ('administrador','supervisor','tecnico'):return
    today=date.today();limit=(today+timedelta(days=7)).isoformat()
    plans=db.execute(text("SELECT id,atividade,proxima_execucao FROM preventivas WHERE proxima_execucao<=:limit AND (:role IN ('administrador','supervisor') OR responsavel_id=:user)"),{'limit':limit,'role':user.perfil,'user':user.id}).mappings()
    for plan in plans:
        stage='atrasada' if plan['proxima_execucao']<today.isoformat() else 'próxima'
        event=f"preventiva:{plan['id']}:{plan['proxima_execucao']}:{stage}"
        db.execute(text('INSERT INTO notificacoes (usuario_id,mensagem,destino,criado_em,lida,evento) VALUES (:user,:message,:destination,:now,:read,:event) ON CONFLICT (usuario_id,evento) DO NOTHING'),{'user':user.id,'message':f"Preventiva {stage}: {plan['atividade']} ({plan['proxima_execucao']})",'destination':'/preventivas','now':now(),'read':False,'event':event})
    db.commit()

from sqlalchemy import text
from ..models import now

def accessible_destination(db, user, notification):
    """Links legados são resolvidos com a permissão atual, sem alterar o registro."""
    import re
    from fastapi import HTTPException
    from ..models import Ticket, Order
    from ..repositories.sql_repository import find
    from .equipment import resolve
    from .support import visible
    destination = notification['destino'] or ''
    if destination == '/ordens':
        legacy = re.search(r'\bOS-([1-9]\d*)\b', notification['mensagem'])
        if legacy:
            destination = '/ordens?id=' + legacy[1]
        else:
            return destination
    if destination == '/preventivas':
        return destination if user.perfil in ('administrador', 'supervisor', 'tecnico') else None
    equipment = re.fullmatch(r'/equipamentos/([^/]+)', destination)
    if equipment:
        try:
            resolve(db, equipment[1])
            return destination
        except HTTPException:
            return None
    match = re.fullmatch(r'/(chamados/|ordens\?id=)([1-9]\d*)', destination)
    if not match or int(match[2]) > 2147483647:
        return None
    id = int(match[2])
    if match[1] == 'ordens?id=':
        order = find(db, Order, id)
        if not order:
            return None
        id = order.chamado_id
    ticket = find(db, Ticket, id)
    return destination if ticket and visible(ticket, user) else None

def notify(db,user_id,message,destination):
    db.execute(text('INSERT INTO notificacoes (usuario_id,mensagem,destino,criado_em,lida) VALUES (:user,:message,:destination,:now,:read)'),{'user':user_id,'message':message,'destination':destination,'now':now(),'read':False})

def managers(db,message,destination):
    for id in db.execute(text("SELECT id FROM usuarios WHERE ativo=:active AND perfil IN ('administrador','supervisor')"),{'active':True}).scalars():
        notify(db,id,message,destination)

def preventive_reminders(db, user):
    """Atualização sob demanda: uma mensagem por plano, vencimento e estágio."""
    from datetime import date, timedelta
    from .equipment import public_identifier
    from ..models import Equipment
    if user.perfil not in ('administrador','supervisor','tecnico'):return
    today=date.today();limit=(today+timedelta(days=7)).isoformat()
    plans=db.execute(text("SELECT p.id,p.atividade,p.proxima_execucao,e.id AS equipamento_id,e.public_id FROM preventivas p JOIN equipamentos e ON e.id=p.equipamento_id WHERE CAST(p.proxima_execucao AS TEXT)<=:limit AND (:role IN ('administrador','supervisor') OR p.responsavel_id=:user)"),{'limit':limit,'role':user.perfil,'user':user.id}).mappings()
    for plan in plans:
        stage='atrasada' if str(plan['proxima_execucao'])[:10]<today.isoformat() else 'próxima'
        event=f"preventiva:{plan['id']}:{plan['proxima_execucao']}:{stage}"
        destination='/equipamentos/' + public_identifier(Equipment(id=plan['equipamento_id'], public_id=plan['public_id']))
        db.execute(text('INSERT INTO notificacoes (usuario_id,mensagem,destino,criado_em,lida,evento) VALUES (:user,:message,:destination,:now,:read,:event) ON CONFLICT (usuario_id,evento) DO NOTHING'),{'user':user.id,'message':f"Preventiva {stage}: {plan['atividade']} ({plan['proxima_execucao']})",'destination':destination,'now':now(),'read':False,'event':event})
    db.commit()

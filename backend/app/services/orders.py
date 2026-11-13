"""Regras de atendimento e transações atômicas de ordens de serviço."""
from fastapi import HTTPException
from ..core.security import allow
from ..models import Ticket, Order, now
from ..repositories.sql_repository import insert, save, visible_orders
from ..schemas import OrderInput, Complete
from ..views.serializers import public
from ..services.support import get, ticket, log

def orders(u, db):
    return [public(o) for o in visible_orders(db, u)]

def create_order(data: OrderInput, u, db):
    allow(u, ['administrador', 'supervisor'])
    t = ticket(db, data.chamado_id, u)
    if not t.tecnico_id or t.status in ('Resolvido', 'Cancelado'):
        raise HTTPException(409, 'Atribua um técnico a um chamado ativo')
    o = insert(db, Order, chamado_id=t.id, tecnico_id=t.tecnico_id)
    log(db, t, u, 'Ordem de serviço criada')
    from .notifications import notify
    notify(db, t.tecnico_id, f'Ordem OS-{o.id} atribuída', '/ordens')
    db.commit()
    return public(o)

def owned_order(db, id, u):
    allow(u, ['administrador', 'supervisor', 'tecnico'])
    o = get(db, Order, id)
    if u.perfil == 'tecnico' and o.tecnico_id != u.id:
        raise HTTPException(403, 'Ordem atribuída a outro técnico')
    return (o, get(db, Ticket, o.chamado_id))

def start(id: int, u, db):
    o, t = owned_order(db, id, u)
    if o.status not in ('Pendente', 'Pausada'):
        raise HTTPException(409, 'Transição inválida')
    o.status = 'Em execução'
    o.inicio = o.inicio or now()
    t.status = 'Em atendimento'
    save(db, o)
    save(db, t)
    log(db, t, u, 'Atendimento iniciado')
    from .notifications import notify
    notify(db, t.solicitante_id, f'Chamado CH-{t.id} em atendimento', f'/chamados/{t.id}')
    db.commit()
    return public(o)

def pause(id: int, u, db):
    o, t = owned_order(db, id, u)
    if o.status != 'Em execução':
        raise HTTPException(409, 'Transição inválida')
    o.status = 'Pausada'
    save(db, o)
    log(db, t, u, 'Atendimento pausado')
    db.commit()
    return public(o)

def complete(id: int, data: Complete, u, db):
    o, t = owned_order(db, id, u)
    if o.status != 'Em execução':
        raise HTTPException(409, 'Inicie o atendimento antes de concluir')
    o.diagnostico = data.diagnostico
    o.solucao = data.solucao
    o.status = 'Concluída'
    o.conclusao = now()
    t.status = 'Resolvido'
    t.resolvido_em = o.conclusao
    save(db, o)
    save(db, t)
    from .notifications import notify
    notify(db, t.solicitante_id, f'Chamado CH-{t.id} resolvido', f'/chamados/{t.id}')
    log(db, t, u, f'Concluído. Diagnóstico: {o.diagnostico}. Solução: {o.solucao}')
    db.commit()
    return public(o)

def diagnose(id, data, u, db):
    o,t=owned_order(db,id,u)
    if o.status!='Em execução':raise HTTPException(409,'Inicie a ordem antes de registrar diagnóstico')
    o.diagnostico=data.diagnostico;save(db,o);log(db,t,u,'Diagnóstico registrado: '+o.diagnostico)
    db.commit();return public(o)

def deadline(id,data,u,db):
    allow(u,['administrador','supervisor'])
    o,t=owned_order(db,id,u)
    if o.status in ('Concluída','Cancelada'):raise HTTPException(409,'Ordem encerrada')
    o.prazo=data.prazo.isoformat();save(db,o);log(db,t,u,'Prazo da OS definido: '+o.prazo)
    db.commit();return public(o)

def cancel(id,data,u,db):
    allow(u,['administrador','supervisor'])
    o,t=owned_order(db,id,u)
    if o.status in ('Concluída','Cancelada'):raise HTTPException(409,'Ordem encerrada')
    o.status='Cancelada';t.status='Cancelado';save(db,o);save(db,t)
    log(db,t,u,'Ordem cancelada: '+data.mensagem)
    from .notifications import notify
    for uid in {t.solicitante_id,o.tecnico_id}:notify(db,uid,f'Ordem OS-{id} cancelada',f'/chamados/{t.id}')
    db.commit();return public(o)

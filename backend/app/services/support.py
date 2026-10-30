from fastapi import HTTPException
from ..models import Ticket, Activity
from ..repositories.sql_repository import find, insert

def get(db, model, id):
    obj = find(db, model, id)
    if not obj:
        raise HTTPException(404, 'Registro não encontrado')
    return obj

def visible(t, u):
    return u.perfil in ('administrador', 'supervisor') or (u.perfil == 'operador' and t.solicitante_id == u.id) or (u.perfil == 'tecnico' and t.tecnico_id == u.id)

def ticket(db, id, u):
    t = get(db, Ticket, id)
    if not visible(t, u):
        raise HTTPException(403, 'Chamado sem permissão de acesso')
    return t

def log(db, t, u, msg, tipo='evento'):
    insert(db, Activity, chamado_id=t.id, usuario_id=u.id, mensagem=msg, tipo=tipo)

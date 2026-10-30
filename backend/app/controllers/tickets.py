"""Controller HTTP: tickets."""
from ..repositories.sql_repository import order_for_ticket, ticket_history
from fastapi import APIRouter, Depends, HTTPException
from ..database import db_session
from ..core.security import current, allow
from ..models import User, Equipment, Ticket
from ..repositories.sql_repository import insert, save, ticket_page
from ..schemas import TicketInput, Assign, Comment
from ..views.serializers import public
from ..services.support import get, ticket, log
router = APIRouter(tags=["Chamados"])

@router.get('/chamados')
def tickets(q: str='', status: str='', prioridade: str='', equipamento_id: int | None=None, tecnico_id: int | None=None, page: int=1, u=Depends(current), db=Depends(db_session)):
    return ticket_page(db, u, q, status, prioridade, equipamento_id, tecnico_id, page)

@router.post('/chamados', status_code=201)
def create_ticket(data: TicketInput, u=Depends(current), db=Depends(db_session)):
    e = get(db, Equipment, data.equipamento_id)
    if not e.ativo:
        raise HTTPException(409, 'Equipamento inativo')
    t = insert(db, Ticket, **data.model_dump(), solicitante_id=u.id)
    log(db, t, u, 'Chamado aberto')
    db.commit()
    return public(t)

@router.get('/chamados/{id}')
def detail(id: int, u=Depends(current), db=Depends(db_session)):
    t = ticket(db, id, u)
    return {**public(t), 'historico': ticket_history(db, id)}

@router.patch('/chamados/{id}/atribuir')
def assign(id: int, data: Assign, u=Depends(current), db=Depends(db_session)):
    allow(u, ['administrador', 'supervisor'])
    t = ticket(db, id, u)
    if t.status in ('Resolvido', 'Cancelado') or order_for_ticket(db, id):
        raise HTTPException(409, 'Atribuição bloqueada após criação da ordem ou encerramento')
    tech = get(db, User, data.tecnico_id)
    if tech.perfil != 'tecnico' or not tech.ativo:
        raise HTTPException(422, 'Selecione um técnico ativo')
    t.tecnico_id = tech.id
    t.prioridade = data.prioridade
    t.status = 'Em análise'
    save(db, t)
    log(db, t, u, f'Atribuído a {tech.nome}. Prioridade: {t.prioridade}')
    db.commit()
    return public(t)

@router.post('/chamados/{id}/comentarios', status_code=201)
def comment(id: int, data: Comment, u=Depends(current), db=Depends(db_session)):
    t = ticket(db, id, u)
    log(db, t, u, data.mensagem, 'comentario')
    db.commit()
    return {'ok': True}

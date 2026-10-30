"""Controller HTTP: catalog."""
from ..repositories.sql_repository import all_records, equipment_tickets
from fastapi import APIRouter, Depends
from ..database import db_session
from ..core.security import current, allow
from ..models import User, Sector, Equipment
from ..repositories.sql_repository import insert, history_for_tickets
from ..schemas import EquipmentInput
from ..views.serializers import public
from ..services.support import get
router = APIRouter(tags=["Cadastros"])

@router.get('/usuarios')
def users(u=Depends(current), db=Depends(db_session)):
    allow(u, ['administrador', 'supervisor'])
    return [public(x) for x in all_records(db, User)]

@router.get('/setores')
def sectors(u=Depends(current), db=Depends(db_session)):
    return [public(x) for x in all_records(db, Sector)]

@router.get('/equipamentos')
def equipments(u=Depends(current), db=Depends(db_session)):
    return [public(x) for x in all_records(db, Equipment)]

@router.post('/equipamentos', status_code=201)
def create_equipment(data: EquipmentInput, u=Depends(current), db=Depends(db_session)):
    allow(u, ['administrador'])
    get(db, Sector, data.setor_id)
    e = insert(db, Equipment, **data.model_dump())
    db.commit()
    return public(e)

@router.get('/equipamentos/{id}')
def equipment(id: int, u=Depends(current), db=Depends(db_session)):
    return public(get(db, Equipment, id))

@router.get('/equipamentos/{id}/historico')
def equipment_history(id: int, u=Depends(current), db=Depends(db_session)):
    get(db, Equipment, id)
    ts = equipment_tickets(db, id, u)
    return {'chamados': [public(t) for t in ts], 'historico': [public(a) for a in history_for_tickets(db, [t.id for t in ts])]}

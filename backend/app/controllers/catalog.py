"""Controller HTTP: catalog."""
from ..repositories.sql_repository import all_records, equipment_tickets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from ..services.equipment import resolve, public_url
from ..schemas import EquipmentPatch
from ..repositories.sql_repository import save, visible_orders
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
    e = insert(db, Equipment, **data.model_dump(), ativo=data.status != 'Inativo')
    from ..services.audit import record
    record(db, u, 'equipamento', e.id, 'criacao', 'Equipamento cadastrado')
    db.commit()
    return public(e)

@router.get('/equipamentos/{id}')
def equipment(id: str, u=Depends(current), db=Depends(db_session)):
    return public(resolve(db, id))

@router.get('/equipamentos/{id}/historico')
def equipment_history(id: str, u=Depends(current), db=Depends(db_session)):
    id = resolve(db, id).id
    ts = equipment_tickets(db, id, u)
    return {'chamados': [public(t) for t in ts], 'historico': [public(a) for a in history_for_tickets(db, [t.id for t in ts])]}

@router.patch('/equipamentos/{identifier}')
def edit_equipment(identifier: str, data: EquipmentPatch, u=Depends(current), db=Depends(db_session)):
    allow(u, ['administrador'])
    equipment = resolve(db, identifier)
    changes = data.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(422, 'Os campos informados não podem ser nulos')
    if 'setor_id' in changes: get(db, Sector, changes['setor_id'])
    for key, value in changes.items(): setattr(equipment, key, value)
    equipment.ativo = equipment.status != 'Inativo'
    save(db, equipment)
    from ..services.audit import record
    record(db, u, 'equipamento', equipment.id, 'alteracao', 'Campos atualizados: '+', '.join(sorted(changes)))
    db.commit()
    return public(equipment)

@router.get('/equipamentos/{identifier}/qrcode')
def qr(identifier: str, u=Depends(current), db=Depends(db_session)):
    import qrcode
    from io import BytesIO
    equipment = resolve(db, identifier)
    buffer = BytesIO()
    qrcode.make(public_url(equipment)).save(buffer, format='PNG')
    return Response(buffer.getvalue(), media_type='image/png', headers={'Content-Disposition': f'attachment; filename="industrack-{equipment.public_id}.png"', 'Cache-Control': 'private, no-store'})

@router.get('/equipamentos/{identifier}/ordens')
def equipment_orders(identifier: str, u=Depends(current), db=Depends(db_session)):
    equipment = resolve(db, identifier)
    ids = {ticket.id for ticket in equipment_tickets(db, equipment.id, u)}
    return [public(order) for order in visible_orders(db, u) if order.chamado_id in ids]

@router.get('/equipamentos/{identifier}/preventivas')
def equipment_plans(identifier: str, u=Depends(current), db=Depends(db_session)):
    from sqlalchemy import text
    equipment = resolve(db, identifier)
    return [dict(row) for row in db.execute(text("SELECT id,atividade,proxima_execucao,frequencia_dias FROM preventivas WHERE equipamento_id=:id AND (:perfil IN ('administrador','supervisor') OR (:perfil='tecnico' AND responsavel_id=:user)) ORDER BY proxima_execucao"), {'id':equipment.id,'perfil':u.perfil,'user':u.id}).mappings()]

@router.get('/equipamentos/{identifier}/auditoria')
def equipment_audit(identifier: str, u=Depends(current), db=Depends(db_session)):
    from sqlalchemy import text
    equipment = resolve(db, identifier)
    return [dict(row) for row in db.execute(text("SELECT a.*,u.nome AS autor FROM auditoria a JOIN usuarios u ON u.id=a.usuario_id WHERE entidade='equipamento' AND registro_id=:id ORDER BY a.id DESC"),{'id':equipment.id}).mappings()]

"""Controllers de ordens: validação HTTP e delegação às regras de negócio."""
from fastapi import APIRouter, Depends
from ..database import db_session
from ..core.security import current
from ..schemas import OrderInput, Complete, Diagnosis, Deadline, Comment
from ..services import orders as service

router = APIRouter(tags=['Ordens de serviço'])

@router.get('/ordens-servico')
def orders(u=Depends(current), db=Depends(db_session)):
    return service.orders(u, db)

@router.post('/ordens-servico', status_code=201)
def create_order(data: OrderInput, u=Depends(current), db=Depends(db_session)):
    return service.create_order(data, u, db)

@router.patch('/ordens-servico/{id}/iniciar')
def start(id: int, u=Depends(current), db=Depends(db_session)):
    return service.start(id, u, db)

@router.patch('/ordens-servico/{id}/pausar')
def pause(id: int, u=Depends(current), db=Depends(db_session)):
    return service.pause(id, u, db)

@router.patch('/ordens-servico/{id}/concluir')
def complete(id: int, data: Complete, u=Depends(current), db=Depends(db_session)):
    return service.complete(id, data, u, db)

@router.patch('/ordens-servico/{id}/diagnostico')
def diagnose(id:int,data:Diagnosis,u=Depends(current),db=Depends(db_session)):
    return service.diagnose(id,data,u,db)

@router.patch('/ordens-servico/{id}/prazo')
def deadline(id:int,data:Deadline,u=Depends(current),db=Depends(db_session)):
    return service.deadline(id,data,u,db)

@router.patch('/ordens-servico/{id}/cancelar')
def cancel(id:int,data:Comment,u=Depends(current),db=Depends(db_session)):
    return service.cancel(id,data,u,db)

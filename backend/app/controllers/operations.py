"""Planejamento preventivo, notificações do usuário e relatórios autorizados."""
import csv
from io import StringIO
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from pydantic import Field
from ..database import db_session
from ..core.security import current, allow
from ..models import Equipment, User, now
from ..schemas import Input, Comment
from ..services.support import get
from ..repositories.sql_repository import access
router=APIRouter(tags=['Operações'])
class PlanInput(Input):
    equipamento_id:int=Field(gt=0)
    responsavel_id:int=Field(gt=0)
    atividade:str=Field(min_length=3,max_length=160)
    descricao:str=Field(default='',max_length=5000)
    frequencia_dias:int=Field(ge=1,le=3650)
    proxima_execucao:date

def plan_access(db,id,user):
    allow(user,['administrador','supervisor','tecnico'])
    plan=db.execute(text('SELECT * FROM preventivas WHERE id=:id'),{'id':id}).mappings().first()
    if not plan:raise HTTPException(404,'Plano não encontrado')
    if user.perfil=='tecnico' and plan['responsavel_id']!=user.id:raise HTTPException(403,'Plano atribuído a outro técnico')
    return plan

@router.get('/manutencoes')
def plans(u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador','supervisor','tecnico'])
    rows=db.execute(text("SELECT * FROM preventivas WHERE :perfil != 'tecnico' OR responsavel_id=:id ORDER BY proxima_execucao"),{'perfil':u.perfil,'id':u.id}).mappings()
    today=date.today()
    return [{**p,'status':'Atrasada' if date.fromisoformat(p['proxima_execucao'])<today else 'Próxima do vencimento' if date.fromisoformat(p['proxima_execucao'])<=today+timedelta(days=7) else 'Programada'} for p in rows]

@router.post('/manutencoes',status_code=201)
def create_plan(data:PlanInput,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador','supervisor'])
    equipment=get(db,Equipment,data.equipamento_id)
    technician=get(db,User,data.responsavel_id)
    if not equipment.ativo or not technician.ativo or technician.perfil!='tecnico':raise HTTPException(422,'Selecione equipamento ativo e técnico ativo')
    values=data.model_dump(mode='json')
    id=db.execute(text('INSERT INTO preventivas (equipamento_id,responsavel_id,atividade,descricao,frequencia_dias,proxima_execucao) VALUES (:equipamento_id,:responsavel_id,:atividade,:descricao,:frequencia_dias,:proxima_execucao) RETURNING id'),values).scalar_one()
    from ..services.notifications import notify
    notify(db,technician.id,'Plano preventivo atribuído: '+data.atividade,'/preventivas')
    db.commit();return {'id':id,**values}

@router.post('/manutencoes/{id}/executar')
def execute_plan(id:int,data:Comment,u=Depends(current),db=Depends(db_session)):
    plan=plan_access(db,id,u)
    next_date=(max(date.today(),date.fromisoformat(plan['proxima_execucao']))+timedelta(days=plan['frequencia_dias'])).isoformat()
    # Compare-and-swap impede duas execuções simultâneas para a mesma ocorrência.
    result=db.execute(text('UPDATE preventivas SET proxima_execucao=:next WHERE id=:id AND proxima_execucao=:old'),{'next':next_date,'old':plan['proxima_execucao'],'id':id})
    if result.rowcount!=1:raise HTTPException(409,'Plano atualizado por outro atendimento. Recarregue.')
    db.execute(text('INSERT INTO execucoes (plano_id,usuario_id,executado_em,observacoes) VALUES (:id,:user,:now,:message)'),{'id':id,'user':u.id,'now':now(),'message':data.mensagem})
    db.commit();return {'proxima_execucao':next_date}

@router.get('/manutencoes/{id}/historico')
def executions(id:int,u=Depends(current),db=Depends(db_session)):
    plan_access(db,id,u)
    return [dict(r) for r in db.execute(text('SELECT * FROM execucoes WHERE plano_id=:id ORDER BY id DESC'),{'id':id}).mappings()]

@router.get('/notificacoes')
def notifications(u=Depends(current),db=Depends(db_session)):
    from ..services.notifications import preventive_reminders
    preventive_reminders(db,u)
    return [dict(r) for r in db.execute(text('SELECT * FROM notificacoes WHERE usuario_id=:id ORDER BY id DESC LIMIT 100'),{'id':u.id}).mappings()]

@router.patch('/notificacoes/ler-todas')
def read_all(u=Depends(current),db=Depends(db_session)):
    db.execute(text('UPDATE notificacoes SET lida=:read WHERE usuario_id=:id'),{'read':True,'id':u.id});db.commit();return {'ok':True}

@router.patch('/notificacoes/{id}/ler')
def read_one(id:int,u=Depends(current),db=Depends(db_session)):
    result=db.execute(text('UPDATE notificacoes SET lida=:read WHERE id=:id AND usuario_id=:user'),{'read':True,'id':id,'user':u.id})
    if result.rowcount!=1:raise HTTPException(404,'Notificação não encontrada')
    db.commit();return {'ok':True}

@router.get('/relatorios/chamados.csv')
def report(inicio:date|None=None,fim:date|None=None,equipamento_id:int|None=None,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador','supervisor'])
    if inicio and fim and inicio>fim:raise HTTPException(422,'Período inválido')
    scope,params=access(u);params.update(equipment_id=equipamento_id,inicio=inicio.isoformat() if inicio else '',fim=fim.isoformat() if fim else '')
    records=db.execute(text('SELECT t.id,t.titulo,t.equipamento_id,t.status,t.prioridade,t.criado_em FROM chamados t WHERE '+scope+" AND (CAST(:equipment_id AS INTEGER) IS NULL OR t.equipamento_id=:equipment_id) AND (:inicio='' OR substr(t.criado_em,1,10)>=:inicio) AND (:fim='' OR substr(t.criado_em,1,10)<=:fim) ORDER BY t.id"),params)
    out=StringIO();writer=csv.writer(out);writer.writerow(['Protocolo','Título','Equipamento','Status','Prioridade','Abertura'])
    for row in records:
        writer.writerow(["'"+str(value) if str(value).lstrip().startswith(('=','+','-','@')) else value for value in row])
    return Response('\ufeff'+out.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="chamados.csv"'})

@router.get('/notificacoes/contador')
def notification_count(u=Depends(current),db=Depends(db_session)):
    from ..services.notifications import preventive_reminders
    preventive_reminders(db,u)
    return {'nao_lidas':db.execute(text('SELECT COUNT(*) FROM notificacoes WHERE usuario_id=:id AND lida=:read'),{'id':u.id,'read':False}).scalar_one()}

"""Cadastros administrativos sem exclusão de registros históricos."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from ..schemas import Input
from ..database import db_session
from ..core.security import current, allow, password_hash
from ..models import User, Sector
from ..repositories.sql_repository import insert, save
from ..services.support import get
from ..services.audit import record
from ..views.serializers import public

router = APIRouter(tags=['Administração'])
Role = Literal['administrador','supervisor','tecnico','operador']
class UserInput(Input):
    nome: str = Field(min_length=2,max_length=120)
    email: str = Field(pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$',max_length=254)
    perfil: Role
    senha: str = Field(min_length=12,max_length=128)
class UserPatch(Input):
    nome: str = Field(min_length=2,max_length=120)
    perfil: Role
    ativo: bool
class SectorInput(Input):
    nome: str = Field(min_length=2,max_length=120)

@router.post('/usuarios',status_code=201)
def create_user(data:UserInput,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador'])
    user=insert(db,User,nome=data.nome,email=data.email.lower(),perfil=data.perfil,senha_hash=password_hash.hash(data.senha))
    record(db,u,'usuario',user.id,'criacao','Usuário cadastrado')
    db.commit();return public(user)

@router.patch('/usuarios/{id}')
def update_user(id:int,data:UserPatch,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador'])
    user=get(db,User,id)
    if id==u.id and (not data.ativo or data.perfil!='administrador'):
        raise HTTPException(409,'Você não pode desativar ou remover o próprio acesso administrativo')
    for key,value in data.model_dump().items():setattr(user,key,value)
    save(db,user)
    record(db,u,'usuario',id,'alteracao',f'Perfil: {user.perfil}; ativo: {user.ativo}')
    db.commit();return public(user)

@router.post('/setores',status_code=201)
def create_sector(data:SectorInput,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador']);sector=insert(db,Sector,**data.model_dump())
    record(db,u,'setor',sector.id,'criacao','Setor cadastrado');db.commit();return public(sector)

@router.patch('/setores/{id}')
def update_sector(id:int,data:SectorInput,u=Depends(current),db=Depends(db_session)):
    allow(u,['administrador']);sector=get(db,Sector,id);sector.nome=data.nome;save(db,sector)
    record(db,u,'setor',id,'alteracao','Nome do setor atualizado');db.commit();return public(sector)

"""Rotas de autenticação; o frontend nunca determina perfil ou modo de acesso."""
from fastapi import APIRouter, Depends
from ..core import config
from ..core.security import current
from ..database import db_session
from ..schemas import Login
from ..services.authentication import authenticate
from ..views.serializers import public

router = APIRouter(tags=['Autenticação'])


@router.get('/auth/config')
def auth_config():
    return {'modo_demo': config.MODO_DEMO}


@router.post('/auth/login')
def login(data: Login, db=Depends(db_session)):
    return authenticate(data, db)


@router.get('/auth/me')
def me(u=Depends(current)):
    return public(u)

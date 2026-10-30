"""Controller HTTP: auth."""
from ..repositories.sql_repository import user_by_email
from ..core.security import password_hash, SECRET
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, Depends, HTTPException
from ..database import db_session
from ..core.security import current
from ..schemas import Login
from ..views.serializers import public
router = APIRouter(tags=["Autenticação"])

@router.post('/auth/login')
def login(data: Login, db=Depends(db_session)):
    u = user_by_email(db, data.email)
    if not u or not u.ativo or (not password_hash.verify(data.senha, u.senha_hash)):
        raise HTTPException(401, 'E-mail ou senha incorretos')
    return {'access_token': jwt.encode({'sub': str(u.id), 'exp': datetime.now(timezone.utc) + timedelta(hours=8)}, SECRET, algorithm='HS256'), 'usuario': public(u)}

@router.get('/auth/me')
def me(u=Depends(current)):
    return public(u)

"""Autenticação JWT e autorização compartilhadas."""
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..database import db_session
from ..models import User
from ..repositories.sql_repository import find
password_hash = PasswordHash.recommended()
from .config import JWT_SECRET
SECRET = JWT_SECRET
bearer = HTTPBearer()

def current(auth: HTTPAuthorizationCredentials=Depends(bearer), db=Depends(db_session)):
    try:
        data = jwt.decode(auth.credentials, SECRET, algorithms=['HS256'])
        user = find(db, User, int(data['sub']))
        if not user or not user.ativo:
            raise ValueError()
        return user
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, 'Sessão inválida ou expirada')

def allow(user, roles):
    if user.perfil not in roles:
        raise HTTPException(403, 'Acesso não autorizado')

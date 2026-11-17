"""Login seguro e demonstrativo usam o mesmo usuário e as mesmas permissões."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
import jwt
from pwdlib.exceptions import UnknownHashError
from sqlalchemy.orm import Session

from ..core import config
from ..core.security import password_hash
from ..repositories.sql_repository import user_by_email
from ..schemas import Login
from ..views.serializers import public


def authenticate(data: Login, db: Session) -> dict:
    user = user_by_email(db, data.email)
    valid = bool(user and user.ativo)
    if valid and not config.MODO_DEMO:
        try:
            valid = bool(data.senha) and password_hash.verify(data.senha, user.senha_hash)
        except (UnknownHashError, ValueError):
            valid = False
    if not valid:
        raise HTTPException(401, 'E-mail ou senha incorretos')
    token = jwt.encode({
        'sub': str(user.id),
        'exp': datetime.now(timezone.utc) + timedelta(hours=8),
        'auth_mode': 'demo' if config.MODO_DEMO else 'password',
    }, config.JWT_SECRET, algorithm='HS256')
    return {'access_token': token, 'token_type': 'bearer', 'usuario': public(user)}

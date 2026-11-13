from urllib.parse import urlsplit
from uuid import UUID
from fastapi import HTTPException
from ..core.config import FRONTEND_URL
from ..models import Equipment
from ..repositories.sql_repository import one

def resolve(db, identifier):
    if str(identifier).isdigit():
        column, value = 'id', int(identifier)
    else:
        try: value = str(UUID(str(identifier)))
        except ValueError: raise HTTPException(404, 'Equipamento não encontrado')
        column = 'public_id'
    equipment = one(db, Equipment, f'SELECT * FROM equipamentos WHERE {column}=:value', {'value': value})
    if not equipment: raise HTTPException(404, 'Equipamento não encontrado')
    return equipment

def public_url(equipment):
    url = urlsplit(FRONTEND_URL)
    if url.scheme != 'https' or not url.hostname or url.hostname in ('localhost', '127.0.0.1', '::1') or url.username or url.password or url.query or url.fragment:
        raise HTTPException(503, 'Configure FRONTEND_URL com o domínio HTTPS público para emitir etiquetas.')
    return FRONTEND_URL.rstrip('/') + '/equipamentos/' + equipment.public_id

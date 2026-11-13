from sqlalchemy import text
from ..models import now

def record(db, user, entity, record_id, event, description):
    db.execute(text('INSERT INTO auditoria (usuario_id,entidade,registro_id,tipo,descricao,criado_em) VALUES (:user,:entity,:id,:event,:description,:created)'), {'user':user.id,'entity':entity,'id':record_id,'event':event,'description':description,'created':now()})

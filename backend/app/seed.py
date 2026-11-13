"""Carga SQL explícita, atômica e idempotente de dados fictícios no SQLite."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import text
from .database import initialize_database, Session
from .core.security import password_hash

VERSION = 'demo-mvc-v1'

def seed(*, allow_production=False):
    from .core.config import ENVIRONMENT, EPHEMERAL_SQLITE
    if ENVIRONMENT == 'production' and not (allow_production and EPHEMERAL_SQLITE):
        raise RuntimeError('Carga demonstrativa bloqueada em produção')
    initialize_database()
    with Session.begin() as db:
        if db.execute(text('SELECT 1 FROM seed_versions WHERE version = :version'), {'version': VERSION}).scalar():
            return 'Carga demonstrativa já aplicada; nenhum dado alterado.'
        if db.execute(text('SELECT COUNT(*) FROM usuarios')).scalar_one():
            return 'Banco já possui usuários; dados existentes preservados. Use um banco vazio para a nova demonstração.'
        reference = datetime.now(timezone.utc)
        params = {f'senha_{i}': password_hash.hash('Demo@12345') for i in range(1, 9)}
        for i in range(1, 16):
            opened = reference - timedelta(days=17-i)
            for key, hours in [('abertura',0),('atribuicao',1),('inicio',2),('conclusao',5),('comentario',0.5)]:
                params[f'{key}_{i}'] = (opened + timedelta(hours=hours)).isoformat()
        script = (Path(__file__).resolve().parent.parent / 'sql' / 'seed_demo.sql').read_text()
        for statement in script.split(';'):
            if statement.strip():
                db.execute(text(statement), params)
        from uuid import uuid4
        for id in db.execute(text('SELECT id FROM equipamentos WHERE public_id IS NULL')).scalars():
            db.execute(text('UPDATE equipamentos SET public_id=:value WHERE id=:id'), {'value': str(uuid4()), 'id': id})
        db.execute(text('INSERT INTO seed_versions (version, aplicado_em) VALUES (:version, :data)'),
                   {'version': VERSION, 'data': reference.isoformat()})
    return 'Demonstração criada: 8 usuários, 3 setores, 8 equipamentos, 15 chamados e 8 ordens.'

if __name__ == '__main__':
    print(seed())

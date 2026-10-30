import os
import tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
os.environ['JWT_SECRET']='test-only-secret-with-more-than-32-characters'
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pytest
from app.main import app
from app.seed import seed
from app.database import Session

@pytest.fixture
def client():
    with TestClient(app) as c:
        # Cada teste começa com a mesma base, sem depender da ordem de execução.
        from app.database import engine
        assert Path(engine.url.database).name == 'test.db'
        with Session.begin() as db:
            for table in ['historico', 'ordens', 'chamados', 'equipamentos', 'setores', 'usuarios', 'seed_versions']:
                db.execute(text(f'DELETE FROM {table}'))
        seed()
        yield c

def auth(c,name):
    r=c.post('/auth/login',json={'email':name+'@industrack.local','senha':'Demo@12345'})
    assert r.status_code==200
    return {'Authorization':'Bearer '+r.json()['access_token']}

def test_full_workflow(client):
    c=client; op=auth(c,'operador'); supervisor=auth(c,'supervisor'); tech=auth(c,'tecnico')
    r=c.post('/chamados',headers=op,json={'titulo':'Vazamento de óleo','descricao':'Vazamento na conexão hidráulica','equipamento_id':1})
    assert r.status_code==201
    id=r.json()['id']
    assert c.patch(f'/chamados/{id}/atribuir',headers=op,json={'tecnico_id':3}).status_code==403
    assert c.get(f'/chamados/{id}',headers=auth(c,'operador2')).status_code==403
    assert c.patch(f'/chamados/{id}/atribuir',headers=supervisor,json={'tecnico_id':3,'prioridade':'Alta'}).status_code==200
    r=c.post('/ordens-servico',headers=supervisor,json={'chamado_id':id}); assert r.status_code==201
    oid=r.json()['id']
    assert c.post('/ordens-servico',headers=supervisor,json={'chamado_id':id}).status_code==409
    done={'diagnostico':'Vedação danificada','solucao':'Vedação substituída e equipamento inspecionado'}
    assert c.patch(f'/ordens-servico/{oid}/concluir',headers=tech,json=done).status_code==409
    assert c.patch(f'/ordens-servico/{oid}/iniciar',headers=auth(c,'tecnico2')).status_code==403
    assert c.patch(f'/ordens-servico/{oid}/iniciar',headers=tech).status_code==200
    assert c.patch(f'/ordens-servico/{oid}/concluir',headers=tech,json={'diagnostico':'','solucao':''}).status_code==422
    assert c.patch(f'/ordens-servico/{oid}/concluir',headers=tech,json=done).status_code==200
    assert c.patch(f'/ordens-servico/{oid}/iniciar',headers=tech).status_code==409
    assert c.post(f'/chamados/{id}/comentarios',headers=op,json={'mensagem':'Funcionamento normalizado.'}).status_code==201
    t=c.get(f'/chamados/{id}',headers=op).json()
    assert t['status']=='Resolvido' and t['resolvido_em'] and len(t['historico'])==6
    assert any(x['mensagem'].startswith('Concluído') for x in c.get('/equipamentos/1/historico',headers=op).json()['historico'])
    summary=c.get('/dashboard/resumo',headers=supervisor).json()
    assert summary['total']==16
    assert next(x for x in summary['status'] if x['nome']=='Resolvido')['quantidade']==4

def test_auth_equipment_integrity(client):
    c=client
    assert c.get('/equipamentos').status_code in (401,403)
    assert c.post('/auth/login',json={'email':'admin@industrack.local','senha':'wrong'}).status_code==401
    body={'codigo':'TEST-001','nome':'Equipamento teste','setor_id':1}
    assert c.post('/equipamentos',headers=auth(c,'operador'),json=body).status_code==403
    assert c.post('/equipamentos',headers=auth(c,'admin'),json=body).status_code==201
    assert c.post('/equipamentos',headers=auth(c,'admin'),json=body).status_code==409
    body['setor_id']=999
    assert c.post('/equipamentos',headers=auth(c,'admin'),json=body).status_code==404
    with Session() as db:
        assert db.execute(text('PRAGMA foreign_keys')).scalar()==1
        with pytest.raises(IntegrityError):
            db.execute(text('DELETE FROM setores WHERE id=1'))
        db.rollback()
    seed()
    assert len(c.get('/usuarios',headers=auth(c,'admin')).json())==8


def test_sql_filters_and_injection(client):
    c = client
    supervisor = auth(c, 'supervisor')
    result = c.get('/chamados', headers=supervisor, params={'q': "' OR 1=1 --"}).json()
    assert result == {'items': [], 'total': 0}
    result = c.get('/chamados', headers=supervisor, params={'status': 'Resolvido', 'equipamento_id': 1}).json()
    assert result['total'] == 1
    assert all(t['status'] == 'Resolvido' and t['equipamento_id'] == 1 for t in result['items'])
    assert c.get('/chamados', headers=supervisor, params={'page': 2}).json()['items'] == []
    operator = auth(c, 'operador2')
    summary = c.get('/dashboard/resumo', headers=operator).json()
    tickets = c.get('/chamados', headers=operator).json()
    assert summary['total'] == tickets['total'] == 5
    assert all(t['solicitante_id'] == 7 for t in tickets['items'])
    assert 'senha_hash' not in c.get('/auth/me', headers=operator).json()


def test_mock_seed_is_persistent_and_idempotent(client):
    with Session() as db:
        before = {table: db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()
                  for table in ['usuarios', 'setores', 'equipamentos', 'chamados', 'ordens', 'historico']}
    seed()
    with Session() as db:
        after = {table: db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one() for table in before}
        assert before == after
        assert db.execute(text('SELECT COUNT(DISTINCT status) FROM chamados')).scalar_one() == 4
        assert db.execute(text('SELECT COUNT(*) FROM ordens WHERE status = :status'), {'status': 'Concluída'}).scalar_one() == 3
        assert db.execute(text('SELECT COUNT(*) FROM seed_versions')).scalar_one() == 1
        assert not db.execute(text("SELECT COUNT(*) FROM usuarios WHERE senha_hash = 'Demo@12345'")).scalar_one()


def test_order_and_history_rollback_together(client, monkeypatch):
    from app.services import orders
    technician = auth(client, 'tecnico')
    def failed_audit(*args, **kwargs):
        raise RuntimeError('Falha simulada na gravação do histórico')
    monkeypatch.setattr(orders, 'log', failed_audit)
    with pytest.raises(RuntimeError, match='Falha simulada'):
        client.patch('/ordens-servico/7/iniciar', headers=technician)
    with Session() as db:
        assert db.execute(text('SELECT status FROM ordens WHERE id = 7')).scalar_one() == 'Pendente'
        assert db.execute(text('SELECT status FROM chamados WHERE id = 7')).scalar_one() == 'Em análise'

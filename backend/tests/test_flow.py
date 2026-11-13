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
            for table in ['auditoria', 'execucoes', 'preventivas', 'notificacoes', 'historico', 'ordens', 'chamados', 'equipamentos', 'setores', 'usuarios', 'seed_versions']:
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


def test_qr_identity_and_access(client, monkeypatch):
    from app.services import equipment
    from app.database import initialize_database
    operator=auth(client,'operador')
    before=client.get('/equipamentos',headers=operator).json()
    assert len({e['public_id'] for e in before})==len(before)
    initialize_database()
    after=client.get('/equipamentos',headers=operator).json()
    assert [e['public_id'] for e in before]==[e['public_id'] for e in after]
    id=before[0]['public_id']
    assert client.get('/equipamentos/'+id,headers=operator).json()['id']==before[0]['id']
    monkeypatch.setattr(equipment,'FRONTEND_URL','http://localhost:5173')
    assert client.get(f'/equipamentos/{id}/qrcode',headers=operator).status_code==503
    monkeypatch.setattr(equipment,'FRONTEND_URL','https://industrial.example.org')
    image=client.get(f'/equipamentos/{id}/qrcode',headers=operator)
    assert image.status_code==200 and image.content.startswith(b'\x89PNG')
    assert client.get(f'/equipamentos/{id}/qrcode').status_code in (401,403)
    assert client.patch('/equipamentos/'+id,headers=operator,json={'status':'Inativo'}).status_code==403


def test_preventive_notifications_report(client):
    supervisor=auth(client,'supervisor'); tech=auth(client,'tecnico'); operator=auth(client,'operador')
    body={'equipamento_id':1,'responsavel_id':3,'atividade':'Inspecionar conexões','frequencia_dias':30,'proxima_execucao':'2026-01-01'}
    assert client.post('/manutencoes',headers=operator,json=body).status_code==403
    response=client.post('/manutencoes',headers=supervisor,json=body)
    assert response.status_code==201
    id=response.json()['id']
    assert client.post(f'/manutencoes/{id}/executar',headers=auth(client,'tecnico2'),json={'mensagem':'Inspeção concluída'}).status_code==403
    assert client.post(f'/manutencoes/{id}/executar',headers=tech,json={'mensagem':'Inspeção concluída'}).status_code==200
    assert len(client.get(f'/manutencoes/{id}/historico',headers=tech).json())==1
    notifications=client.get('/notificacoes',headers=tech).json()
    assert len(notifications)==1
    nid=notifications[0]['id']
    assert client.patch(f'/notificacoes/{nid}/ler',headers=operator).status_code==404
    assert client.patch(f'/notificacoes/{nid}/ler',headers=tech).status_code==200
    assert client.get('/relatorios/chamados.csv',headers=operator).status_code==403
    assert 'Título' in client.get('/relatorios/chamados.csv',headers=supervisor).text
    assert client.get('/health').status_code==200


def test_admin_access_and_audit(client):
    admin=auth(client,'admin'); supervisor=auth(client,'supervisor')
    body={'nome':'Nova Pessoa','email':'nova@example.org','senha':'long-temporary-password','perfil':'tecnico'}
    assert client.post('/usuarios',headers=supervisor,json=body).status_code==403
    response=client.post('/usuarios',headers=admin,json=body);assert response.status_code==201
    uid=response.json()['id'];assert 'senha_hash' not in response.json()
    assert client.patch(f'/usuarios/{uid}',headers=admin,json={'nome':'Nova Pessoa','perfil':'operador','ativo':False}).status_code==200
    assert client.patch('/usuarios/1',headers=admin,json={'nome':'Admin','perfil':'operador','ativo':True}).status_code==409
    assert client.post('/setores',headers=admin,json={'nome':'Novo setor'}).status_code==201
    assert client.patch('/equipamentos/1',headers=admin,json={'descricao':'Inspeção necessária','status':'Inativo'}).status_code==200
    assert client.get('/equipamentos/1/auditoria',headers=admin).json()[-1]['tipo']=='alteracao'


def test_insights_scopes_and_exports(client):
    supervisor=auth(client,'supervisor'); operator=auth(client,'operador2')
    insights=client.get('/dashboard/operacional',headers=operator)
    assert insights.status_code==200
    assert sum(r['quantidade'] for r in insights.json()['chamados_mes'])==5
    assert insights.json()['proximas_preventivas']==[]
    # Um operador não deve encontrar chamado de outro solicitante pela busca global.
    with Session() as db:
        ticket=db.execute(text('SELECT id,titulo FROM chamados WHERE solicitante_id!=7 LIMIT 1')).mappings().one()
    result=client.get('/busca',headers=operator,params={'q':'CH-'+str(ticket['id'])}).json()
    assert not any(r['destino']=='/chamados/'+str(ticket['id']) for r in result)
    for kind in ['chamados','ordens-concluidas','equipamentos-falhas','preventivas-atrasadas','historico-equipamento']:
        assert client.get('/relatorios/'+kind+'.csv',headers=operator).status_code==403
        response=client.get('/relatorios/'+kind+'.csv',headers=supervisor,params={'equipamento_id':1})
        assert response.status_code==200 and 'text/csv' in response.headers['content-type']
        assert client.get('/relatorios/'+kind+'.csv',headers=supervisor,params={'inicio':'2026-12-01','fim':'2026-01-01'}).status_code==422
    result=client.get('/relatorios/chamados.csv',headers=supervisor,params={'equipamento_id':999})
    assert len(result.text.splitlines())==1


def test_reminders_are_deduplicated(client):
    from datetime import date,timedelta
    supervisor=auth(client,'supervisor');tech=auth(client,'tecnico');other=auth(client,'tecnico2')
    response=client.post('/manutencoes',headers=supervisor,json={'equipamento_id':1,'responsavel_id':3,'atividade':'Preventiva vencida','frequencia_dias':30,'proxima_execucao':(date.today()-timedelta(days=2)).isoformat()})
    assert response.status_code==201
    first=client.get('/notificacoes',headers=tech).json()
    second=client.get('/notificacoes',headers=tech).json()
    assert len(first)==len(second)==2
    assert any('atrasada' in n['mensagem'] for n in first)
    assert client.get('/notificacoes/contador',headers=tech).json()['nao_lidas']==2
    assert client.get('/notificacoes',headers=other).json()==[]
    assert client.patch('/notificacoes/ler-todas',headers=tech).status_code==200
    assert client.get('/notificacoes/contador',headers=tech).json()['nao_lidas']==0


def test_edit_cancel_and_deadline(client):
    supervisor=auth(client,'supervisor');tech=auth(client,'tecnico');operator=auth(client,'operador')
    ticket=client.post('/chamados',headers=operator,json={'titulo':'Falha nova','descricao':'Descrição detalhada','equipamento_id':1}).json()
    tid=ticket['id'];edit={'titulo':'Título corrigido','descricao':'Descrição corrigida'}
    assert client.patch(f'/chamados/{tid}',headers=operator,json=edit).status_code==200
    assert client.patch(f'/chamados/{tid}/atribuir',headers=supervisor,json={'tecnico_id':3}).status_code==200
    oid=client.post('/ordens-servico',headers=supervisor,json={'chamado_id':tid}).json()['id']
    assert client.patch(f'/ordens-servico/{oid}/prazo',headers=tech,json={'prazo':'2027-01-01'}).status_code==403
    assert client.patch(f'/ordens-servico/{oid}/prazo',headers=supervisor,json={'prazo':'2027-01-01'}).status_code==200
    assert client.patch(f'/ordens-servico/{oid}/iniciar',headers=tech).status_code==200
    assert client.patch(f'/ordens-servico/{oid}/diagnostico',headers=tech,json={'diagnostico':'Componente avariado'}).status_code==200
    assert client.patch(f'/ordens-servico/{oid}/cancelar',headers=tech,json={'mensagem':'Motivo'}).status_code==403
    assert client.patch(f'/ordens-servico/{oid}/cancelar',headers=supervisor,json={'mensagem':'Equipamento será substituído'}).status_code==200
    assert client.get(f'/chamados/{tid}',headers=operator).json()['status']=='Cancelado'
    assert client.patch(f'/ordens-servico/{oid}/iniciar',headers=tech).status_code==409

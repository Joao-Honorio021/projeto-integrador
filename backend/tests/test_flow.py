import os
import tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
os.environ['JWT_SECRET']='test-only-secret-with-more-than-32-characters'
os.environ['JWT_SECRET_KEY']='test-only-secret-with-more-than-32-characters'
os.environ['ENVIRONMENT']='test'
os.environ['MODO_DEMO']='false'
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

@pytest.mark.parametrize('demo', [False, True])
def test_full_workflow(client, monkeypatch, demo):
    from app.core import config
    monkeypatch.setattr(config, 'MODO_DEMO', demo)
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
    assert c.post('/api/auth/login',json={'email':'admin@industrack.local','senha':'Demo@12345'}).status_code==200
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


def test_equipment_link_qr_and_edit_survive_restart(client, monkeypatch):
    from app.services import equipment
    monkeypatch.setattr(equipment, 'FRONTEND_URL', 'https://industrial.example.org')
    admin = auth(client, 'admin')
    item = client.get('/equipamentos', headers=admin).json()[0]
    path = '/equipamentos/' + item['public_id']
    assert client.patch(path, headers=admin, json={'localizacao': 'Linha persistente'}).status_code == 200
    url = equipment.public_url(type('Equipment', (), item)())
    # Uma nova inicialização deve consultar a mesma identidade e os dados gravados.
    with TestClient(app) as restarted:
        operator = auth(restarted, 'operador')
        response = restarted.get('/api' + path, headers=operator)
        assert response.status_code == 200
        assert response.json()['localizacao'] == 'Linha persistente'
        assert response.json()['public_id'] == item['public_id']
        assert url.endswith(path)
        qr = restarted.get('/api' + path + '/qrcode', headers=operator)
        assert qr.status_code == 200
        assert qr.headers['content-type'] == 'image/png'
        assert qr.content.startswith(b'\x89PNG')
        assert restarted.patch(path, headers=operator, json={'localizacao': 'Proibido'}).status_code == 403


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
    assert client.get('/api/health').status_code==200


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


@pytest.mark.parametrize('name,role', [('admin','administrador'), ('supervisor','supervisor'), ('tecnico','tecnico'), ('operador','operador')])
def test_demo_uses_database_profile_without_hash_verification(client, monkeypatch, name, role):
    from app.core import config
    from app.services.authentication import password_hash
    monkeypatch.setattr(config, 'MODO_DEMO', True)
    def forbidden_verification(*args):
        raise AssertionError('O fluxo demonstrativo não pode comparar hashes')
    monkeypatch.setattr(password_hash, 'verify', forbidden_verification)
    with Session() as db:
        before = db.execute(text('SELECT senha_hash FROM usuarios ORDER BY id')).scalars().all()
    response = client.post('/auth/login', json={'email': '  '+name.upper()+'@INDUSTRACK.LOCAL  ', 'senha': 'qualquer senha'})
    assert response.status_code == 200
    assert response.json()['usuario']['perfil'] == role
    headers = {'Authorization': 'Bearer '+response.json()['access_token']}
    assert client.get('/auth/me', headers=headers).json()['perfil'] == role
    assert client.get('/auth/config').json() == {'modo_demo': True}
    assert client.post('/auth/login', json={'email': name+'@industrack.local'}).status_code == 200
    with Session() as db:
        assert db.execute(text('SELECT senha_hash FROM usuarios ORDER BY id')).scalars().all() == before
    if role != 'administrador':
        assert client.post('/equipamentos', headers=headers, json={'codigo':'DENIED','nome':'Bloqueado','setor_id':1}).status_code == 403
    monkeypatch.setattr(config, 'MODO_DEMO', False)
    assert client.get('/auth/me', headers=headers).status_code == 401


def test_demo_rejects_unknown_inactive_and_client_profile(client, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config, 'MODO_DEMO', True)
    assert client.post('/auth/login', json={'email':'unknown@example.org'}).status_code == 401
    with Session.begin() as db:
        db.execute(text('UPDATE usuarios SET ativo=:active WHERE email=:email'), {'active': False, 'email':'operador@industrack.local'})
    assert client.post('/auth/login', json={'email':'operador@industrack.local'}).status_code == 401
    assert client.post('/auth/login', json={'email':'operador2@industrack.local','perfil':'administrador'}).status_code == 422
    operator = auth(client, 'operador2')
    assert client.get('/chamados/1', headers=operator).status_code == 403


def test_secure_login_handles_legacy_hash_and_preserves_password_spaces(client):
    from app.core.security import password_hash
    assert client.get('/auth/config').json() == {'modo_demo': False}
    assert client.post('/auth/login', json={'email':'admin@industrack.local'}).status_code == 401
    with Session.begin() as db:
        db.execute(text('UPDATE usuarios SET senha_hash=:hash WHERE id=1'), {'hash':'legacy-invalid-hash'})
    assert client.post('/auth/login', json={'email':'admin@industrack.local','senha':'anything'}).status_code == 401
    password = '  a password with spaces  '
    with Session.begin() as db:
        db.execute(text('UPDATE usuarios SET senha_hash=:hash WHERE id=1'), {'hash':password_hash.hash(password)})
    assert client.post('/auth/login', json={'email':'admin@industrack.local','senha':password}).status_code == 200
    assert client.post('/auth/login', json={'email':'admin@industrack.local','senha':password.strip()}).status_code == 401


def test_unavailable_database_returns_sanitized_503(client, monkeypatch):
    from app.services import authentication
    from sqlalchemy.exc import OperationalError
    def unavailable(*args):
        raise OperationalError('private SQL', {}, Exception('private-password'))
    monkeypatch.setattr(authentication, 'user_by_email', unavailable)
    response = client.post('/auth/login', json={'email':'admin@industrack.local','senha':'x'})
    assert response.status_code == 503
    assert 'private' not in response.text


def test_inactive_and_missing_equipment(client):
    admin = auth(client, 'admin')
    operator = auth(client, 'operador')
    assert client.get('/equipamentos/not-a-uuid', headers=operator).status_code == 404
    assert client.get('/equipamentos/00000000-0000-0000-0000-000000000000', headers=operator).status_code == 404
    assert client.patch('/equipamentos/1', headers=admin, json={'status':'Inativo'}).status_code == 200
    assert client.post('/chamados', headers=operator, json={'titulo':'Teste inativo','descricao':'Descrição suficiente','equipamento_id':1}).status_code == 409


def test_cors_uses_explicit_frontend_origins(client):
    from app.core.config import CORS_ORIGINS
    for origin in CORS_ORIGINS:
        response = client.options('/auth/login', headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'Content-Type'})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == origin
    assert 'access-control-allow-origin' not in client.get('/health', headers={'Origin':'https://untrusted.example'}).headers


def test_postgres_startup_never_applies_migrations(client, monkeypatch):
    from app import main
    from types import SimpleNamespace
    disposed = []
    def unexpected_migration():
        raise AssertionError('PostgreSQL não deve ser migrado no startup')
    monkeypatch.setattr(main, 'ENVIRONMENT', 'development')
    monkeypatch.setattr(main, 'initialize_database', unexpected_migration)
    monkeypatch.setattr(main, 'engine', SimpleNamespace(dialect=SimpleNamespace(name='postgresql'), dispose=lambda: disposed.append(True)))
    with TestClient(app):
        pass
    assert disposed == [True]


def test_requester_technician_can_follow_created_ticket(client):
    tech = auth(client, 'tecnico')
    response = client.post('/chamados', headers=tech, json={
        'titulo': 'Falha observada pelo técnico', 'descricao': 'Motor com ruído anormal',
        'equipamento_id': 1,
    })
    assert response.status_code == 201
    tid = response.json()['id']
    assert client.get(f'/chamados/{tid}', headers=tech).status_code == 200
    assert tid in [t['id'] for t in client.get('/chamados', headers=tech).json()['items']]
    assert client.get(f'/chamados/{tid}', headers=auth(client, 'tecnico2')).status_code == 403
    with Session() as db:
        assert db.execute(text('SELECT solicitante_id FROM chamados WHERE id=:id'), {'id': tid}).scalar_one() == 3
        assert db.execute(text('SELECT COUNT(*) FROM historico WHERE chamado_id=:id'), {'id': tid}).scalar_one() == 1
        assert db.execute(text('SELECT COUNT(*) FROM notificacoes WHERE destino=:path'), {'path': f'/chamados/{tid}'}).scalar_one() == 2


@pytest.mark.parametrize('changes', [
    {'equipamento_id': 0}, {'equipamento_id': -1}, {'categoria': '   '},
    {'titulo': 'ab'}, {'descricao': 'abcd'}, {'prioridade': 'Urgente'},
    {'solicitante_id': 7},
])
def test_ticket_invalid_payload_is_atomic(client, changes):
    operator = auth(client, 'operador')
    with Session() as db:
        before = {table: db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()
                  for table in ('chamados', 'historico', 'notificacoes')}
    body = {'titulo': 'Falha válida', 'descricao': 'Descrição completa', 'equipamento_id': 1, **changes}
    assert client.post('/chamados', headers=operator, json=body).status_code == 422
    with Session() as db:
        assert before == {table: db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one() for table in before}


def test_ticket_notification_failure_rolls_back_ticket_and_history(client, monkeypatch):
    from app.services import notifications
    def fail(*args):
        raise RuntimeError('Falha isolada de notificação')
    monkeypatch.setattr(notifications, 'managers', fail)
    with Session() as db:
        before = db.execute(text('SELECT COUNT(*) FROM chamados')).scalar_one()
        history = db.execute(text('SELECT COUNT(*) FROM historico')).scalar_one()
    with pytest.raises(RuntimeError, match='Falha isolada'):
        client.post('/chamados', headers=auth(client, 'operador'), json={
            'titulo': 'Falha de transação', 'descricao': 'Não deve persistir parcialmente', 'equipamento_id': 1})
    with Session() as db:
        assert db.execute(text('SELECT COUNT(*) FROM chamados')).scalar_one() == before
        assert db.execute(text('SELECT COUNT(*) FROM historico')).scalar_one() == history


def test_inactive_assignee_cannot_receive_new_order(client):
    supervisor = auth(client, 'supervisor')
    response = client.post('/chamados', headers=auth(client, 'operador'), json={
        'titulo': 'Atribuição desatualizada', 'descricao': 'Técnico foi desativado após atribuição', 'equipamento_id': 1})
    tid = response.json()['id']
    assert client.patch(f'/chamados/{tid}/atribuir', headers=supervisor, json={'tecnico_id': 3}).status_code == 200
    assert client.patch('/usuarios/3', headers=auth(client, 'admin'), json={
        'nome': 'Técnico inativo', 'perfil': 'tecnico', 'ativo': False}).status_code == 200
    assert client.post('/ordens-servico', headers=supervisor, json={'chamado_id': tid}).status_code == 409


@pytest.mark.parametrize('public_id', [None, '', 'null', 'undefined', 'invalid'])
def test_legacy_equipment_identity_never_generates_invalid_links(client, monkeypatch, public_id):
    from app.services import equipment
    from app.models import Equipment
    monkeypatch.setattr(equipment, 'FRONTEND_URL', 'https://industrial.example.org')
    with Session.begin() as db:
        db.execute(text('UPDATE equipamentos SET public_id=:value WHERE id=1'), {'value': public_id})
    operator = auth(client, 'operador')
    item = client.get('/equipamentos/1', headers=operator).json()
    assert equipment.public_url(Equipment(**item)).endswith('/equipamentos/1')
    results = client.get('/busca', headers=operator, params={'q': item['codigo']}).json()
    assert any(r['destino'] == '/equipamentos/1' for r in results)
    assert client.get('/equipamentos/null', headers=operator).status_code == 404


def test_search_order_opens_specific_order(client):
    supervisor = auth(client, 'supervisor')
    order = client.get('/ordens-servico', headers=supervisor).json()[0]
    results = client.get('/busca', headers=supervisor, params={'q': f'OS-{order["id"]}'}).json()
    assert any(r['destino'] == f'/ordens?id={order["id"]}' for r in results)


def test_notification_destination_is_checked_against_current_access(client):
    from app.services.notifications import notify
    operator = auth(client, 'operador2')
    with Session.begin() as db:
        notify(db, 7, 'Chamado sem permissão', '/chamados/1')
        notify(db, 7, 'Chamado removido', '/chamados/999999')
        notify(db, 7, 'Link inválido', '/equipamentos/null')
        notify(db, 7, 'Link externo', 'https://example.org')
        notify(db, 7, 'Equipamento disponível', '/equipamentos/1')
    items = client.get('/notificacoes', headers=operator).json()
    assert next(n for n in items if n['mensagem'] == 'Equipamento disponível')['destino'] == '/equipamentos/1'
    assert all(n['destino'] is None for n in items if n['mensagem'] != 'Equipamento disponível')
    assert client.get('/chamados/1', headers=operator).status_code == 403


def test_notification_count_includes_older_items_and_read_is_isolated(client):
    from app.services.notifications import notify
    operator = auth(client, 'operador')
    uid = client.get('/auth/me', headers=operator).json()['id']
    with Session.begin() as db:
        for i in range(105):
            notify(db, uid, f'Evento de teste {i}', '/equipamentos/1')
    assert len(client.get('/notificacoes', headers=operator).json()) == 100
    assert client.get('/notificacoes/contador', headers=operator).json()['nao_lidas'] == 105
    nid = client.get('/notificacoes', headers=operator).json()[0]['id']
    assert client.patch(f'/notificacoes/{nid}/ler', headers=auth(client, 'operador2')).status_code == 404
    assert client.patch(f'/notificacoes/{nid}/ler', headers=operator).status_code == 200
    assert client.patch(f'/notificacoes/{nid}/ler', headers=operator).status_code == 200
    assert client.get('/notificacoes/contador', headers=operator).json()['nao_lidas'] == 104
    assert client.patch('/notificacoes/ler-todas', headers=operator).status_code == 200
    assert client.get('/notificacoes/contador', headers=operator).json()['nao_lidas'] == 0


def test_equipment_ticket_lifecycle_with_real_generated_ids(client, monkeypatch):
    from app.services import equipment
    from app.models import Equipment
    from uuid import uuid4
    admin = auth(client, 'admin')
    operator = auth(client, 'operador')
    tech = auth(client, 'tecnico')
    sector = client.post('/setores', headers=admin, json={'nome': 'Setor de regressão'}).json()
    created = client.post('/equipamentos', headers=admin, json={
        'codigo': 'REG-' + uuid4().hex[:12], 'nome': 'Equipamento de regressão', 'setor_id': sector['id']})
    assert created.status_code == 201
    item = created.json()
    path = '/equipamentos/' + item['public_id']
    assert client.get(path, headers=operator).json()['id'] == item['id']
    assert client.patch(path, headers=admin, json={'localizacao': 'Linha de regressão'}).status_code == 200
    assert client.get(path, headers=operator).json()['localizacao'] == 'Linha de regressão'
    assert client.patch(path, headers=admin, json={'setor_id': 999999}).status_code == 404
    assert client.patch(path, headers=admin, json={'nome': None}).status_code == 422
    monkeypatch.setattr(equipment, 'FRONTEND_URL', 'https://industrial.example.org')
    assert equipment.public_url(Equipment(**item)).endswith(path)
    assert client.get(path + '/qrcode', headers=operator).content.startswith(b'\x89PNG')
    before = client.get('/dashboard/resumo', headers=operator).json()['total']
    response = client.post('/chamados', headers=operator, json={
        'titulo': 'Ocorrência via equipamento', 'descricao': 'Solicitação de inspeção completa', 'equipamento_id': item['id']})
    assert response.status_code == 201
    tid = response.json()['id']
    assert client.get('/dashboard/resumo', headers=operator).json()['total'] == before + 1
    filtered = client.get('/chamados', headers=operator, params={'equipamento_id': item['id'], 'prioridade': 'Média'}).json()
    assert [t['id'] for t in filtered['items']] == [tid]
    assert client.get(path + '/historico', headers=operator).json()['chamados'][0]['id'] == tid
    tech_id = client.get('/auth/me', headers=tech).json()['id']
    assert client.patch(f'/chamados/{tid}/atribuir', headers=admin, json={'tecnico_id': tech_id}).status_code == 200
    response = client.post('/ordens-servico', headers=admin, json={'chamado_id': tid})
    assert response.status_code == 201
    oid = response.json()['id']
    opath = f'/ordens-servico/{oid}'
    assert client.patch(opath + '/pausar', headers=tech).status_code == 409
    assert client.patch(opath + '/iniciar', headers=operator).status_code == 403
    assert client.patch(opath + '/iniciar', headers=tech).status_code == 200
    first_start = client.get('/ordens-servico', headers=tech).json()[0]['inicio']
    assert client.patch(opath + '/pausar', headers=tech).status_code == 200
    assert client.patch(opath + '/iniciar', headers=tech).json()['inicio'] == first_start
    assert client.patch(opath + '/diagnostico', headers=tech, json={'diagnostico': 'Conexão defeituosa'}).status_code == 200
    assert client.patch(opath + '/concluir', headers=tech, json={'diagnostico': 'Conexão defeituosa', 'solucao': 'Conexão substituída'}).status_code == 200
    assert client.get(f'/chamados/{tid}', headers=operator).json()['status'] == 'Resolvido'
    assert client.get(path + '/ordens', headers=operator).json()[0]['id'] == oid
    notices = client.get('/notificacoes', headers=operator).json()
    assert any(n['destino'] == f'/chamados/{tid}' and 'resolvido' in n['mensagem'] for n in notices)
    assert client.patch(path, headers=admin, json={'status': 'Inativo'}).status_code == 200
    assert client.post('/chamados', headers=operator, json={
        'titulo': 'Equipamento desativado', 'descricao': 'Não pode criar um novo chamado', 'equipamento_id': item['id']}).status_code == 409
    with Session() as db:
        assert db.execute(text('SELECT setor_id FROM equipamentos WHERE id=:id'), {'id': item['id']}).scalar_one() == sector['id']
        assert db.execute(text('SELECT status FROM chamados WHERE id=:id'), {'id': tid}).scalar_one() == 'Resolvido'
        assert db.execute(text('SELECT solucao FROM ordens WHERE id=:id'), {'id': oid}).scalar_one() == 'Conexão substituída'


def test_old_assignment_notification_is_unavailable_after_reassignment(client):
    admin = auth(client, 'admin')
    tech = auth(client, 'tecnico')
    other = auth(client, 'tecnico2')
    tid = client.post('/chamados', headers=auth(client, 'operador'), json={
        'titulo': 'Reatribuição de atendimento', 'descricao': 'Mudança do responsável pelo atendimento', 'equipamento_id': 1}).json()['id']
    first_id = client.get('/auth/me', headers=tech).json()['id']
    other_id = client.get('/auth/me', headers=other).json()['id']
    assert client.patch(f'/chamados/{tid}/atribuir', headers=admin, json={'tecnico_id': first_id}).status_code == 200
    assert client.get('/notificacoes', headers=tech).json()[0]['destino'] == f'/chamados/{tid}'
    assert client.patch(f'/chamados/{tid}/atribuir', headers=admin, json={'tecnico_id': other_id}).status_code == 200
    assert client.get('/notificacoes', headers=tech).json()[0]['destino'] is None
    assert client.get(f'/chamados/{tid}', headers=tech).status_code == 403
    assert client.get('/notificacoes', headers=other).json()[0]['destino'] == f'/chamados/{tid}'

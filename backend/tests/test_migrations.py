"""Adota um banco legado e preserva cada linha, inclusive históricos e senhas hash."""
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config

def test_legacy_migration_preserves_records(tmp_path):
    root=Path(__file__).resolve().parents[1]
    engine=create_engine('sqlite:///'+str(tmp_path/'legacy.db'))
    config=Config(str(root/'alembic.ini'));config.set_main_option('script_location',str(root/'migrations'))
    with engine.begin() as connection:
        config.attributes['connection']=connection
        command.upgrade(config,'0001')
        connection.execute(text("INSERT INTO usuarios (id,nome,email,senha_hash,perfil,ativo) VALUES (1,'Legado','legacy@example.org','hash-preservado','tecnico',1)"))
        connection.execute(text("INSERT INTO setores (id,nome) VALUES (1,'Produção')"))
        connection.execute(text("INSERT INTO equipamentos (id,codigo,nome,modelo,fabricante,localizacao,setor_id,criticidade,status,ativo) VALUES (1,'LEG-01','Prensa','M1','Fabricante','Linha 1',1,'Alta','Operacional',1)"))
        connection.execute(text("INSERT INTO chamados (id,titulo,descricao,equipamento_id,solicitante_id,tecnico_id,categoria,prioridade,status,criado_em) VALUES (1,'Chamado legado','Registro preservado',1,1,1,'Falha','Alta','Em atendimento','2025-01-01')"))
        connection.execute(text("INSERT INTO ordens (id,chamado_id,tecnico_id,status,diagnostico,solucao,criado_em) VALUES (1,1,1,'Em execução','Diagnóstico original','','2025-01-01')"))
        connection.execute(text("INSERT INTO historico (id,chamado_id,usuario_id,mensagem,tipo,criado_em) VALUES (1,1,1,'Histórico preservado','evento','2025-01-01')"))
        tables=['usuarios','setores','equipamentos','chamados','ordens','historico']
        before={t:[dict(r) for r in connection.execute(text('SELECT * FROM '+t)).mappings()] for t in tables}
        # Simula base anterior ao Alembic: tabelas já existem, sem carimbo de revisão.
        connection.execute(text('DELETE FROM alembic_version'))
        command.upgrade(config,'head')
        for table in tables:
            after=[dict(r) for r in connection.execute(text('SELECT * FROM '+table)).mappings()]
            assert [{k:r[k] for k in before[table][0]} for r in after]==before[table]
        identifier=connection.execute(text('SELECT public_id FROM equipamentos')).scalar_one()
        command.upgrade(config,'head')
        assert connection.execute(text('SELECT public_id FROM equipamentos')).scalar_one()==identifier
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()=='0004'
    engine.dispose()

"""Inspeção explícita, somente leitura, antes de aplicar migrações em PostgreSQL.

Execute: python -m app.check_database
Não imprime registros, senhas, hashes ou a URL de conexão.
"""
import json

from sqlalchemy import Boolean, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .database import engine
from .models import User, Sector, Equipment, Ticket, Order, Activity


def inspect_database(connection) -> dict:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    report = {'connected': True, 'dialect': connection.dialect.name, 'tables': {}, 'issues': []}
    if connection.dialect.name == 'postgresql':
        report['ssl'] = connection.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')).scalar()
    for model in (User, Sector, Equipment, Ticket, Order, Activity):
        name = model.__tablename__
        if name not in tables:
            report['issues'].append(f'Tabela ausente: {name}')
            continue
        columns = inspector.get_columns(name)
        report['tables'][name] = {
            'columns': [{'name': c['name'], 'type': str(c['type']), 'nullable': c['nullable'],
                         'has_default': bool(c.get('default') or c.get('identity'))} for c in columns],
            'foreign_keys': inspector.get_foreign_keys(name),
        }
        missing = set(model.__table__.columns.keys()) - {c['name'] for c in columns}
        report['issues'].extend(f'Coluna ausente: {name}.{column}' for column in sorted(missing))
        if connection.dialect.name == 'postgresql':
            for column in columns:
                if column['name'] == 'ativo' and not isinstance(column['type'], Boolean):
                    report['issues'].append(f'Tipo incompatível: {name}.ativo precisa ser BOOLEAN')
    for name in ('preventivas', 'execucoes', 'notificacoes', 'auditoria', 'alembic_version'):
        if name not in tables:
            report['issues'].append(f'Tabela ausente: {name}')
    if 'alembic_version' in tables:
        report['revision'] = connection.execute(text('SELECT version_num FROM alembic_version')).scalar()
    if connection.dialect.name == 'postgresql':
        report['sequences'] = sequence_status(connection)
        for item in report['sequences']:
            if item['sequence'] is None or item['next_id'] <= item['max_id']:
                report['issues'].append(f'Geração de IDs precisa de revisão: {item["table"]}')
    return report


def sequence_status(connection) -> list[dict]:
    """Nomes vêm de tabelas conhecidas e do catálogo; nunca da entrada HTTP."""
    inspector = inspect(connection)
    quote = connection.dialect.identifier_preparer.quote
    result = []
    for table in ('usuarios', 'setores', 'equipamentos', 'chamados', 'ordens', 'historico',
                  'preventivas', 'execucoes', 'notificacoes', 'auditoria'):
        if not inspector.has_table(table):
            continue
        sequence = connection.execute(text('SELECT pg_get_serial_sequence(:table, :column)'),
                                      {'table': table, 'column': 'id'}).scalar()
        item = {'table': table, 'sequence': sequence,
                'max_id': connection.execute(text(f'SELECT COALESCE(MAX(id), 0) FROM {quote(table)}')).scalar_one()}
        if sequence:
            schema, name, increment = connection.execute(text('''
                SELECT n.nspname, c.relname, s.seqincrement FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_sequence s ON s.seqrelid=c.oid
                WHERE c.oid=CAST(:sequence AS regclass)
            '''), {'sequence': sequence}).one()
            value, called = connection.execute(text(f'SELECT last_value,is_called FROM {quote(schema)}.{quote(name)}')).one()
            item['next_id'] = value + increment if called else value
            item['increment'] = increment
        result.append(item)
    return result


def main() -> None:
    try:
        with engine.connect() as connection, connection.begin():
            if engine.dialect.name == 'postgresql':
                connection.execute(text('SET TRANSACTION READ ONLY'))
            report = inspect_database(connection)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        if report['issues']:
            raise SystemExit(1)
    except SQLAlchemyError as exc:
        print(json.dumps({'connected': False, 'error_type': type(exc).__name__,
                          'detail': 'Verifique DATABASE_URL, rede, SSL e permissões. Nenhum dado foi alterado.'}))
        raise SystemExit(2) from None
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()

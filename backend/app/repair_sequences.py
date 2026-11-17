"""Ajuste explícito de sequências após importações com IDs manuais.

Sem argumentos: somente diagnóstico. --apply: avança sequências existentes,
sem alterar IDs, registros ou defaults. Nunca executado no startup.
"""
import argparse
import json
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .check_database import sequence_status
from .database import engine


def repair(connection) -> list[dict]:
    quote = connection.dialect.identifier_preparer.quote
    tables = sequence_status(connection)
    if any(item['sequence'] is None for item in tables):
        raise RuntimeError('Existem IDs sem sequência associada. Revise o schema antes de qualquer ajuste.')
    if any(item['increment'] != 1 for item in tables):
        raise RuntimeError('Sequência com incremento personalizado exige revisão manual.')
    # Bloqueia INSERT/UPDATE concorrentes enquanto consulta MAX(id) e ajusta nextval.
    for item in tables:
        connection.execute(text(f'LOCK TABLE {quote(item["table"])} IN SHARE ROW EXCLUSIVE MODE'))
    changes = []
    for item in sequence_status(connection):
        if item['next_id'] > item['max_id']:
            continue
        next_id = item['max_id'] + 1
        connection.execute(text('SELECT setval(CAST(:sequence AS regclass), :next_id, false)'),
                           {'sequence': item['sequence'], 'next_id': next_id})
        changes.append({'table': item['table'], 'next_id': next_id})
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Avançar somente sequências abaixo do maior ID existente')
    args = parser.parse_args()
    if engine.dialect.name != 'postgresql':
        raise SystemExit('Este comando é exclusivo do PostgreSQL.')
    try:
        with engine.begin() as connection:
            if args.apply:
                connection.execute(text("SET LOCAL lock_timeout = '5s'"))
                result = {'updated': repair(connection)}
            else:
                connection.execute(text('SET TRANSACTION READ ONLY'))
                result = {'sequences': sequence_status(connection), 'changed': False}
        print(json.dumps(result, ensure_ascii=False))
    except (SQLAlchemyError, RuntimeError) as exc:
        # setval não é desfeito por rollback: repetir é seguro porque nunca reduzimos sequências.
        print(json.dumps({'error_type': type(exc).__name__, 'detail': 'Ajuste interrompido. Execute o diagnóstico novamente; nenhum registro foi alterado.'}))
        raise SystemExit(1) from None
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()

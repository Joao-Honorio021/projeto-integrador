"""Configuração centralizada; segredos são lidos somente do ambiente/.env local."""
import logging
import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / '.env')


def boolean_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value not in ('true', 'false'):
        raise RuntimeError(f'{name} deve ser true ou false')
    return value == 'true'


def database_url(value: str) -> str:
    try:
        url = make_url(value)
    except (ArgumentError, ValueError):
        raise RuntimeError('DATABASE_URL inválida; verifique a configuração privada.') from None
    if url.drivername in ('postgres', 'postgresql', 'postgresql+psycopg'):
        url = url.set(drivername='postgresql+psycopg')
        if (url.host or '').endswith(('.supabase.co', '.supabase.com')) and 'sslmode' not in url.query:
            url = url.update_query_dict({'sslmode': 'require'})
    elif url.drivername == 'sqlite':
        if url.database and url.database != ':memory:' and not Path(url.database).is_absolute():
            url = url.set(database=str((BACKEND_DIR / url.database).resolve()))
    else:
        raise RuntimeError('DATABASE_URL deve utilizar PostgreSQL (psycopg) ou SQLite local.')
    return url.render_as_string(hide_password=False)


DATABASE_URL = database_url(os.getenv('DATABASE_URL', f'sqlite:///{BACKEND_DIR / "industrack.db"}'))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip().lower()
if ENVIRONMENT not in ('development', 'test', 'demo', 'production'):
    raise RuntimeError('ENVIRONMENT deve ser development, test, demo ou production')
MODO_DEMO = boolean_env('MODO_DEMO')
if ENVIRONMENT == 'production' and MODO_DEMO:
    raise RuntimeError('MODO_DEMO é proibido em produção. Use um ambiente demo isolado, com dados fictícios.')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
CORS_ORIGINS = [origin.strip().rstrip('/') for origin in os.getenv('CORS_ORIGINS', FRONTEND_URL).split(',') if origin.strip()]
JWT_SECRET = os.getenv('JWT_SECRET_KEY') or os.getenv('JWT_SECRET', '')
if ENVIRONMENT in ('development', 'test') and len(JWT_SECRET) < 32:
    JWT_SECRET = secrets.token_urlsafe(48)
    logging.getLogger(__name__).warning('JWT_SECRET ausente ou curto; usando segredo temporário de desenvolvimento.')

if ENVIRONMENT in ('production', 'demo'):
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != 'postgresql':
        raise RuntimeError('Produção requer PostgreSQL persistente; SQLite temporário invalida os links e QR Codes dos equipamentos.')
    if url.query.get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
        raise RuntimeError('Produção requer SSL no PostgreSQL')
    if len(JWT_SECRET) < 32:
        raise RuntimeError('Configure JWT_SECRET_KEY com pelo menos 32 caracteres.')
    for origin in [FRONTEND_URL, *CORS_ORIGINS]:
        parsed = urlsplit(origin)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.hostname in ('localhost', '127.0.0.1', '::1')
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or '*' in origin):
            raise RuntimeError('Produção requer origens HTTPS explícitas, sem caminhos ou credenciais')
    if not CORS_ORIGINS:
        raise RuntimeError('Configure CORS_ORIGINS explicitamente.')

"""Configuração centralizada, independente do diretório de execução."""
import logging
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BACKEND_DIR / "industrack.db"}')
JWT_SECRET = os.getenv('JWT_SECRET', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
JWT_SECRET = os.getenv('JWT_SECRET_KEY') or JWT_SECRET
if ENVIRONMENT != 'production' and len(JWT_SECRET) < 32:
    JWT_SECRET = secrets.token_urlsafe(48)
    logging.getLogger(__name__).warning(
        'JWT_SECRET ausente ou curto; usando segredo temporário de desenvolvimento. '
        'Configure um segredo próprio para manter sessões entre reinicializações.'
    )
CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', FRONTEND_URL).split(',') if origin.strip()]
EPHEMERAL_SQLITE = (
    os.getenv('VERCEL', '').lower() in ('1', 'true')
    and os.getenv('ALLOW_EPHEMERAL_SQLITE', '').lower() == 'true'
    and DATABASE_URL.startswith('sqlite:////tmp/')
)

if ENVIRONMENT == 'production':
    from urllib.parse import urlsplit, parse_qs
    if not DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg://')) and not EPHEMERAL_SQLITE:
        raise RuntimeError('Produção requer PostgreSQL')
    if DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg://')) and parse_qs(urlsplit(DATABASE_URL).query).get('sslmode', [''])[0] not in ('require','verify-ca','verify-full'):
        raise RuntimeError('Produção requer SSL no PostgreSQL')
    if not FRONTEND_URL.startswith('https://') or any(not origin.startswith('https://') for origin in CORS_ORIGINS):
        raise RuntimeError('Produção requer origens HTTPS explícitas')

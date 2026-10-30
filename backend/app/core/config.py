"""Configuração centralizada, independente do diretório de execução."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BACKEND_DIR / "industrack.db"}')
JWT_SECRET = os.getenv('JWT_SECRET', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

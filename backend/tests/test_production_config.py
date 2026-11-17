"""Produção não pode aceitar bancos por instância, mesmo com a flag antiga."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


def load_config(database_url, environment='production'):
    env = {
        **os.environ,
        'DATABASE_URL': database_url,
        'ENVIRONMENT': environment,
        'ALLOW_EPHEMERAL_SQLITE': 'true',
        'JWT_SECRET_KEY': 'test-only-secret-with-more-than-32-characters',
        'FRONTEND_URL': 'https://industrial.example.org',
        'CORS_ORIGINS': 'https://industrial.example.org',
    }
    return subprocess.run(
        [sys.executable, '-c', 'from app.core import config'],
        cwd=Path(__file__).resolve().parents[1], env=env,
        capture_output=True, text=True, timeout=10,
    )


@pytest.mark.parametrize('url', ['sqlite:////tmp/industrack.db', 'sqlite:///industrack.db'])
def test_production_rejects_sqlite_even_with_legacy_flag(url):
    result = load_config(url)
    assert result.returncode != 0
    assert 'Produção requer PostgreSQL persistente' in result.stderr


@pytest.mark.parametrize('scheme', ['postgresql', 'postgresql+psycopg'])
def test_production_accepts_persistent_postgres_configuration(scheme):
    result = load_config(f'{scheme}://test:secret@db.example.org/industrack?sslmode=require')
    assert result.returncode == 0, result.stderr


def test_development_keeps_sqlite_support():
    result = load_config('sqlite:///industrack.db', 'development')
    assert result.returncode == 0, result.stderr

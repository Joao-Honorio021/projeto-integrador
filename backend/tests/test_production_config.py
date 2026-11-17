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


def test_production_rejects_demo_mode(monkeypatch):
    monkeypatch.setenv('MODO_DEMO', 'true')
    result = load_config('postgresql://test:secret@db.example.org/test?sslmode=require')
    assert result.returncode != 0
    assert 'MODO_DEMO é proibido em produção' in result.stderr


def test_demo_requires_explicit_environment(monkeypatch):
    monkeypatch.setenv('MODO_DEMO', 'true')
    result = load_config('postgresql://test:secret@db.example.org/test?sslmode=require', 'demo')
    assert result.returncode == 0, result.stderr


def test_supabase_defaults_to_ssl():
    result = load_config('postgresql://postgres:example@db.vcpharygvnbihxmtdsll.supabase.co:5432/postgres')
    assert result.returncode == 0, result.stderr


def test_supabase_explicit_insecure_ssl_rejected():
    result = load_config('postgresql://postgres:example@db.vcpharygvnbihxmtdsll.supabase.co:5432/postgres?sslmode=disable')
    assert result.returncode != 0
    assert 'SSL' in result.stderr


def test_invalid_database_url_does_not_leak_secret():
    result = load_config('sensitive-secret-invalid-url')
    assert result.returncode != 0
    assert 'sensitive-secret' not in result.stderr

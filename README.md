# IndusTrack

Sistema web de suporte técnico e manutenção industrial, desenvolvido para o Projeto Integrador do curso Técnico em Desenvolvimento de Sistemas do SENAI.

Centraliza equipamentos, chamados e ordens de serviço, com histórico de atendimento e indicadores calculados a partir do banco de dados.

## Funcionalidades

- Autenticação e permissões para administrador, supervisor, técnico e operador.
- Cadastro e consulta de equipamentos.
- Abertura de chamados, atribuição de técnicos e comentários.
- Execução de ordens de serviço com diagnóstico e solução.
- Dashboard e histórico dos atendimentos.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Interface | React, TypeScript, Vite e Tailwind CSS |
| API | Python, FastAPI e Pydantic |
| Persistência | SQLite, SQL parametrizado e SQLAlchemy |
| Autenticação | JWT e Argon2 |

A aplicação utiliza uma organização baseada em MVC, com frontend e backend separados. Esta versão é um protótipo local; consulte o [escopo atual](docs/ESCOPO.md) para conhecer as limitações.

## Início rápido

Requisitos: **Python 3.12+** e **Node.js 20.19+**. Os comandos abaixo usam Bash e partem da pasta `industrack`.

**1. Prepare o backend:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Na primeira configuração, substitua o valor de `JWT_SECRET` no `.env` pelo segredo gerado. Preserve o `.env` se já existir.

**2. Carregue a demonstração e inicie a API:**

```bash
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**3. Em outro terminal, inicie a interface:**

```bash
cd frontend
npm ci
npm run dev
```

Acesse a [aplicação](http://127.0.0.1:5173) e a [documentação interativa da API](http://127.0.0.1:8000/docs).

Após executar o seed em um banco vazio, use **admin@industrack.local** com a senha **Demo@12345**. Os demais acessos estão no [guia de uso](docs/GUIA_DE_USO.md).

## Documentação

Consulte o [índice em docs](docs/README.md) para instalação detalhada, arquitetura, banco de dados, API e roteiro de demonstração.

## Verificação

- Na pasta `backend`, com o ambiente virtual ativo: `python -m pytest -q`.
- Na pasta `frontend`: `npm run build`.

## Versão 1.0.2 em desenvolvimento

A evolução inclui migrações Alembic, suporte a Neon PostgreSQL, QR Code, detalhes de equipamentos, preventivas, notificações, CSV e tema escuro. A versão ainda não está liberada para produção.

- [Relatório e matriz de requisitos](docs/RELEASE_1_0_2.md)
- [Preparação para publicação](DEPLOY.md)
- [Histórico de alterações](CHANGELOG.md)

Para atualizar o banco local, faça uma cópia de segurança e execute `alembic upgrade head` na pasta backend com o ambiente virtual ativo. Em produção, migrações são explícitas e o seed é bloqueado. Os guias históricos devem ser lidos em conjunto com o relatório da versão.

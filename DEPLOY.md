# Deploy na Vercel

O IndusTrack usa dois projetos Vercel no mesmo repositório.

- API FastAPI, com Root Directory `backend`
- Frontend React/Vite, com Root Directory `frontend`
- Banco PostgreSQL externo no Neon

## API

Crie um projeto Vercel apontando para o repositório e defina `backend` como **Root Directory**. O arquivo `backend/vercel.json` configura a função Python. A Vercel detecta `app/main.py` como a aplicação FastAPI.

Configure estas variáveis no ambiente Production da API:

```dotenv
DATABASE_URL=postgresql://USUARIO:SENHA@HOST/neondb?sslmode=require
JWT_SECRET_KEY=SEGREDO_ALEATORIO_COM_PELO_MENOS_32_CARACTERES
ENVIRONMENT=production
FRONTEND_URL=https://SEU-FRONTEND.vercel.app
CORS_ORIGINS=https://SEU-FRONTEND.vercel.app
```

Depois do primeiro deploy, execute com as variáveis de produção carregadas:

```bash
alembic upgrade head
python -m app.create_admin
```

O arquivo `.env` e a senha do banco nunca devem ser enviados ao Git.

## Frontend

Crie um segundo projeto Vercel usando o mesmo repositório e defina `frontend` como **Root Directory**. O arquivo `frontend/vercel.json` executa o build e redireciona as rotas do React Router para `index.html`.

Configure no ambiente Production:

```dotenv
VITE_API_URL=https://SEU-BACKEND.vercel.app
```

O valor deve ser apenas a origem pública da API, sem `/api` no final.

## Publicação pelo painel

1. Faça commit e push das alterações para o GitHub.
2. Acesse [vercel.com/new](https://vercel.com/new).
3. Importe o repositório `projeto-integrador`.
4. Crie o projeto da API com Root Directory `backend`.
5. Adicione as cinco variáveis da API.
6. Faça o deploy e teste `https://SEU-BACKEND.vercel.app/health`.
7. Crie o projeto do frontend com Root Directory `frontend`.
8. Configure `VITE_API_URL` com a URL da API.
9. Faça o deploy do frontend.
10. Volte à API e ajuste `FRONTEND_URL` e `CORS_ORIGINS` para o domínio final do frontend.

## Validação local

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

A Vercel executa a API como uma Vercel Function Python. Migrações devem ser aplicadas antes do primeiro uso e não ficam no startup da função em produção.

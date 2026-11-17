# Deploy conjunto na Vercel

Importe a raiz do repositório. O `vercel.json` usa Vercel Services para compilar `frontend/` (Vite) e executar `backend/` (FastAPI, entrypoint `app.main:app`). O projeto precisa ter suporte a Services habilitado.

As rotas `/api` e `/api/*` chegam ao backend; seu middleware existente remove o prefixo. As outras rotas chegam ao frontend, com fallback SPA para manter links de equipamentos e QR Codes ao atualizar a página.

`VITE_API_URL` não é necessária e valores antigos do Render são ignorados. Não configure comandos globais de build que substituam as configurações dos serviços.

## Variáveis privadas na Vercel

- `DATABASE_URL`: PostgreSQL Supabase com `sslmode=require`. Copie o pooler exato do painel Connect; para funções serverless, use Transaction Pooler, porta 6543. O driver já desabilita prepared statements.
- `JWT_SECRET_KEY`: segredo próprio de pelo menos 32 caracteres.
- `ENVIRONMENT=production` e `MODO_DEMO=false`.
- `FRONTEND_URL=https://SEU-PROJETO.vercel.app`.
- `CORS_ORIGINS=https://SEU-PROJETO.vercel.app`.

Senhas na URI devem ser percent-encoded. Nunca coloque credenciais em variáveis VITE. Para demonstração isolada com dados fictícios, as regras existentes permitem `ENVIRONMENT=demo` e `MODO_DEMO=true`.

## Banco e verificação

O startup não cria nem migra PostgreSQL. Com acesso ao banco, execute em `backend`:

```bash
python -m app.check_database
# Após backup e revisão do schema existente:
python -m alembic upgrade head
python -m app.check_database
```

Não execute seed em produção. Preserve registros e UUIDs existentes. Depois do deploy confira `/api/health`, login, equipamentos, QR Code, chamados e ordens. A conexão real com Supabase e o runtime publicado dependem das variáveis privadas e precisam ser homologados no ambiente remoto.

O `render.yaml` fica como configuração alternativa histórica; não é usado pela Vercel.

Referência: https://vercel.com/kb/guide/vercel-services

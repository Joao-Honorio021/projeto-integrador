# Deploy conjunto na Vercel (protótipo)

O `vercel.json` configura frontend e API no mesmo projeto e domínio com Vercel Services. Importe a raiz do repositório, não `frontend` nem `backend`. As Vercel Services podem precisar ser habilitadas na conta.

## Variáveis de ambiente

Configure no ambiente Production:

```dotenv
DATABASE_URL=sqlite:////tmp/industrack.db
ALLOW_EPHEMERAL_SQLITE=true
ENVIRONMENT=production
JWT_SECRET_KEY=SEU_SEGREDO_JA_CONFIGURADO_COM_PELO_MENOS_32_CARACTERES
FRONTEND_URL=https://SEU-PROJETO.vercel.app
CORS_ORIGINS=https://SEU-PROJETO.vercel.app
```

Mantenha o JWT forte que já configurou. Apague `VITE_API_URL` se estiver configurada: o frontend chama `/api` no mesmo domínio. Faça deploy e teste `/api/health`.

O backend aplica as migrações e carrega o seed de demonstração no primeiro startup da função. Acesso inicial: `admin@industrack.local` / `Demo@12345`.

**Limitação:** o banco SQLite fica em `/tmp`, que é temporário e isolado por instância da função Vercel. Dados podem sumir após inicializações frias ou novos deploys. Este modo é somente para executar o protótipo, não para armazenar dados reais.

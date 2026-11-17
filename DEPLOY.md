# Supabase + Render + Vercel

O backend FastAPI fica no Render e o frontend Vite na Vercel. O PostgreSQL é acessado somente pelo backend. Não houve publicação automática nesta revisão.

## 1. Configurar o Supabase

No painel do projeto, abra **Connect** e copie a conexão PostgreSQL. Para conexão direta:

```dotenv
DATABASE_URL=postgresql://postgres:<SENHA>@db.vcpharygvnbihxmtdsll.supabase.co:5432/postgres?sslmode=require
```

Codifique caracteres especiais da senha na URI: espaço `%20`, `@` `%40`, `#` `%23`, `%` `%25`. Não substitua espaços por `+`. Guarde a URL apenas no `.env` ignorado pelo Git ou nas variáveis privadas do Render. Nenhuma chave Supabase deve entrar no React.

A conexão direta normalmente depende de IPv6. Em uma rede somente IPv4, copie **Session pooler**, porta **5432**, do painel:

```dotenv
DATABASE_URL=postgresql://postgres.vcpharygvnbihxmtdsll:<SENHA>@<HOST_EXATO_DO_SESSION_POOLER>:5432/postgres?sslmode=require
```

Não deduza o host do pooler pela região. O projeto mantém um pool SQLAlchemy de até cinco conexões por processo, com timeout, pre-ping e reciclagem. `sslmode=require` é adicionado por padrão aos hosts Supabase; produção recusa SSL desativado. Para validação de certificado, use `verify-full` com o certificado CA do projeto.

## 2. Inspecionar antes de migrar

Em `backend`, com o ambiente virtual ativo e `DATABASE_URL` configurada:

```bash
python -m app.check_database
```

Esse comando usa transação somente leitura no PostgreSQL e informa colunas, tipos, FKs, revisão Alembic, TLS e sequências, sem imprimir registros ou credenciais. Saída 0: nenhum problema detectado pela inspeção; 1: revisar pendências; 2: conexão/consulta falhou. Isso não substitui homologação funcional.

Faça backup e revise as divergências encontradas. Só então execute explicitamente:

```bash
python -m alembic upgrade head
python -m app.check_database
```

O startup nunca migra PostgreSQL, nem mesmo em desenvolvimento. As migrações adotam tabelas e colunas existentes, preenchem apenas `public_id` nulos e preservam os UUIDs já emitidos. Não convertem tipos incompatíveis nem removem dados. Duplicidades de UUID/índices precisam de revisão, sem correção destrutiva automática. Os downgrades antigos continuam bloqueados para evitar perda de dados; restauração requer backup revisado.

Se houve INSERTs com IDs explícitos e o diagnóstico indicar sequência atrasada:

```bash
python -m app.repair_sequences
# Após conferir o diagnóstico e em janela sem importações concorrentes:
python -m app.repair_sequences --apply
```

O ajuste avança somente sequências existentes abaixo do maior ID da tabela, sem alterar registros ou reduzir contadores. Colunas sem sequência/default exigem migração específica após inspeção real. `setval` não sofre rollback: uma falha parcial pode deixar lacunas, mas repetir o comando é seguro. Esses comandos PostgreSQL ainda precisam de homologação no banco acessível.

O seed embutido é exclusivo de SQLite local de desenvolvimento/teste. Ele não é executado no startup nem no deploy. Se um banco vazio precisar do primeiro administrador, execute `python -m app.create_admin` após as migrações.

## 3. Backend no Render

O `render.yaml` descreve o serviço; configure manualmente as variáveis privadas. Não há migração automática no build nem no startup.

| Configuração | Valor |
|---|---|
| Root directory | `backend` |
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/health` |
| `DATABASE_URL` | Conexão privada Supabase com SSL |
| `JWT_SECRET_KEY` | Segredo aleatório de pelo menos 32 caracteres; preserve entre reinícios |
| `ENVIRONMENT` | `production` |
| `MODO_DEMO` | `false` |
| `FRONTEND_URL` | Origem HTTPS definitiva da Vercel, sem caminho |
| `CORS_ORIGINS` | Origens HTTPS explícitas, separadas por vírgula |

`/health` consulta o banco e retorna 503 se ele estiver indisponível, sem revelar detalhes privados. CORS deve incluir o domínio real utilizado; não habilite `*`. Mantenha ambientes Preview separados de dados reais.

## 4. Frontend na Vercel

Importe a **raiz do repositório**. O `vercel.json` instala com `npm ci --prefix frontend`, compila com `npm run build --prefix frontend` e publica `frontend/dist`. A API Python não é mais publicada pela Vercel.

Antes de compilar, configure:

```dotenv
VITE_API_URL=https://seu-backend.onrender.com
```

O build da Vercel recusa a ausência da URL HTTPS. Alterar `VITE_API_URL` exige novo build. O rewrite para `/index.html` permite abrir e atualizar diretamente `/equipamentos/<uuid>`, `/chamados/<id>` e as demais rotas React. Não configure `DATABASE_URL`, senha ou JWT no frontend.

## 5. Demonstração

Local, com banco fictício: `ENVIRONMENT=development` e `MODO_DEMO=true`. Para uma instância hospedada de demonstração isolada: `ENVIRONMENT=demo`, `MODO_DEMO=true`, PostgreSQL fictício, HTTPS e segredo JWT próprio. Produção recusa o modo sem senha.

O login consulta uma conta **ativa e existente** por e-mail; aceita senha vazia ou qualquer texto somente nesse modo. Não cria usuários nem aceita perfil enviado pelo navegador. Sessões continuam assinadas e as permissões são verificadas no backend. Desligar o modo invalida tokens emitidos como demonstração. `MODO_DEMO=false` mantém Argon2 e senha obrigatória. Logout remove o token da sessão do navegador.

## 6. Homologação após configuração

1. Execute a inspeção do banco e confira `/health`.
2. Entre com cada perfil e confira menus e negativas 403 nas ações proibidas.
3. Cadastre um equipamento de teste; confira setor, status, código único e persistência após recarregar.
4. Abra detalhes, baixe o QR e escaneie em celular. O link deve conter o domínio definitivo e o UUID persistido. Uma sessão encerrada deve permitir login sem perder esse endereço.
5. Clique em Registrar ocorrência e confira o equipamento pré-selecionado.
6. Abra o chamado, atribua um técnico como supervisor, crie uma OS, inicie e conclua como técnico; verifique diagnóstico, solução, datas e histórico após recarregar.
7. Repita após reiniciar o backend. Equipamentos inexistentes devem retornar 404; inativos não aceitam novos chamados.

## Referências oficiais consultadas

- [Conexões PostgreSQL e poolers Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [FastAPI no Render](https://render.com/docs/deploy-fastapi)
- [Health checks do Render](https://render.com/docs/health-checks)
- [Vite e rotas SPA na Vercel](https://vercel.com/docs/frameworks/frontend/vite)

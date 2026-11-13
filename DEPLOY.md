# Preparação para Render e Neon

**Ainda não publicado.** Não sincronize o Blueprint sem revisar os requisitos pendentes em [relatório de versão](docs/RELEASE_1_0_2.md).

## Configuração

A raiz Git é a pasta `industrack`; nela está `render.yaml`. O backend utiliza Web Service Python, o frontend usa Static Site. O banco é externo no Neon. As publicações automáticas ficam desligadas.

No backend, configure pelo ambiente:

- `DATABASE_URL`: conexão PostgreSQL do Neon com `sslmode=require` ou validação de certificado mais estrita; não versionar.
- `JWT_SECRET_KEY`: segredo aleatório com pelo menos 32 caracteres.
- `ENVIRONMENT=production`.
- `FRONTEND_URL`: domínio HTTPS definitivo do frontend, sem query, fragmento ou credenciais.
- `CORS_ORIGINS`: origens HTTPS permitidas, separadas por vírgula.

No frontend, configure `VITE_API_URL` com a origem HTTPS da API, sem `/api`. Essa variável é incorporada no build. O proxy `/api` existe somente no desenvolvimento.

## Migrações e contas

Após testar em um banco de homologação, revisar o backup e autorizar a aplicação, execute na pasta backend:

```bash
alembic upgrade head
python -m app.create_admin
```

A conta administrativa é criada interativamente, com senha própria. Não executar seed em produção; o código bloqueia essa operação. O processo de startup em produção não modifica o esquema. A migração deve ser concluída antes da primeira inicialização. O Blueprint não aplica migrações automaticamente. No primeiro deploy, configure os domínios previstos ou reservados antes de inicializar a API. Faça o bootstrap do banco com as variáveis de produção carregadas no ambiente do comando.

As migrações adotam o esquema original e acrescentam identificadores, planos, notificações, auditoria e prazo de ordem de serviço. Elas não transferem dados SQLite para Neon: uma transferência exige procedimento separado, conferência de chaves e contagem dos registros. Não descarte o banco local.

## Inicialização

Backend: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
Frontend: `npm ci && npm run build`; diretório publicado: `dist`; fallback de navegação: `/index.html`.
Health check: `/health` verifica a conexão ao banco, sem revelar credenciais. Ele não substitui a validação de login ou das migrações.

## Etiquetas e câmera

Defina o domínio público definitivo antes de imprimir. Sem configuração HTTPS válida, o endpoint de QR retorna 503 e explica o requisito. Os identificadores persistem entre reinicializações; mudar o domínio exige preservar o domínio anterior ou redirecioná-lo para não invalidar etiquetas antigas.

A câmera precisa de permissão e contexto seguro. A leitura aceita apenas URLs da mesma origem da aplicação e identificadores UUID válidos, confirmados pela API autenticada.

## Verificação antes da publicação

Valide migrações em PostgreSQL de homologação, autenticação, isolamento por perfil, QR em um celular, download e impressão, navegação direta após login, CSV, preventivas e notificações. Confira todos os itens do relatório de versão antes de considerar produção pronta.

O arquivo foi validado contra o esquema JSON oficial. Referência: [Blueprint YAML Reference do Render](https://render.com/docs/blueprint-spec). A configuração local não provisiona serviços. Planos e custos devem ser escolhidos antes da criação.

# Deploy conjunto na Vercel

O `vercel.json` configura frontend e API no mesmo domínio com Vercel Services. Importe a raiz do repositório, não `frontend` nem `backend`.

## Banco persistente obrigatório

Configure no ambiente Production, antes de publicar esta versão:

```dotenv
DATABASE_URL=postgresql://USUARIO:SENHA@HOST/BANCO?sslmode=require
ENVIRONMENT=production
JWT_SECRET_KEY=SEU_SEGREDO_JA_CONFIGURADO_COM_PELO_MENOS_32_CARACTERES
FRONTEND_URL=https://SEU-PROJETO.vercel.app
CORS_ORIGINS=https://SEU-PROJETO.vercel.app
```

Use a conexão do PostgreSQL/Neon existente, mantendo os parâmetros SSL fornecidos pelo provedor. Não coloque credenciais no Git. Remova `ALLOW_EPHEMERAL_SQLITE`: a opção não habilita mais SQLite em produção. Configure Preview com um banco persistente próprio se também executar com `ENVIRONMENT=production`.

O SQLite em `/tmp` é isolado por instância. O antigo startup criava demonstrações independentes com UUIDs aleatórios: a lista podia gerar um link que a requisição seguinte não encontrava. Dados, links e etiquetas não sobreviviam de forma confiável a novas instâncias. UUIDs determinísticos ou links por ID numérico não corrigem essa perda de persistência.

## Migrações e preservação dos dados

Faça backup do banco existente. Em um ambiente com acesso ao Neon e as variáveis acima, execute a partir de `backend`:

```bash
python -m alembic upgrade head
```

As migrações devem concluir antes do deploy. O startup de produção não recria o banco nem executa o seed. Não apague tabelas, não regenere `public_id` existentes e não execute a carga de demonstração sobre dados reais. Se houver dados a recuperar do SQLite temporário, exporte-os da instância ainda acessível antes de trocar o banco; não há recuperação garantida de instâncias já descartadas. Etiquetas cujos UUIDs só existiam nessas instâncias precisarão ser reemitidas.

Somente se o banco estiver vazio e precisar de acesso inicial, crie um administrador explicitamente:

```bash
python -m app.create_admin
```

Mantenha o segredo JWT atual. Para o deploy conjunto, deixe `VITE_API_URL` ausente: o frontend usa `/api`. Faça um novo deploy após configurar as variáveis.

## Verificação após publicar

1. Confira `/api/health` e faça login pela interface.
2. Abra Equipamentos → Ver detalhes e QR Code. A API deve responder 200 para os detalhes e `image/png` para o QR Code.
3. Volte à lista e recarregue: o UUID do mesmo equipamento deve permanecer idêntico. Abra também o endereço contido na etiqueta.
4. Edite um equipamento de teste com o administrador, recarregue e confirme a persistência. Confira que operador continua sem permissão de edição.
5. Repita após uma nova inicialização da API. Nenhum UUID deve ser recriado.

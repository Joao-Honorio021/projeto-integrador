# Instalação e execução

[Índice da documentação](README.md)

## Requisitos

- Python 3.12 ou superior.
- Node.js 20.19 ou superior e npm.
- Terminal Bash para os comandos deste guia.

O SQLite é utilizado localmente e não exige um servidor de banco separado. Execute os comandos nas pastas indicadas para manter o caminho relativo do banco consistente.

## Preparar o backend

A partir da pasta `industrack`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Na primeira instalação, copie o modelo de configuração:

```bash
cp .env.example .env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Cole o valor gerado em `JWT_SECRET` no `.env`. Não sobrescreva uma configuração existente ao atualizar o projeto.

| Variável | Finalidade |
|---|---|
| `JWT_SECRET` | Segredo de assinatura dos tokens; a API exige pelo menos 32 caracteres |
| `DATABASE_URL` | Endereço do SQLite; o exemplo usa `sqlite:///./industrack.db` |
| `FRONTEND_URL` | Origem autorizada para acesso direto à API via CORS |

O arquivo `.env` é carregado a partir de `backend`. Uma variável já definida no ambiente tem precedência sobre o arquivo. O caminho relativo de `DATABASE_URL` é resolvido a partir do diretório de execução. Sem essa variável, o código usa um caminho absoluto para `backend/industrack.db`.

## Preparar os dados e iniciar a API

Com o ambiente virtual ativo, na pasta `backend`:

```bash
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O seed é opcional e explícito: popula um banco vazio com dados de demonstração. Sem ele, a inicialização cria as tabelas, mas não cria uma conta de acesso. A interface ainda não possui cadastro público de usuários.

O seed não sobrescreve bancos que já possuem usuários. Consulte [banco de dados](BANCO_DE_DADOS.md) para usar uma demonstração separada.

## Iniciar o frontend

Em outro terminal, a partir de `industrack`:

```bash
cd frontend
npm ci
npm run dev
```

O frontend usa o proxy do Vite: requisições para `/api` são encaminhadas para `http://127.0.0.1:8000`, removendo o prefixo.

| Serviço | Endereço padrão |
|---|---|
| Aplicação | [127.0.0.1:5173](http://127.0.0.1:5173) |
| API | [127.0.0.1:8000](http://127.0.0.1:8000) |
| Swagger | [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |

Use o endereço mostrado pelo Vite se ele escolher outra porta. Encerre os servidores com `Ctrl+C` nos respectivos terminais.

## Verificar o projeto

Na pasta `backend`, com o ambiente virtual ativo:

```bash
python -m pytest -q
```

Os testes usam um banco temporário separado e restauram a carga inicial antes de cada caso. Cobrem autenticação, permissões, integridade, filtros SQL, seed idempotente, atendimento e rollback.

Na pasta `frontend`:

```bash
npm run build
```

O comando verifica TypeScript e gera a interface em `frontend/dist`. A compilação não inicia a API nem configura uma implantação de produção. A revisão visual e os testes de navegador são verificações complementares.

## Problemas comuns

| Situação | O que verificar |
|---|---|
| Erro de `JWT_SECRET` | Substitua o valor de exemplo por um segredo aleatório e reinicie a API |
| Login não funciona | Confirme que o seed foi executado no mesmo banco usado pela API |
| Banco já possui usuários | O seed preserva os registros; use as contas existentes ou um banco separado |
| Interface não conecta | Confirme que a API responde na porta 8000 e que os dois servidores estão ativos |
| Porta ocupada | Verifique se o projeto já está em execução; evite iniciar servidores duplicados |
| Alteração de tabela não aparece | `schema.sql` não modifica colunas existentes; prepare uma migração |

A configuração documentada destina-se à execução local. O `.env`, o banco e as credenciais demonstrativas não devem ser tratados como configuração de produção.

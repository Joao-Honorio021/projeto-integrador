# Referência da API

[Índice da documentação](README.md)

## Endereços e autenticação

A API local usa `http://127.0.0.1:8000`. O frontend acessa `/api` pelo proxy do Vite; esse prefixo não faz parte das rotas do FastAPI.

Com o backend ativo, consulte o [Swagger](http://127.0.0.1:8000/docs) para os contratos detalhados e o [OpenAPI](http://127.0.0.1:8000/openapi.json) para a especificação gerada pelo código.

A rota de login recebe JSON:

```http
POST /auth/login
Content-Type: application/json

{
  "email": "operador@industrack.local",
  "senha": "Demo@12345"
}
```

A resposta contém `access_token` e `usuario`. Nas demais rotas, envie:

```http
Authorization: Bearer <access_token>
```

O token JWT expira em oito horas. O hash da senha é omitido nas respostas públicas de usuário.

## Endpoints disponíveis

### Autenticação e cadastros

| Método | Rota | Finalidade |
|---|---|---|
| POST | `/auth/login` | Autenticar com e-mail e senha |
| GET | `/auth/me` | Consultar o usuário autenticado |
| GET | `/usuarios` | Listar usuários; administrador e supervisor |
| GET | `/setores` | Listar setores |
| GET | `/equipamentos` | Listar equipamentos |
| POST | `/equipamentos` | Cadastrar equipamento; administrador |
| GET | `/equipamentos/{id}` | Consultar equipamento |
| GET | `/equipamentos/{id}/historico` | Consultar chamados e histórico do equipamento dentro do acesso do usuário |

### Chamados

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/chamados` | Buscar chamados com filtros e paginação |
| POST | `/chamados` | Abrir chamado |
| GET | `/chamados/{id}` | Consultar detalhes e timeline |
| PATCH | `/chamados/{id}/atribuir` | Atribuir técnico e prioridade; administrador e supervisor |
| POST | `/chamados/{id}/comentarios` | Registrar comentário em um chamado acessível |

A listagem aceita `q`, `status`, `prioridade`, `equipamento_id`, `tecnico_id` e `page`. Retorna `items` e `total`, com 20 registros por página, em ordem decrescente de ID. O parâmetro `q` procura título ou número.

Exemplo de abertura:

```json
{
  "titulo": "Vazamento na conexão hidráulica",
  "descricao": "Acúmulo de óleo identificado durante o turno. Solicito inspeção.",
  "equipamento_id": 1,
  "categoria": "Falha mecânica",
  "prioridade": "Alta"
}
```

O solicitante e a data de abertura são definidos pelo servidor. Prioridades aceitas: `Baixa`, `Média`, `Alta` e `Crítica`.

### Ordens e indicadores

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/ordens-servico` | Listar ordens dentro do acesso do usuário |
| POST | `/ordens-servico` | Criar ordem a partir de um chamado; administrador e supervisor |
| PATCH | `/ordens-servico/{id}/iniciar` | Iniciar ou retomar atendimento |
| PATCH | `/ordens-servico/{id}/pausar` | Pausar atendimento em execução |
| PATCH | `/ordens-servico/{id}/concluir` | Concluir com diagnóstico e solução |
| GET | `/dashboard/resumo` | Consultar totais, distribuição de status, prioridades e ordens pendentes |

A criação da ordem recebe `{"chamado_id": 1}`. O chamado precisa estar ativo e possuir técnico atribuído. Técnicos só podem executar ações nas próprias ordens; administradores e supervisores também podem gerenciá-las.

Exemplo de conclusão:

```json
{
  "diagnostico": "Vedação danificada na conexão hidráulica.",
  "solucao": "Vedação substituída e funcionamento verificado."
}
```

A conclusão exige ordem em execução. O servidor registra a data, resolve o chamado e grava o histórico na mesma transação.

## Respostas de erro

| Código | Significado |
|---|---|
| 401 | Credenciais inválidas ou sessão inválida/expirada |
| 403 | Usuário sem permissão para a operação ou registro |
| 404 | Registro não encontrado |
| 409 | Conflito de integridade ou transição de estado inválida |
| 422 | Dados de entrada inválidos |

Erros de negócio usam o campo `detail`. Erros de validação podem retornar uma lista de campos nesse mesmo atributo. A resposta a uma requisição sem token é controlada pelo componente HTTP Bearer do FastAPI.

As rotas desta página correspondem à implementação atual. Módulos previstos, como preventivas e anexos, não possuem endpoints nesta versão.

## Novas rotas da versão 1.0.2 em desenvolvimento

- `GET /health`: conexão ao banco.
- `GET /equipamentos/{identificador}`: aceita ID interno ou UUID público.
- `PATCH /equipamentos/{identificador}`: edição administrativa.
- `GET /equipamentos/{identificador}/qrcode`: PNG autenticado, exige domínio HTTPS.
- `GET /equipamentos/{identificador}/ordens`: ordens acessíveis do equipamento.
- `GET` e `POST /manutencoes`: lista e cadastro de planos.
- `POST /manutencoes/{id}/executar`: execução e reagendamento; corpo `mensagem`.
- `GET /manutencoes/{id}/historico`: execuções acessíveis.
- `GET /notificacoes`, `PATCH /notificacoes/{id}/ler`, `PATCH /notificacoes/ler-todas`: notificações do usuário.
- `GET /relatorios/chamados.csv?inicio=AAAA-MM-DD&fim=AAAA-MM-DD`: exportação autorizada.

Consulte [a matriz de requisitos](RELEASE_1_0_2.md) para limites de validação e funcionalidades incompletas.

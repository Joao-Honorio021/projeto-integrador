# Guia de uso e demonstração

[Índice da documentação](README.md)

## Perfis de acesso

| Perfil | Funcionalidades atuais |
|---|---|
| Administrador | Visão geral, cadastro de equipamentos, atribuição de técnicos e gestão de ordens |
| Supervisor | Visão geral, definição de prioridade na atribuição e gestão de ordens |
| Técnico | Consulta dos chamados e ordens atribuídos, início, pausa e conclusão de atendimentos |
| Operador | Abertura e acompanhamento das próprias solicitações |

Todos os perfis autenticados podem consultar equipamentos e abrir chamados. O painel e as consultas de chamados respeitam o escopo do usuário. As permissões são verificadas no backend.

## Contas demonstrativas

Disponíveis após a carga inicial em um banco vazio. A senha de todas é **`Demo@12345`**.

| Perfil | E-mail |
|---|---|
| Administrador | `admin@industrack.local` |
| Supervisor | `supervisor@industrack.local` |
| Técnico | `tecnico@industrack.local` |
| Técnicos adicionais | `tecnico2@industrack.local`, `tecnico3@industrack.local` |
| Operador | `operador@industrack.local` |
| Operadores adicionais | `operador2@industrack.local`, `operador3@industrack.local` |

Essas contas representam pessoas fictícias e são destinadas à demonstração local.

## Roteiro de apresentação

### 1. Registrar uma ocorrência

Entre como operador. Acesse **Equipamentos** e clique em **Abrir solicitação** no equipamento desejado. Preencha título, descrição e prioridade, confira o equipamento e salve.

Exemplo: título “Vazamento na conexão hidráulica” e descrição “Foi identificado acúmulo de óleo próximo à conexão durante o turno. Solicito inspeção técnica”.

### 2. Organizar o atendimento

Saia e entre como supervisor. Na **Central de suporte**, localize e abra o chamado. Selecione um técnico, defina a prioridade e clique em **Atribuir técnico**. Em seguida, crie a ordem de serviço.

A atribuição exige um técnico ativo. Depois de criar a ordem, a reatribuição fica bloqueada nesta versão.

### 3. Executar a ordem

Entre com a conta do técnico atribuído. Acesse **Ordens de serviço**, localize a ordem e clique em **Iniciar atendimento**.

Se necessário, pause e retome o trabalho. Para finalizar, clique em **Registrar solução**, preencha diagnóstico e solução executada e conclua.

### 4. Conferir o resultado

O chamado passa para **Resolvido**. A ordem registra a conclusão e a timeline recebe o diagnóstico e a solução. Volte ao dashboard para conferir os indicadores atualizados.

As métricas consultam o banco ao carregar a página; não há atualização por WebSocket.

## Regras de atendimento

| Ação | Estado permitido | Resultado |
|---|---|---|
| Criar ordem | Chamado ativo com técnico atribuído | Ordem pendente |
| Iniciar ou retomar | Ordem pendente ou pausada | Ordem em execução |
| Pausar | Ordem em execução | Ordem pausada |
| Concluir | Ordem em execução, com diagnóstico e solução | Ordem concluída e chamado resolvido |

Cada chamado admite uma única ordem. Uma ordem concluída não pode ser reiniciada. As alterações da ordem e do chamado são salvas na mesma transação que o histórico.

## Navegação

- **Dashboard:** indicadores, distribuição de status, prioridades e solicitações recentes.
- **Central de suporte:** busca por título ou número, filtros, paginação, detalhes e comentários.
- **Ordens de serviço:** acompanhamento e execução dos atendimentos.
- **Equipamentos:** consulta, pesquisa e cadastro pelo administrador.

O logout remove o token do navegador. Os tokens expiram em oito horas; a revogação no servidor ainda não está implementada.

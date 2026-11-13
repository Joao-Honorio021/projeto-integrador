# Relatório técnico 1.0.2

Data: 12 de novembro de 2026. Status: **configuração de publicação validada localmente. Homologação no domínio definitivo pendente**.

## Auditoria

A base existente utiliza React/Vite, FastAPI, SQLAlchemy e SQLite, com quatro perfis e histórico. Foram identificados acoplamentos ao SQLite (`PRAGMA`, `lastrowid`, `instr` e DDL no startup). As alterações mantêm as rotas e o fluxo de atendimento e substituem esses acoplamentos na camada de conexão, consultas e migrações.

Nenhum registro de produção foi excluído. O seed legado continua explícito e foi bloqueado em produção. A conexão Neon foi validada com TLS e consulta somente leitura; havia zero tabelas públicas. Não foram aplicadas migrações no Neon, realizados pushes ou deploys. Credenciais não foram gravadas no projeto.

## Matriz de requisitos

| Área | Classificação | Evidência ou pendência |
|---|---|---|
| Autenticação e quatro perfis | Implementado e validado | Testes locais preservam login, autorização e fluxo de ordens |
| SQL portátil e driver PostgreSQL | Implementado e validado localmente | PostgreSQL 17 com migração, login, cadastro, chamados, dashboard, busca, CSV, notificações e QR PNG |
| Conexão Neon | Implementado e validado | TLS e SELECT somente leitura; não implica validação do esquema |
| Migrações Alembic | Implementado e validado localmente | Preservação de registros em SQLite legado e criação do esquema em PostgreSQL 17 |
| UUID persistente | Implementado e validado | Teste de unicidade e estabilidade após migração repetida |
| QR PNG e endpoint protegido | Implementado e validado | PNG, autenticação e bloqueio de localhost testados |
| Página de equipamento e edição | Implementado, mas não validado integralmente | API e formulários completos; revisão visual pendente |
| Download e impressão de etiqueta | Implementado, mas não validado | Ações adicionadas; impressão física não conferida |
| Leitura por câmera | Implementado, mas não validado | ZXing com tratamento de câmera e origem; teste em câmera real pendente |
| QR em domínio de produção | Bloqueado | Falta domínio HTTPS definitivo do frontend |
| Registro de ocorrência por equipamento | Parcialmente implementado | Seleção por URL existente; percurso integral com câmera e domínio ainda não validado |
| Filtros de equipamento | Implementado, mas não validado no navegador | Nome, código, setor, status, criticidade e paginação na URL |
| Chamados e protocolos | Parcialmente implementado | Protocolo, edição e cancelamento validados na API; filtro por setor e anexos pendentes |
| Ordens de serviço | Parcialmente implementado | Início, pausa, conclusão, diagnóstico, prazo, cancelamento e histórico |
| Preventivas | Parcialmente implementado | Cadastro, lista, vencimento, execução e histórico testados na API; filtro por período implementado na interface |
| Notificações | Parcialmente implementado | Persistência, leitura, lembretes sem duplicação e contador testados na API |
| Dashboard | Parcialmente implementado | Consultas reais e novos gráficos e painéis; revisão visual pendente |
| Relatórios CSV | Parcialmente implementado | Cinco exportações verificadas na API |
| Auditoria | Parcialmente implementado | Histórico de chamados, ordens e execuções, com auditoria de equipamentos, usuários e setores |
| Dark mode | Implementado, mas não validado visualmente | Tokens e superfícies atualizados; revisão de contraste e dispositivos pendente |
| Sidebar e header | Parcialmente implementado | Agrupamento, menu móvel, recolhimento e busca global implementados |
| Administração | Implementado e validado na API | Cadastro, edição e desativação de usuários, cadastro e edição de setores e CLI de bootstrap |
| Vercel | Implementado, mas não publicado | Configurações separadas para API FastAPI e frontend Vite; variáveis, migração Neon e publicação pendentes |
| Testes de frontend | Parcialmente implementado | Lint, typecheck e build passaram; navegação e câmera aguardam homologação |
| Uploads | Pendente | Nenhum endpoint de upload foi exposto |

## Verificações locais

Doze testes passaram após a migração e os novos módulos. Os testes utilizam banco separado e verificam permissões, fluxo de atendimento, rollback, SQL, idempotência, UUID, QR PNG, execução preventiva, notificações e CSV. O lint, o typecheck e o build do frontend passaram.

Não foi feita cópia dos dados SQLite para Neon. A referência do Word preparada anteriormente descreve a versão local anterior e precisará de nova revisão após estabilização desta versão.

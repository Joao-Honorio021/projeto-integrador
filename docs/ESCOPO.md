# Escopo atual e evolução

[Índice da documentação](README.md)

## Objetivo

Demonstrar um fluxo de suporte industrial: o operador registra uma falha, o supervisor organiza o atendimento e o técnico executa a manutenção, preservando o histórico do equipamento.

## Implementado

| Área | Recursos disponíveis |
|---|---|
| Acesso | Login, JWT, quatro perfis, restauração de sessão e logout local |
| Equipamentos | Listagem, pesquisa na interface, cadastro pelo administrador e consulta individual pela API |
| Suporte | Abertura, busca, filtros, paginação, detalhes, comentários e atribuição |
| Ordens | Criação, início, pausa, retomada, diagnóstico, solução e conclusão |
| Histórico | Timeline de chamados e histórico do equipamento pela API |
| Indicadores | Totais, status, prioridades, ordens pendentes e solicitações recentes |
| Banco | SQLite persistente, integridade referencial, SQL parametrizado e seed explícito |
| Qualidade | Testes de API e fluxo, validação TypeScript e build do frontend |

A abertura de chamado a partir de um equipamento já encaminha sua seleção para o formulário. Os indicadores respeitam o acesso do usuário autenticado.

## Próximas etapas

- Cadastro e edição de usuários e setores.
- Edição e desativação de equipamentos; página própria de detalhes e histórico.
- Planejamento de preventivas e registro de execuções recorrentes.
- Anexos de imagens e QR Code de equipamentos.
- Transições adicionais de chamados, cancelamento de ordens, prazos e observações.
- Datas e campos complementares de atendimento e auditoria administrativa.
- Filtros adicionais na interface, ordenação e identificação de solicitante e técnico na tabela.
- Relatórios, configurações e indicadores de evolução, recorrência e tempo médio de resolução.
- Migrações automatizadas do esquema.
- Testes automatizados de navegador e revisão visual mais abrangente.

## Limites desta versão

O projeto é destinado à demonstração local. Implantação pública, recuperação de senha e revogação de tokens no servidor não estão implementadas. O logout remove o token do navegador, mas não invalida uma cópia já emitida.

Não há sensores, ESP32, IoT, telemetria, inteligência artificial, ERP, pagamentos ou aplicativo móvel nativo. Os dados demonstrativos são fictícios e persistidos no banco; os componentes React não simulam os atendimentos.

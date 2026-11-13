# Changelog

## 1.0.2 em desenvolvimento — 12 de novembro de 2026

- Migrações Alembic incrementais; adoção do esquema legado sem exclusão de registros.
- Driver PostgreSQL psycopg, SSL obrigatório em produção e pool reduzido.
- Identificador público UUID para equipamentos existentes e novos.
- Detalhes de equipamento, edição administrativa, QR PNG e etiqueta imprimível.
- Leitor por câmera com ZXing e validação de origem e identificador.
- Planos preventivos, execução e histórico persistentes.
- Notificações individuais de chamado, atribuição e conclusão; leitura individual e coletiva.
- Exportação CSV de chamados com período e proteção contra fórmulas.
- Tokens visuais escuros e novas rotas respeitando os perfis.
- Health check e Blueprint Render sem banco adicional ou publicação automática.

A versão ainda não atende integralmente aos critérios de produção. Consulte docs/RELEASE_1_0_2.md.

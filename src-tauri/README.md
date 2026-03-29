# Backend Tauri + Rust

Esta pasta contem a base inicial do novo backend em Rust.

## Objetivo desta primeira etapa

- preparar a estrutura do projeto Tauri
- configurar a conexao com MariaDB
- criar o estado compartilhado da aplicacao
- expor comandos iniciais para health check e leitura de configuracao

## Proximos passos

1. executar `database/schema.sql` no MariaDB
2. implementar `operation_service`
3. implementar `monitor_service`
4. conectar a interface Tauri
5. adicionar contingencia local

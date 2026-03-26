# Rede Compartilhada e Contingencia Offline

## Arquivos modelo

- `config.rede.maquinas.modelo.ini`: modelo para as 6 maquinas de corte.
- `config.rede.monitor.modelo.ini`: modelo para a maquina do monitor.
- `Iniciar_CorteDobra_Rede_Exemplo.bat`: exemplo de inicializacao com `PCP_CONFIG_FILE` e `PCP_MACHINE_ID`.
- `Abrir_Monitor_Rede_Exemplo.bat`: exemplo de inicializacao do monitor.

## Como implantar

1. Crie um compartilhamento UNC central, por exemplo `\\SERVIDOR-PCP\PlanoCorte`.
2. Dentro dele, crie:
   - `acervo_cnc`
   - `plano_corte`
   - `dados`
   - `app_data`
   - `saidas_cortadas`
3. Copie `config.rede.maquinas.modelo.ini` para `config.rede.maquinas.ini` e ajuste o nome do servidor.
4. Copie `config.rede.monitor.modelo.ini` para `config.rede.monitor.ini` e ajuste o nome do servidor.
5. Em cada maquina de corte, use o mesmo `config.rede.maquinas.ini` e inicie com um `PCP_MACHINE_ID` diferente.
6. Na maquina do monitor, use `config.rede.monitor.ini`.

## Placeholders suportados

- `{machine}`: substituido pelo valor de `PCP_MACHINE_ID` ou por `current_machine`.
- `{date}`: substituido automaticamente em `DadosXml`.

## Contingencia offline

- Quando o XML remoto nao puder ser atualizado, o app grava um evento local em `OfflineQueueDir`.
- A fila local e tentada novamente a cada 15 segundos.
- Quando a rede volta, os eventos pendentes sao sincronizados automaticamente.

## Limitacao importante

- O modo offline cobre o historico (`DadosXml`).
- O controle de concorrencia continua dependendo do `LocksFile` compartilhado.
- Se a rede cair antes do inicio de uma nova operacao, o app nao deve iniciar uma saida nova sem acesso ao lock central, para evitar duas maquinas usando a mesma saida ao mesmo tempo.

# Guia Técnico - Sistema de Monitoramento de Corte

## 1. Funcionamento dos Bloqueios (Locks)

Para evitar que duas máquinas operem o mesmo plano de corte simultaneamente, o sistema utiliza um arquivo central `active_locks.json`.

- **Timeout:** 4 horas (expira automaticamente após este período).
- **Integridade:** Utiliza travas de arquivo (`.lock`) para evitar corrupção durante acessos simultâneos.

## 2. Configuração de Rede (6+ Máquinas)

Todas as máquinas devem apontar para o mesmo servidor via caminhos UNC no `config.ini`:

```ini
[Paths]
DadosXml = \\SERVIDOR\Pasta\dados_{date}.xml
LocksFile = \\SERVIDOR\Pasta\active_locks.json
```

Use o script `configurar_unc.py` para automatizar essa descoberta.

## 3. Monitoramento em Tempo Real

O `monitor_app.py` lê os bloqueios ativos a cada 5 segundos.

- **Verde:** Operação normal.
- **Vermelho:** Operação atrasada (mais de 1 hora).
- **Branco:** Histórico de operações finalizadas (carregado do XML).

## 4. Troubleshooting

Se o monitor não mostrar operações:

1. Verifique se o arquivo `active_locks.json` no servidor tem conteúdo.
2. Certifique-se de que o relógio de todas as máquinas está sincronizado (essencial para o cálculo de duração).
3. Se o arquivo travar, apague manualmente o arquivo `active_locks.json.lock`.

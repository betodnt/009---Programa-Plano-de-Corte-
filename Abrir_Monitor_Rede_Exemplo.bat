@echo off
cd /d "%~dp0"

set "PCP_CONFIG_FILE=%~dp0config.rede.monitor.ini"

title Monitor de Operacoes em Rede
echo Abrindo monitor com config: %PCP_CONFIG_FILE%
python monitor_app.py
pause

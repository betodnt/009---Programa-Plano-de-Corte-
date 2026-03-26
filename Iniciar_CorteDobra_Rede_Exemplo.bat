@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo Uso:
    echo   Iniciar_CorteDobra_Rede_Exemplo.bat "Bodor1 (12K)"
    pause
    exit /b 1
)

set "PCP_CONFIG_FILE=%~dp0config.rede.maquinas.ini"
set "PCP_MACHINE_ID=%~1"

title Controle de Corte e Dobra - %PCP_MACHINE_ID%
echo Iniciando em rede para %PCP_MACHINE_ID% com config: %PCP_CONFIG_FILE%
python main.py
pause

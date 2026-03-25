@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo Uso:
    echo   Iniciar_CorteDobra_Com_ID.bat "Bodor1 (12K)"
    echo   Iniciar_CorteDobra_Com_ID.bat "Trumpf2"
    pause
    exit /b 1
)

set "PCP_MACHINE_ID=%~1"
title Controle de Corte e Dobra - %PCP_MACHINE_ID%
echo Iniciando o sistema para %PCP_MACHINE_ID%...
python main.py
pause

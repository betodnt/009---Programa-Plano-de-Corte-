@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo Uso:
    echo   Abrir_Monitor_Com_ID.bat "Bodor1 (12K)"
    echo   Abrir_Monitor_Com_ID.bat "Trumpf2"
    pause
    exit /b 1
)

set "PCP_MACHINE_ID=%~1"
title Monitor de Operacoes - %PCP_MACHINE_ID%
echo Abrindo monitor para %PCP_MACHINE_ID%...
python monitor_app.py
pause

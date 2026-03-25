@echo off
title Simulador de Multiplas Instancias - PCP
cd /d "%~dp0"

echo ==========================================
echo      INICIANDO AMBIENTE DE SIMULACAO
echo ==========================================
echo.

echo 1. Iniciando Monitor...
start "Monitor PCP" python monitor_app.py

:: Aguarda 2 segundos para o monitor subir
timeout /t 2 >nul

echo 2. Iniciando Bodor1 (12K)...
start "App - Bodor1" cmd /c "set PCP_MACHINE_ID=Bodor1 (12K)&& python main.py"

echo 3. Iniciando Bodor2 (6K)...
start "App - Bodor2" cmd /c "set PCP_MACHINE_ID=Bodor2 (6K)&& python main.py"

echo 4. Iniciando Bodor3 (4K)...
start "App - Bodor3" cmd /c "set PCP_MACHINE_ID=Bodor3 (4K)&& python main.py"

echo 5. Iniciando Trumpf1...
start "App - Trumpf1" cmd /c "set PCP_MACHINE_ID=Trumpf1&& python main.py"

echo 6. Iniciando Trumpf2...
start "App - Trumpf2" cmd /c "set PCP_MACHINE_ID=Trumpf2&& python main.py"

echo.
echo Todas as instancias foram iniciadas.
echo Voce pode fechar esta janela, os apps continuarao rodando.
pause
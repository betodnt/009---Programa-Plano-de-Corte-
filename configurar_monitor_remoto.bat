@echo off
REM Script para configurar Monitor em uma máquina remota da rede
REM Execute como Administrador

echo.
echo ========== CONFIGURADOR DE MONITOR REMOTO ==========
echo.
echo Este script irá:
echo  1. Detectar o caminho UNC da seu servidor
echo  2. Atualizar config.ini para funcionar em rede
echo  3. Preparar arquivos para outra máquina
echo.

REM Executar script Python
python configurar_unc.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========== PRÓXIMO PASSO ==========
    echo.
    echo Copie os seguintes arquivos para a outra máquina:
    echo.
    echo   monitor_app.py
    echo   core/config.py
    echo   core/locks.py
    echo   config.ini (já atualizado com caminhos UNC)
    echo.
    echo Na outra máquina, execute:
    echo   python monitor_app.py
    echo.
) else (
    echo.
    echo [ERRO] Falha na configuração!
    echo.
)

pause

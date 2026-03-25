@echo off
REM Script para descobrir o caminho UNC da unidade V:
echo.
echo ========== DESCOBRINDO CAMINHO UNC ==========
echo.

REM Tentar descobrir usando net use
echo Unidades de rede mapeadas:
net use

echo.
echo ========== TESTE DE CONECTIVIDADE ==========
echo.

REM Pedir ao usuario para digitar manualmente se precisar
echo Se a unidade V: nao aparecer acima, voce pode:
echo 1. Abrir "Este PC"
echo 2. Clicar direito na unidade V:
echo 3. Escolher "Desconectar unidade de rede" ou "Propriedades"
echo 4. Colar aqui o caminho UNC encontrado
echo.

REM Testar acesso aos dados
echo Testando acesso sa pasta de dados...
if exist "V:\8. CONTROLE DE PRODUCAO\3. DADOS" (
    echo [OK] Pasta de dados acessivel: V:\8. CONTROLE DE PRODUCAO\3. DADOS
) else (
    echo [ERRO] Pasta nao encontrada em V:\
)

echo.
pause

@echo off
title Teste de Estresse (Locks e Concorrencia)
echo ==========================================
echo      EXECUTANDO TESTE DE ESTRESSE
echo ==========================================
echo.
echo O teste ira rodar e salvar os resultados em:
echo %~dp0stress_test_log.txt
echo.
echo Aguarde o termino...

cd /d "%~dp0"

echo ========================================== > stress_test_log.txt
echo DATA: %DATE% %TIME% >> stress_test_log.txt
echo ========================================== >> stress_test_log.txt

:: Executa o script Python em modo unbuffered (-u) para gravar o log em tempo real
python -u test_stress.py >> stress_test_log.txt 2>&1

echo. >> stress_test_log.txt
echo ========================================== >> stress_test_log.txt
echo FIM: %DATE% %TIME% >> stress_test_log.txt
echo ========================================== >> stress_test_log.txt

echo.
echo Teste finalizado!
echo Verifique o arquivo stress_test_log.txt para ver os resultados.
pause
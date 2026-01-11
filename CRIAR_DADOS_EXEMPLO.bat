@echo off
chcp 65001 >nul
cls

echo ═══════════════════════════════════════════════════════════════
echo   CRIAR DADOS DE EXEMPLO
echo ═══════════════════════════════════════════════════════════════
echo.
echo ⚠️  ATENÇÃO: Este script vai:
echo    - Criar usuários de teste
echo    - Criar 15 produtos de exemplo
echo    - Configurar WhatsApp exemplo
echo.
echo ❓ Deseja continuar?
echo.
pause
echo.

python populate_sample_data.py

echo.
pause

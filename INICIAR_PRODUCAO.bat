@echo off
chcp 65001 >nul
cls

echo ═══════════════════════════════════════════════════════════════
echo   PAULICEIA TINTAS - SERVIDOR DE PRODUCAO
echo ═══════════════════════════════════════════════════════════════
echo.

echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    pause
    exit /b
)

echo ✅ Python encontrado!
echo.

echo 🚀 Iniciando servidor de produção (Waitress)...
echo.

venv\Scripts\python wsgi.py

pause

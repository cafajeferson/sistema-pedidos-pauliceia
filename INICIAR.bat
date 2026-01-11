@echo off
chcp 65001 >nul
cls

echo ═══════════════════════════════════════════════════════════════
echo   SISTEMA DE PEDIDOS B2B - INICIALIZAÇÃO
echo ═══════════════════════════════════════════════════════════════
echo.

echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale o Python em: https://www.python.org/downloads/
    echo Marque a opção "Add Python to PATH" durante a instalação
    echo.
    pause
    exit /b
)

echo ✅ Python encontrado!
echo.

echo 🔍 Verificando dependências...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo.
    echo 📦 Instalando dependências...
    echo Aguarde, isso pode levar alguns minutos...
    echo.
    
    if errorlevel 1 (
        echo.
        echo ❌ Erro ao instalar dependências!
        echo.
        pause
        exit /b
    )
    echo.
    echo ✅ Dependências instaladas com sucesso!
) else (
    echo ✅ Dependências já instaladas!
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo   INICIANDO SERVIDOR...
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🌐 Acesse o sistema em: http://localhost:5000
echo.
echo 🔐 Login Admin:
echo    Usuário: admin
echo    Senha: admin123
echo.
echo ⚠️  Para PARAR o servidor, pressione Ctrl+C
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

python app.py

pause

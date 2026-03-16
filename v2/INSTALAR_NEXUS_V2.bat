@echo off
chcp 65001 >nul
title NEXUS v2 — Instalador
color 0A

echo.
echo  ╔══════════════════════════════════╗
echo  ║   NEXUS v2 by Simplex            ║
echo  ║   Instalacion automatica         ║
echo  ╚══════════════════════════════════╝
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo Instala Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

echo [1/4] Python encontrado.

:: Instalar dependencias
echo [2/4] Instalando dependencias...
python -m pip install fastapi uvicorn python-dotenv groq Pillow numpy qrcode --quiet
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo       OK

:: Crear carpetas necesarias
echo [3/4] Creando carpetas...
if not exist "C:\nexus" mkdir "C:\nexus"
if not exist "C:\nexus\MERCH_OUTPUT" mkdir "C:\nexus\MERCH_OUTPUT"
echo       OK

:: Verificar .env
echo [4/4] Verificando configuracion...
if not exist "C:\nexus\.env" (
    echo.
    echo [AVISO] No se encontro C:\nexus\.env
    echo Crea el archivo con:
    echo   GROQ_API_KEY=tu_key_aqui
    echo.
    echo Obtener key gratis en: https://console.groq.com
    echo.
)

echo.
echo  Instalacion completada.
echo  Iniciando NEXUS v2...
echo.

:: Iniciar servidor
start "NEXUS v2" python "C:\nexus_v2\server.py"
timeout /t 4 >nul

:: Abrir panel
start http://localhost:8001

echo  Panel abierto en: http://localhost:8001
echo.
echo  Para iniciar manualmente:
echo    cd C:\nexus_v2
echo    python server.py
echo.
pause

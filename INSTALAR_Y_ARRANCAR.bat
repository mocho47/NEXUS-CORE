@echo off
title NEXUS v3 — Instalador y Arranque
cd /d C:\NEXUS_v3_NEW
set PYTHONIOENCODING=utf-8
color 0B

echo.
echo  =======================================
echo   NEXUS v3 by Simplex — Instalador
echo  =======================================
echo.

REM 1. Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Instala Python 3.12 primero.
    pause & exit /b 1
)
echo  [OK] Python encontrado

REM 2. Instalar dependencias
echo  [..] Instalando dependencias...
python -m pip install -r requirements.txt --quiet --no-warn-script-location
echo  [OK] Dependencias instaladas

REM 3. Instalar psutil si falta
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    python -m pip install psutil --quiet
)

REM 4. Crear directorios necesarios
if not exist "data"    mkdir data
if not exist "logs"    mkdir logs
if not exist "output"  mkdir output
if not exist "uploads" mkdir uploads
echo  [OK] Directorios creados

REM 5. Verificar .env
if not exist ".env" (
    echo  [!!] No existe .env — copiando desde .env.example
    copy .env.example .env >nul
    echo  [!!] IMPORTANTE: Abre .env y configura tus API keys
)
echo  [OK] .env verificado

REM 6. Matar procesos viejos
echo  [..] Cerrando instancias anteriores...
powershell -Command "Stop-Process -Name python -Force -ErrorAction SilentlyContinue" >nul 2>&1
timeout /t 2 /nobreak >nul
echo  [OK] Procesos anteriores cerrados

echo.
echo  =======================================
echo   Iniciando motores...
echo  =======================================
echo.

REM 7. Motor principal
start "NEXUS Core"      /min python nexus_core.py
timeout /t 4 /nobreak >nul

REM 8. Motores especializados
start "NEXUS ATF"       /min python motors\motor_atf.py
start "NEXUS Auth"      /min python motors\motor_auth.py
start "NEXUS Teens"     /min python motors\motor_teens.py
start "NEXUS Pagos"     /min python motors\motor_pagos.py
start "NEXUS Reportes"  /min python motors\motor_reportes.py
start "NEXUS Sistema"   /min python motors\motor_sistema.py
start "NEXUS Redes"     /min python motors\motor_redes.py
start "NEXUS Watchdog"  /min python motors\motor_watchdog.py

REM 9. Esperar que todo levante
echo  [..] Esperando que los motores levanten...
timeout /t 10 /nobreak >nul

REM 10. Verificar que el core responde
curl -s http://localhost:8003/ai/status >nul 2>&1
if errorlevel 1 (
    echo  [!!] Core tardando en responder — esperando 10s mas...
    timeout /t 10 /nobreak >nul
)

echo.
echo  [OK] NEXUS v3 listo
echo  [OK] Panel: http://localhost:8003/
echo.

REM 11. Abrir panel
start "" http://localhost:8003/

echo  Presiona cualquier tecla para cerrar esta ventana...
pause >nul

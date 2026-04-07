@echo off
title NEXUS v3 — Arrancando...
cd /d C:\NEXUS_v3_NEW
set PYTHONIOENCODING=utf-8

REM Cerrar instancias viejas
powershell -Command "Stop-Process -Name python -Force -ErrorAction SilentlyContinue" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Arrancar orquestador principal
start "NEXUS Core" /min python nexus_core.py
timeout /t 5 /nobreak >nul

REM Arrancar motores especializados
start "Motor ATF"       /min python motors\motor_atf.py
start "Motor Teens"     /min python motors\motor_teens.py
start "Motor Auth"      /min python motors\motor_auth.py
start "Motor Pagos"     /min python motors\motor_pagos.py
start "Motor Reportes"  /min python motors\motor_reportes.py
start "Motor Sistema"   /min python motors\motor_sistema.py
start "Motor Redes"     /min python motors\motor_redes.py
start "Motor Watchdog"  /min python motors\motor_watchdog.py
timeout /t 10 /nobreak >nul

REM Abrir panel (PROMPT_ZAI activo automaticamente — no necesita pegar nada)
start "" http://localhost:8003/

echo.
echo  ==========================================
echo   NEXUS v3 listo en http://localhost:8003
echo   El prompt maestro esta activo automaticamente.
echo  ==========================================
timeout /t 4 /nobreak >nul

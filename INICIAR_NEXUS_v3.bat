@echo off
title NEXUS v3 by Simplex
cd /d C:\NEXUS_v3_NEW

echo Iniciando NEXUS v3...
set PYTHONIOENCODING=utf-8

REM Motor principal (puerto 8003)
start "NEXUS Core" /min python nexus_core.py

REM Motores especializados
timeout /t 3 /nobreak >nul
start "NEXUS ATF"      /min python motors\motor_atf.py
start "NEXUS Auth"     /min python motors\motor_auth.py
start "NEXUS Teens"    /min python motors\motor_teens.py
start "NEXUS Pagos"    /min python motors\motor_pagos.py
start "NEXUS Reportes" /min python motors\motor_reportes.py
start "NEXUS Sistema"  /min python motors\motor_sistema.py
start "NEXUS Redes"    /min python motors\motor_redes.py

REM Esperar que todo arranque
timeout /t 8 /nobreak >nul

REM Abrir panel en el navegador
start "" http://localhost:8003/

echo NEXUS v3 listo en http://localhost:8003/

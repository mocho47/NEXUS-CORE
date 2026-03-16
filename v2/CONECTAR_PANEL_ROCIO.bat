@echo off
chcp 65001 >nul
title NEXUS v2 — Panel Rocio
color 0B

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   NEXUS v2 — Conectar Panel              ║
echo  ║   Milens + ATF  by Simplex               ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Este archivo conecta esta computadora
echo  al servidor de Anuar en la red local.
echo.

:: IP del servidor (cambiar si cambia la IP de la PC de Anuar)
set SERVIDOR_IP=192.168.1.6
set NEXUS_URL=http://%SERVIDOR_IP%:8001

echo  Conectando a: %NEXUS_URL%
echo.

:: Verificar conexion
curl -s --connect-timeout 3 "%NEXUS_URL%/api/health" >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] No se puede conectar al servidor.
    echo.
    echo  Verifica que:
    echo  1. La PC de Anuar este encendida
    echo  2. NEXUS este corriendo en la PC de Anuar
    echo     ^(doble clic en INICIAR_SERVIDOR_RED.bat^)
    echo  3. Ambas PCs esten en el mismo WiFi
    echo.
    pause
    exit /b 1
)

echo  Conexion exitosa!
echo.

:: Abrir panel apuntando al servidor correcto
start %NEXUS_URL%/?server=%SERVIDOR_IP%

echo  Panel abierto. Inicia sesion con tu PIN.
echo.
echo  Si la IP del servidor cambia, edita este archivo
echo  y cambia la linea: set SERVIDOR_IP=192.168.1.6
echo.
pause

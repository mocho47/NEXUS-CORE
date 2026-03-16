@echo off
chcp 65001 >nul
title NEXUS v2 — Servidor de Red
color 0A

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   NEXUS v2 — Servidor Principal          ║
echo  ║   Milens + ATF  by Simplex               ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Obtener IP local
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /i "IPv4" ^| findstr "192.168"') do (
    set LOCAL_IP=%%A
)
set LOCAL_IP=%LOCAL_IP: =%

:: Abrir puerto 8001 en el firewall (si no existe la regla)
netsh advfirewall firewall show rule name="NEXUS v2" >nul 2>&1
if errorlevel 1 (
    echo  Abriendo puerto 8001 en firewall...
    netsh advfirewall firewall add rule name="NEXUS v2" dir=in action=allow protocol=TCP localport=8001 >nul
    echo  Listo.
)

echo.
echo  ┌─────────────────────────────────────────┐
echo  │  Esta computadora (Anuar):              │
echo  │  http://localhost:8001                  │
echo  │                                         │
echo  │  Computadora de Rocio:                  │
echo  │  http://%LOCAL_IP%:8001             │
echo  │                                         │
echo  │  Copia esa URL en el navegador de Rocio │
echo  └─────────────────────────────────────────┘
echo.
echo  Iniciando NEXUS...
echo.

:: Iniciar servidor
start "NEXUS v2 Servidor" python "C:\nexus_v2\server.py"
timeout /t 4 >nul

:: Abrir panel local
start http://localhost:8001

echo  Servidor corriendo. No cierres esta ventana.
echo  Para detener el servidor cierra la ventana de Python.
echo.
pause

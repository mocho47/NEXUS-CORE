@echo off
title NEXUS + Tunel Internet
color 0A

echo.
echo  ==========================================
echo   NEXUS by SimplexGDL - Iniciando...
echo  ==========================================
echo.

:: Matar procesos anteriores
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM ngrok.exe /T >nul 2>&1
timeout /t 2 >nul

:: Iniciar servidor NEXUS
echo  [1/2] Iniciando servidor NEXUS...
start "" /MIN cmd /c "cd /d C:\nexus && python nexus_server.py"
timeout /t 4 >nul

:: Iniciar tunel ngrok con dominio fijo
echo  [2/2] Abriendo tunel internet...
start "" cmd /c "ngrok start nexus"
timeout /t 5 >nul

echo.
echo  ==========================================
echo   NEXUS LISTO
echo  ==========================================
echo.
echo   Dashboard (esta PC):
echo   http://localhost:8000/dashboard
echo.
echo   Teens (cualquier cel):
echo   https://enrique-slaty-afton.ngrok-free.dev/teens
echo.
echo   NO cierres esta ventana ni la de ngrok
echo  ==========================================
echo.

:: Abrir dashboard en navegador
start "" "http://localhost:8000/dashboard"

pause

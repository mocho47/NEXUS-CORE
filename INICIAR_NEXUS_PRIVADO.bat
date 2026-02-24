@echo off
TITLE NEXUS (PRIVADO)
color 0A
cls
echo ==========================================
echo        INICIANDO NEXUS - MODO PRIVADO
echo ==========================================
echo.
cd /d "%~dp0"

REM OFFLINE: bloquea llamadas a nube por defecto
set NEXUS_PRIVACY_MODE=offline
set NEXUS_DISABLE_CLOUD=1

REM No seteamos GROQ_API_KEY aqui a proposito.

echo Lanzando Nucleo (offline)...
python nexus_core.py

pause

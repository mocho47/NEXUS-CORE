@echo off
TITLE NEXUS SYSTEM
color 0A
cls
echo ==========================================
echo        INICIANDO PROTOCOLO NEXUS
echo ==========================================
echo.
echo [1/3] Accediendo a Base...
cd /d "%~dp0"
REM Modo por defecto: nube habilitada (puedes decir 'bloquea nube' cuando lo requieras)
set NEXUS_PRIVACY_MODE=online
set NEXUS_DISABLE_CLOUD=0
REM IMPORTANTE: No hardcodear llaves aquí. Usa el archivo .env (python-dotenv)
REM GROQ_API_KEY=...

echo [2/3] Lanzando Nucleo...
python nexus_core.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR CRITICO] Nexus no pudo arrancar.
    echo.
    echo Diagnostico:
    echo 1. Es posible que Python no este instalado.
    echo 2. O faltan las librerias necesarias.
    echo.
    echo --- INTENTANDO AUTO-REPARACION (Instalar librerias) ---
    timeout /t 3
    pip install -r requirements.txt
    echo.
    echo [REINTENTO] Lanzando Nexus de nuevo...
    python nexus_core.py
)

pause

@echo off
TITLE NEXUS Business Suite v2026
color 0A
cls

echo.
echo  =====================================================
echo           N E X U S   B U S I N E S S   S U I T E
echo                    v2026.02.24 - FULL
echo  =====================================================
echo.
echo  Modulos activos:
echo    Core + Pedidos + Clientes + Stock + Finanzas
echo    Marketing IA + Galeria Binaural + Legal (LFPDPPP)
echo    Teens + Familia + Admin + Auto-Ventas
echo    Telegram + Notifier + Asistente IA + Voz
echo    IoT + MiLens + Video + Spy + Backup + Scheduler
echo.
echo  Paneles web disponibles al iniciar:
echo    http://localhost:8000/            - Dashboard
echo    http://localhost:8000/dashboard   - Panel principal
echo    http://localhost:8000/admin       - Control ADMIN (PIN)
echo    http://localhost:8000/autoventas  - Auto-Ventas pipeline
echo    http://localhost:8000/landing     - Landing page publica
echo    http://localhost:8000/nexus-ear   - Oido + Chat NEXUS
echo    http://localhost:8000/teens       - NEXUS Teens
echo    http://localhost:8000/galeria     - Galeria Binaural
echo    http://localhost:8000/legal       - Aviso de Privacidad
echo    http://localhost:8000/marketing   - Marketing IA
echo    http://localhost:8000/finanzas    - Dashboard Financiero
echo.
echo  =====================================================
echo.

cd /d "%~dp0"

REM Entorno
set NEXUS_PRIVACY_MODE=online
set NEXUS_DISABLE_CLOUD=0

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no encontrado. Instala Python 3.10+ y vuelve a intentar.
    pause
    exit /b 1
)

echo  Iniciando NEXUS... (esto puede tardar unos segundos)
echo.

REM Arrancar servidor
start "NEXUS Server" /B python nexus_server.py

REM Esperar 3 segundos y abrir el navegador
timeout /t 3 /nobreak >nul
start "" http://localhost:8000/dashboard

echo  NEXUS activo en http://localhost:8000
echo.
echo  Comandos utiles desde otra terminal:
echo    python nexus_test_runner.py     - Pruebas E2E
echo    python nexus_admin.py setup     - Configurar admin (primera vez)
echo    python nexus_admin.py catalogo  - Ver catalogo de modulos
echo    python nexus_legal.py estado    - Estado legal/privacidad
echo    python nexus_autoventas.py metricas - Pipeline de ventas
echo.
echo  No cierre esta ventana mientras NEXUS este en uso.
echo  Para detener: Ctrl+C
echo.
timeout /t 99999 >nul

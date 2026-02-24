@echo off
TITLE NEXUS SYSTEM LAUNCHER V2.0
color 0A
cls

echo ==========================================
echo        INICIANDO PROTOCOLO NEXUS
echo ==========================================
echo.

:: 1. INTENTAR RUTA PRINCIPAL (CEREBRO)
if exist "C:\NEXUS\CEREBRO\nexus_core.py" (
    echo [OK] Nucleo encontrado en CEREBRO.
    cd /d "C:\NEXUS\CEREBRO"
    python nexus_core.py
    goto FIN
)

:: 2. INTENTAR RUTA RAIZ (RESPALDO)
if exist "C:\NEXUS\nexus_core.py" (
    echo [OK] Nucleo encontrado en RAIZ.
    cd /d "C:\NEXUS"
    python nexus_core.py
    goto FIN
)

:: 3. SI NO SE ENCUENTRA
color 0C
echo.
echo [ERROR CRITICO] No encuentro el archivo 'nexus_core.py'.
echo.
echo Busque en:
echo - C:\NEXUS\CEREBRO\nexus_core.py
echo - C:\NEXUS\nexus_core.py
echo.
echo Por favor, copia el archivo 'nexus_core.py' a alguna de esas carpetas.
echo.

:FIN
echo.
echo ==========================================
echo        SESION FINALIZADA
echo ==========================================
pause

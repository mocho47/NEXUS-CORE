@echo off
:: ============================================================
::  NEXUS v3 by Simplex - Lanzador
::  Inicia el servidor NEXUS y abre el navegador
:: ============================================================
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title NEXUS v3 by Simplex

:: Colores ANSI
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "CYAN=[36m"
set "MAGENTA=[35m"
set "RESET=[0m"
set "BOLD=[1m"

:: Cambiar al directorio del script (por si se llama desde otro lugar)
cd /d "%~dp0"

echo.
echo %BOLD%%MAGENTA%    _   _ _____  ___   _ ____   ____ _   _ _______ %RESET%
echo %BOLD%%MAGENTA%   | | | |_   _|/ _ \ / / ___| / ___| | | | ____\ \%RESET%
echo %BOLD%%MAGENTA%   | |_| | | | | | | | \___ \| |   | |_| |  _| | | |%RESET%
echo %BOLD%%MAGENTA%   |  _  | | | | |_| | |___) | |___|  _  | |___| | |%RESET%
echo %BOLD%%MAGENTA%   |_| |_| |_| \___/ \_\____/ \____|_| |_|_____|_|_%RESET%
echo.
echo %BOLD%                    by Simplex GDL%RESET%
echo %BOLD%                      v3.0%RESET%
echo.
echo %CYAN%============================================================%RESET%
echo.

:: Verificar que el entorno virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo %RED%[ERROR]%RESET No se encontro el entorno virtual.
    echo.
    echo %YELLOW%[!]%RESET Ejecuta install.bat primero para instalar NEXUS.
    echo.
    pause
    exit /b 1
)

:: Verificar que nexus_core.py existe
if not exist "nexus_core.py" (
    echo %RED%[ERROR]%RESET No se encontro nexus_core.py en la carpeta actual.
    echo.
    echo %YELLOW%[!]%RESET Asegurate de que todos los archivos de NEXUS esten en esta carpeta.
    echo.
    pause
    exit /b 1
)

:: Activar entorno virtual
echo %CYAN%[*]%RESET Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo %RED%[ERROR]%RESET No se pudo activar el entorno virtual.
    echo.
    echo %YELLOW%[!]%RESET Intenta ejecutar install.bat de nuevo.
    echo.
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET Entorno virtual activado.

:: Verificar que las dependencias estan instaladas
echo %CYAN%[*]%RESET Verificando dependencias...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[!]%RESET Faltan dependencias. Instalando...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo %RED%[ERROR]%RESET No se pudieron instalar las dependencias.
        echo %YELLOW%[!]%RESET Ejecuta install.bat para una instalacion completa.
        pause
        exit /b 1
    )
    echo %GREEN%[OK]%RESET Dependencias instaladas.
) else (
    echo %GREEN%[OK]%RESET Dependencias verificadas.
)

:: Leer puerto del .env si existe
set NEXUS_PORT=8000
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in ('findstr /i "^NEXUS_PORT" .env 2^>nul') do (
        if not "%%b"=="" set NEXUS_PORT=%%b
    )
)

:: Verificar si Ollama esta corriendo
echo %CYAN%[*]%RESET Verificando Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[!]%RESET Ollama no esta instalado o no esta en PATH.
    echo %YELLOW%[!]%RESET El modo local (Ollama/phi3:mini) no estara disponible.
    echo %YELLOW%[!]%RESET Puedes usar Groq y Z.ai como alternativas en la nube.
    echo.
) else (
    :: Verificar si el servicio de Ollama esta corriendo
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%[!]%RESET Ollama esta instalado pero el servicio no esta corriendo.
        echo %YELLOW%[!]%RESET Inicia Ollama desde el menu Inicio para activar el modo local.
        echo.
    ) else (
        echo %GREEN%[OK]%RESET Ollama corriendo correctamente.
    )
)

:: Iniciar NEXUS
echo.
echo %BOLD%%GREEN%============================================================%RESET%
echo %BOLD%%GREEN%   Iniciando NEXUS v3...%RESET%
echo %BOLD%%GREEN%============================================================%RESET%
echo.
echo %CYAN%[*]%RESET NEXUS estara disponible en: http://localhost:%NEXUS_PORT%
echo %CYAN%[*]%RESET Presiona Ctrl+C para detener el servidor.
echo.
echo %BOLD%Personalidades:%RESET
echo %MAGENTA%   [NEXUS] %RESET%- Asistente empresarial para Simplex GDL
echo %MAGENTA%   [FORJA] %RESET%- Coach de emprendedores (Nathalye)
echo %MAGENTA%   [TEENS] %RESET%- Coach para jovenes y familia
echo.
echo %BOLD%================================================================%RESET%
echo.

:: Abrir navegador despues de 5 segundos (en segundo plano)
start /b "" cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:%NEXUS_PORT%"

:: Ejecutar NEXUS
python nexus_core.py
set EXIT_CODE=%errorlevel%

:: Si NEXUS se cierra inesperadamente
if %EXIT_CODE% neq 0 (
    echo.
    echo.
    echo %RED%============================================================%RESET%
    echo %RED%   [ERROR] NEXUS se detuvo inesperadamente.%RESET%
    echo %RED%============================================================%RESET%
    echo.
    echo %YELLOW%Codigo de salida: %EXIT_CODE%%RESET%
    echo.
    echo %CYAN%Posibles soluciones:%RESET
    echo   1. Revisa que el puerto %NEXUS_PORT% no este en uso por otro programa
    echo   2. Ejecuta install.bat para reinstalar dependencias
    echo   3. Revisa el archivo .env para configuracion correcta
    echo   4. Reinicia tu computadora si el problema persiste
    echo.
    echo %YELLOW%[!]%RESET Para ver el error detallado, ejecuta manualmente:%RESET
    echo %YELLOW%    venv\Scripts\activate && python nexus_core.py%RESET%
    echo.
    pause
) else (
    echo.
    echo %CYAN%NEXUS se detuvo correctamente.%RESET%
    echo.
    pause
)

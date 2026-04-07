@echo off
:: ============================================================
::  NEXUS v3 by Simplex - Instalador Automatico
::  Para Windows 10/11 - Requiere Administrador recomendado
:: ============================================================
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title NEXUS v3 - Instalador

:: Colores ANSI (Windows 10+)
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "CYAN=[36m"
set "RESET=[0m"
set "BOLD=[1m"

echo.
echo %BOLD%%CYAN%============================================================%RESET%
echo %BOLD%%CYAN%   NEXUS v3 by Simplex - Instalador Automatico%RESET%
echo %BOLD%%CYAN%============================================================%RESET%
echo.

:: ---- Paso 1: Verificar Python ----
echo %CYAN%[1/8]%RESET Verificando Python 3.10+...

python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET Python no esta instalado en este equipo.
    echo.
    echo %YELLOW%NEXUS necesita Python 3.10 o superior para funcionar.%RESET
    echo.
    echo Abriendo la pagina de descarga de Python...
    start https://www.python.org/downloads/
    echo.
    echo %YELLOW%[!]%RESET Descarga Python 3.10+, instalalo marcando "Add Python to PATH"
    echo %YELLOW%[!]%RESET Luego ejecuta este instalador de nuevo.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo %GREEN%[OK]%RESET Python encontrado: !PYVER!

:: Verificar que sea 3.10 o superior
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if !PYMAJOR! lss 3 (
    echo %RED%[ERROR]%RESET Python !PYVER! es demasiado antiguo. Se necesita 3.10+
    pause
    exit /b 1
)
if !PYMAJOR! equ 3 if !PYMINOR! lss 10 (
    echo %RED%[ERROR]%RESET Python !PYVER! es demasiado antiguo. Se necesita 3.10+
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET Version !PYVER! es compatible.

:: ---- Paso 2: Crear entorno virtual ----
echo.
echo %CYAN%[2/8]%RESET Creando entorno virtual...

if exist "venv\Scripts\activate.bat" (
    echo %YELLOW%[!]%RESET El entorno virtual ya existe. Se reutilizara.
) else (
    if exist "venv" (
        echo %YELLOW%[!]%RESET Eliminando entorno virtual anterior...
        rmdir /s /q venv 2>nul
        if errorlevel 1 (
            echo %RED%[ERROR]%RESET No se pudo eliminar la carpeta venv anterior. Cierra todos los programas y vuelve a intentar.
            pause
            exit /b 1
        )
    )
    python -m venv venv
    if errorlevel 1 (
        echo %RED%[ERROR]%RESET No se pudo crear el entorno virtual.
        echo %YELLOW%[!]%RESET Asegurate de que Python este correctamente instalado.
        pause
        exit /b 1
    )
    echo %GREEN%[OK]%RESET Entorno virtual creado exitosamente.
)

:: ---- Paso 3: Instalar dependencias ----
echo.
echo %CYAN%[3/8]%RESET Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo %RED%[ERROR]%RESET No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET Entorno virtual activado.

echo.
echo %CYAN%[4/8]%RESET Actualizando pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo %YELLOW%[!]%RESET Hubo un problema al actualizar pip, continuando de todas formas...
) else (
    echo %GREEN%[OK]%RESET Pip actualizado.
)

echo.
echo %CYAN%[5/8]%RESET Instalando dependencias desde requirements.txt...
if not exist "requirements.txt" (
    echo %RED%[ERROR]%RESET No se encontro requirements.txt en la carpeta actual.
    echo %YELLOW%[!]%RESET Asegurate de ejecutar este instalador desde la carpeta de NEXUS.
    pause
    exit /b 1
)

pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo %RED%[ERROR]%RESET No se pudieron instalar las dependencias.
    echo.
    echo Intentando reinstalar con salida detallada para diagnostico:
    pip install -r requirements.txt
    echo.
    echo %YELLOW%[!]%RESET Revisa los errores arriba. Es posible que necesites instalar Visual C++ Build Tools.
    echo %YELLOW%[!]%RESET Descarga desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET Todas las dependencias instaladas correctamente.

:: ---- Paso 4: Crear archivo .env ----
echo.
echo %CYAN%[6/8]%RESET Configurando archivo .env...

if exist ".env" (
    echo %YELLOW%[!]%RESET El archivo .env ya existe. No se sobrescribira.
    echo %YELLOW%[!]%RESET Si quieres reiniciar la configuracion, elimina .env manualmente.
) else (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul 2>&1
        if errorlevel 1 (
            echo %RED%[ERROR]%RESET No se pudo copiar .env.example a .env.
            pause
            exit /b 1
        )
        echo %GREEN%[OK]%RESET Archivo .env creado desde .env.example
        echo %YELLOW%[!]%RESET IMPORTANTE: Edita el archivo .env y agrega tus API keys.
    ) else (
        echo %YELLOW%[!]%RESET No se encontro .env.example. Creando .env basico...
        (
            echo # NEXUS v3 by Simplex - Configuracion
            echo GROQ_API_KEY=
            echo ZAI_API_KEY=
            echo NEXUS_PORT=8000
            echo NEXUS_OWNER=Anuar
            echo ATF_PHONE=3323530146
        ) > .env
        echo %GREEN%[OK]%RESET Archivo .env basico creado.
        echo %YELLOW%[!]%RESET Editalo y agrega tus API keys para mejor funcionamiento.
    )
)

:: ---- Paso 5: Instalar Ollama ----
echo.
echo %CYAN%[7/8]%RESET Verificando Ollama...

:: Verificar si Ollama ya esta instalado
ollama --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[!]%RESET Ollama no esta instalado. Procediendo a instalarlo...
    echo.

    :: Intento 1: winget
    echo %CYAN%[*]%RESET Intentando instalar con winget...
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%[!]%RESET winget no disponible o fallo. Intentando descarga directa...
        echo.

        :: Intento 2: PowerShell descarga directa
        echo %CYAN%[*]%RESET Descargando Ollama desde GitHub...
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "$ProgressPreference='SilentlyContinue'; " ^
            "try { " ^
            "  Invoke-WebRequest -Uri 'https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'; " ^
            "  Write-Host 'Descarga completada.'; " ^
            "  Write-Host 'Ejecutando instalador...'; " ^
            "  Start-Process -FilePath '%TEMP%\OllamaSetup.exe' -ArgumentList '/S' -Wait; " ^
            "  Write-Host 'Instalacion completada.'; " ^
            "} catch { " ^
            "  Write-Host 'Error: No se pudo descargar o instalar Ollama.'; " ^
            "  Write-Host 'Instala Ollama manualmente desde https://ollama.com/download/'; " ^
            "  exit 1; " ^
            "}"

        if errorlevel 1 (
            echo.
            echo %RED%[ERROR]%RESET No se pudo instalar Ollama automaticamente.
            echo.
            echo %YELLOW%[!]%RESET Puedes instalar Ollama manualmente:%RESET
            echo %YELLOW%[!]%RESET   1. Ve a https://ollama.com/download/%RESET
            echo %YELLOW%[!]%RESET   2. Descarga e instala Ollama para Windows%RESET
            echo %YELLOW%[!]%RESET   3. Abre una terminal y ejecuta: ollama pull phi3:mini%RESET
            echo.
            goto :ollama_skip
        )
    ) else (
        echo %GREEN%[OK]%RESET Ollama instalado via winget.
    )

    :: Esperar a que Ollama este en PATH
    echo %CYAN%[*]%RESET Esperando que Ollama este disponible...
    set OLLAMA_WAIT=0
    :wait_ollama
    timeout /t 2 /nobreak >nul
    set /a OLLAMA_WAIT+=2
    ollama --version >nul 2>&1
    if errorlevel 1 (
        if !OLLAMA_WAIT! lss 30 (
            goto :wait_ollama
        ) else (
            echo %YELLOW%[!]%RESET Ollama se instalo pero no se detecta en PATH.
            echo %YELLOW%[!]%RESET Es posible que necesites reiniciar tu computadora.
            goto :ollama_skip
        )
    )
    echo %GREEN%[OK]%RESET Ollama esta listo.
) else (
    for /f "tokens=*" %%v in ('ollama --version 2^>^&1') do echo %GREEN%[OK]%RESET Ollama ya instalado: %%v
)

:ollama_skip

:: ---- Paso 6: Descargar modelo Phi-3 Mini ----
echo.
echo %CYAN%[*]%RESET Verificando modelo Phi-3 Mini...

ollama list 2>nul | findstr /i "phi3" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[!]%RESET Modelo phi3:mini no encontrado. Descargando...
    echo %YELLOW%[!]%RESET Esto puede tardar varios minutos dependiendo de tu internet.
    echo.
    ollama pull phi3:mini
    if errorlevel 1 (
        echo %RED%[ERROR]%RESET No se pudo descargar el modelo phi3:mini.
        echo %YELLOW%[!]%RESET Puedes intentarlo manualmente despues con: ollama pull phi3:mini
    ) else (
        echo.
        echo %GREEN%[OK]%RESET Modelo phi3:mini descargado correctamente.
    )
) else (
    echo %GREEN%[OK]%RESET Modelo phi3:mini ya disponible.
)

:: ---- Paso 7: Crear acceso directo en el escritorio ----
echo.
echo %CYAN%[8/8]%RESET Creando acceso directo en el escritorio...

set "SHORTCUT_NAME=NEXUS by Simplex.lnk"
set "DESKTOP_PATH=%USERPROFILE%\Desktop"
set "TARGET_BAT=%~dp0NEXUS.bat"
set "WORK_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%DESKTOP_PATH%\%SHORTCUT_NAME%'); " ^
    "$Shortcut.TargetPath = '%TARGET_BAT%'; " ^
    "$Shortcut.WorkingDirectory = '%WORK_DIR%'; " ^
    "$Shortcut.IconLocation = 'shell32.dll,14'; " ^
    "$Shortcut.Description = 'NEXUS v3 by Simplex - Asistente de IA Multi-Modelo'; " ^
    "$Shortcut.Save()"

if errorlevel 1 (
    echo %YELLOW%[!]%RESET No se pudo crear el acceso directo automaticamente.
    echo %YELLOW%[!]%RESET Puedes crearlo manualmente: haz click derecho en NEXUS.bat y envialo al escritorio.
) else (
    echo %GREEN%[OK]%RESET Acceso directo creado en el escritorio.
)

:: ---- Resumen final ----
echo.
echo.
echo %BOLD%%GREEN%============================================================%RESET%
echo %BOLD%%GREEN%   NEXUS v3 instalado exitosamente.%RESET%
echo %BOLD%%GREEN%============================================================%RESET%
echo.
echo %CYAN%Siguientes pasos:%RESET
echo   1. Edita el archivo .env con tus API keys (opcional pero recomendado)
echo   2. Doble click en NEXUS.bat para iniciar
echo   3. Se abrira tu navegador en http://localhost:8000
echo.
echo %CYAN%Personalidades disponibles:%RESET
echo   - NEXUS   : Asistente empresarial
echo   - FORJA   : Coach de emprendedores
echo   - TEENS   : Coach para jovenes y familia
echo.
echo %CYAN%Proveedores de IA:%RESET
echo   - Groq    : Modelo rapido en la nube (llama-3.1-8b)
echo   - Z.ai    : Modelo avanzado en la nube (glm-5)
echo   - Ollama  : Modelo local sin internet (phi3:mini)
echo.
echo %YELLOW%[!]%RESET Si Ollama no responde, asegurate de que el servicio este corriendo.%RESET
echo %YELLOW%[!]%RESET Si tienes problemas, reinicia tu computadora despues de instalar.%RESET
echo.
echo %BOLD%%GREEN%Doble click en NEXUS.bat para iniciar.%RESET%
echo.
pause

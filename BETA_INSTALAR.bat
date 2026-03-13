@echo off
chcp 65001 >nul
title NEXUS by Simplex — Instalador Beta
color 0A

echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║         NEXUS by Simplex — Beta Pack           ║
echo  ║      El cerebro digital para tu negocio        ║
echo  ╚════════════════════════════════════════════════╝
echo.
echo  Bienvenido. Este instalador configura NEXUS en
echo  menos de 3 minutos. No necesitas saber de tecnologia.
echo.
pause

:: ── 1. Verificar Python ──────────────────────────────────────────────────────
echo.
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Python no encontrado. Instalando automaticamente...
    echo.
    :: Intentar descarga via winget (Windows 11)
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo  Por favor descarga Python 3.12 desde:
        echo  https://python.org/downloads
        echo  Marca "Add Python to PATH" durante la instalacion.
        start https://python.org/downloads
        pause
        exit /b 1
    )
    echo  Python instalado correctamente.
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  OK: %%v

:: ── 2. Crear carpetas ─────────────────────────────────────────────────────────
echo.
echo [2/6] Preparando NEXUS...
set NEXUS_DIR=%~dp0
set NEXUS_DIR=%NEXUS_DIR:~0,-1%

if not exist "%NEXUS_DIR%\CONFIG"        mkdir "%NEXUS_DIR%\CONFIG"
if not exist "%NEXUS_DIR%\out"           mkdir "%NEXUS_DIR%\out"
if not exist "%NEXUS_DIR%\logs"          mkdir "%NEXUS_DIR%\logs"
if not exist "%NEXUS_DIR%\uploads"       mkdir "%NEXUS_DIR%\uploads"
if not exist "%NEXUS_DIR%\DROP_IN"       mkdir "%NEXUS_DIR%\DROP_IN"
if not exist "%NEXUS_DIR%\DROP_IN\INBOX" mkdir "%NEXUS_DIR%\DROP_IN\INBOX"
echo  OK: Estructura lista

:: ── 3. Instalar dependencias ─────────────────────────────────────────────────
echo.
echo [3/6] Instalando modulos (primera vez: 2-5 minutos)...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install fastapi uvicorn jinja2 python-multipart groq supabase python-dotenv httpx requests aiohttp reportlab pillow edge-tts psutil qrcode[pil] --quiet
if errorlevel 1 (
    echo  AVISO: Algunos modulos tuvieron problemas. NEXUS igual puede funcionar.
) else (
    echo  OK: Todos los modulos instalados
)

:: ── 4. Configurar .env con API Key beta ──────────────────────────────────────
echo.
echo [4/6] Configurando inteligencia artificial...
if not exist "%NEXUS_DIR%\.env" (
    :: API Key beta compartida — el usuario puede cambiarla despues desde NEXUS
    echo GROQ_API_KEY=gsk_BETA_COMPARTIDA_NEXUS > "%NEXUS_DIR%\.env"
    echo NEXUS_NODE_NAME=MI_NEXUS >> "%NEXUS_DIR%\.env"
    echo NEXUS_BETA=true >> "%NEXUS_DIR%\.env"
    echo  OK: Configurado con clave beta compartida
    echo  MISION PENDIENTE: Obtener tu propia clave en console.groq.com
) else (
    echo  OK: Configuracion existente respetada
)

:: Crear perfil inicial si no existe
if not exist "%NEXUS_DIR%\CONFIG\negocio.json" (
    echo {"nombre": "Mi Negocio", "giro": "", "telefono": "", "ciudad": "Guadalajara", "configured": false, "beta": true} > "%NEXUS_DIR%\CONFIG\negocio.json"
)

:: ── 5. Crear acceso directo en escritorio ────────────────────────────────────
echo.
echo [5/6] Creando acceso directo en escritorio...

:: Script VBS inteligente: si ya esta corriendo, solo abre el browser
set VBS_PATH=%NEXUS_DIR%\ABRIR_NEXUS.vbs
echo Set oShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo Set oHTTP = CreateObject("MSXML2.XMLHTTP") >> "%VBS_PATH%"
echo On Error Resume Next >> "%VBS_PATH%"
echo oHTTP.Open "GET", "http://127.0.0.1:8000/", False >> "%VBS_PATH%"
echo oHTTP.Send >> "%VBS_PATH%"
echo Dim bRunning >> "%VBS_PATH%"
echo bRunning = (oHTTP.Status = 200) >> "%VBS_PATH%"
echo On Error GoTo 0 >> "%VBS_PATH%"
echo If Not bRunning Then >> "%VBS_PATH%"
echo     oShell.Run "cmd /c cd /d %NEXUS_DIR% && python nexus_server.py > logs\server.log 2>&1", 0, False >> "%VBS_PATH%"
echo     Dim i >> "%VBS_PATH%"
echo     For i = 1 To 25 >> "%VBS_PATH%"
echo         WScript.Sleep 1000 >> "%VBS_PATH%"
echo         On Error Resume Next >> "%VBS_PATH%"
echo         oHTTP.Open "GET", "http://127.0.0.1:8000/", False >> "%VBS_PATH%"
echo         oHTTP.Send >> "%VBS_PATH%"
echo         If oHTTP.Status = 200 Then Exit For >> "%VBS_PATH%"
echo         On Error GoTo 0 >> "%VBS_PATH%"
echo     Next >> "%VBS_PATH%"
echo End If >> "%VBS_PATH%"
echo oShell.Run "http://localhost:8000/dashboard" >> "%VBS_PATH%"

:: Crear .lnk en escritorio
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\NEXUS.lnk'); $s.TargetPath='wscript.exe'; $s.Arguments='\""%VBS_PATH%\"\"'; $s.WorkingDirectory='%NEXUS_DIR%'; $s.Description='Abrir NEXUS - Cerebro de tu negocio'; $s.Save()" 2>nul
echo  OK: Acceso directo "NEXUS" creado en escritorio

:: ── 6. Arrancar y abrir bienvenida ───────────────────────────────────────────
echo.
echo [6/6] Iniciando NEXUS por primera vez...

:: Cerrar instancias previas en puerto 8000
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 >nul

:: Arrancar servidor
start "" cmd /k "cd /d %NEXUS_DIR% && echo NEXUS iniciando... && python nexus_server.py"

:: Esperar que responda
echo  Esperando que NEXUS despierte...
:waitloop
timeout /t 2 >nul
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/', timeout=2)" >nul 2>&1
if errorlevel 1 goto waitloop

:: Abrir BIENVENIDA (onboarding) en lugar del dashboard directamente
start http://localhost:8000/bienvenida

echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║   NEXUS Beta instalado correctamente          ║
echo  ║                                                ║
echo  ║   Tu navegador abre el wizard de inicio.       ║
echo  ║   Tarda 3 minutos — vale la pena.              ║
echo  ║                                                ║
echo  ║   Acceso directo creado en escritorio.         ║
echo  ║   Proxima vez: doble clic en "NEXUS"           ║
echo  ╚════════════════════════════════════════════════╝
echo.
echo  Comparte NEXUS con alguien que lo necesite.
echo  Un negocio a la vez.
echo.
pause

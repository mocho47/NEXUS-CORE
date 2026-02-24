@echo off
title NEXUS — Instalador de Claude Code
color 0B
cls

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         NEXUS — SETUP DE CLAUDE CODE             ║
echo  ║     Instalador automatico para C:\NEXUS          ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── VERIFICAR ADMINISTRADOR ──────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Ejecuta este archivo como ADMINISTRADOR.
    echo      Clic derecho → Ejecutar como administrador
    pause
    exit /b 1
)

:: ── VERIFICAR NODE.JS ─────────────────────────────────
echo  [1/4] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Node.js no encontrado. Descargando instalador...
    echo      Esto abrira el navegador. Instala la version LTS.
    start https://nodejs.org/en/download
    echo.
    echo  Cuando termines de instalar Node.js, cierra esta ventana
    echo  y vuelve a ejecutar este archivo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('node --version') do set NODE_VER=%%v
    echo  [OK] Node.js instalado: %NODE_VER%
)

:: ── VERIFICAR NPM ─────────────────────────────────────
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] npm no encontrado. Reinstala Node.js desde nodejs.org
    pause
    exit /b 1
)

:: ── INSTALAR CLAUDE CODE ──────────────────────────────
echo.
echo  [2/4] Instalando Claude Code...
npm install -g @anthropic-ai/claude-code >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Error instalando Claude Code. Intentando con permisos...
    npm install -g @anthropic-ai/claude-code --force
    if %errorlevel% neq 0 (
        echo  [!] Fallo la instalacion. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
)
echo  [OK] Claude Code instalado correctamente.

:: ── VERIFICAR C:\NEXUS ────────────────────────────────
echo.
echo  [3/4] Verificando proyecto NEXUS...
if not exist "C:\NEXUS" (
    echo  [!] No se encontro C:\NEXUS
    echo      Asegurate de que el proyecto este en C:\NEXUS
    pause
    exit /b 1
)
echo  [OK] Proyecto encontrado en C:\NEXUS

:: ── CREAR CLAUDE.MD CON CONTEXTO DE NEXUS ─────────────
echo.
echo  [4/4] Preparando contexto para Claude Code...

(
echo # NEXUS — Contexto del Proyecto
echo.
echo ## Que es NEXUS
echo Sistema integral de taller virtual por voz para sublimacion, laser y gran formato.
echo Desarrollado en Python 3.12 para Windows. Ruta: C:\NEXUS
echo.
echo ## Estado Actual
echo - main.py: NexusApp V2.9 corriendo. Trigger "Nexus" detectado pero respuesta "Mande" implementada.
echo - voice_service.py: Google Speech Recognition + gTTS + pyttsx3 fallback
echo - nexus_authorization.py: Control de permisos central
echo - nexus_iot.py: Control Chromecast corregido
echo - nexus_panel.html: Panel web de control
echo.
echo ## Modulos del Sistema
echo - nexus_core.py, nexus_voice.py, nexus_db.py, nexus_orders.py
echo - nexus_logs.py, nexus_panel.py, nexus_vault.py, nexus_iot.py
echo - nexus_marketing.py, nexus_video_maker.py, nexus_coder.py
echo - nexus_memory.py, nexus_self_heal.py, nexus_doctor.py
echo - nexus_housekeeping.py, nexus_watchtower.py, nexus_supabase_keepalive.py
echo - nexus_social_operator.py, nexus_ecosystem.py
echo.
echo ## Prioridades
echo 1. Verificar que el trigger de voz "Nexus" responda "Mande" correctamente
echo 2. Integrar todos los modulos que falten en main.py
echo 3. Hacer funcionar todos los comandos de voz del taller
echo 4. Limpiar residuos de RAV Antivirus del sistema si los hay
echo.
echo ## Reglas del Proyecto
echo - Nunca borrar ASSETS, TALLER, PEDIDOS, RESPALDO_MAESTRO
echo - Credenciales en CONFIG/VAULT_PRIVATE nunca se imprimen
echo - Dependencias: Python 3.12, vosk, psutil, pyttsx3, gtts, pygame, SpeechRecognition
echo - Variables de entorno en .env (SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY^)
echo.
echo ## Como Arrancar
echo   cd C:\NEXUS
echo   python main.py
) > "C:\NEXUS\CLAUDE.md"

echo  [OK] Contexto creado en C:\NEXUS\CLAUDE.md

:: ── LANZAR CLAUDE CODE ────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Todo listo. Abriendo Claude Code en C:\NEXUS   ║
echo  ║                                                  ║
echo  ║  1. Se abrira el navegador para iniciar sesion  ║
echo  ║  2. Usa tu cuenta Claude.ai (Pro o Max)         ║
echo  ║  3. Escribe: lee CLAUDE.md y continua NEXUS     ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause

cd /d C:\NEXUS
claude

pause

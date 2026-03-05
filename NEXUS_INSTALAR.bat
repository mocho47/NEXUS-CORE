@echo off
chcp 65001 > /dev/null
title NEXUS by Simplex — Instalador
color 0A
cls
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║        NEXUS by Simplex — Instalador     ║
echo  ║        Asistente IA para tu negocio      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verificar Python
echo [1/6] Verificando Python...
python --version > /dev/null 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python no encontrado.
    echo  Descarga Python 3.12 desde https://python.org
    pause & exit /b 1
)
echo  OK

:: Verificar pip e instalar dependencias
echo [2/6] Instalando dependencias...
pip install fastapi uvicorn jinja2 python-multipart groq edge-tts pygame requests httpx supabase ezdxf reportlab opencv-python numpy --quiet --no-warn-script-location > /dev/null 2>&1
echo  OK

:: Crear estructura de carpetas
echo [3/6] Creando estructura...
if not exist "CONFIG" mkdir CONFIG
if not exist "DATA"   mkdir DATA
if not exist "logs"   mkdir logs
if not exist "out"    mkdir out
if not exist "TALLER\SUBLIMINAL" mkdir "TALLER\SUBLIMINAL"
echo  OK

:: Activar licencia demo si no hay licencia
echo [4/6] Configurando licencia...
python nexus_license.py demo > /dev/null 2>&1
echo  OK

:: Configurar perfil NEGOCIO por defecto para cliente
echo [5/6] Configurando perfil...
python -c "from nexus_profiles import set_perfil_activo; set_perfil_activo('negocio')" > /dev/null 2>&1
echo  OK

:: Crear acceso directo en escritorio
echo [6/6] Creando acceso directo...
python -c "
import os, winreg
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
vbs_path = os.path.join(desktop, 'NEXUS.vbs')
nexus_dir = os.path.abspath('.')
vbs_content = '''Set WShell = CreateObject(\"WScript.Shell\")
WShell.CurrentDirectory = \"%s\"
WShell.Run \"python nexus_server.py\", 0, False
WScript.Sleep 3000
WShell.Run \"http://localhost:8000/dashboard\"
''' %% nexus_dir
open(vbs_path,'w').write(vbs_content)
print('  Acceso directo creado en escritorio')
" 2>&1
echo  OK

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  Instalacion completada!                 ║
echo  ║  Abre NEXUS.vbs en tu escritorio         ║
echo  ║  O ejecuta: python nexus_server.py       ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Primer paso: Ve a http://localhost:8000/setup
echo  para configurar tu negocio.
echo.
pause

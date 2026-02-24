@echo off
color 0c
echo ==================================================
echo   NEXUS EMERGENCY REPAIR - DETENIENDO TODO
echo ==================================================
echo Cerrando instancias trabadas de Python...
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
echo Cerrando Inkscape si se quedo pegado...
taskkill /F /IM inkscape.exe
echo.
echo ==================================================
echo   SISTEMA LIMPIO - REINICIANDO
echo ==================================================
cd /d C:\NEXUS
echo Iniciando Nucleo...
start "NEXUS CORE" python nexus_core.py
echo.
echo Si ves la ventana negra, todo esta bien.
echo El panel grafico deberia abrirse en unos segundos.
pause

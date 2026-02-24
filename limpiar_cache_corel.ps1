# Script para Limpiar Cache y Mensajes de CorelDRAW
# Elimina la carpeta "Messages" que contiene el aviso de "Ilegal"

$ErrorActionPreference = "SilentlyContinue"

Write-Host "Cerrando CorelDRAW si esta abierto..." -ForegroundColor Cyan
Stop-Process -Name "CorelDRW" -Force
Stop-Process -Name "CorelPP" -Force

Write-Host "Limpiando archivos basura y mensajes de alerta..." -ForegroundColor Yellow

# Rutas comunes donde Corel guarda los mensajes
$rutas = @(
    "$env:APPDATA\Corel\Messages",
    "$env:ProgramData\Corel\Messages",
    "$env:APPDATA\Corel\CorelDRAW Graphics Suite 2019\Draw\Workspace\Messages",
    "$env:APPDATA\Corel\CorelDRAW Graphics Suite 2020\Draw\Workspace\Messages",
    "$env:APPDATA\Corel\CorelDRAW Graphics Suite 2021\Draw\Workspace\Messages",
    "$env:APPDATA\Corel\CorelDRAW Graphics Suite 2022\Draw\Workspace\Messages"
)

$contador = 0

foreach ($ruta in $rutas) {
    if (Test-Path $ruta) {
        Write-Host "Eliminando: $ruta" -ForegroundColor Red
        Remove-Item -Path $ruta -Recurse -Force
        $contador++
    }
}

# Buscar carpetas 'Messages' en todo el directorio de Corel en AppData por si acaso
$appDataCorel = "$env:APPDATA\Corel"
if (Test-Path $appDataCorel) {
    Get-ChildItem -Path $appDataCorel -Recurse -Filter "Messages" -Directory | ForEach-Object {
        Write-Host "Eliminando extra: $($_.FullName)" -ForegroundColor Red
        Remove-Item -Path $_.FullName -Recurse -Force
        $contador++
    }
}

Write-Host "`n------------------------------------------------"
if ($contador -gt 0) {
    Write-Host " [EXITO] Se eliminaron $contador carpetas de mensajes." -ForegroundColor Green
    Write-Host " El aviso de 'Software Ilegal' deberia haber desaparecido."
} else {
    Write-Host " [INFO] No se encontraron carpetas de mensajes." -ForegroundColor Gray
    Write-Host " Es posible que ya estuvieran borradas."
}
Write-Host "------------------------------------------------"

Write-Host "`nPresiona Enter para salir..."
Read-Host

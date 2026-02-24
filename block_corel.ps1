# Script de Bloqueo y Limpieza para CorelDRAW
# Busca el ejecutable, lo bloquea en el Firewall y limpia carpetas de "Messages" (cache de validación)

$ErrorActionPreference = "SilentlyContinue"

# 1. BUSCAR EJECUTABLES (CorelDRAW y PhotoPaint)
Write-Host "Buscando instalaciones de Corel..."
$searchPaths = @("C:\Program Files", "C:\Program Files (x86)")
$executables = Get-ChildItem -Path $searchPaths -Include "CorelDRW.exe", "CorelPP.exe" -Recurse -File

if ($executables.Count -eq 0) {
    Write-Warning "No se encontraron ejecutables de Corel en las rutas estandar."
    # Intentar buscar en todo C si falla lo estandar (puede tardar, mejor avisar)
}

# 2. BLOQUEAR EN FIREWALL
foreach ($exe in $executables) {
    $name = $exe.Name
    $path = $exe.FullName
    
    Write-Host "Procesando: $name en $path"
    
    # Borrar reglas viejas si existen para evitar duplicados
    Remove-NetFirewallRule -DisplayName "NEXUS Block $name Out" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "NEXUS Block $name In" -ErrorAction SilentlyContinue
    
    # Crear reglas nuevas
    try {
        New-NetFirewallRule -DisplayName "NEXUS Block $name Out" -Direction Outbound -Program $path -Action Block -Profile Any -Force | Out-Null
        New-NetFirewallRule -DisplayName "NEXUS Block $name In" -Direction Inbound -Program $path -Action Block -Profile Any -Force | Out-Null
        Write-Host "   [BLOQUEADO] Firewall configurado para $name" -ForegroundColor Green
    } catch {
        Write-Error "   [ERROR] No se pudo bloquear $name. Se requieren permisos de Administrador."
    }
}

# 3. LIMPIAR CACHE Y DATOS (Carpetas Messages)
# Estas carpetas suelen contener los datos de validacion de licencia/mensajes del servidor
Write-Host "`nLimpiando Cache y Datos de Validacion..."

$cleanPaths = @(
    "$env:APPDATA\Corel\Messages",
    "$env:ProgramData\Corel\Messages"
)

foreach ($p in $cleanPaths) {
    if (Test-Path $p) {
        Write-Host "   Limpiando: $p"
        Remove-Item -Path "$p\*" -Recurse -Force
    } else {
        Write-Host "   No existe (o ya esta limpio): $p"
    }
}

Write-Host "`nOperacion completada."

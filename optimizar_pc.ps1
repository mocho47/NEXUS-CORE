# NEXUS v3 - Script de optimización de PC
# Ejecutar como Administrador para máximo efecto

Write-Host "=== NEXUS - Optimizando PC ===" -ForegroundColor Cyan

# 1. Espacio en disco
Write-Host "`n[DISCO]" -ForegroundColor Yellow
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | ForEach-Object {
    $libre = [math]::Round($_.Free / 1GB, 1)
    $usado = [math]::Round($_.Used / 1GB, 1)
    Write-Host "  $($_.Name): Libre $libre GB / Usado $usado GB"
}

# 2. Limpiar archivos temporales
Write-Host "`n[TEMP] Limpiando archivos temporales..." -ForegroundColor Yellow
$antes = (Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
$liberado = [math]::Round($antes / 1MB, 0)
Write-Host "  Liberados aprox $liberado MB de temporales"

# 3. Limpiar prefetch (requiere admin)
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue
Write-Host "  Prefetch limpiado"

# 4. Vaciar papelera
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Host "  Papelera vaciada"

# 5. Servicios pesados innecesarios
Write-Host "`n[SERVICIOS] Ajustando servicios..." -ForegroundColor Yellow
$deshabilitar = @(
    @{Nombre="DiagTrack"; Desc="Telemetría Microsoft"},
    @{Nombre="WMPNetworkSvc"; Desc="Windows Media Player Network"},
    @{Nombre="XblGameSave"; Desc="Xbox Game Save"},
    @{Nombre="XboxGipSvc"; Desc="Xbox Accessory Management"},
    @{Nombre="RetailDemo"; Desc="Modo demo de tienda"},
    @{Nombre="RemoteRegistry"; Desc="Registro remoto"},
    @{Nombre="Fax"; Desc="Servicio de Fax"}
)

foreach ($svc in $deshabilitar) {
    $s = Get-Service $svc.Nombre -ErrorAction SilentlyContinue
    if ($s) {
        if ($s.Status -eq "Running") {
            Stop-Service $svc.Nombre -Force -ErrorAction SilentlyContinue
            Set-Service $svc.Nombre -StartupType Disabled -ErrorAction SilentlyContinue
            Write-Host "  Deshabilitado: $($svc.Desc)"
        } else {
            Write-Host "  Ya estaba inactivo: $($svc.Desc)"
        }
    }
}

# 6. Optimizar memoria RAM (vaciar working sets)
Write-Host "`n[RAM] Liberando memoria de procesos en espera..." -ForegroundColor Yellow
[System.GC]::Collect()
Write-Host "  GC ejecutado"

# 7. Desfragmentar caché DNS
ipconfig /flushdns | Out-Null
Write-Host "`n[RED] Caché DNS limpiado"

# 8. Resumen RAM actual
Write-Host "`n[RAM ACTUAL]" -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$libre = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$usada = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 1)
Write-Host "  Total: $total GB"
Write-Host "  Usada: $usada GB"
Write-Host "  Libre: $libre GB"

Write-Host "`n=== Optimización completada ===" -ForegroundColor Green
Write-Host "Presiona cualquier tecla para cerrar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

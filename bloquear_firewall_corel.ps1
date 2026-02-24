# Script para Bloquear CorelDRAW en el Firewall de Windows
# Debe ejecutarse como Administrador

$ErrorActionPreference = "SilentlyContinue"

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "IMPORTANTE: Necesitas ejecutar esto como Administrador." -ForegroundColor Red
    Write-Host "Haz clic derecho en este archivo y elige 'Ejecutar con PowerShell'"
    Start-Sleep -s 5
    Exit
}

Write-Host "Buscando CorelDRAW en tu sistema (esto puede tardar unos segundos)..." -ForegroundColor Cyan

# Buscar el ejecutable principal de Corel
$corelPaths = Get-ChildItem -Path "C:\Program Files\Corel", "C:\Program Files (x86)\Corel" -Recurse -Filter "CorelDRW.exe" -ErrorAction SilentlyContinue

if ($corelPaths) {
    foreach ($exe in $corelPaths) {
        $path = $exe.FullName
        Write-Host "Encontrado: $path" -ForegroundColor Green
        
        $ruleName = "Bloqueo CorelDRAW - " + $exe.Directory.Name
        
        # Eliminar regla si ya existe para evitar duplicados
        Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        # Crear nueva regla de bloqueo de salida
        New-NetFirewallRule -DisplayName $ruleName `
                            -Direction Outbound `
                            -Program $path `
                            -Action Block `
                            -Profile Any `
                            -Description "Bloqueo automatico de Corel para evitar verificacion de licencia"

        Write-Host " BLOQUEADO EXITOSAMENTE en el Firewall." -ForegroundColor Yellow
    }
    
    Write-Host "`n[EXITO] CorelDRAW ha sido aislado de internet." -ForegroundColor Green
    Write-Host "Ahora intenta abrir el programa. Si el mensaje persiste, reinicia la PC."
} else {
    Write-Host "No se encontró 'CorelDRW.exe' en las carpetas estandar." -ForegroundColor Red
    Write-Host "Tendras que bloquearlo manualmente en el Firewall de Windows."
}

Write-Host "`nPresiona Enter para salir..."
Read-Host

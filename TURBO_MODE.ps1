# TURBO MODE - OPTIMIZACION EXTREMA PARA CREACIONES MILEN
# Ejecutar con PowerShell como Administrador

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      ACTIVANDO MODO TURBO (HIPER RENDIMIENTO)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Ideal para PCs lentas o antiguas (HP AIO, Tablets, Laptops)" -ForegroundColor Yellow
Write-Host ""

# 1. PLAN DE ENERGIA: ALTO RENDIMIENTO
Write-Host "[1/5] Forzando plan de Alto Rendimiento..." -ForegroundColor Green
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61

# 2. EFECTOS VISUALES (RENDIMIENTO)
Write-Host "[2/5] Desactivando efectos visuales innecesarios..." -ForegroundColor Green
$visualEffects = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
Set-ItemProperty -Path $visualEffects -Name "VisualFXSetting" -Value 2 # Ajustar para mejor rendimiento

# Desactivar transparencias
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "EnableTransparency" -Value 0

# 3. ELIMINAR BLOATWARE (APPS BASURA)
Write-Host "[3/5] Eliminando Apps Basura (Xbox, Solitario, Noticias)..." -ForegroundColor Green
$bloatware = @(
    "*Xbox*",
    "*Zune*",
    "*Solitaire*",
    "*BingNews*",
    "*GetHelp*",
    "*FeedbackHub*",
    "*YourPhone*",
    "*People*"
)
foreach ($app in $bloatware) {
    Get-AppxPackage $app | Remove-AppxPackage -ErrorAction SilentlyContinue
    Write-Host " - Eliminado: $app" -ForegroundColor Gray
}

# 4. LIMPIEZA DE DISCO Y TEMP
Write-Host "[4/5] Limpiando archivos temporales..." -ForegroundColor Green
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 5. DESACTIVAR TELEMETRIA Y SERVICIOS
Write-Host "[5/5] Desactivando telemetría y servicios pesados..." -ForegroundColor Green
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection" -Name "AllowTelemetry" -Value 0
Stop-Service "DiagTrack" -ErrorAction SilentlyContinue
Set-Service "DiagTrack" -StartupType Disabled

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      OPTIMIZACION COMPLETADA - MODO TURBO ACTIVO" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Por favor, REINICIA la PC para aplicar todos los cambios."
Write-Host "Presiona Enter para salir..."
Read-Host

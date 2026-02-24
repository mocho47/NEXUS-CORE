# Script para evitar que la PC se duerma durante la impresion 3D
# Simula una pulsacion de tecla cada 60 segundos

$wsh = New-Object -ComObject WScript.Shell

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   MODO INSOMNIO ACTIVADO - IMPRESION 3D EN CURSO" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Tu PC no se dormira mientras esta ventana este abierta."
Write-Host "Minimizala y dejala trabajar."
Write-Host "Para salir, presiona Ctrl+C o cierra la ventana."

while ($true) {
    # Simula presionar la tecla F15 (una tecla que no hace nada)
    $wsh.SendKeys("{F15}")
    Write-Host "." -NoNewline -ForegroundColor Gray
    Start-Sleep -Seconds 60








$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\NEXUS v3.lnk")
$Shortcut.TargetPath = "C:\NEXUS_v3_NEW\INICIAR_NEXUS_v3.bat"
$Shortcut.WorkingDirectory = "C:\NEXUS_v3_NEW"
$Shortcut.WindowStyle = 7
$Shortcut.Description = "Iniciar NEXUS v3 by Simplex"
$Shortcut.IconLocation = "C:\Windows\System32\imageres.dll,109"
$Shortcut.Save()
Write-Host "Listo"

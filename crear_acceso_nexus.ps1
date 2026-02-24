$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = "$desktop\NEXUS.lnk"
$targetPath = "C:\NEXUS\INICIAR_NEXUS_FULL.bat"
$iconPath = "C:\NEXUS\nexus.ico"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $targetPath
$Shortcut.WorkingDirectory = "C:\NEXUS"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "NEXUS"
$Shortcut.IconLocation = $iconPath
$Shortcut.Save()

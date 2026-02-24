param(
    [string]$TargetFolder = "C:\NEXUS"
)

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Este script no está corriendo como Administrador. Puede fallar al aplicar ACLs. Recomendación: clic derecho -> 'Ejecutar con PowerShell' (Administrador)."
}

if (!(Test-Path -Path $TargetFolder)) {
    New-Item -ItemType Directory -Path $TargetFolder -Force
}

function Add-Permission {
    param (
        [string]$Path,
        [string]$User,
        [string]$Rights
    )
    try {
        $Acl = Get-Acl -Path $Path
        $Ar = New-Object System.Security.AccessControl.FileSystemAccessRule($User, $Rights, "ContainerInherit,ObjectInherit", "None", "Allow")
        $Acl.AddAccessRule($Ar)
        Set-Acl -Path $Path -AclObject $Acl
        Write-Host "Successfully granted $Rights to $User on $Path"
        return $true
    } catch {
        # Silent failure to try next user
        return $false
    }
}

Write-Host "Granting permissions on $TargetFolder..."

# Orden: cuenta actual -> grupos privilegiados -> grupos comunes (fallback)
$currentUserDomain = "$env:USERDOMAIN\$env:USERNAME"
$currentUserLocal = "$env:COMPUTERNAME\$env:USERNAME"

$userNames = @(
    $currentUserDomain,
    $currentUserLocal,
    $env:USERNAME,
    "BUILTIN\Administrators",
    "NT AUTHORITY\SYSTEM",
    "Users",
    "Usuarios",
    "Everyone",
    "Todos"
) | Select-Object -Unique
$success = $false

foreach ($user in $userNames) {
    if (Add-Permission -Path $TargetFolder -User $user -Rights "FullControl") {
        $success = $true
        # Don't break, try to add for all compatible groups to be safe
    }
}

if ($success) {
    Write-Host "Permissions updated successfully."
} else {
    Write-Error "Failed to grant permissions to any known group (Todos/Everyone/Users)."
}

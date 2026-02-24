# LIMPIEZA MAESTRA TOTAL (C:, D:, E:, F:)
# 1. Copia lo valioso a C:\NEXUS\RESPALDO_MAESTRO
# 2. Ignora la basura de AION/IonMaster
# 3. Consolida todo en un solo lugar seguro

$backupDir = "C:\NEXUS\RESPALDO_MAESTRO"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

# Unidades a escanear (Incluyendo C: y F:)
# NOTA: En C: solo escanearemos carpetas de Usuario para no romper Windows
$drives = @("D:\", "E:\", "F:\") 

# Extensiones a salvar (SOLO LO ESENCIAL, SIN VIDEOS NI DISEÑOS)
# Eliminados: *.mp4, *.rd, *.rld, *.rdvset, *.dxf, *.studio3, *.cdr, *.crv3d, *.gcode
$extensions = @("*.jpg", "*.png", "*.pdf", "*.rar", "*.zip", "*.exe", "*.msi", "*.doc", "*.docx", "*.xls", "*.xlsx")

# Patrones de BASURA a ignorar (Agregado Videos de Proceso para asegurar)
$trashPatterns = @("*AION*", "*IonMaster*", "*boot*", "*efi*", "*sources*", "*winsetup*", "*System Volume Information*", "*$RECYCLE.BIN*", "*Program Files*", "*Windows*", "*Videos de Proceso*")

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      INICIANDO RESCATE TOTAL DE ARCHIVOS" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# --- FASE 1: UNIDADES EXTERNAS (D, E, F) ---
foreach ($drive in $drives) {
    if (Test-Path $drive) {
        Write-Host ">>> Escaneando unidad $drive ..." -ForegroundColor Yellow
        
        foreach ($ext in $extensions) {
            $files = Get-ChildItem -Path $drive -Recurse -Filter $ext -ErrorAction SilentlyContinue
            
            foreach ($file in $files) {
                # Filtro de basura
                $isTrash = $false
                foreach ($pattern in $trashPatterns) {
                    if ($file.FullName -like $pattern) { $isTrash = $true; break }
                }
                if ($isTrash) { continue }

                # Copiar
                $dest = Join-Path $backupDir $file.Name
                if (Test-Path $dest) { $dest = Join-Path $backupDir "$($drive[0])_$($file.Name)" }
                
                Write-Host "  [RESCATE] Copiando: $($file.Name)" -ForegroundColor Green
                Copy-Item -Path $file.FullName -Destination $dest -Force
            }
        }
    } else {
        Write-Host ">>> Unidad $drive no detectada, saltando..." -ForegroundColor Gray
    }
}

# --- FASE 2: LIMPIEZA DE DISCO C: (Solo Documentos/Escritorio) ---
Write-Host ">>> Escaneando Disco C: (Solo Datos de Usuario) ..." -ForegroundColor Yellow
$userPath = $env:USERPROFILE
$targetFolders = @("Desktop", "Documents", "Downloads", "Pictures", "Videos")

foreach ($folder in $targetFolders) {
    $scanPath = Join-Path $userPath $folder
    Write-Host "   -> Revisando $scanPath ..." -ForegroundColor White
    
    foreach ($ext in $extensions) {
        $files = Get-ChildItem -Path $scanPath -Recurse -Filter $ext -ErrorAction SilentlyContinue
        
        foreach ($file in $files) {
             # Filtro de basura (Extra estricto para C:)
            $isTrash = $false
            foreach ($pattern in $trashPatterns) {
                if ($file.FullName -like $pattern) { $isTrash = $true; break }
            }
            # Ignorar carpeta del propio respaldo y proyectos de programación
            if ($file.FullName -like "*\trae_projects\*" -or $file.FullName -like "*\NEXUS\*") { $isTrash = $true }
            
            if ($isTrash) { continue }

            # Copiar
            $dest = Join-Path $backupDir "C_$($file.Name)"
            if (Test-Path $dest) { $dest = Join-Path $backupDir "C_DUP_$($file.Name)" }
            
            Write-Host "  [RESCATE C:] Copiando: $($file.Name)" -ForegroundColor Cyan
            Copy-Item -Path $file.FullName -Destination $dest -Force
        }
    }
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      RESCATE MAESTRO COMPLETADO" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Todo lo valioso de C:, D:, E: y F: esta ahora en:"
Write-Host "   C:\NEXUS\RESPALDO_MAESTRO"
Write-Host ""
Write-Host "PASOS FINALES:"
Write-Host "1. Revisa la carpeta RESPALDO_MAESTRO."
Write-Host "2. Formatea las USBs (D, E, F) para dejarlas limpias."
Write-Host "3. Borra manualmente la basura de Documentos/Escritorio si quieres."
Write-Host ""
# pause eliminada para ejecucion automatica

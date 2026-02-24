"""
nexus_backup.py — Backups automáticos de configuración y templates.

Crea un zip diario de CONFIG/ y WEB/templates/ en BACKUPS/.
Mantiene solo los últimos 7 backups.

Uso:
    python nexus_backup.py                  # backup ahora
    import nexus_backup; nexus_backup.daily_backup()
"""
import os
import zipfile
import glob
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUPS_DIR = os.path.join(BASE_DIR, "BACKUPS")
KEEP_LAST = 7
FOLDERS_TO_BACKUP = ["CONFIG", os.path.join("WEB", "templates")]


def daily_backup(base_dir: str = None) -> str:
    """Crea un backup zip y devuelve la ruta del archivo creado."""
    base_dir = base_dir or BASE_DIR
    os.makedirs(BACKUPS_DIR, exist_ok=True)

    today = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    zip_path = os.path.join(BACKUPS_DIR, f"nexus_backup_{today}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in FOLDERS_TO_BACKUP:
            abs_folder = os.path.join(base_dir, folder)
            if not os.path.exists(abs_folder):
                continue
            for root, _, files in os.walk(abs_folder):
                for fname in files:
                    # Excluir archivos binarios grandes y secretos
                    if fname.endswith((".enc", ".key", ".db")):
                        continue
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, base_dir)
                    zf.write(fpath, arcname)

    # Mantener solo los últimos KEEP_LAST backups
    backups = sorted(glob.glob(os.path.join(BACKUPS_DIR, "nexus_backup_*.zip")))
    while len(backups) > KEEP_LAST:
        try:
            os.remove(backups[0])
        except Exception:
            pass
        backups = backups[1:]

    size_kb = os.path.getsize(zip_path) // 1024
    print(f"[BACKUP] Creado: {zip_path} ({size_kb} KB)")
    return zip_path


if __name__ == "__main__":
    path = daily_backup()
    print(f"Backup guardado en: {path}")

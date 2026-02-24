import os
import datetime
import shutil
import time

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "LOGS")
os.makedirs(LOGS_DIR, exist_ok=True)

class Bitacora:
    def __init__(self):
        self.current_log_file = os.path.join(LOGS_DIR, f"nexus_log_{datetime.datetime.now().strftime('%Y-%m')}.txt")

    def log(self, category, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{category}] {message}"
        print(entry) # También imprimir en consola
        
        try:
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            print(f"Error escribiendo log: {e}")

    def archive_now(self):
        """Comprime los logs antiguos."""
        try:
            archive_name = os.path.join(LOGS_DIR, f"backup_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.make_archive(archive_name, 'zip', LOGS_DIR)
            return "Historial comprimido exitosamente."
        except Exception as e:
            return f"Error al comprimir historial: {e}"

# Instancia global
bitacora = Bitacora()

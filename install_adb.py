import os
import zipfile
import requests
import shutil

# Configuración
ADB_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
TOOLS_DIR = r"C:\NEXUS\TOOLS"
ADB_DIR = os.path.join(TOOLS_DIR, "adb")

def install_adb():
    if not os.path.exists(TOOLS_DIR):
        os.makedirs(TOOLS_DIR)
        
    # Verificar si ya existe
    adb_exe = os.path.join(ADB_DIR, "platform-tools", "adb.exe")
    if os.path.exists(adb_exe):
        print("ADB ya está instalado.")
        return adb_exe

    print("Descargando ADB (Android Debug Bridge)...")
    zip_path = os.path.join(TOOLS_DIR, "adb.zip")
    
    try:
        # Descargar
        r = requests.get(ADB_URL, stream=True)
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
            
        print("Extrayendo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ADB_DIR)
            
        print("Limpiando...")
        os.remove(zip_path)
        
        print("ADB Instalado correctamente.")
        return adb_exe
        
    except Exception as e:
        print(f"Error instalando ADB: {e}")
        return None

if __name__ == "__main__":
    install_adb()

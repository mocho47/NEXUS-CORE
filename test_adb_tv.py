from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
import os

# Configuración
TV_IP = "192.168.1.5"
PORT = 5555

def connect_tv():
    print(f"--- CONECTANDO A TV ({TV_IP}) ---")
    
    # Intentar conexión sin claves primero (a veces funciona en redes locales confiables)
    device = AdbDeviceTcp(TV_IP, PORT, default_transport_timeout_s=9.)
    
    try:
        print("1. Intentando conectar...")
        device.connect()
        print("   ¡Conexión ADB exitosa!")
        
        print("2. Enviando comando de prueba (Abrir Configuración)...")
        # Abre el menú de configuración para probar control
        device.shell('am start -a android.settings.SETTINGS')
        print("   Comando enviado. Mira la TV.")
        
        return True
    except Exception as e:
        print(f"\n[ERROR] No se pudo conectar: {e}")
        print("\nPOSIBLES CAUSAS:")
        print("1. Debes activar 'Depuración por USB' en las opciones de desarrollador de la TV.")
        print("2. Debes aceptar el mensaje en la pantalla de la TV.")
        return False

if __name__ == "__main__":
    connect_tv()

import os
import json
import time
import webbrowser
import pyautogui
import subprocess
import getpass
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")

# Carpeta única y privada para credenciales
VAULT_DIR = os.path.join(CONFIG_DIR, "VAULT_PRIVATE")
VAULT_FILE = os.path.join(VAULT_DIR, "vault.enc")
KEY_FILE = os.path.join(VAULT_DIR, "secret.key")

# URLs Conocidas
URLS = {
    "facebook": "https://www.facebook.com",
    "tiktok": "https://www.tiktok.com/login",
    "instagram": "https://www.instagram.com",
    "gmail": "https://accounts.google.com",
    "netflix": "https://www.netflix.com/login",
    "spotify": "https://accounts.spotify.com/login"
}

class NexusVault:
    def __init__(self):
        self.ensure_private_dir()
        self.key = self.load_key()
        self.cipher = Fernet(self.key)
        self.db = self.load_db()

    def ensure_private_dir(self):
        """Crea carpeta de bóveda y trata de restringir ACL a usuario actual.
        Nota: en Windows, Administrators/SYSTEM pueden seguir teniendo acceso (normal/esperado).
        """
        try:
            os.makedirs(VAULT_DIR, exist_ok=True)
        except Exception:
            return

        # Intento de endurecer permisos (mejor esfuerzo).
        # /inheritance:r  => quita herencia
        # /grant:r        => reemplaza grants
        try:
            user = getpass.getuser()
            subprocess.run(
                [
                    "icacls",
                    VAULT_DIR,
                    "/inheritance:r",
                    "/grant:r",
                    f"{user}:(OI)(CI)F",
                    "/grant:r",
                    "SYSTEM:(OI)(CI)F",
                    "/grant:r",
                    "Administrators:(OI)(CI)F",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
        except Exception:
            pass

    def load_key(self):
        """Carga o genera la llave maestra."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            try:
                os.makedirs(VAULT_DIR, exist_ok=True)
            except Exception:
                pass
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            return key

    def load_db(self):
        if os.path.exists(VAULT_FILE):
            try:
                with open(VAULT_FILE, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            except:
                return {}
        return {}

    def save_db(self):
        encrypted_data = self.cipher.encrypt(json.dumps(self.db).encode())
        try:
            os.makedirs(VAULT_DIR, exist_ok=True)
        except Exception:
            pass
        with open(VAULT_FILE, "wb") as f:
            f.write(encrypted_data)

    def add_credential(self, app, user, password):
        self.db[app.lower()] = {"user": user, "pass": password}
        self.save_db()
        return f"Credencial guardada para {app}."

    def login(self, app):
        app = app.lower()
        if app not in self.db:
            return False, "No tengo credenciales para esa app."
        
        creds = self.db[app]
        url = URLS.get(app, f"https://www.{app}.com")
        
        # 1. Abrir Navegador
        webbrowser.open(url)
        
        # 2. Esperar carga (ajustable)
        time.sleep(5) 
        
        # 3. Escribir Usuario
        pyautogui.write(creds["user"])
        pyautogui.press("tab")
        time.sleep(0.5)
        
        # 4. Escribir Password
        pyautogui.write(creds["pass"])
        pyautogui.press("enter")
        
        return True, f"Iniciando sesión en {app}..."

manager = NexusVault()

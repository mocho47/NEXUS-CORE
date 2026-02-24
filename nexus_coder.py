import os
import sys
import subprocess
import time
from groq import Groq

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.join(BASE_DIR, "LABORATORIO")
os.makedirs(LAB_DIR, exist_ok=True)

class NexusCoder:
    def __init__(self):
        privacy_mode = os.environ.get("NEXUS_PRIVACY_MODE", "supervised").strip().lower()
        disable_cloud = os.environ.get("NEXUS_DISABLE_CLOUD", "0").strip().lower() in ("1", "true", "yes")
        if privacy_mode == "offline" or disable_cloud:
            self.api_key = None
            print("[CODER] Modo privado/offline: cerebro de código (Groq) deshabilitado.")
            return
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            print("[CODER ERROR] No hay API Key de Groq. No puedo programar.")
            
    def generate_code(self, prompt):
        """Genera código Python basado en una descripción."""
        if not self.api_key: return None
        
        client = Groq(api_key=self.api_key)
        
        system_prompt = """
        Eres un Experto Programador Python.
        Tu tarea es escribir scripts completos, funcionales y sin errores.
        SOLO devuelve el código Python dentro de bloques ```python```.
        No expliques nada. Solo código.
        Usa librerías estándar o populares (requests, pandas, yt-dlp).
        Si necesitas instalar algo, pon un comentario al principio: # REQUIREMENTS: libreria1 libreria2
        """
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Modelo potente para código
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Escribe un script python para: {prompt}"}
                ],
                temperature=0.1 # Baja temperatura para precisión
            )
            
            content = completion.choices[0].message.content
            # Extraer código de los bloques
            import re
            code_match = re.search(r"```python(.*?)```", content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            return content # Fallback si no hay bloques
            
        except Exception as e:
            print(f"[CODER ERROR] {e}")
            return None

    def save_and_run(self, code, filename="generated_script.py"):
        """Guarda el código en el laboratorio para revisión manual.

        La ejecución automática está deshabilitada por seguridad.
        Para ejecutar: python LABORATORIO/<filename>
        """
        filepath = os.path.join(LAB_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"[CODER] Código guardado en: {filepath}")
        print(f"[CODER] Revisa el código antes de ejecutarlo manualmente.")
        return f"Guardado en LABORATORIO/{filename} — requiere revisión manual antes de ejecutar."

    def execute_saved(self, filename="generated_script.py"):
        """Ejecuta un script ya guardado en LABORATORIO/ (requiere llamada explícita)."""
        filepath = os.path.join(LAB_DIR, filename)
        if not os.path.exists(filepath):
            return f"Archivo no encontrado: {filepath}"

        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        requirements = []
        for line in code.split("\n"):
            if "# REQUIREMENTS:" in line:
                requirements = line.split(":")[1].strip().split()
                break

        if requirements:
            print(f"[CODER] Instalando dependencias: {requirements}")
            subprocess.run([sys.executable, "-m", "pip", "install"] + requirements)

        print(f"[CODER] Ejecutando {filename}...")
        try:
            result = subprocess.run([sys.executable, filepath], capture_output=True, text=True, timeout=30)
            return result.stdout + "\n" + result.stderr
        except subprocess.TimeoutExpired:
            return "Error: El script tardó demasiado y fue detenido."
        except Exception as e:
            return f"Error de ejecución: {e}"

coder = NexusCoder()

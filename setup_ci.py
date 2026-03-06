"""
setup_ci.py — Configura el entorno para GitHub Actions CI.
Crea CONFIG/ con datos de prueba, perfil admin y licencia bypass.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import datetime
import base64

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE, "CONFIG")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Config negocio de prueba
negocio = {
    "nombre": "NEXUS Test CI",
    "giro": "Pruebas automatizadas",
    "telefono": "0000000000",
    "ciudad": "CI",
    "configured": True,
    "color_marca": "#00ff88"
}
with open(os.path.join(CONFIG_DIR, "negocio.json"), "w", encoding="utf-8") as f:
    json.dump(negocio, f, ensure_ascii=False)

# Perfil admin CI
from nexus_profiles import set_perfil_activo
set_perfil_activo("admin")

# Licencia ADMIN bypass (sin huella hardware)
lic = {
    "tipo": "ADMIN",
    "cliente": "CI_TEST",
    "huella": "BYPASS",
    "creada": datetime.datetime.now().isoformat(),
    "expira": datetime.datetime(2099, 1, 1).isoformat(),
    "modulos": ["*"],
    "firma": "CI_BYPASS"
}
raw = json.dumps(lic, ensure_ascii=False).encode()
with open(os.path.join(CONFIG_DIR, "license.key"), "wb") as f:
    f.write(base64.b64encode(raw))

# Carpetas necesarias
os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE, "out"), exist_ok=True)
os.makedirs(os.path.join(BASE, "TALLER", "MARKETING_STUDIO"), exist_ok=True)

print("CONFIG CI OK — perfil ADMIN, licencia BYPASS, carpetas listas")

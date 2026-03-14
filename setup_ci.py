"""
setup_ci.py — Configura el entorno para GitHub Actions CI.
Crea CONFIG/ con datos de prueba, perfil admin y licencia valida BYPASS.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import datetime

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

# Licencia ADMIN con firma HMAC real (huella BYPASS = omite verificacion hardware)
from nexus_license import crear_licencia
lic = crear_licencia(
    huella="BYPASS",
    tipo="ADMIN",
    cliente="CI_TEST",
    duracion_dias=36500,
    modulos=["*"]
)
print("Licencia CI creada:", lic.get("tipo"), "| Huella:", lic.get("huella"))

# Carpetas necesarias
os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE, "out"), exist_ok=True)
os.makedirs(os.path.join(BASE, "TALLER", "MARKETING_STUDIO"), exist_ok=True)

print("CONFIG CI OK — perfil ADMIN, licencia BYPASS firmada correctamente")

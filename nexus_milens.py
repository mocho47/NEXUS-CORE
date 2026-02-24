"""
nexus_milens.py — Módulo Creaciones Milens.
Usa nexus_boxes_gui.py y nexus_core.py para cotizar y generar archivos.
"""
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cotizar_caja(largo, ancho, alto, material="MDF 2.7mm"):
    """Calcula precio estimado de caja basado en precios_base.json."""
    try:
        with open(os.path.join(BASE_DIR, "CONFIG", "precios_base.json"), "r", encoding="utf-8") as f:
            precios = json.load(f)
        costo_min = precios.get("laser", {}).get("costo_minuto", 8.0)
        # Estimado: 1 minuto por cada 10cm de perímetro
        perimetro = 2 * (largo + ancho + alto)
        minutos_est = perimetro / 10
        total = minutos_est * costo_min
        return {"minutos": round(minutos_est, 1), "precio": round(total, 2), "material": material}
    except Exception as e:
        return {"error": str(e)}

def abrir_disenador():
    """Abre la GUI de diseño de cajas."""
    import subprocess, sys
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "nexus_boxes_gui.py")])

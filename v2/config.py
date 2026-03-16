# -*- coding: utf-8 -*-
"""
NEXUS v2 — Configuración central
Precios, constantes, rutas. Un solo lugar para cambiar todo.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv("C:/nexus/.env")

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_KEY        = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL      = "llama-3.1-8b-instant"    # 500k tokens/día — uso general
GROQ_MODEL_PRO  = "llama-3.3-70b-versatile" # 100k tokens/día — análisis profundo

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path("C:/nexus")
V2_DIR      = Path("C:/nexus_v2")
OUTPUT_DIR  = Path("C:/nexus/MERCH_OUTPUT")
DB_PATH     = BASE_DIR / "nexus_v2.db"

# ── Apps del taller ───────────────────────────────────────────────────────────
APPS = {
    "corel":      r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelDRW.exe",
    "silhouette": r"C:\Program Files\Silhouette America\Silhouette Studio\Silhouette Studio.exe",
    "boxes":      r"C:\Program Files\Python312\Scripts\boxes.exe",
}

# ── Precios ATF — Aozoom ──────────────────────────────────────────────────────
AOZOOM = {
    "X1": {"dist": 2350, "pub": 3149, "nombre": "Aozoom X1"},
    "X2": {"dist": 2050, "pub": 2799, "nombre": "Aozoom X2"},
    "X3": {"dist": 2350, "pub": 3149, "nombre": "Aozoom X3"},
    "X4": {"dist": 1990, "pub": 2699, "nombre": "Aozoom X4 (top)"},
    "X5": {"dist": 1199, "pub": 1599, "nombre": "Aozoom X5"},
    "X6": {"dist": 1199, "pub": 1599, "nombre": "Aozoom X6"},
    "X7": {"dist": 1550, "pub": 2069, "nombre": "Aozoom X7"},
}

def ganancia_atf(modelo: str) -> dict:
    """Calcula ganancia y margen para un kit Aozoom."""
    k = AOZOOM.get(modelo.upper())
    if not k:
        return {}
    ganancia = k["pub"] - k["dist"]
    margen   = round((ganancia / k["pub"]) * 100, 1)
    return {**k, "ganancia": ganancia, "margen": margen}

# ── Servicios Milens — Precios reales (fuente: precios_base.json v1) ──────────
# Hoja estándar 122x244cm = 29,768 cm²
# costo_cm2 = precio_hoja / area_hoja

COSTO_MAQUINA_MIN = 8.0   # $/minuto de uso de láser (real Milens)
MARGEN_LASER      = 0.50  # 50% ganancia

MATERIALES_LASER = {
    # MDF
    "mdf_3":      {"nombre": "MDF 2.7mm",           "costo_cm2": round(110  / (122*244), 4), "precio_hoja": 110,  "alias": ["2.7","mdf3","mdf_3mm","mdf 3"]},
    "mdf_3mm":    {"nombre": "MDF 2.7mm",           "costo_cm2": round(110  / (122*244), 4), "precio_hoja": 110,  "alias": []},
    "mdf_6":      {"nombre": "MDF 5.5mm",           "costo_cm2": round(280  / (122*244), 4), "precio_hoja": 280,  "alias": ["5.5","mdf6","mdf_6mm","mdf 6"]},
    "mdf_6mm":    {"nombre": "MDF 5.5mm",           "costo_cm2": round(280  / (122*244), 4), "precio_hoja": 280,  "alias": []},
    "multiplay":  {"nombre": "Multiplay 4mm",       "costo_cm2": round(350  / (122*244), 4), "precio_hoja": 350,  "alias": ["triplay","4mm","plywood"]},
    "triplay":    {"nombre": "Multiplay 4mm",       "costo_cm2": round(350  / (122*244), 4), "precio_hoja": 350,  "alias": []},
    # Acrílico
    "acrilico":   {"nombre": "Acrílico 3mm Color", "costo_cm2": round(900  / (120*180), 4), "precio_hoja": 900,  "alias": ["acrilico color","acrílico"]},
    "acrilico_t": {"nombre": "Acrílico 3mm Trans.", "costo_cm2": round(800  / (120*180), 4), "precio_hoja": 800,  "alias": ["transparente","cristal","acrilico transparente"]},
    "acrilico_6": {"nombre": "Acrílico 6mm",       "costo_cm2": round(1800 / (120*180), 4), "precio_hoja": 1800, "alias": ["acrilico 6","acrilico grueso"]},
}

SERVICIOS_SUBLIMACION = {
    "tarjeta":    {"nombre": "Tarjeta presentación", "precio_unit": 8,   "minimo": 50},
    "lona_m2":    {"nombre": "Lona (por m²)",         "precio_unit": 180, "minimo": 1},
    "taza":       {"nombre": "Taza Cerámica 11oz",    "precio_unit": 95,  "minimo": 12},
    "taza_magica":{"nombre": "Taza Mágica",           "precio_unit": 150, "minimo": 6},
    "termo_20":   {"nombre": "Termo 20oz Skinny",     "precio_unit": 280, "minimo": 1},
    "termo_30":   {"nombre": "Termo 30oz",            "precio_unit": 320, "minimo": 1},
    "termo_40":   {"nombre": "Termo 40oz Travel",     "precio_unit": 450, "minimo": 1},
    "playera":    {"nombre": "Playera Poliéster Subli","precio_unit": 180, "minimo": 6},
    "playera_dtf":{"nombre": "Playera Algodón DTF",   "precio_unit": 250, "minimo": 6},
    "gorra":      {"nombre": "Gorra Subli/Vinil",     "precio_unit": 120, "minimo": 6},
    "mousepad":   {"nombre": "Mousepad",              "precio_unit": 65,  "minimo": 10},
}

# ── DPI por servicio ──────────────────────────────────────────────────────────
DPI_SERVICIO = {
    "sublimacion": 300,
    "laser":       1200,  # vectorial, pero para raster 1200dpi
    "lona":        100,   # gran formato: 100dpi al tamaño final
    "dtf":         300,
    "tarjeta":     300,
}

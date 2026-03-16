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

# ── Servicios Milens ──────────────────────────────────────────────────────────
MATERIALES_LASER = {
    "mdf_3mm":    {"nombre": "MDF 3mm",    "costo_cm2": 0.08},
    "mdf_6mm":    {"nombre": "MDF 6mm",    "costo_cm2": 0.12},
    "acrilico":   {"nombre": "Acrílico",   "costo_cm2": 0.18},
    "triplay":    {"nombre": "Triplay",    "costo_cm2": 0.10},
}

SERVICIOS_SUBLIMACION = {
    "tarjeta":    {"nombre": "Tarjeta presentación", "precio_unit": 8,   "minimo": 50},
    "lona_m2":    {"nombre": "Lona (por m²)",         "precio_unit": 180, "minimo": 1},
    "taza":       {"nombre": "Taza sublimada",        "precio_unit": 85,  "minimo": 12},
    "playera":    {"nombre": "Playera sublimada",     "precio_unit": 120, "minimo": 6},
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

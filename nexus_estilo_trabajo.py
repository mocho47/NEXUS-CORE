# -*- coding: utf-8 -*-
"""
NEXUS — Estilo de Trabajo de Anuar (Simplex GDL)
Este módulo enseña a NEXUS cómo trabaja el propietario
para que actúe de forma autónoma con el mismo criterio.
"""

PERFIL = {
    "propietario": "Anuar — Simplex GDL",
    "telefono": "3326148674",

    # ── IMPRESIÓN ──────────────────────────────────────────────────────────
    "impresion": {
        "dpi": 300,
        "formatos_salida": ["pdf", "png"],  # siempre ambos
        "unidades": "cm",
        "directorio": "C:/nexus/MERCH_OUTPUT/",
        "abrir_al_terminar": True,
        "marcas_corte": True,
        "tick_mm": 3,
        "color_guia": (220, 220, 220),
        "regla": "Sin márgenes propios — la maquiladora maneja el acomodo",
    },

    # ── PLANILLAS ──────────────────────────────────────────────────────────
    "planillas": {
        "regla": "Calcular máximo de piezas que caben. Gap uniforme para centrar.",
        "tipos_frecuentes": [
            {"nombre": "Sticker redondo",   "tamano_cm": 4,   "hoja": "33x48"},
            {"nombre": "Etiqueta vertical", "tamano_cm": "4x8", "hoja": "60x100"},
            {"nombre": "Llavero MDF",       "tamano_cm": "8x4", "hoja": "carta"},
            {"nombre": "Iman grande",       "tamano_cm": "9x6", "hoja": "carta"},
        ],
        "nombre_archivo": "{tipo}_{descripcion}_{hoja}cm.pdf",
    },

    # ── COTIZACIONES ───────────────────────────────────────────────────────
    "cotizaciones": {
        "columnas": ["producto", "codigo", "cantidad", "precio_dist", "total_dist",
                     "precio_pub", "total_pub"],
        "siempre_incluir": ["ganancia_neta", "margen_pct", "mano_de_obra"],
        "colores": {
            "header":  "#1a1a6e",  # azul marino
            "totales": "#003322",  # verde oscuro
            "acento":  "#00ff88",  # verde neón
            "fila_a":  "#ffffff",
            "fila_b":  "#eef2ff",
        },
        "footer": "ATF by Simplex  |  3326148674  |  Generado con NEXUS",
        "nombre_archivo": "Cotizacion_{descripcion}_{fecha}.pdf",
    },

    # ── NEGOCIOS ───────────────────────────────────────────────────────────
    "negocios": {
        "atf": {
            "nombre": "ATF by Simplex",
            "giro": "Retrofit Faros LED",
            "ciudad": "Guadalajara",
            "tel": "3326148674",
            "catalogo": "ilume_prices.json",
            "mano_obra": {"basico": 800, "pro": 2500, "elite": "cotizar"},
        },
        "milens": {
            "nombre": "Milens by Simplex",
            "giro": "Corte Láser MDF/Acrílico",
            "ciudad": "Guadalajara",
            "tel": "3326148674",
        },
        "canbusfix": {
            "nombre": "CanbusFix by Simplex",
            "giro": "Red Instaladores Retrofit",
            "ciudad": "Guadalajara",
            "tel": "3326148674",
        },
    },

    # ── CLIENTES EXTERNOS (maquiladora/diseño) ─────────────────────────────
    "clientes_externos": {
        "regla": "Recibe JPG/PNG/PDF de terceros. Solo escala y acomoda. NO modifica diseño.",
        "ejemplos": ["tortillas", "aguas frescas", "pozole", "tarjetas"],
        "flujo": [
            "1. Recibe archivo + medidas deseadas",
            "2. Escala a cm exactos a 300 DPI",
            "3. Si pide planilla: calcula piezas y genera",
            "4. Si pide 1 sola: genera PDF exacto para maquiladora",
            "5. Abre automáticamente al terminar",
        ],
    },

    # ── COMPORTAMIENTO NEXUS ───────────────────────────────────────────────
    "nexus_comportamiento": {
        "autonomia": "TOTAL — no pedir confirmación para generar archivos",
        "preguntar_solo_si": [
            "El tamaño no está claro",
            "El archivo no se encuentra",
            "Hay conflicto entre medidas y diseño",
        ],
        "nunca_preguntar": [
            "Si usar 300 DPI (siempre sí)",
            "Si generar PDF (siempre sí)",
            "Si abrir el archivo al terminar (siempre sí)",
            "Si incluir ganancia en cotización (siempre sí)",
        ],
        "estilo_respuesta": "Directo. Resultado primero. Sin relleno.",
    },
}


def get_perfil():
    """Retorna el perfil completo de trabajo."""
    return PERFIL


def get_config_impresion():
    return PERFIL["impresion"]


def get_config_cotizacion():
    return PERFIL["cotizaciones"]


def get_negocio(nombre: str):
    return PERFIL["negocios"].get(nombre.lower(), {})


def comportamiento_autonomo(tarea: str) -> dict:
    """
    Dado el texto de una tarea, retorna cómo debe actuar NEXUS
    según el estilo de trabajo de Anuar.
    """
    tarea = tarea.lower()
    respuesta = {
        "dpi": 300,
        "formatos": ["pdf", "png"],
        "abrir": True,
        "directorio": PERFIL["impresion"]["directorio"],
        "marcas_corte": True,
        "accion": None,
    }

    if any(w in tarea for w in ["planilla", "hoja", "llenar", "distribuir"]):
        respuesta["accion"] = "generar_planilla"
        respuesta["calcular_piezas"] = True

    elif any(w in tarea for w in ["cotizacion", "cotizar", "precio", "cuanto"]):
        respuesta["accion"] = "generar_cotizacion"
        respuesta["incluir_ganancia"] = True

    elif any(w in tarea for w in ["etiqueta", "sticker", "logo", "ajusta", "tamano"]):
        respuesta["accion"] = "ajustar_etiqueta"

    elif any(w in tarea for w in ["playera", "iman", "llavero", "merch"]):
        respuesta["accion"] = "generar_merch"

    return respuesta


if __name__ == "__main__":
    import json
    print("Perfil de trabajo cargado:")
    print(json.dumps(PERFIL["nexus_comportamiento"], ensure_ascii=False, indent=2))

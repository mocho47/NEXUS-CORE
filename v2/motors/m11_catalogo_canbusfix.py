# -*- coding: utf-8 -*-
"""Motor 11 — Catálogo CanbusFix: servicios y precios."""
import sys
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar

CATALOGO = [
    {"servicio": "Instalacion bi-LED basica",        "precio_desde": 1200, "tiempo": "2-3 hrs"},
    {"servicio": "Instalacion bi-LED premium Aozoom","precio_desde": 1800, "tiempo": "3-4 hrs"},
    {"servicio": "Adaptador canbus anti-error",       "precio_desde":  350, "tiempo": "30 min"},
    {"servicio": "Restauracion de faros (pulido)",    "precio_desde":  800, "tiempo": "2 hrs"},
    {"servicio": "Kit DRL / luces de dia",            "precio_desde":  600, "tiempo": "1-2 hrs"},
    {"servicio": "Angel eyes / halos LED",            "precio_desde":  900, "tiempo": "2 hrs"},
    {"servicio": "Retrofit completo (faros + canbus)","precio_desde": 3500, "tiempo": "4-5 hrs"},
]

@registrar("m11_catalogo_canbusfix")
def catalogo_canbusfix(texto: str = "", **_) -> dict:
    txt = texto.lower()

    # Buscar servicio específico
    for item in CATALOGO:
        palabras = item["servicio"].lower().split()
        if any(p in txt for p in palabras if len(p) > 4):
            return {
                "ok": True,
                "respuesta": (
                    f"{item['servicio']}\n"
                    f"  Precio desde: ${item['precio_desde']:,}\n"
                    f"  Tiempo: {item['tiempo']}"
                ),
                "datos": item
            }

    # Mostrar catálogo completo
    lineas = ["Catalogo de servicios CanbusFix:\n"]
    for item in CATALOGO:
        lineas.append(f"  {item['servicio']:45} desde ${item['precio_desde']:,} | {item['tiempo']}")

    return {"ok": True, "respuesta": "\n".join(lineas), "datos": CATALOGO}

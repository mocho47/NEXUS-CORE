# -*- coding: utf-8 -*-
"""
Motor 7 — Cotizador ATF
Una función: recibe modelo Aozoom + datos → devuelve cotización completa.
"""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')

from cerebro import registrar
from config import AOZOOM, ganancia_atf

@registrar("m07_cotizar_atf")
def cotizar_atf(texto: str = "", modelo: str = "", cliente: str = "",
                cantidad: int = 1, **_) -> dict:
    """
    Detecta el modelo Aozoom en el texto y devuelve la cotización.
    También acepta modelo y cliente directamente como params.
    """
    # Detectar modelo en el texto si no se pasó directo
    if not modelo:
        match = re.search(r'\bX([1-7])\b', texto, re.IGNORECASE)
        if match:
            modelo = f"X{match.group(1).upper()}"

    if not modelo:
        # Listar todos los disponibles
        lineas = ["Kits Aozoom disponibles:\n"]
        for k, v in AOZOOM.items():
            g = ganancia_atf(k)
            lineas.append(
                f"  {k}: Dist ${v['dist']:,} | Pub ${v['pub']:,} | "
                f"Ganancia ${g['ganancia']:,} ({g['margen']}%)"
            )
        return {"ok": True, "respuesta": "\n".join(lineas), "datos": AOZOOM}

    modelo = modelo.upper()
    if modelo not in AOZOOM:
        disponibles = ", ".join(AOZOOM.keys())
        return {"ok": False, "respuesta": f"Modelo '{modelo}' no existe. Disponibles: {disponibles}"}

    g = ganancia_atf(modelo)
    cant_txt = f" x{cantidad}" if cantidad > 1 else ""
    total_dist = g['dist'] * cantidad
    total_pub  = g['pub']  * cantidad
    total_gan  = g['ganancia'] * cantidad

    cliente_txt = f" para {cliente}" if cliente else ""

    respuesta = (
        f"Cotización {g['nombre']}{cant_txt}{cliente_txt}\n"
        f"  Precio dist:   ${total_dist:,}\n"
        f"  Precio público: ${total_pub:,}\n"
        f"  Tu ganancia:   ${total_gan:,} ({g['margen']}%)"
    )

    # Mensaje listo para WhatsApp
    wa = (
        f"Hola{', ' + cliente if cliente else ''}! "
        f"Te cotizo el {g['nombre']}{cant_txt} en ${total_pub:,} pesos. "
        f"Incluye instalación profesional con garantía. "
        f"¿Te agendo una cita?"
    )

    return {
        "ok": True,
        "respuesta": respuesta,
        "datos": {
            "modelo": modelo,
            "cantidad": cantidad,
            "dist": total_dist,
            "pub": total_pub,
            "ganancia": total_gan,
            "margen": g["margen"],
            "whatsapp": wa,
        }
    }

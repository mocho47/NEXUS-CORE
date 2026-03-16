# -*- coding: utf-8 -*-
"""
Motor 2 — Cotizador Sublimación
Una función: servicio + cantidad → precio con ganancia.
"""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')

from cerebro import registrar
from config import SERVICIOS_SUBLIMACION

# Margen de ganancia estándar Milens
MARGEN_SUBLIMACION = 0.45  # 45% ganancia sobre costo

@registrar("m02_cotizar_sub")
def cotizar_sub(texto: str = "", servicio: str = "", cantidad: int = 0, **_) -> dict:
    """
    Detecta servicio y cantidad en el texto y cotiza.
    """
    txt = texto.lower()

    # Detectar cantidad en el texto
    if not cantidad:
        m = re.search(r'(\d+)\s*(tarjetas?|lonas?|tazas?|playeras?|mousepads?|piezas?|pzas?)', txt)
        if m:
            cantidad = int(m.group(1))

    # Detectar servicio en el texto
    if not servicio:
        if "tarjeta" in txt:          servicio = "tarjeta"
        elif "lona" in txt:           servicio = "lona_m2"
        elif "taza" in txt:           servicio = "taza"
        elif "playera" in txt:        servicio = "playera"
        elif "mousepad" in txt:       servicio = "mousepad"

    if not servicio:
        # Listar servicios disponibles
        lineas = ["Servicios de sublimacion disponibles:\n"]
        for k, v in SERVICIOS_SUBLIMACION.items():
            lineas.append(f"  {v['nombre']}: ${v['precio_unit']:,}/pza (min {v['minimo']} pzas)")
        return {"ok": True, "respuesta": "\n".join(lineas), "datos": SERVICIOS_SUBLIMACION}

    svc = SERVICIOS_SUBLIMACION.get(servicio)
    if not svc:
        return {"ok": False, "respuesta": f"Servicio '{servicio}' no encontrado."}

    cantidad = cantidad or svc["minimo"]
    precio_unit = svc["precio_unit"]
    total_pub   = precio_unit * cantidad
    costo_est   = round(total_pub * (1 - MARGEN_SUBLIMACION))
    ganancia    = total_pub - costo_est
    margen_pct  = round((ganancia / total_pub) * 100, 1)

    respuesta = (
        f"Cotizacion {svc['nombre']} x{cantidad}\n"
        f"  Precio unitario: ${precio_unit:,}\n"
        f"  Total:           ${total_pub:,}\n"
        f"  Ganancia est.:   ${ganancia:,} ({margen_pct}%)\n"
        f"  Minimo pedido:   {svc['minimo']} pzas"
    )

    wa = (
        f"Hola! Cotizacion de {svc['nombre']}: "
        f"{cantidad} piezas = ${total_pub:,} pesos. "
        f"Tiempo de entrega 3-5 dias habiles. "
        f"Te mando muestra de diseno? "
    )

    return {
        "ok": True,
        "respuesta": respuesta,
        "datos": {
            "servicio": servicio,
            "nombre": svc["nombre"],
            "cantidad": cantidad,
            "precio_unit": precio_unit,
            "total": total_pub,
            "ganancia": ganancia,
            "margen": margen_pct,
            "whatsapp": wa,
        }
    }

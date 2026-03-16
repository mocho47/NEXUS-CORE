# -*- coding: utf-8 -*-
"""
Motor 4 — Cotizador Láser
Una función: material + dimensiones + tipo → precio con ganancia.
"""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')

from cerebro import registrar
from config import MATERIALES_LASER, COSTO_MAQUINA_MIN, MARGEN_LASER

@registrar("m04_cotizar_laser")
def cotizar_laser(texto: str = "", material: str = "", ancho: float = 0,
                  alto: float = 0, tipo: str = "corte", cantidad: int = 1, **_) -> dict:
    """
    Cotiza trabajo láser por material y dimensiones.
    Detecta datos del texto si no se pasan directamente.
    """
    txt = texto.lower()

    # Detectar dimensiones en texto: "20x30", "20 x 30", "20cm x 30cm"
    if not ancho or not alto:
        m = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', texto)
        if m:
            ancho = float(m.group(1))
            alto  = float(m.group(2))

    # Detectar material — busca en aliases también
    if not material:
        matched = None
        for key, mat_data in MATERIALES_LASER.items():
            all_terms = [key] + mat_data.get("alias", [])
            if any(a in txt for a in all_terms):
                matched = key
                break
        material = matched or "mdf_3"  # default MDF 2.7mm

    # Detectar tipo
    if "grab" in txt:  tipo = "grabado"
    elif "cort" in txt: tipo = "corte"

    # Detectar cantidad
    if not cantidad or cantidad == 1:
        m = re.search(r'(\d+)\s*(?:piezas?|pzas?|unidades?)', txt)
        if m:
            cantidad = int(m.group(1))

    if not ancho or not alto:
        lineas = ["Especifica dimensiones. Ejemplo: 'cotiza laser 20x30 mdf'\n"]
        lineas.append("Materiales disponibles:")
        for k, v in MATERIALES_LASER.items():
            lineas.append(f"  {v['nombre']}: ${v['costo_cm2']}/cm²")
        return {"ok": True, "respuesta": "\n".join(lineas)}

    mat = MATERIALES_LASER.get(material, MATERIALES_LASER["mdf_3"])
    area_cm2 = (ancho * alto) / 100  # mm² → cm²

    # Tiempo estimado de corte (aprox 1 min por 50cm² para corte, 30cm² para grabado)
    velocidad = 50 if tipo == "corte" else 30
    tiempo_min = max(2, area_cm2 / velocidad)

    costo_material = area_cm2 * mat["costo_cm2"] * cantidad
    costo_maquina  = tiempo_min * COSTO_MAQUINA_MIN * cantidad
    costo_total    = costo_material + costo_maquina
    precio_pub     = round(costo_total / (1 - MARGEN_LASER))
    ganancia       = precio_pub - costo_total

    unidad_txt = f" x{cantidad}" if cantidad > 1 else ""

    respuesta = (
        f"Cotizacion laser {tipo} — {mat['nombre']}{unidad_txt}\n"
        f"  Dimensiones:  {ancho}×{alto}mm\n"
        f"  Tiempo est.:  {tiempo_min:.1f} min/pza\n"
        f"  Costo total:  ${costo_total:,.0f}\n"
        f"  Precio pub:   ${precio_pub:,.0f}\n"
        f"  Tu ganancia:  ${ganancia:,.0f} ({MARGEN_LASER*100:.0f}%)"
    )

    wa = (
        f"Hola! Cotizacion de {tipo} laser en {mat['nombre']}, "
        f"{ancho}x{alto}mm{unidad_txt}: ${precio_pub:,.0f} pesos. "
        f"Entrega en 2-3 dias. Te mando preview del diseno?"
    )

    return {
        "ok": True,
        "respuesta": respuesta,
        "datos": {
            "material": mat["nombre"],
            "ancho": ancho, "alto": alto,
            "tipo": tipo, "cantidad": cantidad,
            "tiempo_min": round(tiempo_min, 1),
            "costo": round(costo_total, 2),
            "precio_pub": round(precio_pub, 2),
            "ganancia": round(ganancia, 2),
            "margen": MARGEN_LASER * 100,
            "whatsapp": wa,
        }
    }

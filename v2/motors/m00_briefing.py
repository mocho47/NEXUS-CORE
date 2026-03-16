# -*- coding: utf-8 -*-
"""Motor 0 — Briefing del día: qué tienes hoy sin gastar tokens Groq."""
import sys
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now
from datetime import datetime, timedelta

@registrar("m00_briefing")
def briefing(texto: str = "", **_) -> dict:
    hoy     = now()[:10]
    manana  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    semana  = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    secciones = []

    with _conn() as c:
        # Pedidos que entregan hoy
        hoy_pedidos = rows_to_list(c.execute(
            "SELECT cliente_nombre, descripcion FROM pedidos WHERE fecha_entrega=? AND estado!='entregado'",
            (hoy,)
        ).fetchall())

        # Pedidos atrasados
        atrasados = rows_to_list(c.execute(
            "SELECT cliente_nombre, descripcion, fecha_entrega FROM pedidos WHERE fecha_entrega<? AND estado NOT IN ('entregado','cancelado') AND fecha_entrega!=''",
            (hoy,)
        ).fetchall())

        # Listos para entregar
        listos = rows_to_list(c.execute(
            "SELECT cliente_nombre, descripcion FROM pedidos WHERE estado='listo'"
        ).fetchall())

        # Instalaciones ATF hoy
        instalaciones = rows_to_list(c.execute(
            "SELECT cliente, modelo_kit, hora FROM agenda_atf WHERE fecha=? AND estado!='cancelado'",
            (hoy,)
        ).fetchall())

        # Prospectos calientes (pipeline en seguimiento)
        prospectos = rows_to_list(c.execute(
            "SELECT cliente, servicio FROM pipeline WHERE estado IN ('cotizado','seguimiento') ORDER BY updated_at DESC LIMIT 5"
        ).fetchall())

        # Total pedidos activos
        total_activos = c.execute(
            "SELECT COUNT(*) as n FROM pedidos WHERE estado NOT IN ('entregado','cancelado')"
        ).fetchone()["n"]

    # Construir briefing
    hora_actual = datetime.now().strftime("%H:%M")
    secciones.append(f"NEXUS — Briefing {hoy} {hora_actual}\n")

    if instalaciones:
        secciones.append(f"INSTALACIONES HOY ({len(instalaciones)}):")
        for i in instalaciones:
            hora = f" a las {i['hora']}" if i.get('hora') else ""
            secciones.append(f"  {i['cliente']} — {i.get('modelo_kit','kit')} {hora}")

    if hoy_pedidos:
        secciones.append(f"\nENTREGAS HOY ({len(hoy_pedidos)}):")
        for p in hoy_pedidos:
            secciones.append(f"  {p['cliente_nombre']}: {p['descripcion'][:40]}")

    if atrasados:
        secciones.append(f"\nATRASADOS ({len(atrasados)}) — URGENTE:")
        for p in atrasados:
            secciones.append(f"  {p['cliente_nombre']}: {p['descripcion'][:35]} (vencio {p['fecha_entrega']})")

    if listos:
        secciones.append(f"\nLISTOS PARA ENTREGAR ({len(listos)}):")
        for p in listos:
            secciones.append(f"  {p['cliente_nombre']}: {p['descripcion'][:40]}")

    if prospectos:
        secciones.append(f"\nPROSPECTOS ACTIVOS ({len(prospectos)}):")
        for p in prospectos:
            secciones.append(f"  {p['cliente']} — {p.get('servicio','')}")

    secciones.append(f"\nTotal pedidos activos: {total_activos}")

    if not any([instalaciones, hoy_pedidos, atrasados, listos, prospectos]):
        secciones.append("Agenda limpia. Buen dia para prospectar.")

    return {
        "ok": True,
        "respuesta": "\n".join(secciones),
        "datos": {
            "instalaciones": instalaciones,
            "entregas_hoy": hoy_pedidos,
            "atrasados": atrasados,
            "listos": listos,
            "prospectos": prospectos,
            "total_activos": total_activos,
        }
    }

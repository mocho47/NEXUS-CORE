# -*- coding: utf-8 -*-
"""Motor 8 — Agenda ATF: registra y consulta instalaciones."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now

@registrar("m08_agenda_atf")
def agenda_atf(texto: str = "", accion: str = "", **_) -> dict:
    txt = texto.lower()

    # Ver agenda del día o semana
    if any(w in txt for w in ["ver", "agenda", "qué tengo", "instalaciones", "hoy", "semana"]):
        hoy = now()[:10]
        with _conn() as c:
            if "semana" in txt:
                from datetime import datetime, timedelta
                fin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                rows = c.execute(
                    "SELECT * FROM agenda_atf WHERE fecha BETWEEN ? AND ? AND estado!='cancelado' ORDER BY fecha,hora",
                    (hoy, fin)
                ).fetchall()
                titulo = "Agenda ATF — proximos 7 dias"
            else:
                rows = c.execute(
                    "SELECT * FROM agenda_atf WHERE fecha=? AND estado!='cancelado' ORDER BY hora",
                    (hoy,)
                ).fetchall()
                titulo = f"Instalaciones hoy {hoy}"

        instalaciones = rows_to_list(rows)
        if not instalaciones:
            return {"ok": True, "respuesta": f"Sin instalaciones agendadas ({titulo})."}

        lineas = [f"{titulo} ({len(instalaciones)}):\n"]
        for i in instalaciones:
            hora = f" a las {i['hora']}" if i.get("hora") else ""
            lineas.append(
                f"  {i['fecha']}{hora} — {i['cliente']} | {i.get('modelo_kit','')} | {i.get('carro','')}"
            )
        return {"ok": True, "respuesta": "\n".join(lineas), "datos": instalaciones}

    # Registrar nueva instalación
    cliente = ""
    m = re.search(r'(?:para|cliente)\s+([A-ZÁÉÍÓÚa-záéíóú][a-záéíóú\s]{2,25})', texto, re.IGNORECASE)
    if m:
        cliente = m.group(1).strip()

    modelo = ""
    m2 = re.search(r'\b(X[1-7])\b', texto, re.IGNORECASE)
    if m2:
        modelo = m2.group(1).upper()

    fecha = now()[:10]
    m3 = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2})', texto)
    if m3:
        fecha = m3.group(1)

    hora = ""
    m4 = re.search(r'(\d{1,2}(?::\d{2})?)\s*(?:hrs?|am|pm|horas?)?', texto, re.IGNORECASE)
    if m4:
        hora = m4.group(1)

    carro = ""
    m5 = re.search(r'(?:en|para)\s+([A-Z][a-z]+(?:\s+\d{4})?)', texto)
    if m5:
        carro = m5.group(1)

    if not cliente:
        return {"ok": False, "respuesta": "¿Para qué cliente es la instalación? Ej: 'agenda instalacion X1 para Juan el martes'"}

    with _conn() as c:
        cur = c.execute(
            "INSERT INTO agenda_atf (cliente, modelo_kit, carro, fecha, hora) VALUES (?,?,?,?,?)",
            (cliente, modelo, carro, fecha, hora)
        )
        aid = cur.lastrowid

    respuesta = (
        f"Instalacion agendada #{aid}\n"
        f"  Cliente: {cliente}\n"
        f"  Kit: {modelo or '—'} | Carro: {carro or '—'}\n"
        f"  Fecha: {fecha}{' a las ' + hora if hora else ''}"
    )
    return {"ok": True, "respuesta": respuesta,
            "datos": {"id": aid, "cliente": cliente, "modelo": modelo, "fecha": fecha}}

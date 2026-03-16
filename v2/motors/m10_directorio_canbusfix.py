# -*- coding: utf-8 -*-
"""Motor 10 — Directorio CanbusFix: instaladores por ciudad."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list

# Semilla de instaladores iniciales
_SEMILLA = [
    ("Anuar Gonzalez", "Guadalajara", "3326148674", "ATF,CanbusFix,Milens"),
    ("Instalador Demo 1", "Monterrey", "8112345678", "CanbusFix,ATF"),
    ("Instalador Demo 2", "CDMX", "5512345678", "CanbusFix"),
]

def _seed():
    with _conn() as c:
        existing = c.execute("SELECT COUNT(*) as n FROM instaladores_canbusfix").fetchone()["n"]
        if existing == 0:
            for nombre, ciudad, tel, esp in _SEMILLA:
                c.execute(
                    "INSERT INTO instaladores_canbusfix (nombre, ciudad, telefono, especialidades) VALUES (?,?,?,?)",
                    (nombre, ciudad, tel, esp)
                )

_seed()

@registrar("m10_directorio_canbusfix")
def directorio_canbusfix(texto: str = "", ciudad: str = "", **_) -> dict:
    txt = texto.lower()

    # Detectar ciudad en texto
    if not ciudad:
        ciudades = ["guadalajara", "monterrey", "cdmx", "mexico", "puebla", "tijuana",
                    "queretaro", "leon", "morelia", "zapopan"]
        for c in ciudades:
            if c in txt:
                ciudad = c.capitalize()
                break

    with _conn() as c:
        if ciudad:
            rows = rows_to_list(c.execute(
                "SELECT * FROM instaladores_canbusfix WHERE ciudad LIKE ? AND activo=1",
                (f"%{ciudad}%",)
            ).fetchall())
        else:
            rows = rows_to_list(c.execute(
                "SELECT * FROM instaladores_canbusfix WHERE activo=1 ORDER BY ciudad"
            ).fetchall())

    if not rows:
        return {"ok": True, "respuesta": f"Sin instaladores registrados{' en ' + ciudad if ciudad else ''}."}

    lineas = [f"Instaladores CanbusFix{' en ' + ciudad if ciudad else ''} ({len(rows)}):\n"]
    for i in rows:
        esp = i.get("especialidades", "")
        lineas.append(f"  {i['nombre']} — {i['ciudad']} | WA: {i['telefono']} | {esp}")

    return {"ok": True, "respuesta": "\n".join(lineas), "datos": rows}

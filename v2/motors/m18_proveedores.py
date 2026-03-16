# -*- coding: utf-8 -*-
"""Motor 18 — Directorio de Proveedores y Distribuidores.
Materia prima, equipos, maquilas. Cotizacion externa con margen."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now

def listar_proveedores(categoria: str = "", q: str = "") -> list:
    with _conn() as c:
        if q:
            rows = c.execute(
                """SELECT * FROM proveedores
                   WHERE activo=1 AND (
                       nombre LIKE ? OR empresa LIKE ? OR
                       productos LIKE ? OR categoria LIKE ?
                   ) ORDER BY categoria, nombre""",
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
            ).fetchall()
        elif categoria:
            rows = c.execute(
                "SELECT * FROM proveedores WHERE activo=1 AND categoria LIKE ? ORDER BY nombre",
                (f"%{categoria}%",)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM proveedores WHERE activo=1 ORDER BY categoria, nombre"
            ).fetchall()
    return rows_to_list(rows)

def nuevo_proveedor(nombre: str, empresa: str = "", telefono: str = "",
                    categoria: str = "", productos: str = "",
                    precio_notas: str = "", tiempo_entrega: str = "",
                    condiciones: str = "") -> dict:
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO proveedores
               (nombre, empresa, telefono, categoria, productos,
                precio_notas, tiempo_entrega, condiciones)
               VALUES (?,?,?,?,?,?,?,?)""",
            (nombre, empresa, telefono, categoria, productos,
             precio_notas, tiempo_entrega, condiciones)
        )
    return {"ok": True, "id": cur.lastrowid, "nombre": nombre}

@registrar("m18_proveedores")
def motor_proveedores(texto: str = "", **_) -> dict:
    txt = texto.lower()

    # Buscar proveedor específico
    m = re.search(r'(?:proveedor|distribuidor|quien surte|surte)\s+(?:de\s+)?(.+)', txt)
    q = m.group(1).strip() if m else ""

    provs = listar_proveedores(q=q)

    if not provs:
        return {
            "ok": True,
            "respuesta": "Sin proveedores registrados aun. Agrega uno desde el panel.",
            "datos": []
        }

    lineas = [f"Proveedores ({len(provs)}):\n"]
    cat_actual = None
    for p in provs:
        if p.get("categoria") != cat_actual:
            cat_actual = p.get("categoria", "")
            if cat_actual:
                lineas.append(f"\n  [{cat_actual.upper()}]")
        lineas.append(f"  {p['nombre']}" +
                      (f" ({p['empresa']})" if p.get('empresa') else "") +
                      (f" — WA: {p['telefono']}" if p.get('telefono') else ""))
        if p.get("productos"):
            lineas.append(f"    Suministra: {p['productos'][:60]}")
        if p.get("tiempo_entrega"):
            lineas.append(f"    Entrega: {p['tiempo_entrega']}")

    return {
        "ok": True,
        "respuesta": "\n".join(lineas),
        "datos": provs
    }

# -*- coding: utf-8 -*-
"""Motor 17 — Pipeline de Ventas: Prospecto→Cotizado→Seguimiento→Cerrado→Entregado."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now

ESTADOS = ["prospecto", "cotizado", "seguimiento", "cerrado", "entregado", "perdido"]

@registrar("m17_pipeline")
def pipeline(texto: str = "", accion: str = "", **_) -> dict:
    txt = texto.lower()

    # Ver pipeline completo
    if any(w in txt for w in ["ver", "pipeline", "embudo", "estado", "ventas", "prospectos"]):
        with _conn() as c:
            rows = rows_to_list(c.execute(
                """SELECT estado, COUNT(*) as total, SUM(valor) as valor_total
                   FROM pipeline WHERE estado NOT IN ('perdido')
                   GROUP BY estado ORDER BY
                   CASE estado
                     WHEN 'prospecto'   THEN 1
                     WHEN 'cotizado'    THEN 2
                     WHEN 'seguimiento' THEN 3
                     WHEN 'cerrado'     THEN 4
                     WHEN 'entregado'   THEN 5
                   END""",
            ).fetchall())
            todos = rows_to_list(c.execute(
                "SELECT * FROM pipeline WHERE estado NOT IN ('perdido','entregado') ORDER BY updated_at DESC"
            ).fetchall())

        if not rows:
            return {"ok": True, "respuesta": "Pipeline vacío. Agrega prospectos con 'nuevo prospecto [cliente] [servicio]'."}

        lineas = ["Pipeline de ventas:\n"]
        for r in rows:
            val = f"${r['valor_total']:,.0f}" if r.get("valor_total") else "$0"
            lineas.append(f"  {r['estado'].upper():15} {r['total']} clientes — {val}")

        if todos:
            lineas.append("\nDetalle:")
            for p in todos[:10]:
                val = f" ${p['valor']:,.0f}" if p.get("valor") else ""
                lineas.append(f"  [{p['estado']}] {p['cliente']} — {p.get('servicio','')}{val}")

        return {"ok": True, "respuesta": "\n".join(lineas), "datos": {"resumen": rows, "detalle": todos}}

    # Nuevo prospecto
    if any(w in txt for w in ["nuevo", "agrega", "registra", "prospecto"]):
        cliente = ""
        m = re.search(r'(?:prospecto|para|cliente)\s+([A-ZÁÉÍÓÚa-záéíóú][a-záéíóú\s]{2,25})',
                      texto, re.IGNORECASE)
        if m:
            cliente = m.group(1).strip()
        if not cliente:
            return {"ok": False, "respuesta": "¿Qué cliente es el prospecto?"}

        servicio = ""
        for s in ["atf", "laser", "sub", "sublimacion", "canbusfix", "tarjeta", "lona"]:
            if s in txt:
                servicio = s
                break

        valor = 0
        mv = re.search(r'\$\s*(\d+(?:,\d{3})*)', texto)
        if mv:
            valor = float(mv.group(1).replace(",", ""))

        with _conn() as c:
            cur = c.execute(
                "INSERT INTO pipeline (cliente, servicio, valor, estado) VALUES (?,?,?,'prospecto')",
                (cliente, servicio, valor)
            )
            pid = cur.lastrowid

        return {
            "ok": True,
            "respuesta": f"Prospecto #{pid} agregado: {cliente} — {servicio or 'servicio por definir'}",
            "datos": {"id": pid, "cliente": cliente, "estado": "prospecto"}
        }

    # Mover estado
    m_estado = re.search(r'\b(' + '|'.join(ESTADOS) + r')\b', txt)
    m_cliente = re.search(r'(?:de|mover|actualiza)\s+([A-ZÁÉÍÓÚa-záéíóú][a-záéíóú\s]{2,25})',
                          texto, re.IGNORECASE)
    if m_estado and m_cliente:
        estado   = m_estado.group(1)
        cliente  = m_cliente.group(1).strip()
        with _conn() as c:
            c.execute(
                "UPDATE pipeline SET estado=?, updated_at=? WHERE cliente LIKE ?",
                (estado, now(), f"%{cliente}%")
            )
        return {"ok": True, "respuesta": f"{cliente} movido a [{estado}]."}

    return {"ok": True, "respuesta": "Pipeline: usa 'ver pipeline', 'nuevo prospecto [nombre]' o 'mover [nombre] a [estado]'."}

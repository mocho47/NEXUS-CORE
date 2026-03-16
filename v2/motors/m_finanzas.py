# -*- coding: utf-8 -*-
"""Motor Finanzas — resumen de ingresos, ganancias y métricas del taller."""
import sys
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now
from datetime import datetime, timedelta

@registrar("m_finanzas")
def finanzas(texto: str = "", **_) -> dict:
    txt  = texto.lower()
    hoy  = now()[:10]
    mes  = hoy[:7]  # YYYY-MM

    # Rango según texto
    if "semana" in txt:
        desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        periodo = "ultimos 7 dias"
    elif "mes" in txt:
        desde = f"{mes}-01"
        periodo = f"mes actual ({mes})"
    else:
        desde = f"{mes}-01"
        periodo = f"mes actual ({mes})"

    with _conn() as c:
        # Pedidos entregados en el periodo
        entregados = rows_to_list(c.execute(
            """SELECT cliente_nombre, descripcion, precio, servicio
               FROM pedidos
               WHERE estado='entregado' AND updated_at >= ?
               AND precio IS NOT NULL AND precio > 0
               ORDER BY precio DESC""",
            (desde + " 00:00",)
        ).fetchall())

        # Pipeline cerrado
        cerrados = rows_to_list(c.execute(
            """SELECT cliente, servicio, valor FROM pipeline
               WHERE estado='cerrado' AND updated_at >= ?
               AND valor IS NOT NULL AND valor > 0""",
            (desde + " 00:00",)
        ).fetchall())

        # Pedidos activos con precio
        activos_valor = c.execute(
            "SELECT SUM(precio) as total FROM pedidos WHERE estado NOT IN ('entregado','cancelado') AND precio>0"
        ).fetchone()["total"] or 0

    total_facturado  = sum(p.get("precio", 0) or 0 for p in entregados)
    total_pipeline   = sum(p.get("valor",  0) or 0 for p in cerrados)
    total_combinado  = total_facturado + total_pipeline
    ganancia_est     = round(total_combinado * 0.45)  # margen promedio 45%

    if not entregados and not cerrados:
        return {
            "ok": True,
            "respuesta": (
                f"Finanzas — {periodo}\n"
                f"  Sin ventas registradas aun.\n"
                f"  En proceso (estimado): ${activos_valor:,.0f}"
            ),
            "datos": {"periodo": periodo, "total": 0}
        }

    lineas = [f"Finanzas — {periodo}\n"]
    lineas.append(f"  Facturado:      ${total_facturado:,.0f}")
    lineas.append(f"  Pipeline cerrado: ${total_pipeline:,.0f}")
    lineas.append(f"  TOTAL:          ${total_combinado:,.0f}")
    lineas.append(f"  Ganancia est.:  ${ganancia_est:,.0f} (~45%)")
    lineas.append(f"  En proceso:     ${activos_valor:,.0f}")

    if entregados:
        lineas.append(f"\nTop trabajos:")
        for p in entregados[:5]:
            lineas.append(f"  {p['cliente_nombre']}: ${p.get('precio',0):,.0f} — {p['descripcion'][:30]}")

    return {
        "ok": True,
        "respuesta": "\n".join(lineas),
        "datos": {
            "periodo": periodo,
            "facturado": total_facturado,
            "pipeline": total_pipeline,
            "total": total_combinado,
            "ganancia_est": ganancia_est,
            "en_proceso": activos_valor,
        }
    }

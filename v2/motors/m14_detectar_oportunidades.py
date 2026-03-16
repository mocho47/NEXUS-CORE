# -*- coding: utf-8 -*-
"""Motor 14 — Detector de Oportunidades: clientes fríos, cotizaciones sin respuesta, pedidos atrasados."""
import sys
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from db import _conn, rows_to_list, now

@registrar("m14_detectar_oportunidades")
def detectar_oportunidades(texto: str = "", dias: int = 7, **_) -> dict:
    import re
    m = re.search(r'(\d+)\s*dias?', texto, re.IGNORECASE)
    if m:
        dias = int(m.group(1))

    hoy = now()[:10]
    oportunidades = []

    with _conn() as c:
        # 1. Pedidos atrasados
        atrasados = rows_to_list(c.execute(
            """SELECT cliente_nombre, descripcion, fecha_entrega, estado FROM pedidos
               WHERE estado NOT IN ('entregado','cancelado')
               AND fecha_entrega < ? AND fecha_entrega != ''""",
            (hoy,)
        ).fetchall())
        for p in atrasados:
            oportunidades.append({
                "tipo": "ATRASADO",
                "cliente": p["cliente_nombre"],
                "detalle": f"Pedido vencido desde {p['fecha_entrega']}: {p['descripcion'][:40]}"
            })

        # 2. Pedidos listos sin entregar (más de 2 días)
        from datetime import datetime, timedelta
        hace2 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        listos = rows_to_list(c.execute(
            """SELECT cliente_nombre, descripcion, updated_at FROM pedidos
               WHERE estado='listo' AND updated_at < ?""",
            (hace2 + " 00:00",)
        ).fetchall())
        for p in listos:
            oportunidades.append({
                "tipo": "LISTO_SIN_ENTREGAR",
                "cliente": p["cliente_nombre"],
                "detalle": f"Listo desde {p['updated_at'][:10]}: {p['descripcion'][:40]}"
            })

        # 3. Prospectos sin mover en el pipeline
        desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
        pipeline_frios = rows_to_list(c.execute(
            """SELECT cliente, servicio, estado, updated_at FROM pipeline
               WHERE estado NOT IN ('cerrado','perdido')
               AND updated_at < ?""",
            (desde + " 00:00",)
        ).fetchall())
        for p in pipeline_frios:
            oportunidades.append({
                "tipo": "PROSPECTO_FRIO",
                "cliente": p["cliente"],
                "detalle": f"Sin mover desde {p['updated_at'][:10]} [{p['estado']}] — {p.get('servicio','')}"
            })

        # 4. Clientes dormidos — último pedido entregado hace >30 días, sin activos
        hace30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        dormidos = rows_to_list(c.execute(
            """SELECT cliente_nombre, MAX(updated_at) as ultima, COUNT(*) as total
               FROM pedidos
               WHERE estado='entregado'
               GROUP BY cliente_id
               HAVING ultima < ?
               AND cliente_id NOT IN (
                   SELECT DISTINCT cliente_id FROM pedidos
                   WHERE estado NOT IN ('entregado','cancelado')
               )
               ORDER BY ultima ASC LIMIT 10""",
            (hace30 + " 00:00",)
        ).fetchall())
        for p in dormidos:
            oportunidades.append({
                "tipo": "REACTIVAR",
                "cliente": p["cliente_nombre"],
                "detalle": f"Ultimo trabajo: {(p['ultima'] or '')[:10]} ({p['total']} pedido{'s' if p['total']>1 else ''} historico{'s' if p['total']>1 else ''})"
            })

    if not oportunidades:
        return {
            "ok": True,
            "respuesta": f"Todo al dia. Sin oportunidades pendientes (revision: {dias} dias).",
            "datos": []
        }

    lineas = [f"Oportunidades detectadas ({len(oportunidades)}):\n"]
    for o in oportunidades:
        lineas.append(f"  [{o['tipo']}] {o['cliente']}: {o['detalle']}")

    return {"ok": True, "respuesta": "\n".join(lineas), "datos": oportunidades}

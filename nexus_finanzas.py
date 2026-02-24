"""
nexus_finanzas.py — Motor de inteligencia financiera para NEXUS.

Calcula en tiempo real desde los datos locales:
  - Ingresos del mes / semana / día (estimados con valor promedio de pedidos)
  - Variación vs período anterior (% de crecimiento)
  - Top clientes por valor total invertido
  - Clientes dormidos (30+ días sin actividad)
  - Distribución de demanda por área de servicio
  - Proyección simple del mes en curso
  - Ticket promedio y métricas de retención
  - Alertas de negocio inteligentes (stock bajo, pedidos vencidos, etc.)
"""

import os
import datetime
import json
from collections import defaultdict

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")


def _cargar_datos():
    """Carga pedidos, clientes y stock desde los managers."""
    from nexus_orders import manager as om
    from nexus_crm    import manager as cm
    from nexus_stock  import manager as sm

    om.load_orders()
    cm.load_clientes()
    sm.load_stock()

    return om.orders, cm.clientes, sm.stock


# ── Helpers de fecha ──────────────────────────────────────────────────────────

def _hoy():
    return datetime.date.today()

def _inicio_mes(offset_meses: int = 0) -> datetime.date:
    hoy = _hoy()
    mes = hoy.month - offset_meses
    year = hoy.year
    while mes <= 0:
        mes += 12
        year -= 1
    while mes > 12:
        mes -= 12
        year += 1
    return datetime.date(year, mes, 1)

def _fin_mes(offset_meses: int = 0) -> datetime.date:
    inicio = _inicio_mes(offset_meses)
    if inicio.month == 12:
        return datetime.date(inicio.year + 1, 1, 1) - datetime.timedelta(days=1)
    return datetime.date(inicio.year, inicio.month + 1, 1) - datetime.timedelta(days=1)

def _inicio_semana() -> datetime.date:
    hoy = _hoy()
    return hoy - datetime.timedelta(days=hoy.weekday())

def _fecha_orden(o: dict) -> datetime.date:
    raw = o.get("deadline") or o.get("fecha") or o.get("created_at") or ""
    try:
        return datetime.date.fromisoformat(raw[:10])
    except Exception:
        return datetime.date.min

def _es_completado(o: dict) -> bool:
    return o.get("status", "") in ("LISTO", "ENTREGADO")


# ── Cálculo de ingresos ───────────────────────────────────────────────────────

def _ticket_promedio(clientes: list) -> float:
    """Calcula el ticket promedio real desde datos de clientes."""
    total_gastado = sum(c.get("gastado", 0) or 0 for c in clientes)
    total_pedidos = sum(c.get("pedidos", 0) or 0 for c in clientes)
    if total_pedidos == 0:
        return 0.0
    return round(total_gastado / total_pedidos, 2)

def _ingresos_periodo(pedidos: list, desde: datetime.date, hasta: datetime.date, ticket: float) -> float:
    """Suma ingresos de pedidos completados en el rango de fechas."""
    total = 0.0
    for o in pedidos:
        if not _es_completado(o):
            continue
        fecha = _fecha_orden(o)
        if desde <= fecha <= hasta:
            # Si el pedido tiene precio guardado, úsalo; si no, usa ticket promedio
            precio = o.get("precio") or o.get("total") or ticket
            total += float(precio)
    return round(total, 2)

def _pedidos_periodo(pedidos: list, desde: datetime.date, hasta: datetime.date) -> list:
    return [o for o in pedidos if desde <= _fecha_orden(o) <= hasta]


# ── Análisis de clientes ──────────────────────────────────────────────────────

def _clientes_dormidos(clientes: list, pedidos: list, dias: int = 30) -> list:
    """Clientes que no han pedido en X días y tienen al menos 1 pedido previo."""
    hoy = _hoy()
    limite = hoy - datetime.timedelta(days=dias)

    # Último pedido por cliente
    ultimo_pedido = {}
    for o in pedidos:
        cli = (o.get("cliente") or "").strip().lower()
        fecha = _fecha_orden(o)
        if cli and fecha > datetime.date.min:
            if cli not in ultimo_pedido or fecha > ultimo_pedido[cli]:
                ultimo_pedido[cli] = fecha

    dormidos = []
    for c in clientes:
        nombre = (c.get("nombre") or "").strip()
        nombre_key = nombre.lower()
        if not nombre or nombre_key.isdigit():
            continue
        pedidos_count = c.get("pedidos", 0) or 0
        if pedidos_count < 1:
            continue
        ultimo = ultimo_pedido.get(nombre_key)
        if ultimo and ultimo < limite:
            dormidos.append({
                "nombre":      nombre,
                "telefono":    c.get("telefono", ""),
                "gastado":     c.get("gastado", 0),
                "dias_inactivo": (hoy - ultimo).days,
                "ultimo_pedido": str(ultimo)
            })

    dormidos.sort(key=lambda x: x["gastado"], reverse=True)
    return dormidos


def _top_clientes(clientes: list, n: int = 5) -> list:
    validos = [
        {
            "nombre":  (c.get("nombre") or "").strip(),
            "gastado": c.get("gastado", 0) or 0,
            "pedidos": c.get("pedidos", 0) or 0,
            "telefono": c.get("telefono", "")
        }
        for c in clientes
        if (c.get("gastado", 0) or 0) > 0
        and not (c.get("nombre") or "").strip().isdigit()
    ]
    validos.sort(key=lambda x: x["gastado"], reverse=True)
    return validos[:n]


# ── Distribución por servicio ─────────────────────────────────────────────────

def _distribucion_servicios(pedidos: list) -> dict:
    """Cuenta pedidos completados por área de servicio."""
    conteo = defaultdict(int)
    for o in pedidos:
        if _es_completado(o):
            area = (o.get("area") or "GENERAL").upper()
            conteo[area] += 1
    if not conteo:
        return {}
    total = sum(conteo.values())
    return {
        area: {"cantidad": qty, "pct": round(qty * 100 / total, 1)}
        for area, qty in sorted(conteo.items(), key=lambda x: -x[1])
    }


# ── Proyección ────────────────────────────────────────────────────────────────

def _proyeccion_mes(ingresos_mes_actual: float, dias_transcurridos: int) -> float:
    """Proyección lineal simple del mes completo."""
    if dias_transcurridos == 0:
        return 0.0
    hoy = _hoy()
    dias_en_mes = (_fin_mes(0) - _inicio_mes(0)).days + 1
    diario = ingresos_mes_actual / dias_transcurridos
    return round(diario * dias_en_mes, 2)


# ── Alertas inteligentes ──────────────────────────────────────────────────────

def _generar_alertas(pedidos: list, stock: list, clientes_dormidos: list) -> list:
    alertas = []
    hoy = _hoy()

    # Pedidos vencidos (deadline pasó pero siguen PENDIENTE)
    vencidos = [
        o for o in pedidos
        if o.get("status") == "PENDIENTE"
        and _fecha_orden(o) < hoy
        and _fecha_orden(o) > datetime.date.min
    ]
    if vencidos:
        alertas.append({
            "nivel": "CRITICA",
            "mensaje": f"{len(vencidos)} pedido(s) PENDIENTE con deadline vencido",
            "accion": "Revisar tab Pedidos"
        })

    # Stock bajo
    bajo = [s for s in stock if (s.get("cantidad") or 0) <= 3]
    if bajo:
        alertas.append({
            "nivel": "ALTA",
            "mensaje": f"{len(bajo)} item(s) con stock crítico (≤3 unidades)",
            "accion": "Revisar Inventario"
        })

    # Clientes dormidos de alto valor
    dormidos_vip = [c for c in clientes_dormidos if (c.get("gastado") or 0) >= 200]
    if dormidos_vip:
        alertas.append({
            "nivel": "MEDIA",
            "mensaje": f"{len(dormidos_vip)} cliente(s) VIP sin pedir en 30+ días",
            "accion": "Enviar reactivación por WhatsApp"
        })

    # Pedidos para hoy
    hoy_pedidos = [
        o for o in pedidos
        if o.get("status") == "PENDIENTE"
        and _fecha_orden(o) == hoy
    ]
    if hoy_pedidos:
        alertas.append({
            "nivel": "INFO",
            "mensaje": f"{len(hoy_pedidos)} pedido(s) con entrega programada para HOY",
            "accion": "Verificar que estén listos"
        })

    return alertas


# ── API pública principal ─────────────────────────────────────────────────────

def obtener_dashboard() -> dict:
    """
    Genera el dashboard financiero completo.
    Retorna dict con todos los indicadores calculados.
    """
    pedidos, clientes, stock = _cargar_datos()
    hoy   = _hoy()
    ticket = _ticket_promedio(clientes)

    # Períodos
    ini_mes    = _inicio_mes(0)
    fin_mes_   = _fin_mes(0)
    ini_mes_ant = _inicio_mes(1)
    fin_mes_ant = _fin_mes(1)
    ini_semana  = _inicio_semana()
    dias_trans  = (hoy - ini_mes).days + 1

    # Ingresos
    ing_mes     = _ingresos_periodo(pedidos, ini_mes,     fin_mes_,   ticket)
    ing_mes_ant = _ingresos_periodo(pedidos, ini_mes_ant, fin_mes_ant, ticket)
    ing_semana  = _ingresos_periodo(pedidos, ini_semana,  hoy,         ticket)
    ing_hoy     = _ingresos_periodo(pedidos, hoy,         hoy,         ticket)

    # Variación mes
    var_mes = 0.0
    if ing_mes_ant > 0:
        var_mes = round((ing_mes - ing_mes_ant) / ing_mes_ant * 100, 1)

    # Proyección
    proyeccion = _proyeccion_mes(ing_mes, dias_trans)

    # Pedidos
    total_pedidos = len(pedidos)
    pedidos_mes   = len(_pedidos_periodo(pedidos, ini_mes, fin_mes_))
    pendientes    = len([o for o in pedidos if o.get("status") == "PENDIENTE"])
    completados   = len([o for o in pedidos if _es_completado(o)])

    # Clientes
    dormidos = _clientes_dormidos(clientes, pedidos, dias=30)
    top      = _top_clientes(clientes, n=5)

    # Servicios
    distribucion = _distribucion_servicios(pedidos)

    # Alertas
    alertas = _generar_alertas(pedidos, stock, dormidos)

    # Historial de ingresos (últimos 6 meses para gráfico)
    historial = []
    meses_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    for i in range(5, -1, -1):
        ini = _inicio_mes(i)
        fin = _fin_mes(i)
        val = _ingresos_periodo(pedidos, ini, fin, ticket)
        historial.append({
            "mes":    meses_es[ini.month - 1],
            "valor":  val,
            "pedidos": len(_pedidos_periodo(pedidos, ini, fin))
        })

    return {
        "ok": True,
        "generado": hoy.isoformat(),
        "periodo": {
            "mes_actual":    f"{meses_es[hoy.month-1]} {hoy.year}",
            "dias_transcurridos": dias_trans,
            "dias_en_mes":   (_fin_mes(0) - _inicio_mes(0)).days + 1,
        },
        "ingresos": {
            "hoy":        ing_hoy,
            "semana":     ing_semana,
            "mes":        ing_mes,
            "mes_ant":    ing_mes_ant,
            "variacion_pct": var_mes,
            "proyeccion_mes": proyeccion,
        },
        "pedidos": {
            "total":      total_pedidos,
            "este_mes":   pedidos_mes,
            "pendientes": pendientes,
            "completados": completados,
            "ticket_promedio": ticket,
        },
        "clientes": {
            "total":        len(clientes),
            "dormidos":     dormidos[:5],    # top 5 a reactivar
            "top":          top,
        },
        "servicios":  distribucion,
        "historial":  historial,
        "alertas":    alertas,
    }


def resumen_texto() -> str:
    """Genera resumen en texto natural para el agente conversacional."""
    d = obtener_dashboard()
    ing = d["ingresos"]
    ped = d["pedidos"]
    cli = d["clientes"]
    alr = d["alertas"]
    var = ing["variacion_pct"]
    var_txt = f"+{var}%" if var >= 0 else f"{var}%"

    lineas = [
        f"RESUMEN FINANCIERO — {d['periodo']['mes_actual']}",
        f"",
        f"Ingresos del mes: ${ing['mes']:,.2f} ({var_txt} vs mes anterior)",
        f"Proyeccion del mes: ${ing['proyeccion_mes']:,.2f}",
        f"Esta semana: ${ing['semana']:,.2f}",
        f"Hoy: ${ing['hoy']:,.2f}",
        f"",
        f"Pedidos: {ped['este_mes']} este mes | {ped['pendientes']} pendientes | Ticket prom: ${ped['ticket_promedio']:,.2f}",
        f"Clientes: {cli['total']} registrados | {len(cli['dormidos'])} inactivos 30+ dias",
    ]
    if alr:
        lineas.append("")
        lineas.append("ALERTAS:")
        for a in alr:
            lineas.append(f"  [{a['nivel']}] {a['mensaje']}")
    return "\n".join(lineas)

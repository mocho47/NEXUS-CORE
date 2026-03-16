# -*- coding: utf-8 -*-
"""
Motor 12 — Pedidos + Clientes
CRUD real: registrar, consultar, actualizar pedidos y clientes.
"""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')

from cerebro import registrar
from db import _conn, rows_to_list, row_to_dict, now

# ── Clientes ───────────────────────────────────────────────────────────────────

def _buscar_o_crear_cliente(nombre: str, telefono: str = "") -> int:
    with _conn() as c:
        r = c.execute(
            "SELECT id FROM clientes WHERE nombre LIKE ? LIMIT 1",
            (f"%{nombre}%",)
        ).fetchone()
        if r:
            return r["id"]
        cur = c.execute(
            "INSERT INTO clientes (nombre, telefono) VALUES (?,?)",
            (nombre, telefono)
        )
        return cur.lastrowid

def buscar_cliente(nombre: str) -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM clientes WHERE nombre LIKE ? ORDER BY nombre LIMIT 10",
            (f"%{nombre}%",)
        ).fetchall()
    return rows_to_list(rows)

def listar_clientes() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM clientes ORDER BY nombre"
        ).fetchall()
    return rows_to_list(rows)

# ── Pedidos ────────────────────────────────────────────────────────────────────

def nuevo_pedido(cliente: str, descripcion: str, servicio: str = "",
                 precio: float = 0, fecha_entrega: str = "",
                 notas: str = "", telefono: str = "") -> dict:
    cliente_id = _buscar_o_crear_cliente(cliente, telefono)
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO pedidos
               (cliente_id, cliente_nombre, descripcion, servicio, precio,
                fecha_entrega, notas, estado)
               VALUES (?,?,?,?,?,?,?,'pendiente')""",
            (cliente_id, cliente, descripcion, servicio,
             precio, fecha_entrega, notas)
        )
        pid = cur.lastrowid
    return {"ok": True, "id": pid, "cliente": cliente, "descripcion": descripcion}

def ver_pedidos(estado: str = "") -> list:
    with _conn() as c:
        if estado:
            rows = c.execute(
                "SELECT * FROM pedidos WHERE estado=? ORDER BY fecha_entrega, id DESC",
                (estado,)
            ).fetchall()
        else:
            rows = c.execute(
                """SELECT * FROM pedidos
                   WHERE estado NOT IN ('entregado','cancelado')
                   ORDER BY fecha_entrega, id DESC"""
            ).fetchall()
    return rows_to_list(rows)

def actualizar_estado(pedido_id: int, estado: str) -> dict:
    estados_validos = ["pendiente", "en_proceso", "listo", "entregado", "cancelado"]
    if estado not in estados_validos:
        return {"ok": False, "error": f"Estado inválido. Usa: {estados_validos}"}
    with _conn() as c:
        c.execute(
            "UPDATE pedidos SET estado=?, updated_at=? WHERE id=?",
            (estado, now(), pedido_id)
        )
    return {"ok": True, "id": pedido_id, "estado": estado}

def pedidos_atrasados() -> list:
    hoy = now()[:10]
    with _conn() as c:
        rows = c.execute(
            """SELECT * FROM pedidos
               WHERE estado NOT IN ('entregado','cancelado')
               AND fecha_entrega < ?
               AND fecha_entrega != ''
               ORDER BY fecha_entrega""",
            (hoy,)
        ).fetchall()
    return rows_to_list(rows)

# ── Motor registrado ───────────────────────────────────────────────────────────

@registrar("m12_nuevo_pedido")
def motor_nuevo_pedido(texto: str = "", cliente: str = "",
                       descripcion: str = "", **_) -> dict:
    # Extraer cliente del texto si no viene directo
    if not cliente:
        m = re.search(r'(?:para|de)\s+([A-ZÁÉÍÓÚa-záéíóú][a-záéíóúA-ZÁÉÍÓÚ\s]{2,20})',
                      texto, re.IGNORECASE)
        if m:
            cliente = m.group(1).strip()
    if not cliente:
        return {"ok": False, "respuesta": "¿Para qué cliente es el pedido?"}

    if not descripcion:
        # Todo lo que no sea el nombre del cliente
        descripcion = texto

    r = nuevo_pedido(cliente=cliente, descripcion=descripcion)
    return {
        "ok": True,
        "respuesta": f"Pedido #{r['id']} registrado para {cliente}.",
        "datos": r
    }

@registrar("m12_ver_pedidos")
def motor_ver_pedidos(texto: str = "", **_) -> dict:
    txt = texto.lower()
    if "atrasado" in txt or "vencido" in txt or "tarde" in txt:
        pedidos = pedidos_atrasados()
        titulo  = "Pedidos atrasados"
    elif "listo" in txt or "terminado" in txt:
        pedidos = ver_pedidos("listo")
        titulo  = "Pedidos listos para entregar"
    else:
        pedidos = ver_pedidos()
        titulo  = "Pedidos activos"

    if not pedidos:
        return {"ok": True, "respuesta": f"Sin {titulo.lower()}."}

    lineas = [f"{titulo} ({len(pedidos)}):\n"]
    for p in pedidos:
        fecha = f" — entregar {p['fecha_entrega']}" if p.get("fecha_entrega") else ""
        precio = f" ${p['precio']:,.0f}" if p.get("precio") else ""
        lineas.append(f"  #{p['id']} {p['cliente_nombre']}: {p['descripcion'][:40]}{precio}{fecha} [{p['estado']}]")

    return {"ok": True, "respuesta": "\n".join(lineas), "datos": pedidos}

@registrar("m12_actualizar")
def motor_actualizar_pedido(texto: str = "", **_) -> dict:
    txt = texto.lower()
    # Detectar ID del pedido
    m_id = re.search(r'(?:#|pedido\s+)(\d+)', txt)
    if not m_id:
        return {"ok": False, "respuesta": "Indica el número del pedido. Ej: 'pedido 3 listo' o '#5 entregado'"}
    pedido_id = int(m_id.group(1))

    # Detectar nuevo estado
    estado_map = {
        "listo": "listo", "terminado": "listo", "terminé": "listo",
        "entregado": "entregado", "entregué": "entregado", "entregue": "entregado",
        "en proceso": "en_proceso", "en_proceso": "en_proceso", "iniciado": "en_proceso",
        "cancelado": "cancelado", "cancela": "cancelado",
        "pendiente": "pendiente"
    }
    estado = None
    for k, v in estado_map.items():
        if k in txt:
            estado = v
            break

    if not estado:
        return {"ok": False, "respuesta": "¿Cuál es el nuevo estado? (listo, entregado, en_proceso, cancelado)"}

    r = actualizar_estado(pedido_id, estado)
    if not r["ok"]:
        return {"ok": False, "respuesta": r.get("error", "Error al actualizar")}

    # Verificar que existe
    with _conn() as c:
        p = c.execute("SELECT cliente_nombre, descripcion FROM pedidos WHERE id=?", (pedido_id,)).fetchone()
    nombre = p["cliente_nombre"] if p else f"#{pedido_id}"
    desc   = p["descripcion"][:30] if p else ""

    return {
        "ok": True,
        "respuesta": f"Pedido #{pedido_id} ({nombre} — {desc}) marcado como [{estado}].",
        "datos": {"id": pedido_id, "estado": estado}
    }

@registrar("m12_clientes")
def motor_clientes(texto: str = "", **_) -> dict:
    # Buscar cliente específico
    m = re.search(r'(?:busca|cliente|info de|historial de)\s+([A-ZÁÉÍÓÚa-z]{3,})',
                  texto, re.IGNORECASE)
    if m:
        nombre = m.group(1)
        clientes = buscar_cliente(nombre)
        if not clientes:
            return {"ok": True, "respuesta": f"No encontré cliente '{nombre}'."}
        c = clientes[0]
        # Ver pedidos del cliente
        with _conn() as conn:
            pedidos = rows_to_list(conn.execute(
                "SELECT * FROM pedidos WHERE cliente_id=? ORDER BY id DESC LIMIT 5",
                (c["id"],)
            ).fetchall())
        resp = f"Cliente: {c['nombre']}\nTel: {c.get('telefono','—')}\n"
        if pedidos:
            resp += f"Ultimos pedidos:\n"
            for p in pedidos:
                resp += f"  #{p['id']} {p['descripcion'][:40]} [{p['estado']}]\n"
        return {"ok": True, "respuesta": resp, "datos": {"cliente": c, "pedidos": pedidos}}

    # Listar todos
    clientes = listar_clientes()
    if not clientes:
        return {"ok": True, "respuesta": "Sin clientes registrados aún."}
    lineas = [f"Clientes registrados ({len(clientes)}):\n"]
    for c in clientes[:20]:
        tel = f" — {c['telefono']}" if c.get("telefono") else ""
        lineas.append(f"  {c['nombre']}{tel}")
    return {"ok": True, "respuesta": "\n".join(lineas), "datos": clientes}

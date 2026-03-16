# -*- coding: utf-8 -*-
"""
NEXUS v2 — Servidor principal
Delgado. Solo monta rutas y llama al cerebro.
Sin lógica de negocio aquí.
"""
import sys
sys.path.insert(0, 'C:/nexus_v2')

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import sys
sys.path.insert(0, 'C:/nexus_v2')

WEB_DIR = Path("C:/nexus_v2/WEB")

# Importar cerebro
import cerebro

# Registrar todos los motores
import motors.m01_convertir
import motors.m02_cotizar_sub
import motors.m03_preparar_sub
import motors.m04_cotizar_laser
import motors.m05_caja_laser
import motors.m06a_optimizar
import motors.m06b_vectorizar
import motors.m07_cotizar_atf
import motors.m08_agenda_atf
import motors.m09_material_atf
import motors.m10_directorio_canbusfix
import motors.m11_catalogo_canbusfix
import motors.m12_pedidos_clientes
import motors.m14_detectar_oportunidades
import motors.m15_generar_mensaje
import motors.m16_publicar_redes
import motors.m17_pipeline
import motors.m00_briefing
import motors.m_finanzas

app = FastAPI(title="NEXUS v2", version="2.0.0", docs_url=None, redoc_url=None)

# ── Archivos estáticos ────────────────────────────────────────────────────────
out_dir = Path("C:/nexus/MERCH_OUTPUT")
out_dir.mkdir(exist_ok=True)
app.mount("/out", StaticFiles(directory=str(out_dir)), name="out")

# ── API principal — UN solo endpoint de entrada ───────────────────────────────

@app.post("/api/nexus")
async def api_nexus(request: Request) -> JSONResponse:
    """Entrada única al cerebro orquestador."""
    try:
        data  = await request.json()
        texto = data.get("texto", "").strip()
        if not texto:
            return JSONResponse({"ok": False, "respuesta": "Sin instrucción."})
        resultado = cerebro.pensar(texto)
        return JSONResponse(resultado)
    except Exception as e:
        return JSONResponse({"ok": False, "respuesta": f"Error: {e}"})

@app.get("/api/nexus")
async def api_nexus_get(q: str = "") -> JSONResponse:
    """GET cómodo para pruebas rápidas: /api/nexus?q=cotiza+X1"""
    resultado = cerebro.pensar(q)
    return JSONResponse(resultado)

@app.get("/api/motores")
async def api_motores() -> JSONResponse:
    """Lista de motores registrados."""
    return JSONResponse({"motores": cerebro.motores_activos()})

@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "motores": len(cerebro.motores_activos()), "version": "2.0"})

# ── API REST directa — para el panel (sin pasar por cerebro) ─────────────────

@app.get("/api/dashboard")
async def api_dashboard() -> JSONResponse:
    """Todos los datos del panel en una sola llamada."""
    from motors.m00_briefing import briefing
    from motors.m_finanzas   import finanzas
    b = briefing()
    f = finanzas()
    return JSONResponse({
        "ok": True,
        "briefing": b.get("datos", {}),
        "finanzas": f.get("datos", {}),
        "resumen_texto": b.get("respuesta", ""),
    })

@app.get("/api/pedidos")
async def api_pedidos(estado: str = "") -> JSONResponse:
    from motors.m12_pedidos_clientes import ver_pedidos
    return JSONResponse({"ok": True, "pedidos": ver_pedidos(estado)})

@app.put("/api/pedido/{pedido_id}")
async def api_actualizar_pedido(pedido_id: int, request: Request) -> JSONResponse:
    from motors.m12_pedidos_clientes import actualizar_estado
    data   = await request.json()
    estado = data.get("estado", "")
    precio = data.get("precio")
    from db import _conn, now
    with _conn() as c:
        if precio is not None:
            c.execute("UPDATE pedidos SET precio=?, updated_at=? WHERE id=?",
                      (precio, now(), pedido_id))
        if estado:
            c.execute("UPDATE pedidos SET estado=?, updated_at=? WHERE id=?",
                      (estado, now(), pedido_id))
    return JSONResponse({"ok": True, "id": pedido_id, "estado": estado})

@app.get("/api/agenda")
async def api_agenda(dias: int = 7) -> JSONResponse:
    from db import _conn, rows_to_list, now
    from datetime import datetime, timedelta
    hoy = now()[:10]
    fin = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    with _conn() as c:
        rows = rows_to_list(c.execute(
            "SELECT * FROM agenda_atf WHERE fecha BETWEEN ? AND ? AND estado!='cancelado' ORDER BY fecha,hora",
            (hoy, fin)
        ).fetchall())
    return JSONResponse({"ok": True, "agenda": rows})

@app.get("/api/pipeline")
async def api_pipeline() -> JSONResponse:
    from db import _conn, rows_to_list
    with _conn() as c:
        rows = rows_to_list(c.execute(
            "SELECT * FROM pipeline WHERE estado NOT IN ('perdido','entregado') ORDER BY updated_at DESC"
        ).fetchall())
    return JSONResponse({"ok": True, "pipeline": rows})

@app.put("/api/prospecto/{prospecto_id}")
async def api_mover_prospecto(prospecto_id: int, request: Request) -> JSONResponse:
    data   = await request.json()
    estado = data.get("estado", "")
    if not estado:
        return JSONResponse({"ok": False, "error": "estado requerido"}, status_code=400)
    from db import _conn, now
    with _conn() as c:
        c.execute("UPDATE pipeline SET estado=?, updated_at=? WHERE id=?",
                  (estado, now(), prospecto_id))
    return JSONResponse({"ok": True, "id": prospecto_id, "estado": estado})

@app.post("/api/prospecto")
async def api_nuevo_prospecto(request: Request) -> JSONResponse:
    data    = await request.json()
    cliente = data.get("cliente", "")
    servicio= data.get("servicio", "")
    valor   = data.get("valor", 0)
    if not cliente:
        return JSONResponse({"ok": False, "error": "Cliente requerido"}, status_code=400)
    from db import _conn, rows_to_list, now
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO pipeline (cliente, servicio, valor, estado) VALUES (?,?,?,'prospecto')",
            (cliente, servicio, valor)
        )
    return JSONResponse({"ok": True, "id": cur.lastrowid, "cliente": cliente})

@app.post("/api/agenda")
async def api_nueva_cita(request: Request) -> JSONResponse:
    data    = await request.json()
    cliente = data.get("cliente", "").strip()
    if not cliente:
        return JSONResponse({"ok": False, "error": "cliente requerido"}, status_code=400)
    from db import _conn, now
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO agenda_atf (cliente, modelo_kit, carro, fecha, hora, telefono, notas) VALUES (?,?,?,?,?,?,?)",
            (cliente, data.get("modelo_kit",""), data.get("carro",""),
             data.get("fecha", now()[:10]), data.get("hora",""),
             data.get("telefono",""), data.get("notas",""))
        )
    return JSONResponse({"ok": True, "id": cur.lastrowid, "cliente": cliente})

@app.post("/api/instalador")
async def api_nuevo_instalador(request: Request) -> JSONResponse:
    data   = await request.json()
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return JSONResponse({"ok": False, "error": "nombre requerido"}, status_code=400)
    from db import _conn
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO instaladores_canbusfix (nombre, ciudad, telefono, especialidades) VALUES (?,?,?,?)",
            (nombre, data.get("ciudad",""), data.get("telefono",""), data.get("especialidades",""))
        )
    return JSONResponse({"ok": True, "id": cur.lastrowid, "nombre": nombre})

@app.get("/api/instaladores")
async def api_instaladores(ciudad: str = "") -> JSONResponse:
    from db import _conn, rows_to_list
    with _conn() as c:
        if ciudad:
            rows = rows_to_list(c.execute(
                "SELECT * FROM instaladores_canbusfix WHERE ciudad LIKE ? AND activo=1 ORDER BY ciudad",
                (f"%{ciudad}%",)
            ).fetchall())
        else:
            rows = rows_to_list(c.execute(
                "SELECT * FROM instaladores_canbusfix WHERE activo=1 ORDER BY ciudad"
            ).fetchall())
    return JSONResponse({"ok": True, "instaladores": rows})

@app.post("/api/pedido")
async def api_crear_pedido(request: Request) -> JSONResponse:
    data     = await request.json()
    cliente  = data.get("cliente", "").strip()
    desc     = data.get("descripcion", "").strip()
    servicio = data.get("servicio", "")
    fecha    = data.get("fecha_entrega", "")
    precio   = data.get("precio") or 0
    notas    = data.get("notas", "")
    if not cliente or not desc:
        return JSONResponse({"ok": False, "error": "cliente y descripcion requeridos"}, status_code=400)
    from motors.m12_pedidos_clientes import nuevo_pedido
    r = nuevo_pedido(cliente=cliente, descripcion=desc, servicio=servicio,
                     precio=float(precio), fecha_entrega=fecha, notas=notas)
    return JSONResponse(r)

@app.get("/api/clientes")
async def api_clientes(q: str = "") -> JSONResponse:
    from motors.m12_pedidos_clientes import buscar_cliente, listar_clientes
    if q:
        return JSONResponse({"ok": True, "clientes": buscar_cliente(q)})
    return JSONResponse({"ok": True, "clientes": listar_clientes()})

# ── UI — panel completo ────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def panel():
    panel_file = WEB_DIR / "panel.html"
    if panel_file.exists():
        return HTMLResponse(panel_file.read_text(encoding="utf-8"))
    # Fallback mínimo si no existe panel.html
    n = len(cerebro.motores_activos())
    return HTMLResponse(f"<h1>NEXUS v2</h1><p>{n} motores activos. panel.html no encontrado.</p>")

if __name__ == "__main__":
    print(f"NEXUS v2 — {len(cerebro.motores_activos())} motores registrados")
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=False)

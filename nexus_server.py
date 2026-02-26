from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
import json
import platform
import shutil
import tempfile
from nexus_orders import manager as orders_mgr
from nexus_crm import manager as crm_mgr
from nexus_stock import manager as stock_mgr

app = FastAPI(title="Nexus Mobile")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "WEB", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "WEB", "static")
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_precios():
    try:
        path = os.path.join(CONFIG_DIR, "precios_base.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {}

def nexus_status():
    modules = []
    for mod in ["nexus_db", "nexus_voice", "nexus_video", "nexus_stock", "nexus_crm", "nexus_orders"]:
        try:
            __import__(mod)
            modules.append({"nombre": mod, "ok": True})
        except Exception:
            modules.append({"nombre": mod, "ok": False})
    return {
        "status": "ONLINE",
        "modules": modules,
        "version": "2026.02.23",
        "os": platform.platform(),
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    pendientes = orders_mgr.get_pending()
    stock_mgr.load_stock()
    bajo_stock = stock_mgr.list_bajo_stock(minimo=3)
    crm_mgr.load_clientes()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "pedidos": pendientes,
        "total_pendientes": len(pendientes),
        "total_clientes": len(crm_mgr.clientes),
        "total_stock": len(stock_mgr.stock),
        "bajo_stock": bajo_stock,
    })

@app.get("/api/nexus_status", response_class=JSONResponse)
async def api_nexus_status():
    return nexus_status()

@app.get("/api/pedidos", response_class=JSONResponse)
async def api_pedidos():
    return orders_mgr.get_pending()

@app.get("/api/stock", response_class=JSONResponse)
async def api_stock():
    stock_mgr.load_stock()
    return stock_mgr.stock

@app.get("/api/clientes", response_class=JSONResponse)
async def api_clientes():
    crm_mgr.load_clientes()
    return crm_mgr.clientes

@app.get("/cotizar", response_class=HTMLResponse)
async def cotizar_view(request: Request):
    precios = load_precios()
    return templates.TemplateResponse("cotizar_pro.html", {"request": request, "db": precios})

@app.get("/cotizar-rapido", response_class=HTMLResponse)
async def cotizar_simple_view(request: Request):
    precios = load_precios()
    return templates.TemplateResponse("cotizar_simple.html", {"request": request, "db": precios})

@app.post("/nuevo_pedido")
async def crear_pedido(
    cliente: str = Form(...),
    producto: str = Form(...),
    entrega: str = Form(...)
):
    res = orders_mgr.add_order(cliente, producto, entrega)
    return RedirectResponse(url="/", status_code=303)

@app.post("/nuevo_cliente")
async def crear_cliente(
    nombre: str = Form(...),
    telefono: str = Form(...),
    email: str = Form("")
):
    crm_mgr.add_cliente(nombre, telefono, email)
    return RedirectResponse(url="/clientes", status_code=303)

@app.post("/nuevo_item_stock")
async def crear_stock(
    nombre: str = Form(...),
    cantidad: int = Form(...),
    precio: float = Form(...),
    categoria: str = Form("GENERAL")
):
    stock_mgr.add_item(nombre, cantidad, precio, categoria)
    return RedirectResponse(url="/stock", status_code=303)

@app.get("/clientes", response_class=HTMLResponse)
async def clientes_view(request: Request):
    crm_mgr.load_clientes()
    return templates.TemplateResponse("clientes.html", {
        "request": request,
        "clientes": crm_mgr.clientes
    })

@app.get("/stock", response_class=HTMLResponse)
async def stock_view(request: Request):
    stock_mgr.load_stock()
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "stock": stock_mgr.stock,
        "bajo_stock": stock_mgr.list_bajo_stock(minimo=3)
    })

@app.get("/pedidos", response_class=HTMLResponse)
async def pedidos_view(request: Request):
    import datetime
    orders_mgr.load_orders()
    return templates.TemplateResponse("pedidos.html", {
        "request":   request,
        "pedidos":   orders_mgr.orders,
        "pendientes": [o for o in orders_mgr.orders if o.get("status") == "PENDIENTE"],
        "today":     str(datetime.date.today()),
    })

@app.get("/nuevo_pedido_form", response_class=HTMLResponse)
async def nuevo_pedido_form(request: Request):
    return templates.TemplateResponse("nuevo_pedido.html", {"request": request})

@app.get("/nuevo_cliente_form", response_class=HTMLResponse)
async def nuevo_cliente_form(request: Request):
    return templates.TemplateResponse("nuevo_cliente_form.html", {"request": request})

@app.get("/nuevo_stock_form", response_class=HTMLResponse)
async def nuevo_stock_form(request: Request):
    return templates.TemplateResponse("nuevo_stock_form.html", {"request": request})

@app.post("/marcar_listo")
async def marcar_listo(id: int = None, cliente: str = None):
    orders_mgr.load_orders()
    for o in orders_mgr.orders:
        match = (id and o.get("id") == id) or (cliente and cliente.lower() in o.get("cliente","").lower())
        if match and o.get("status") == "PENDIENTE":
            o["status"] = "LISTO"
            import nexus_db
            nexus_db.db.upsert_pedido(o)
            try:
                from nexus_notifier import notifier
                hora = (o.get("deadline") or "")[:16]
                notifier.pedido_listo(o.get("cliente",""), o.get("producto",""), hora)
            except Exception:
                pass
            break
    return RedirectResponse(url="/pedidos", status_code=303)

@app.post("/marcar_entregado")
async def marcar_entregado(id: int = None):
    orders_mgr.load_orders()
    for o in orders_mgr.orders:
        if o.get("id") == id:
            o["status"] = "ENTREGADO"
            import nexus_db
            nexus_db.db.upsert_pedido(o)
            break
    return RedirectResponse(url="/pedidos", status_code=303)

@app.get("/logs")
async def logs_view():
    """Últimas 100 líneas del log actual para el panel."""
    try:
        import datetime
        log_path = os.path.join(BASE_DIR, "logs", f"nexus_log_{datetime.datetime.now().strftime('%Y-%m')}.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return "\n".join(lines[-100:])
    except Exception as e:
        return f"[Log no disponible: {e}]"
    return "[Log vacío]"

@app.get("/api/resumen")
async def api_resumen():
    """Resumen ejecutivo del día para móvil o integración."""
    import datetime
    pendientes = orders_mgr.get_pending()
    hoy = str(datetime.date.today())
    hoy_pedidos = [p for p in pendientes if p.get("deadline","").startswith(hoy)]
    stock_mgr.load_stock()
    crm_mgr.load_clientes()
    return {
        "pedidos_pendientes": len(pendientes),
        "pedidos_hoy": len(hoy_pedidos),
        "detalle_hoy": hoy_pedidos,
        "total_clientes": len(crm_mgr.clientes),
        "items_stock": len(stock_mgr.stock),
        "bajo_stock": stock_mgr.list_bajo_stock(minimo=3),
        "fecha": hoy,
    }

@app.get("/reporte", response_class=HTMLResponse)
async def reporte_view(request: Request):
    return templates.TemplateResponse("reporte.html", {"request": request})

@app.get("/api/system", response_class=JSONResponse)
async def api_system():
    try:
        import psutil
        return {
            "cpu": psutil.cpu_percent(interval=0.2),
            "ram": psutil.virtual_memory().percent,
            "disco": psutil.disk_usage('/').percent,
        }
    except:
        return {"cpu": 0, "ram": 0, "disco": 0}

@app.get("/catalogo", response_class=HTMLResponse)
async def catalogo_view(request: Request):
    import nexus_catalog
    path = nexus_catalog.manager.generate_html_catalog()
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

class CommandRequest(BaseModel):
    command: str = ""

@app.post("/command", response_class=JSONResponse)
async def web_command(payload: CommandRequest):
    """Recibe comandos de texto desde el panel web y los escribe en web_command.txt."""
    cmd = (payload.command or "").strip()
    if not cmd:
        return {"status": "error", "message": "Comando vacío"}
    try:
        cmd_file = os.path.join(BASE_DIR, "web_command.txt")
        with open(cmd_file, "w", encoding="utf-8") as f:
            f.write(cmd)
        return {"status": "sent", "command": cmd}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/editar_pedido_form", response_class=HTMLResponse)
async def editar_pedido_form(request: Request, id: int = None):
    orders_mgr.load_orders()
    pedido = next((o for o in orders_mgr.orders if o.get("id") == id), None)
    if not pedido:
        return RedirectResponse(url="/pedidos")
    return templates.TemplateResponse("editar_pedido.html", {"request": request, "pedido": pedido})

@app.post("/editar_pedido")
async def editar_pedido_post(
    id: int = Form(...),
    cliente: str = Form(...),
    producto: str = Form(...),
    deadline: str = Form(""),
    status: str = Form(...),
    area: str = Form("GENERAL"),
):
    import datetime as dt
    orders_mgr.load_orders()
    for o in orders_mgr.orders:
        if o.get("id") == id:
            o["cliente"] = cliente
            o["producto"] = producto
            o["status"] = status
            o["area"] = area
            if deadline:
                try:
                    o["deadline"] = dt.datetime.strptime(deadline, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    o["deadline"] = deadline
            import nexus_db
            nexus_db.db.upsert_pedido(o)
            break
    return RedirectResponse(url="/pedidos", status_code=303)

@app.post("/eliminar_pedido")
async def eliminar_pedido(id: int = Form(...)):
    import nexus_db
    orders_mgr.load_orders()
    orders_mgr.orders = [o for o in orders_mgr.orders if o.get("id") != id]
    nexus_db.db._save_json_backup("pedidos", orders_mgr.orders)
    try:
        conn = nexus_db.db._get_conn()
        if conn:
            conn.table("pedidos").delete().eq("id", id).execute()
    except Exception:
        pass
    return RedirectResponse(url="/pedidos", status_code=303)

@app.get("/qr", response_class=HTMLResponse)
async def qr_view(request: Request):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    url = f"http://{ip}:8000"
    return templates.TemplateResponse("qr.html", {"request": request, "url": url, "ip": ip})

@app.get("/precios_admin", response_class=HTMLResponse)
async def precios_admin_view(request: Request):
    return templates.TemplateResponse("precios_admin.html", {"request": request})

@app.get("/marketing", response_class=HTMLResponse)
async def marketing_view(request: Request):
    return templates.TemplateResponse("marketing.html", {"request": request})

@app.get("/historial", response_class=HTMLResponse)
async def historial_view(request: Request):
    orders_mgr.load_orders()
    return templates.TemplateResponse("historial.html", {
        "request": request,
        "pedidos": orders_mgr.orders,
    })

@app.get("/agenda", response_class=HTMLResponse)
async def agenda_view(request: Request):
    import datetime as dt
    orders_mgr.load_orders()
    hoy = dt.date.today()
    dias = []
    nombres_dia = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    for i in range(7):
        fecha = hoy + dt.timedelta(days=i)
        fecha_str = str(fecha)
        pedidos_dia = [
            o for o in orders_mgr.orders
            if (o.get("deadline") or "").startswith(fecha_str) and o.get("status") == "PENDIENTE"
        ]
        pedidos_dia.sort(key=lambda x: x.get("deadline", ""))
        dias.append({
            "fecha": fecha.strftime("%d/%m/%Y"),
            "nombre": nombres_dia[fecha.weekday()],
            "es_hoy": (i == 0),
            "pedidos": pedidos_dia,
        })
    return templates.TemplateResponse("agenda.html", {"request": request, "agenda": dias})

@app.get("/api/agenda", response_class=JSONResponse)
async def api_agenda():
    import datetime as dt
    orders_mgr.load_orders()
    hoy = dt.date.today()
    result = []
    for i in range(7):
        fecha = hoy + dt.timedelta(days=i)
        fecha_str = str(fecha)
        pedidos_dia = [
            o for o in orders_mgr.orders
            if (o.get("deadline") or "").startswith(fecha_str) and o.get("status") == "PENDIENTE"
        ]
        result.append({"date": fecha_str, "pedidos": pedidos_dia})
    return result

@app.get("/cotizacion_pdf", response_class=HTMLResponse)
async def cotizacion_pdf_view(request: Request, cliente: str = "", items_json: str = "[]"):
    import datetime as dt, json as _json
    negocio_path = os.path.join(CONFIG_DIR, "negocio.json")
    negocio = {}
    try:
        with open(negocio_path, "r", encoding="utf-8") as f:
            negocio = _json.load(f)
    except Exception:
        pass
    try:
        items = _json.loads(items_json)
    except Exception:
        items = []
    total = sum((i.get("precio_unit", i.get("precio", 0))) * i.get("cantidad", 1) for i in items)
    return templates.TemplateResponse("cotizacion_pdf.html", {
        "request": request,
        "cliente": cliente,
        "items": items,
        "total": total,
        "subtotal": total,
        "negocio": negocio,
        "folio": dt.datetime.now().strftime("%y%m%d%H%M"),
        "fecha": dt.date.today().strftime("%d/%m/%Y"),
    })

@app.get("/perfil_cliente", response_class=HTMLResponse)
async def perfil_cliente_view(request: Request, nombre: str = ""):
    crm_mgr.load_clientes()
    orders_mgr.load_orders()
    cliente = next(
        (c for c in crm_mgr.clientes if c.get("nombre", "").lower() == nombre.lower()), None
    )
    if not cliente:
        return RedirectResponse(url="/clientes")
    pedidos_cliente = [o for o in orders_mgr.orders if nombre.lower() in o.get("cliente", "").lower()]
    pedidos_cliente.sort(key=lambda x: x.get("deadline", ""), reverse=True)
    return templates.TemplateResponse("perfil_cliente.html", {
        "request": request,
        "cliente": cliente,
        "pedidos": pedidos_cliente,
    })

class CampañaRequest(BaseModel):
    nombre: str
    plataforma: str = "instagram"
    tipo: str = "laser"
    objetivo: str = ""

@app.post("/api/crear_campaña", response_class=JSONResponse)
async def api_crear_campaña(req: CampañaRequest):
    try:
        import nexus_marketing
        resultado = nexus_marketing.manager.create_campaign_files(req.nombre, req.tipo)
        return {"ok": True, "folder": str(resultado)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/campaña_form", response_class=HTMLResponse)
async def campaña_form_view(request: Request):
    return templates.TemplateResponse("campaña_form.html", {"request": request})

@app.post("/api/backup", response_class=JSONResponse)
async def api_backup():
    try:
        from nexus_backup import daily_backup
        path = daily_backup()
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/config_negocio", response_class=HTMLResponse)
async def config_negocio_view(request: Request):
    return templates.TemplateResponse("config_negocio.html", {"request": request})

@app.get("/api/config_negocio", response_class=JSONResponse)
async def api_config_negocio_get():
    try:
        path = os.path.join(CONFIG_DIR, "negocio.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

class NegocioConfig(BaseModel):
    nombre: str = ""
    telefono: str = ""
    ciudad: str = ""
    horario: str = ""
    slogan: str = ""
    instagram: str = ""
    tiktok: str = ""
    facebook: str = ""

@app.post("/api/config_negocio", response_class=JSONResponse)
async def api_config_negocio_post(cfg: NegocioConfig):
    try:
        path = os.path.join(CONFIG_DIR, "negocio.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data["nombre"]   = cfg.nombre
        data["telefono"] = cfg.telefono
        data["ciudad"]   = cfg.ciudad
        data["horario"]  = cfg.horario
        data["slogan"]   = cfg.slogan
        data.setdefault("redes", {})
        data["redes"]["instagram"] = cfg.instagram
        data["redes"]["tiktok"]    = cfg.tiktok
        data["redes"]["facebook"]  = cfg.facebook
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class CopyRequest(BaseModel):
    tipo: str = "laser_industrial"
    titulo: str = ""
    auto: str = ""
    modelo_auto: str = ""
    componentes: str = ""
    beneficio_clave: str = ""

@app.post("/api/generar_copy", response_class=JSONResponse)
async def api_generar_copy(req: CopyRequest):
    try:
        from nexus_social import generar_copy
        datos = {k: v for k, v in req.__dict__.items() if v}
        copy_text = generar_copy(req.tipo, datos)
        return {"copy": copy_text}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/precios", response_class=JSONResponse)
async def api_precios():
    return load_precios()

class PrecioUpdate(BaseModel):
    servicio: str
    campo: str
    valor: float

@app.post("/api/precios/update", response_class=JSONResponse)
async def api_precios_update(update: PrecioUpdate):
    try:
        path = os.path.join(CONFIG_DIR, "precios_base.json")
        precios = load_precios()
        svc = precios.get(update.servicio)
        if isinstance(svc, dict) and update.campo in svc:
            svc[update.campo] = update.valor
            with open(path, "w", encoding="utf-8") as f:
                json.dump(precios, f, ensure_ascii=False, indent=2)
            return {"ok": True}
        return {"ok": False, "error": "Servicio o campo no encontrado"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── PÁGINAS EXTRA ─────────────────────────────────────────────────────────────

@app.get("/milens", response_class=HTMLResponse)
async def milens_view(request: Request):
    return templates.TemplateResponse("milens.html", {"request": request})

# ── ESTUDIO (módulo independiente) ───────────────────────────────────────────
@app.get("/estudio", response_class=HTMLResponse)
async def estudio_view(request: Request):
    return templates.TemplateResponse("estudio.html", {"request": request})

@app.post("/api/estudio/procesar", response_class=JSONResponse)
async def api_estudio_procesar(
    archivo: UploadFile = File(...),
    modo: str = Form("vectorizar"),
    opciones: str = Form("{}")
):
    try:
        import json as _json
        data = await archivo.read()
        opts = _json.loads(opciones) if opciones else {}
        ext = (archivo.filename or "").rsplit(".", 1)[-1].lower()

        # Archivos vectoriales → motor especializado
        if modo == "corte_vector" or ext in ("dxf", "svg", "ai", "eps"):
            from nexus_studio_vector import procesar_vector
            return procesar_vector(
                data, ext,
                material_key    = opts.get("material", "mdf_3"),
                ancho_mm        = float(opts.get("ancho_mm", 0)),
                alto_mm         = float(opts.get("alto_mm", 0)),
                grosor_origen_mm= float(opts.get("grosor_orig", 3.0)),
                aplicar_kerf    = bool(opts.get("kerf", True)),
            )
        # Imágenes → motor de imagen
        from nexus_estudio import procesar
        return procesar(data, modo, opts)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/estudio/materiales", response_class=JSONResponse)
async def api_estudio_materiales():
    from nexus_studio_vector import get_materiales
    return get_materiales()

# Servir carpeta out/ para descargas
from fastapi.staticfiles import StaticFiles as _SF
import os as _os
_out_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "out")
_os.makedirs(_out_dir, exist_ok=True)
app.mount("/out", _SF(directory=_out_dir), name="out")

# ── CARTOONIZER (acceso directo legacy) ──────────────────────────────────────
@app.get("/cartoonizer", response_class=HTMLResponse)
async def cartoonizer_view(request: Request):
    return templates.TemplateResponse("cartoonizer.html", {"request": request})

@app.get("/atf", response_class=HTMLResponse)
async def atf_view():
    path = os.path.join(BASE_DIR, "WEB_ATF", "index.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>ATF - Actualiza Tus Faros</title>
    <script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white flex items-center justify-center h-screen">
    <div class="text-center"><h1 class="text-4xl font-bold text-yellow-400 mb-4">💡 Actualiza Tus Faros</h1>
    <p class="text-gray-400">Módulo en construcción — agrega tu contenido en WEB_ATF/index.html</p>
    <a href="/dashboard" class="mt-6 inline-block bg-yellow-500 text-black px-6 py-2 rounded">← Volver</a></div></body></html>""")

@app.get("/canbusfix", response_class=HTMLResponse)
async def canbusfix_view():
    path = os.path.join(BASE_DIR, "WEB_CANBUSFIX", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/demo", response_class=HTMLResponse)
async def demo_view(request: Request):
    return templates.TemplateResponse("demo.html", {"request": request})

@app.get("/licencias", response_class=HTMLResponse)
async def licencias_view(request: Request):
    return templates.TemplateResponse("licencias.html", {"request": request})

@app.post("/api/milens/cotizar", response_class=JSONResponse)
async def api_milens_cotizar(data: dict):
    try:
        from nexus_milens import cotizar_caja
        return cotizar_caja(data.get("largo",10), data.get("ancho",10), data.get("alto",5), data.get("material","MDF 2.7mm"))
    except Exception as e:
        return {"error": str(e)}

# ── VOZ ───────────────────────────────────────────────────────────────────────

class HablarRequest(BaseModel):
    texto: str = ""

@app.post("/api/hablar", response_class=JSONResponse)
async def api_hablar(req: HablarRequest):
    try:
        import threading
        from nexus_voice import hablar
        threading.Thread(target=hablar, args=(req.texto,), daemon=True).start()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── AGENT ─────────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    session_id: str = "default"
    mensaje: str = ""

@app.post("/api/agent/mensaje", response_class=JSONResponse)
async def api_agent_mensaje(req: AgentRequest):
    try:
        from nexus_agent import agente
        resultado = agente.procesar_mensaje(req.session_id, req.mensaje)
        return resultado
    except Exception as e:
        return {"respuesta": f"Error en agente: {e}", "tipo": "error", "progreso": 0}

class AutopilotRequest(BaseModel):
    tipo: str = ""
    activo: bool = False

@app.post("/api/agent/autopilot", response_class=JSONResponse)
async def api_agent_autopilot(req: AutopilotRequest):
    try:
        cfg_path = os.path.join(CONFIG_DIR, "autopilot.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        cfg[req.tipo] = req.activo
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return {"ok": True, "tipo": req.tipo, "activo": req.activo}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── IMAGEN ────────────────────────────────────────────────────────────────────

@app.post("/api/imagen/procesar", response_class=JSONResponse)
async def api_imagen_procesar(
    servicio: str = Form("GENERAL"),
    archivo: UploadFile = File(...)
):
    tmp_path = None
    try:
        suffix = os.path.splitext(archivo.filename or "img.png")[1] or ".png"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        shutil.copyfileobj(archivo.file, tmp)
        tmp.close()
        tmp_path = tmp.name

        from nexus_image_processor import procesar_imagen
        resultado = procesar_imagen(tmp_path, servicio)
        return resultado
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

@app.post("/api/imagen/analizar", response_class=JSONResponse)
async def api_imagen_analizar(archivo: UploadFile = File(...)):
    tmp_path = None
    try:
        suffix = os.path.splitext(archivo.filename or "img.png")[1] or ".png"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        shutil.copyfileobj(archivo.file, tmp)
        tmp.close()
        tmp_path = tmp.name

        from nexus_image_processor import analizar_imagen
        return analizar_imagen(tmp_path)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

# ── SUBLIMINAL ────────────────────────────────────────────────────────────────

@app.get("/api/subliminal/pistas", response_class=JSONResponse)
async def api_subliminal_pistas():
    try:
        from nexus_subliminal import get_pistas
        return {"ok": True, "pistas": get_pistas()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class SubRequest(BaseModel):
    categoria:    str = "deseo"
    cantidad:     int = 10

@app.post("/api/subliminal/generar", response_class=JSONResponse)
async def api_subliminal_generar(req: SubRequest):
    try:
        from nexus_subliminal import generar_pista
        return generar_pista(req.categoria, req.cantidad)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class WavRequest(BaseModel):
    categoria:    str = "deseo"
    duracion_seg: int = 60

@app.post("/api/subliminal/wav", response_class=JSONResponse)
async def api_subliminal_wav(req: WavRequest):
    try:
        from nexus_subliminal import generar_audio_categoria
        return generar_audio_categoria(req.categoria, req.duracion_seg)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class ScriptRequest(BaseModel):
    negocio:    str = ""
    servicio:   str = ""
    categoria:  str = "deseo"
    duracion_s: int = 30

@app.post("/api/subliminal/script", response_class=JSONResponse)
async def api_subliminal_script(req: ScriptRequest):
    try:
        from nexus_subliminal import generar_script_video
        cfg_path = os.path.join(CONFIG_DIR, "negocio.json")
        negocio = req.negocio
        if not negocio:
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    negocio = json.load(f).get("nombre", "Mi Negocio")
            except Exception:
                negocio = "Mi Negocio"
        return generar_script_video(negocio, req.servicio, req.categoria, req.duracion_s)
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── FINANZAS ──────────────────────────────────────────────────────────────────

@app.get("/finanzas", response_class=HTMLResponse)
async def finanzas_view(request: Request):
    return templates.TemplateResponse("finanzas.html", {"request": request})

@app.get("/api/finanzas/dashboard", response_class=JSONResponse)
async def api_finanzas_dashboard():
    try:
        from nexus_finanzas import obtener_dashboard
        return obtener_dashboard()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/finanzas/resumen", response_class=JSONResponse)
async def api_finanzas_resumen():
    try:
        from nexus_finanzas import resumen_texto
        return {"ok": True, "resumen": resumen_texto()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── LICENCIA ──────────────────────────────────────────────────────────────────

@app.get("/api/licencia/info", response_class=JSONResponse)
async def api_licencia_info():
    try:
        from nexus_license import info_licencia
        return info_licencia()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/licencia/huella", response_class=JSONResponse)
async def api_licencia_huella():
    try:
        from nexus_fingerprint import obtener_info_hardware
        return obtener_info_hardware()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── AUTOPILOT STATUS ──────────────────────────────────────────────────────────

@app.get("/api/autopilot/estado", response_class=JSONResponse)
async def api_autopilot_estado():
    try:
        from nexus_autopilot import autopilot
        return autopilot.estado()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/autopilot/ejecutar", response_class=JSONResponse)
async def api_autopilot_ejecutar(tarea: str = "resumen"):
    try:
        from nexus_autopilot import (
            tarea_resumen_diario, tarea_backup,
            tarea_alerta_pedidos, tarea_clientes_inactivos, tarea_sugerencia_post
        )
        mapa = {
            "resumen":    tarea_resumen_diario,
            "backup":     tarea_backup,
            "alertas":    tarea_alerta_pedidos,
            "inactivos":  tarea_clientes_inactivos,
            "post":       tarea_sugerencia_post,
        }
        fn = mapa.get(tarea)
        if not fn:
            return {"ok": False, "error": f"Tarea '{tarea}' no existe"}
        resultado = fn()
        return {"ok": True, "tarea": tarea, "resultado": resultado}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── GALERÍA DE EXPERIENCIAS ───────────────────────────────────────────────────

@app.get("/galeria", response_class=HTMLResponse)
async def galeria_view(request: Request):
    return templates.TemplateResponse("galeria.html", {"request": request})

@app.get("/api/galeria/catalogo", response_class=JSONResponse)
async def api_galeria_catalogo():
    try:
        from nexus_galeria import get_catalogo_completo
        return get_catalogo_completo()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/galeria/uso", response_class=JSONResponse)
async def api_galeria_uso():
    try:
        from nexus_galeria import get_uso_actual
        return get_uso_actual()
    except Exception as e:
        return {"ok": False, "error": str(e)}

class GaleriaActivarReq(BaseModel):
    tipo: str   # "audio" o "visual"
    id:   str

@app.post("/api/galeria/activar", response_class=JSONResponse)
async def api_galeria_activar(req: GaleriaActivarReq):
    try:
        from nexus_galeria import activar_item
        return activar_item(req.tipo, req.id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class GaleriaCreditoReq(BaseModel):
    tipo:     str = "audio"
    cantidad: int = 1
    nota:     str = "Compra extra"

@app.post("/api/galeria/credito", response_class=JSONResponse)
async def api_galeria_credito(req: GaleriaCreditoReq):
    try:
        from nexus_galeria import agregar_creditos
        return agregar_creditos(req.tipo, req.cantidad, req.nota)
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── LEGAL / PRIVACIDAD ────────────────────────────────────────────────────────

@app.get("/legal", response_class=HTMLResponse)
async def legal_view(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

@app.get("/api/legal/acepto", response_class=JSONResponse)
async def api_legal_acepto():
    """Registra que el usuario aceptó el aviso de privacidad y términos."""
    try:
        import datetime
        cfg_path = os.path.join(CONFIG_DIR, "legal_acepto.json")
        data = {
            "aceptado": True,
            "fecha":    datetime.datetime.now().isoformat(),
            "version":  "2026-02-24",
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True, "mensaje": "Aceptación registrada"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/legal/estado", response_class=JSONResponse)
async def api_legal_estado():
    """Verifica si el usuario ya aceptó los términos."""
    try:
        cfg_path = os.path.join(CONFIG_DIR, "legal_acepto.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"aceptado": False}
    except Exception as e:
        return {"aceptado": False, "error": str(e)}

# ── NEXUS TEENS ───────────────────────────────────────────────────────────────

@app.get("/teens", response_class=HTMLResponse)
async def teens_view(request: Request):
    return templates.TemplateResponse("teens.html", {"request": request})

class TeensUserReq(BaseModel):
    user_id: str
    nombre:  str = "Teen"
    edad:    int = 17

@app.post("/api/teens/usuario", response_class=JSONResponse)
async def api_teens_usuario(req: TeensUserReq):
    try:
        from nexus_teens import registrar_usuario
        return registrar_usuario(req.user_id, req.nombre, req.edad)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/perfil/{user_id}", response_class=JSONResponse)
async def api_teens_perfil(user_id: str):
    try:
        from nexus_teens import get_perfil
        return get_perfil(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/misiones/{user_id}", response_class=JSONResponse)
async def api_teens_misiones(user_id: str):
    try:
        from nexus_teens import get_misiones
        return get_misiones(user_id)
    except Exception as e:
        return []

class TeensMisionReq(BaseModel):
    user_id:   str
    mision_id: str

@app.post("/api/teens/completar", response_class=JSONResponse)
async def api_teens_completar(req: TeensMisionReq):
    try:
        from nexus_teens import completar_mision
        return completar_mision(req.user_id, req.mision_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/impulsar/{user_id}/{aptitud}", response_class=JSONResponse)
async def api_teens_impulsar(user_id: str, aptitud: str):
    try:
        from nexus_teens import impulsar_aptitud
        return impulsar_aptitud(user_id, aptitud)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/viral/{aptitud}", response_class=JSONResponse)
async def api_teens_viral(aptitud: str):
    try:
        from nexus_teens import generar_idea_viral
        return generar_idea_viral(aptitud)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/guion", response_class=JSONResponse)
async def api_teens_guion(tema: str = "mi contenido", aptitud: str = "general", duracion: int = 60):
    try:
        from nexus_teens import generar_guion_reel
        return generar_guion_reel(tema, aptitud, duracion)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class TutorReq(BaseModel):
    mensaje:  str
    user_id:  str = "default"

@app.post("/api/teens/tutor", response_class=JSONResponse)
async def api_teens_tutor(req: TutorReq):
    try:
        import os as _os
        from groq import Groq
        client  = Groq(api_key=_os.environ.get("GROQ_API_KEY", ""))
        system  = ("Eres el tutor de NEXUS Teens. Eres cercano, directo y usas lenguaje juvenil "
                   "mexicano. Explicas conceptos de marketing digital, emprendimiento, creatividad "
                   "y tecnología de forma sencilla. Máximo 3 párrafos cortos. Sin emojis excesivos.")
        chat    = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role":"system","content":system},
                        {"role":"user","content":req.mensaje}],
            max_tokens=400,
        )
        return {"ok": True, "respuesta": chat.choices[0].message.content}
    except Exception as e:
        # Fallback sin Groq
        respuestas_fallback = {
            "default": "Interesante pregunta. Para responderla bien: primero investiga en YouTube buscando el tema + '2025', luego practica durante 10 minutos. El aprendizaje real viene de la acción, no solo de leer.",
        }
        return {"ok": True, "respuesta": respuestas_fallback["default"] + f"\n\n(Modo sin conexión IA — activa GROQ_API_KEY para respuestas completas)"}

@app.get("/api/teens/leaderboard", response_class=JSONResponse)
async def api_teens_leaderboard():
    try:
        from nexus_teens import get_leaderboard
        return get_leaderboard()
    except Exception as e:
        return []

class TeensParentalReq(BaseModel):
    user_id: str
    pin:     str
    config:  dict

@app.post("/api/teens/parental", response_class=JSONResponse)
async def api_teens_parental(req: TeensParentalReq):
    try:
        from nexus_teens import control_parental_update
        return control_parental_update(req.user_id, req.pin, req.config)
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── TEENS: BLOQUE FAMILIA ─────────────────────────────────────────────────────

@app.get("/api/teens/familia/{user_id}", response_class=JSONResponse)
async def api_teens_familia(user_id: str):
    try:
        from nexus_teens import get_estado_familia
        return get_estado_familia(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/monitor/{user_id}", response_class=JSONResponse)
async def api_teens_monitor(user_id: str, pin: str = "0000"):
    try:
        from nexus_teens import get_monitor_parental
        return get_monitor_parental(user_id, pin)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class AcuerdoReq(BaseModel):
    user_id:     str
    titulo:      str
    descripcion: str
    meta:        str
    recompensa:  str
    plazo_dias:  int = 7
    pin_padre:   str = "0000"

@app.post("/api/teens/acuerdo/crear", response_class=JSONResponse)
async def api_teens_acuerdo_crear(req: AcuerdoReq):
    try:
        from nexus_teens import crear_acuerdo
        return crear_acuerdo(req.user_id, req.titulo, req.descripcion,
                             req.meta, req.recompensa, req.plazo_dias, req.pin_padre)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/acuerdos/{user_id}", response_class=JSONResponse)
async def api_teens_acuerdos(user_id: str):
    try:
        from nexus_teens import get_acuerdos
        return get_acuerdos(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class ResolverAcuerdoReq(BaseModel):
    user_id:    str
    acuerdo_id: str
    estado:     str   # cumplido | roto
    nota:       str   = ""
    pin_padre:  str   = "0000"

@app.post("/api/teens/acuerdo/resolver", response_class=JSONResponse)
async def api_teens_acuerdo_resolver(req: ResolverAcuerdoReq):
    try:
        from nexus_teens import resolver_acuerdo
        return resolver_acuerdo(req.user_id, req.acuerdo_id, req.estado, req.nota, req.pin_padre)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class CheckinReq(BaseModel):
    user_id: str
    estado:  str
    nota:    str = ""

@app.post("/api/teens/checkin", response_class=JSONResponse)
async def api_teens_checkin(req: CheckinReq):
    try:
        from nexus_teens import registrar_checkin
        return registrar_checkin(req.user_id, req.estado, req.nota)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/checkins/{user_id}", response_class=JSONResponse)
async def api_teens_checkins(user_id: str):
    try:
        from nexus_teens import get_checkins_semana
        return get_checkins_semana(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class ReconocimientoReq(BaseModel):
    user_id:  str
    tipo:     str
    mensaje:  str = ""
    pin_padre:str = "0000"

@app.post("/api/teens/reconocimiento", response_class=JSONResponse)
async def api_teens_reconocimiento(req: ReconocimientoReq):
    try:
        from nexus_teens import dar_reconocimiento
        return dar_reconocimiento(req.user_id, req.tipo, req.mensaje, req.pin_padre)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/privilegios/{user_id}", response_class=JSONResponse)
async def api_teens_privilegios(user_id: str):
    try:
        from nexus_teens import get_privilegios
        return get_privilegios(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class CanjeReq(BaseModel):
    user_id:       str
    privilegio_id: str
    pin_padre:     str = "0000"

@app.post("/api/teens/canje", response_class=JSONResponse)
async def api_teens_canje(req: CanjeReq):
    try:
        from nexus_teens import canjear_privilegio
        return canjear_privilegio(req.user_id, req.privilegio_id, req.pin_padre)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class CodigoHonorReq(BaseModel):
    user_id:   str
    frases:    list
    pin_padre: str = "0000"

@app.post("/api/teens/codigo_honor", response_class=JSONResponse)
async def api_teens_codigo_honor(req: CodigoHonorReq):
    try:
        from nexus_teens import guardar_codigo_honor
        return guardar_codigo_honor(req.user_id, req.frases, req.pin_padre)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/codigo_honor/{user_id}", response_class=JSONResponse)
async def api_teens_get_codigo_honor(user_id: str):
    try:
        from nexus_teens import get_codigo_honor
        return get_codigo_honor(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/valores", response_class=JSONResponse)
async def api_teens_valores():
    try:
        from nexus_teens import get_valores_catalogo
        return get_valores_catalogo()
    except Exception as e:
        return {"ok": False, "error": str(e)}

class RecLeidoReq(BaseModel):
    user_id: str
    rec_id:  str

@app.post("/api/teens/reconocimiento_leido", response_class=JSONResponse)
async def api_teens_rec_leido(req: RecLeidoReq):
    try:
        from nexus_teens import marcar_reconocimiento_leido
        return marcar_reconocimiento_leido(req.user_id, req.rec_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ════════════════════════════════════════════════════════════════════════════════
# ADMIN — Panel de Control Exclusivo
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

class AdminLoginReq(BaseModel):
    pin: str

class AdminTokenReq(BaseModel):
    token: str

class AdminTierSetReq(BaseModel):
    token:   str
    tier:    str
    modulos: list

class AdminPrecioReq(BaseModel):
    token:  str
    item:   str
    precio: float

class AdminNegocioReq(BaseModel):
    token:  str
    nombre: str

class AdminPinReq(BaseModel):
    pin_actual: str
    pin_nuevo:  str

@app.post("/api/admin/login", response_class=JSONResponse)
async def api_admin_login(req: AdminLoginReq):
    try:
        from nexus_admin import login_admin
        return login_admin(req.pin)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/logout", response_class=JSONResponse)
async def api_admin_logout(req: AdminTokenReq):
    try:
        from nexus_admin import logout_admin
        return logout_admin(req.token)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/admin/dashboard", response_class=JSONResponse)
async def api_admin_dashboard(token: str):
    try:
        from nexus_admin import get_admin_dashboard
        return get_admin_dashboard(token)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/admin/catalogo", response_class=JSONResponse)
async def api_admin_catalogo():
    try:
        from nexus_admin import get_catalogo_tienda
        return get_catalogo_tienda()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/admin/tier/{tier}", response_class=JSONResponse)
async def api_admin_get_tier(tier: str, token: str):
    try:
        from nexus_admin import get_modulos_tier, verificar_token
        if not verificar_token(token):
            return {"ok": False, "error": "Token inválido"}
        return {"ok": True, "tier": tier, "modulos": get_modulos_tier(tier)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/tier/set", response_class=JSONResponse)
async def api_admin_set_tier(req: AdminTierSetReq):
    try:
        from nexus_admin import set_config_tier
        return set_config_tier(req.tier, req.modulos, req.token)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/precio/set", response_class=JSONResponse)
async def api_admin_set_precio(req: AdminPrecioReq):
    try:
        from nexus_admin import set_precio
        return set_precio(req.item, req.precio, req.token)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/negocio", response_class=JSONResponse)
async def api_admin_negocio(req: AdminNegocioReq):
    try:
        from nexus_admin import verificar_token, _load_cfg, _save_cfg
        if not verificar_token(req.token):
            return {"ok": False, "error": "Token inválido"}
        cfg = _load_cfg()
        cfg["nombre_negocio"] = req.nombre
        _save_cfg(cfg)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/cambiar_pin", response_class=JSONResponse)
async def api_admin_cambiar_pin(req: AdminPinReq):
    try:
        from nexus_admin import cambiar_pin
        return cambiar_pin(req.pin_actual, req.pin_nuevo)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/admin/setup_check", response_class=JSONResponse)
async def api_admin_setup_check():
    try:
        from nexus_admin import _cfg_inicializado
        return {"ok": True, "configurado": _cfg_inicializado()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/setup", response_class=JSONResponse)
async def api_admin_setup(req: dict):
    try:
        from nexus_admin import setup_admin
        return setup_admin(req.get("pin",""), req.get("nombre_negocio","Mi Negocio"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── TIENDA PÚBLICA (usuarios sin autenticación admin) ─────────────────────────
@app.get("/tienda", response_class=JSONResponse)
async def tienda_catalogo():
    try:
        from nexus_admin import get_catalogo_tienda
        return get_catalogo_tienda()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# AUTOVENTAS — NEXUS se vende a sí mismo
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/autoventas", response_class=HTMLResponse)
async def autoventas_panel(request: Request):
    return templates.TemplateResponse("autoventas.html", {"request": request})

@app.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

class ProspectoReq(BaseModel):
    nombre:       str
    telefono:     str
    tipo_negocio: str = "General"
    canal:        str = "web"
    notas:        str = ""

class StageReq(BaseModel):
    pid:   str
    stage: str
    nota:  str = ""

class SeguimientoReq(BaseModel):
    pid: str
    dia: int

@app.post("/api/autoventas/prospecto", response_class=JSONResponse)
async def av_registrar_prospecto(req: ProspectoReq):
    try:
        from nexus_autoventas import registrar_prospecto
        return registrar_prospecto(req.nombre, req.telefono, req.tipo_negocio,
                                   req.canal, req.notas)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/pipeline", response_class=JSONResponse)
async def av_pipeline():
    try:
        from nexus_autoventas import get_pipeline
        return get_pipeline()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/autoventas/stage", response_class=JSONResponse)
async def av_stage(req: StageReq):
    try:
        from nexus_autoventas import avanzar_stage
        return avanzar_stage(req.pid, req.stage, req.nota)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/seguimiento", response_class=JSONResponse)
async def av_seguimiento():
    try:
        from nexus_autoventas import check_seguimiento_pendiente
        return {"ok": True, "pendientes": check_seguimiento_pendiente()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/autoventas/seguimiento/marcar", response_class=JSONResponse)
async def av_marcar_seguimiento(req: SeguimientoReq):
    try:
        from nexus_autoventas import marcar_seguimiento_enviado
        return marcar_seguimiento_enviado(req.pid, req.dia)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/propuesta/{pid}", response_class=JSONResponse)
async def av_propuesta(pid: str):
    try:
        from nexus_autoventas import generar_propuesta
        return generar_propuesta(pid)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/calendario", response_class=JSONResponse)
async def av_calendario():
    try:
        from nexus_autoventas import get_calendario_semanal
        return {"ok": True, "calendario": get_calendario_semanal()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/hooks/{canal}", response_class=JSONResponse)
async def av_hooks(canal: str):
    try:
        from nexus_autoventas import get_hooks_canal
        return {"ok": True, "canal": canal, "hooks": get_hooks_canal(canal)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/autoventas/metricas", response_class=JSONResponse)
async def av_metricas():
    try:
        from nexus_autoventas import get_metricas
        return get_metricas()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── NEXUS EAR ─────────────────────────────────────────────────────────────────
@app.get("/nexus-ear", response_class=HTMLResponse)
async def nexus_ear(request: Request):
    return templates.TemplateResponse("nexus_ear.html", {"request": request})

class AsistenteReq(BaseModel):
    texto:      str
    session_id: str = "default"

@app.post("/api/asistente", response_class=JSONResponse)
async def api_asistente_chat(req: AsistenteReq):
    try:
        from nexus_assistant import get_respuesta
        r = get_respuesta(req.texto, req.session_id)
        return r if isinstance(r, dict) else {"respuesta": str(r)}
    except Exception as e:
        return {"respuesta": f"Error del asistente: {str(e)}"}

# Captura de leads desde landing page (POST form)
@app.post("/api/autoventas/lead")
async def av_lead_form(
    nombre:       str = Form(...),
    telefono:     str = Form(...),
    tipo_negocio: str = Form("General"),
    canal:        str = Form("landing"),
):
    try:
        from nexus_autoventas import registrar_prospecto
        r = registrar_prospecto(nombre, telefono, tipo_negocio, canal)
        return RedirectResponse(url="/landing?gracias=1", status_code=303)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


# ── PARANORMAL ────────────────────────────────────────────────────────────────
@app.get("/paranormal", response_class=HTMLResponse)
async def paranormal_panel(request: Request):
    return templates.TemplateResponse("paranormal.html", {"request": request})

class ParanormalActivarReq(BaseModel):
    victima: str = None

@app.post("/api/paranormal/activar", response_class=JSONResponse)
async def api_paranormal_activar(req: ParanormalActivarReq):
    try:
        from nexus_paranormal import activar_paranormal
        return activar_paranormal(req.victima)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/paranormal/terror", response_class=JSONResponse)
async def api_paranormal_terror(req: ParanormalActivarReq):
    try:
        from nexus_paranormal import activar_full_terror
        return activar_full_terror(req.victima)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/paranormal/parar", response_class=JSONResponse)
async def api_paranormal_parar():
    try:
        from nexus_paranormal import intentar_parar
        return intentar_parar()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/paranormal/spirit", response_class=JSONResponse)
async def api_paranormal_spirit(req: ParanormalActivarReq):
    try:
        from nexus_paranormal import spirit_box_rapido
        return spirit_box_rapido(req.victima)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/paranormal/estado", response_class=JSONResponse)
async def api_paranormal_estado():
    try:
        from nexus_paranormal import get_estado
        return get_estado()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/paranormal/reset", response_class=JSONResponse)
async def api_paranormal_reset():
    try:
        from nexus_paranormal import forzar_reset
        return forzar_reset()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── PANEL DE COMANDOS ─────────────────────────────────────────────────────────
@app.get("/comandos", response_class=HTMLResponse)
async def panel_comandos(request: Request):
    return templates.TemplateResponse("comandos.html", {"request": request})

# ── SETUP WIZARD (primera vez) ─────────────────────────────────────────────────
@app.get("/setup", response_class=HTMLResponse)
async def setup_wizard(request: Request):
    return templates.TemplateResponse("setup_wizard.html", {"request": request})

class SetupFinalReq(BaseModel):
    nombre_negocio: str
    pin:            str
    tipo_negocio:   str = "general"
    ciudad:         str = ""
    owner_name:     str = ""

@app.post("/api/setup/finalizar", response_class=JSONResponse)
async def api_setup_finalizar(req: SetupFinalReq):
    try:
        from nexus_admin import setup_admin
        r = setup_admin(req.pin, req.nombre_negocio)
        if r.get("ok"):
            # Guardar datos extra en CONFIG/negocio.json
            import json, os
            neg = {
                "nombre":       req.nombre_negocio,
                "tipo":         req.tipo_negocio,
                "ciudad":       req.ciudad,
                "owner":        req.owner_name,
                "setup_date":   __import__('datetime').datetime.now().isoformat(),
                "configured":   True
            }
            cfg = os.path.join(os.path.dirname(__file__), "CONFIG", "negocio.json")
            with open(cfg, "w", encoding="utf-8") as f:
                json.dump(neg, f, ensure_ascii=False, indent=2)
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/setup/check", response_class=JSONResponse)
async def api_setup_check():
    """¿Ya fue configurado NEXUS?"""
    try:
        import json, os
        cfg = os.path.join(os.path.dirname(__file__), "CONFIG", "negocio.json")
        if os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as f:
                d = json.load(f)
            return {"configurado": d.get("configured", False), "negocio": d.get("nombre", "")}
        return {"configurado": False}
    except Exception:
        return {"configurado": False}


# ── ESTUDIO: MOTORS (lanzador de apps) ───────────────────────────────────────
@app.get("/api/estudio/apps", response_class=JSONResponse)
async def api_estudio_apps():
    """Lista de apps instaladas y detectadas."""
    try:
        from nexus_motors import apps_disponibles
        return {"ok": True, "apps": apps_disponibles()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class AbrirAppReq(BaseModel):
    app: str
    archivo: str = ""

@app.get("/api/estudio/macros_corel", response_class=JSONResponse)
async def api_macros_corel_lista():
    """Lista de macros VBA predefinidos para CorelDRAW."""
    try:
        from nexus_motors import macros_disponibles
        return {"ok": True, "macros": macros_disponibles()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/estudio/instalar_macros", response_class=JSONResponse)
async def api_instalar_macros_corel():
    """Instala/actualiza todos los macros NEXUS en el directorio GMS de CorelDRAW."""
    try:
        from nexus_motors import instalar_macros_nexus
        return instalar_macros_nexus()
    except Exception as e:
        return {"ok": False, "error": str(e)}

class EjecutarMacroReq(BaseModel):
    modulo: str
    sub:    str
    args:   list = []

@app.post("/api/estudio/ejecutar_macro", response_class=JSONResponse)
async def api_ejecutar_macro_corel(req: EjecutarMacroReq):
    """Ejecuta un macro en CorelDRAW (CorelDRAW debe estar abierto)."""
    try:
        from nexus_motors import ejecutar_macro_corel_com
        return ejecutar_macro_corel_com(req.modulo, req.sub, *req.args)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class EscribirMacroReq(BaseModel):
    nombre: str
    codigo: str

@app.post("/api/estudio/escribir_macro", response_class=JSONResponse)
async def api_escribir_macro_corel(req: EscribirMacroReq):
    """Escribe un macro VBA personalizado en el directorio GMS de CorelDRAW."""
    try:
        from nexus_motors import escribir_macro_corel
        return escribir_macro_corel(req.nombre, req.codigo)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/estudio/abrir", response_class=JSONResponse)
async def api_estudio_abrir(req: AbrirAppReq):
    """Abre una app externa, opcionalmente con un archivo."""
    try:
        from nexus_motors import abrir_en_app, abrir_carpeta_out
        if req.app == "carpeta":
            return abrir_carpeta_out()
        archivo = req.archivo if req.archivo else None
        return abrir_en_app(req.app, archivo)
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── ESTUDIO: GENERADOR DE CAJAS ───────────────────────────────────────────────
@app.get("/api/estudio/tipos_caja", response_class=JSONResponse)
async def api_estudio_tipos_caja():
    """Lista de tipos de caja disponibles."""
    try:
        from nexus_boxes_gen import tipos_caja
        return {"ok": True, "tipos": tipos_caja()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class GenerarCajaReq(BaseModel):
    tipo:        str   = "ClosedBox"
    ancho:       float = 200
    alto:        float = 150
    prof:        float = 80
    material:    str   = "mdf_3"
    grosor:      float = 0   # 0 = usar el del material

@app.post("/api/estudio/generar_caja", response_class=JSONResponse)
async def api_estudio_generar_caja(req: GenerarCajaReq):
    """Genera una caja parametrica con boxes.py."""
    try:
        from nexus_boxes_gen import generar_caja
        grosor = req.grosor if req.grosor > 0 else None
        return generar_caja(req.tipo, req.ancho, req.alto, req.prof, req.material, grosor)
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── HEALTH / AUTO-DIAGNÓSTICO ────────────────────────────────────────────────
@app.get("/api/health/check", response_class=JSONResponse)
async def api_health_check():
    """Check rápido: servidor, disco, alertas. Sin llamadas externas."""
    try:
        from nexus_health import check_disco, check_archivos, check_apps, check_env
        disco  = check_disco()
        archivos = check_archivos()
        apps   = check_apps()
        env    = check_env()
        alertas = []
        if disco["alerta"]:
            alertas.append(f"Disco bajo: {disco['libre_gb']}GB libres")
        faltantes = [f for f, ok in archivos.items() if not ok]
        if faltantes:
            alertas.append(f"Archivos faltantes: {len(faltantes)}")
        deps_env = [k for k, v in env.items() if not v and k in ("GROQ_API_KEY","SUPABASE_URL")]
        if deps_env:
            alertas.append(f"Env vars faltantes: {', '.join(deps_env)}")
        return {
            "ok": True,
            "estado": "OK" if not alertas else "ALERTA",
            "alertas": alertas,
            "disco": disco,
            "apps": {k: v["ok"] for k, v in apps.items()},
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/health/reporte", response_class=JSONResponse)
async def api_health_reporte():
    """Reporte completo con todas las verificaciones (tarda ~5s)."""
    try:
        from nexus_health import reporte_completo
        return reporte_completo()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/health/diagnostico", response_class=JSONResponse)
async def api_health_diagnostico():
    """Reporte completo + diagnóstico asistido por LLM."""
    try:
        from nexus_health import reporte_completo, diagnostico_llm
        r = reporte_completo()
        r["diagnostico_llm"] = diagnostico_llm(r)
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/health/reparar", response_class=JSONResponse)
async def api_health_reparar():
    """Intenta instalar dependencias faltantes automáticamente."""
    try:
        from nexus_health import check_dependencias, instalar_faltantes
        deps = check_dependencias()
        faltantes = [
            pkg["nombre"]
            for grupo in deps.values()
            for pkg in grupo if not pkg["ok"]
        ]
        if not faltantes:
            return {"ok": True, "mensaje": "No hay dependencias faltantes", "instalados": []}
        resultados = instalar_faltantes(faltantes)
        return {"ok": True, "instalados": resultados}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    from nexus_autopilot import autopilot as _ap
    _ap.iniciar()
    uvicorn.run(app, host="0.0.0.0", port=8000)

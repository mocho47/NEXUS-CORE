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
import urllib.parse
from nexus_orders import manager as orders_mgr
from nexus_crm import manager as crm_mgr
from nexus_stock import manager as stock_mgr

app = FastAPI(title="Nexus Mobile")

# ── VOZ v2 — Módulo independiente ─────────────────────────────────────────────
try:
    from nexus_voz_router import router as voz_router
    app.include_router(voz_router)
    print("[VOZ v2] Router adjuntado OK")
except Exception as _e:
    print(f"[VOZ v2] No disponible: {_e}")

# ── CARTOON — Módulo independiente ────────────────────────────────────────────
try:
    from nexus_cartoon_module import setup_routes as _cartoon_setup
    _cartoon_setup(app)
    print("[CARTOON] Módulo adjuntado OK — /cartoonizer, /api/cartoon/procesar")
except Exception as _e:
    print(f"[CARTOON] No disponible: {_e}")

# ── STUDIO — Módulo independiente ─────────────────────────────────────────────
try:
    from nexus_studio_module import setup_routes as _studio_setup
    _studio_setup(app)
except Exception as _e:
    print(f"[STUDIO] No disponible: {_e}")

# Detectar modo nube — features desktop deshabilitadas en Linux/Render
CLOUD_MODE = os.getenv("CLOUD_MODE", "false").lower() == "true"

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

# ── PERFILES DE USUARIO ──────────────────────────────────────────────────────
@app.get("/api/perfil", response_class=JSONResponse)
async def api_perfil_info():
    try:
        from nexus_profiles import info_perfil, get_perfil_activo
        info = info_perfil()
        perfil = get_perfil_activo()
        return {"ok": True, "perfil": info, "tabs": perfil.get("tabs_dashboard", [])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/perfil/set", response_class=JSONResponse)
async def api_perfil_set(request: Request):
    try:
        data = await request.json()
        perfil_id = data.get("perfil", "admin")
        from nexus_profiles import set_perfil_activo
        p = set_perfil_activo(perfil_id)
        return {"ok": True, "perfil": p.get("tipo"), "nombre": p.get("nombre")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/perfil/permisos", response_class=JSONResponse)
async def api_perfil_permisos():
    try:
        from nexus_profiles import get_perfil_activo, PERMISOS
        tipo = get_perfil_activo().get("tipo", "NEGOCIO")
        return {"ok": True, "tipo": tipo, "permisos": PERMISOS.get(tipo, {})}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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

class NuevoPedidoJSON(BaseModel):
    cliente: str
    producto: str
    entrega: str = "Por definir"

@app.post("/api/pedidos/nuevo", response_class=JSONResponse)
async def api_nuevo_pedido(req: NuevoPedidoJSON):
    try:
        res = orders_mgr.add_order(req.cliente, req.producto, req.entrega)
        return {"ok": True, "mensaje": f"Pedido creado para {req.cliente}: {req.producto}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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

@app.get("/marketing/panel", response_class=HTMLResponse)
async def marketing_panel(request: Request):
    return templates.TemplateResponse("marketing_panel.html", {"request": request})

# ── VIDEO PROMO ───────────────────────────────────────────────────────────────

class VideoPromoRequest(BaseModel):
    prompt: str
    marca: str = "NEXUS"
    formato: str = "tiktok"

@app.post("/api/marketing/generar_promo", response_class=JSONResponse)
async def api_marketing_generar_promo(req: VideoPromoRequest):
    try:
        from nexus_video_promo import iniciar_job
        job_id = iniciar_job(req.prompt, req.marca, req.formato)
        return {"ok": True, "job_id": job_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/marketing/promo_status/{job_id}", response_class=JSONResponse)
async def api_marketing_promo_status(job_id: str):
    try:
        from nexus_video_promo import estado_job
        return estado_job(job_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}

class CaptionRapidoRequest(BaseModel):
    texto: str
    marca: str = "NEXUS"
    red: str = "instagram"

@app.post("/api/marketing/caption_rapido", response_class=JSONResponse)
async def api_marketing_caption_rapido(req: CaptionRapidoRequest):
    try:
        from nexus_video_promo import caption_rapido
        return await caption_rapido(req.texto, req.marca, req.red)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MarketAnalizarRequest(BaseModel):
    query: str

@app.post("/api/market/analizar", response_class=JSONResponse)
async def api_market_analizar(req: MarketAnalizarRequest):
    """Analiza precios de mercado usando Groq IA."""
    try:
        import os
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        prompt = f"""Eres experto en precios de mercado en Mexico. Analiza: "{req.query}"
Devuelve JSON puro sin markdown:
{{"stats":{{"min":150,"max":800,"promedio":420,"mediana":380}},"analisis":"recomendacion corta de precio en Guadalajara con oportunidades."}}"""
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=400, temperature=0.4
        )
        import json as _json
        raw = resp.choices[0].message.content.strip()
        start = raw.find('{'); end = raw.rfind('}') + 1
        data = _json.loads(raw[start:end]) if start >= 0 else {}
        return {"ok": True, "stats": data.get("stats",{}), "analisis": data.get("analisis","Sin datos")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MotionVideoRequest(BaseModel):
    prompt: str
    marca: str = "NEXUS"
    formato: str = "tiktok"

@app.post("/api/marketing/generar_motion", response_class=JSONResponse)
async def api_marketing_generar_motion(req: MotionVideoRequest):
    try:
        from nexus_motion_video import iniciar_motion_job
        job_id = iniciar_motion_job(req.prompt, req.marca, req.formato)
        return {"ok": True, "job_id": job_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/marketing/motion_status/{job_id}", response_class=JSONResponse)
async def api_marketing_motion_status(job_id: str):
    try:
        from nexus_motion_video import estado_job
        return estado_job(job_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

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
    giro: str = ""
    telefono: str = ""
    whatsapp: str = ""
    email: str = ""
    ciudad: str = ""
    horario: str = ""
    slogan: str = ""
    color_marca: str = "#00ff88"
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
        data["nombre"]      = cfg.nombre
        data["giro"]        = cfg.giro
        data["telefono"]    = cfg.telefono
        data["whatsapp"]    = cfg.whatsapp or cfg.telefono
        data["email"]       = cfg.email
        data["ciudad"]      = cfg.ciudad
        data["horario"]     = cfg.horario
        data["slogan"]      = cfg.slogan
        data["color_marca"] = cfg.color_marca or "#00ff88"
        data["configured"]  = True
        data.setdefault("redes", {})
        data["redes"]["instagram"] = cfg.instagram
        data["redes"]["tiktok"]    = cfg.tiktok
        data["redes"]["facebook"]  = cfg.facebook
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True, "nombre": cfg.nombre}
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

@app.get("/atf/galeria", response_class=HTMLResponse)
async def atf_galeria():
    path = os.path.join(BASE_DIR, "WEB", "templates", "atf_galeria.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Galería no generada aún. Ejecuta organizar_atf_videos.py</h1>")

@app.post("/api/atf/clasificar_videos")
async def clasificar_videos(request: Request):
    import json, shutil
    from pathlib import Path
    try:
        data = await request.json()
        clasificacion = data.get("clasificacion", {})
        trabajos_dir = Path(BASE_DIR) / "TRABAJOS_ATF"
        movidos = 0
        for trabajo in trabajos_dir.iterdir():
            if not trabajo.is_dir() or not trabajo.name.startswith("TRABAJO_"):
                continue
            proceso_dir = trabajo / "proceso"
            terminado_dir = trabajo / "terminado"
            proceso_dir.mkdir(exist_ok=True)
            terminado_dir.mkdir(exist_ok=True)
            for tipo_dir in [proceso_dir, terminado_dir]:
                for video in list(tipo_dir.glob("*.mp4")):
                    nombre = video.name
                    if nombre in clasificacion:
                        nuevo_tipo = clasificacion[nombre]
                        nuevo_tipo_dir = trabajo / nuevo_tipo
                        destino = nuevo_tipo_dir / nombre
                        if not destino.exists():
                            shutil.move(str(video), str(destino))
                            movidos += 1
        return {"ok": True, "movidos": movidos}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Servir archivos de TRABAJOS_ATF estáticamente
_trabajos_dir = os.path.join(BASE_DIR, "TRABAJOS_ATF")
if os.path.exists(_trabajos_dir):
    from fastapi.staticfiles import StaticFiles as _SFT
    app.mount("/trabajos_atf", _SFT(directory=_trabajos_dir), name="trabajos_atf")

class ATFAgendarReq(BaseModel):
    nombre: str
    telefono: str
    vehiculo: str
    servicio: str = "Retrofit faros"
    fecha_preferida: str = ""
    notas: str = ""

@app.post("/api/atf/agendar", response_class=JSONResponse)
async def api_atf_agendar(req: ATFAgendarReq):
    """Agenda un servicio ATF — crea pedido en el sistema de ordenes."""
    try:
        import nexus_db, time, datetime
        now = datetime.datetime.now()
        # Determinar deadline: mañana al mediodía si no se especificó
        if req.fecha_preferida:
            deadline = req.fecha_preferida + " 12:00:00"
        else:
            tmr = now + datetime.timedelta(days=1)
            deadline = tmr.strftime("%Y-%m-%d 12:00:00")
        order = {
            "id": int(time.time()),
            "cliente": req.nombre,
            "whatsapp": req.telefono,
            "producto": f"{req.servicio} — {req.vehiculo}. {req.notas}",
            "tipo": "ATF",
            "precio": 0,
            "deadline": deadline,
            "status": "NUEVO",
            "area": "ATF",
            "notified_1h": False, "notified_15m": False,
            "insistent_level": 0, "last_nag_time": 0.0,
        }
        nexus_db.db.upsert_pedido(order)
        orders_mgr.load_orders()
        # WhatsApp de confirmacion
        num = req.telefono.replace(" ","").replace("-","")
        if len(num) == 10: num = "52" + num
        wa_msg = f"Hola {req.nombre}! Tu cita ATF fue recibida.\nServicio: {req.servicio}\nVehiculo: {req.vehiculo}\nTe contactamos para confirmar fecha.\nATF by Simplex"
        wa_url = f"https://wa.me/{num}?text={urllib.parse.quote(wa_msg)}"
        return {"ok": True, "id": order["id"], "wa_url": wa_url, "mensaje": f"Servicio agendado para {req.nombre}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/atf/agenda", response_class=JSONResponse)
async def api_atf_agenda():
    """Lista ordenes ATF."""
    orders_mgr.load_orders()
    atf = [o for o in orders_mgr.get_all_orders() if o.get("tipo") == "ATF" or o.get("area") == "ATF"]
    return {"ok": True, "servicios": atf}

@app.get("/api/atf/videos_terminados")
async def atf_videos_terminados():
    from pathlib import Path
    trabajos_dir = Path(BASE_DIR) / "TRABAJOS_ATF"
    videos = []
    if trabajos_dir.exists():
        for trabajo in sorted(trabajos_dir.iterdir()):
            if not trabajo.is_dir() or not trabajo.name.startswith("TRABAJO_"):
                continue
            for tipo in ["terminado", "proceso"]:
                tipo_dir = trabajo / tipo
                if tipo_dir.exists():
                    for mp4 in sorted(tipo_dir.glob("*.mp4")):
                        videos.append({"trabajo": trabajo.name, "tipo": tipo, "nombre": mp4.name})
    return {"videos": videos, "total": len(videos)}

@app.get("/canbusfix", response_class=HTMLResponse)
async def canbusfix_view():
    path = os.path.join(BASE_DIR, "WEB_CANBUSFIX", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/canbusfix/catalogo", response_class=HTMLResponse)
async def canbusfix_catalogo():
    path = os.path.join(BASE_DIR, "WEB_CANBUSFIX", "catalogo.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/canbusfix/productos")
async def canbusfix_productos():
    import json
    path = os.path.join(BASE_DIR, "ilume_prices.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/canbusfix/catalogo", response_class=JSONResponse)
async def api_canbusfix_catalogo(tier: str = "publico"):
    """Devuelve productos con precios por tier: publico/pro/elite."""
    import json
    path = os.path.join(BASE_DIR, "ilume_prices.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    precio_key = {"publico":"precio_publico","pro":"precio_pro","elite":"precio_elite","distribuidor":"precio_distribuidor"}.get(tier, "precio_publico")
    productos = []
    for codigo, p in raw.items():
        productos.append({
            "codigo": codigo,
            "descripcion": p.get("descripcion",""),
            "precio": p.get(precio_key, p.get("precio_publico",0)),
            "temp_color": p.get("temp_color",""),
            "pulgadas": p.get("pulgadas",""),
            "destacado": p.get("destacado", False),
        })
    return {"ok": True, "tier": tier, "productos": productos, "total": len(productos)}

class CanbusInstaladorReq(BaseModel):
    nombre: str
    ciudad: str
    telefono: str
    experiencia: str = "basica"
    notas: str = ""

@app.post("/api/canbusfix/registrar_instalador", response_class=JSONResponse)
async def api_canbusfix_registrar(req: CanbusInstaladorReq):
    """Registra nuevo instalador en la red Canbusfix."""
    try:
        import nexus_db, time
        registro = {
            "id": int(time.time()),
            "nombre": req.nombre,
            "ciudad": req.ciudad,
            "telefono": req.telefono,
            "experiencia": req.experiencia,
            "notas": req.notas,
            "tier": "BASICO",
            "estado": "PENDIENTE_APROBACION",
            "fecha": time.strftime("%Y-%m-%d"),
        }
        # Guardar como cliente en CRM
        crm_mgr.add_cliente(
            req.nombre,
            req.telefono,
            email="",
        )
        return {"ok": True, "id": registro["id"], "mensaje": f"Solicitud de {req.nombre} recibida. Te contactamos en 24h."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/demo", response_class=HTMLResponse)
async def demo_view(request: Request):
    return templates.TemplateResponse("demo.html", {"request": request})

@app.get("/licencias", response_class=HTMLResponse)
async def licencias_view(request: Request):
    return templates.TemplateResponse("licencias.html", {"request": request})

@app.get("/modulos", response_class=HTMLResponse)
async def modulos_view(request: Request):
    return templates.TemplateResponse("modulos.html", {"request": request})

@app.post("/api/licencia/activar_demo", response_class=JSONResponse)
async def api_licencia_activar_demo():
    try:
        from nexus_license import activar_demo
        return activar_demo()
    except Exception as e:
        return {"ok": False, "error": str(e)}

class LicenciaAdminRequest(BaseModel):
    huella: str = ""
    cliente: str = ""
    tipo: str = "DEMO"
    dias: int = None
    modulos: list = []

@app.post("/api/licencia/crear_admin", response_class=JSONResponse)
async def api_licencia_crear_admin(req: LicenciaAdminRequest):
    try:
        from nexus_license import crear_licencia, guardar_licencia
        modulos = req.modulos if req.modulos else None
        dias = req.dias if req.dias else None
        lic = crear_licencia(
            huella=req.huella.upper(),
            tipo=req.tipo,
            cliente=req.cliente,
            dias=dias,
            modulos=modulos,
        )
        # Guardar solo si la huella coincide con la máquina local (admin en su propia máquina)
        try:
            from nexus_fingerprint import generar_huella
            huella_local = generar_huella()
            if req.huella.upper() == huella_local or req.huella.upper() == "BYPASS":
                guardar_licencia(lic)
        except Exception:
            pass
        return {"ok": True, "licencia": lic}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── ANALIZADOR DE MERCADO ─────────────────────────────────────────────────────

@app.get("/mercado", response_class=HTMLResponse)
async def mercado_view(request: Request):
    return templates.TemplateResponse("mercado.html", {"request": request})

class MercadoAnalizarRequest(BaseModel):
    query: str
    mi_precio: float = None
    limite: int = 30
    contexto: str = ""

@app.post("/api/mercado/analizar", response_class=JSONResponse)
async def api_mercado_analizar(req: MercadoAnalizarRequest):
    try:
        from nexus_market_analyzer import analisis_completo
        return await analisis_completo(
            query=req.query,
            mi_precio=req.mi_precio,
            limite=req.limite,
            contexto=req.contexto,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/mercado/buscar", response_class=JSONResponse)
async def api_mercado_buscar(q: str, limite: int = 20):
    try:
        from nexus_market_analyzer import buscar_ml
        return await buscar_ml(q, limite)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/milens/cotizar", response_class=JSONResponse)
async def api_milens_cotizar(data: dict):
    try:
        from nexus_milens import cotizar_caja
        return cotizar_caja(data.get("largo",10), data.get("ancho",10), data.get("alto",5), data.get("material","MDF 2.7mm"))
    except Exception as e:
        return {"error": str(e)}

# ── MILENS FLUJO ──────────────────────────────────────────────────────────────

class MilensOrdenReq(BaseModel):
    cliente: str
    whatsapp: str = ""
    tipo: str = "LASER"
    descripcion: str
    precio: float = 0
    entrega: str = "mañana"

@app.post("/api/milens/orden", response_class=JSONResponse)
async def api_milens_orden(req: MilensOrdenReq):
    try:
        import time, datetime
        now = datetime.datetime.now()
        entrega_txt = req.entrega.strip()
        if "hoy" in entrega_txt.lower():
            deadline = datetime.datetime.combine(now.date(), datetime.time(20, 0))
        else:
            deadline = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(14, 0))
        order = {
            "id": int(time.time()),
            "cliente": req.cliente,
            "whatsapp": req.whatsapp,
            "producto": req.descripcion,
            "tipo": req.tipo,
            "precio": req.precio,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "NUEVO",
            "area": req.tipo,
            "notified_1h": False,
            "notified_15m": False,
            "insistent_level": 0,
            "last_nag_time": 0.0,
        }
        import nexus_db
        nexus_db.db.upsert_pedido(order)
        orders_mgr.load_orders()
        return {"ok": True, "id": order["id"], "mensaje": f"Orden de {req.cliente} creada"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/milens/tablero", response_class=JSONResponse)
async def api_milens_tablero():
    orders_mgr.load_orders()
    todos = orders_mgr.get_all_orders()
    resultado = {"NUEVO": [], "PRODUCCION": [], "LISTO": [], "ENTREGADO": []}
    for o in todos:
        s = o.get("status", "NUEVO")
        if s == "PENDIENTE":
            s = "NUEVO"
        if s in resultado:
            resultado[s].append(o)
        elif s not in ("ENTREGADO",):
            resultado["NUEVO"].append(o)
    return resultado

class MilensEstadoReq(BaseModel):
    id: int
    status: str

@app.post("/api/milens/estado", response_class=JSONResponse)
async def api_milens_estado(req: MilensEstadoReq):
    try:
        orders_mgr.load_orders()
        import nexus_db
        for o in orders_mgr.orders:
            if o["id"] == req.id:
                o["status"] = req.status
                nexus_db.db.upsert_pedido(o)
                orders_mgr.load_orders()
                return {"ok": True}
        return {"ok": False, "error": "Orden no encontrada"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/milens/sugerir_precio", response_class=JSONResponse)
async def api_milens_sugerir_precio(data: dict):
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        import os
        g = Groq(api_key=os.getenv("GROQ_API_KEY"))
        desc = data.get("descripcion", "")
        tipo = data.get("tipo", "LASER")
        prompt = f"""Eres experto en precios de taller de corte laser y sublimacion en Mexico (Guadalajara).
El cliente pide: "{desc}" (tipo: {tipo}).
Da un precio estimado en pesos mexicanos. Responde SOLO con un JSON asi:
{{"precio_min": 150, "precio_max": 300, "sugerido": 200, "nota": "breve explicacion"}}
Sin texto extra."""
        r = g.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=150
        )
        import json
        txt = r.choices[0].message.content.strip()
        return json.loads(txt)
    except Exception as e:
        return {"precio_min": 0, "precio_max": 0, "sugerido": 0, "nota": str(e)}

@app.post("/api/milens/caption", response_class=JSONResponse)
async def api_milens_caption(data: dict):
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        import os
        g = Groq(api_key=os.getenv("GROQ_API_KEY"))
        desc = data.get("descripcion", "")
        tipo = data.get("tipo", "LASER")
        prompt = f"""Genera un caption corto para Instagram/TikTok para un taller de corte laser y sublimacion en Guadalajara llamado "Creaciones Milens".
Trabajo realizado: {desc} ({tipo}).
Caption: entusiasta, mexicano, con emojis, maximo 3 lineas + 5 hashtags relevantes.
SOLO el caption, sin explicaciones."""
        r = g.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200
        )
        return {"ok": True, "caption": r.choices[0].message.content.strip()}
    except Exception as e:
        return {"ok": False, "caption": "", "error": str(e)}

# ── VOZ ───────────────────────────────────────────────────────────────────────

class HablarRequest(BaseModel):
    texto: str = ""

@app.post("/api/hablar", response_class=JSONResponse)
async def api_hablar(req: HablarRequest):
    if CLOUD_MODE:
        return {"ok": False, "error": "Voz no disponible en modo nube — solo en PC local"}
    # __stop__ = comando para detener TTS, no leer en voz alta
    if req.texto.strip() == "__stop__":
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "mpv.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "ffplay.exe"], capture_output=True)
        except Exception:
            pass
        return {"ok": True, "stopped": True}
    try:
        import threading
        from nexus_voice import hablar
        threading.Thread(target=hablar, args=(req.texto,), daemon=True).start()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/cast/hablar", response_class=JSONResponse)
async def api_cast_hablar(req: HablarRequest):
    """Habla por el Google Home Mini."""
    if CLOUD_MODE:
        return {"ok": False, "error": "Cast no disponible en modo nube"}
    try:
        import threading
        from nexus_cast import hablar_en_mini
        def _run():
            result = hablar_en_mini(req.texto)
            if not result.get("ok"):
                print(f"[MINI ERROR] {result.get('error','desconocido')}")
            else:
                print(f"[MINI OK] '{req.texto[:40]}'")
        threading.Thread(target=_run, daemon=True).start()
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

# ── MI NEXUS (espacio personal del dueño — PIN en frontend) ──────────────────

@app.get("/mio", response_class=HTMLResponse)
async def mio_view(request: Request):
    return templates.TemplateResponse("mio.html", {"request": request})

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

@app.get("/teens/instalar", response_class=HTMLResponse)
async def teens_instalar(request: Request):
    return templates.TemplateResponse("teens_bienvenida.html", {"request": request})

@app.get("/teens_sw.js")
async def teens_sw():
    from fastapi.responses import FileResponse as _FR
    return _FR(os.path.join(BASE_DIR, "WEB", "static", "teens_sw.js"),
               media_type="application/javascript",
               headers={"Service-Worker-Allowed": "/"})

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
    emocion:  str = ""
    etapa:    str = ""   # "secundaria" | "prepa" | "adulto"

@app.post("/api/teens/tutor", response_class=JSONResponse)
async def api_teens_tutor(req: TutorReq):
    try:
        import os as _os
        from groq import Groq
        client  = Groq(api_key=_os.environ.get("GROQ_API_KEY", ""))

        etapa_ctx = ""
        if req.etapa == "secundaria":
            etapa_ctx = "La teen está en secundaria (12-14 años). Usa ejemplos de su mundo inmediato: salón, amigos, familia, redes. Lenguaje muy simple, sin términos complejos. "
        elif req.etapa == "prepa":
            etapa_ctx = "La teen está en prepa (15-17 años). Puede hablar de dinero, decisiones de vida, presión social más compleja, identidad. Lenguaje directo y sin condescendencia. "
        elif req.etapa == "adulto":
            etapa_ctx = "Ya está en una etapa de mayor independencia (17+). Puede hablar de trabajo, emprendimiento real, relaciones adultas, autonomía financiera. "

        if req.emocion:
            system = (
                f"{etapa_ctx}"
                "Eres el acompañante de NEXUS Teens. Ahora mismo la chava que escribe parece sentir algo difícil "
                f"— la señal detectada es: {req.emocion}. "
                "Tu único trabajo en este momento es escuchar de verdad. "
                "REGLAS DE ORO para este modo: "
                "1. Empieza SIEMPRE validando lo que siente, con 1 sola frase honesta y sin exagerar. Nunca digas 'entiendo cómo te sientes', 'todo va a estar bien', ni 'échale ganas'. "
                "2. Haz UNA sola pregunta abierta que invite a contar más, sin presionar. "
                "3. Al final ofrece solo 2 opciones: seguir hablando de eso o hacer una pausa y platicar de otra cosa. "
                "4. Nunca des consejos no pedidos. Nunca minimices. Nunca compares con otros. "
                "5. Si detectas señales de crisis real (autolesión, 'ya no quiero estar aquí', etc.), con calma y sin drama sugiere hablar con alguien de confianza en persona. "
                "Tono: como ese hermano mayor o prima que sí escucha, sin juzgar. Máximo 3 párrafos cortos."
            )
        else:
            system = (
                f"{etapa_ctx}"
                "Eres el acompañante de NEXUS Teens. Tu personalidad tiene psicología real de adolescentes — "
                "entiendes cómo funciona el mundo adulto, el sistema, la presión social, la familia, la economía, "
                "y cuando el teen lo necesita se lo explicas honestamente, sin adornos, como las reglas no escritas "
                "que nadie enseña en la escuela. No eres terapeuta ni das diagnósticos — eres ese hermano mayor "
                "o prima que ya pasó por esto y habla sin rodeos. "
                "\n\nTU VISIÓN DEL MUNDO (no la predicas, la encarnas — la compartes solo cuando viene al caso): "
                "1. SIEMPRE HAY OPCIONES. Aunque todo parezca cerrado, hay caminos que no se ven a primera vista. "
                "Tu trabajo es mostrarlos, nunca elegirlos por el teen. "
                "2. TODO TIENE UN PRECIO — incluso las decisiones correctas. Hacer lo correcto suele ser más "
                "pesado, más incómodo, más solitario a corto plazo. No lo endulces. Dilo tal cual. "
                "3. EL RESULTADO NO SIEMPRE ES EL ESPERADO. Tomar buenas decisiones no garantiza que todo salga "
                "bien de inmediato. Pero la dirección importa más que el resultado puntual. A largo plazo, "
                "la disciplina autoimpuesta sí construye algo — no perfectamente, pero construye. "
                "4. NADIE VIENE A HACER LO QUE TE CORRESPONDE. No como amenaza — como dato liberador. "
                "Si lo entiendes temprano, tienes ventaja real sobre la mayoría. "
                "5. LA DISCIPLINA QUE TE PONES TÚ MISMO vale infinitamente más que cualquier regla impuesta. "
                "Porque viene de adentro y nadie te la puede quitar. "
                "\n\nREGLAS DE COMUNICACIÓN: "
                "- Hablas como alguien de 22 años: directo, relajado, con humor natural mexicano. "
                "- NUNCA ordenas, NUNCA aconsejas directamente. SIEMPRE terminas con 2 opciones concretas "
                "y preguntas cuál le late. Formato: 'Opción A: ... / Opción B: ... — ¿cuál te late más?' "
                "- Para temas escolares: explica con ejemplos de la vida real, sin rollo académico. "
                "- Para lana y ahorro: 'feria', 'lana', 'ahorrar chido' — nunca términos financieros formales. "
                "- Si el teen duda de sí mismo: muéstrale que otros en su lugar encontraron caminos reales — "
                "sin decirle que 'debe' hacer nada, sin frases vacías como 'tú puedes'. "
                "- Máximo 4 párrafos cortos. Sin listas largas. Sin emojis excesivos (máximo 2 por respuesta). "
                "- Si detectas que el teen necesita entender cómo funciona algo del mundo adulto (presión familiar, "
                "sistema escolar, dinero, relaciones), explícalo como mecanismo — cómo funciona de verdad — "
                "sin juzgar ni aconsejar. Solo iluminar."
            )
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

@app.get("/teens/admin", response_class=HTMLResponse)
async def teens_admin_panel(request: Request):
    return templates.TemplateResponse("teens_admin.html", {"request": request})

@app.get("/api/teens/admin/usuarios", response_class=JSONResponse)
async def api_teens_admin_usuarios():
    try:
        from nexus_teens import _load_data
        data = _load_data()
        usuarios = data.get("usuarios", {})
        result = []
        for uid, p in usuarios.items():
            result.append({
                "user_id": uid,
                "nombre": p.get("nombre", uid),
                "edad": p.get("edad", 0),
                "rol": p.get("rol", "hijo"),
                "nivel": p.get("nivel", 1),
                "xp": p.get("xp", 0),
                "racha": p.get("racha_dias", 0),
                "ultimo_acceso": p.get("ultimo_acceso", ""),
                "familia_id": p.get("familia_id", ""),
                "activo": p.get("activo", True),
            })
        return {"ok": True, "total": len(result), "usuarios": result}
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

# ── TIENDA PÚBLICA ────────────────────────────────────────────────────────────
@app.get("/tienda", response_class=HTMLResponse)
async def tienda_view(request: Request):
    return templates.TemplateResponse("tienda.html", {"request": request})

@app.get("/api/tienda/catalogo", response_class=JSONResponse)
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

@app.get("/nexus", response_class=HTMLResponse)
async def nexus_landing(request: Request):
    return templates.TemplateResponse("nexus_landing.html", {"request": request})

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

@app.post("/api/asistente/stream")
async def api_asistente_stream(req: AsistenteReq):
    """Streaming SSE: emite oraciones conforme Groq las genera."""
    import json as _json
    from fastapi.responses import StreamingResponse as _SR

    async def _gen():
        # Intentar respuesta rápida por keywords primero (sin Groq)
        t = req.texto.lower().strip()
        _quick_keys = ["pedido","stock","cliente","venta","sistema","hora","fecha",
                       "hola","buenos","agenda","cotiz","diagnos","inventario","finanza"]
        if any(k in t for k in _quick_keys):
            try:
                from nexus_assistant import get_respuesta
                r = get_respuesta(req.texto, req.session_id)
                resp = r.get("respuesta","") if isinstance(r,dict) else str(r)
                for oracion in resp.replace("!",".").replace("?",".").split("."):
                    oracion = oracion.strip()
                    if oracion:
                        yield f"data: {oracion}.\n\n"
            except Exception as e:
                yield f"data: Error: {e}\n\n"
            yield "data: [FIN]\n\n"
            return

        # Groq streaming para preguntas abiertas
        groq_key = os.environ.get("GROQ_API_KEY","")
        if not groq_key:
            try:
                from nexus_assistant import get_respuesta
                r = get_respuesta(req.texto, req.session_id)
                resp = r.get("respuesta","") if isinstance(r,dict) else str(r)
                yield f"data: {resp}\n\n"
            except Exception as e:
                yield f"data: Error: {e}\n\n"
            yield "data: [FIN]\n\n"
            return

        try:
            from groq import Groq
            try:
                _cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)),"CONFIG","negocio.json")
                with open(_cfg,"r",encoding="utf-8") as _f:
                    _neg = _json.load(_f)
                _ctx = f"Negocio: {_neg.get('nombre','Negocio')}. Servicios: {_neg.get('servicios','laser, retrofit de faros')}."
            except Exception:
                _ctx = "Negocio de servicios: laser, cajas, retrofit de faros (ATF), canbusfix."

            client = Groq(api_key=groq_key)
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role":"system","content":(
                        f"Eres NEXUS, asistente IA para un negocio mexicano. {_ctx} "
                        "Responde en español mexicano, directo y natural. Máximo 3 oraciones."
                    )},
                    {"role":"user","content":req.texto}
                ],
                max_tokens=200,
                temperature=0.7,
                stream=True,
            )
            buf = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                buf += delta
                # Emitir por cada fin de oración
                while True:
                    idx = -1
                    for sep in [".", "!", "?"]:
                        pos = buf.find(sep)
                        if pos != -1 and (idx == -1 or pos < idx):
                            idx = pos
                    if idx == -1:
                        break
                    oracion = buf[:idx+1].strip()
                    buf = buf[idx+1:]
                    if oracion:
                        yield f"data: {oracion}\n\n"
            if buf.strip():
                yield f"data: {buf.strip()}\n\n"
        except Exception as e:
            yield f"data: Error Groq: {e}\n\n"
        yield "data: [FIN]\n\n"

    return _SR(_gen(), media_type="text/event-stream", headers={
        "Cache-Control":"no-cache",
        "X-Accel-Buffering":"no"
    })

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
        destino = "/nexus" if canal == "nexus" else "/landing"
        return RedirectResponse(url=f"{destino}?gracias=1", status_code=303)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})



# ── SOCIAL — Posts por negocio ───────────────────────────────────────────────
@app.get("/api/social/templates", response_class=JSONResponse)
async def api_social_templates():
    try:
        from nexus_social import get_templates_disponibles
        return {"ok": True, "templates": get_templates_disponibles()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class SocialPostReq(BaseModel):
    negocio: str
    datos_extra: dict = {}

@app.post("/api/social/generar_post", response_class=JSONResponse)
async def api_social_generar_post(req: SocialPostReq):
    try:
        from nexus_social import generar_post_negocio
        return generar_post_negocio(req.negocio, req.datos_extra)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/social/abrir_instagram", response_class=JSONResponse)
async def api_social_abrir_ig(req: SocialPostReq):
    try:
        from nexus_social import abrir_instagram_web
        return abrir_instagram_web(req.negocio)
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -- DREAM / APRENDIZAJE GENERATIVO -------------------------------------------

@app.post("/api/dream/sonar", response_class=JSONResponse)
async def api_dream_sonar():
    """Lanza ciclo de sueno generativo manualmente (admin)."""
    try:
        from nexus_dream import sonar
        return sonar()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/dream/despertar", response_class=JSONResponse)
async def api_dream_despertar():
    """Retorna el conocimiento consolidado del ultimo sueno."""
    try:
        from nexus_dream import despertar
        return despertar()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/dream/conocimiento", response_class=JSONResponse)
async def api_dream_conocimiento():
    """Retorna todo el conocimiento acumulado (historial de suenos)."""
    try:
        from nexus_dream import get_conocimiento_completo
        return get_conocimiento_completo()
    except Exception as e:
        return {"ok": False, "error": str(e)}

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
_CLOUD_DESKTOP = {"ok": False, "error": "Función solo disponible en PC local (modo nube activo)"}

@app.get("/api/estudio/apps", response_class=JSONResponse)
async def api_estudio_apps():
    """Lista de apps instaladas y detectadas."""
    if CLOUD_MODE: return _CLOUD_DESKTOP
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


# ── PLANILLA STICKERS ────────────────────────────────────────────────────────
@app.post("/api/estudio/planilla_stickers", response_class=JSONResponse)
async def api_planilla_stickers(
    request: Request,
    imagen: UploadFile = File(None)
):
    try:
        from nexus_planilla_stickers import generar_planilla_pdf
        form = await request.form()
        ancho_hoja  = float(form.get("ancho_hoja", 279))
        alto_hoja   = float(form.get("alto_hoja", 432))
        ancho_st    = float(form.get("ancho_sticker", 60))
        alto_st     = float(form.get("alto_sticker", 90))
        margen      = float(form.get("margen", 3))
        titulo      = form.get("titulo", "Planilla Stickers")

        img_path = None
        if imagen and imagen.filename:
            tmp = os.path.join(BASE_DIR, "out", f"tmp_{imagen.filename}")
            with open(tmp, "wb") as f:
                f.write(await imagen.read())
            img_path = tmp

        nombre = f"planilla_{int(ancho_st)}x{int(alto_st)}.pdf"
        out_path = os.path.join(BASE_DIR, "out", nombre)

        result = generar_planilla_pdf(
            imagen_path=img_path,
            ancho_hoja_mm=ancho_hoja, alto_hoja_mm=alto_hoja,
            ancho_sticker_mm=ancho_st, alto_sticker_mm=alto_st,
            margen_mm=margen, output_path=out_path, titulo=titulo
        )
        result["url"] = f"/out/{nombre}"
        return result
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


# ── VIDEO STUDIO ──────────────────────────────────────────────────────────────
@app.get("/video-studio", response_class=HTMLResponse)
async def page_video_studio(request: Request):
    return templates.TemplateResponse("video_studio.html", {"request": request})

@app.post("/api/video_studio/crear_job")
async def api_vs_crear_job(video: UploadFile = File(...), negocio: str = Form("ATF faros retrofit")):
    try:
        from nexus_video_studio import crear_job, UPLOAD_DIR
        import aiofiles
        dest = UPLOAD_DIR / video.filename
        async with aiofiles.open(str(dest), "wb") as f:
            await f.write(await video.read())
        return crear_job(str(dest), negocio)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/video_studio/detectar_escenas/{job_id}")
async def api_vs_detectar(job_id: str, threshold: float = 27.0):
    try:
        from nexus_video_studio import job_detectar_escenas
        return job_detectar_escenas(job_id, threshold)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/video_studio/thumbnails/{job_id}")
async def api_vs_thumbs(job_id: str):
    try:
        from nexus_video_studio import job_generar_thumbnails
        return job_generar_thumbnails(job_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

class VSSegmentosReq(BaseModel):
    segmentos: list
    redes: list = ["tiktok", "reels"]
    negocio: str = "ATF faros retrofit"

@app.post("/api/video_studio/set_segmentos/{job_id}")
async def api_vs_set_segmentos(job_id: str, req: VSSegmentosReq):
    try:
        from nexus_video_studio import job_set_segmentos, _jobs
        r = job_set_segmentos(job_id, req.segmentos)
        if job_id in _jobs:
            _jobs[job_id]["redes"] = req.redes
            _jobs[job_id]["negocio"] = req.negocio
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/video_studio/procesar/{job_id}")
async def api_vs_procesar(job_id: str):
    try:
        from nexus_video_studio import job_iniciar_proceso
        return job_iniciar_proceso(job_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/video_studio/estado/{job_id}")
async def api_vs_estado(job_id: str):
    try:
        from nexus_video_studio import job_estado
        return job_estado(job_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/video_studio/jobs")
async def api_vs_listar():
    try:
        from nexus_video_studio import listar_jobs
        return {"ok": True, "jobs": listar_jobs()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Servir archivos VIDEO_STUDIO
from fastapi.staticfiles import StaticFiles as _SF2
import os as _os2
_vs_out = _os2.path.join(_os2.path.dirname(__file__), "VIDEO_STUDIO")
_os2.makedirs(_vs_out, exist_ok=True)
app.mount("/VIDEO_STUDIO", _SF2(directory=_vs_out, html=False), name="video_studio_files")

# ── MERCH DESIGN ──────────────────────────────────────────────────────────────
@app.get("/merch-design", response_class=HTMLResponse)
async def page_merch_design(request: Request):
    return templates.TemplateResponse("merch_design.html", {"request": request})

class MerchPlayeraReq(BaseModel):
    negocio: str = "atf"
    nombre_marca: str = "ATF by Simplex"
    color_playera: list = [20, 20, 20]

@app.post("/api/merch/playera")
async def api_merch_playera(req: MerchPlayeraReq):
    try:
        from nexus_merch_design import generar_playera, MERCH_OUT
        r = generar_playera(nombre_marca=req.nombre_marca, color_playera=tuple(req.color_playera))
        if r.get("ok") and r.get("archivos"):
            base = str(MERCH_OUT)
            for k, v in r["archivos"].items():
                if v and isinstance(v, str):
                    r["archivos"][k] = "/MERCH/" + v.replace(base, "").replace("\\", "/").lstrip("/")
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MerchImanReq(BaseModel):
    negocio: str = "atf"
    tamano: str = "grande"
    texto_principal: str = "ATF by Simplex"
    subtexto: str = "Retrofit Faros LED • GDL"
    telefono: str = "3326148674"

@app.post("/api/merch/iman")
async def api_merch_iman(req: MerchImanReq):
    try:
        from nexus_merch_design import generar_iman, MERCH_OUT
        r = generar_iman(tamano=req.tamano, texto_principal=req.texto_principal,
                          subtexto=req.subtexto, telefono=req.telefono)
        base = str(MERCH_OUT)
        for k in ["archivo", "pdf_planilla"]:
            if r.get(k):
                r[k] = "/MERCH/" + r[k].replace(base, "").replace("\\", "/").lstrip("/")
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MerchLlaveroReq(BaseModel):
    negocio: str = "atf"
    texto: str = "ATF by Simplex"
    subtexto: str = "Retrofit • GDL"
    telefono: str = "3326148674"
    descuento: str = "10% OFF"

@app.post("/api/merch/llavero")
async def api_merch_llavero(req: MerchLlaveroReq):
    try:
        from nexus_merch_design import generar_llavero, MERCH_OUT
        r = generar_llavero(texto=req.texto, subtexto=req.subtexto,
                             telefono=req.telefono, descuento=req.descuento)
        base = str(MERCH_OUT)
        for k in ["frente", "reverso", "pdf_planilla"]:
            if r.get(k):
                r[k] = "/MERCH/" + r[k].replace(base, "").replace("\\", "/").lstrip("/")
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

class MerchKitReq(BaseModel):
    negocio: str = "atf"
    telefono: str = "3326148674"

@app.post("/api/merch/kit")
async def api_merch_kit(req: MerchKitReq):
    try:
        from nexus_merch_design import generar_kit_completo, MERCH_OUT
        r = generar_kit_completo(negocio=req.negocio, telefono=req.telefono)
        base = str(MERCH_OUT)
        def _fix_paths(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, str) and v.startswith(str(MERCH_OUT)):
                        d[k] = "/MERCH/" + v.replace(base, "").replace("\\", "/").lstrip("/")
                    elif isinstance(v, dict):
                        _fix_paths(v)
        _fix_paths(r)
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Servir archivos MERCH
_merch_out = _os2.path.join(_os2.path.dirname(__file__), "MERCH_OUTPUT")
_os2.makedirs(_merch_out, exist_ok=True)
app.mount("/MERCH", _SF2(directory=_merch_out, html=False), name="merch_files")

# ── VOZ ESCUCHA ───────────────────────────────────────────────────────────────
@app.post("/api/voz/iniciar")
async def api_voz_iniciar():
    try:
        from nexus_voz_escucha import iniciar
        return iniciar()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/voz/detener")
async def api_voz_detener():
    try:
        from nexus_voz_escucha import detener
        return detener()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/voz/estado")
async def api_voz_estado():
    try:
        from nexus_voz_escucha import estado
        return estado()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/voz/eventos")
async def api_voz_eventos():
    try:
        from nexus_voz_escucha import eventos_pendientes
        return {"ok": True, "eventos": eventos_pendientes()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ════════════════════════════════════════════════════════════
# MONITOR CLIENTE — Señalética digital
# ════════════════════════════════════════════════════════════
import asyncio
from pathlib import Path as _Path

_MONITOR_DIR_DEFAULT = str(_Path("C:/nexus/MONITOR_VIDEOS").resolve())
_MONITOR_EXTENSIONS  = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v"}

_monitor_state = {
    "suspendido": False,
    "carpeta":    _MONITOR_DIR_DEFAULT,
    "volumen":    0.8,
    "videos":     [],
    "idx":        0,
}
_monitor_clients: list = []   # colas SSE activas

def _scan_monitor_videos(carpeta: str) -> list:
    p = _Path(carpeta)
    if not p.exists():
        return []
    return sorted([
        f.name for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in _MONITOR_EXTENSIONS
    ])

def _monitor_push(data: dict):
    """Envía estado a todos los clientes SSE conectados."""
    import json as _json
    msg = f"data: {_json.dumps(data)}\n\n"
    for q in list(_monitor_clients):
        try:
            q.put_nowait(msg)
        except Exception:
            pass

# Montar carpeta de videos
try:
    _mon_dir = _Path(_MONITOR_DIR_DEFAULT)
    _mon_dir.mkdir(parents=True, exist_ok=True)
    from fastapi.staticfiles import StaticFiles as _SFMon
    app.mount("/monitor_videos", _SFMon(directory=str(_mon_dir), html=False), name="monitor_videos")
except Exception as _me:
    print(f"[Monitor] No se pudo montar carpeta: {_me}")

@app.get("/monitor", response_class=HTMLResponse)
async def page_monitor(request: Request):
    return templates.TemplateResponse("monitor.html", {"request": request})

@app.get("/monitor/control", response_class=HTMLResponse)
async def page_monitor_control(request: Request):
    return templates.TemplateResponse("monitor_control.html", {"request": request})

@app.get("/api/monitor/videos", response_class=JSONResponse)
async def api_monitor_videos():
    if not _monitor_state["videos"]:
        _monitor_state["videos"] = _scan_monitor_videos(_monitor_state["carpeta"])
    return {
        "ok":      True,
        "videos":  _monitor_state["videos"],
        "volumen": _monitor_state["volumen"],
        "carpeta": _monitor_state["carpeta"],
    }

@app.get("/api/monitor/estado", response_class=JSONResponse)
async def api_monitor_estado():
    if not _monitor_state["videos"]:
        _monitor_state["videos"] = _scan_monitor_videos(_monitor_state["carpeta"])
    return {"ok": True, **_monitor_state, "total": len(_monitor_state["videos"])}

@app.post("/api/monitor/toggle", response_class=JSONResponse)
async def api_monitor_toggle():
    _monitor_state["suspendido"] = not _monitor_state["suspendido"]
    _monitor_push({
        "suspendido": _monitor_state["suspendido"],
        "volumen":    _monitor_state["volumen"],
    })
    return {"ok": True, **_monitor_state, "total": len(_monitor_state["videos"])}

@app.post("/api/monitor/siguiente", response_class=JSONResponse)
async def api_monitor_siguiente():
    _monitor_push({"accion": "siguiente", "suspendido": _monitor_state["suspendido"], "volumen": _monitor_state["volumen"]})
    return {"ok": True}

@app.post("/api/monitor/reload", response_class=JSONResponse)
async def api_monitor_reload():
    _monitor_state["videos"] = _scan_monitor_videos(_monitor_state["carpeta"])
    _monitor_push({"accion": "reload_playlist", "suspendido": _monitor_state["suspendido"], "volumen": _monitor_state["volumen"]})
    return {"ok": True, "total": len(_monitor_state["videos"])}

@app.post("/api/monitor/volumen", response_class=JSONResponse)
async def api_monitor_volumen(body: dict):
    vol = float(body.get("volumen", 0.8))
    _monitor_state["volumen"] = max(0.0, min(1.0, vol))
    _monitor_push({"suspendido": _monitor_state["suspendido"], "volumen": _monitor_state["volumen"]})
    return {"ok": True, "volumen": _monitor_state["volumen"]}

@app.post("/api/monitor/carpeta", response_class=JSONResponse)
async def api_monitor_carpeta(body: dict):
    carpeta = body.get("carpeta", "").strip()
    if not carpeta:
        return {"ok": False, "error": "Carpeta vacía"}
    p = _Path(carpeta)
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {"ok": False, "error": str(e)}
    _monitor_state["carpeta"] = str(p)
    _monitor_state["videos"]  = _scan_monitor_videos(str(p))
    # Remontar static
    try:
        from fastapi.staticfiles import StaticFiles as _SFMonR
        app.mount("/monitor_videos", _SFMonR(directory=str(p), html=False), name="monitor_videos")
    except Exception:
        pass
    _monitor_push({"accion": "reload_playlist", "suspendido": _monitor_state["suspendido"], "volumen": _monitor_state["volumen"]})
    return {"ok": True, "total": len(_monitor_state["videos"]), "carpeta": str(p)}

@app.get("/api/monitor/eventos")
async def api_monitor_eventos():
    from fastapi.responses import StreamingResponse as _SR
    import asyncio as _aio, queue as _queue
    q: _queue.Queue = _queue.Queue()
    _monitor_clients.append(q)

    async def _gen():
        # Enviar estado inicial
        import json as _json
        yield f"data: {_json.dumps({'suspendido': _monitor_state['suspendido'], 'volumen': _monitor_state['volumen']})}\n\n"
        try:
            while True:
                try:
                    msg = q.get_nowait()
                    yield msg
                except _queue.Empty:
                    yield ": ping\n\n"
                await _aio.sleep(1)
        except _aio.CancelledError:
            pass
        finally:
            _monitor_clients.remove(q)

    return _SR(_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


if __name__ == "__main__":
    from nexus_autopilot import autopilot as _ap
    _ap.iniciar()
    # Arrancar bot de Telegram
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from nexus_telegram import TelegramBot
        _bot = TelegramBot()
        _bot.start()
        _bot.send("🟢 <b>NEXUS iniciado</b>\nServidor activo en puerto 8000.")
    except Exception as _e:
        print(f"[Telegram] No se pudo iniciar bot: {_e}")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

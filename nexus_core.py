# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════╗
║                NEXUS v3 — Orquestador Principal                ║
║                      by Simplex                               ║
║  Cerebro del sistema: coordina motores, IA, memoria y web.    ║
║  Puerto 8000.                                                  ║
╚════════════════════════════════════════════════════════════════╝
"""

import uuid, logging, asyncio, json, os, sys, time, tempfile
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from lib.config import settings
from lib import database, ai_client, memory, file_utils

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("nexus_core")

# ── Personalidades disponibles ──────────────────────────────
PERSONALIDADES = {
    "asistente": {"nombre": "NEXUS Asistente",
        "prompt": "Eres NEXUS, un asistente inteligente de propósito general. "
                  "Eres amable, preciso y siempre ayudas al usuario. Respondes en español."},
    "creativo": {"nombre": "NEXUS Creativo",
        "prompt": "Eres NEXUS en modo creativo. Experto en diseño, arte, redacción publicitaria "
                  "y contenido visual. Tu tono es inspirador y prolífico. Respondes en español."},
    "analista": {"nombre": "NEXUS Analista",
        "prompt": "Eres NEXUS en modo analista. Riguroso con datos, métricas y tendencias. "
                  "Tono profesional y objetivo. Respondes en español."},
    "coach": {"nombre": "NEXUS Coach",
        "prompt": "Eres NEXUS en modo coach empresarial. Ayudas al usuario a alcanzar metas "
                  "de negocio con motivación y estrategia. Respondes en español."},
    "tecnicos": {"nombre": "NEXUS Técnico",
        "prompt": "Eres NEXUS en modo técnico. Experto en sistemas, automatización, impresión, "
                  "corte y software. Das soluciones prácticas paso a paso. Respondes en español."},
}

# ── Motores especializados ───────────────────────────────────
MOTORES = {
    "motor_atf":      {"puerto": 8004, "nombre": "ATF Faros",
        "descripcion": "Cotizaciones Aozoom, agenda instalaciones, pipeline ATF",
        "alternativas": "consultas generales de negocio o precios"},
    "motor_teens":    {"puerto": 8005, "nombre": "Teens Familiar",
        "descripcion": "Misiones familiares, puntos, aprobaciones padre/hijo",
        "alternativas": "consejos de organización familiar"},
    "motor_auth":     {"puerto": 8006, "nombre": "Auth Seguridad",
        "descripcion": "Login PIN, tokens de sesión, roles de usuario",
        "alternativas": "configuración de accesos"},
    "motor_pagos":    {"puerto": 8007, "nombre": "Pagos Finanzas",
        "descripcion": "Cotizaciones, registro de pagos, resumen financiero",
        "alternativas": "consejos financieros generales"},
    "motor_reportes": {"puerto": 8008, "nombre": "Reportes IA",
        "descripcion": "Resumen diario, semanal, análisis con IA",
        "alternativas": "análisis manual de datos"},
    "motor_sistema":  {"puerto": 8009, "nombre": "Sistema PC",
        "descripcion": "Control del sistema, archivos, procesos, Git",
        "alternativas": "operaciones manuales del sistema"},
    "motor_redes":    {"puerto": 8010, "nombre": "Redes Sociales",
        "descripcion": "Instagram, Facebook, TikTok, WhatsApp",
        "alternativas": "publicación manual en redes"},
}

# ── Palabras clave para enrutamiento ────────────────────────
REGLAS_ENRUTAMIENTO = [
    {"palabras": ["convertir", "dxf", "pdf", "archivo"], "motor": "motor_archivos"},
    {"palabras": ["diseño", "cortar", "rdw", "silhouette", "plotter"], "motor": "motor_diseno"},
    {"palabras": ["cliente", "pedido", "venta", "inventario", "stock"], "motor": "motor_negocios"},
    {"palabras": ["misión", "mision", "puntos", "recompensa", "coach"], "motor": "motor_coaching"},
    {"palabras": ["publicar", "post", "instagram", "facebook", "redes"], "motor": "motor_social"},
    {"palabras": ["forja", "emprendedor", "diagnóstico", "diagnostico", "comisión"], "motor": "motor_forja"},
]

# ── Respuestas degradadas (sin IA) ──────────────────────────
RESPUESTAS_DEGRADADAS = {
    "saludo": "¡Hola! Soy NEXUS v3. En este momento los proveedores de IA no están disponibles, "
              "pero estoy aquí para ayudarte en lo que pueda. Prueba de nuevo en unos minutos.",
    "motor": "El módulo solicitado no está disponible. Estamos trabajando para restablecerlo.",
    "default": "Disculpa, en este momento no puedo procesar tu solicitud porque los proveedores de "
               "IA no están disponibles. Por favor intenta nuevamente en unos instantes.",
}

# ── Aplicación FastAPI ───────────────────────────────────────
app = FastAPI(title="NEXUS v3 by Simplex",
    description="Orquestador inteligente multi-motor con capacidades de IA", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

# ── Estado global ────────────────────────────────────────────
motor_estado: dict = {}
ai_cliente = None
gestor_memoria = None
tiempo_inicio: float = 0.0


# ══════════════════════════════════════════════════════════════
#  FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════

async def verificar_motor(puerto: int, nombre: str, timeout: float = 3.0) -> dict:
    """Verifica si un motor responde en /health."""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"http://127.0.0.1:{puerto}/health",
                             timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return {"nombre": nombre, "puerto": puerto, "activo": True, "detalles": await r.json()}
    except Exception:
        pass
    return {"nombre": nombre, "puerto": puerto, "activo": False, "detalles": None}


async def delegar_a_motor(motor_key: str, accion: str, datos: dict, tiempo_maximo: int = 30) -> dict:
    """Envía una solicitud de ejecución a un motor especializado."""
    if motor_key not in MOTORES:
        return {"error": f"Motor desconocido: {motor_key}"}
    motor = MOTORES[motor_key]
    if not motor_estado.get(motor_key, {}).get("activo", False):
        return {"error": "Motor no disponible",
                "mensaje_friendly": f"El módulo de {motor['nombre']} no está disponible en este momento. "
                                    f"Puedo ayudarte con {motor['alternativas']}."}
    import aiohttp
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"http://127.0.0.1:{motor['puerto']}/execute",
                              json={"action": accion, "data": datos},
                              timeout=aiohttp.ClientTimeout(total=tiempo_maximo)) as r:
                if r.status == 200:
                    return {"exito": True, "datos": await r.json(), "motor": motor_key}
                return {"exito": False, "error": f"Motor respondió con estado {r.status}",
                        "detalle": await r.text(), "motor": motor_key}
    except asyncio.TimeoutError:
        return {"error": "Motor no disponible",
                "mensaje_friendly": f"El módulo de {motor['nombre']} tardó demasiado. "
                                    f"Puedo ayudarte con {motor['alternativas']}."}
    except Exception as exc:
        logger.error("Error al delegar al motor %s: %s", motor_key, exc)
        return {"error": "Motor no disponible",
                "mensaje_friendly": f"El módulo de {motor['nombre']} no está disponible. "
                                    f"Puedo ayudarte con {motor['alternativas']}."}


def determinar_motor(mensaje: str) -> Optional[str]:
    """Determina a qué motor delegar según palabras clave del mensaje."""
    msg = mensaje.lower()
    for regla in REGLAS_ENRUTAMIENTO:
        if any(p in msg for p in regla["palabras"]):
            return regla["motor"]
    return None


def obtener_respuesta_degradada(mensaje: str) -> str:
    """Retorna una respuesta pre-escrita cuando no hay IA disponible."""
    msg = mensaje.lower()
    if any(s in msg for s in ["hola", "buenos", "hey", "saludos"]):
        return RESPUESTAS_DEGRADADAS["saludo"]
    if any(s in msg for s in ["motor", "módulo", "modulo"]):
        return RESPUESTAS_DEGRADADAS["motor"]
    return RESPUESTAS_DEGRADADAS["default"]


def obtener_entorno_jinja() -> Environment:
    """Crea el entorno Jinja2 para plantillas."""
    directorio = os.path.join(os.path.dirname(__file__), "templates")
    if not os.path.isdir(directorio):
        os.makedirs(directorio, exist_ok=True)
    return Environment(loader=FileSystemLoader(directorio), autoescape=True)


def _generar_html_panel(uptime: str, proveedores: list, lista_motores: list,
                        stats_memoria: dict, metricas_negocio: dict) -> str:
    """Genera un panel HTML mínimo como respaldo si no hay plantilla Jinja2."""
    filas_motores = ""
    for m in lista_motores:
        icono = "🟢" if m["activo"] else "🔴"
        filas_motores += f"<tr><td>{icono}</td><td>{m['nombre']}</td><td>{m['descripcion']}</td></tr>"
    items_prov = "".join(f"<li>{p.get('nombre','?')}: {p.get('estado','?')}</li>" for p in proveedores)
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>NEXUS v3 — Panel de Control</title>
<style>body{{font-family:-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;margin:40px}}
h1{{color:#00ff88}}h2{{color:#00cc66;border-bottom:1px solid #333;padding-bottom:8px}}
table{{border-collapse:collapse;width:100%;margin:10px 0}}td,th{{border:1px solid #333;padding:8px;text-align:left}}
.card{{background:#111;border:1px solid #222;border-radius:8px;padding:20px;margin:15px 0}}
pre{{background:#0d0d0d;padding:10px;border-radius:4px;overflow-x:auto}}a{{color:#00ff88}}</style>
</head><body><h1>NEXUS v3 by Simplex</h1>
<p>Tiempo activo: <strong>{uptime}</strong> | v3.0.0</p>
<div class="card"><h2>Proveedores de IA</h2><ul>{items_prov}</ul></div>
<div class="card"><h2>Motores Especializados</h2>
<table><tr><th>Estado</th><th>Nombre</th><th>Descripción</th></tr>{filas_motores}</table></div>
<div class="card"><h2>Memoria</h2><pre>{json.dumps(stats_memoria,indent=2,ensure_ascii=False)}</pre></div>
<div class="card"><h2>Métricas de Negocio</h2><pre>{json.dumps(metricas_negocio,indent=2,ensure_ascii=False)}</pre></div>
<p style="margin-top:30px"><a href="/">← Volver al chat</a></p></body></html>"""


# ══════════════════════════════════════════════════════════════
#  EVENTO DE INICIO
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def evento_inicio():
    """Inicializa base de datos, IA, memoria, verifica motores y detecta programas."""
    global ai_cliente, gestor_memoria, motor_estado, tiempo_inicio
    tiempo_inicio = time.time()

    print("NEXUS v3 by Simplex - Iniciando...")

    logger.info("═══════════════════════════════════════════════")
    logger.info("  NEXUS v3 by Simplex — Iniciando orquestador")
    logger.info("═══════════════════════════════════════════════")

    # 1) Base de datos
    try:
        from lib.config import DB_PATH as _DB_PATH
        await database.init_db(str(_DB_PATH))
        logger.info("✓ Base de datos inicializada correctamente")
    except Exception as exc:
        logger.error("✗ Error al inicializar la base de datos: %s", exc)

    # 2) Cliente de IA
    try:
        from lib.ai_client import AIClient
        import os as _os
        ai_cliente = AIClient({
            "GROQ_API_KEY": _os.getenv("GROQ_API_KEY", ""),
            "ZAI_API_KEY": _os.getenv("ZAI_API_KEY", ""),
            "OLLAMA_URL": _os.getenv("OLLAMA_URL", "http://localhost:11434"),
        })
        logger.info("✓ Cliente de IA inicializado")
        proveedores = ["Groq", "Z.ai", "Ollama"]
        logger.info("  Proveedores de IA disponibles: %s", ", ".join(proveedores))
    except Exception as exc:
        logger.error("✗ Error al inicializar el cliente de IA: %s", exc)
        ai_cliente = None

    # 3) Gestor de memoria
    try:
        from lib.memory import MemoryManager
        gestor_memoria = MemoryManager()
        logger.info("✓ Gestor de memoria inicializado")
    except Exception as exc:
        logger.error("✗ Error al inicializar el gestor de memoria: %s", exc)
        gestor_memoria = None

    # 4) Verificar motores (8001-8006)
    logger.info("Verificando motores especializados...")
    for nombre_motor, info_motor in MOTORES.items():
        estado = await verificar_motor(info_motor["puerto"], info_motor["nombre"])
        motor_estado[nombre_motor] = estado
        icono = "✓" if estado["activo"] else "✗"
        logger.info("  %s %s (puerto %d): %s", icono, info_motor["nombre"],
                     info_motor["puerto"], "ACTIVO" if estado["activo"] else "INACTIVO")

    activos = [k for k, v in motor_estado.items() if v.get("activo")]
    logger.info("Motores activos: %d de %d", len(activos), len(MOTORES))

    # 5) Detectar programas instalados
    logger.info("Detectando programas instalados...")
    for cmd, nombre in [("inkscape","Inkscape"),("gimp","GIMP"),("libreoffice","LibreOffice"),
                         ("rdworks","RDWorks"),("silhouette","Silhouette Studio"),
                         ("ffmpeg","FFmpeg"),("magick","ImageMagick")]:
        try:
            proc = await asyncio.create_subprocess_shell(f"which {cmd}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await asyncio.wait_for(proc.communicate(), timeout=2.0)
            if proc.returncode == 0:
                logger.info("  ✓ %s detectado", nombre)
        except Exception:
            pass

    logger.info("═══════════════════════════════════════════════")
    logger.info("  NEXUS v3 listo — Escuchando en http://127.0.0.1:8000")
    logger.info("═══════════════════════════════════════════════")


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS PRINCIPALES
# ══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def pagina_principal(request: Request):
    """Sirve la página de chat con personalidades, motores y proveedores."""
    try:
        entorno = obtener_entorno_jinja()
        plantilla = entorno.get_template("chat.html")
        lista_motores = [
            {"clave": k, "nombre": v["nombre"], "descripcion": v["descripcion"],
             "activo": motor_estado.get(k, {}).get("activo", False), "puerto": v["puerto"]}
            for k, v in MOTORES.items()
        ]
        proveedores_ia = ["Groq", "Z.ai", "Ollama"] if ai_cliente else []
        html = plantilla.render(request=request, personalidades=PERSONALIDADES,
                                motores=lista_motores, proveedores_ia=proveedores_ia,
                                titulo="NEXUS v3 by Simplex")
        return HTMLResponse(content=html)
    except Exception as exc:
        logger.error("Error al renderizar la página principal: %s", exc)
        return HTMLResponse(content="<html><body><h1>NEXUS v3 by Simplex</h1>"
            "<p>Sistema inicializándose. Recarga en unos segundos.</p></body></html>",
            status_code=503)


@app.post("/chat")
async def endpoint_chat(request: Request):
    """Endpoint principal de chat: recibe mensaje, delega a motor si aplica, llama IA, guarda y aprende."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "El cuerpo debe ser JSON válido"})

    mensaje = body.get("message", "").strip()
    if not mensaje:
        return JSONResponse(status_code=400, content={"error": "El campo 'message' es obligatorio"})

    # INTERCEPCION TEMPRANA — comandos del sistema antes de cualquier IA
    _m = mensaje.lower().strip()
    if _m.startswith(("lee ", "leer ", "abre ")):
        _ruta = mensaje.split(" ", 1)[1].strip().strip('"').strip("'")
        try:
            from pathlib import Path as _Path
            _contenido = _Path(_ruta).read_text(encoding="utf-8", errors="ignore")
            return JSONResponse(content={
                "response": f"Archivo leído: `{_ruta}`\n\n{_contenido[:10000]}",
                "personality": body.get("personality", "asistente"),
                "session_id": body.get("session_id", "cmd")
            })
        except Exception as _e:
            return JSONResponse(content={
                "response": f"No pude leer `{_ruta}`: {_e}",
                "personality": body.get("personality", "asistente"),
                "session_id": body.get("session_id", "cmd")
            })

    personalidad_key = body.get("personality", "asistente")
    if personalidad_key not in PERSONALIDADES:
        personalidad_key = "asistente"
    session_id = body.get("session_id") or str(uuid.uuid4())
    motor_utilizado = None
    resultado_motor = None
    proveedor_usado = "ninguno"

    # a) Guardar mensaje del usuario
    try:
        database.guardar_mensaje(session_id=session_id, rol="user",
                                 contenido=mensaje, personalidad=personalidad_key)
    except Exception as exc:
        logger.warning("No se pudo guardar mensaje del usuario: %s", exc)

    # b) Obtener últimos 20 mensajes de contexto
    historial = []
    try:
        historial = database.obtener_mensajes(session_id, limite=20)
    except Exception as exc:
        logger.warning("No se pudo recuperar historial: %s", exc)

    # c) Memoria relevante para la consulta
    contexto_memoria = ""
    if gestor_memoria:
        try:
            datos_mem = gestor_memoria.buscar_relevantes(mensaje, limite=5)
            if datos_mem:
                lineas = [f"- {d.get('clave','info')}: {d.get('valor','')}" for d in datos_mem]
                contexto_memoria = "\n\n[Memoria del usuario]\n" + "\n".join(lineas) + "\n[/Memoria]"
        except Exception as exc:
            logger.warning("No se pudo acceder a la memoria: %s", exc)

    # d) Comandos directos del sistema (antes de pasar a IA)
    msg_lower = mensaje.lower().strip()

    # Comando: leer archivo
    if msg_lower.startswith("lee ") or msg_lower.startswith("leer ") or msg_lower.startswith("abre "):
        ruta = mensaje.split(" ", 1)[1].strip().strip('"').strip("'")
        try:
            from pathlib import Path
            contenido = Path(ruta).read_text(encoding="utf-8", errors="ignore")
            respuesta = f"Archivo leído: `{ruta}`\n\n```\n{contenido[:8000]}\n```"
            return JSONResponse(content={"response": respuesta, "personality": personalidad_key,
                                         "session_id": session_id, "motor": "sistema"})
        except Exception as e:
            return JSONResponse(content={"response": f"No pude leer `{ruta}`: {e}",
                                         "personality": personalidad_key, "session_id": session_id})

    # Comando: estado del sistema
    if any(x in msg_lower for x in ["estado del sistema", "estado motores", "cuántos motores", "cuantos motores"]):
        import httpx as _httpx
        try:
            async with _httpx.AsyncClient(timeout=5) as _c:
                estado = (await _c.get("http://localhost:8009/sistema/estado")).json()
            ram = estado.get("ram", {})
            resp = f"RAM libre: {ram.get('libre_gb')} GB / {ram.get('total_gb')} GB ({ram.get('pct')}% usada)\nCPU: {estado.get('cpu_pct')}%"
            return JSONResponse(content={"response": resp, "personality": personalidad_key, "session_id": session_id})
        except Exception:
            pass

    # e) Determinar y delegar a motor si aplica
    motor_key = determinar_motor(mensaje)
    if motor_key:
        info_motor = MOTORES[motor_key]
        motor_utilizado = motor_key
        resultado_motor = await delegar_a_motor(motor_key, "process_query",
            {"message": mensaje, "session_id": session_id, "personality": personalidad_key})
        if not resultado_motor.get("exito"):
            msj_err = resultado_motor.get("mensaje_friendly",
                                          f"El módulo de {info_motor['nombre']} no está disponible.")
            try:
                database.guardar_mensaje(session_id=session_id, rol="assistant",
                                         contenido=msj_err, personalidad=personalidad_key)
            except Exception:
                pass
            return JSONResponse(content={"response": msj_err, "personality": personalidad_key,
                                         "session_id": session_id, "motor_used": motor_key,
                                         "ai_provider": "ninguno (motor no disponible)"})

    # f) Construir prompt para la IA
    prompt_sistema = PERSONALIDADES[personalidad_key]["prompt"]
    if resultado_motor and resultado_motor.get("exito"):
        datos_brutos = json.dumps(resultado_motor.get("datos", {}), ensure_ascii=False, indent=2)
        prompt_sistema += (
            f"\n\n[Resultado del motor {motor_utilizado}]\n"
            f"El motor especializado devolvió:\n{datos_brutos}\n[/Resultado del motor]\n\n"
            "Instrucciones: Presenta esta información al usuario de forma clara, "
            "natural y bien organizada. Traduce términos técnicos si es necesario.")
    if contexto_memoria:
        prompt_sistema += contexto_memoria

    # Formatear historial para la IA
    mensajes_ia = [{"role": "system", "content": prompt_sistema}]
    for msg in historial:
        rol = msg.get("rol", "user")
        if rol in ("user", "assistant"):
            mensajes_ia.append({"role": rol, "content": msg.get("contenido", "")})

    # Llamar a la IA
    respuesta_ia = ""
    try:
        if ai_cliente is None:
            raise RuntimeError("Cliente de IA no inicializado")
        respuesta_ia = await ai_cliente.generar_respuesta(mensajes_ia)
        # Fix: Groq a veces devuelve texto con doble codificación UTF-8 en Windows
        try:
            respuesta_ia = respuesta_ia.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        proveedor_usado = ai_cliente.proveedor_actual()
    except Exception as exc:
        logger.error("Error al llamar a la IA: %s", exc)
        respuesta_ia = obtener_respuesta_degradada(mensaje)
        proveedor_usado = "ninguno (degradado)"

    if not respuesta_ia or not respuesta_ia.strip():
        respuesta_ia = "Disculpa, no pude generar una respuesta. Por favor intenta de nuevo."

    # g) Guardar respuesta de la IA
    try:
        database.guardar_mensaje(session_id=session_id, rol="assistant",
                                 contenido=respuesta_ia, personalidad=personalidad_key)
    except Exception as exc:
        logger.warning("No se pudo guardar la respuesta: %s", exc)

    # h) Aprender de la conversación
    if gestor_memoria:
        try:
            gestor_memoria.aprender_de_mensaje(mensaje_usuario=mensaje, respuesta_ia=respuesta_ia,
                                               session_id=session_id)
        except Exception as exc:
            logger.warning("No se pudo aprender de la conversación: %s", exc)

    # i) Retornar respuesta
    return JSONResponse(content={"response": respuesta_ia, "personality": personalidad_key,
                                 "session_id": session_id, "motor_used": motor_utilizado,
                                 "ai_provider": proveedor_usado},
                        media_type="application/json; charset=utf-8")


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS DE ESTADO Y MONITOREO
# ══════════════════════════════════════════════════════════════

@app.get("/motors/status")
async def estado_motores():
    """Estado de todos los motores especializados."""
    return {k: {"nombre": v["nombre"], "descripcion": v["descripcion"], "puerto": v["puerto"],
                "activo": motor_estado.get(k, {}).get("activo", False),
                "detalles": motor_estado.get(k, {}).get("detalles")}
            for k, v in MOTORES.items()}


@app.get("/ai/status")
async def estado_ia():
    """Estado de los proveedores de IA."""
    if not ai_cliente:
        return {"estado": "no_disponible", "mensaje": "Cliente de IA no inicializado", "proveedores": []}
    detalles = []
    for prov in ai_cliente.listar_proveedores():
        try:
            detalles.append(ai_cliente.obtener_estado_proveedor(prov))
        except Exception as exc:
            detalles.append({"nombre": prov, "estado": "error", "detalle": str(exc)})
    return {"estado": "disponible", "proveedor_actual": ai_cliente.proveedor_actual(), "proveedores": detalles}


@app.get("/memory/stats")
async def estadisticas_memoria():
    """Estadísticas del sistema de memoria."""
    if not gestor_memoria:
        return {"estado": "no_disponible", "estadisticas": {}}
    try:
        return {"estado": "disponible", "estadisticas": gestor_memoria.obtener_estadisticas()}
    except Exception as exc:
        return {"estado": "error", "detalle": str(exc)}


@app.get("/memory/summary")
async def resumen_memoria():
    """Resumen de la memoria del usuario."""
    if not gestor_memoria:
        return {"estado": "no_disponible", "resumen": []}
    try:
        return {"estado": "disponible", "resumen": gestor_memoria.obtener_resumen()}
    except Exception as exc:
        return {"estado": "error", "detalle": str(exc)}


@app.delete("/memory/{clave}")
async def eliminar_memoria(clave: str):
    """Elimina una entrada de la memoria del usuario."""
    if not gestor_memoria:
        return JSONResponse(status_code=503, content={"error": "Gestor de memoria no disponible"})
    try:
        if gestor_memoria.eliminar(clave):
            return {"mensaje": f"Entrada '{clave}' eliminada correctamente"}
        return JSONResponse(status_code=404, content={"error": f"No se encontró la entrada '{clave}'"})
    except Exception as exc:
        logger.error("Error al eliminar memoria: %s", exc)
        return JSONResponse(status_code=500, content={"error": f"Error interno: {exc}"})


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS DE VOZ (TTS y reconocimiento)
# ══════════════════════════════════════════════════════════════

@app.post("/tts")
async def texto_a_voz(request: Request):
    """Convierte texto a voz usando edge_tts. Retorna MP3 como StreamingResponse."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "El cuerpo debe ser JSON válido"})
    texto = body.get("text", "").strip()
    if not texto:
        return JSONResponse(status_code=400, content={"error": "El campo 'text' es obligatorio"})
    voz = body.get("voice", "es-MX-JorgeNeural")
    try:
        import edge_tts
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        ruta = tmp.name; tmp.close()
        await edge_tts.Communicate(texto, voz).save(ruta)
        def gen():
            with open(ruta, "rb") as f:
                yield from f
            try: os.unlink(ruta)
            except OSError: pass
        return StreamingResponse(gen(), media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=nexus_tts.mp3"})
    except ImportError:
        return JSONResponse(status_code=503,
            content={"error": "Librería edge_tts no instalada. Ejecuta: pip install edge-tts"})
    except Exception as exc:
        logger.error("Error en TTS: %s", exc)
        return JSONResponse(status_code=500, content={"error": f"Error al generar audio: {exc}"})


@app.post("/voice_chat")
async def chat_por_voz(audio: UploadFile = File(...)):
    """Recibe audio → texto → IA → TTS. Requiere SpeechRecognition y ffmpeg."""
    try:
        import speech_recognition as sr
    except ImportError:
        return JSONResponse(status_code=503, content={"error":
            "Reconocimiento de voz no disponible. Instala: pip install SpeechRecognition pydub y ffmpeg."})
    # Guardar audio subido temporalmente
    ruta_audio = ""
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(await audio.read()); tmp.close()
        ruta_audio = tmp.name
        reconocedor = sr.Recognizer()
        with sr.AudioFile(ruta_audio) as fuente:
            texto_transcrito = reconocedor.recognize_google(reconocedor.record(fuente), language="es-ES")
    except sr.UnknownValueError:
        return JSONResponse(status_code=400, content={"error": "No se pudo entender el audio."})
    except sr.RequestError as exc:
        return JSONResponse(status_code=503, content={"error": f"Error del servicio de voz: {exc}"})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": f"Error al procesar audio: {exc}"})
    finally:
        if ruta_audio:
            try: os.unlink(ruta_audio)
            except OSError: pass

    if not texto_transcrito.strip():
        return JSONResponse(status_code=400, content={"error": "El audio no contenía texto reconocible."})

    # Procesar con IA
    try:
        if ai_cliente:
            respuesta = await ai_cliente.generar_respuesta([
                {"role": "system", "content": PERSONALIDADES["asistente"]["prompt"]},
                {"role": "user", "content": texto_transcrito}])
        else:
            respuesta = obtener_respuesta_degradada(texto_transcrito)
    except Exception as exc:
        logger.error("Error al procesar voz con IA: %s", exc)
        respuesta = obtener_respuesta_degradada(texto_transcrito)

    return JSONResponse(content={"texto_original": texto_transcrito, "respuesta": respuesta,
                                 "audio_url": "/tts"})


# ══════════════════════════════════════════════════════════════
#  ENDPOINTS PROXY — Negocios y Coaching
# ══════════════════════════════════════════════════════════════

async def _proxy_motor(motor_key: str, accion: str, nombre_servicio: str):
    """Helper genérico para proxy a motores de negocio/coaching."""
    resultado = await delegar_a_motor(motor_key, accion, {})
    if resultado.get("exito"):
        return JSONResponse(content=resultado.get("datos", {}))
    return JSONResponse(status_code=503,
        content={"error": resultado.get("mensaje_friendly", f"Servicio de {nombre_servicio} no disponible")})


@app.get("/api/status")
async def api_status():
    """Ping — el frontend lo usa para verificar conexión cada 30s."""
    return {"ok": True, "version": "3.0", "estado": "online"}


@app.get("/api/clients")
async def obtener_clientes():
    """Proxy: lista de clientes desde motor_negocios."""
    return await _proxy_motor("motor_negocios", "list_clients", "clientes")

@app.get("/api/products")
async def obtener_productos():
    """Proxy: lista de productos desde motor_negocios."""
    return await _proxy_motor("motor_negocios", "list_products", "productos")

@app.get("/api/orders")
async def obtener_pedidos():
    """Proxy: lista de pedidos desde motor_negocios."""
    return await _proxy_motor("motor_negocios", "list_orders", "pedidos")

@app.get("/api/missions")
async def obtener_misiones():
    """Proxy: lista de misiones desde motor_coaching."""
    return await _proxy_motor("motor_coaching", "list_missions", "misiones")


# ══════════════════════════════════════════════════════════════
#  MANUAL
# ══════════════════════════════════════════════════════════════

@app.get("/manual", response_class=HTMLResponse)
async def manual(request: Request):
    """Manual de usuario NEXUS v3."""
    ruta = os.path.join(os.path.dirname(__file__), "templates", "manual.html")
    with open(ruta, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ══════════════════════════════════════════════════════════════
#  PANEL DE CONTROL
# ══════════════════════════════════════════════════════════════

@app.get("/panel", response_class=HTMLResponse)
async def panel_control(request: Request):
    """Panel con: uptime, proveedores IA, motores, memoria, métricas de negocio."""
    up = time.time() - tiempo_inicio
    uptime = f"{int(up//3600)}h {int((up%3600)//60)}m {int(up%60)}s"

    # Proveedores IA
    proveedores = []
    if ai_cliente:
        for p in ai_cliente.listar_proveedores():
            try: proveedores.append(ai_cliente.obtener_estado_proveedor(p))
            except Exception: proveedores.append({"nombre": p, "estado": "desconocido"})

    # Motores
    lista_motores = [{"clave": k, "nombre": v["nombre"], "descripcion": v["descripcion"],
                      "activo": motor_estado.get(k, {}).get("activo", False)} for k, v in MOTORES.items()]

    # Memoria
    stats_memoria = {}
    if gestor_memoria:
        try: stats_memoria = gestor_memoria.obtener_estadisticas()
        except Exception: stats_memoria = {"error": "no disponible"}

    # Métricas de negocio
    metricas_negocio = {}
    if motor_estado.get("motor_negocios", {}).get("activo"):
        res = await delegar_a_motor("motor_negocios", "get_metrics", {}, tiempo_maximo=10)
        if res.get("exito"):
            metricas_negocio = res.get("datos", {})

    # Intentar plantilla Jinja2, si no existe generar HTML mínimo
    try:
        entorno = obtener_entorno_jinja()
        plantilla = entorno.get_template("panel.html")
        html = plantilla.render(request=request, titulo="NEXUS v3 — Panel de Control",
            uptime=uptime, proveedores=proveedores, motores=lista_motores,
            memoria=stats_memoria, negocio=metricas_negocio, version="3.0.0")
        return HTMLResponse(content=html)
    except Exception:
        logger.warning("Plantilla panel.html no encontrada, generando panel mínimo")
        return HTMLResponse(content=_generar_html_panel(uptime, proveedores, lista_motores,
                                                        stats_memoria, metricas_negocio))


# ══════════════════════════════════════════════════════════════
#  MANEJO GLOBAL DE ERRORES
# ══════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def manejador_errores(request: Request, exc: Exception):
    """Captura excepciones no manejadas y retorna respuesta segura al usuario."""
    logger.error("Excepción no manejada en %s %s: %s", request.method, request.url.path, exc,
                 exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "Ocurrió un error interno en NEXUS v3. Intenta de nuevo.",
        "detalle_tecnico": str(exc) if getattr(settings, 'DEBUG', False) else None})


# ── Montar archivos estáticos ────────────────────────────────
dir_static = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(dir_static):
    app.mount("/static", StaticFiles(directory=dir_static), name="static")


# ══════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("\033[92m Iniciando NEXUS v3 by Simplex...\033[0m")
    port = int(os.getenv("NEXUS_PORT", 8003))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

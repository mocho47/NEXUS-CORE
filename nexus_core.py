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

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from lib.config import settings
from lib import database, ai_client, memory

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("nexus_core")

# ── Personalidades disponibles ──────────────────────────────
# Prompt maestro — se carga al inicio y se reintenta en cada chat si es None
_PROMPT_ZAI_PATH     = "C:/NEXUS_v3_NEW/PROMPT_ZAI.md"
_PROMPT_COMPACT_PATH = "C:/NEXUS_v3_NEW/PROMPT_COMPACT.md"

def _leer_prompt_maestro() -> str | None:
    """Carga PROMPT_COMPACT.md para uso diario. PROMPT_ZAI.md solo si piden análisis profundo."""
    from pathlib import Path
    # Primero intenta el prompt compacto (operativo, ~400 chars)
    try:
        txt = Path(_PROMPT_COMPACT_PATH).read_text(encoding="utf-8")
        print(f"[PROMPT] COMPACT cargado ({len(txt)} chars)", flush=True)
        return txt
    except Exception:
        pass
    # Fallback al prompt maestro completo
    try:
        txt = Path(_PROMPT_ZAI_PATH).read_text(encoding="utf-8")
        print(f"[PROMPT] ZAI cargado ({len(txt)} chars)", flush=True)
        return txt
    except Exception as e:
        print(f"[WARN] No se pudo leer prompt: {e}", flush=True)
        return None

_PROMPT_MAESTRO = _leer_prompt_maestro()

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
    "motor_editor":   {"puerto": 8012, "nombre": "Editor de Imágenes",
        "descripcion": "Genera imágenes desde texto (Z.ai/Pollinations) y edita imágenes con PIL",
        "alternativas": "editar manualmente en Photoshop o Corel"},
    "motor_maquila":  {"puerto": 8011, "nombre": "Maquila DTF/Sublimación",
        "descripcion": "Genera layouts de piezas para DTF UV, sublimación, stickers, corte",
        "alternativas": "acomodar manualmente en Corel"},
    "motor_forja":    {"puerto": 8020, "nombre": "FORJA Emprendedores",
        "descripcion": "Diagnóstico negocio, plan, MLM comisiones, coaching",
        "alternativas": "asesoría manual"},
    "motor_canbus":   {"puerto": 8021, "nombre": "CAN Bus Automotriz",
        "descripcion": "Diagnóstico eléctrico automotriz, retrofit faros, CAN/LIN Bus multimarca",
        "alternativas": "diagnóstico manual con multímetro"},
    "motor_cajas":    {"puerto": 8013, "nombre": "Cajas Láser",
        "descripcion": "Genera cajas MDF/acrílico paramétrica con boxes.exe y cajas de luz con ezdxf",
        "alternativas": "diseño manual en CorelDRAW"},
    "motor_operador": {"puerto": 8014, "nombre": "Operador de Software",
        "descripcion": "Opera CorelDRAW, Silhouette, Inkscape y cualquier app con COM/pyautogui",
        "alternativas": "operar manualmente el programa"},
    "motor_coaching": {"puerto": 8016, "nombre": "Coaching y Psicología",
        "descripcion": "Coaching empresarial, psicología familiar, misiones y hábitos",
        "alternativas": "consejo general de bienestar"},
    "motor_watchdog": {"puerto": 8015, "nombre": "Guardián del Sistema",
        "descripcion": "Monitorea RAM/CPU, ping motores cada 5min, limpieza automática",
        "alternativas": "revisar manualmente el estado del sistema"},
    "motor_diseno":   {"puerto": 8002, "nombre": "Diseño y Programas",
        "descripcion": "Abre archivos en CorelDRAW/Silhouette/Aspire, exporta con Inkscape CLI",
        "alternativas": "abrir el programa manualmente"},
    "motor_catalogo": {"puerto": 8017, "nombre": "Catálogos B2B",
        "descripcion": "Genera catálogos Milens con imágenes, PDF y video de presentación (hotelería, restaurantes)",
        "alternativas": "armar catálogo manualmente en Corel"},
    "motor_archivos": {"puerto": 8001, "nombre": "Archivos y Conversión",
        "descripcion": "Convierte imágenes/PDFs/SVGs entre formatos, valida archivos de diseño (PNG/JPG/SVG/DXF/PDF)",
        "alternativas": "convertir manualmente en CorelDRAW o Inkscape"},
}

# ── Palabras clave para enrutamiento ────────────────────────
REGLAS_ENRUTAMIENTO = [
    {"palabras": ["cotizar", "costo", "presupuesto", "aozoom", "retrofit", "instalacion", "instalación", "kit led", "kit xenon"], "motor": "motor_atf"},
    {"palabras": ["mision", "misión", "puntos", "recompensa", "canje", "hijo", "familia", "papá", "mamá"], "motor": "motor_teens"},
    {"palabras": ["catalogo", "catálogo", "milens", "hoteleria", "hotelería", "hotel", "restaurante", "articulo milens", "caja mdf", "posavasos", "tabla servicio"], "motor": "motor_catalogo"},
    {"palabras": ["pago", "factura", "cobro", "abono", "finanzas", "ingreso", "gasto"], "motor": "motor_pagos"},
    {"palabras": ["reporte", "resumen", "estadística", "estadistica", "semana", "ventas del"], "motor": "motor_reportes"},
    {"palabras": ["publicar", "post", "instagram", "facebook", "tiktok", "redes", "story"], "motor": "motor_redes"},
    {"palabras": ["proceso", "cpu", "ram", "disco", "sistema", "reiniciar motor", "git push"], "motor": "motor_sistema"},
    {"palabras": ["convierte", "convertir", "conversion", "conversión", "formato", "png a", "jpg a", "pdf a", "svg a", "dxf a", "a png", "a jpg", "a pdf", "a svg", "a dxf"], "motor": "motor_archivos"},
    {"palabras": ["genera imagen", "generar imagen", "crea imagen", "crear imagen",
                  "genera una imagen", "crea una imagen", "haz una imagen", "quiero imagen",
                  "imagina", "diseña imagen", "dibuja", "ilustra",
                  "cambia color", "modifica imagen", "edita imagen", "ajusta imagen",
                  "brillo", "contraste", "escala de grises", "rota imagen", "voltea imagen",
                  "convierte a sepia", "quita fondo", "imagen de "], "motor": "motor_editor"},
    {"palabras": ["piezas", "layout dtf", "layout maquila", "planilla dtf",
                  "acomodo piezas", "distribuye piezas", "maquila dtf", "sublimacion",
                  "sublimación", "dtf uv", "piezas cm", "piezas de", "piezas en",
                  "area de impresion", "área de impresion",
                  "cm espacio", "mm espacio", "2mm", "3mm espacio"], "motor": "motor_maquila"},
    {"palabras": ["forja", "emprendedor", "comisión", "referido", "plan de negocio"], "motor": "motor_forja"},
    {"palabras": ["abrir en corel", "exportar en corel", "exportar corel", "corel exporta",
                  "abrir corel", "operar corel", "opera corel", "desde corel",
                  "abrir en silhouette", "exportar silhouette", "abre corel",
                  "captura pantalla", "screenshot nexus",
                  "clic en pantalla", "click pantalla",
                  "exportar svg", "exportar pdf inkscape"], "motor": "motor_operador"},
    {"palabras": ["coaching", "coach", "hábito", "habito", "motivación", "motivacion",
                  "psicología", "psicologia", "misión personal", "meta personal"], "motor": "motor_coaching"},
    {"palabras": ["caja", "cajas", "caja mdf", "caja laser", "caja láser", "caja de luz",
                  "letrero luminoso", "caja acrilico", "caja acrílico", "genera caja",
                  "generar caja", "crear caja", "bandeja", "cajón laser", "cajon laser",
                  "bisagra mdf", "display case", "tapa corredera"], "motor": "motor_cajas"},
    {"palabras": ["modo canbus", "canbus", "can bus", "lin bus", "obd", "dtc", "falla electrica", "falla eléctrica",
                  "señal de altas", "señal altas", "balastro", "bixenon", "bi-xenon", "bi-led", "projector",
                  "relay faro", "faro no enciende", "error bombilla", "bcm faro", "faro led",
                  "cable altas", "cable bajas", "conector faro", "cluster faro",
                  "ford faro", "toyota faro", "honda faro", "nissan faro", "vw faro",
                  "diagnostico automotriz", "diagnóstico automotriz",
                  "electrica automotriz", "eléctrica automotriz"], "motor": "motor_canbus"},
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
    """Determina a qué motor delegar según palabras clave del mensaje.
    Requiere al menos 2 palabras clave O una palabra clave al inicio del mensaje
    para evitar falsos positivos en mensajes largos."""
    msg = mensaje.lower()
    palabras_msg = set(msg.split())
    for regla in REGLAS_ENRUTAMIENTO:
        coincidencias = [p for p in regla["palabras"] if p in msg]
        if not coincidencias:
            continue
        # Routear solo si: el mensaje empieza con la palabra clave
        # O hay 2+ coincidencias, o el mensaje es corto (menos de 8 palabras)
        es_corto = len(palabras_msg) < 8
        empieza = any(msg.strip().startswith(p) for p in coincidencias)
        multiple = len(coincidencias) >= 2
        if empieza or multiple or es_corto:
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
            "OPENROUTER_API_KEY": _os.getenv("OPENROUTER_API_KEY", "") or _os.getenv("DEEPSEEK_API_KEY", ""),
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
        from lib.config import DB_PATH as _DB_PATH
        gestor_memoria = MemoryManager(db=str(_DB_PATH))
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


@app.get("/forja", response_class=HTMLResponse)
async def pagina_forja(request: Request):
    """Cuestionario de diagnóstico empresarial — Forja NEXUS (20 pasos)."""
    html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Diagnóstico de Negocio — Forja by NEXUS</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
:root{--c:#00c2e0;--bg:#04090f;--card:#0a1628;--border:rgba(0,194,224,0.2);}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#fff;min-height:100vh;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:20px;}

/* Progress */
.progress-wrap{width:100%;max-width:560px;margin-bottom:24px;padding-top:20px;}
.progress-label{display:flex;justify-content:space-between;font-size:0.72rem;color:rgba(255,255,255,0.4);margin-bottom:8px;letter-spacing:1px;}
.progress-bar{height:3px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;}
.progress-fill{height:100%;background:var(--c);transition:width .4s ease;border-radius:4px;}

/* Card */
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:44px 40px;
  max-width:560px;width:100%;box-shadow:0 8px 48px rgba(0,0,0,0.6);min-height:340px;
  display:flex;flex-direction:column;justify-content:space-between;}

/* Logo */
.logo{font-size:0.8rem;font-weight:900;letter-spacing:3px;color:var(--c);text-transform:uppercase;margin-bottom:32px;opacity:0.8;}

/* Step */
.step{display:none;animation:fadeUp .35s ease;}
.step.active{display:flex;flex-direction:column;flex:1;}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

.step-num{font-size:0.7rem;color:rgba(255,255,255,0.3);letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;}
.step-q{font-size:1.45rem;font-weight:800;line-height:1.3;margin-bottom:8px;}
.step-hint{font-size:0.85rem;color:rgba(255,255,255,0.4);margin-bottom:28px;line-height:1.5;}

/* Text input */
input[type=text],input[type=tel],input[type=email],textarea{
  background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;
  padding:14px 16px;color:#fff;font-size:1rem;outline:none;transition:border-color .2s;width:100%;
  font-family:inherit;}
input:focus,textarea:focus{border-color:var(--c);}
input::placeholder,textarea::placeholder{color:rgba(255,255,255,0.25);}
textarea{resize:vertical;min-height:90px;}

/* Options (single choice) */
.options{display:flex;flex-direction:column;gap:10px;margin-top:4px;}
.opt{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;
  padding:13px 18px;cursor:pointer;font-size:0.93rem;transition:all .2s;text-align:left;
  color:rgba(255,255,255,0.8);}
.opt:hover{border-color:var(--c);color:#fff;background:rgba(0,194,224,0.06);}
.opt.selected{border-color:var(--c);background:rgba(0,194,224,0.12);color:#fff;font-weight:600;}

/* Multi-choice */
.opt.multi.selected::before{content:'✓ ';}

/* Nav */
.nav{display:flex;gap:12px;margin-top:32px;align-items:center;}
.btn-next{background:var(--c);color:#04090f;border:none;border-radius:10px;padding:14px 28px;
  font-size:0.95rem;font-weight:800;cursor:pointer;transition:opacity .2s,transform .2s;flex:1;letter-spacing:.3px;}
.btn-next:hover{opacity:.88;transform:translateY(-1px);}
.btn-next:disabled{opacity:.35;cursor:not-allowed;transform:none;}
.btn-back{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.5);border:1px solid rgba(255,255,255,0.1);
  border-radius:10px;padding:14px 18px;font-size:0.93rem;cursor:pointer;transition:all .2s;}
.btn-back:hover{color:#fff;border-color:rgba(255,255,255,0.25);}

/* Loading */
.loading{display:none;flex-direction:column;align-items:center;justify-content:center;gap:20px;padding:40px 0;}
.spinner{width:40px;height:40px;border:3px solid rgba(0,194,224,0.15);border-top-color:var(--c);
  border-radius:50%;animation:spin 0.8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
.loading p{color:rgba(255,255,255,0.5);font-size:0.9rem;text-align:center;}

/* Results */
.results{display:none;flex-direction:column;gap:0;}
.results-header{text-align:center;margin-bottom:32px;}
.results-header h2{font-size:1.8rem;font-weight:900;color:var(--c);margin-bottom:8px;}
.results-header p{color:rgba(255,255,255,0.5);font-size:0.9rem;}
.score-ring{width:80px;height:80px;margin:0 auto 20px;position:relative;}
.score-ring svg{transform:rotate(-90deg);}
.score-ring .score-num{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  font-size:1.4rem;font-weight:900;color:var(--c);}
.diag-content{font-size:0.92rem;line-height:1.75;color:rgba(255,255,255,0.75);white-space:pre-wrap;}
.diag-section{margin-bottom:20px;}
.diag-section h3{font-size:0.8rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;
  color:var(--c);margin-bottom:8px;}
.diag-section p{color:rgba(255,255,255,0.7);font-size:0.9rem;line-height:1.7;}
.btn-wa{background:#25d366;color:#fff;border:none;border-radius:10px;padding:14px 24px;
  font-size:0.95rem;font-weight:700;cursor:pointer;width:100%;margin-top:20px;
  display:flex;align-items:center;justify-content:center;gap:10px;}
.btn-wa:hover{opacity:.9;}

@media(max-width:500px){.card{padding:32px 24px;}.step-q{font-size:1.2rem;}}
</style>
</head>
<body>

<div class="progress-wrap">
  <div class="progress-label">
    <span class="logo">FORJA · NEXUS</span>
    <span id="prog-label">Paso 1 de 20</span>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="prog-fill" style="width:5%"></div></div>
</div>

<div class="card" id="main-card">

  <!-- STEPS -->
  <div id="steps-wrap" style="display:flex;flex-direction:column;flex:1;">

    <!-- 1 Nombre -->
    <div class="step active" data-step="1" data-type="text" data-key="nombre">
      <div>
        <div class="step-num">Pregunta 1 · Personal</div>
        <div class="step-q">¿Cuál es tu nombre?</div>
        <div class="step-hint">Como quieres que te llame NEXUS.</div>
        <input type="text" placeholder="Tu nombre" autocomplete="off" autocapitalize="words">
      </div>
    </div>

    <!-- 2 Negocio -->
    <div class="step" data-step="2" data-type="text" data-key="negocio">
      <div>
        <div class="step-num">Pregunta 2 · Tu negocio</div>
        <div class="step-q">¿Cómo se llama tu negocio o proyecto?</div>
        <div class="step-hint">Puede ser una idea, un proyecto en marcha o un negocio establecido.</div>
        <input type="text" placeholder="Nombre de tu negocio" autocomplete="off">
      </div>
    </div>

    <!-- 3 Giro -->
    <div class="step" data-step="3" data-type="text" data-key="giro">
      <div>
        <div class="step-num">Pregunta 3 · Operación</div>
        <div class="step-q">¿A qué se dedica tu negocio?</div>
        <div class="step-hint">Describe brevemente qué vendes o qué servicio ofreces.</div>
        <textarea placeholder="Ej: vendo ropa en línea, doy clases de yoga, instalo alarmas..."></textarea>
      </div>
    </div>

    <!-- 4 Tiempo -->
    <div class="step" data-step="4" data-type="choice" data-key="tiempo_operacion">
      <div>
        <div class="step-num">Pregunta 4 · Madurez</div>
        <div class="step-q">¿Cuánto tiempo llevas operando?</div>
        <div class="step-hint">Elige la opción más cercana a tu realidad.</div>
        <div class="options">
          <button class="opt" data-val="idea">Todavía es solo una idea</button>
          <button class="opt" data-val="menos1">Menos de 1 año</button>
          <button class="opt" data-val="1a3">Entre 1 y 3 años</button>
          <button class="opt" data-val="3a5">Entre 3 y 5 años</button>
          <button class="opt" data-val="mas5">Más de 5 años</button>
        </div>
      </div>
    </div>

    <!-- 5 Equipo -->
    <div class="step" data-step="5" data-type="choice" data-key="empleados">
      <div>
        <div class="step-num">Pregunta 5 · Equipo</div>
        <div class="step-q">¿Cuántas personas trabajan en tu negocio?</div>
        <div class="step-hint">Cuenta freelancers y colaboradores frecuentes.</div>
        <div class="options">
          <button class="opt" data-val="solo">Solo yo</button>
          <button class="opt" data-val="2a5">2 a 5 personas</button>
          <button class="opt" data-val="6a20">6 a 20 personas</button>
          <button class="opt" data-val="mas20">Más de 20 personas</button>
        </div>
      </div>
    </div>

    <!-- 6 Facturación -->
    <div class="step" data-step="6" data-type="choice" data-key="facturacion_mensual">
      <div>
        <div class="step-num">Pregunta 6 · Finanzas</div>
        <div class="step-q">¿Cuánto factura tu negocio al mes aproximadamente?</div>
        <div class="step-hint">Ventas brutas, antes de costos. Es confidencial.</div>
        <div class="options">
          <button class="opt" data-val="0">Aún no genera ingresos</button>
          <button class="opt" data-val="menos20k">Menos de $20,000</button>
          <button class="opt" data-val="20a50k">$20,000 – $50,000</button>
          <button class="opt" data-val="50a150k">$50,000 – $150,000</button>
          <button class="opt" data-val="150a500k">$150,000 – $500,000</button>
          <button class="opt" data-val="mas500k">Más de $500,000</button>
        </div>
      </div>
    </div>

    <!-- 7 Margen -->
    <div class="step" data-step="7" data-type="choice" data-key="margen_ganancia">
      <div>
        <div class="step-num">Pregunta 7 · Rentabilidad</div>
        <div class="step-q">¿Cuál es tu margen de ganancia aproximado?</div>
        <div class="step-hint">Lo que te queda después de pagar costos y gastos operativos.</div>
        <div class="options">
          <button class="opt" data-val="negativo">Estoy perdiendo dinero</button>
          <button class="opt" data-val="0a10">0 – 10 %</button>
          <button class="opt" data-val="10a25">10 – 25 %</button>
          <button class="opt" data-val="25a40">25 – 40 %</button>
          <button class="opt" data-val="mas40">Más del 40 %</button>
          <button class="opt" data-val="no_se">No lo tengo calculado</button>
        </div>
      </div>
    </div>

    <!-- 8 Captación -->
    <div class="step" data-step="8" data-type="choice" data-key="captacion_clientes">
      <div>
        <div class="step-num">Pregunta 8 · Ventas</div>
        <div class="step-q">¿Cómo consigues la mayoría de tus clientes?</div>
        <div class="step-hint">El canal que más clientes te trae hoy.</div>
        <div class="options">
          <button class="opt" data-val="referidos">Referidos / boca a boca</button>
          <button class="opt" data-val="redes">Redes sociales (IG, FB, TikTok)</button>
          <button class="opt" data-val="whatsapp">WhatsApp directo</button>
          <button class="opt" data-val="marketplace">Marketplace (ML, Amazon, Shopify)</button>
          <button class="opt" data-val="google">Google / SEO / publicidad</button>
          <button class="opt" data-val="fisico">Local físico / mostrador</button>
          <button class="opt" data-val="sin_sistema">No tengo un sistema claro</button>
        </div>
      </div>
    </div>

    <!-- 9 Proceso venta -->
    <div class="step" data-step="9" data-type="choice" data-key="proceso_venta">
      <div>
        <div class="step-num">Pregunta 9 · Proceso</div>
        <div class="step-q">¿Tienes un proceso de venta definido?</div>
        <div class="step-hint">Un guión, embudo o protocolo que tu equipo siga.</div>
        <div class="options">
          <button class="opt" data-val="si_documentado">Sí, está documentado y lo seguimos</button>
          <button class="opt" data-val="si_informal">Sí, pero está en mi cabeza</button>
          <button class="opt" data-val="improvisado">Cada venta es diferente, improviso</button>
          <button class="opt" data-val="no">No tengo proceso de venta</button>
        </div>
      </div>
    </div>

    <!-- 10 Retención -->
    <div class="step" data-step="10" data-type="choice" data-key="retencion_clientes">
      <div>
        <div class="step-num">Pregunta 10 · Fidelización</div>
        <div class="step-q">¿Qué porcentaje de tus clientes repite o te recomienda?</div>
        <div class="step-hint">Estima de manera honesta.</div>
        <div class="options">
          <button class="opt" data-val="menos20">Menos del 20 %</button>
          <button class="opt" data-val="20a40">20 – 40 %</button>
          <button class="opt" data-val="40a60">40 – 60 %</button>
          <button class="opt" data-val="mas60">Más del 60 %</button>
          <button class="opt" data-val="no_se">No lo he medido</button>
        </div>
      </div>
    </div>

    <!-- 11 Sistema gestión -->
    <div class="step" data-step="11" data-type="choice" data-key="sistema_gestion">
      <div>
        <div class="step-num">Pregunta 11 · Herramientas</div>
        <div class="step-q">¿Usas algún sistema para gestionar tu negocio?</div>
        <div class="step-hint">CRM, ERP, hojas de cálculo, apps, etc.</div>
        <div class="options">
          <button class="opt" data-val="erp">Software especializado (ERP/CRM)</button>
          <button class="opt" data-val="excel">Hojas de cálculo (Excel/Sheets)</button>
          <button class="opt" data-val="whatsapp_notas">WhatsApp + notas en papel</button>
          <button class="opt" data-val="memoria">Solo en mi cabeza</button>
          <button class="opt" data-val="ninguno">Ninguno</button>
        </div>
      </div>
    </div>

    <!-- 12 Redes -->
    <div class="step" data-step="12" data-type="choice" data-key="presencia_digital">
      <div>
        <div class="step-num">Pregunta 12 · Digital</div>
        <div class="step-q">¿Tienes presencia digital activa?</div>
        <div class="step-hint">Donde publicas contenido o atienes clientes en línea.</div>
        <div class="options">
          <button class="opt" data-val="web_redes">Sitio web + redes activas</button>
          <button class="opt" data-val="solo_redes">Solo redes sociales activas</button>
          <button class="opt" data-val="redes_abandonadas">Tengo redes pero no las actualizo</button>
          <button class="opt" data-val="ninguna">Sin presencia digital</button>
        </div>
      </div>
    </div>

    <!-- 13 Horas -->
    <div class="step" data-step="13" data-type="choice" data-key="horas_semana">
      <div>
        <div class="step-num">Pregunta 13 · Tiempo</div>
        <div class="step-q">¿Cuántas horas a la semana dedicas a tu negocio?</div>
        <div class="step-hint">Incluyendo operación, ventas y administración.</div>
        <div class="options">
          <button class="opt" data-val="menos20">Menos de 20 horas (proyecto paralelo)</button>
          <button class="opt" data-val="20a40">20 – 40 horas</button>
          <button class="opt" data-val="40a60">40 – 60 horas</button>
          <button class="opt" data-val="mas60">Más de 60 horas (no tengo vida)</button>
        </div>
      </div>
    </div>

    <!-- 14 Socios -->
    <div class="step" data-step="14" data-type="choice" data-key="socios">
      <div>
        <div class="step-num">Pregunta 14 · Estructura</div>
        <div class="step-q">¿Tienes socios o inversionistas?</div>
        <div class="step-hint">Personas con participación formal en tu negocio.</div>
        <div class="options">
          <button class="opt" data-val="no_solo">No, soy el único dueño</button>
          <button class="opt" data-val="socios_activos">Sí, socios activos en la operación</button>
          <button class="opt" data-val="socios_pasivos">Sí, socios/inversionistas silenciosos</button>
          <button class="opt" data-val="familia">Es un negocio familiar</button>
        </div>
      </div>
    </div>

    <!-- 15 Deudas -->
    <div class="step" data-step="15" data-type="choice" data-key="deudas_negocio">
      <div>
        <div class="step-num">Pregunta 15 · Salud financiera</div>
        <div class="step-q">¿Tu negocio tiene deudas?</div>
        <div class="step-hint">Préstamos, créditos o cuentas por pagar pendientes.</div>
        <div class="options">
          <button class="opt" data-val="sin_deudas">Sin deudas</button>
          <button class="opt" data-val="manejables">Deudas manejables, al corriente</button>
          <button class="opt" data-val="presion">Deudas que generan presión</button>
          <button class="opt" data-val="critico">Situación de deuda crítica</button>
        </div>
      </div>
    </div>

    <!-- 16 Escalado -->
    <div class="step" data-step="16" data-type="choice" data-key="intento_escalar">
      <div>
        <div class="step-num">Pregunta 16 · Experiencia</div>
        <div class="step-q">¿Has intentado escalar tu negocio antes?</div>
        <div class="step-hint">Crecer en ventas, equipo o mercado.</div>
        <div class="options">
          <button class="opt" data-val="no_primera">No, esta es la primera vez que lo intento</button>
          <button class="opt" data-val="si_funciono">Sí, y funcionó parcialmente</button>
          <button class="opt" data-val="si_fallo">Sí, pero no funcionó como esperaba</button>
          <button class="opt" data-val="creciendo">Estoy en proceso de escalar ahora</button>
        </div>
      </div>
    </div>

    <!-- 17 Mayor reto -->
    <div class="step" data-step="17" data-type="choice" data-key="reto_principal">
      <div>
        <div class="step-num">Pregunta 17 · Retos</div>
        <div class="step-q">¿Cuál es tu mayor reto hoy?</div>
        <div class="step-hint">El que más te quita el sueño.</div>
        <div class="options">
          <button class="opt" data-val="conseguir_clientes">Conseguir más clientes</button>
          <button class="opt" data-val="cobrar_mejor">Cobrar mejor / subir precios</button>
          <button class="opt" data-val="organizar_equipo">Organizar mi equipo</button>
          <button class="opt" data-val="flujo_caja">Flujo de caja / liquidez</button>
          <button class="opt" data-val="tiempo">No me alcanza el tiempo</button>
          <button class="opt" data-val="competencia">La competencia me come el mercado</button>
          <button class="opt" data-val="marketing">No sé cómo hacer marketing</button>
        </div>
      </div>
    </div>

    <!-- 18 Meta -->
    <div class="step" data-step="18" data-type="text" data-key="meta_12_meses">
      <div>
        <div class="step-num">Pregunta 18 · Visión</div>
        <div class="step-q">¿Cuál es tu meta principal en los próximos 12 meses?</div>
        <div class="step-hint">En números concretos si puedes. Ej: llegar a $100k/mes, abrir sucursal, salir a 2 países.</div>
        <textarea placeholder="Mi meta es..."></textarea>
      </div>
    </div>

    <!-- 19 Bloqueador -->
    <div class="step" data-step="19" data-type="text" data-key="bloqueador">
      <div>
        <div class="step-num">Pregunta 19 · Obstáculos</div>
        <div class="step-q">¿Qué te impide crecer más rápido?</div>
        <div class="step-hint">Sé honesto. Es la pregunta más importante del diagnóstico.</div>
        <textarea placeholder="Lo que me frena es..."></textarea>
      </div>
    </div>

    <!-- 20 WhatsApp -->
    <div class="step" data-step="20" data-type="tel" data-key="whatsapp">
      <div>
        <div class="step-num">Pregunta 20 · Contacto</div>
        <div class="step-q">¿Cuál es tu WhatsApp?</div>
        <div class="step-hint">Para enviarte tu diagnóstico personalizado y acceso a Forja.</div>
        <input type="tel" placeholder="10 dígitos, sin espacios" maxlength="15">
      </div>
    </div>

  </div><!-- /steps-wrap -->

  <!-- Loading -->
  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p id="loading-msg">Analizando tu negocio con IA...<br>Esto tarda unos segundos.</p>
  </div>

  <!-- Results -->
  <div class="results" id="results">
    <div class="results-header">
      <div class="score-ring">
        <svg viewBox="0 0 80 80" width="80" height="80">
          <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,194,224,0.12)" stroke-width="6"/>
          <circle id="score-circle" cx="40" cy="40" r="34" fill="none" stroke="#00c2e0" stroke-width="6"
            stroke-dasharray="213.6" stroke-dashoffset="213.6" stroke-linecap="round" style="transition:stroke-dashoffset 1.2s ease"/>
        </svg>
        <div class="score-num" id="score-num">–</div>
      </div>
      <h2 id="res-titulo">Diagnóstico listo</h2>
      <p id="res-sub">Aquí está el análisis de tu negocio</p>
    </div>
    <div id="diag-body"></div>
    <button onclick="hablarConNathalye()" style="width:100%;padding:14px;background:linear-gradient(135deg,#00c2e0,#0099b5);color:#04090f;font-weight:700;font-size:1rem;border:none;border-radius:14px;cursor:pointer;margin-bottom:.75rem;">
      💬 Hablar con Nathalye — tu coach
    </button>
    <button class="btn-wa" id="btn-wa-result" onclick="compartirWA()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      Compartir diagnóstico por WhatsApp
    </button>
  </div>

  <!-- Nav buttons -->
  <div class="nav" id="nav-btns">
    <button class="btn-back" id="btn-back" onclick="goBack()" style="display:none">← Atrás</button>
    <button class="btn-next" id="btn-next" onclick="goNext()">Continuar →</button>
  </div>

</div><!-- /card -->

<script>
const TOTAL = 20;
let current = 1;
const answers = {};

function getStep(n){ return document.querySelector(`.step[data-step="${n}"]`); }
function getType(n){ return getStep(n)?.dataset.type; }
function getKey(n){ return getStep(n)?.dataset.key; }

function getVal(n){
  const s = getStep(n); if(!s) return '';
  const t = getType(n);
  if(t === 'choice'){
    const sel = s.querySelector('.opt.selected');
    return sel ? sel.dataset.val : '';
  }
  if(t === 'tel'){
    return s.querySelector('input')?.value.trim() || '';
  }
  const inp = s.querySelector('input,textarea');
  return inp ? inp.value.trim() : '';
}

function updateProgress(){
  const pct = Math.round((current / TOTAL) * 100);
  document.getElementById('prog-fill').style.width = pct + '%';
  document.getElementById('prog-label').textContent = `Paso ${current} de ${TOTAL}`;
}

function showStep(n){
  document.querySelectorAll('.step').forEach(s=>s.classList.remove('active'));
  const s = getStep(n);
  if(s) s.classList.add('active');
  document.getElementById('btn-back').style.display = n > 1 ? '' : 'none';
  document.getElementById('btn-next').textContent = n < TOTAL ? 'Continuar →' : 'Ver mi diagnóstico →';
  updateProgress();
  // Focus input
  setTimeout(()=>{
    const inp = s?.querySelector('input,textarea');
    if(inp && getType(n) !== 'choice') inp.focus();
  }, 350);
}

// Choice selection
document.querySelectorAll('.opt').forEach(btn=>{
  btn.addEventListener('click', function(){
    const group = this.closest('.options');
    if(!this.classList.contains('multi')){
      group.querySelectorAll('.opt').forEach(b=>b.classList.remove('selected'));
    }
    this.classList.toggle('selected');
    checkNext();
  });
});

// Enter key for text inputs
document.querySelectorAll('input,textarea').forEach(inp=>{
  inp.addEventListener('input', checkNext);
  inp.addEventListener('keydown', e=>{
    if(e.key==='Enter' && !e.shiftKey && inp.tagName!=='TEXTAREA') goNext();
  });
});

function checkNext(){
  const val = getVal(current);
  const btn = document.getElementById('btn-next');
  btn.disabled = !val;
}

function goNext(){
  const val = getVal(current);
  if(!val) return;
  answers[getKey(current)] = val;
  if(current < TOTAL){
    current++;
    showStep(current);
    checkNext();
  } else {
    submitDiag();
  }
}

function goBack(){
  if(current > 1){ current--; showStep(current); checkNext(); }
}

function showLoading(){
  document.getElementById('steps-wrap').style.display = 'none';
  document.getElementById('nav-btns').style.display = 'none';
  document.getElementById('loading').style.display = 'flex';
  document.querySelector('.progress-wrap').style.opacity = '0.3';
}

function showResults(data){
  document.getElementById('loading').style.display = 'none';
  const res = document.getElementById('results');
  res.style.display = 'flex';

  // Score
  const score = data.score || 50;
  document.getElementById('score-num').textContent = score;
  document.getElementById('res-titulo').textContent = data.titulo || 'Diagnóstico listo';
  document.getElementById('res-sub').textContent = `Hola ${answers.nombre} · ${answers.negocio}`;
  setTimeout(()=>{
    const circunf = 2 * Math.PI * 34;
    const offset = circunf - (score / 100) * circunf;
    document.getElementById('score-circle').style.strokeDashoffset = offset;
  }, 100);

  // Body
  const body = document.getElementById('diag-body');
  body.innerHTML = '';
  (data.secciones || []).forEach(sec=>{
    const div = document.createElement('div');
    div.className = 'diag-section';
    div.innerHTML = `<h3>${sec.titulo}</h3><p>${sec.contenido}</p>`;
    body.appendChild(div);
  });
}

async function submitDiag(){
  showLoading();
  const msgs = [
    'Analizando tu negocio con IA...',
    'Calculando tu score empresarial...',
    'Generando recomendaciones personalizadas...',
  ];
  let mi = 0;
  const msgEl = document.getElementById('loading-msg');
  const msgInt = setInterval(()=>{ msgEl.innerHTML = msgs[++mi % msgs.length] + '<br><span style="opacity:.5;font-size:.8rem">Solo unos segundos más</span>'; }, 2500);

  try {
    const r = await fetch('/forja/registro', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(answers)
    });
    const data = await r.json();
    clearInterval(msgInt);
    if(data.diagnostico) showResults(data.diagnostico);
    else showResults({score:60, titulo:'Registro completado', secciones:[
      {titulo:'¡Gracias!', contenido:`${answers.nombre}, recibimos tu diagnóstico. Te contactamos por WhatsApp en menos de 24 horas con tu plan de acción personalizado.`}
    ]});
  } catch(e){
    clearInterval(msgInt);
    showResults({score:60, titulo:'Registro recibido', secciones:[
      {titulo:'Próximo paso', contenido:`${answers.nombre}, te contactaremos por WhatsApp al ${answers.whatsapp} con tu acceso a Forja y tu diagnóstico completo.`}
    ]});
  }
}

function compartirWA(){
  const txt = encodeURIComponent(`Acabo de hacer el diagnóstico de mi negocio "${answers.negocio}" en Forja by NEXUS. ¿Lo quieres hacer tú también? ${window.location.href}`);
  window.open(`https://wa.me/?text=${txt}`, '_blank');
}

function hablarConNathalye(){
  const p = new URLSearchParams({
    nombre: answers.nombre||'',
    negocio: answers.negocio||answers.nombre||'',
    giro: answers.giro||'',
    reto: answers.reto_principal||''
  });
  window.location.href = '/forja/chat?'+p.toString();
}

// Init
showStep(1);
checkNext();
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post("/forja/registro")
async def registro_forja(request: Request):
    """Guarda registro de emprendedor en Forja y genera diagnóstico determinista (0 tokens IA)."""
    import json as _json, pathlib, datetime
    data = await request.json()
    data["fecha"] = datetime.datetime.now().isoformat()

    # Guardar registro
    ruta = pathlib.Path("data/forja_registros.json")
    ruta.parent.mkdir(exist_ok=True)
    registros = _json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []
    registros.append(data)
    ruta.write_text(_json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── DIAGNÓSTICO DETERMINISTA — cero tokens ─────────────────────────────
    nombre  = data.get("nombre", "Emprendedor")
    negocio = data.get("negocio", "tu negocio")
    giro    = data.get("giro", "")

    # — Score (máx 100) —
    score = 20  # base
    score += {"0":0,"menos20k":8,"20a50k":16,"50a150k":26,"150a500k":36,"mas500k":45}.get(data.get("facturacion_mensual",""),0)
    score += {"negativo":-8,"0a10":0,"10a25":8,"25a40":14,"mas40":18,"no_se":0}.get(data.get("margen_ganancia",""),0)
    score += {"si_documentado":10,"si_informal":5,"improvisado":2,"no":0}.get(data.get("proceso_venta",""),0)
    score += {"erp":8,"excel":5,"whatsapp_notas":2,"memoria":0,"ninguno":0}.get(data.get("sistema_gestion",""),0)
    score += {"web_redes":8,"solo_redes":5,"redes_abandonadas":1,"ninguna":0}.get(data.get("presencia_digital",""),0)
    score += {"menos20":0,"20a40":4,"40a60":8,"mas60":12,"no_se":0}.get(data.get("retencion_clientes",""),0)
    score += {"sin_deudas":5,"manejables":2,"presion":0,"critico":-8}.get(data.get("deudas_negocio",""),0)
    score += {"idea":0,"menos1":2,"1a3":4,"3a5":7,"mas5":10}.get(data.get("tiempo_operacion",""),0)
    score = max(8, min(score, 96))

    # — Título según score —
    if score >= 75:   titulo = f"{nombre}: negocio sólido con potencial real"
    elif score >= 55: titulo = f"{nombre}: buen camino, hay puntos clave a ajustar"
    elif score >= 35: titulo = f"{nombre}: base hay, necesitas estructura"
    else:             titulo = f"{nombre}: etapa inicial — el momento es ahora"

    # — Fortalezas según respuestas —
    fortalezas = []
    if data.get("tiempo_operacion") in ("3a5","mas5"):
        fortalezas.append(f"Llevas años operando en {giro or 'tu sector'}: conoces el mercado mejor que la mayoría.")
    if data.get("retencion_clientes") in ("40a60","mas60"):
        fortalezas.append("Tu retención de clientes es alta — tienes algo que la gente valora y repite.")
    if data.get("proceso_venta") in ("si_documentado","si_informal"):
        fortalezas.append("Ya tienes un proceso de venta definido, eso te pone adelante del 70% de los emprendedores.")
    if data.get("captacion_clientes") == "referidos":
        fortalezas.append("Tus clientes llegan por recomendación — señal de que tu producto/servicio genera confianza real.")
    if data.get("margen_ganancia") in ("25a40","mas40"):
        fortalezas.append("Tu margen de ganancia es saludable — tienes espacio para invertir en crecimiento.")
    if data.get("presencia_digital") == "web_redes":
        fortalezas.append("Presencia digital activa: ya tienes canal de atracción de clientes funcionando.")
    if not fortalezas:
        fortalezas.append(f"Estás tomando acción — registrarte en Forja ya te pone por encima del emprendedor promedio que solo piensa.")
        if giro: fortalezas.append(f"Tienes claro tu giro ({giro}), eso es el primer paso.")

    # — Oportunidad crítica según reto + contexto —
    reto = data.get("reto_principal","")
    gestion = data.get("sistema_gestion","")
    captacion = data.get("captacion_clientes","")
    oportunidad_map = {
        "conseguir_clientes": "No tienes un sistema de captación predecible. Depender de que 'lleguen solos' es el techo más común en PyMEs. Necesitas un proceso repetible: contenido + seguimiento + oferta clara.",
        "cobrar_mejor":       "Estás cobrando por debajo de tu valor. El precio bajo no es estrategia, es miedo. La solución no es competir en precio sino demostrar por qué vales más.",
        "organizar_equipo":   "Sin procesos documentados, tú eres el cuello de botella. Cada tarea que solo tú puedes hacer es un freno al crecimiento.",
        "flujo_caja":         "El flujo de caja se rompe cuando vendes pero no cobras a tiempo, o cuando gastas antes de que entre. Necesitas un control simple de entradas y salidas por semana.",
        "tiempo":             "Trabajas para el negocio en lugar de trabajar en él. Si el negocio para cuando tú paras, aún no tienes un negocio — tienes un empleo propio.",
        "competencia":        "La diferenciación es la única salida a la guerra de precios. Necesitas un ángulo único que la competencia no pueda copiar fácilmente.",
        "marketing":          "Sin marketing consistente, las ventas son aleatorias. La buena noticia: no necesitas presupuesto grande, necesitas un sistema simple y repetible.",
    }
    oportunidad = oportunidad_map.get(reto, "Identificar el cuello de botella principal de tu operación es el primer paso. Con Forja lo mapeamos juntos en tu primera sesión.")

    # — Acción inmediata según captación + sistema —
    accion_map = {
        ("referidos","memoria"):     "Esta semana: manda un mensaje a tus 5 mejores clientes pidiéndoles que te refieran a alguien. Ofréceles algo simple: descuento, prioridad o gracias en público.",
        ("redes","ninguno"):         "Esta semana: crea una hoja en Excel (o Google Sheets) con columna: Nombre / WhatsApp / Interés / Seguimiento. Registra a los que te contactan por redes.",
        ("whatsapp_notas","memoria"):"Esta semana: guarda todos tus contactos activos en una lista de difusión de WhatsApp. Manda un mensaje recordándoles que existes y qué ofreces.",
        ("sin_sistema","ninguno"):   "Esta semana: define tu oferta en 1 oración: 'Ayudo a [quién] a [resultado] en [tiempo].' Ponla en tu bio de WhatsApp ahora mismo.",
    }
    accion = accion_map.get((captacion, gestion)) or accion_map.get((captacion, "ninguno")) or accion_map.get(("sin_sistema","ninguno"))
    if not accion:
        accion = f"Esta semana: contacta a tus 3 mejores clientes, pregúntales qué es lo que más valoran de {negocio or 'tu negocio'}. Esa respuesta te dirá exactamente qué comunicar para atraer más como ellos."

    # — Potencial a 12 meses —
    facturacion = data.get("facturacion_mensual","")
    potencial_map = {
        "0":       f"Con la hoja de ruta correcta, {negocio} puede generar sus primeros ingresos reales en 60–90 días.",
        "menos20k":f"{negocio} puede llegar a $50,000/mes con captación consistente y precio bien posicionado.",
        "20a50k":  f"Con proceso de venta y retención activa, {negocio} puede cruzar los $100k/mes en 12 meses.",
        "50a150k": f"Optimizando márgenes y equipo, {negocio} puede duplicar su facturación sin duplicar el trabajo.",
        "150a500k":f"{negocio} está listo para escalar: automatización y delegación son la clave del siguiente nivel.",
        "mas500k": f"{negocio} ya tiene escala — el enfoque ahora es sistema, equipo y expansión de mercado.",
    }
    potencial = potencial_map.get(facturacion, f"El potencial de {negocio} depende de la velocidad con que implementes las mejoras identificadas aquí.")

    diagnostico = {
        "score": score,
        "titulo": titulo,
        "secciones": [
            {"titulo": "FORTALEZAS",              "contenido": " ".join(fortalezas[:2])},
            {"titulo": "OPORTUNIDAD CRÍTICA",     "contenido": oportunidad},
            {"titulo": "ACCIÓN ESTA SEMANA",      "contenido": accion},
            {"titulo": "POTENCIAL A 12 MESES",    "contenido": potencial},
        ]
    }

    return {"ok": True, "total": len(registros), "diagnostico": diagnostico, "uid": data.get("uid", "")}


@app.api_route("/forja/api/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def forja_proxy(path: str, request: Request):
    """Proxy al motor_forja en puerto 8020."""
    import httpx as _httpx
    url = f"http://localhost:8020/{path}"
    try:
        body = await request.body()
        async with _httpx.AsyncClient(timeout=30) as c:
            r = await c.request(method=request.method, url=url, content=body,
                                headers={"Content-Type":"application/json"},
                                params=dict(request.query_params))
            return JSONResponse(content=r.json(), status_code=r.status_code)
    except Exception as e:
        return JSONResponse({"ok": False, "respuesta": "Nathalye no está disponible ahora.", "error": str(e)[:80]}, status_code=503)


@app.get("/forja/chat", response_class=HTMLResponse)
async def forja_chat():
    """Chat con Nathalye — coach de emprendedores Forja by NEXUS."""
    html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Nathalye — Forja by NEXUS</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
:root{--bg:#04090f;--surface:#0a1628;--border:rgba(0,194,224,.18);--accent:#00c2e0;--accent2:#0099b5;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#fff;height:100dvh;display:flex;flex-direction:column;}
#header{display:flex;align-items:center;gap:.75rem;padding:.85rem 1rem;background:var(--surface);border-bottom:1px solid var(--border);flex-shrink:0;}
.av{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1rem;color:#04090f;}
.hinfo{flex:1;}
.hname{font-weight:700;font-size:.95rem;}
.hstatus{font-size:.72rem;color:var(--accent);opacity:.8;}
#messages{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.75rem;}
.msg{display:flex;gap:.5rem;max-width:88%;}
.msg.user{align-self:flex-end;flex-direction:row-reverse;}
.bubble{padding:.7rem .95rem;border-radius:18px;font-size:.9rem;line-height:1.5;white-space:pre-wrap;}
.msg.bot .bubble{background:var(--surface);border:1px solid var(--border);border-bottom-left-radius:4px;}
.msg.user .bubble{background:var(--accent);color:#04090f;border-bottom-right-radius:4px;}
.mtime{font-size:.65rem;color:rgba(255,255,255,.3);align-self:flex-end;padding-bottom:.2rem;}
.typing span{display:inline-block;width:7px;height:7px;background:var(--accent);border-radius:50%;margin:0 2px;animation:blink 1.2s infinite;}
.typing span:nth-child(2){animation-delay:.2s;} .typing span:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%,80%,100%{opacity:.2;}40%{opacity:1;}}
#input-wrap{display:flex;gap:.5rem;padding:.75rem 1rem;background:var(--surface);border-top:1px solid var(--border);flex-shrink:0;}
textarea{flex:1;background:#0d1f35;border:1px solid var(--border);border-radius:12px;padding:.65rem .9rem;color:#fff;font-family:inherit;font-size:.9rem;resize:none;min-height:42px;max-height:100px;outline:none;}
textarea:focus{border-color:var(--accent);}
button#sbtn{background:var(--accent);color:#04090f;border:none;border-radius:12px;width:42px;height:42px;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
#ctx-bar{font-size:.72rem;color:rgba(255,255,255,.4);padding:.3rem 1rem;background:var(--surface);border-bottom:1px solid var(--border);flex-shrink:0;display:none;}
</style>
</head>
<body>
<div id="header">
  <div class="av">N</div>
  <div class="hinfo">
    <div class="hname">Nathalye</div>
    <div class="hstatus">● Coach Forja · online</div>
  </div>
</div>
<div id="ctx-bar" id="ctx-bar"></div>
<div id="messages"></div>
<div id="input-wrap">
  <textarea id="txt" rows="1" placeholder="Cuéntame tu negocio o tu reto..." onkeydown="tecla(event)" oninput="resize(this)"></textarea>
  <button id="sbtn" onclick="enviar()">↑</button>
</div>
<script>
const S = (() => {
  try { return JSON.parse(localStorage.getItem('nxf')||'{}'); } catch(e){return {};}
})();
let historial = [];

function save(){ localStorage.setItem('nxf', JSON.stringify(S)); }

function hora(){ return new Date().toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit'}); }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>'); }
function scroll(){ const b=document.getElementById('messages'); b.scrollTop=b.scrollHeight; }
function resize(el){ el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,100)+'px'; }

function addMsg(txt, rol){
  const box=document.getElementById('messages');
  const d=document.createElement('div');
  d.className='msg '+rol;
  d.innerHTML=`<div class="bubble">${esc(txt)}</div><div class="mtime">${hora()}</div>`;
  box.appendChild(d); scroll();
}
function showTyping(){
  const box=document.getElementById('messages');
  const d=document.createElement('div'); d.id='ty'; d.className='msg bot';
  d.innerHTML='<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
  box.appendChild(d); scroll();
}
function hideTyping(){ const t=document.getElementById('ty'); if(t) t.remove(); }

async function enviar(){
  const el=document.getElementById('txt');
  const txt=el.value.trim(); if(!txt) return;
  el.value=''; el.style.height='auto';
  document.getElementById('sbtn').disabled=true;
  addMsg(txt,'user');
  historial.push({role:'user',content:txt});
  showTyping();
  try{
    const contexto = S.negocio ? `Negocio: ${S.negocio}. Giro: ${S.giro||''}. Reto: ${S.reto||''}.` : '';
    const r = await fetch('/forja/api/execute',{
      method:'POST',
      headers:{'Content-Type':'application/json','ngrok-skip-browser-warning':'true'},
      body: JSON.stringify({action:'process_query', data:{message:txt, contexto, historial: historial.slice(-6)}})
    });
    const d = await r.json();
    hideTyping();
    const resp = d.respuesta || d.resultado?.mensaje || 'Sin respuesta.';
    addMsg(resp,'bot');
    historial.push({role:'assistant',content:resp});
    if(historial.length>20) historial=historial.slice(-20);
  }catch(e){hideTyping();addMsg('Sin conexión ahora mismo.','bot');}
  document.getElementById('sbtn').disabled=false;
  document.getElementById('txt').focus();
}

function tecla(e){ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();enviar();} }

// Bienvenida
const params = new URLSearchParams(location.search);
const nombre = params.get('nombre') || S.nombre || '';
const negocio = params.get('negocio') || S.negocio || '';
const giro    = params.get('giro') || S.giro || '';
const reto    = params.get('reto') || S.reto || '';

if(nombre){ S.nombre=nombre; S.negocio=negocio; S.giro=giro; S.reto=reto; save(); }

if(S.negocio){
  const bar=document.getElementById('ctx-bar');
  bar.textContent=`📋 ${S.negocio}${S.giro?' · '+S.giro:''}`;
  bar.style.display='block';
}

const bienvenida = nombre
  ? `¡Hola ${nombre}! 👋 Ya vi tu diagnóstico de "${negocio}". ¿Por dónde quieres empezar? Cuéntame tu reto más urgente.`
  : '¡Hola! Soy Nathalye, tu coach de negocios en Forja. ¿Cómo se llama tu negocio y cuál es tu reto más grande ahorita?';
setTimeout(()=>addMsg(bienvenida,'bot'),400);
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


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
    # Convertir session_id string a int estable para la DB
    session_int = abs(hash(session_id)) % 2147483647
    motor_utilizado = None
    resultado_motor = None
    proveedor_usado = "ninguno"

    # a) Guardar mensaje del usuario
    try:
        await database.save_message(session_id=session_int, role="user", content=mensaje)
    except Exception as exc:
        logger.warning("No se pudo guardar mensaje del usuario: %s", exc)

    # b) Obtener últimos 20 mensajes de contexto
    historial = []
    try:
        historial = await database.get_session_messages(session_int, limit=6)
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
        # motor_editor puede tardar hasta 90s generando imagen con APIs externas
        _timeout = 90 if motor_key == "motor_editor" else 30
        resultado_motor = await delegar_a_motor(motor_key, "process_query",
            {"message": mensaje, "session_id": session_id, "personality": personalidad_key},
            tiempo_maximo=_timeout)

        # Motor falló o no disponible — reportar exactamente eso, sin IA
        if not resultado_motor.get("exito"):
            msj_err = resultado_motor.get("mensaje_friendly",
                                          f"El motor '{info_motor['nombre']}' no está disponible ahora.")
            try:
                await database.save_message(session_id=session_int, role="assistant", content=msj_err)
            except Exception:
                pass
            return JSONResponse(content={"response": msj_err, "personality": personalidad_key,
                                         "session_id": session_id, "motor_used": motor_key,
                                         "ai_provider": "ninguno (motor no disponible)"})

        # Motor respondió — si tiene campo "respuesta" o "ok", entregarlo DIRECTO sin pasar por IA
        datos_motor = resultado_motor.get("datos", {})
        respuesta_directa = datos_motor.get("respuesta") or datos_motor.get("response")
        if respuesta_directa:
            try:
                await database.save_message(session_id=session_int, role="assistant",
                                            content=respuesta_directa)
            except Exception:
                pass
            payload_directo = {"response": respuesta_directa,
                               "personality": personalidad_key,
                               "session_id": session_id,
                               "motor_used": motor_key,
                               "ai_provider": "motor_directo"}
            # Propagar imagen si el motor la generó/editó
            if datos_motor.get("imagen_b64"):
                payload_directo["imagen_b64"] = datos_motor["imagen_b64"]
            return JSONResponse(content=payload_directo)

    # f) Construir prompt para la IA
    # Intentar cargar prompt maestro si no está en memoria
    prompt_zai = _PROMPT_MAESTRO or _leer_prompt_maestro()
    prompt_sistema = prompt_zai if prompt_zai else PERSONALIDADES[personalidad_key]["prompt"]
    logger.info("PROMPT activo: %s", "PROMPT_ZAI.md" if prompt_zai else f"PERSONALIDADES[{personalidad_key}]")
    if resultado_motor and resultado_motor.get("exito"):
        datos_brutos = json.dumps(resultado_motor.get("datos", {}), ensure_ascii=False, indent=2)
        prompt_sistema += (
            f"\n\n[Resultado del motor {motor_utilizado}]\n"
            f"El motor especializado devolvió:\n{datos_brutos}\n[/Resultado del motor]\n\n"
            "Instrucciones: Presenta esta información al usuario de forma clara, "
            "natural y bien organizada. Traduce términos técnicos si es necesario.")
    if contexto_memoria:
        prompt_sistema += contexto_memoria

    # Formatear historial para la IA (DB usa role/content, no rol/contenido)
    mensajes_ia = [{"role": "system", "content": prompt_sistema}]
    for msg in historial:
        rol = msg.get("role", msg.get("rol", "user"))
        contenido = msg.get("content", msg.get("contenido", ""))
        if rol in ("user", "assistant") and contenido:
            mensajes_ia.append({"role": rol, "content": contenido})

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
        await database.save_message(session_id=session_int, role="assistant", content=respuesta_ia)
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


@app.post("/motors/refresh")
async def refrescar_motores():
    """Re-verifica el estado de todos los motores (útil después de arrancar los motores)."""
    global motor_estado
    resultados = {}
    for nombre_motor, info_motor in MOTORES.items():
        estado = await verificar_motor(info_motor["puerto"], info_motor["nombre"])
        motor_estado[nombre_motor] = estado
        resultados[nombre_motor] = {"activo": estado["activo"], "puerto": info_motor["puerto"]}
    activos = sum(1 for v in resultados.values() if v["activo"])
    return {"ok": True, "motores_activos": activos, "total": len(MOTORES), "detalle": resultados}


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


@app.post("/api/session")
@app.get("/api/session")
async def api_session(request: Request):
    """Crea o verifica sesión."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id, "ok": True}


@app.get("/api/user")
async def api_user():
    """Info del usuario/owner del sistema."""
    return {"nombre": "Anuar", "rol": "admin", "ok": True}


@app.get("/api/stats")
async def api_stats():
    """Estadísticas rápidas del sistema."""
    motores_activos = sum(1 for v in motor_estado.values() if v.get("activo", False))
    return {
        "motores_activos": motores_activos,
        "motores_total": len(MOTORES),
        "proveedor_ia": ai_cliente.proveedor_actual() if ai_cliente else "ninguno",
        "ok": True
    }


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
#  UPLOAD DESDE CHAT (drag-drop directo)
# ══════════════════════════════════════════════════════════════

@app.post("/chat/upload")
async def chat_upload(
    file:        UploadFile = File(...),
    personality: str        = Form("nexus"),
    session_id:  str        = Form(""),
):
    """
    Recibe archivos arrastrados al chat.
    - Imagen con >60% blanco (dibujo lineal) → engrosa líneas automáticamente
    - Imagen normal → pide instrucción
    - Otro archivo  → confirma recepción
    """
    import tempfile, shutil, numpy as _np
    from pathlib import Path as _P
    from PIL import Image as _PILimg, ImageFilter as _IFilter

    OUTPUT_DIR = _P("C:/NEXUS_v3_NEW/output")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sufijo      = _P(file.filename).suffix.lower() if file.filename else ".bin"
    nombre_base = _P(file.filename).stem           if file.filename else "archivo"
    IMAGENES    = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

    # Guardar temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        shutil.copyfileobj(file.file, tmp)
        ruta_tmp = _P(tmp.name)

    if sufijo not in IMAGENES:
        return JSONResponse({"response": f"Archivo `{file.filename}` recibido. ¿Qué quieres hacer con él?",
                             "motor": "archivos", "personality": personality})

    try:
        img  = _PILimg.open(ruta_tmp)
        arr  = _np.array(img.convert("L"))
        pct_blanco = float(_np.sum(arr > 200)) / arr.size * 100

        if pct_blanco < 60:
            return JSONResponse({"response": f"Imagen recibida ({round(pct_blanco)}% blanco). "
                                             "Di **crea tarjeta de presentación**, **engrosa las líneas**, "
                                             "**convierte a PDF**, **quita el fondo**, etc.",
                                 "motor": "archivos", "personality": personality})

        # ── Dibujo lineal detectado → engrosar automáticamente ──────
        # Detectar y recortar filas de UI (ads, toolbars) si es screenshot
        h, w = arr.shape
        crop_top = 0
        for i in range(min(300, h - 1)):
            if arr[i].mean() > 245 and arr[i + 1].mean() > 245:
                crop_top = i
                break
        crop_bottom = h
        for i in range(h - 1, max(h - 300, 0), -1):
            if arr[i].mean() > 245:
                crop_bottom = i
                break

        img_crop = img.crop((0, crop_top, w, crop_bottom))
        arr2     = _np.where(_np.array(img_crop.convert("L")) < 200, 0, 255).astype("uint8")
        clean    = _PILimg.fromarray(arr2, mode="L")
        thick    = clean.filter(_IFilter.MinFilter(3)).filter(_IFilter.MinFilter(3))

        ruta_salida = OUTPUT_DIR / f"{nombre_base}_lineas_gruesas.png"
        thick.save(str(ruta_salida), "PNG")

        url = f"/static/output/{ruta_salida.name}"
        kb  = round(ruta_salida.stat().st_size / 1024, 1)
        return JSONResponse({
            "response":    f"Dibujo lineal detectado ({round(pct_blanco)}% blanco). "
                           f"Líneas engrosadas automáticamente — {kb} KB.",
            "url":         url,
            "nombre":      ruta_salida.name,
            "kb":          kb,
            "motor":       "Pillow/engrosar_auto",
            "personality": personality,
        })

    except Exception as e:
        return JSONResponse({"response": f"No pude procesar la imagen: {e}",
                             "motor": "error", "personality": personality})


# ══════════════════════════════════════════════════════════════
#  CONVERTIDOR DE ARCHIVOS
# ══════════════════════════════════════════════════════════════

@app.post("/api/convert")
async def convertir_archivo(
    file: UploadFile = File(...),
    format: str = Form("pdf"),
    dpi: int = Form(300),
    mejorar: bool = Form(True),
    vectorizar: bool = Form(False),
    quitar_fondo: bool = Form(False),
    sublimacion: bool = Form(False),
    efecto: str = Form(""),
):
    """
    Convierte y mejora archivos usando CorelDRAW como motor principal.
    Fallback automático: Pillow / Inkscape / PyMuPDF / ezdxf.
    DPI recomendado: 300 impresión/sublimación, 150 pantalla, 72 web.
    mejorar=True     → nitidez + contraste automático
    vectorizar=True  → PowerTRACE bitmap→vector (solo CorelDRAW)
    quitar_fondo=True → elimina fondo blanco/gris → transparencia PNG
    """
    from pathlib import Path as _P
    import tempfile, shutil

    OUTPUT_DIR = _P("C:/nexus/MERCH_OUTPUT")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sufijo = _P(file.filename).suffix.lower() if file.filename else ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        shutil.copyfileobj(file.file, tmp)
        ruta_origen = _P(tmp.name)

    motor_usado = "fallback"

    try:
        nombre_base = _P(file.filename).stem if file.filename else "archivo"
        formato     = format.lower().strip(".")
        ext_origen  = sufijo.lstrip(".")

        if formato == "jpeg": formato = "jpg"
        if ext_origen == "jpeg": ext_origen = "jpg"

        ruta_salida = OUTPUT_DIR / f"{nombre_base}.{formato}"
        IMAGENES = {"png", "jpg", "bmp", "gif", "tiff", "webp"}

        # ══════════════════════════════════════════════════════════
        # EFECTOS ESPECIALES — se aplican antes que todo, devuelven
        # siempre PNG con fondo transparente (listo para sublimación,
        # estampado, corte láser, etc.)
        # ══════════════════════════════════════════════════════════
        efecto = efecto.strip().lower()
        IMAGENES = {"png", "jpg", "bmp", "gif", "tiff", "webp"}

        if efecto in ("cartoon", "lineal") and sufijo.lstrip(".") in IMAGENES:
            import cv2, numpy as np
            from PIL import Image as _PILimg

            img_cv = cv2.imread(str(ruta_origen))
            if img_cv is None:
                raise HTTPException(400, "No se pudo leer la imagen para efecto especial")

            if efecto == "cartoon":
                # ── Cartoon estilo Disney ────────────────────────────
                # 1. Suavizar colores preservando bordes (bilateral filter)
                suave = img_cv.copy()
                for _ in range(6):
                    suave = cv2.bilateralFilter(suave, 9, 80, 80)
                # 2. Saturación estilo cel-shading
                hsv = cv2.cvtColor(suave, cv2.COLOR_BGR2HSV).astype(np.float32)
                hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.6, 0, 255)
                hsv[:,:,2] = np.clip(hsv[:,:,2] * 1.1, 0, 255)
                suave = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
                # 3. Bordes negros tipo cartoon
                gris  = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                gris  = cv2.medianBlur(gris, 5)
                bordes = cv2.adaptiveThreshold(
                    gris, 255,
                    cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
                    blockSize=9, C=9
                )
                # 4. Combinar colores + bordes
                bordes_3c = cv2.cvtColor(bordes, cv2.COLOR_GRAY2BGR)
                resultado_cv = cv2.bitwise_and(suave, bordes_3c)
                efecto_nombre = "cartoon"

            else:  # lineal
                # ── Dibujo lineal (lápiz) ────────────────────────────
                gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                inv  = 255 - gris
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                # Dodge blend → líneas negras sobre blanco
                sketch = cv2.divide(gris, 255 - blur, scale=256)
                # Reforzar contraste del sketch
                sketch = cv2.equalizeHist(sketch)
                resultado_cv = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
                efecto_nombre = "lineal"

            # ── Quitar fondo blanco/gris → canal alpha ───────────────
            resultado_rgb = cv2.cvtColor(resultado_cv, cv2.COLOR_BGR2RGB)
            pil_rgba = _PILimg.fromarray(resultado_rgb).convert("RGBA")
            datos = np.array(pil_rgba)
            r, g, b = datos[:,:,0], datos[:,:,1], datos[:,:,2]
            fondo_mask = (r > 230) & (g > 230) & (b > 230) & \
                         (np.abs(r.astype(int)-g.astype(int)) < 25) & \
                         (np.abs(g.astype(int)-b.astype(int)) < 25)
            datos[fondo_mask, 3] = 0
            resultado_final = _PILimg.fromarray(datos)

            # Upscale a DPI objetivo
            w_orig, h_orig = resultado_final.size
            src_dpi = 72
            try:
                inf = _PILimg.open(ruta_origen).info.get("dpi")
                if inf and isinstance(inf, (tuple,list)):
                    src_dpi = max(int(inf[0]), 1) or 72
            except Exception:
                pass
            if dpi > src_dpi:
                factor = dpi / src_dpi
                nw = min(int(w_orig * factor), 8000)
                nh = min(int(h_orig * factor), 8000)
                if nw > w_orig:
                    resultado_final = resultado_final.resize((nw, nh), _PILimg.LANCZOS)

            ruta_salida = OUTPUT_DIR / f"{nombre_base}_{efecto_nombre}.png"
            resultado_final.save(str(ruta_salida), "PNG", dpi=(dpi, dpi))

            return {
                "ok": True, "success": True,
                "url":    f"/static/output/{ruta_salida.name}",
                "nombre": ruta_salida.name,
                "path":   str(ruta_salida),
                "formato": "png",
                "dpi":    dpi,
                "kb":     round(ruta_salida.stat().st_size / 1024, 1),
                "motor":  f"OpenCV/{efecto_nombre}+sin_fondo",
            }

        # ══════════════════════════════════════════════════════════
        # EFECTO: ENGROSAR LÍNEAS
        # Para dibujos lineales con trazos delgados.
        # Usa dilation morfológica (MinFilter) — sin dependencias extra.
        # ══════════════════════════════════════════════════════════
        if efecto == "engrosar_lineas" and sufijo.lstrip(".") in IMAGENES:
            from PIL import Image as _PILimg, ImageFilter as _IFilter
            import numpy as _np

            img_src = _PILimg.open(ruta_origen)
            w_src, h_src = img_src.size

            # Detectar y recortar bordes de UI automáticamente:
            # elimina filas superiores/inferiores con promedio < 245 (ads, toolbars)
            arr_full = _np.array(img_src.convert("L"))
            crop_top = 0
            for _i in range(0, min(300, h_src)):
                row_mean = arr_full[_i].mean()
                if row_mean > 245:
                    crop_top = _i
                    break
            crop_bottom = h_src
            for _i in range(h_src - 1, max(h_src - 300, 0), -1):
                if arr_full[_i].mean() > 245:
                    crop_bottom = _i
                    break

            img_crop = img_src.crop((0, crop_top, w_src, crop_bottom))

            # Umbral: blanco puro / negro puro
            arr = _np.array(img_crop.convert("L"))
            arr = _np.where(arr < 200, 0, 255).astype("uint8")
            clean = _PILimg.fromarray(arr, mode="L")

            # Engrosar: 2 pasadas MinFilter size=3
            thick = clean.filter(_IFilter.MinFilter(3))
            thick = thick.filter(_IFilter.MinFilter(3))

            ruta_salida = OUTPUT_DIR / f"{nombre_base}_lineas_gruesas.png"
            thick.save(str(ruta_salida), "PNG", dpi=(dpi, dpi))

            return {
                "ok": True, "success": True,
                "url":    f"/static/output/{ruta_salida.name}",
                "nombre": ruta_salida.name,
                "path":   str(ruta_salida),
                "formato": "png",
                "dpi":    dpi,
                "kb":     round(ruta_salida.stat().st_size / 1024, 1),
                "motor":  "Pillow/engrosar_lineas",
            }

        # ══════════════════════════════════════════════════════════
        # TARJETA DE PRESENTACIÓN — vectoriza + genera SVG/PNG/PDF
        # ══════════════════════════════════════════════════════════
        if efecto == "tarjeta_presentacion" and sufijo.lstrip(".") in IMAGENES:
            import vtracer as _vt
            from PIL import Image as _PILimg, ImageFilter as _IFilter, ImageEnhance as _IEnh
            import zipfile as _zf

            # 1. Leer fuente
            img_src = _PILimg.open(ruta_origen).convert("RGB")

            # 2. Vectorizar: escalar 4x primero para dar más detalle al trazado
            w4, h4 = img_src.width * 4, img_src.height * 4
            img4x  = img_src.resize((w4, h4), _PILimg.LANCZOS)
            tmp_4x = OUTPUT_DIR / f"{nombre_base}_4x_tmp.png"
            img4x.save(str(tmp_4x))

            svg_path = OUTPUT_DIR / f"{nombre_base}_VECTOR.svg"
            _vt.convert_image_to_svg_py(
                str(tmp_4x), str(svg_path),
                colormode="color", hierarchical="stacked", mode="spline",
                filter_speckle=4, color_precision=8, layer_difference=16,
                corner_threshold=60, length_threshold=4.0,
                max_iterations=10, splice_threshold=45, path_precision=8,
            )
            tmp_4x.unlink(missing_ok=True)

            # 3. Raster de alta calidad: 9.6cm × 5.6cm @ 300 DPI (con 3mm sangría)
            W_CARD, H_CARD = 1134, 661
            img_rgba = _PILimg.open(ruta_origen).convert("RGBA")

            # Logo al 85% del canvas manteniendo proporción, centrado
            logo_w = int(W_CARD * 0.85)
            logo_h = int(H_CARD * 0.85)
            img_rgba.thumbnail((logo_w, logo_h), _PILimg.LANCZOS)
            logo_w, logo_h = img_rgba.size

            # Sharpening y contraste
            img_rgba = img_rgba.filter(_IFilter.UnsharpMask(radius=2, percent=200, threshold=3))
            img_rgba = _IEnh.Sharpness(img_rgba).enhance(1.8)
            img_rgba = _IEnh.Contrast(img_rgba).enhance(1.15)

            # Canvas blanco con logo centrado (soporta transparencia)
            canvas = _PILimg.new("RGBA", (W_CARD, H_CARD), (255, 255, 255, 255))
            x_off  = (W_CARD - logo_w) // 2
            y_off  = (H_CARD - logo_h) // 2
            canvas.paste(img_rgba, (x_off, y_off), img_rgba)
            canvas = canvas.convert("RGB")

            png_path = OUTPUT_DIR / f"{nombre_base}_tarjeta_PREVIEW.png"
            pdf_path = OUTPUT_DIR / f"{nombre_base}_tarjeta_IMPRIMIR.pdf"
            canvas.save(str(png_path), "PNG", dpi=(300, 300))

            # PDF con fpdf2 (más limpio que PIL nativo)
            try:
                from fpdf import FPDF as _FPDF
                _pdf = _FPDF(unit="mm", format=(96, 56))
                _pdf.add_page()
                _pdf.image(str(png_path), x=0, y=0, w=96, h=56)
                _pdf.output(str(pdf_path))
            except Exception:
                canvas.save(str(pdf_path), "PDF", resolution=300)

            return {
                "ok": True, "success": True,
                "mensaje": "Tarjeta lista — SVG editable + PNG + PDF para maquilar",
                "urls": [
                    {"url": f"/static/output/{svg_path.name}", "nombre": svg_path.name},
                    {"url": f"/static/output/{png_path.name}", "nombre": png_path.name},
                    {"url": f"/static/output/{pdf_path.name}", "nombre": pdf_path.name},
                ],
                "motor": "vtracer+Pillow/tarjeta_300dpi",
                "kb":    round((svg_path.stat().st_size + png_path.stat().st_size + pdf_path.stat().st_size) / 1024, 1),
            }

        # ══════════════════════════════════════════════════════════
        # MOTOR 1 — CorelDRAW (calidad profesional, motor primario)
        # ══════════════════════════════════════════════════════════
        COREL_ENTRADA = IMAGENES | {"pdf", "svg", "dxf", "ai", "eps", "cdr"}
        COREL_SALIDA  = {"pdf", "png", "jpg", "svg", "dxf", "cdr", "ai"}
        corel_ok = False

        if ext_origen in COREL_ENTRADA and formato in COREL_SALIDA:
            try:
                from lib.corel_engine import convertir as corel_convertir, disponible as corel_disponible
                if corel_disponible():
                    res_corel = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: corel_convertir(
                            str(ruta_origen), formato,
                            dpi=dpi, nombre_salida=nombre_base,
                            vectorizar=vectorizar, mejorar=mejorar,
                        )
                    )
                    ruta_salida = _P(res_corel["ruta"])
                    motor_usado = "CorelDRAW"
                    corel_ok    = True
                    logger.info(f"Convert CorelDRAW OK → {ruta_salida.name}")
            except Exception as e_corel:
                logger.warning(f"CorelDRAW no disponible, usando fallback: {e_corel}")

        # ══════════════════════════════════════════════════════════
        # MOTOR 2 — Fallback: Pillow / Inkscape / PyMuPDF / ezdxf
        # ══════════════════════════════════════════════════════════
        if not corel_ok:

            # ── Quitar fondo blanco/gris antes de procesar ──────────
            if quitar_fondo and ext_origen in IMAGENES:
                from PIL import Image as _Img
                import numpy as _np
                _im = _Img.open(ruta_origen).convert("RGBA")
                _d  = _np.array(_im)
                _r, _g, _b = _d[:,:,0], _d[:,:,1], _d[:,:,2]
                _mask = (_r > 230) & (_g > 230) & (_b > 230) & \
                        (_np.abs(_r.astype(int) - _g.astype(int)) < 20) & \
                        (_np.abs(_g.astype(int) - _b.astype(int)) < 20)
                _d[_mask, 3] = 0
                _tmp_bg = ruta_origen.parent / f"{ruta_origen.stem}_nobg.png"
                _Img.fromarray(_d).save(str(_tmp_bg), "PNG")
                ruta_origen = _tmp_bg
                ext_origen  = "png"

            # ── Helper: mejora REAL con upscale de píxeles ───────────
            def _enh(ruta: _P, tdpi: int, subli: bool = False) -> _P:
                """
                Upscale real de píxeles al DPI objetivo + mejoras visuales.
                subli=True → +30% saturación para compensar pérdida en transferencia.
                """
                from PIL import Image as _I, ImageEnhance as _IE, ImageFilter as _IF
                im = _I.open(ruta)

                # Leer DPI del archivo (EXIF/info); asumir 72 si no tiene
                src_dpi = 72
                try:
                    info_dpi = im.info.get("dpi") or im.info.get("jfif_density")
                    if info_dpi and isinstance(info_dpi, (tuple, list)):
                        src_dpi = max(int(info_dpi[0]), 1) or 72
                    elif info_dpi:
                        src_dpi = max(int(info_dpi), 1) or 72
                except Exception:
                    pass

                w, h = im.size
                # Upscale real: aumentar píxeles para alcanzar tdpi al mismo tamaño físico
                if tdpi > src_dpi:
                    factor = tdpi / src_dpi
                    nuevo_w = int(w * factor)
                    nuevo_h = int(h * factor)
                    # Limitar a 8000px para no reventar la RAM
                    max_px = 8000
                    if max(nuevo_w, nuevo_h) > max_px:
                        scale = max_px / max(nuevo_w, nuevo_h)
                        nuevo_w = int(nuevo_w * scale)
                        nuevo_h = int(nuevo_h * scale)
                    if nuevo_w > w:  # solo si realmente agranda
                        im = im.resize((nuevo_w, nuevo_h), _I.LANCZOS)

                # Nitidez post-upscale
                im = im.filter(_IF.UnsharpMask(radius=2.0, percent=180, threshold=3))
                # Contraste
                im = _IE.Contrast(im).enhance(1.3)
                # Vibrado de color base
                if im.mode in ("RGB", "RGBA"):
                    im = _IE.Color(im).enhance(1.20)
                # Modo sublimación: +saturación extra (compensar pérdida en calor)
                if subli and im.mode in ("RGB", "RGBA"):
                    im = _IE.Color(im).enhance(1.35)
                    im = _IE.Brightness(im).enhance(1.05)

                out = ruta.parent / f"{ruta.stem}_enh{ruta.suffix}"
                if ruta.suffix.lower() in (".jpg", ".jpeg") and im.mode in ("RGBA","P","LA"):
                    im = im.convert("RGB")
                im.save(str(out), dpi=(tdpi, tdpi))
                return out

            # ══════════════════════════════════════════
            # IMAGEN → PDF
            # ══════════════════════════════════════════
            if ext_origen in IMAGENES and formato == "pdf":
                from PIL import Image
                src = _enh(ruta_origen, dpi, subli=sublimacion) if mejorar else ruta_origen
                img = Image.open(src)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.save(str(ruta_salida), "PDF", resolution=dpi)
                motor_usado = "Pillow"

            # ══════════════════════════════════════════
            # IMAGEN → PNG / JPG
            # ══════════════════════════════════════════
            elif ext_origen in IMAGENES and formato in ("png", "jpg"):
                from PIL import Image
                src = _enh(ruta_origen, dpi, subli=sublimacion) if mejorar else ruta_origen
                img = Image.open(src)
                if formato == "jpg" and img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                fmt_pil = "JPEG" if formato == "jpg" else "PNG"
                img.save(str(ruta_salida), fmt_pil, dpi=(dpi, dpi),
                         **({"quality": 95} if formato == "jpg" else {}))
                motor_usado = "Pillow"

            # ══════════════════════════════════════════
            # PDF → PDF  (recomprimir)
            # ══════════════════════════════════════════
            elif ext_origen == "pdf" and formato == "pdf":
                import fitz
                doc = fitz.open(str(ruta_origen))
                doc.save(str(ruta_salida), garbage=4, deflate=True, clean=True)
                doc.close()
                motor_usado = "PyMuPDF"

            # ══════════════════════════════════════════
            # PDF → PNG / JPG
            # ══════════════════════════════════════════
            elif ext_origen == "pdf" and formato in ("png", "jpg"):
                import fitz
                from PIL import Image, ImageEnhance, ImageFilter
                doc = fitz.open(str(ruta_origen))
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
                pix.save(str(ruta_salida))
                doc.close()
                if mejorar:
                    img = Image.open(ruta_salida)
                    img = img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=180, threshold=3))
                    img = ImageEnhance.Contrast(img).enhance(1.3)
                    if img.mode in ("RGB", "RGBA"):
                        img = ImageEnhance.Color(img).enhance(1.20)
                    if sublimacion and img.mode in ("RGB", "RGBA"):
                        img = ImageEnhance.Color(img).enhance(1.35)
                        img = ImageEnhance.Brightness(img).enhance(1.05)
                    if formato == "jpg" and img.mode in ("RGBA","P"):
                        img = img.convert("RGB")
                    img.save(str(ruta_salida), dpi=(dpi, dpi),
                             **({"quality": 95} if formato == "jpg" else {}))
                motor_usado = "PyMuPDF"

            # ══════════════════════════════════════════
            # PDF → SVG
            # ══════════════════════════════════════════
            elif ext_origen == "pdf" and formato == "svg":
                import fitz
                doc = fitz.open(str(ruta_origen))
                ruta_salida.write_text(doc[0].get_svg_image(), encoding="utf-8")
                doc.close()
                motor_usado = "PyMuPDF"

            # ══════════════════════════════════════════
            # PDF → DXF  (render → contornos → ezdxf)
            # ══════════════════════════════════════════
            elif ext_origen == "pdf" and formato == "dxf":
                import fitz, ezdxf, cv2, numpy as np
                doc = fitz.open(str(ruta_origen))
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                gris = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else arr
                _, bin_ = cv2.threshold(gris, 127, 255, cv2.THRESH_BINARY_INV)
                conts, _ = cv2.findContours(bin_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                doc.close()
                d = ezdxf.new("R2010"); msp = d.modelspace(); esc = 25.4 / dpi
                for c in conts:
                    pts = [(p[0][0]*esc, -p[0][1]*esc) for p in c]
                    if len(pts) >= 2: msp.add_lwpolyline(pts, close=True)
                d.saveas(str(ruta_salida))
                motor_usado = "ezdxf"

            # ══════════════════════════════════════════
            # IMAGEN → DXF
            # ══════════════════════════════════════════
            elif ext_origen in IMAGENES and formato == "dxf":
                import cv2, ezdxf, numpy as np
                img_cv = cv2.imread(str(ruta_origen), cv2.IMREAD_GRAYSCALE)
                if img_cv is None:
                    raise HTTPException(status_code=400, detail="No se pudo leer la imagen")
                _, bin_ = cv2.threshold(img_cv, 127, 255, cv2.THRESH_BINARY_INV)
                conts, _ = cv2.findContours(bin_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                d = ezdxf.new("R2010"); msp = d.modelspace(); esc = 25.4 / dpi
                for c in conts:
                    pts = [(p[0][0]*esc, -p[0][1]*esc) for p in c]
                    if len(pts) >= 2: msp.add_lwpolyline(pts, close=True)
                d.saveas(str(ruta_salida))
                motor_usado = "ezdxf"

            # ══════════════════════════════════════════
            # IMAGEN → SVG  (PNG embebido con mm reales)
            # ══════════════════════════════════════════
            elif ext_origen in IMAGENES and formato == "svg":
                from PIL import Image
                import base64
                src = _enh(ruta_origen, dpi, subli=sublimacion) if mejorar else ruta_origen
                img = Image.open(src); w, h = img.size
                png_tmp = OUTPUT_DIR / f"{nombre_base}_embed.png"
                img.save(str(png_tmp), "PNG", dpi=(dpi, dpi))
                b64  = base64.b64encode(png_tmp.read_bytes()).decode()
                w_mm = round(w * 25.4 / dpi, 2); h_mm = round(h * 25.4 / dpi, 2)
                svg  = (f'<?xml version="1.0" encoding="UTF-8"?>'
                        f'<svg xmlns="http://www.w3.org/2000/svg" '
                        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                        f'width="{w_mm}mm" height="{h_mm}mm" viewBox="0 0 {w} {h}">'
                        f'<image xlink:href="data:image/png;base64,{b64}" '
                        f'x="0" y="0" width="{w}" height="{h}"/></svg>')
                ruta_salida.write_text(svg, encoding="utf-8")
                png_tmp.unlink(missing_ok=True)
                motor_usado = "Pillow"

            # ══════════════════════════════════════════
            # SVG → SVG  (ajustar stroke-width láser,
            #             sin tocar dimensiones)
            # ══════════════════════════════════════════
            elif ext_origen == "svg" and formato == "svg":
                from lxml import etree
                tree = etree.parse(str(ruta_origen))
                root = tree.getroot()
                grosor_px = round(0.1 + (dpi - 72) * (2.0 / 228), 3)
                for el in root.iter():
                    style = el.get("style", "")
                    if style:
                        partes = [p.strip() for p in style.split(";") if p.strip()]
                        nuevas = [
                            f"stroke-width:{grosor_px}px" if p.startswith("stroke-width") else p
                            for p in partes
                        ]
                        el.set("style", ";".join(nuevas))
                    if el.get("stroke-width"):
                        el.set("stroke-width", str(grosor_px))
                tree.write(str(ruta_salida), xml_declaration=True,
                           encoding="utf-8", pretty_print=True)
                motor_usado = "lxml"

            # ══════════════════════════════════════════
            # SVG → PNG / JPG / PDF / DXF  (Inkscape CLI)
            # ══════════════════════════════════════════
            elif ext_origen == "svg" and formato in ("png", "jpg", "pdf", "dxf"):
                import subprocess
                inkscape = r"C:\Program Files\Inkscape\bin\inkscape.exe"
                fmt_ink  = "png" if formato == "jpg" else formato
                tmp_out  = (OUTPUT_DIR / f"{nombre_base}_ink.{fmt_ink}"
                            if formato == "jpg" else ruta_salida)
                res = subprocess.run([
                    inkscape, f"--export-type={fmt_ink}",
                    f"--export-dpi={dpi}", f"--export-filename={tmp_out}",
                    str(ruta_origen)
                ], capture_output=True, timeout=60)
                if res.returncode != 0:
                    raise HTTPException(500,
                        f"Inkscape: {res.stderr.decode(errors='ignore')[:200]}")
                if formato == "jpg":
                    from PIL import Image, ImageEnhance, ImageFilter
                    img = Image.open(str(tmp_out)).convert("RGB")
                    if mejorar:
                        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
                        img = ImageEnhance.Contrast(img).enhance(1.2)
                    img.save(str(ruta_salida), "JPEG", dpi=(dpi, dpi), quality=95)
                    tmp_out.unlink(missing_ok=True)
                motor_usado = "Inkscape"

            # ══════════════════════════════════════════
            # DXF → PNG / JPG  (ezdxf + matplotlib)
            # ══════════════════════════════════════════
            elif ext_origen == "dxf" and formato in ("png", "jpg"):
                import ezdxf
                from ezdxf.addons.drawing import RenderContext, Frontend
                from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
                import matplotlib.pyplot as plt
                doc = ezdxf.readfile(str(ruta_origen))
                fig = plt.figure(figsize=(12, 12), dpi=dpi)
                ax  = fig.add_axes([0, 0, 1, 1])
                Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(
                    doc.modelspace(), finalize=True)
                fig.savefig(str(ruta_salida), dpi=dpi,
                            format="png" if formato == "png" else "jpg",
                            bbox_inches="tight", pad_inches=0)
                plt.close(fig)
                motor_usado = "ezdxf+matplotlib"

            # ══════════════════════════════════════════
            # DXF → DXF  (normalizar pesos de línea)
            # ══════════════════════════════════════════
            elif ext_origen == "dxf" and formato == "dxf":
                import ezdxf
                doc = ezdxf.readfile(str(ruta_origen))
                for capa in doc.layers:
                    n = capa.dxf.name.upper()
                    if any(k in n for k in ["CUT","CORTE","CUT_LINE","C1"]):
                        capa.dxf.lineweight = 0
                    elif any(k in n for k in ["ENGRAVE","GRAB","RASTER","E1"]):
                        capa.dxf.lineweight = 25
                doc.saveas(str(ruta_salida))
                motor_usado = "ezdxf"

            # ══════════════════════════════════════════
            # DXF → PDF  (ezdxf SVGBackend → Inkscape)
            # ══════════════════════════════════════════
            elif ext_origen == "dxf" and formato == "pdf":
                import subprocess, ezdxf
                from ezdxf.addons.drawing import RenderContext, Frontend
                from ezdxf.addons.drawing.svg import SVGBackend
                svg_tmp = OUTPUT_DIR / f"{nombre_base}_tmp.svg"
                doc = ezdxf.readfile(str(ruta_origen))
                backend = SVGBackend()
                Frontend(RenderContext(doc), backend).draw_layout(
                    doc.modelspace(), finalize=True)
                svg_tmp.write_text(backend.get_xml_root_element_as_string(), encoding="utf-8")
                inkscape = r"C:\Program Files\Inkscape\bin\inkscape.exe"
                subprocess.run([inkscape, "--export-type=pdf",
                    f"--export-filename={ruta_salida}", str(svg_tmp)],
                    capture_output=True, timeout=60)
                svg_tmp.unlink(missing_ok=True)
                motor_usado = "ezdxf+Inkscape"

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Combinación .{ext_origen} → .{formato} no soportada."
                )

        if not ruta_salida.exists():
            raise HTTPException(status_code=500, detail="El motor no generó archivo de salida")

        kb = round(ruta_salida.stat().st_size / 1024, 1)
        return {
            "ok":      True,
            "success": True,
            "path":    str(ruta_salida),
            "url":     f"/static/output/{ruta_salida.name}",
            "nombre":  ruta_salida.name,
            "formato": formato,
            "dpi":     dpi,
            "kb":      kb,
            "motor":   motor_usado,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Convert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            ruta_origen.unlink(missing_ok=True)
        except Exception:
            pass


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
#  NEXUS TEENS — UI + proxy a motor_teens (puerto 8005)
# ══════════════════════════════════════════════════════════════

@app.get("/teens", response_class=HTMLResponse)
async def teens_ui(request: Request):
    """UI web para NEXUS Teens — funciona desde cualquier dispositivo."""
    ruta = os.path.join(os.path.dirname(__file__), "templates", "teens.html")
    with open(ruta, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/teens-launch")
async def teens_launch(response: Response):
    """Punto de entrada que bypasea el interstitial de ngrok y redirige a /teens."""
    response.set_cookie("ngrok-skip-browser-warning", "true", max_age=31536000, path="/")
    response.status_code = 302
    response.headers["Location"] = "/teens"
    return response


@app.get("/teens/sw.js")
async def teens_sw():
    """Service worker para PWA offline cache."""
    sw_code = """
const CACHE = 'teens-v1';
const SHELL = ['/teens'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Solo cachear la shell HTML; las API siempre van a la red
  if (url.pathname === '/teens') {
    e.respondWith(
      fetch(e.request, {headers: {'ngrok-skip-browser-warning': 'true'}})
        .then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
        .catch(() => caches.match('/teens'))
    );
  } else if (url.pathname.startsWith('/teens/api')) {
    // API: siempre red, agregar header bypass
    const req = new Request(e.request, {headers: Object.assign({}, ...Array.from(e.request.headers.entries()).map(([k,v]) => ({[k]:v})), {'ngrok-skip-browser-warning': 'true'})});
    e.respondWith(fetch(req));
  }
});
"""
    return Response(content=sw_code, media_type="application/javascript")


@app.get("/teens/manifest.json")
async def teens_manifest():
    """PWA manifest para instalar en el teléfono."""
    return JSONResponse({
        "name": "NEXUS Teens",
        "short_name": "Teens",
        "start_url": "/teens",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#7c3aed",
        "orientation": "portrait",
        "icons": [
            {"src": "/static/teens-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/teens-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })


@app.api_route("/teens/api/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def teens_proxy(path: str, request: Request):
    """Proxy transparente a motor_teens en puerto 8005."""
    import httpx as _httpx
    # /execute vive en la raíz del motor, el resto bajo /teens/
    if path == "execute":
        teens_url = "http://localhost:8005/execute"
    else:
        teens_url = f"http://localhost:8005/teens/{path}"
    try:
        body = await request.body()
        async with _httpx.AsyncClient(timeout=90) as c:
            r = await c.request(
                method=request.method,
                url=teens_url,
                content=body,
                headers={"Content-Type": "application/json"},
                params=dict(request.query_params),
            )
            return JSONResponse(content=r.json(), status_code=r.status_code)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:100]}, status_code=503)


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

# ── Montar carpeta de salida (archivos convertidos) ───────────
from pathlib import Path as _PathStatic
_output_dir = _PathStatic("C:/nexus/MERCH_OUTPUT")
_output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/output", StaticFiles(directory=str(_output_dir)), name="output")

# ── Montar carpeta de diagramas automotrices ──────────────────
_diag_dir = _PathStatic("C:/NEXUS_v3_NEW/output/diagramas")
_diag_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/diagramas", StaticFiles(directory=str(_diag_dir)), name="diagramas")

# ── Sitios web completos servidos por NEXUS ───────────────────
_atf_web   = _PathStatic("C:/NEXUS_v3_NEW/output/atf_web")
_milens_web = _PathStatic("C:/NEXUS_v3_NEW/output/milens_web")
_atf_web.mkdir(parents=True, exist_ok=True)
_milens_web.mkdir(parents=True, exist_ok=True)
app.mount("/sitio/atf",    StaticFiles(directory=str(_atf_web),   html=True), name="atf_web")
app.mount("/sitio/milens", StaticFiles(directory=str(_milens_web), html=True), name="milens_web")

@app.get("/atf", response_class=HTMLResponse, tags=["Sitios"])
async def redirect_atf():
    return HTMLResponse('<meta http-equiv="refresh" content="0;url=/sitio/atf/">', status_code=302)

@app.get("/milens", response_class=HTMLResponse, tags=["Sitios"])
async def redirect_milens():
    return HTMLResponse('<meta http-equiv="refresh" content="0;url=/sitio/milens/">', status_code=302)

# ── API estado sitios (para panel NEXUS) ──────────────────────
@app.get("/api/sitios", tags=["Sitios"])
async def estado_sitios():
    """Estado y links de los sitios web gestionados por NEXUS."""
    import os as _os
    def _size(p):
        try: return _os.path.getsize(p)
        except: return 0
    return {
        "ok": True,
        "sitios": [
            {
                "nombre": "ATF — Actualiza Tus Faros",
                "url_local": "http://localhost:8003/atf",
                "url_ngrok": "https://enrique-slaty-afton.ngrok-free.dev/atf",
                "index_bytes": _size("C:/NEXUS_v3_NEW/output/atf_web/index.html"),
                "redes": {
                    "facebook": "https://www.facebook.com/ActualizaTusFaros",
                    "instagram": "https://www.instagram.com/atf.guadalajara",
                    "tiktok": "https://www.tiktok.com/@atfguadalajara",
                    "whatsapp": "https://wa.me/523323530146"
                },
                "wa_numero": "33 2353 0146",
                "tel_numero": "33 2614 8674"
            },
            {
                "nombre": "Creaciones Milens",
                "url_local": "http://localhost:8003/milens",
                "url_ngrok": "https://enrique-slaty-afton.ngrok-free.dev/milens",
                "index_bytes": _size("C:/NEXUS_v3_NEW/output/milens_web/index.html"),
                "redes": {
                    "whatsapp": "https://wa.me/523323530146"
                },
                "wa_numero": "33 2353 0146"
            }
        ]
    }

# ══════════════════════════════════════════════════════════════
#  MERCADOPAGO — CHECKOUT PRO
# ══════════════════════════════════════════════════════════════
# SDK: pip install mercadopago  (ya instalado 2.3.0)
# Credenciales: https://www.mercadopago.com.mx/settings/account/credentials
# .env: MP_ACCESS_TOKEN, MP_PUBLIC_KEY, MP_MODO (test|prod)

def _mp_sdk():
    """Retorna instancia SDK MP. Lanza ValueError si no hay token."""
    import mercadopago
    token = os.getenv("MP_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("MP_ACCESS_TOKEN no configurado en .env")
    return mercadopago.SDK(token)

def _mp_ngrok_base():
    """URL base pública (ngrok) para callbacks MP."""
    return "https://enrique-slaty-afton.ngrok-free.dev"

@app.get("/api/mp/estado", tags=["MercadoPago"])
async def mp_estado():
    """Verifica si MP está configurado y el token es válido."""
    token = os.getenv("MP_ACCESS_TOKEN", "")
    modo  = os.getenv("MP_MODO", "test")
    if not token:
        return {
            "ok": False,
            "configurado": False,
            "mensaje": "MP_ACCESS_TOKEN vacío en .env",
            "instrucciones": [
                "1. Ve a https://www.mercadopago.com.mx/settings/account/credentials",
                "2. Copia Access Token (TEST para pruebas, PRODUCCION para cobros reales)",
                "3. Agrega MP_ACCESS_TOKEN=tu_token en C:/NEXUS_v3_NEW/.env",
                "4. Reinicia NEXUS"
            ]
        }
    try:
        sdk = _mp_sdk()
        # Verificar token consultando métodos de pago
        r = sdk.payment_methods().list_all({})
        valido = r["status"] == 200
        return {
            "ok": valido,
            "configurado": True,
            "modo": modo,
            "metodos_pago": len(r.get("response", [])) if valido else 0,
            "token_preview": token[:8] + "..." + token[-4:]
        }
    except Exception as e:
        return {"ok": False, "configurado": True, "error": str(e)}

@app.post("/api/mp/preferencia", tags=["MercadoPago"])
async def mp_crear_preferencia(request: Request):
    """
    Crea preferencia de pago Checkout Pro.
    Body JSON: {
      "titulo": "Aozoom X4 Dragon Knight",
      "precio": 1990,
      "cantidad": 1,
      "descripcion": "Kit Bi-LED instalado en Guadalajara",
      "referencia": "ATF-X4-001"   (opcional, tu ID interno)
    }
    Retorna: { "ok": true, "checkout_url": "...", "preference_id": "..." }
    """
    try:
        sdk = _mp_sdk()
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)

    body = await request.json()
    titulo    = body.get("titulo", "Instalación ATF")
    precio    = float(body.get("precio", 0))
    cantidad  = int(body.get("cantidad", 1))
    desc      = body.get("descripcion", "Iluminación vehicular profesional — Guadalajara")
    referencia = body.get("referencia", "ATF-WEB")
    modo      = os.getenv("MP_MODO", "test")
    base      = _mp_ngrok_base()

    preference_data = {
        "items": [{
            "id":          referencia,
            "title":       titulo,
            "description": desc,
            "category_id": "services",
            "quantity":    cantidad,
            "unit_price":  precio,
            "currency_id": "MXN"
        }],
        "payer": {
            "phone": {"number": "3323530146"}
        },
        "back_urls": {
            "success": f"{base}/api/mp/exito",
            "failure": f"{base}/api/mp/falla",
            "pending": f"{base}/api/mp/pendiente"
        },
        "auto_return": "approved",
        "notification_url": f"{base}/api/mp/webhook",
        "statement_descriptor": "ATF SIMPLEX GDL",
        "external_reference": referencia,
        "expires": False,
        "binary_mode": False,          # permite pagos pendientes (OXXO, etc)
        "metadata": {
            "negocio": "ATF",
            "canal":   "web"
        }
    }

    try:
        result = sdk.preference().create(preference_data)
        resp   = result["response"]
        pref_id = resp.get("id")

        if modo == "test":
            checkout_url = resp.get("sandbox_init_point", resp.get("init_point"))
        else:
            checkout_url = resp.get("init_point")

        logger.info("MP preferencia creada: %s — %s $%.0f", pref_id, titulo, precio)
        return {
            "ok":             True,
            "preference_id":  pref_id,
            "checkout_url":   checkout_url,
            "modo":           modo,
            "titulo":         titulo,
            "precio":         precio
        }
    except Exception as e:
        logger.error("MP error creando preferencia: %s", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/mp/exito", tags=["MercadoPago"], response_class=HTMLResponse)
async def mp_exito(request: Request):
    """Callback MP pago exitoso — redirige al sitio con confirmación."""
    params = dict(request.query_params)
    pago_id   = params.get("payment_id", "")
    referencia = params.get("external_reference", "")
    logger.info("MP pago exitoso — payment_id=%s ref=%s", pago_id, referencia)
    wa_msg = f"Mi%20pago%20fue%20aprobado%20%F0%9F%8E%89%20Ref:%20{referencia}%20ID:%20{pago_id}"
    html = f"""<!DOCTYPE html><html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pago Aprobado - ATF</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Inter',sans-serif;background:#04090f;color:#fff;
  min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;}}
.card{{max-width:440px;background:rgba(255,255,255,.04);border:1px solid rgba(37,211,102,.2);
  border-radius:20px;padding:48px 36px;}}
.icon{{font-size:4rem;margin-bottom:20px;}}
h1{{font-size:1.8rem;font-weight:900;color:#25d366;margin-bottom:12px;}}
p{{color:rgba(255,255,255,.55);line-height:1.7;margin-bottom:24px;}}
.ref{{font-size:.75rem;color:rgba(255,255,255,.25);margin-bottom:28px;}}
.btn{{background:#25d366;color:#fff;padding:14px 28px;border-radius:10px;
  font-weight:700;text-decoration:none;display:inline-block;}}
</style></head>
<body><div class="card">
  <div class="icon">🎉</div>
  <h1>Pago Aprobado</h1>
  <p>Tu apartado esta confirmado. En breve te contactamos por WhatsApp para coordinar tu instalacion.</p>
  <div class="ref">Referencia: {referencia} &nbsp;|&nbsp; Pago: {pago_id}</div>
  <a class="btn" href="https://wa.me/523323530146?text={wa_msg}" target="_blank">Confirmar por WhatsApp</a>
</div></body></html>"""
    return HTMLResponse(html)

@app.get("/api/mp/falla", tags=["MercadoPago"], response_class=HTMLResponse)
async def mp_falla(request: Request):
    """Callback MP pago fallido."""
    html = """<!DOCTYPE html><html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pago No Procesado - ATF</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',sans-serif;background:#04090f;color:#fff;
  min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;}
.card{max-width:440px;background:rgba(255,255,255,.04);border:1px solid rgba(239,68,68,.2);
  border-radius:20px;padding:48px 36px;}
.icon{font-size:4rem;margin-bottom:20px;}
h1{font-size:1.8rem;font-weight:900;color:#ef4444;margin-bottom:12px;}
p{color:rgba(255,255,255,.55);line-height:1.7;margin-bottom:28px;}
.btn{background:#25d366;color:#fff;padding:14px 28px;border-radius:10px;
  font-weight:700;text-decoration:none;display:inline-block;}
</style></head>
<body><div class="card">
  <div class="icon">⚠️</div>
  <h1>Pago No Procesado</h1>
  <p>No se pudo completar el pago. Puedes intentarlo de nuevo o contactarnos directamente.</p>
  <a class="btn" href="https://wa.me/523323530146?text=Hola%20ATF%2C%20tuve%20problema%20con%20mi%20pago%20en%20la%20web" target="_blank">Contactar por WhatsApp</a>
</div></body></html>"""
    return HTMLResponse(html)

@app.get("/api/mp/pendiente", tags=["MercadoPago"], response_class=HTMLResponse)
async def mp_pendiente(request: Request):
    """Callback MP pago pendiente (OXXO, transferencia)."""
    params = dict(request.query_params)
    referencia = params.get("external_reference", "")
    html = f"""<!DOCTYPE html><html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pago Pendiente - ATF</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Inter',sans-serif;background:#04090f;color:#fff;
  min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;}}
.card{{max-width:440px;background:rgba(255,255,255,.04);border:1px solid rgba(245,158,11,.2);
  border-radius:20px;padding:48px 36px;}}
.icon{{font-size:4rem;margin-bottom:20px;}}
h1{{font-size:1.8rem;font-weight:900;color:#f59e0b;margin-bottom:12px;}}
p{{color:rgba(255,255,255,.55);line-height:1.7;margin-bottom:28px;}}
.btn{{background:#25d366;color:#fff;padding:14px 28px;border-radius:10px;
  font-weight:700;text-decoration:none;display:inline-block;}}
</style></head>
<body><div class="card">
  <div class="icon">⏳</div>
  <h1>Pago Pendiente</h1>
  <p>Tu pago esta en proceso. Te avisaremos cuando se confirme. Referencia: <strong>{referencia}</strong></p>
  <a class="btn" href="https://wa.me/523323530146?text=Hola%20ATF%2C%20hice%20un%20pago%20pendiente%20Ref:%20{referencia}" target="_blank">Avisar por WhatsApp</a>
</div></body></html>"""
    return HTMLResponse(html)

@app.post("/api/mp/webhook", tags=["MercadoPago"])
async def mp_webhook(request: Request):
    """IPN de MercadoPago — registra notificaciones de pagos."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    tipo    = body.get("type", request.query_params.get("topic", ""))
    data_id = body.get("data", {}).get("id") or request.query_params.get("id", "")
    logger.info("MP webhook: tipo=%s id=%s", tipo, data_id)

    if tipo == "payment" and data_id:
        try:
            sdk = _mp_sdk()
            pago = sdk.payment().get(data_id)
            status = pago["response"].get("status")
            monto  = pago["response"].get("transaction_amount")
            ref    = pago["response"].get("external_reference")
            logger.info("MP pago %s — status=%s monto=%s ref=%s", data_id, status, monto, ref)
            # TODO: aquí registrar en DB de NEXUS cuando esté integrado
        except Exception as e:
            logger.error("MP error procesando webhook payment: %s", e)

    return JSONResponse({"ok": True})

@app.get("/api/mp/pagos", tags=["MercadoPago"])
async def mp_listar_pagos(limite: int = 20):
    """Lista los últimos pagos recibidos via MP."""
    try:
        sdk = _mp_sdk()
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)
    try:
        result = sdk.payment().search({
            "filters": {"sort": "date_created", "criteria": "desc"},
            "offset": 0,
            "limit": limite
        })
        pagos_raw = result["response"].get("results", [])
        pagos = [{
            "id":         p.get("id"),
            "estado":     p.get("status"),
            "monto":      p.get("transaction_amount"),
            "descripcion":p.get("description"),
            "referencia": p.get("external_reference"),
            "fecha":      p.get("date_created","")[:10],
            "metodo":     p.get("payment_type_id")
        } for p in pagos_raw]
        total = sum(p["monto"] or 0 for p in pagos if p["estado"] == "approved")
        return {
            "ok":    True,
            "total_aprobado": total,
            "pagos": pagos
        }
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ── Cotizacion ATF con MP link cuando este listo ───────────────
@app.get("/api/atf/cotizacion", tags=["ATF"])
async def atf_cotizacion(producto: str = "", precio: int = 0):
    """Genera link de cotización ATF. Si MP está configurado, genera preferencia."""
    import urllib.parse as _up
    wa_msg = f"Hola ATF, quiero apartar {producto} por ${precio:,}. Guadalajara."
    wa_url = f"https://wa.me/523323530146?text={_up.quote(wa_msg)}"
    token  = os.getenv("MP_ACCESS_TOKEN", "")
    return {
        "ok":          True,
        "producto":    producto,
        "precio":      precio,
        "wa_url":      wa_url,
        "mp_activo":   bool(token),
        "mp_endpoint": "/api/mp/preferencia" if token else None,
        "nota":        "MP activo" if token else "Agrega MP_ACCESS_TOKEN en .env para activar pagos"
    }


# ══════════════════════════════════════════════════════════════
#  MERCADOLIBRE — OAuth2 + Publicaciones
# ══════════════════════════════════════════════════════════════
_MELI_TOKEN_FILE = "C:/NEXUS_v3_NEW/data/meli_token.json"
_MELI_FOTOS_DIR  = "C:/NEXUS_v3_NEW/data/fotos_aozoom/"

# Mapeo producto → imágenes (main + detalles del catálogo PDF)
_MELI_FOTOS_MAP = {
    # Aozoom proyectores
    "AOZOOM_X1":        ["aozoom_x1.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X2":        ["aozoom_x2.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X3":        ["aozoom_x3.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X4":        ["aozoom_x4.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X5":        ["aozoom_x5.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X6":        ["aozoom_x6.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X7":        ["aozoom_x7.jpg", "aozoom_x7t.jpg", "led_proyector_lens.jpg"],
    "AOZOOM_X7_TRICOLOR":["aozoom_x7t.jpg", "aozoom_x7.jpg", "led_proyector_lens.jpg"],
    # Kits LED Ilume
    "LED_PLUS_SINGLE":          ["led_plus.jpg", "led_proyector_lens.jpg"],
    "LED_PLUS_DOBLE":           ["led_plus.jpg", "led_proyector_lens.jpg"],
    "LED_BASIC_SINGLE":         ["led_basic.jpg", "led_proyector_lens.jpg"],
    "LED_BASIC_DOBLE":          ["led_basic.jpg", "led_proyector_lens.jpg"],
    "LED_CLASSIC_SINGLE":       ["led_classic.jpg", "led_proyector_lens.jpg"],
    "LED_CLASSIC_DOBLE":        ["led_classic.jpg", "led_proyector_lens.jpg"],
    "LED_TRICOLOR_SINGLE":      ["led_tricolor.jpg", "led_proyector_lens.jpg"],
    "LED_TRICOLOR_DOBLE":       ["led_tricolor.jpg", "led_proyector_lens.jpg"],
    "LED_PREMIUM_LITE_SINGLE":  ["led_premium_lite.jpg", "led_proyector_lens.jpg"],
    "LED_PREMIUM_LITE_DOBLE":   ["led_premium_lite.jpg", "led_proyector_lens.jpg"],
    "LED_PROYECTOR_LENS_H4_2":  ["led_proyector_lens.jpg"],
    "LED_PROYECTOR_LENS_H4_3":  ["led_proyector_lens.jpg"],
    "LED_PREMIUM_55W_SINGLE":   ["led_premium_55w.jpg", "led_proyector_lens.jpg"],
    "LED_PREMIUM_55W_DOBLE":    ["led_premium_55w.jpg", "led_proyector_lens.jpg"],
    "LED_EXCLUSIVE_70W_SINGLE": ["led_exclusive_70w.jpg", "led_proyector_lens.jpg"],
    "LED_EXCLUSIVE_70W_DOBLE":  ["led_exclusive_70w.jpg", "led_proyector_lens.jpg"],
    "LED_EXCLUSIVE_90W_SINGLE": ["led_exclusive_90w.jpg", "led_proyector_lens.jpg"],
    "LED_EXCLUSIVE_90W_DOBLE":  ["led_exclusive_90w.jpg", "led_proyector_lens.jpg"],
    # Auxiliares
    "AUX_P13W":         ["aux_p13w.jpg"],
    "AUX_1156_BLANCO":  ["aux_1156.jpg", "aux_t10_canbus.jpg"],
    "AUX_1156_AMBAR":   ["aux_1156_ambar.jpg"],
    "AUX_1156_RED":     ["aux_1156_red.jpg"],
    "AUX_3156":         ["aux_3157.jpg"],
    "AUX_7440":         ["aux_7440.jpg"],
    "AUX_3157_BICOLOR": ["aux_3157_bicolor.jpg"],
    "AUX_1157_BICOLOR": ["aux_3157_bicolor.jpg"],
    "AUX_7443_BICOLOR": ["aux_3157_bicolor.jpg"],
    "AUX_FESTOON_31":   ["aux_festoon_31.jpg", "aux_festoon_36.jpg"],
    "AUX_FESTOON_36":   ["aux_festoon_36.jpg", "aux_festoon_31.jpg"],
    "AUX_FESTOON_39":   ["aux_festoon_36.jpg", "aux_festoon_42.jpg"],
    "AUX_FESTOON_42":   ["aux_festoon_42.jpg", "aux_festoon_36.jpg"],
    "AUX_T10_CORTO":    ["aux_t10_board.jpg", "aux_t10_canbus.jpg"],
    "AUX_T10_LUPA":     ["aux_t10_lupa.jpg", "aux_t10_canbus.jpg"],
    "AUX_T10_GRANDE":   ["aux_t10_corn.jpg", "aux_t10_canbus.jpg"],
    "AUX_T10_LARGA_CORN":["aux_t10_corn.jpg"],
    "AUX_T10_360":      ["aux_t10_360.jpg", "aux_t10_canbus.jpg"],
    # ALO Off-Road
    "ALO_FLUSH_MOUNT":   ["alo_flush_mount.jpg"],
    "ALO_DUALLY":        ["alo_dually.jpg"],
    "ALO_SINGLE_ROW_6":  ["alo_single_row_6.jpg", "alo_single_row_10.jpg"],
    "ALO_SINGLE_ROW_10": ["alo_single_row_10.jpg", "alo_single_row_6.jpg"],
    "ALO_QUAD_DRIVING":  ["alo_quad_driving.jpg"],
    "ALO_ROUND_LIGHT":   ["alo_round_light.jpg"],
    "ALO_ROCK_LIGHT_KIT":["alo_rock_light_kit.jpg"],
    "MAMMOTH_ASADOR":    ["mammoth_asador.jpg"],
}

def _meli_save_token(data: dict):
    import json as _j
    with open(_MELI_TOKEN_FILE, "w", encoding="utf-8") as f:
        _j.dump(data, f)

def _meli_load_token() -> dict:
    import json as _j
    try:
        with open(_MELI_TOKEN_FILE, encoding="utf-8") as f:
            return _j.load(f)
    except Exception:
        return {}

def _meli_refresh() -> str:
    """Refresca access_token usando refresh_token. Retorna nuevo access_token."""
    import requests as _req
    t = _meli_load_token()
    if not t.get("refresh_token"):
        raise ValueError("Sin refresh_token — necesita re-autorizar en /api/meli/auth")
    cid  = os.getenv("MELI_CLIENT_ID", "")
    csec = os.getenv("MELI_CLIENT_SECRET", "")
    body = f"grant_type=refresh_token&client_id={cid}&client_secret={csec}&refresh_token={t['refresh_token']}"
    r = _req.post(
        "https://api.mercadolibre.com/oauth/token",
        headers={"accept": "application/json", "content-type": "application/x-www-form-urlencoded"},
        data=body
    )
    if not r.ok:
        raise ValueError(f"Refresh fallido {r.status_code}: {r.text[:120]} — re-autorizar en /api/meli/auth")
    nuevo = r.json()
    nuevo.setdefault("refresh_token", t["refresh_token"])
    _meli_save_token(nuevo)
    logger.info("MELI token renovado automaticamente")
    return nuevo["access_token"]

def _meli_access_token() -> str:
    """Retorna access_token válido. Auto-refresca si recibe 401. Thread-safe."""
    import requests as _req
    t = _meli_load_token()
    if not t.get("access_token"):
        raise ValueError("No autorizado — ve a /api/meli/auth")
    token = t["access_token"]
    # Verificación ligera: si el token falla intentamos refresh automático
    probe = _req.get("https://api.mercadolibre.com/users/me",
                     headers={"Authorization": f"Bearer {token}"}, timeout=5)
    if probe.status_code == 401:
        logger.warning("MELI token expirado — intentando refresh automatico")
        token = _meli_refresh()   # lanza ValueError si falla
    return token

def _meli_upscale_img(src_path: str, min_px: int = 500) -> bytes:
    """Upscale imagen a min_px si es más pequeña. Retorna bytes JPEG."""
    from PIL import Image as _PIL
    import io as _io
    img = _PIL.open(src_path).convert("RGB")
    w, h = img.size
    if w < min_px or h < min_px:
        factor = max(min_px / w, min_px / h)
        img = img.resize((int(w * factor), int(h * factor)), _PIL.LANCZOS)
    buf = _io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()

def _meli_upload_foto(token: str, img_bytes: bytes) -> str:
    """Sube imagen a ML y retorna su ID."""
    import requests as _req
    r = _req.post(
        "https://api.mercadolibre.com/pictures/items/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("foto.jpg", img_bytes, "image/jpeg")}
    )
    if not r.ok:
        raise ValueError(f"Upload foto fallido {r.status_code}: {r.text[:80]}")
    d = r.json()
    return d.get("id") or d.get("_id") or ""

def _meli_preparar_fotos(token: str, key: str) -> list:
    """Upscalea y sube 3-5 fotos del producto. Retorna lista de IDs ML."""
    import os as _os
    fotos = _MELI_FOTOS_MAP.get(key, [f"aozoom_{key.split('_')[-1].lower()}.jpg"])
    ids = []
    for fn in fotos:
        path = _os.path.join(_MELI_FOTOS_DIR, fn)
        if not _os.path.exists(path):
            continue
        try:
            img_bytes = _meli_upscale_img(path, min_px=500)
            fid = _meli_upload_foto(token, img_bytes)
            if fid:
                ids.append({"id": fid})
        except Exception as ex:
            logger.warning("Foto %s no subida: %s", fn, ex)
    return ids

@app.get("/api/meli/estado", tags=["MercadoLibre"])
async def meli_estado():
    """Verifica si MELI está autorizado y el token es válido. Auto-refresca si expiró."""
    import requests as _req
    cid  = os.getenv("MELI_CLIENT_ID", "")
    csec = os.getenv("MELI_CLIENT_SECRET", "")
    t    = _meli_load_token()
    if not cid or not csec:
        return {"ok": False, "paso": "credenciales",
                "mensaje": "MELI_CLIENT_ID / MELI_CLIENT_SECRET vacíos en .env"}
    if not t.get("access_token"):
        return {"ok": False, "paso": "autorizar",
                "accion": "GET /api/meli/auth → abre la URL en browser → autoriza"}
    # Verificar token en vivo
    probe = _req.get("https://api.mercadolibre.com/users/me",
                     headers={"Authorization": f"Bearer {t['access_token']}"}, timeout=5)
    if probe.status_code == 401:
        try:
            _meli_refresh()
            t = _meli_load_token()
            token_status = "renovado_automaticamente"
        except Exception as ex:
            return {"ok": False, "paso": "expirado", "error": str(ex),
                    "accion": "GET /api/meli/auth → abre la URL en browser → autoriza"}
    else:
        token_status = "activo"
    usuario = probe.json() if probe.ok else _meli_load_token()
    return {
        "ok":            True,
        "autorizado":    True,
        "token_status":  token_status,
        "user_id":       t.get("user_id"),
        "nickname":      usuario.get("nickname", ""),
        "token_preview": t["access_token"][:12] + "...",
        "tiene_refresh": bool(t.get("refresh_token")),
        "accion":        "Token listo — puedes llamar POST /api/meli/publicar-todo"
    }

import hashlib, base64, secrets as _secrets
_PKCE_STORE: dict = {}   # state -> code_verifier

@app.get("/api/meli/auth", tags=["MercadoLibre"])
async def meli_auth():
    """Genera URL de autorización OAuth2 de ML con PKCE (requerido por la app)."""
    import urllib.parse as _up, json as _jj2
    cid = os.getenv("MELI_CLIENT_ID", "")
    if not cid:
        return JSONResponse({"ok": False, "error": "MELI_CLIENT_ID vacío en .env"}, status_code=503)
    redirect = "https://enrique-slaty-afton.ngrok-free.dev/api/meli/callback"
    code_verifier  = base64.urlsafe_b64encode(_secrets.token_bytes(32)).rstrip(b'=').decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    state = _secrets.token_hex(8)
    _PKCE_STORE[state] = code_verifier
    # Persistir en disco — sobrevive reinicios de NEXUS
    try:
        _pkce_path2 = "C:/NEXUS_v3_NEW/data/pkce_temp.json"
        _ex = {}
        try:
            with open(_pkce_path2) as _f: _ex = _jj2.load(_f)
        except Exception: pass
        _ex[state] = code_verifier
        with open(_pkce_path2, "w") as _f: _jj2.dump(_ex, _f)
    except Exception: pass
    url = (
        "https://auth.mercadolibre.com.mx/authorization"
        f"?response_type=code&client_id={cid}"
        f"&redirect_uri={_up.quote(redirect, safe='')}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
        f"&state={state}"
    )
    return {
        "ok":          True,
        "url_autorizar": url,
        "instruccion": "Copia esta URL y ábrela en tu browser. Inicia sesión con tu cuenta ML y autoriza la app."
    }

@app.get("/api/meli/callback", tags=["MercadoLibre"], response_class=HTMLResponse)
async def meli_callback(request: Request):
    """Callback OAuth2 — ML redirige aquí con el code. NEXUS lo intercambia por tokens."""
    import requests as _req
    import urllib.parse as _up
    code  = request.query_params.get("code", "")
    state = request.query_params.get("state", "")
    error = request.query_params.get("error", "")
    if error or not code:
        return HTMLResponse(f"<h2>Error ML: {error or 'sin code'}</h2>", status_code=400)
    cid          = os.getenv("MELI_CLIENT_ID", "")
    csec         = os.getenv("MELI_CLIENT_SECRET", "")
    redirect     = "https://enrique-slaty-afton.ngrok-free.dev/api/meli/callback"
    code_verifier = _PKCE_STORE.pop(state, "")
    if not code_verifier:
        # Fallback: leer del archivo temporal (para auth generada externamente)
        try:
            import json as _jj
            _pkce_path = "C:/NEXUS_v3_NEW/data/pkce_temp.json"
            with open(_pkce_path) as _pf:
                _store = _jj.load(_pf)
            code_verifier = _store.pop(state, "")
            with open(_pkce_path, "w") as _pf:
                _jj.dump(_store, _pf)
        except Exception:
            pass
    try:
        logger.info("MELI token exchange — cid=%s code=%s... pkce=%s", cid, code[:8], bool(code_verifier))
        payload = {
            "grant_type":    "authorization_code",
            "client_id":     cid,
            "client_secret": csec,
            "code":          code,
            "redirect_uri":  redirect,
            "code_verifier": code_verifier,
        }
        r = _req.post(
            "https://api.mercadolibre.com/oauth/token",
            data=payload
        )
        if not r.ok:
            logger.error("MELI token error %s: %s", r.status_code, r.text)
            return HTMLResponse(f"<h2>Error ML {r.status_code}</h2><pre>{r.text}</pre>", status_code=400)
        token_data = r.json()
        _meli_save_token(token_data)
        uid = token_data.get("user_id", "")
        logger.info("MELI autorizado — user_id=%s", uid)
        html = f"""<!DOCTYPE html><html lang="es">
<head><meta charset="UTF-8"><title>ML Autorizado</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Inter',sans-serif;background:#04090f;color:#fff;min-height:100vh;
  display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;}}
.card{{max-width:420px;background:rgba(255,255,255,.04);border:1px solid rgba(255,230,0,.2);
  border-radius:20px;padding:48px 36px;}}
h1{{font-size:1.8rem;font-weight:900;color:#ffe600;margin:16px 0 12px;}}
p{{color:rgba(255,255,255,.55);line-height:1.7;margin-bottom:24px;}}
.uid{{font-size:.75rem;color:rgba(255,255,255,.25);}}
.btn{{background:#ffe600;color:#000;padding:14px 28px;border-radius:10px;
  font-weight:700;text-decoration:none;display:inline-block;}}
</style></head>
<body><div class="card">
  <div style="font-size:3rem">🟡</div>
  <h1>MercadoLibre Autorizado</h1>
  <p>NEXUS ya puede publicar, gestionar preguntas y ver ventas en tu cuenta ML.</p>
  <div class="uid">User ID: {uid}</div><br>
  <a class="btn" href="http://localhost:8003/api/meli/estado">Ver estado</a>
</div></body></html>"""
        return HTMLResponse(html)
    except Exception as e:
        logger.error("MELI callback error: %s", e)
        return HTMLResponse(f"<h2>Error al obtener token: {e}</h2>", status_code=500)

@app.get("/api/meli/publicaciones", tags=["MercadoLibre"])
async def meli_mis_publicaciones(limite: int = 20):
    """Lista publicaciones activas en ML."""
    import requests as _req
    try:
        token = _meli_access_token()
        uid_data = _req.get(f"https://api.mercadolibre.com/users/me",
                            headers={"Authorization": f"Bearer {token}"})
        uid = uid_data.json().get("id")
        r = _req.get(
            f"https://api.mercadolibre.com/users/{uid}/items/search",
            params={"limit": limite, "status": "active"},
            headers={"Authorization": f"Bearer {token}"}
        )
        items = r.json().get("results", [])
        publicaciones = []
        for item_id in items[:10]:
            d = _req.get(f"https://api.mercadolibre.com/items/{item_id}",
                         headers={"Authorization": f"Bearer {token}"}).json()
            publicaciones.append({
                "id":        d.get("id"),
                "titulo":    d.get("title"),
                "precio":    d.get("price"),
                "estado":    d.get("status"),
                "vendidos":  d.get("sold_quantity", 0),
                "url":       d.get("permalink")
            })
        return {"ok": True, "total": len(items), "publicaciones": publicaciones}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.post("/api/meli/publicar-todo", tags=["MercadoLibre"])
async def meli_publicar_todo(solo_key: str = ""):
    """
    Publica catálogo Aozoom en ML.
    - Precio de lista (precio_publico)
    - 3-5 fotos limpias por producto (upscale 500px, sin texto)
    - Atributos completos: BRAND, PART_NUMBER, garantía, envíos Mercado Envíos
    - solo_key: si se indica (ej "AOZOOM_X1"), publica solo ese producto
    - Token auto-refresh incluido
    """
    import requests as _req, time as _time
    try:
        token = _meli_access_token()
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e),
                             "accion": "Abre http://localhost:8003/api/meli/auth y autoriza"}, status_code=503)

    catalog_path = "C:/NEXUS_v3_NEW/data/catalogo_atf.json"
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    prods = data["productos"]
    if solo_key:
        prods = {k: v for k, v in prods.items() if k == solo_key}

    # Cargar publicaciones previas para no duplicar
    pub_file = "C:/NEXUS_v3_NEW/data/ml_publicaciones.json"
    try:
        with open(pub_file, encoding="utf-8") as f:
            prev = json.load(f)
        ya_publicados = {p["key"]: p["id"] for p in prev.get("publicados", [])}
    except Exception:
        ya_publicados = {}

    publicados = []
    errores    = []

    # Categorías ML por tipo de producto
    def _ml_categoria(key: str) -> str:
        if key.startswith("ALO_") or key == "MAMMOTH_ASADOR":
            return "MLM192294"   # Accesorios y luces off-road
        return "MLM182686"       # Bombillas y luces LED para autos

    for key, prod in prods.items():
        if key in ya_publicados:
            publicados.append({"key": key, "id": ya_publicados[key], "omitido": True})
            continue

        nombre = prod["nombre"]
        specs  = prod.get("specs", {})
        # Título limpio sin "instalado" — max 60 chars
        titulo_base = nombre.split("—")[0].split("–")[0].strip()
        titulo = (titulo_base + " Proyector Bi-LED Retrofit ATF")[:60]
        desc = (
            f"{prod.get('descripcion_corta','')}\n\n"
            f"✅ PRODUCTO SIN INSTALACIÓN — Solo el kit de proyectores.\n"
            f"📦 Envíos lunes a viernes. Pedidos hasta el viernes 5:00 PM.\n"
            f"🔧 ¿Quieres instalación? Cotiza por teléfono, servicio bajo cita.\n"
            f"   📞 WA: 33 2353 0146 — ATF Actualiza Tus Faros, Guadalajara.\n\n"
            f"Especificaciones:\n" +
            "\n".join(f"• {k}: {v}" for k, v in specs.items()) +
            f"\n\n🛡️ Garantía: 12 meses contra defectos de fábrica.\n"
            f"Marca: Aozoom | Distribuidor Oficial ATF"
        )

        # CAR_LED_BULB_TYPE = tipo de conector; H7 es el más universal para retrofit
        conector = prod.get("specs", {}).get("conector", "H7")
        if conector not in ["D2S","H1","D2R","H5","H4","H3","H11","H16","H7","HB4","T10","T5"]:
            conector = "H7"
        attrs = [
            {"id": "BRAND",             "value_name": "Aozoom"},
            {"id": "PART_NUMBER",       "value_name": prod.get("codigo", key)},
            {"id": "CAR_LED_BULB_TYPE", "value_name": conector},
        ]

        # Supervisor de calidad — valida antes de publicar
        fotos_fns = _MELI_FOTOS_MAP.get(key, [f"aozoom_{key.split('_')[-1].lower()}.jpg"])
        fotos_paths = [os.path.join(_MELI_FOTOS_DIR, fn) for fn in fotos_fns]
        validacion = _ml_validar_producto(key, prod, fotos_paths)
        if not validacion["ok"]:
            msg = f"❌ {key} bloqueado por supervisor:\n" + "\n".join(validacion["errores"])
            _ml_alertar(msg)
            errores.append({"key": key, "status": "bloqueado_supervisor",
                            "error": "Supervisor rechazó el producto antes de publicar",
                            "detalles": validacion})
            continue
        if validacion["advertencias"]:
            logger.warning("SUPERVISOR %s advertencias: %s", key, validacion["advertencias"])

        fotos_ids = _meli_preparar_fotos(token, key)

        listing = {
            "title":              titulo,
            "category_id":        _ml_categoria(key),
            "price":              prod["precio_publico"],
            "currency_id":        "MXN",
            "available_quantity": 1,
            "buying_mode":        "buy_it_now",
            "condition":          "new",
            "listing_type_id":    "free",
            "description":        {"plain_text": desc},
            "attributes":         attrs,
            "shipping": {
                "mode":          "me2",
                "local_pick_up": True,
                "free_shipping": True,   # ME2 adoption obligatoria en esta categoría
            },
            "sale_terms": [
                {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
                {"id": "WARRANTY_TIME", "value_name": "12 meses"}
            ]
        }
        if fotos_ids:
            listing["pictures"] = fotos_ids

        r = _req.post(
            "https://api.mercadolibre.com/items",
            json=listing,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        if r.status_code in (200, 201):
            d = r.json()
            publicados.append({"key": key, "id": d.get("id"), "url": d.get("permalink")})
            logger.info("ML publicado %s → %s", key, d.get("id"))
        else:
            err = r.json()
            errores.append({"key": key, "status": r.status_code,
                            "error": err.get("message", ""), "cause": str(err.get("cause",""))[:120]})
            logger.warning("ML error %s %s: %s", key, r.status_code, r.text[:120])

        _time.sleep(3)

    # Guardar resultado
    resultado = {"publicados": publicados + [{"key": k, "id": v} for k, v in ya_publicados.items()
                                              if not any(p["key"]==k for p in publicados)],
                 "errores": errores}
    with open(pub_file, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return {
        "ok":         len(errores) == 0,
        "publicados": len(publicados),
        "omitidos":   sum(1 for p in publicados if p.get("omitido")),
        "errores":    len(errores),
        "items":      publicados,
        "fallos":     errores
    }

@app.post("/api/meli/publicar-instalacion", tags=["MercadoLibre"])
async def meli_publicar_instalacion():
    """Publica el servicio de instalación retrofit como listado ML."""
    import requests as _req
    try:
        token = _meli_access_token()
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)

    servicios = [
        {
            "titulo": "Instalación Retrofit Bi-LED Proyector Aozoom ATF",
            "precio": 1800,
            "desc": (
                "🔧 SERVICIO DE INSTALACIÓN RETROFIT BI-LED\n"
                "Instalación profesional de proyectores Bi-LED Aozoom en tu vehículo.\n\n"
                "✅ Incluye:\n"
                "• Desmontaje y montaje de faros\n"
                "• Instalación y alineación de proyectores\n"
                "• Prueba de funcionamiento\n"
                "• Sellado y acabado profesional\n\n"
                "📍 Servicio SOLO en Guadalajara, Jalisco — BAJO CITA.\n"
                "📞 Agenda tu cita: WA 33 2353 0146\n\n"
                "⚠️ NO incluye los proyectores (se cotizan aparte).\n"
                "⏱️ Tiempo estimado: 3-5 horas según vehículo.\n"
                "🛡️ Garantía de mano de obra: 3 meses.\n\n"
                "ATF — Actualiza Tus Faros | Especialistas en retrofit Guadalajara."
            ),
        },
        {
            "titulo": "Cotización Retrofit LED Faros Aozoom + Instalación ATF GDL",
            "precio": 100,  # precio simbólico para cotización
            "desc": (
                "💡 COTIZA TU RETROFIT COMPLETO (Kit + Instalación)\n\n"
                "Obtén precio exacto para tu vehículo con proyectores Bi-LED Aozoom.\n\n"
                "✅ ¿Qué incluye la cotización?\n"
                "• Diagnóstico de tus faros actuales\n"
                "• Recomendación del proyector ideal para tu auto\n"
                "• Precio total kit + instalación\n"
                "• Agendado de cita\n\n"
                "📍 Atención SOLO en Guadalajara — Bajo cita previa.\n"
                "📞 WA: 33 2353 0146\n\n"
                "Pago de esta publicación se descuenta del servicio total.\n"
                "ATF — Actualiza Tus Faros."
            ),
        },
    ]

    publicados = []
    for s in servicios:
        listing = {
            "title":              s["titulo"][:60],
            "category_id":        "MLM1743",  # Servicios para autos
            "price":              s["precio"],
            "currency_id":        "MXN",
            "available_quantity": 99,
            "buying_mode":        "buy_it_now",
            "condition":          "new",
            "listing_type_id":    "free",
            "description":        {"plain_text": s["desc"]},
            "shipping":           {"mode": "not_specified", "local_pick_up": True},
            "sale_terms":         [{"id": "WARRANTY_TYPE", "value_name": "Sin garantía"}],
        }
        r = _req.post(
            "https://api.mercadolibre.com/items",
            json=listing,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        if r.status_code in (200, 201):
            d = r.json()
            publicados.append({"titulo": s["titulo"][:40], "id": d.get("id"), "url": d.get("permalink")})
        else:
            publicados.append({"titulo": s["titulo"][:40], "error": r.text[:120]})

    return {"ok": True, "servicios": publicados}

# ══════════════════════════════════════════════════════════════
# SUPERVISOR DE CALIDAD ML
# ══════════════════════════════════════════════════════════════

# Políticas ML que el supervisor conoce
_ML_POLITICAS = {
    "titulo_max": 60,
    "titulo_prohibido": ["!", "?", "http", "@", "gratis", "oferta", "mejor precio", "garantizado"],
    "imagen_min_px": 500,
    "imagenes_max": 8,
    "imagenes_sin_texto": True,   # ML rechaza imágenes con texto superpuesto
    "attrs_requeridos": ["BRAND", "PART_NUMBER", "CAR_LED_BULB_TYPE"],
    "descripcion_min_chars": 100,
    "desc_prohibido": ["whatsapp.com", "http://", "https://", "facebook.com"],
    "cantidad_free": 1,           # free listing solo permite qty=1
    "garantia_requerida": True,
}

def _ml_alertar(msg: str):
    """Envía alerta al Telegram de Anuar."""
    import requests as _req
    bot = os.getenv("TELEGRAM_BOT_TOKEN","")
    chat = os.getenv("TELEGRAM_CHAT_ID","")
    if not bot or not chat:
        return
    try:
        _req.post(f"https://api.telegram.org/bot{bot}/sendMessage",
                  json={"chat_id": chat, "text": f"🔍 NEXUS Supervisor ML\n{msg}"},
                  timeout=5)
    except Exception:
        pass

def _ml_validar_producto(key: str, prod: dict, fotos_paths: list) -> dict:
    """
    Valida un producto contra políticas ML antes de publicar.
    Retorna {"ok": bool, "errores": [], "advertencias": []}
    """
    from PIL import Image as _PIL_IMG
    errores = []
    advertencias = []
    specs = prod.get("specs", {})

    # 1. Título
    nombre = prod.get("nombre","")
    titulo_base = nombre.split("—")[0].split("–")[0].strip()
    titulo = (titulo_base + " Proyector Bi-LED Retrofit ATF")[:60]
    if len(titulo) > _ML_POLITICAS["titulo_max"]:
        errores.append(f"Título demasiado largo: {len(titulo)} chars (max {_ML_POLITICAS['titulo_max']})")
    for palabra in _ML_POLITICAS["titulo_prohibido"]:
        if palabra.lower() in titulo.lower():
            advertencias.append(f"Título contiene palabra problemática: '{palabra}'")

    # 2. Descripción
    desc = prod.get("descripcion_corta","")
    if len(desc) < _ML_POLITICAS["descripcion_min_chars"]:
        advertencias.append(f"Descripción corta ({len(desc)} chars) — ML puede bajar visibilidad")
    for palabra in _ML_POLITICAS["desc_prohibido"]:
        if palabra in desc:
            errores.append(f"Descripción contiene URL/contacto externo: '{palabra}'")

    # 3. Precio
    precio = prod.get("precio_publico", 0)
    if precio <= 0:
        errores.append("Precio inválido (0 o negativo)")
    if precio < 100:
        advertencias.append(f"Precio muy bajo (${precio}) — puede ser rechazado")

    # 4. Atributos requeridos
    codigo = prod.get("codigo","")
    if not codigo:
        errores.append("Falta PART_NUMBER (código del producto)")

    # 5. Imágenes
    if not fotos_paths:
        errores.append("Sin imágenes — ML requiere al menos 1 foto")
    else:
        for fp in fotos_paths:
            if not os.path.exists(fp):
                advertencias.append(f"Imagen no encontrada: {os.path.basename(fp)}")
                continue
            try:
                img = _PIL_IMG.open(fp)
                w, h = img.size
                if w < _ML_POLITICAS["imagen_min_px"] or h < _ML_POLITICAS["imagen_min_px"]:
                    advertencias.append(f"Imagen pequeña {w}×{h}px: {os.path.basename(fp)} (min {_ML_POLITICAS['imagen_min_px']}px)")
                # Detectar si viene de PDF (probablemente tiene texto)
                if "pdf_p" in os.path.basename(fp):
                    errores.append(f"Imagen de PDF con texto superpuesto: {os.path.basename(fp)} — ML rechaza imágenes con texto")
            except Exception as e:
                advertencias.append(f"No se pudo leer imagen {os.path.basename(fp)}: {e}")

        if len(fotos_paths) > _ML_POLITICAS["imagenes_max"]:
            errores.append(f"Demasiadas imágenes ({len(fotos_paths)}) — max {_ML_POLITICAS['imagenes_max']}")

    ok = len(errores) == 0
    return {"ok": ok, "errores": errores, "advertencias": advertencias, "titulo_generado": titulo}

@app.get("/api/meli/supervisor", tags=["MercadoLibre"])
async def meli_supervisor():
    """
    Supervisor de calidad ML:
    1. Valida catálogo pendiente de publicar (pre-publish)
    2. Audita publicaciones activas en ML (post-publish)
    3. Alerta por Telegram si hay problemas
    """
    import requests as _req

    catalog_path = "C:/NEXUS_v3_NEW/data/catalogo_atf.json"
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    prods = {k: v for k, v in data["productos"].items() if k.startswith("AOZOOM")}

    # --- PRE-PUBLISH: validar catálogo ---
    pre_resultados = {}
    for key, prod in prods.items():
        fotos = _MELI_FOTOS_MAP.get(key, [f"aozoom_{key.split('_')[-1].lower()}.jpg"])
        fotos_paths = [os.path.join(_MELI_FOTOS_DIR, fn) for fn in fotos]
        pre_resultados[key] = _ml_validar_producto(key, prod, fotos_paths)

    pre_errores = {k: v for k, v in pre_resultados.items() if not v["ok"]}
    pre_ok      = {k: v for k, v in pre_resultados.items() if v["ok"]}

    # --- POST-PUBLISH: auditar publicaciones activas ---
    pub_file = "C:/NEXUS_v3_NEW/data/ml_publicaciones.json"
    post_resultados = {}
    try:
        token = _meli_access_token()
        with open(pub_file, encoding="utf-8") as f:
            pub_data = json.load(f)
        publicados = [p for p in pub_data.get("publicados", []) if not p.get("omitido") and p.get("id")]
        for p in publicados:
            item_id = p["id"]
            r = _req.get(f"https://api.mercadolibre.com/items/{item_id}",
                         headers={"Authorization": f"Bearer {token}"}, timeout=8)
            if r.ok:
                d = r.json()
                estado = {
                    "status":     d.get("status"),
                    "health":     d.get("health"),
                    "warnings":   d.get("warnings", []),
                    "fotos":      len(d.get("pictures", [])),
                    "tiene_desc": False,
                }
                # Verificar descripción
                rd = _req.get(f"https://api.mercadolibre.com/items/{item_id}/description",
                              headers={"Authorization": f"Bearer {token}"}, timeout=5)
                if rd.ok:
                    estado["tiene_desc"] = bool(rd.json().get("plain_text","").strip())
                post_resultados[p["key"]] = {"item_id": item_id, **estado}
    except Exception as e:
        post_resultados["_error"] = str(e)

    # --- ALERTAS ---
    alertas = []
    for key, res in pre_errores.items():
        for err in res["errores"]:
            alertas.append(f"❌ {key}: {err}")
    for key, res in post_resultados.items():
        if key.startswith("_"): continue
        if res.get("status") != "active":
            alertas.append(f"⚠️ {key} ({res['item_id']}): estado={res.get('status')}")
        if not res.get("tiene_desc"):
            alertas.append(f"⚠️ {key} ({res['item_id']}): sin descripción")
        if res.get("warnings"):
            alertas.append(f"⚠️ {key}: ML warnings={res['warnings']}")

    if alertas:
        msg = "Supervisión ML — se encontraron problemas:\n" + "\n".join(alertas[:15])
        _ml_alertar(msg)
        logger.warning("SUPERVISOR ML: %d alertas enviadas", len(alertas))

    return {
        "ok": len(alertas) == 0,
        "pre_publish": {
            "listos":   list(pre_ok.keys()),
            "con_error": pre_errores,
        },
        "post_publish": post_resultados,
        "alertas": alertas,
        "alertas_telegram": len(alertas) > 0,
    }

@app.get("/api/meli/preguntas", tags=["MercadoLibre"])
async def meli_preguntas():
    """Preguntas sin responder en ML."""
    import requests as _req
    try:
        token = _meli_access_token()
        r = _req.get(
            "https://api.mercadolibre.com/questions/search",
            params={"status": "UNANSWERED"},
            headers={"Authorization": f"Bearer {token}"}
        )
        preguntas = r.json().get("questions", [])
        return {
            "ok":       True,
            "total":    len(preguntas),
            "preguntas": [{
                "id":       p.get("id"),
                "texto":    p.get("text"),
                "item_id":  p.get("item_id"),
                "fecha":    p.get("date_created","")[:10]
            } for p in preguntas]
        }
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/sistema/ram", tags=["Sistema"])
async def sistema_ram():
    """RAM en tiempo real: NEXUS + todos los motores + sistema."""
    import psutil, os as _os
    procesos = []
    total_nexus = 0
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if 'python' not in p.info['name'].lower():
                continue
            cmd = ' '.join(p.info['cmdline'] or [])
            if 'spawn_main' in cmd:
                continue
            mb = round(p.info['memory_info'].rss / 1024 / 1024, 1)
            nombre = 'nexus_core' if 'nexus_core' in cmd else cmd.split('\\')[-1].split('/')[-1][:30]
            procesos.append({"proceso": nombre, "pid": p.pid, "mb": mb})
            total_nexus += mb
        except Exception:
            pass
    mem = psutil.virtual_memory()
    return {
        "ok": True,
        "sistema": {
            "total_gb":   round(mem.total / 1024**3, 1),
            "libre_mb":   round(mem.available / 1024 / 1024),
            "usado_pct":  mem.percent,
        },
        "nexus": {
            "total_mb":   round(total_nexus, 1),
            "procesos":   sorted(procesos, key=lambda x: -x["mb"])
        }
    }

# ══════════════════════════════════════════════════════════════
#  EDITOR — proxy a motor_editor:8012
# ══════════════════════════════════════════════════════════════
@app.get("/editor", response_class=HTMLResponse)
async def editor_ui(request: Request):
    html_path = os.path.join(os.path.dirname(__file__), "templates", "editor.html")
    return HTMLResponse(open(html_path, encoding="utf-8").read())

@app.api_route("/editor/api/{path:path}", methods=["GET", "POST"])
async def editor_proxy(path: str, request: Request):
    import httpx
    url = f"http://localhost:8012/{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=90) as hx:
        r = await hx.request(request.method, url, content=body, headers={"Content-Type":"application/json"})
    return JSONResponse(r.json())


# ══════════════════════════════════════════════════════════════
#  MAQUILA — proxy a motor_maquila:8011
# ══════════════════════════════════════════════════════════════
@app.get("/maquila", response_class=HTMLResponse)
async def maquila_ui(request: Request):
    html_path = os.path.join(os.path.dirname(__file__), "templates", "maquila.html")
    return HTMLResponse(open(html_path, encoding="utf-8").read())

@app.api_route("/maquila/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def maquila_proxy(path: str, request: Request):
    import httpx
    url = f"http://localhost:8011/{path}" if path != "execute" else "http://localhost:8011/execute"
    body = await request.body()
    async with httpx.AsyncClient(timeout=60) as hx:
        r = await hx.request(request.method, url, content=body, headers={"Content-Type":"application/json"})
    return JSONResponse(r.json())


# ══════════════════════════════════════════════════════════════
#  AGENTE — proxy a motor_agente:8010
# ══════════════════════════════════════════════════════════════
@app.get("/agente", response_class=HTMLResponse)
async def agente_ui(request: Request):
    html_path = os.path.join(os.path.dirname(__file__), "templates", "agente.html")
    return HTMLResponse(open(html_path, encoding="utf-8").read())

@app.api_route("/agente/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def agente_proxy(path: str, request: Request):
    import httpx
    if path == "execute":
        url = "http://localhost:8010/execute"
    else:
        url = f"http://localhost:8010/{path}"
    body = await request.body()
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=120) as hx:
        r = await hx.request(request.method, url, content=body, headers=headers)
    return JSONResponse(r.json())


# ══════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("\033[92m Iniciando NEXUS v3 by Simplex...\033[0m")
    port = int(os.getenv("NEXUS_PORT", 8003))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

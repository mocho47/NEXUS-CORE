# -*- coding: utf-8 -*-
"""
NEXUS CLOUD — Servidor standalone para deploy en la nube
Render / Railway / Fly.io — puerto dinamico via $PORT

Incluye:
  - NEXUS Teens (completo: tutor IA, misiones, aptitudes, viral, guion)
  - NEXUS Cerebro (chat general)
  - ATF / CanbusFix paginas publicas
  - Health check

Minimal deps: fastapi, uvicorn, groq, jinja2, python-dotenv, python-multipart, httpx
NO requiere: opencv, faster-whisper, moviepy, pygame, win32com, edge-tts

Variables de entorno requeridas:
  GROQ_API_KEY = sk-...
  NEXUS_ENV    = cloud  (activa modo cloud)
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus_cloud")

# ── RUTAS ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
TEMPLATES  = Jinja2Templates(directory=str(BASE_DIR / "WEB" / "templates"))
STATIC_DIR = BASE_DIR / "WEB" / "static"

app = FastAPI(title="NEXUS by Simplex — Cloud", docs_url=None, redoc_url=None)

# ── SEGURIDAD — Headers anti-copia / anti-embed ───────────────────────────────
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Powered-By"] = "NEXUS by Simplex"
        # Solo páginas HTML — bloquear cache de código fuente
        if "text/html" in response.headers.get("content-type", ""):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response

app.add_middleware(SecurityHeadersMiddleware)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── DASHBOARD / ROOT ──────────────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    try:
        return TEMPLATES.TemplateResponse("dashboard.html", {"request": request})
    except Exception:
        return HTMLResponse("""
        <html><head><meta charset="utf-8"><title>NEXUS by Simplex</title>
        <style>body{background:#050d08;color:#00ff88;font-family:monospace;
        display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:20px}
        h1{font-size:2.5em;letter-spacing:4px}p{color:#666}
        a{color:#00cfff;text-decoration:none;padding:12px 24px;border:1px solid #00cfff;border-radius:8px}
        </style></head>
        <body>
        <h1>NEXUS</h1>
        <p>by Simplex — Guadalajara</p>
        <a href="/teens">NEXUS Teens</a>
        <a href="/atf">ATF by Simplex</a>
        </body></html>
        """)

@app.get("/dashboard")
async def dashboard(request: Request):
    try:
        return TEMPLATES.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        return JSONResponse({"error": str(e)})

@app.get("/admin")
async def admin_panel(request: Request):
    return TEMPLATES.TemplateResponse("nexus_admin_panel.html", {"request": request})

@app.get("/health")
@app.get("/api/health")
async def health():
    return {"ok": True, "version": "cloud", "ts": datetime.now().isoformat()}

# ── NEXUS TEENS ───────────────────────────────────────────────────────────────
@app.get("/teens", response_class=HTMLResponse)
async def teens_view(request: Request):
    return TEMPLATES.TemplateResponse("teens.html", {"request": request})

@app.get("/teens/instalar", response_class=HTMLResponse)
async def teens_instalar(request: Request):
    return TEMPLATES.TemplateResponse("teens_bienvenida.html", {"request": request})

@app.get("/teens_sw.js")
async def teens_sw():
    sw_path = STATIC_DIR / "teens_sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})
    return JSONResponse({"error": "sw not found"}, status_code=404)

# Models
class TeensUserReq(BaseModel):
    user_id: str
    nombre:  str = "Teen"
    edad:    int = 17

class TeensMisionReq(BaseModel):
    user_id:   str
    mision_id: str

class TutorReq(BaseModel):
    mensaje: str
    user_id: str = "default"
    emocion: str = ""
    etapa:   str = ""

class TeensParentalReq(BaseModel):
    user_id: str
    pin:     str
    config:  dict

# API Routes
@app.post("/api/teens/usuario")
async def api_teens_usuario(req: TeensUserReq):
    try:
        from nexus_teens import registrar_usuario
        return registrar_usuario(req.user_id, req.nombre, req.edad)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/perfil/{user_id}")
async def api_teens_perfil(user_id: str):
    try:
        from nexus_teens import get_perfil
        return get_perfil(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/misiones/{user_id}")
async def api_teens_misiones(user_id: str):
    try:
        from nexus_teens import get_misiones
        return get_misiones(user_id)
    except Exception as e:
        return []

@app.post("/api/teens/completar")
async def api_teens_completar(req: TeensMisionReq):
    try:
        from nexus_teens import completar_mision
        return completar_mision(req.user_id, req.mision_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/impulsar/{user_id}/{aptitud}")
async def api_teens_impulsar(user_id: str, aptitud: str):
    try:
        from nexus_teens import impulsar_aptitud
        return impulsar_aptitud(user_id, aptitud)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/viral/{aptitud}")
async def api_teens_viral(aptitud: str, nombre_negocio: str = "", edad: int = 17):
    try:
        from nexus_teens import generar_idea_viral
        return generar_idea_viral(aptitud, nombre_negocio, edad)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/guion")
async def api_teens_guion(tema: str = "mi contenido", aptitud: str = "general", duracion: int = 60):
    try:
        from nexus_teens import generar_guion_reel
        return generar_guion_reel(tema, aptitud, duracion)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/tutor")
async def api_teens_tutor(req: TutorReq):
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

        etapa_ctx = ""
        if req.etapa == "secundaria":
            etapa_ctx = "La teen está en secundaria (12-14 años). Usa ejemplos de su mundo inmediato: salón, amigos, familia, redes. Lenguaje muy simple. "
        elif req.etapa == "prepa":
            etapa_ctx = "La teen está en prepa (15-17 años). Puede hablar de dinero, decisiones de vida, presión social, identidad. Lenguaje directo. "
        elif req.etapa == "adulto":
            etapa_ctx = "Ya está en etapa de mayor independencia (17+). Puede hablar de trabajo, emprendimiento real, relaciones adultas, autonomía financiera. "

        if req.emocion:
            system = (
                f"{etapa_ctx}"
                "Eres el acompañante de NEXUS Teens. La chava parece sentir algo difícil "
                f"— señal detectada: {req.emocion}. "
                "Tu trabajo: escuchar de verdad. "
                "1. Empieza validando lo que siente, 1 frase honesta. Nunca: 'entiendo cómo te sientes', 'todo va a estar bien'. "
                "2. Haz UNA sola pregunta abierta, sin presionar. "
                "3. Ofrece 2 opciones: seguir hablando o hacer pausa. "
                "4. Nunca des consejos no pedidos. Nunca minimices. "
                "Si detectas crisis real, sugiere hablar con alguien de confianza en persona. "
                "Tono: hermano mayor/prima que escucha. Máximo 3 párrafos cortos."
            )
        else:
            system = (
                f"{etapa_ctx}"
                "Eres el acompañante de NEXUS Teens — ese hermano mayor o prima que ya pasó por esto "
                "y habla sin rodeos. Entiendes la presión social, la familia, la economía, el sistema. "
                "VISIÓN QUE ENCARNAS (solo cuando viene al caso): "
                "Siempre hay opciones aunque todo parezca cerrado. Todo tiene un precio, incluso lo correcto. "
                "Nadie viene a hacer lo que te corresponde — eso es liberador, no una amenaza. "
                "La disciplina que te pones tú mismo vale infinitamente más que cualquier regla impuesta. "
                "REGLAS: Directo, relajado, humor natural mexicano. NUNCA ordenas ni aconsejas directo. "
                "Termina con 2 opciones: 'Opción A: ... / Opción B: ... — ¿cuál te late más?' "
                "Máximo 4 párrafos cortos. Sin listas largas. Máximo 2 emojis."
            )

        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system},
                      {"role": "user",   "content": req.mensaje}],
            max_tokens=400,
        )
        return {"ok": True, "respuesta": chat.choices[0].message.content}
    except Exception as e:
        return {
            "ok": True,
            "respuesta": "Buena pregunta. Para profundizar: busca el tema en YouTube + '2025', practica 10 minutos. El aprendizaje real viene de la acción. (Modo offline — reconecta para respuestas completas)"
        }

@app.get("/api/teens/leaderboard")
async def api_teens_leaderboard():
    try:
        from nexus_teens import get_leaderboard
        return get_leaderboard()
    except Exception as e:
        return []

@app.post("/api/teens/parental")
async def api_teens_parental(req: TeensParentalReq):
    try:
        from nexus_teens import control_parental_update
        return control_parental_update(req.user_id, req.pin, req.config)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/familia/{user_id}")
async def api_teens_familia(user_id: str):
    try:
        from nexus_teens import get_perfil
        p = get_perfil(user_id)
        return {"ok": True, "codigo_familia": p.get("codigo_familia"), "perfil": p.get("nombre")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/admin/usuarios")
async def api_teens_admin_usuarios(pin: str = ""):
    try:
        from nexus_teens import _cargar_datos
        datos = _cargar_datos()
        usuarios = datos.get("usuarios", {})
        return {
            "ok": True,
            "total": len(usuarios),
            "usuarios": [
                {"id": uid, "nombre": u.get("nombre","?"), "edad": u.get("edad",0),
                 "xp": u.get("xp_total",0), "ultimo_acceso": u.get("ultimo_acceso","")}
                for uid, u in list(usuarios.items())[-50:]
            ]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── NEXUS CEREBRO — Chat general ──────────────────────────────────────────────
class AsistenteReq(BaseModel):
    texto:      str
    session_id: str = "cloud"

@app.post("/api/asistente")
async def api_asistente(req: AsistenteReq):
    try:
        from nexus_cerebro import get_cerebro
        return get_cerebro().pensar(req.texto)
    except Exception as e:
        return {"respuesta": f"Error: {e}", "accion": "error", "params": {}}

# Endpoint para beta/teens — usa cerebro completo pero filtra acciones de admin
_ACCIONES_SOLO_ADMIN = {"abrir_corel","ejecutar_macro","backup","licencia","crear_admin",
                        "admin","logout_admin","set_config_tier","set_precio","cambiar_pin"}

@app.post("/api/asistente/beta")
async def api_asistente_beta(req: AsistenteReq):
    """Beta y Teens: IA completa, sin acceso a acciones de admin ni sistema."""
    try:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            return {"respuesta": "Sin conexión con el cerebro por ahora.", "accion": "conversar", "params": {}}
        from groq import Groq
        client = Groq(api_key=groq_key)
        system = (
            "Eres NEXUS, asistente de inteligencia artificial de Simplex. "
            "Ayudas al usuario a resolver dudas, navegar su día, dar ideas de negocio, "
            "responder mensajes, buscar información y operar con inteligencia. "
            "Eres directo, sin relleno, con carácter. Guadalajara, México. "
            "NO puedes ejecutar comandos del sistema, NO tienes acceso al panel admin, "
            "NO puedes ver datos de otros usuarios. Solo ayudas al usuario frente a ti. "
            "Si preguntan por funciones premium: 'Eso está disponible en la versión completa.' "
            "Responde en español, máximo 3 párrafos."
        )
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": req.texto}],
            max_tokens=400, temperature=0.7
        )
        resp = chat.choices[0].message.content or "Sin respuesta."
        return {"respuesta": resp, "accion": "conversar", "params": {}}
    except Exception as e:
        return {"respuesta": f"Error: {e}", "accion": "error", "params": {}}

# ── BETA / MANUAL ─────────────────────────────────────────────────────────────
@app.get("/bienvenida", response_class=HTMLResponse)
async def bienvenida(request: Request):
    return TEMPLATES.TemplateResponse("bienvenida_beta.html", {"request": request})

@app.get("/manual", response_class=HTMLResponse)
async def manual(request: Request):
    return TEMPLATES.TemplateResponse("manual_beta.html", {"request": request})

@app.get("/manual/admin", response_class=HTMLResponse)
async def manual_admin(request: Request):
    return TEMPLATES.TemplateResponse("manual_admin.html", {"request": request})

@app.get("/teens/manual", response_class=HTMLResponse)
async def manual_teens(request: Request):
    return TEMPLATES.TemplateResponse("manual_teens.html", {"request": request})

# ── ATF PUBLICA ───────────────────────────────────────────────────────────────
@app.get("/atf", response_class=HTMLResponse)
async def atf_view(request: Request):
    try:
        return TEMPLATES.TemplateResponse("atf.html", {"request": request})
    except Exception:
        return HTMLResponse("<h1>ATF by Simplex</h1><p>Retrofit faros Guadalajara. WA: 3326148674</p>")

@app.get("/canbusfix", response_class=HTMLResponse)
async def canbusfix_view(request: Request):
    try:
        return TEMPLATES.TemplateResponse("canbusfix.html", {"request": request})
    except Exception:
        return HTMLResponse("<h1>CanbusFix</h1><p>Red instaladores retrofit. WA: 3326148674</p>")

# ── STARTUP ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("NEXUS Cloud arriba — modo cloud activo")
    logger.info(f"GROQ_API_KEY: {'OK' if os.environ.get('GROQ_API_KEY') else 'FALTA'}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("nexus_cloud:app", host="0.0.0.0", port=port, reload=False)

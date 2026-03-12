# -*- coding: utf-8 -*-
"""
nexus_teens_server.py — Servidor independiente NEXUS Teens
===========================================================
Distribucion separada del modulo Teens.
Puerto: 8100 (no conflicta con NEXUS principal en 8000)

Arranca: python nexus_teens_server.py
EXE:     NEXUS_Teens.exe
URL:     http://localhost:8100/teens
"""

import os
import sys
import json
import webbrowser
import threading
import time
from pathlib import Path

# ── Rutas portables ───────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(sys.executable).parent / "NEXUS_Teens_Data"
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR

DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR = DATA_DIR / "CONFIG"
CONFIG_DIR.mkdir(exist_ok=True)

# Inyectar rutas para que nexus_teens las encuentre
os.environ.setdefault("NEXUS_BASE_DIR", str(BASE_DIR))
os.environ.setdefault("NEXUS_CONFIG_DIR", str(CONFIG_DIR))

# ── FastAPI ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="NEXUS Teens", version="2026.1")

TEMPLATES_DIR = BASE_DIR / "WEB" / "templates"
STATIC_DIR    = BASE_DIR / "WEB" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Importar motor Teens ──────────────────────────────────────────────────────
import nexus_teens as _teens

# ── Rutas HTML ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/teens", response_class=HTMLResponse)
async def teens_home(request: Request):
    return templates.TemplateResponse("teens.html", {"request": request})

@app.get("/teens/admin", response_class=HTMLResponse)
async def teens_admin(request: Request):
    return templates.TemplateResponse("teens_admin.html", {"request": request})

@app.get("/teens/bienvenida", response_class=HTMLResponse)
async def teens_bienvenida(request: Request):
    return templates.TemplateResponse("teens_bienvenida.html", {"request": request})

@app.get("/teens/instalar", response_class=HTMLResponse)
async def teens_instalar():
    html = """<!DOCTYPE html><html><head><meta charset='utf-8'>
    <title>NEXUS Teens — Instalar</title>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <meta name='theme-color' content='#1a0a2e'>
    <link rel='manifest' href='/teens_manifest.json'>
    </head><body style='background:#0d0118;color:#fff;font-family:sans-serif;text-align:center;padding:2rem'>
    <h2>NEXUS Teens</h2>
    <p>Para instalar como app: abre en Chrome/Edge → menú → "Instalar aplicación"</p>
    <a href='/teens' style='color:#b39ddb'>← Ir a NEXUS Teens</a>
    </body></html>"""
    return HTMLResponse(html)

# ── API Teens (todos los endpoints) ──────────────────────────────────────────
@app.post("/api/teens/usuario", response_class=JSONResponse)
async def api_usuario(request: Request):
    try:
        b = await request.json()
        return _teens.registrar_usuario(b["user_id"], b["nombre"], b.get("edad", 16))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/perfil/{user_id}", response_class=JSONResponse)
async def api_perfil(user_id: str):
    try:
        return _teens.get_perfil(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/misiones/{user_id}", response_class=JSONResponse)
async def api_misiones(user_id: str, frecuencia: str = None):
    try:
        return {"ok": True, "misiones": _teens.get_misiones(user_id, frecuencia)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/completar", response_class=JSONResponse)
async def api_completar(request: Request):
    try:
        b = await request.json()
        return _teens.completar_mision(b["user_id"], b["mision_id"])
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/impulsar/{user_id}/{aptitud}", response_class=JSONResponse)
async def api_impulsar(user_id: str, aptitud: str):
    try:
        return _teens.impulsar_aptitud(user_id, aptitud)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/viral/{aptitud}", response_class=JSONResponse)
async def api_viral(aptitud: str, negocio: str = "", edad: int = 17):
    try:
        return _teens.generar_idea_viral(aptitud, negocio, edad)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/guion", response_class=JSONResponse)
async def api_guion(tema: str = "", aptitud: str = "general", duracion: int = 60):
    try:
        return _teens.generar_guion_reel(tema, aptitud, duracion)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/tutor", response_class=JSONResponse)
async def api_tutor(request: Request):
    try:
        b = await request.json()
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return {"ok": False, "error": "Sin GROQ_API_KEY"}
        client = Groq(api_key=key)
        tema = b.get("tema", "")
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un tutor joven, claro y motivador para adolescentes. Explica en espanol mexicano."},
                {"role": "user", "content": f"Explica brevemente: {tema}. Luego da 3 preguntas de quiz con respuesta."}
            ],
            max_tokens=500,
        )
        return {"ok": True, "respuesta": r.choices[0].message.content}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/leaderboard", response_class=JSONResponse)
async def api_leaderboard():
    try:
        return {"ok": True, "leaderboard": _teens.get_leaderboard()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/parental", response_class=JSONResponse)
async def api_parental(request: Request):
    try:
        b = await request.json()
        return _teens.control_parental_update(b["user_id"], b.get("pin","0000"), b.get("config",{}))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/familia/{user_id}", response_class=JSONResponse)
async def api_familia(user_id: str):
    try:
        datos = _teens._cargar_datos()
        familia = {k: v for k, v in datos.get("usuarios", {}).items()
                   if v.get("familia") == datos.get("usuarios", {}).get(user_id, {}).get("familia")}
        return {"ok": True, "familia": list(familia.keys())}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/admin/usuarios", response_class=JSONResponse)
async def api_admin_usuarios():
    try:
        datos = _teens._cargar_datos()
        usuarios = []
        for uid, p in datos.get("usuarios", {}).items():
            usuarios.append({
                "user_id": uid, "nombre": p.get("nombre", uid),
                "nivel": p.get("nivel", 1), "xp": p.get("xp_total", 0),
                "racha": p.get("racha_dias", 0),
            })
        return {"ok": True, "usuarios": usuarios}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/monitor/{user_id}", response_class=JSONResponse)
async def api_monitor(user_id: str):
    try:
        p = _teens.get_perfil(user_id)
        checkins = _teens.get_checkins_semana(user_id)
        return {"ok": True, "perfil": p.get("perfil"), "checkins": checkins}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/acuerdo/crear", response_class=JSONResponse)
async def api_acuerdo_crear(request: Request):
    try:
        b = await request.json()
        return _teens.crear_acuerdo(b["user_id"], b["titulo"], b["descripcion"],
                                    b.get("recompensa", ""), b.get("pin_padre", "0000"),
                                    b.get("tipo", "compromiso"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/acuerdos/{user_id}", response_class=JSONResponse)
async def api_acuerdos(user_id: str):
    try:
        return _teens.get_acuerdos(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/acuerdo/resolver", response_class=JSONResponse)
async def api_acuerdo_resolver(request: Request):
    try:
        b = await request.json()
        return _teens.resolver_acuerdo(b["user_id"], b["acuerdo_id"],
                                       b.get("cumplido", True), b.get("pin_padre", "0000"),
                                       b.get("nota", ""))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/checkin", response_class=JSONResponse)
async def api_checkin(request: Request):
    try:
        b = await request.json()
        return _teens.registrar_checkin(b["user_id"], b["estado"], b.get("nota", ""))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/checkins/{user_id}", response_class=JSONResponse)
async def api_checkins(user_id: str):
    try:
        return _teens.get_checkins_semana(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/reconocimiento", response_class=JSONResponse)
async def api_reconocimiento(request: Request):
    try:
        b = await request.json()
        return _teens.dar_reconocimiento(b["user_id"], b["tipo"], b.get("nota", ""),
                                         b.get("de_quien", "familia"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/privilegios/{user_id}", response_class=JSONResponse)
async def api_privilegios(user_id: str):
    try:
        return _teens.get_privilegios(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/canje", response_class=JSONResponse)
async def api_canje(request: Request):
    try:
        b = await request.json()
        return _teens.canjear_privilegio(b["user_id"], b["privilegio_id"],
                                         b.get("pin_padre", "0000"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/codigo_honor", response_class=JSONResponse)
async def api_honor_save(request: Request):
    try:
        b = await request.json()
        return _teens.guardar_codigo_honor(b["user_id"], b["frases"], b.get("pin_padre", "0000"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/codigo_honor/{user_id}", response_class=JSONResponse)
async def api_honor_get(user_id: str):
    try:
        return _teens.get_codigo_honor(user_id)
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/valores", response_class=JSONResponse)
async def api_valores():
    try:
        return {"ok": True, "aptitudes": _teens.get_aptitudes_catalogo()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/teens/reconocimiento_leido", response_class=JSONResponse)
async def api_reconocimiento_leido(request: Request):
    try:
        b = await request.json()
        datos = _teens._cargar_datos()
        uid = b.get("user_id", "")
        if uid in datos.get("usuarios", {}):
            for r in datos["usuarios"][uid].get("reconocimientos", []):
                r["leido"] = True
            _teens._guardar_datos(datos)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/teens/aptitudes/{user_id}", response_class=JSONResponse)
async def api_aptitudes(user_id: str):
    try:
        p = _teens.get_perfil(user_id)
        return {"ok": True, "aptitudes": p.get("perfil", {}).get("aptitudes", {})}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/health", response_class=JSONResponse)
async def health():
    return {"ok": True, "app": "NEXUS Teens", "version": "2026.1", "puerto": 8100}

# ── Arranque ──────────────────────────────────────────────────────────────────
def _abrir_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8100/teens")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("=" * 50)
    print("  NEXUS Teens v2026 — by Simplex")
    print("  http://localhost:8100/teens")
    print("=" * 50)
    # Abrir browser automaticamente
    threading.Thread(target=_abrir_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8100)

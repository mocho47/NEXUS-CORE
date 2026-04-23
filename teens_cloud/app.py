"""
NEXUS Teens — Servidor standalone para Railway/cloud
Combina motor_teens + rutas web en un solo proceso
"""
import os, time, uuid, json, asyncio, logging, hashlib
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("teens")

PORT         = int(os.getenv("PORT", 8005))
DB_PATH      = os.getenv("TEENS_DB", "/data/teens.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ZAI_API_KEY  = os.getenv("ZAI_API_KEY", "")

app = FastAPI(title="NEXUS Teens")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Detección de riesgo ───────────────────────────────────────────────────────
RIESGO_VITAL = [
    "suicid","me quiero morir","hacerme daño","cortarme","no quiero vivir",
    "quitarme la vida","mejor muerto","desaparecer para siempre","me voy a hacer algo",
    "mejor no estuviera","no quiero estar aquí","ya no quiero estar",
    "me voy a lastimar","no tiene caso seguir","no vale la pena vivir",
    "quisiera dormirme y no despertar","todos estarían mejor sin mí"
]
TEMAS_SENSIBLES = {
    "riesgo_medio": ["drogas","marihuana","mota","feto","porro","pastillas pa ponerse",
                     "me están obligando","me tocó","abuso","me forzaron"],
    "emocional":    ["me odio","nadie me quiere","no valgo","soy un fracaso","lloro solo"],
    "relaciones":   ["primera vez","relaciones sexuales","condón","embarazo",
                     "me mandó fotos","me pidió fotos"],
    "bullying":     ["me pegan","me molestan","me humillan","me acosan",
                     "me hacen menos","se burlan de mí","me amenazan"],
}
SUGERENCIAS_PADRES = {
    "riesgo_medio": "Puede estar enfrentando presión de grupo. Conversación sin juicio.",
    "emocional":    "Expresó algo sobre cómo se siente. Un '¿cómo estás de verdad?' genuino puede abrir mucho.",
    "relaciones":   "Surgió tema de relaciones. Conversación abierta, sin drama.",
    "bullying":     "Algo pasa en su entorno social. Escucha primero.",
}

PROMPT_TEEN = """<role_definition>
Eres NEXUS. No eres amigo de {nombre}, no eres su padre, no eres su terapeuta.
Eres un espacio neutral con sesgo de lealtad hacia {nombre}.
</role_definition>
<reglas>
1. CERO TERMINOLOGÍA CLÍNICA. Traduce la jerga clínica a lenguaje real.
2. RESPUESTAS CORTAS. Máximo 3 líneas.
3. CERO EMPATÍA FALSA. Empieza directo o validando el hecho.
4. TÚ NO RESUELVES. Eres espejo. Si preguntan qué hacer, devuelve la pregunta.
5. SILENCIO Y RESISTENCIA: si responde con monosílabos, no insistas.
</reglas>
<tutor_mode>
Si pregunta sobre materias: Paso 1: qué cree que es la respuesta. Paso 2: un ejemplo paralelo. Paso 3: que conecte los puntos — nunca los conectes tú.
</tutor_mode>
<risk_protocol>
Si {nombre} menciona autolesión o abuso: Para el flujo. Di exactamente: "Oye, lo que acabas de decir no lo voy a guardar solo. Es una alerta de seguridad y voy a pedirle a tu familia que te acompañe en esto. No es para castigarte — es para que no cargues solo con eso."
</risk_protocol>
<user_state>Nombre: {nombre}, {edad} años. Último humor: {last_mood}. Tema activo: {active_context}.</user_state>
Respuesta inicial obligatoria (solo primer mensaje): "Aquí estoy. Qué hay." — nada más."""

PROMPT_PADRE = """Eres el aliado de {nombre} en la crianza de {teen}.
Das opciones reales — comunicación no violenta, crianza con límites. No ordenas, no juzgas.
ACUERDOS ACTIVOS: {acuerdos}
SEÑALES RECIENTES: {alertas}
Máximo 4 líneas."""

# ── DB ────────────────────────────────────────────────────────────────────────
async def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS familias (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, codigo_acceso TEXT UNIQUE, creado REAL);
            CREATE TABLE IF NOT EXISTS miembros (id TEXT PRIMARY KEY, familia_id TEXT NOT NULL, nombre TEXT NOT NULL, rol TEXT NOT NULL, edad INTEGER DEFAULT 15, pin_hash TEXT, puntos_total INTEGER DEFAULT 0, memoria_json TEXT DEFAULT '{}', active_context TEXT DEFAULT '{}', activo INTEGER DEFAULT 1, creado REAL);
            CREATE TABLE IF NOT EXISTS mood_history (id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL, score INTEGER NOT NULL, nota TEXT, creado REAL);
            CREATE TABLE IF NOT EXISTS misiones (id TEXT PRIMARY KEY, familia_id TEXT NOT NULL, titulo TEXT NOT NULL, descripcion TEXT, puntos INTEGER DEFAULT 10, asignado_a TEXT, estado TEXT DEFAULT 'pendiente', evidencia_url TEXT, aprobado_por TEXT, creado REAL, completado REAL, aprobado REAL);
            CREATE TABLE IF NOT EXISTS acuerdos (id TEXT PRIMARY KEY, familia_id TEXT NOT NULL, teen_id TEXT NOT NULL, descripcion TEXT NOT NULL, condicion TEXT, recompensa TEXT, propuesto_por TEXT DEFAULT 'padre', estado TEXT DEFAULT 'propuesto', creado REAL, cumplido REAL);
            CREATE TABLE IF NOT EXISTS alertas (id TEXT PRIMARY KEY, familia_id TEXT NOT NULL, teen_id TEXT NOT NULL, tipo TEXT NOT NULL, resumen TEXT, sugerencia TEXT, visto INTEGER DEFAULT 0, creado REAL);
            CREATE TABLE IF NOT EXISTS deseos (id TEXT PRIMARY KEY, teen_id TEXT NOT NULL, familia_id TEXT NOT NULL, descripcion TEXT NOT NULL, puntos_necesarios INTEGER DEFAULT 0, estado TEXT DEFAULT 'activo', creado REAL);
            CREATE TABLE IF NOT EXISTS logros (id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL, titulo TEXT NOT NULL, descripcion TEXT, icono TEXT DEFAULT 'star', creado REAL);
            CREATE TABLE IF NOT EXISTS conversaciones (id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL, familia_id TEXT NOT NULL, rol TEXT NOT NULL, mensaje TEXT NOT NULL, respuesta TEXT NOT NULL, creado REAL);
        """)
        await db.commit()

@app.on_event("startup")
async def startup():
    await init_db()

# ── Pydantic models ───────────────────────────────────────────────────────────
class RegistrarFamilia(BaseModel):
    nombre: str
    codigo_acceso: Optional[str] = None

class RegistrarMiembro(BaseModel):
    familia_id: str; nombre: str; rol: str; edad: int = 15; pin: Optional[str] = None

class CrearMision(BaseModel):
    familia_id: str; titulo: str; descripcion: Optional[str] = None; puntos: int = 10; asignado_a: Optional[str] = None

class CompletarMision(BaseModel):
    miembro_id: Optional[str] = None; evidencia_url: Optional[str] = None

class AprobarMision(BaseModel):
    aprobado_por: str; pin_padre: str; familia_id: str

class CrearAcuerdo(BaseModel):
    familia_id: str; teen_id: str; descripcion: str
    condicion: Optional[str] = None; recompensa: Optional[str] = None; propuesto_por: str = "padre"

class AgregarDeseo(BaseModel):
    teen_id: str; familia_id: str; descripcion: str; puntos_necesarios: int = 0

class QuickMood(BaseModel):
    miembro_id: str; score: int; nota: Optional[str] = None

# ── IA ────────────────────────────────────────────────────────────────────────
async def llamar_ia(prompt: str, mensaje: str, historial: list = None) -> str:
    if ZAI_API_KEY:
        r = await _zai(prompt, mensaje, historial)
        if r: return r
    if GROQ_API_KEY:
        r = await _groq(prompt, mensaje, historial)
        if r: return r
    return "Sin IA disponible ahora mismo."

async def _zai(prompt: str, mensaje: str, historial=None) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=ZAI_API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=8.0)
        msgs = [{"role":"system","content":prompt}]
        if historial: msgs.extend(historial[-6:])
        msgs.append({"role":"user","content":mensaje})
        loop = asyncio.get_event_loop()
        resp = await asyncio.wait_for(loop.run_in_executor(None, lambda: client.chat.completions.create(model="glm-4-flash",messages=msgs,max_tokens=400,temperature=0.8)), timeout=10.0)
        return resp.choices[0].message.content
    except Exception as e:
        logger.warning("Z.ai: %s", str(e)[:60])
        return None

async def _groq(prompt: str, mensaje: str, historial=None) -> Optional[str]:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY, timeout=12.0)
        msgs = [{"role":"system","content":prompt}]
        if historial: msgs.extend(historial[-4:])
        msgs.append({"role":"user","content":mensaje})
        loop = asyncio.get_event_loop()
        resp = await asyncio.wait_for(loop.run_in_executor(None, lambda: client.chat.completions.create(model="llama-3.1-8b-instant",messages=msgs,max_tokens=400,temperature=0.8)), timeout=15.0)
        return resp.choices[0].message.content
    except Exception as e:
        logger.error("Groq: %s", str(e)[:60])
        return None

# ── DB helpers ────────────────────────────────────────────────────────────────
async def get_miembro(db, mid):
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT * FROM miembros WHERE id=?", (mid,))
    row = await cur.fetchone()
    return dict(row) if row else None

async def get_last_mood(db, mid):
    cur = await db.execute("SELECT score,nota FROM mood_history WHERE miembro_id=? ORDER BY creado DESC LIMIT 1", (mid,))
    row = await cur.fetchone()
    if not row: return "sin registro"
    labels = {1:"muy bajo",2:"bajo",3:"regular",4:"bien",5:"muy bien"}
    return f"{labels.get(row[0],str(row[0]))}{' — '+row[1] if row[1] else ''}"

def detectar_riesgo_vital(texto): return any(p in texto.lower() for p in RIESGO_VITAL)
def detectar_tema(texto):
    t = texto.lower()
    for tipo, palabras in TEMAS_SENSIBLES.items():
        if any(p in t for p in palabras): return tipo
    return None

async def registrar_alerta(db, fid, tid, tipo):
    sug = SUGERENCIAS_PADRES.get(tipo,"Mantén canales abiertos.")
    await db.execute("INSERT INTO alertas VALUES (?,?,?,?,?,?,0,?)",
                     (str(uuid.uuid4())[:8], fid, tid, tipo, f"Tema: {tipo}", sug, time.time()))

async def _get_teen_agreements(db, fid, tid):
    cur = await db.execute("SELECT descripcion FROM acuerdos WHERE familia_id=? AND teen_id=? AND estado='activo'", (fid,tid))
    rows = await cur.fetchall()
    return ", ".join([r[0] for r in rows]) if rows else "ninguno"

async def _build_prompt_padre(db, nombre, fid):
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT nombre FROM miembros WHERE familia_id=? AND rol IN ('teen','hermano') LIMIT 1", (fid,))
    tr = await cur.fetchone(); teen = tr[0] if tr else "tu hijo/a"
    cur2 = await db.execute("SELECT descripcion,recompensa FROM acuerdos WHERE familia_id=? AND estado='activo'", (fid,))
    acs = [dict(r) for r in await cur2.fetchall()]
    ac_txt = "\n".join([f"  • {a['descripcion']} → {a['recompensa'] or 'sin recompensa'}" for a in acs]) or "Sin acuerdos."
    cur3 = await db.execute("SELECT tipo,sugerencia FROM alertas WHERE familia_id=? AND visto=0 ORDER BY creado DESC LIMIT 3", (fid,))
    als = [dict(r) for r in await cur3.fetchall()]
    al_txt = "\n".join([f"  [{a['tipo']}] {a['sugerencia']}" for a in als]) or "Sin señales."
    return PROMPT_PADRE.format(nombre=nombre, teen=teen, acuerdos=ac_txt, alertas=al_txt)

# ── Web routes ────────────────────────────────────────────────────────────────
HTML_PATH = Path(__file__).parent / "teens.html"

@app.get("/", response_class=HTMLResponse)
@app.get("/teens", response_class=HTMLResponse)
async def serve_teens():
    return HTMLResponse(content=HTML_PATH.read_text(encoding="utf-8"))

@app.get("/teens-launch")
async def teens_launch(response: Response):
    response.set_cookie("ngrok-skip-browser-warning", "true", max_age=31536000, path="/")
    response.status_code = 302
    response.headers["Location"] = "/teens"
    return response

@app.get("/teens/manifest.json")
async def manifest():
    return JSONResponse({"name":"NEXUS Teens","short_name":"Teens","start_url":"/teens",
        "display":"standalone","background_color":"#0a0a0a","theme_color":"#7c3aed","orientation":"portrait",
        "icons":[{"src":"/teens-192.png","sizes":"192x192","type":"image/png"},
                 {"src":"/teens-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]})

@app.get("/teens/sw.js")
async def service_worker():
    sw = """const CACHE='teens-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/teens'])));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(clients.claim());});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.pathname==='/teens'){
    e.respondWith(fetch(e.request,{headers:{'ngrok-skip-browser-warning':'true'}}).then(r=>{caches.open(CACHE).then(c=>c.put(e.request,r.clone()));return r;}).catch(()=>caches.match('/teens')));
  }
});"""
    return Response(content=sw, media_type="application/javascript")

@app.get("/health")
async def health():
    return {"status":"ok","motor":"teens","version":"3.0"}

# ── API endpoints (mismo path que local: /teens/api/*) ────────────────────────
@app.post("/teens/familias")
async def registrar_familia(req: RegistrarFamilia):
    fid = str(uuid.uuid4())[:8]
    codigo = req.codigo_acceso or str(uuid.uuid4())[:6].upper()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO familias VALUES (?,?,?,?)", (fid, req.nombre, codigo, time.time()))
        await db.commit()
    return {"ok":True,"familia_id":fid,"codigo_acceso":codigo}

@app.get("/teens/familias/codigo/{codigo}")
async def buscar_familia(codigo: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id,nombre FROM familias WHERE codigo_acceso=?", (codigo.upper(),))
        row = await cur.fetchone()
    if not row: return {"ok":False,"error":"Código no válido"}
    return {"ok":True,"familia_id":dict(row)["id"],"nombre":dict(row)["nombre"]}

@app.post("/teens/miembros")
async def registrar_miembro(req: RegistrarMiembro):
    mid = str(uuid.uuid4())[:8]
    pin_hash = hashlib.sha256(req.pin.encode()).hexdigest() if req.pin else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO miembros VALUES (?,?,?,?,?,?,0,'{}','{}',1,?)",
                         (mid,req.familia_id,req.nombre,req.rol,req.edad,pin_hash,time.time()))
        await db.commit()
    return {"ok":True,"miembro_id":mid,"nombre":req.nombre,"rol":req.rol}

@app.get("/teens/miembros/{mid}")
async def ver_miembro(mid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id,familia_id,nombre,rol,edad,puntos_total FROM miembros WHERE id=? AND activo=1", (mid,))
        row = await cur.fetchone()
    if not row: return {"ok":False,"error":"Miembro no encontrado"}
    return {"ok":True,**dict(row)}

@app.get("/teens/familia/{fid}")
async def ver_familia(fid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id,nombre,rol,edad,puntos_total FROM miembros WHERE familia_id=? AND activo=1", (fid,))
        miembros = [dict(r) for r in await cur.fetchall()]
        cur2 = await db.execute("SELECT COUNT(*) FROM misiones WHERE familia_id=? AND estado='completada'", (fid,))
        pendientes = (await cur2.fetchone())[0]
        cur3 = await db.execute("SELECT id,descripcion,recompensa FROM acuerdos WHERE familia_id=? AND estado='activo'", (fid,))
        acuerdos = [dict(r) for r in await cur3.fetchall()]
        cur4 = await db.execute("SELECT COUNT(*) FROM alertas WHERE familia_id=? AND visto=0", (fid,))
        alertas_nuevas = (await cur4.fetchone())[0]
    return {"ok":True,"miembros":miembros,"misiones_pendientes":pendientes,"acuerdos_activos":acuerdos,"alertas_nuevas":alertas_nuevas}

@app.post("/teens/mood")
async def quick_mood(req: QuickMood):
    if not 1 <= req.score <= 5: raise HTTPException(400,"score 1-5")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO mood_history VALUES (?,?,?,?,?)",(str(uuid.uuid4())[:8],req.miembro_id,req.score,req.nota,time.time()))
        await db.commit()
    return {"ok":True,"respuesta":{1:"Notado.",2:"Ok.",3:"Copy.",4:"Bien.",5:"Qué bueno."}.get(req.score,"Ok.")}

@app.get("/teens/misiones/{fid}")
async def listar_misiones(fid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE familia_id=? ORDER BY creado DESC", (fid,))
        rows = await cur.fetchall()
    return {"ok":True,"misiones":[dict(r) for r in rows]}

@app.post("/teens/misiones")
async def crear_mision(req: CrearMision):
    mid = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO misiones VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (mid,req.familia_id,req.titulo,req.descripcion,req.puntos,req.asignado_a,"pendiente",None,None,time.time(),None,None))
        await db.commit()
    return {"ok":True,"id":mid,"respuesta":f"Misión '{req.titulo}' creada — {req.puntos} pts"}

@app.put("/teens/misiones/{mid}/completar")
async def completar_mision(mid: str, req: CompletarMision):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        m = dict(await cur.fetchone()) if (row := await cur.fetchone()) else None
        cur2 = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        m = dict(await cur2.fetchone())
        if m["estado"] != "pendiente": raise HTTPException(400,"La misión no está pendiente")
        await db.execute("UPDATE misiones SET estado='completada',evidencia_url=?,completado=? WHERE id=?",
                         (req.evidencia_url,time.time(),mid))
        await db.commit()
    return {"ok":True,"respuesta":f"'{m['titulo']}' completada — esperando aprobación"}

@app.put("/teens/misiones/{mid}/aprobar")
async def aprobar_mision(mid: str, req: AprobarMision):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        m = dict(await cur.fetchone())
        if m["estado"] != "completada": raise HTTPException(400,"Misión no completada aún")
        pin_hash = hashlib.sha256(req.pin_padre.encode()).hexdigest()
        cur2 = await db.execute("SELECT id FROM miembros WHERE familia_id=? AND rol IN ('padre','madre') AND pin_hash=?", (req.familia_id,pin_hash))
        if not await cur2.fetchone(): raise HTTPException(401,"PIN incorrecto")
        await db.execute("UPDATE misiones SET estado='aprobada',aprobado_por=?,aprobado=? WHERE id=?", (req.aprobado_por,time.time(),mid))
        if m.get("asignado_a"):
            await db.execute("UPDATE miembros SET puntos_total=puntos_total+? WHERE id=?", (m["puntos"],m["asignado_a"]))
            cur3 = await db.execute("SELECT puntos_total FROM miembros WHERE id=?", (m["asignado_a"],))
            pts = (await cur3.fetchone())[0]
            for umbral,titulo in [(100,"Centurión"),(50,"Cincuenta"),(10,"Arranque")]:
                if pts >= umbral and (pts-m["puntos"]) < umbral:
                    await db.execute("INSERT INTO logros VALUES (?,?,?,?,?,?)",
                                     (str(uuid.uuid4())[:8],m["asignado_a"],titulo,f"{umbral} puntos acumulados","star",time.time()))
        await db.commit()
    return {"ok":True,"puntos_asignados":m["puntos"],"respuesta":f"Aprobada — +{m['puntos']} pts"}

@app.get("/teens/acuerdos/{fid}")
async def listar_acuerdos(fid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM acuerdos WHERE familia_id=? ORDER BY creado DESC", (fid,))
        rows = await cur.fetchall()
    return {"ok":True,"acuerdos":[dict(r) for r in rows]}

@app.post("/teens/acuerdos")
async def crear_acuerdo(req: CrearAcuerdo):
    aid = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO acuerdos VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (aid,req.familia_id,req.teen_id,req.descripcion,req.condicion,req.recompensa,req.propuesto_por,"propuesto",time.time(),None))
        await db.commit()
    return {"ok":True,"acuerdo_id":aid,"respuesta":"Acuerdo registrado."}

@app.put("/teens/acuerdos/{aid}/activar")
async def activar_acuerdo(aid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE acuerdos SET estado='activo' WHERE id=?", (aid,))
        await db.commit()
    return {"ok":True,"respuesta":"Acuerdo activo."}

@app.put("/teens/acuerdos/{aid}/cumplir")
async def cumplir_acuerdo(aid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM acuerdos WHERE id=?", (aid,))
        ac = dict(await cur.fetchone())
        await db.execute("UPDATE acuerdos SET estado='cumplido',cumplido=? WHERE id=?", (time.time(),aid))
        await db.execute("UPDATE miembros SET puntos_total=puntos_total+50 WHERE id=?", (ac["teen_id"],))
        await db.commit()
    return {"ok":True,"respuesta":"Acuerdo cumplido. +50 pts."}

@app.post("/teens/deseos")
async def agregar_deseo(req: AgregarDeseo):
    did = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO deseos VALUES (?,?,?,?,?,?,?)",
                         (did,req.teen_id,req.familia_id,req.descripcion,req.puntos_necesarios,"activo",time.time()))
        await db.commit()
    return {"ok":True,"deseo_id":did,"respuesta":f"'{req.descripcion}' en tu lista."}

@app.get("/teens/deseos/{tid}")
async def ver_deseos(tid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT d.id,d.descripcion,d.puntos_necesarios,m.puntos_total FROM deseos d JOIN miembros m ON d.teen_id=m.id WHERE d.teen_id=? AND d.estado='activo' ORDER BY d.puntos_necesarios ASC", (tid,))
        deseos = [dict(r) for r in await cur.fetchall()]
    return {"ok":True,"deseos":deseos}

@app.get("/teens/alertas/{fid}")
async def ver_alertas(fid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT tipo,resumen,sugerencia,creado FROM alertas WHERE familia_id=? ORDER BY creado DESC LIMIT 20", (fid,))
        alertas = [dict(r) for r in await cur.fetchall()]
        await db.execute("UPDATE alertas SET visto=1 WHERE familia_id=?", (fid,))
        await db.commit()
    return {"ok":True,"alertas":alertas}

@app.get("/teens/logros/{mid}")
async def ver_logros(mid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT titulo,descripcion,icono,creado FROM logros WHERE miembro_id=? ORDER BY creado DESC", (mid,))
        logros = [dict(r) for r in await cur.fetchall()]
    return {"ok":True,"logros":logros}

# ── /execute (IA chat) ────────────────────────────────────────────────────────
class ExecuteReq(BaseModel):
    action: str = "process_query"
    data: Optional[dict] = None

@app.post("/teens/api/execute")
@app.post("/execute")
async def execute(req: ExecuteReq):
    data = req.data or {}
    mensaje = (data.get("message") or "").strip()
    mid = data.get("miembro_id") or data.get("session_id","")
    fid = data.get("familia_id","")

    if not mid:
        return {"ok":False,"requiere_contexto":True,"respuesta":"¿Quién pregunta? Necesito tu ID de miembro.","motor":"teens"}

    async with aiosqlite.connect(DB_PATH) as db:
        miembro = await get_miembro(db, mid)
        if not miembro:
            return {"ok":False,"requiere_contexto":True,"respuesta":"No encontré ese miembro. Regístrate primero.","motor":"teens"}

        rol = miembro["rol"]; nombre = miembro["nombre"]; fid = fid or miembro["familia_id"]
        ctx = {}
        try: ctx = json.loads(miembro.get("active_context") or "{}")
        except: pass

        # Riesgo vital
        if rol in ("teen","hermano") and detectar_riesgo_vital(mensaje):
            await registrar_alerta(db, fid, mid, "riesgo_alto")
            await db.commit()
            resp = "Oye, lo que acabas de decir no lo voy a guardar solo. Es una alerta de seguridad y voy a pedirle a tu familia que te acompañe en esto. No es para castigarte — es para que no cargues solo con eso."
            await db.execute("INSERT INTO conversaciones VALUES (?,?,?,?,?,?,?)",(str(uuid.uuid4())[:8],mid,fid,rol,mensaje,resp,time.time()))
            await db.commit()
            return {"ok":True,"motor":"teens","respuesta":resp,"alerta":"riesgo_alto"}

        # Temas sensibles
        if rol in ("teen","hermano") and mensaje:
            tema = detectar_tema(mensaje)
            if tema:
                await registrar_alerta(db, fid, mid, tema)
                await db.commit()

        # Historial
        cur_h = await db.execute("SELECT mensaje,respuesta FROM conversaciones WHERE miembro_id=? ORDER BY creado DESC LIMIT 4", (mid,))
        rows_h = await cur_h.fetchall()
        historial = []
        for h in reversed(rows_h):
            historial += [{"role":"user","content":h[0]},{"role":"assistant","content":h[1]}]

        # Prompt
        if rol in ("padre","madre"):
            prompt = await _build_prompt_padre(db, nombre, fid)
        else:
            last_mood = await get_last_mood(db, mid)
            teen_agr = await _get_teen_agreements(db, fid, mid)
            prompt = PROMPT_TEEN.format(nombre=nombre, edad=miembro.get("edad",15),
                                        last_mood=last_mood, active_context=ctx.get("tema_principal","ninguno"))

        if not mensaje:
            return {"ok":True,"motor":"teens","respuesta":"Aquí estoy. Qué hay." if rol not in ("padre","madre") else f"Hola {nombre}. ¿Qué quieres revisar?"}

        respuesta = await llamar_ia(prompt, mensaje, historial)

        await db.execute("INSERT INTO conversaciones VALUES (?,?,?,?,?,?,?)",
                         (str(uuid.uuid4())[:8],mid,fid,rol,mensaje,respuesta,time.time()))
        await db.commit()
        return {"ok":True,"motor":"teens","respuesta":respuesta,"rol":rol}

# También aceptar las rutas con prefijo /teens/api/ que usa el HTML
@app.api_route("/teens/api/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def teens_api_pass(path: str, request: Request):
    """Redirige /teens/api/X → /teens/X internamente."""
    import httpx
    url = f"http://localhost:{PORT}/teens/{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.request(method=request.method, url=url, content=body,
                            headers={"Content-Type":"application/json"},
                            params=dict(request.query_params))
        return JSONResponse(r.json(), status_code=r.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

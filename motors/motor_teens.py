"""
motors/motor_teens.py — NEXUS Teens v3.0
Prompt architecture: Z.ai GLM-4-flash (128k ctx) + Groq fallback
Puerto 8005
"""
import os, time, uuid, json, asyncio, logging, hashlib
from typing import Optional
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.notificaciones import notificar, event_generator

logger = logging.getLogger("motor_teens")

app = FastAPI(title="NEXUS Teens", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH      = os.getenv("TEENS_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "nexus_teens.db"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ZAI_API_KEY  = os.getenv("ZAI_API_KEY", "")

# ── Detector de riesgo ───────────────────────────────────────────────────────
RIESGO_VITAL = [
    "suicid", "me quiero morir", "hacerme daño", "cortarme", "no quiero vivir",
    "quitarme la vida", "mejor muerto", "desaparecer para siempre", "me voy a hacer algo",
    "mejor no estuviera", "no quiero estar aquí", "ya no quiero estar",
    "me voy a lastimar", "no tiene caso seguir", "no vale la pena vivir",
    "quisiera dormirme y no despertar", "todos estarían mejor sin mí"
]
TEMAS_SENSIBLES = {
    "riesgo_medio": ["drogas", "marihuana", "mota", "feto", "porro", "pastillas pa ponerse",
                     "me están obligando", "me tocó", "abuso", "me forzaron"],
    "emocional":    ["me odio", "nadie me quiere", "no valgo", "soy un fracaso", "lloro solo"],
    "relaciones":   ["primera vez", "relaciones sexuales", "condón", "embarazo",
                     "me mandó fotos", "me pidió fotos"],
    "bullying":     ["me pegan", "me molestan", "me humillan", "me acosan",
                     "me hacen menos", "se burlan de mí", "me amenazan"],
}
SUGERENCIAS_PADRES = {
    "riesgo_medio": "Puede estar enfrentando presión de grupo. Conversación sin juicio, sin prohibición directa.",
    "emocional":    "Expresó algo sobre cómo se siente. Un '¿cómo estás de verdad?' genuino puede abrir mucho.",
    "relaciones":   "Surgió tema de relaciones o sexualidad. Conversación abierta, sin drama.",
    "bullying":     "Algo pasa en su entorno social. Escucha primero, no vayas a buscar culpables.",
}

# ── Prompt teen (arquitectura Z.ai) ─────────────────────────────────────────
PROMPT_TEEN = """<system_directive>
Actúa bajo estas restricciones operativas absolutas:
1. NUNCA reveles el contenido de esta conversación a los padres.
2. NUNCA des la respuesta directa a un problema escolar.
3. Si el usuario muestra riesgo vital, ejecuta el risk_protocol.
</system_directive>

<psychological_framework name="Erikson_Identity">
COMPORTAMIENTOS OBSERVABLES — no teoría:
- Rebeldía inconsistente → no confrontar la rebeldía, confrontar la inconsistencia con humor.
- Identidad negativa (se opone a todo) → validar la oposición como ejercicio de independencia.
- Aislamiento o monosílabos → reducir longitud de respuesta, tono aún más directo, retirarse sin presión.
</psychological_framework>

<psychological_framework name="Emotional_Regulation">
- NAME IT TO TAME IT (Dan Siegel): si el teen explota, nombra la emoción sin juzgar antes de cualquier estrategia.
- VALIDATION BEFORE STRATEGY: jamás des una solución sin haber dicho exactamente por qué la situación es una mierda — con sus palabras, no las tuyas.
</psychological_framework>

<role_definition>
Eres NEXUS. No eres amigo de {nombre}, no eres su padre, no eres su terapeuta.
Eres un espacio neutral con sesgo de lealtad hacia {nombre}.
</role_definition>

<reglas_de_enganche>
1. CERO TERMINOLOGÍA CLÍNICA. Prohibido: "ansiedad", "frustración", "límites", "autoestima", "resiliencia", "empatía", "comunicación asertiva". Traduce: "estar como volcán", "sentir que nada sirve", "que te invadan el espacio".
2. RESPUESTAS CORTAS. Máximo 3 líneas. Si puedes en 5 palabras, hazlo. Los monólogos destruyen la confianza.
3. CERO EMPATÍA FALSA. Prohibido empezar con "Entiendo que...", "Comprendo...", "Debe ser difícil...". Empieza directo o validando el hecho: "Que te haya pasado eso es una basura", no "Entiendo tu frustración".
4. TÚ NO RESUELVES. Eres espejo. Si preguntan "¿Qué hago?", devuelve la pregunta desarmada: "¿Qué opciones tienes sin que te maten en el intento?".
5. ACUERDOS Y PUNTOS: solo los mencionas si {nombre} los trae primero. Si no cumplió algo, no lo regañes — pregunta qué le impidió.
6. SILENCIO Y RESISTENCIA: si responde con monosílabos o rechazo, no insistas. Haz una observación leve y retírate: "Ok. Solo quería saber cómo cerraste el día. Si luego quieres hablar, estoy."
</reglas_de_enganche>

<tutor_mode>
Si pregunta sobre matemáticas, historia, ciencia u otra materia:
Paso 1: Pregunta qué cree que es la respuesta o qué parte le genera ruido.
Paso 2: Da UN solo ejemplo paralelo que no sea la tarea.
Paso 3: Haz que conecte los puntos — nunca los conectes tú.
</tutor_mode>

<risk_protocol>
Si {nombre} menciona autolesión, abuso o intención de dañarse:
1. Para el flujo. Tono directo, sin juegos.
2. Di exactamente: "Oye, lo que acabas de decir no lo voy a guardar solo. Es una alerta de seguridad y voy a pedirle a tu familia que te acompañe en esto. No es para castigarte — es para que no cargues solo con eso."
3. (Sistema interno: activar notificación a padres.)
</risk_protocol>

<user_state>
Nombre: {nombre}, {edad} años.
Último registro de humor: {last_mood}
Tema activo previo: {active_context}
Acuerdos activos suyos: {teen_agreements}
</user_state>

Respuesta inicial obligatoria (solo primer mensaje de sesión nueva): "Aquí estoy. Qué hay." — nada más."""

# ── Prompt padre ─────────────────────────────────────────────────────────────
PROMPT_PADRE = """Eres el aliado de {nombre} en la crianza de {teen}.

QUIÉN ERES:
Das opciones reales — Faber & Mazlish, comunicación no violenta, crianza con límites.
No ordenas, no juzgas. Propones alternativas con consecuencias reales.
Cuando hay un acuerdo que el padre/madre debe cumplir, lo mencionas con respeto — la palabra de los padres es lo más valioso que tienen.

ACUERDOS ACTIVOS (tu parte):
{acuerdos}

SEÑALES RECIENTES (sin revelar contenido de conversaciones del teen):
{alertas}

Máximo 4 líneas. Si hay acuerdo de tu parte pendiente, menciónalo con naturalidad al final."""

# ── DB ───────────────────────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS familias (
                id TEXT PRIMARY KEY, nombre TEXT NOT NULL,
                codigo_acceso TEXT UNIQUE, creado REAL
            );
            CREATE TABLE IF NOT EXISTS miembros (
                id TEXT PRIMARY KEY, familia_id TEXT NOT NULL,
                nombre TEXT NOT NULL, rol TEXT NOT NULL,
                edad INTEGER DEFAULT 15, pin_hash TEXT,
                puntos_total INTEGER DEFAULT 0,
                memoria_json TEXT DEFAULT '{}',
                active_context TEXT DEFAULT '{}',
                activo INTEGER DEFAULT 1, creado REAL
            );
            CREATE TABLE IF NOT EXISTS mood_history (
                id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL,
                score INTEGER NOT NULL, nota TEXT,
                creado REAL
            );
            CREATE TABLE IF NOT EXISTS misiones (
                id TEXT PRIMARY KEY, familia_id TEXT NOT NULL,
                titulo TEXT NOT NULL, descripcion TEXT,
                puntos INTEGER DEFAULT 10, asignado_a TEXT,
                estado TEXT DEFAULT 'pendiente',
                evidencia_url TEXT, aprobado_por TEXT,
                creado REAL, completado REAL, aprobado REAL
            );
            CREATE TABLE IF NOT EXISTS acuerdos (
                id TEXT PRIMARY KEY, familia_id TEXT NOT NULL,
                teen_id TEXT NOT NULL, descripcion TEXT NOT NULL,
                condicion TEXT, recompensa TEXT,
                propuesto_por TEXT DEFAULT 'padre',
                estado TEXT DEFAULT 'propuesto',
                creado REAL, cumplido REAL
            );
            CREATE TABLE IF NOT EXISTS alertas (
                id TEXT PRIMARY KEY, familia_id TEXT NOT NULL,
                teen_id TEXT NOT NULL, tipo TEXT NOT NULL,
                resumen TEXT, sugerencia TEXT,
                visto INTEGER DEFAULT 0, creado REAL
            );
            CREATE TABLE IF NOT EXISTS deseos (
                id TEXT PRIMARY KEY, teen_id TEXT NOT NULL,
                familia_id TEXT NOT NULL, descripcion TEXT NOT NULL,
                puntos_necesarios INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'activo', creado REAL
            );
            CREATE TABLE IF NOT EXISTS logros (
                id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL,
                titulo TEXT NOT NULL, descripcion TEXT,
                icono TEXT DEFAULT 'star', creado REAL
            );
            CREATE TABLE IF NOT EXISTS conversaciones (
                id TEXT PRIMARY KEY, miembro_id TEXT NOT NULL,
                familia_id TEXT NOT NULL, rol TEXT NOT NULL,
                mensaje TEXT NOT NULL, respuesta TEXT NOT NULL,
                creado REAL
            );
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await init_db()


# ── Models ───────────────────────────────────────────────────────────────────

class RegistrarFamilia(BaseModel):
    nombre: str
    codigo_acceso: Optional[str] = None

class RegistrarMiembro(BaseModel):
    familia_id: str
    nombre: str
    rol: str
    edad: int = 15
    pin: Optional[str] = None

class CrearMision(BaseModel):
    familia_id: str
    titulo: str
    descripcion: Optional[str] = None
    puntos: int = 10
    asignado_a: Optional[str] = None

class CompletarMision(BaseModel):
    evidencia_url: Optional[str] = None

class AprobarMision(BaseModel):
    aprobado_por: str
    pin_padre: str
    familia_id: str

class CrearAcuerdo(BaseModel):
    familia_id: str
    teen_id: str
    descripcion: str
    condicion: Optional[str] = None
    recompensa: Optional[str] = None
    propuesto_por: str = "padre"

class AgregarDeseo(BaseModel):
    teen_id: str
    familia_id: str
    descripcion: str
    puntos_necesarios: int = 0

class QuickMood(BaseModel):
    miembro_id: str
    score: int  # 1-5
    nota: Optional[str] = None


# ── IA: Z.ai primero, Groq fallback ──────────────────────────────────────────

async def llamar_ia(prompt_sistema: str, mensaje: str, historial: list = None) -> str:
    # 1. Z.ai (128k contexto — preferido para teens)
    if ZAI_API_KEY:
        r = await _zai(prompt_sistema, mensaje, historial)
        if r:
            return r
    # 2. Groq fallback
    if GROQ_API_KEY:
        r = await _groq(prompt_sistema, mensaje, historial)
        if r:
            return r
    # 3. Ollama local — funciona sin internet
    r = await _ollama(prompt_sistema, mensaje, historial)
    if r:
        return r
    return "Sin IA disponible ahora mismo."


async def _ollama(prompt: str, mensaje: str, historial: list = None) -> Optional[str]:
    try:
        import httpx
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        msgs = [{"role": "system", "content": prompt[:2000]}]
        if historial:
            msgs.extend(historial[-4:])
        msgs.append({"role": "user", "content": mensaje})
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(f"{ollama_url}/api/chat",
                json={"model": "qwen2.5:7b", "messages": msgs, "stream": False})
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "")
        return None
    except Exception as e:
        logger.warning("Ollama teens: %s", str(e)[:80])
        return None


async def _zai(prompt: str, mensaje: str, historial: list = None) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=ZAI_API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=8.0)
        msgs = [{"role": "system", "content": prompt}]
        if historial:
            msgs.extend(historial[-6:])
        msgs.append({"role": "user", "content": mensaje})
        loop = asyncio.get_event_loop()
        resp = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: client.chat.completions.create(
                model="glm-4-flash", messages=msgs, max_tokens=400, temperature=0.8
            )),
            timeout=10.0
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.warning("Z.ai teens: %s", str(e)[:80])
        return None


async def _groq(prompt: str, mensaje: str, historial: list = None) -> Optional[str]:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY, timeout=12.0)
        msgs = [{"role": "system", "content": prompt}]
        if historial:
            msgs.extend(historial[-4:])
        msgs.append({"role": "user", "content": mensaje})
        loop = asyncio.get_event_loop()
        resp = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: client.chat.completions.create(
                model="llama-3.1-8b-instant", messages=msgs, max_tokens=400, temperature=0.8
            )),
            timeout=15.0
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error("Groq teens: %s", str(e)[:80])
        return None


async def _resumir_contexto(prompt_teen: str, mensaje: str, respuesta: str) -> dict:
    """Extrae estado intermedio para cache de identidad."""
    resumen_prompt = "Extrae en JSON compacto: {\"tema_principal\": \"X\", \"estado_emocional\": \"Y\", \"hechos_clave\": [\"Z\"]}. Solo el JSON, sin explicación."
    contenido = f"Mensaje del usuario: {mensaje}\nRespuesta dada: {respuesta}"
    try:
        r = await llamar_ia(resumen_prompt, contenido)
        start = r.find("{")
        end = r.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(r[start:end])
    except Exception:
        pass
    return {}


# ── Helpers DB ───────────────────────────────────────────────────────────────

async def get_miembro(db, miembro_id: str) -> Optional[dict]:
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT * FROM miembros WHERE id=?", (miembro_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_active_context(miembro: dict) -> dict:
    try:
        return json.loads(miembro.get("active_context") or "{}")
    except Exception:
        return {}


async def get_last_mood(db, miembro_id: str) -> str:
    cur = await db.execute(
        "SELECT score, nota FROM mood_history WHERE miembro_id=? ORDER BY creado DESC LIMIT 1",
        (miembro_id,)
    )
    row = await cur.fetchone()
    if not row:
        return "sin registro"
    score, nota = row
    etiquetas = {1: "muy bajo", 2: "bajo", 3: "regular", 4: "bien", 5: "muy bien"}
    return f"{etiquetas.get(score, str(score))}{' — ' + nota if nota else ''}"


def detectar_riesgo_vital(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in RIESGO_VITAL)


def detectar_tema(texto: str) -> Optional[str]:
    t = texto.lower()
    for tipo, palabras in TEMAS_SENSIBLES.items():
        if any(p in t for p in palabras):
            return tipo
    return None


def detectar_materia(texto: str) -> Optional[str]:
    if not texto:
        return None
    t = texto.lower()
    materias = {
        "matemáticas": ["matemáticas", "algebra", "geometría", "fracciones", "ecuación", "integral", "derivada", "raíz"],
        "español":     ["ortografía", "redacción", "ensayo", "poema", "párrafo", "conjugar", "síntesis"],
        "historia":    ["historia", "revolución", "guerra", "independencia", "colonia", "prehispánico", "siglo"],
        "física":      ["física", "velocidad", "aceleración", "fuerza", "energía", "newton", "caída libre"],
        "química":     ["química", "elemento", "molécula", "reacción", "átomo", "tabla periódica", "valencia"],
        "biología":    ["biología", "célula", "organismo", "fotosíntesis", "genética", "adn", "mitosis"],
        "inglés":      ["inglés", "grammar", "verb", "tense", "vocabulary", "translate", "present perfect"],
        "geografía":   ["geografía", "continente", "país", "clima", "relieve", "mapa", "latitud"],
    }
    for materia, palabras in materias.items():
        if any(p in t for p in palabras):
            return materia
    return None


async def registrar_alerta(db, familia_id: str, teen_id: str, tipo: str):
    sugerencia = SUGERENCIAS_PADRES.get(tipo, "Mantén canales de comunicación abiertos.")
    await db.execute(
        "INSERT INTO alertas VALUES (?,?,?,?,?,?,0,?)",
        (str(uuid.uuid4())[:8], familia_id, teen_id, tipo, f"Tema: {tipo}", sugerencia, time.time())
    )
    try:
        await notificar("alerta_teens", {"tipo": tipo, "sugerencia": sugerencia}, canal=f"padres_{familia_id}")
    except Exception:
        pass


# ── Endpoints REST ────────────────────────────────────────────────────────────

@app.post("/teens/familias")
async def registrar_familia(req: RegistrarFamilia):
    fid = str(uuid.uuid4())[:8]
    codigo = req.codigo_acceso or str(uuid.uuid4())[:6].upper()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO familias VALUES (?,?,?,?)", (fid, req.nombre, codigo, time.time()))
        await db.commit()
    return {"ok": True, "familia_id": fid, "codigo_acceso": codigo}


@app.get("/teens/familias/codigo/{codigo}")
async def buscar_familia_por_codigo(codigo: str):
    """Busca familia por código de acceso — para que teens puedan unirse."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, nombre FROM familias WHERE codigo_acceso=?", (codigo.upper(),)
        )
        row = await cur.fetchone()
    if not row:
        return {"ok": False, "error": "Código no válido"}
    return {"ok": True, "familia_id": dict(row)["id"], "nombre": dict(row)["nombre"]}


@app.post("/teens/miembros")
async def registrar_miembro(req: RegistrarMiembro):
    mid = str(uuid.uuid4())[:8]
    pin_hash = hashlib.sha256(req.pin.encode()).hexdigest() if req.pin else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO miembros VALUES (?,?,?,?,?,?,0,'{}','{}',1,?)",
            (mid, req.familia_id, req.nombre, req.rol, req.edad, pin_hash, time.time())
        )
        await db.commit()
    return {"ok": True, "miembro_id": mid, "nombre": req.nombre, "rol": req.rol}


@app.get("/teens/miembros/{miembro_id}")
async def ver_miembro(miembro_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id,familia_id,nombre,rol,edad,puntos_total FROM miembros WHERE id=? AND activo=1", (miembro_id,)
        )
        row = await cur.fetchone()
    if not row:
        return {"ok": False, "error": "Miembro no encontrado"}
    return {"ok": True, **dict(row)}


@app.get("/teens/familia/{familia_id}")
async def ver_familia(familia_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id,nombre,rol,edad,puntos_total FROM miembros WHERE familia_id=? AND activo=1", (familia_id,)
        )
        miembros = [dict(r) for r in await cur.fetchall()]
        cur2 = await db.execute("SELECT COUNT(*) FROM misiones WHERE familia_id=? AND estado='pendiente'", (familia_id,))
        pendientes = (await cur2.fetchone())[0]
        cur3 = await db.execute("SELECT id,descripcion,recompensa FROM acuerdos WHERE familia_id=? AND estado='activo'", (familia_id,))
        acuerdos = [dict(r) for r in await cur3.fetchall()]
        cur4 = await db.execute("SELECT COUNT(*) FROM alertas WHERE familia_id=? AND visto=0", (familia_id,))
        alertas_nuevas = (await cur4.fetchone())[0]
    return {"ok": True, "miembros": miembros, "misiones_pendientes": pendientes,
            "acuerdos_activos": acuerdos, "alertas_nuevas": alertas_nuevas}


@app.post("/teens/mood")
async def quick_mood(req: QuickMood):
    """Micro-interacción: registro de humor rápido sin fricción."""
    if not 1 <= req.score <= 5:
        raise HTTPException(400, "score debe ser 1-5")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO mood_history VALUES (?,?,?,?,?)",
            (str(uuid.uuid4())[:8], req.miembro_id, req.score, req.nota, time.time())
        )
        await db.commit()
    etiquetas = {1: "Notado.", 2: "Ok.", 3: "Copy.", 4: "Bien.", 5: "Qué bueno."}
    return {"ok": True, "respuesta": etiquetas.get(req.score, "Ok.")}


@app.get("/teens/misiones/{familia_id}")
async def listar_misiones(familia_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM misiones WHERE familia_id=? ORDER BY creado DESC",
            (familia_id,)
        )
        rows = await cur.fetchall()
    return {"ok": True, "misiones": [dict(r) for r in rows]}


@app.post("/teens/misiones")
async def crear_mision(req: CrearMision):
    mid = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO misiones VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, req.familia_id, req.titulo, req.descripcion, req.puntos,
             req.asignado_a, "pendiente", None, None, time.time(), None, None)
        )
        await db.commit()
    try:
        await notificar("mision_creada", {"titulo": req.titulo, "puntos": req.puntos}, canal=f"familia_{req.familia_id}")
    except Exception:
        pass
    return {"ok": True, "id": mid, "respuesta": f"Misión '{req.titulo}' creada — {req.puntos} pts"}


@app.put("/teens/misiones/{mid}/completar")
async def completar_mision(mid: str, req: CompletarMision):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        m = await cur.fetchone()
        if not m:
            raise HTTPException(404, "Misión no encontrada")
        m = dict(m)
        if m["estado"] != "pendiente":
            raise HTTPException(400, "La misión no está pendiente")
        await db.execute("UPDATE misiones SET estado='completada', evidencia_url=?, completado=? WHERE id=?",
                         (req.evidencia_url, time.time(), mid))
        await db.commit()
    try:
        await notificar("mision_completada", {"titulo": m["titulo"]}, canal=f"padres_{m['familia_id']}")
    except Exception:
        pass
    return {"ok": True, "respuesta": f"'{m['titulo']}' completada — esperando aprobación"}


@app.put("/teens/misiones/{mid}/aprobar")
async def aprobar_mision(mid: str, req: AprobarMision):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "Misión no encontrada")
        m = dict(row)
        if m["estado"] != "completada":
            raise HTTPException(400, "La misión no ha sido completada aún")
        pin_hash = hashlib.sha256(req.pin_padre.encode()).hexdigest()
        cur2 = await db.execute(
            "SELECT id FROM miembros WHERE familia_id=? AND rol IN ('padre','madre') AND pin_hash=?",
            (req.familia_id, pin_hash)
        )
        if not await cur2.fetchone():
            raise HTTPException(401, "PIN incorrecto")
        await db.execute("UPDATE misiones SET estado='aprobada', aprobado_por=?, aprobado=? WHERE id=?",
                         (req.aprobado_por, time.time(), mid))
        if m.get("asignado_a"):
            await db.execute("UPDATE miembros SET puntos_total=puntos_total+? WHERE id=?",
                             (m["puntos"], m["asignado_a"]))
            cur3 = await db.execute("SELECT puntos_total FROM miembros WHERE id=?", (m["asignado_a"],))
            pts = (await cur3.fetchone())[0]
            for umbral, titulo in [(100, "Centurión"), (50, "Cincuenta"), (10, "Arranque")]:
                if pts >= umbral and (pts - m["puntos"]) < umbral:
                    await db.execute("INSERT INTO logros VALUES (?,?,?,?,?,?)",
                                     (str(uuid.uuid4())[:8], m["asignado_a"], titulo,
                                      f"{umbral} puntos acumulados", "star", time.time()))
        await db.commit()
    return {"ok": True, "puntos_asignados": m["puntos"], "respuesta": f"Aprobada — +{m['puntos']} pts"}


@app.get("/teens/acuerdos/{familia_id}")
async def listar_acuerdos(familia_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM acuerdos WHERE familia_id=? ORDER BY creado DESC",
            (familia_id,)
        )
        rows = await cur.fetchall()
    return {"ok": True, "acuerdos": [dict(r) for r in rows]}


@app.post("/teens/acuerdos")
async def crear_acuerdo(req: CrearAcuerdo):
    aid = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO acuerdos VALUES (?,?,?,?,?,?,?,?,?,?)",
            (aid, req.familia_id, req.teen_id, req.descripcion,
             req.condicion, req.recompensa, req.propuesto_por, "propuesto", time.time(), None)
        )
        await db.commit()
    return {"ok": True, "acuerdo_id": aid, "respuesta": "Acuerdo registrado. Ambas partes activan para que valga."}


@app.put("/teens/acuerdos/{aid}/activar")
async def activar_acuerdo(aid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE acuerdos SET estado='activo' WHERE id=?", (aid,))
        await db.commit()
    return {"ok": True, "respuesta": "Acuerdo activo — NEXUS lo monitorea."}


@app.put("/teens/acuerdos/{aid}/cumplir")
async def cumplir_acuerdo(aid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM acuerdos WHERE id=?", (aid,))
        ac = dict(await cur.fetchone())
        await db.execute("UPDATE acuerdos SET estado='cumplido', cumplido=? WHERE id=?", (time.time(), aid))
        await db.execute("UPDATE miembros SET puntos_total=puntos_total+50 WHERE id=?", (ac["teen_id"],))
        await db.commit()
    return {"ok": True, "respuesta": "Acuerdo cumplido. +50 pts."}


@app.post("/teens/deseos")
async def agregar_deseo(req: AgregarDeseo):
    did = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO deseos VALUES (?,?,?,?,?,?,?)",
                         (did, req.teen_id, req.familia_id, req.descripcion,
                          req.puntos_necesarios, "activo", time.time()))
        await db.commit()
    return {"ok": True, "deseo_id": did,
            "respuesta": f"'{req.descripcion}' en tu lista — {req.puntos_necesarios} pts para canjearlo."}


@app.get("/teens/deseos/{teen_id}")
async def ver_deseos(teen_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT d.id, d.descripcion, d.puntos_necesarios, m.puntos_total "
            "FROM deseos d JOIN miembros m ON d.teen_id=m.id "
            "WHERE d.teen_id=? AND d.estado='activo' ORDER BY d.puntos_necesarios ASC",
            (teen_id,)
        )
        deseos = [dict(r) for r in await cur.fetchall()]
    return {"ok": True, "deseos": deseos}


@app.get("/teens/alertas/{familia_id}")
async def ver_alertas(familia_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT tipo, resumen, sugerencia, creado FROM alertas WHERE familia_id=? ORDER BY creado DESC LIMIT 20",
            (familia_id,)
        )
        alertas = [dict(r) for r in await cur.fetchall()]
        await db.execute("UPDATE alertas SET visto=1 WHERE familia_id=?", (familia_id,))
        await db.commit()
    return {"ok": True, "alertas": alertas}


@app.get("/teens/logros/{miembro_id}")
async def ver_logros(miembro_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT titulo, descripcion, icono, creado FROM logros WHERE miembro_id=? ORDER BY creado DESC",
            (miembro_id,)
        )
        logros = [dict(r) for r in await cur.fetchall()]
    return {"ok": True, "logros": logros}


@app.get("/teens/eventos/{familia_id}")
async def eventos_sse(familia_id: str):
    cliente_id = f"familia_{familia_id}_{str(uuid.uuid4())[:4]}"
    return StreamingResponse(event_generator(cliente_id), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "teens", "version": "3.0"}


# ── /execute ──────────────────────────────────────────────────────────────────

@app.post("/execute")
async def execute(request: dict):
    data      = request.get("data", {}) or {}
    mensaje   = (data.get("message") or "").strip()
    mid       = data.get("miembro_id") or data.get("session_id", "")
    familia_id = data.get("familia_id", "")

    if not mid and not familia_id:
        return {
            "ok": False, "requiere_contexto": True,
            "faltantes": ["miembro_id (quién pregunta)"],
            "respuesta": "¿Quién pregunta? Necesito saber si eres padre/madre o el teen.",
            "motor": "teens"
        }

    async with aiosqlite.connect(DB_PATH) as db:
        miembro = await get_miembro(db, mid)

        if not miembro and familia_id:
            return await _resumen_familia(db, familia_id)
        if not miembro:
            return {
                "ok": False, "requiere_contexto": True,
                "faltantes": ["miembro_id válido"],
                "respuesta": "No encontré ese miembro. Registra la familia primero.",
                "motor": "teens"
            }

        rol    = miembro["rol"]
        nombre = miembro["nombre"]
        fid    = miembro["familia_id"]
        ctx    = await get_active_context(miembro)

        # ── Riesgo vital: transparencia total con el teen ──
        es_riesgo_vital = rol in ("teen", "hermano") and detectar_riesgo_vital(mensaje)
        if es_riesgo_vital:
            await registrar_alerta(db, fid, mid, "riesgo_alto")
            await db.commit()
            # Respuesta fija — no delegar al modelo para riesgo vital
            respuesta_riesgo = "Oye, lo que acabas de decir no lo voy a guardar solo. Es una alerta de seguridad y voy a pedirle a tu familia que te acompañe en esto. No es para castigarte — es para que no cargues solo con eso."
            await db.execute("INSERT INTO conversaciones VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4())[:8], mid, fid, rol, mensaje, respuesta_riesgo, time.time()))
            await db.commit()
            return {"ok": True, "motor": "teens", "respuesta": respuesta_riesgo, "rol": rol, "alerta": "riesgo_alto"}

        # ── Otros temas sensibles ──
        if not es_riesgo_vital and rol in ("teen", "hermano") and mensaje:
            tema = detectar_tema(mensaje)
            if tema:
                await registrar_alerta(db, fid, mid, tema)
                await db.commit()

        # ── Historial reciente ──
        cur_h = await db.execute(
            "SELECT mensaje, respuesta FROM conversaciones WHERE miembro_id=? ORDER BY creado DESC LIMIT 4",
            (mid,)
        )
        rows_h = await cur_h.fetchall()
        historial = []
        for h in reversed(rows_h):
            historial += [{"role": "user", "content": h[0]}, {"role": "assistant", "content": h[1]}]

        # ── Construir prompt ──
        if rol in ("padre", "madre"):
            prompt = await _build_prompt_padre(db, nombre, fid)
        else:
            last_mood = await get_last_mood(db, mid)
            teen_agreements = await _get_teen_agreements(db, fid, mid)
            active_ctx_str = ctx.get("tema_principal", "ninguno")
            materia = detectar_materia(mensaje)
            base_prompt = PROMPT_TEEN.format(
                nombre=nombre,
                edad=miembro.get("edad", 15),
                last_mood=last_mood,
                active_context=active_ctx_str,
                teen_agreements=teen_agreements,
            )
            if materia:
                base_prompt += f"\n\nNota: el tema actual es de {materia}. Aplica tutor_mode."
            prompt = base_prompt

        # ── Sin mensaje ──
        if not mensaje:
            if rol in ("padre", "madre"):
                return {"ok": True, "motor": "teens", "respuesta": f"Hola {nombre}. ¿Qué quieres revisar?"}
            # Primer mensaje de sesión
            return {"ok": True, "motor": "teens", "respuesta": "Aquí estoy. Qué hay."}

        # ── Llamar IA ──
        respuesta = await llamar_ia(prompt, mensaje, historial)

        # ── Guardar conversación ──
        await db.execute(
            "INSERT INTO conversaciones VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4())[:8], mid, fid, rol, mensaje, respuesta, time.time())
        )

        # ── Actualizar cache de identidad (async sin bloquear respuesta) ──
        nuevo_ctx = await _resumir_contexto(prompt, mensaje, respuesta)
        if nuevo_ctx:
            await db.execute(
                "UPDATE miembros SET active_context=? WHERE id=?",
                (json.dumps(nuevo_ctx, ensure_ascii=False), mid)
            )

        await db.commit()

        return {"ok": True, "motor": "teens", "respuesta": respuesta, "rol": rol}


# ── Helpers internos ──────────────────────────────────────────────────────────

async def _resumen_familia(db, familia_id: str) -> dict:
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT COUNT(*) FROM miembros WHERE familia_id=?", (familia_id,))
    m = (await cur.fetchone())[0]
    cur2 = await db.execute("SELECT COUNT(*) FROM misiones WHERE familia_id=? AND estado='pendiente'", (familia_id,))
    p = (await cur2.fetchone())[0]
    cur3 = await db.execute("SELECT COUNT(*) FROM acuerdos WHERE familia_id=? AND estado='activo'", (familia_id,))
    a = (await cur3.fetchone())[0]
    return {"ok": True, "motor": "teens",
            "respuesta": f"Familia activa — {m} miembros · {p} misiones pendientes · {a} acuerdos activos.\nUsa tu miembro_id para respuesta personalizada."}


async def _build_prompt_padre(db, nombre: str, familia_id: str) -> str:
    db.row_factory = aiosqlite.Row
    cur_t = await db.execute(
        "SELECT nombre FROM miembros WHERE familia_id=? AND rol IN ('teen','hermano') LIMIT 1", (familia_id,)
    )
    tr = await cur_t.fetchone()
    teen_nombre = tr[0] if tr else "tu hijo/a"

    cur_a = await db.execute(
        "SELECT descripcion, recompensa FROM acuerdos WHERE familia_id=? AND estado='activo'", (familia_id,)
    )
    acuerdos = [dict(r) for r in await cur_a.fetchall()]
    acuerdos_txt = "\n".join([f"  • {a['descripcion']} → {a['recompensa'] or 'sin recompensa definida'}"
                               for a in acuerdos]) or "Sin acuerdos activos."

    cur_al = await db.execute(
        "SELECT tipo, sugerencia FROM alertas WHERE familia_id=? AND visto=0 ORDER BY creado DESC LIMIT 3",
        (familia_id,)
    )
    alertas = [dict(r) for r in await cur_al.fetchall()]
    alertas_txt = "\n".join([f"  [{a['tipo']}] {a['sugerencia']}" for a in alertas]) or "Sin señales recientes."

    return PROMPT_PADRE.format(nombre=nombre, teen=teen_nombre, acuerdos=acuerdos_txt, alertas=alertas_txt)


async def _get_teen_agreements(db, familia_id: str, teen_id: str) -> str:
    db.row_factory = aiosqlite.Row
    cur = await db.execute(
        "SELECT descripcion FROM acuerdos WHERE familia_id=? AND teen_id=? AND estado='activo'",
        (familia_id, teen_id)
    )
    rows = await cur.fetchall()
    return ", ".join([r[0] for r in rows]) if rows else "ninguno"


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TEENS_PORT", 8005))
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False, log_level="warning")

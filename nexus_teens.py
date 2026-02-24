"""
nexus_teens.py — NEXUS Teens: Motor de desarrollo juvenil y marketing viral.

¿Qué hace este módulo?
  El chaval NO es el cliente — ES el contenido. NEXUS Teens convierte
  las habilidades naturales de los jóvenes en activos de marketing reales.

Componentes:
  1. IMPULSOR DE APTITUDES  — Detecta, mide y potencia 7 aptitudes clave.
                               Cada misión completada suma XP a aptitudes.
                               Roadmap de desarrollo personalizado.

  2. GAMIFICACIÓN           — Tokens, misiones, niveles, racha diaria,
                               badges, leaderboard semanal.

  3. GENERADOR VIRAL        — Hooks TikTok, guiones Reel 60s, hashtags
                               trending, ideas de challenge.

  4. TUTOR IA               — Explica temas con Groq + genera quiz de 3 preguntas.

  5. CONTROL PARENTAL       — Panel de acceso para padres: activar/desactivar
                               módulos, ver actividad, fijar horarios.

  6. RADAR DE TALENTO       — Datos para gráfico tipo spider/radar en el front.

Datos en CONFIG/teens_data.json
"""

import os
import json
import datetime
import random

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
DATA_PATH  = os.path.join(CONFIG_DIR, "teens_data.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

# ── Catálogo de aptitudes ──────────────────────────────────────────────────────

APTITUDES = {
    "creatividad": {
        "nombre":  "Creatividad",
        "emoji":   "🎨",
        "color":   "#ff6b9d",
        "descripcion": "Generas ideas originales, diseñas y expresas tu mundo único.",
        "niveles": ["Aprendiz", "Creativo", "Artista", "Visionario", "Genio Creativo"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["diseño", "contenido", "video", "reel", "edicion"],
        "roadmap": [
            "Crea tu primer post con identidad visual propia",
            "Diseña una miniatura de video con herramienta gratuita",
            "Sube un reel con tu propio guión y música",
            "Lanza tu primera campaña visual de 5 posts",
            "Crea un branding completo para un proyecto propio",
        ],
    },
    "comunicacion": {
        "nombre":  "Comunicación",
        "emoji":   "🎤",
        "color":   "#4ecdc4",
        "descripcion": "Hablas, escribes y convences. El mundo te escucha.",
        "niveles": ["Tímido", "Comunicador", "Influyente", "Orador", "Líder de Opinión"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["copy", "caption", "guion", "presentacion", "podcast"],
        "roadmap": [
            "Escribe 5 captions para redes con gancho emocional",
            "Graba un video de 30 segundos contando algo que sabes",
            "Genera un guión completo de TikTok y grábalo",
            "Presenta un tema frente a 3 personas y recibe feedback",
            "Construye una audiencia de 100 seguidores reales",
        ],
    },
    "liderazgo": {
        "nombre":  "Liderazgo",
        "emoji":   "🚀",
        "color":   "#ffe66d",
        "descripcion": "Inspiras, organizas y llevas proyectos al siguiente nivel.",
        "niveles": ["Seguidor", "Organizador", "Líder", "Capitán", "Visionario"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["proyecto", "equipo", "reto", "challenge", "mision_grupal"],
        "roadmap": [
            "Organiza un reto grupal con al menos 3 participantes",
            "Completa 5 misiones consecutivas sin fallar (racha)",
            "Ayuda a otro usuario a completar su primera misión",
            "Lidera una campaña de marketing para un negocio local",
            "Crea y dirige tu propio proyecto de 30 días",
        ],
    },
    "tecnologia": {
        "nombre":  "Tecnología",
        "emoji":   "💻",
        "color":   "#a8ff78",
        "descripcion": "Dominas herramientas digitales y entiendes cómo funciona el mundo tech.",
        "niveles": ["Novato", "Usuario", "Técnico", "Developer", "Tech Master"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["herramienta", "app", "automatizacion", "edicion", "ia"],
        "roadmap": [
            "Aprende a usar una herramienta de IA (Canva, CapCut, NEXUS)",
            "Automatiza una tarea repetitiva con NEXUS",
            "Crea una landing page o formulario digital",
            "Edita un video con efectos y subtítulos automáticos",
            "Construye un flujo de trabajo digital completo",
        ],
    },
    "emprendimiento": {
        "nombre":  "Emprendimiento",
        "emoji":   "💡",
        "color":   "#ff9a3c",
        "descripcion": "Ves oportunidades donde otros ven problemas. Construyes.",
        "niveles": ["Observador", "Explorador", "Emprendedor", "Fundador", "CEO"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["negocio", "ventas", "cliente", "cotizacion", "propuesta"],
        "roadmap": [
            "Identifica un problema en tu comunidad que puedas resolver",
            "Diseña un servicio o producto que podrías ofrecer",
            "Consigue tu primer cliente o pedido real",
            "Genera tu primera factura o cobro formal",
            "Lanza tu primer negocio con plan de marketing propio",
        ],
    },
    "arte": {
        "nombre":  "Arte Visual",
        "emoji":   "🌈",
        "color":   "#c471ed",
        "descripcion": "Fotografía, ilustración, animación. Tu ojo es único.",
        "niveles": ["Observador", "Ilustrador", "Artista", "Maestro", "Iconos"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["foto", "ilustracion", "animacion", "sticker", "logo"],
        "roadmap": [
            "Toma 10 fotos con buena composición y edítalas",
            "Crea un set de 5 stickers para tu comunidad",
            "Diseña el logo de un proyecto o negocio pequeño",
            "Crea una animación corta (GIF o Reel animado)",
            "Publica un portafolio digital con tu mejor trabajo",
        ],
    },
    "bienestar": {
        "nombre":  "Bienestar",
        "emoji":   "🧘",
        "color":   "#56ab2f",
        "descripcion": "Cuidas tu mente y cuerpo. Eres productivo y equilibrado.",
        "niveles": ["Errático", "Consciente", "Equilibrado", "Atleta Mental", "Maestro Zen"],
        "xp_por_nivel": [0, 200, 500, 1000, 2000],
        "misiones_tipo": ["habito", "pausa", "ejercicio", "meditacion", "racha"],
        "roadmap": [
            "Completa 7 días consecutivos en la app (racha)",
            "Activa 3 sesiones de audio de bienestar de la galería",
            "Establece y cumple tu horario de trabajo/estudio 5 días",
            "Haz una pausa activa después de cada sesión larga",
            "Mantén una racha de 30 días de actividad diaria",
        ],
    },
}

# ── Catálogo de misiones ───────────────────────────────────────────────────────

MISIONES_CATALOGO = [
    # DIARIAS
    {"id": "D01", "nombre": "Primer paso del día",     "desc": "Abre NEXUS Teens y revisa tus misiones activas.",
     "xp": 10,  "tokens": 5,   "tipo": "habito",     "frecuencia": "diaria",  "aptitud": "bienestar"},
    {"id": "D02", "nombre": "Idea viral del día",       "desc": "Genera una idea viral y guárdala en tu bitácora.",
     "xp": 20,  "tokens": 10,  "tipo": "contenido",  "frecuencia": "diaria",  "aptitud": "creatividad"},
    {"id": "D03", "nombre": "Caption gancho",           "desc": "Escribe un caption con gancho para Instagram o TikTok.",
     "xp": 25,  "tokens": 15,  "tipo": "copy",       "frecuencia": "diaria",  "aptitud": "comunicacion"},
    {"id": "D04", "nombre": "Aprende algo nuevo",       "desc": "Usa el tutor IA para aprender sobre un tema de tu interés.",
     "xp": 30,  "tokens": 20,  "tipo": "ia",         "frecuencia": "diaria",  "aptitud": "tecnologia"},

    # SEMANALES
    {"id": "S01", "nombre": "Reel completo",            "desc": "Genera el guión, graba y sube un Reel de 30-60 segundos.",
     "xp": 100, "tokens": 60,  "tipo": "reel",       "frecuencia": "semanal", "aptitud": "creatividad"},
    {"id": "S02", "nombre": "Challenge lanzado",        "desc": "Crea y lanza un reto/challenge para tus seguidores.",
     "xp": 120, "tokens": 70,  "tipo": "challenge",  "frecuencia": "semanal", "aptitud": "liderazgo"},
    {"id": "S03", "nombre": "5 posts en 5 días",        "desc": "Publica contenido 5 días consecutivos.",
     "xp": 150, "tokens": 80,  "tipo": "contenido",  "frecuencia": "semanal", "aptitud": "comunicacion"},
    {"id": "S04", "nombre": "Primer cliente teens",     "desc": "Ofrece un servicio (diseño, edición, clase) y consigue un cliente.",
     "xp": 200, "tokens": 120, "tipo": "negocio",    "frecuencia": "semanal", "aptitud": "emprendimiento"},
    {"id": "S05", "nombre": "Portafolio digital",       "desc": "Crea o actualiza tu portafolio con 5 trabajos recientes.",
     "xp": 180, "tokens": 100, "tipo": "arte",       "frecuencia": "semanal", "aptitud": "arte"},
    {"id": "S06", "nombre": "Racha de 7 días",          "desc": "Abre y usa NEXUS Teens 7 días seguidos.",
     "xp": 200, "tokens": 150, "tipo": "racha",      "frecuencia": "semanal", "aptitud": "bienestar"},
    {"id": "S07", "nombre": "Herramienta nueva",        "desc": "Aprende y usa una herramienta tech que no conocías.",
     "xp": 100, "tokens": 60,  "tipo": "herramienta","frecuencia": "semanal", "aptitud": "tecnologia"},

    # ÉPICAS (logros únicos)
    {"id": "E01", "nombre": "¡Primera vez!",            "desc": "Completa tu primera misión en NEXUS Teens.",
     "xp": 50,  "tokens": 30,  "tipo": "habito",     "frecuencia": "unica",   "aptitud": "bienestar"},
    {"id": "E02", "nombre": "Talento descubierto",      "desc": "Alcanza nivel 2 en cualquier aptitud.",
     "xp": 300, "tokens": 200, "tipo": "aptitud",    "frecuencia": "unica",   "aptitud": "creatividad"},
    {"id": "E03", "nombre": "Influencer en potencia",   "desc": "Alcanza nivel 3 en Comunicación.",
     "xp": 500, "tokens": 350, "tipo": "aptitud",    "frecuencia": "unica",   "aptitud": "comunicacion"},
    {"id": "E04", "nombre": "Mini CEO",                 "desc": "Consigue 3 clientes reales con tus servicios.",
     "xp": 800, "tokens": 500, "tipo": "negocio",    "frecuencia": "unica",   "aptitud": "emprendimiento"},
    {"id": "E05", "nombre": "Colección completa",       "desc": "Obtén al menos 1 badge en todas las aptitudes.",
     "xp": 1000,"tokens": 700, "tipo": "aptitud",    "frecuencia": "unica",   "aptitud": "liderazgo"},
]

# ── Badges ────────────────────────────────────────────────────────────────────

BADGES = {
    "primera_mision":   {"nombre": "Primeros Pasos",     "emoji": "👟", "desc": "Completaste tu primera misión"},
    "racha_7":          {"nombre": "Semana Perfecta",     "emoji": "🔥", "desc": "7 días de racha"},
    "racha_30":         {"nombre": "Mes Legendario",      "emoji": "⚡", "desc": "30 días de racha"},
    "creativo_2":       {"nombre": "Mente Creativa",      "emoji": "🎨", "desc": "Nivel 2 en Creatividad"},
    "comunicador_2":    {"nombre": "Voz que Conecta",     "emoji": "🎤", "desc": "Nivel 2 en Comunicación"},
    "lider_2":          {"nombre": "Nace un Líder",       "emoji": "🚀", "desc": "Nivel 2 en Liderazgo"},
    "tech_2":           {"nombre": "Digital Native",      "emoji": "💻", "desc": "Nivel 2 en Tecnología"},
    "emprendedor_2":    {"nombre": "Instinto Emprendedor","emoji": "💡", "desc": "Nivel 2 en Emprendimiento"},
    "artista_2":        {"nombre": "Ojo de Artista",      "emoji": "🌈", "desc": "Nivel 2 en Arte Visual"},
    "zen_2":            {"nombre": "Mente Equilibrada",   "emoji": "🧘", "desc": "Nivel 2 en Bienestar"},
    "viral":            {"nombre": "Viral en Potencia",   "emoji": "📱", "desc": "Generaste 10 ideas virales"},
    "mini_ceo":         {"nombre": "Mini CEO",            "emoji": "👑", "desc": "Primer cliente real"},
    "completo":         {"nombre": "Todo Terreno",        "emoji": "🏆", "desc": "Badge en todas las aptitudes"},
}

# ── Hooks virales por categoría ────────────────────────────────────────────────

HOOKS_TIKTOK = {
    "creatividad": [
        "Hice esto con solo 3 colores y nadie lo creyó 🎨",
        "El truco de diseño que aprenden en universidad pero gratis aquí 👇",
        "POV: descubres que tienes talento de artista a los {edad} 🤯",
        "De 0 a creativo en 30 días — mi proceso real",
        "Este efecto lo uso en todos mis posts y nadie sabe cómo 🔥",
    ],
    "comunicacion": [
        "3 palabras que hacen que la gente haga scroll STOP 📱",
        "Así escribo captions que generan comentarios reales",
        "El secreto de los influencers para hablar frente a cámara",
        "POV: aprendes a vender sin sonar a vendedor 😮",
        "Este gancho hizo que mi video llegara a 10k personas",
    ],
    "liderazgo": [
        "Organicé un reto con mis amigos y esto pasó 🚀",
        "Cómo conseguí que 10 personas siguieran mi idea en 48h",
        "El hack de productividad que usan los líderes de 17 años",
        "Lideré mi primer proyecto a los {edad} y aprendí esto",
        "¿Eres el líder del grupo o solo crees que lo eres? 👀",
    ],
    "emprendimiento": [
        "Cobré mi primer $500 pesos con esta habilidad 💰",
        "Tienes un negocio en tus manos y no lo ves 👀",
        "De cliente a jefe en 3 semanas — mi historia real",
        "El error que cometí al lanzar mi primer servicio",
        "Esta app me ayudó a conseguir mi primer cliente sin salir de casa",
    ],
    "tecnologia": [
        "5 apps que usan los creadores de contenido exitosos 🛠️",
        "Aprendí esto de IA en 10 minutos y cambió todo",
        "El workflow de un creador digital en un día normal",
        "Automaticé esto y me ahorré 3 horas semanales ⚡",
        "CapCut + IA = contenido que parece producción profesional",
    ],
    "general": [
        "Lo que aprendí en {dias} días usando NEXUS Teens 🚀",
        "3 habilidades que te pagan aunque seas estudiante",
        "POV: empiezas a tomarte en serio tu potencial 💪",
        "Antes vs Ahora — mi evolución real en 30 días",
        "Nadie me enseñó esto en la escuela pero cambió mi vida",
    ],
}

HASHTAGS_TEENS = {
    "creatividad":    ["#CreativosLatam", "#DesignerLife", "#ArteTeen", "#CreaTuContenido", "#NexusCreativo"],
    "comunicacion":   ["#ContentCreator", "#TikTokTips", "#CaptionHacks", "#HablaYConvence", "#NexusVoz"],
    "liderazgo":      ["#LíderesJóvenes", "#GenZ", "#EquipoGanador", "#Reto30Días", "#NexusLíder"],
    "emprendimiento": ["#EmprendedorJoven", "#NegociosTeen", "#PrimerCliente", "#JóvenesEmprendedores", "#NexusBusiness"],
    "tecnologia":     ["#TechTeen", "#IACreativa", "#HerramientasDigitales", "#FuturoDigital", "#NexusTech"],
    "arte":           ["#ArteDigital", "#IllustracionMX", "#CreadorDeContenido", "#DiseñoLatam", "#NexusArte"],
    "general":        ["#NexusTeens", "#JóvenesTalentosos", "#GenZMéxico", "#PotencialJoven", "#SoyNexus"],
}

# ── Gestión de datos ───────────────────────────────────────────────────────────

def _cargar_datos() -> dict:
    try:
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return _datos_iniciales()


def _guardar_datos(data: dict):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _datos_iniciales() -> dict:
    return {
        "usuarios": {},           # {user_id: {...perfil}}
        "leaderboard": [],        # top 10 de la semana
        "semana_actual": _semana_actual(),
        "total_misiones_completadas": 0,
    }


def _semana_actual() -> str:
    hoy = datetime.date.today()
    return f"{hoy.year}-W{hoy.isocalendar()[1]:02d}"


def _perfil_inicial(nombre: str, edad: int = 16) -> dict:
    return {
        "nombre":    nombre,
        "edad":      edad,
        "tokens":    0,
        "xp_total":  0,
        "racha":     0,
        "ultimo_dia": None,
        "nivel_global": 1,
        "aptitudes": {k: {"xp": 0, "nivel": 0} for k in APTITUDES},
        "misiones_completadas": [],
        "badges": [],
        "ideas_generadas": 0,
        "clientes_conseguidos": 0,
        "control_parental": {
            "activo":          False,
            "modulos_bloq":    [],
            "horario_inicio":  "07:00",
            "horario_fin":     "22:00",
            "padre_pin":       "0000",
        },
        "creado": datetime.datetime.now().isoformat(),
    }


# ── API pública ────────────────────────────────────────────────────────────────

def registrar_usuario(user_id: str, nombre: str, edad: int = 16) -> dict:
    """Registra un nuevo usuario teens o retorna el existente."""
    data = _cargar_datos()
    if user_id not in data["usuarios"]:
        data["usuarios"][user_id] = _perfil_inicial(nombre, edad)
        _guardar_datos(data)
        return {"ok": True, "nuevo": True, "perfil": data["usuarios"][user_id]}
    return {"ok": True, "nuevo": False, "perfil": data["usuarios"][user_id]}


def get_perfil(user_id: str) -> dict:
    """Retorna el perfil completo del usuario con niveles calculados."""
    data = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    # Calcular nivel de cada aptitud
    for apt_key, apt_data in perfil["aptitudes"].items():
        xp = apt_data["xp"]
        nivel = 0
        umbrales = APTITUDES[apt_key]["xp_por_nivel"]
        for i, umbral in enumerate(umbrales):
            if xp >= umbral:
                nivel = i
        apt_data["nivel"]     = nivel
        apt_data["nombre"]    = APTITUDES[apt_key]["nombre"]
        apt_data["emoji"]     = APTITUDES[apt_key]["emoji"]
        apt_data["color"]     = APTITUDES[apt_key]["color"]
        apt_data["nombre_nivel"] = APTITUDES[apt_key]["niveles"][min(nivel, len(APTITUDES[apt_key]["niveles"])-1)]
        # Próximo umbral
        if nivel < len(umbrales) - 1:
            apt_data["xp_siguiente"] = umbrales[nivel + 1]
            apt_data["xp_falta"]     = umbrales[nivel + 1] - xp
            apt_data["progreso_pct"] = int((xp - umbrales[nivel]) / max(1, umbrales[nivel+1] - umbrales[nivel]) * 100)
        else:
            apt_data["xp_siguiente"] = xp
            apt_data["xp_falta"]     = 0
            apt_data["progreso_pct"] = 100

    # Radar data para el gráfico
    perfil["radar"] = {
        k: min(100, int(v["xp"] / max(1, APTITUDES[k]["xp_por_nivel"][-1]) * 100))
        for k, v in perfil["aptitudes"].items()
    }

    # Siguiente misión sugerida
    completadas = set(perfil.get("misiones_completadas", []))
    pendientes  = [m for m in MISIONES_CATALOGO if m["id"] not in completadas]
    perfil["mision_sugerida"] = pendientes[0] if pendientes else None

    return {"ok": True, "perfil": perfil}


def completar_mision(user_id: str, mision_id: str) -> dict:
    """Marca una misión como completada. Suma XP, tokens y actualiza aptitudes."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    mision = next((m for m in MISIONES_CATALOGO if m["id"] == mision_id), None)
    if not mision:
        return {"ok": False, "error": f"Misión {mision_id} no existe"}

    completadas = perfil.get("misiones_completadas", [])

    # Misiones únicas no se repiten
    if mision["frecuencia"] == "unica" and mision_id in completadas:
        return {"ok": False, "error": "Esta misión única ya fue completada"}

    # Actualizar tokens y XP global
    perfil["tokens"]   = perfil.get("tokens", 0) + mision["tokens"]
    perfil["xp_total"] = perfil.get("xp_total", 0) + mision["xp"]

    # XP a la aptitud correspondiente
    apt_key = mision.get("aptitud", "bienestar")
    if apt_key in perfil["aptitudes"]:
        perfil["aptitudes"][apt_key]["xp"] = perfil["aptitudes"][apt_key].get("xp", 0) + mision["xp"]

    # Registrar
    if mision["frecuencia"] == "unica":
        completadas.append(mision_id)
    perfil["misiones_completadas"] = completadas

    # Racha diaria
    hoy = str(datetime.date.today())
    ultimo = perfil.get("ultimo_dia")
    ayer   = str(datetime.date.today() - datetime.timedelta(days=1))
    if ultimo == ayer:
        perfil["racha"] = perfil.get("racha", 0) + 1
    elif ultimo != hoy:
        perfil["racha"] = 1
    perfil["ultimo_dia"] = hoy

    # Nivel global
    perfil["nivel_global"] = min(50, 1 + perfil["xp_total"] // 300)

    # Verificar badges
    nuevos_badges = _verificar_badges(perfil)

    data["total_misiones_completadas"] = data.get("total_misiones_completadas", 0) + 1
    _guardar_datos(data)

    return {
        "ok":           True,
        "mision":       mision["nombre"],
        "xp_ganado":    mision["xp"],
        "tokens_ganado":mision["tokens"],
        "tokens_total": perfil["tokens"],
        "racha":        perfil["racha"],
        "nuevos_badges":nuevos_badges,
        "nivel_global": perfil["nivel_global"],
    }


def _verificar_badges(perfil: dict) -> list:
    """Verifica si el usuario ganó nuevos badges. Retorna lista de nuevos."""
    nuevos = []
    badges_actuales = set(perfil.get("badges", []))

    def _add(badge_id):
        if badge_id not in badges_actuales:
            badges_actuales.add(badge_id)
            nuevos.append({**BADGES[badge_id], "id": badge_id})

    completadas = set(perfil.get("misiones_completadas", []))
    racha       = perfil.get("racha", 0)
    aptitudes   = perfil.get("aptitudes", {})

    if completadas:
        _add("primera_mision")
    if racha >= 7:
        _add("racha_7")
    if racha >= 30:
        _add("racha_30")

    niveles_map = {
        "creatividad":    "creativo_2",
        "comunicacion":   "comunicador_2",
        "liderazgo":      "lider_2",
        "tecnologia":     "tech_2",
        "emprendimiento": "emprendedor_2",
        "arte":           "artista_2",
        "bienestar":      "zen_2",
    }
    for apt_key, badge_id in niveles_map.items():
        if aptitudes.get(apt_key, {}).get("xp", 0) >= APTITUDES[apt_key]["xp_por_nivel"][2]:
            _add(badge_id)

    if perfil.get("clientes_conseguidos", 0) >= 1:
        _add("mini_ceo")

    if perfil.get("ideas_generadas", 0) >= 10:
        _add("viral")

    # Colección completa = badge en cada aptitud
    badges_con = {b.replace("_2","") for b in badges_actuales if b.endswith("_2")}
    if all(k in badges_con for k in ["creativo","comunicador","lider","tech","emprendedor","artista","zen"]):
        _add("completo")

    perfil["badges"] = list(badges_actuales)
    return nuevos


def generar_idea_viral(aptitud: str = "general", nombre_negocio: str = "", edad: int = 17) -> dict:
    """Genera idea viral TikTok/Instagram adaptada a la aptitud."""
    apt = aptitud if aptitud in HOOKS_TIKTOK else "general"
    hooks = HOOKS_TIKTOK[apt]
    hook  = random.choice(hooks).replace("{edad}", str(edad)).replace("{dias}", str(random.choice([14,21,30,45,60])))

    hashtags_base  = HASHTAGS_TEENS.get(apt, [])
    hashtags_extra = HASHTAGS_TEENS["general"]
    hashtags = list(dict.fromkeys(hashtags_base + hashtags_extra))[:7]

    formatos = {
        "creatividad":    "Reel de proceso (time-lapse + reveal)",
        "comunicacion":   "Tutorial rápido / Talking head con texto animado",
        "liderazgo":      "POV story con CTA de participación",
        "emprendimiento": "Before/After o '¿Cuánto cobro por esto?'",
        "tecnologia":     "Pantalla compartida con voz en off",
        "arte":           "Speed art con música trending",
        "general":        "Storytelling corto con giro al final",
    }

    captions = [
        f"{hook}\n\n¿A ti también te pasó? Comenta 👇\n\n{' '.join(hashtags)}",
        f"💡 {hook}\n\nGuarda este video para cuando lo necesites.\n\n{' '.join(hashtags)}",
        f"Nadie habla de esto… 👀\n{hook}\n\nSígueme para más tips.\n\n{' '.join(hashtags)}",
    ]

    return {
        "ok":        True,
        "hook":      hook,
        "formato":   formatos.get(apt, formatos["general"]),
        "caption":   random.choice(captions),
        "hashtags":  hashtags,
        "plataforma":["TikTok", "Instagram Reels"],
        "duracion":  "15-60 segundos",
        "tip_extra": _tip_viral(apt),
    }


def _tip_viral(apt: str) -> str:
    tips = {
        "creatividad":    "Los primeros 2 segundos son todo. Muestra el resultado final primero.",
        "comunicacion":   "Habla directo a la cámara. El contacto visual genera conexión real.",
        "liderazgo":      "Termina con una pregunta. Los comentarios disparan el algoritmo.",
        "emprendimiento": "Muestra el dinero o el resultado concreto. La gente quiere ver prueba.",
        "tecnologia":     "Los 'antes y después' con herramientas digitales siempre funcionan.",
        "arte":           "El proceso es tan viral como el resultado. Graba todo desde el inicio.",
        "general":        "Música trending + texto grande + ritmo rápido = views garantizados.",
    }
    return tips.get(apt, tips["general"])


def generar_guion_reel(tema: str, aptitud: str = "general", duracion: int = 60) -> dict:
    """Genera guión completo para un Reel de TikTok/Instagram."""
    idea = generar_idea_viral(aptitud)
    hook = idea["hook"]

    if duracion <= 30:
        estructura = [
            {"seg": "0-3s",   "accion": "HOOK — " + hook},
            {"seg": "3-15s",  "accion": "Muestra el punto principal rápido, sin introducción"},
            {"seg": "15-25s", "accion": "El valor/tip/reveal central"},
            {"seg": "25-30s", "accion": "CTA: 'Guarda esto' / 'Sígueme' / 'Comenta X si te pasó'"},
        ]
    else:
        estructura = [
            {"seg": "0-3s",   "accion": "HOOK — " + hook},
            {"seg": "3-8s",   "accion": "Presenta de qué va el video (SIN introducciones largas)"},
            {"seg": "8-30s",  "accion": f"Punto 1: {tema} — muestra, no solo cuentes"},
            {"seg": "30-45s", "accion": "Punto 2: El tip/proceso/método clave"},
            {"seg": "45-55s", "accion": "Resultado o transformación visible"},
            {"seg": "55-60s", "accion": "CTA fuerte: '¿Te funcionó? Comenta'"},
        ]

    return {
        "ok":        True,
        "tema":      tema,
        "hook":      hook,
        "duracion":  f"{duracion}s",
        "estructura":estructura,
        "caption":   idea["caption"],
        "hashtags":  idea["hashtags"],
        "formato":   idea["formato"],
        "tip":       idea["tip_extra"],
    }


def impulsar_aptitud(user_id: str, aptitud: str) -> dict:
    """
    Retorna el plan de impulso personalizado para una aptitud.
    Incluye nivel actual, XP, roadmap y siguiente misión recomendada.
    """
    if aptitud not in APTITUDES:
        return {"ok": False, "error": f"Aptitud '{aptitud}' no existe"}

    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    apt_info   = APTITUDES[aptitud]
    apt_perfil = perfil["aptitudes"].get(aptitud, {"xp": 0})
    xp_actual  = apt_perfil.get("xp", 0)
    umbrales   = apt_info["xp_por_nivel"]

    # Nivel actual
    nivel = 0
    for i, u in enumerate(umbrales):
        if xp_actual >= u:
            nivel = i

    nombre_nivel = apt_info["niveles"][min(nivel, len(apt_info["niveles"])-1)]
    paso_roadmap = min(nivel, len(apt_info["roadmap"]) - 1)

    # Misiones pendientes de esta aptitud
    completadas = set(perfil.get("misiones_completadas", []))
    misiones_apt = [
        m for m in MISIONES_CATALOGO
        if m.get("aptitud") == aptitud and m["id"] not in completadas
    ]

    return {
        "ok":           True,
        "aptitud":      aptitud,
        "nombre":       apt_info["nombre"],
        "emoji":        apt_info["emoji"],
        "color":        apt_info["color"],
        "nivel_actual": nivel,
        "nombre_nivel": nombre_nivel,
        "xp_actual":    xp_actual,
        "xp_siguiente": umbrales[nivel + 1] if nivel < len(umbrales)-1 else xp_actual,
        "falta_xp":     max(0, umbrales[nivel+1] - xp_actual) if nivel < len(umbrales)-1 else 0,
        "descripcion":  apt_info["descripcion"],
        "paso_actual_roadmap": apt_info["roadmap"][paso_roadmap],
        "roadmap_completo":    apt_info["roadmap"],
        "misiones_pendientes": misiones_apt[:3],
        "consejo": _consejo_aptitud(aptitud, nivel),
    }


def _consejo_aptitud(aptitud: str, nivel: int) -> str:
    consejos = {
        "creatividad": [
            "Copia lo que admiras hasta que encuentres tu propia voz. Todo creativo empezó así.",
            "La consistencia supera al talento. 10 posts regulares valen más que 1 perfecto.",
            "Tu proceso es tan valioso como tu resultado. Muéstralo.",
            "Los mejores creativos roban con elegancia. Estudia a quienes te inspiran.",
            "Ya tienes un estilo único. Solo necesitas publicarlo más.",
        ],
        "comunicacion": [
            "Habla como le hablas a un amigo. La gente huye del lenguaje formal en redes.",
            "El gancho es el 80% del trabajo. Si el primer segundo no engancha, nada más importa.",
            "Escucha más de lo que hablas. Los mejores comunicadores son grandes oyentes.",
            "Tu historia personal vende más que cualquier argumento técnico.",
            "Ya tienes la voz. Solo falta subirle el volumen.",
        ],
        "liderazgo": [
            "Un líder no da órdenes — da ejemplo. ¿Tú harías lo que le pides a otros?",
            "Los mejores líderes jóvenes empiezan liderando su propia vida.",
            "Empieza con proyectos pequeños. El liderazgo se entrena, no se nace.",
            "Tu equipo es tu espejo. Elige bien a quién te rodeas.",
            "Ya lideras algo. Identifica qué y escálalo.",
        ],
        "emprendimiento": [
            "El primer cliente es el más difícil. Los siguientes vienen solos si cumples bien.",
            "No esperes tener todo perfecto. Lanza y mejora sobre la marcha.",
            "Tu habilidad más obvia para ti es invisible y valiosa para otros.",
            "El dinero sigue al valor. Enfócate en resolver problemas reales.",
            "Ya eres emprendedor. Solo falta que empieces a cobrar por lo que haces.",
        ],
        "tecnologia": [
            "La mejor herramienta es la que realmente usas. Domina una antes de aprender diez.",
            "La IA no te va a reemplazar. Pero quien use IA sí podría hacerlo.",
            "Aprende lo básico de cada herramienta — el 80% del potencial está en el 20% de funciones.",
            "La tecnología es un multiplicador de talento. ¿Qué talento tienes que multiplicar?",
            "Ya estás en el nivel correcto para aprender lo que necesitas. El internet es gratis.",
        ],
        "arte": [
            "El arte no tiene que gustarle a todos — solo a tu audiencia ideal.",
            "Crea algo feo hoy. La perfección es el enemigo del progreso.",
            "Tu estilo único se forja repitiendo, no pensando.",
            "Sube el trabajo 'imperfecto'. Ese es el que más conecta.",
            "El ojo se entrena mirando. Sigue a 10 artistas que admires.",
        ],
        "bienestar": [
            "Sin energía no hay creatividad. Tu cuerpo y mente son tu herramienta más importante.",
            "La racha no es un juego — entrena tu disciplina real.",
            "Trabaja en bloques de 25 minutos. Tu cerebro adolescente lo agradece.",
            "El descanso también es parte del proceso.",
            "Eres tu propia empresa. Cuida al activo principal.",
        ],
    }
    lista = consejos.get(aptitud, ["Sigue adelante. Cada misión te acerca más a tu versión ideal."])
    return lista[min(nivel, len(lista)-1)]


def get_leaderboard() -> list:
    """Top 10 usuarios por tokens de la semana actual."""
    data = _cargar_datos()
    semana = _semana_actual()

    if data.get("semana_actual") != semana:
        # Nueva semana: reset leaderboard
        data["semana_actual"] = semana
        data["leaderboard"]   = []
        _guardar_datos(data)

    usuarios = data.get("usuarios", {})
    ranking  = sorted(
        [{"id": k, "nombre": v.get("nombre","?"), "tokens": v.get("tokens",0),
          "nivel": v.get("nivel_global",1), "racha": v.get("racha",0),
          "badges": len(v.get("badges",[]))}
         for k, v in usuarios.items()],
        key=lambda x: x["tokens"], reverse=True
    )
    return ranking[:10]


def get_misiones(user_id: str = None, frecuencia: str = None) -> list:
    """Lista misiones con estado para un usuario."""
    completadas = set()
    if user_id:
        data = _cargar_datos()
        perfil = data["usuarios"].get(user_id, {})
        completadas = set(perfil.get("misiones_completadas", []))

    misiones = MISIONES_CATALOGO
    if frecuencia:
        misiones = [m for m in misiones if m["frecuencia"] == frecuencia]

    return [
        {**m,
         "completada":    m["id"] in completadas,
         "aptitud_info": {
             "nombre": APTITUDES[m["aptitud"]]["nombre"],
             "emoji":  APTITUDES[m["aptitud"]]["emoji"],
             "color":  APTITUDES[m["aptitud"]]["color"],
         }}
        for m in misiones
    ]


def get_aptitudes_catalogo() -> dict:
    """Retorna el catálogo de aptitudes para mostrar en UI."""
    return {k: {
        "nombre":      v["nombre"],
        "emoji":       v["emoji"],
        "color":       v["color"],
        "descripcion": v["descripcion"],
        "niveles":     v["niveles"],
        "roadmap":     v["roadmap"],
    } for k, v in APTITUDES.items()}


def control_parental_update(user_id: str, pin: str, config: dict) -> dict:
    """Actualiza configuración de control parental (requiere pin)."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("padre_pin", "0000") != pin:
        return {"ok": False, "error": "PIN incorrecto"}

    cp.update({k: v for k, v in config.items() if k in
               ["activo","modulos_bloq","horario_inicio","horario_fin","padre_pin"]})
    perfil["control_parental"] = cp
    _guardar_datos(data)
    return {"ok": True, "control_parental": cp}


# ══════════════════════════════════════════════════════════════════════════════
# BLOQUE FAMILIA — Padres + Teens: un solo ecosistema
# ══════════════════════════════════════════════════════════════════════════════
#
# Filosofía:
#   El teen y el padre NO usan apps separadas. Son el MISMO bloque.
#   El padre ve el progreso del teen en tiempo real.
#   El teen sabe que sus acciones tienen consecuencias reales (acuerdos).
#   La confianza se construye y se mide (Puntos de Confianza).
#   Los valores son compartidos, no impuestos.
#
# Componentes:
#   VALORES       — 7 valores core con misiones y reflexiones diarias
#   ACUERDOS      — Contratos digitales teen↔padre, firma de ambos, seguimiento
#   CONFIANZA     — Métrica independiente. Sube con acuerdos cumplidos.
#   CHECK-IN      — Estado de ánimo diario (emoji rápido). Padre ve tendencias.
#   RECONOCIMIENTOS — Padre da insignias al teen por acciones reales fuera de app
#   ECONOMÍA      — Tokens ↔ Privilegios. Padre define la tabla de canje.
#   CÓDIGO HONOR  — Manifiesto familiar de 5 frases firmado por ambos.
#   MONITOR       — Vista padre: progreso real, alertas, semana en resumen.
#
# Binaurales: EXCLUSIVAMENTE para adultos (padres con licencia NEXUS regular).
#             Teens NUNCA tienen acceso a binaurales por política de protección.
# ══════════════════════════════════════════════════════════════════════════════

# ── Catálogo de Valores ────────────────────────────────────────────────────────

VALORES = {
    "honestidad": {
        "nombre":      "Honestidad",
        "emoji":       "🤍",
        "color":       "#ffffff",
        "descripcion": "Dices la verdad aunque sea difícil. Tu palabra vale.",
        "reflexion":   "¿Hubo hoy un momento donde pudiste ser más honesto/a?",
        "misiones": [
            "Reconoce un error frente a alguien importante para ti",
            "Di lo que realmente piensas en una conversación difícil",
            "Corrige algo que hiciste mal, aunque nadie lo note",
        ],
    },
    "responsabilidad": {
        "nombre":      "Responsabilidad",
        "emoji":       "⚓",
        "color":       "#4ecdc4",
        "descripcion": "Cumples lo que prometes. Eres dueño/a de tus acciones.",
        "reflexion":   "¿Qué compromisos tienes pendientes que puedes cumplir hoy?",
        "misiones": [
            "Completa una tarea que habías dejado pendiente sin que te lo pidan",
            "Llega a tiempo a algo importante sin excusas",
            "Cumple un acuerdo familiar esta semana",
        ],
    },
    "respeto": {
        "nombre":      "Respeto",
        "emoji":       "🤝",
        "color":       "#ffe66d",
        "descripcion": "Tratas a todos con dignidad, incluyendo a quienes piensan diferente.",
        "reflexion":   "¿Hubo alguien hoy que merece un agradecimiento o disculpa?",
        "misiones": [
            "Escucha activamente a tu padre/madre sin interrumpir",
            "Agradece a alguien que normalmente das por hecho",
            "Trata bien a alguien con quien generalmente hay tensión",
        ],
    },
    "perseverancia": {
        "nombre":      "Perseverancia",
        "emoji":       "🔥",
        "color":       "#ff9a3c",
        "descripcion": "Cuando te caes, te levantas. El progreso es más importante que la perfección.",
        "reflexion":   "¿Qué dificulad superaste hoy, aunque sea pequeña?",
        "misiones": [
            "Completa algo que empezaste y no habías terminado",
            "Mantén una racha de 5 días en la app",
            "Sigue adelante con un proyecto después de un fracaso pequeño",
        ],
    },
    "creatividad": {
        "nombre":      "Creatividad",
        "emoji":       "🎨",
        "color":       "#ff6b9d",
        "descripcion": "Ves soluciones donde otros ven problemas. Tu perspectiva es única.",
        "reflexion":   "¿Resolviste algo hoy de una manera diferente o nueva?",
        "misiones": [
            "Propón una solución creativa a un problema en casa",
            "Crea algo (video, texto, dibujo) que refleje quién eres",
            "Encuentra una forma más eficiente de hacer algo cotidiano",
        ],
    },
    "gratitud": {
        "nombre":      "Gratitud",
        "emoji":       "💛",
        "color":       "#ffe66d",
        "descripcion": "Reconoces lo bueno que ya tienes mientras construyes lo que quieres.",
        "reflexion":   "Nombra 3 cosas concretas por las que estás agradecido/a hoy.",
        "misiones": [
            "Escribe 3 cosas que agradeces de tu familia hoy",
            "Dile a alguien en persona por qué lo valoras",
            "Haz algo bueno por alguien sin esperar nada a cambio",
        ],
    },
    "generosidad": {
        "nombre":      "Generosidad",
        "emoji":       "🌟",
        "color":       "#a8ff78",
        "descripcion": "Dar de lo que tienes (tiempo, talento, atención) hace al mundo mejor.",
        "reflexion":   "¿Ayudaste a alguien hoy, aunque sea en algo pequeño?",
        "misiones": [
            "Ayuda a alguien de la familia con una tarea sin que te lo pidan",
            "Comparte algo que sabes hacer con alguien que lo necesita",
            "Dona tiempo a una causa o persona que lo necesite",
        ],
    },
}

# ── Gestión de Acuerdos ────────────────────────────────────────────────────────

def crear_acuerdo(user_id: str, titulo: str, descripcion: str,
                  meta: str, recompensa: str, plazo_dias: int,
                  pin_padre: str = "0000") -> dict:
    """
    Crea un acuerdo digital teen↔padre.
    Requiere PIN del padre para ser válido (garantía de que el padre participó).
    """
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "PIN del padre incorrecto"}

    acuerdo_id = f"ACU-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    hoy        = datetime.date.today()
    vence      = str(hoy + datetime.timedelta(days=plazo_dias))

    acuerdo = {
        "id":           acuerdo_id,
        "titulo":       titulo,
        "descripcion":  descripcion,
        "meta":         meta,
        "recompensa":   recompensa,
        "plazo_dias":   plazo_dias,
        "fecha_inicio": str(hoy),
        "fecha_vence":  vence,
        "estado":       "activo",       # activo | cumplido | roto | vencido
        "firma_teen":   True,
        "firma_padre":  (pin_padre != "0000"),
        "historial":    [
            {"fecha": str(hoy), "evento": "Acuerdo creado", "por": "sistema"}
        ],
        "puntos_confianza": 20,         # se ganan al cumplir
        "tokens_recompensa": 50,
    }

    if "acuerdos" not in perfil:
        perfil["acuerdos"] = []
    perfil["acuerdos"].append(acuerdo)
    _guardar_datos(data)

    return {"ok": True, "acuerdo_id": acuerdo_id, "acuerdo": acuerdo}


def get_acuerdos(user_id: str) -> dict:
    """Retorna todos los acuerdos del usuario con su estado actual."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    hoy      = str(datetime.date.today())
    acuerdos = perfil.get("acuerdos", [])

    # Actualizar estados vencidos
    for a in acuerdos:
        if a["estado"] == "activo" and a.get("fecha_vence", "9999") < hoy:
            a["estado"] = "vencido"
            a["historial"].append({"fecha": hoy, "evento": "Acuerdo vencido sin marcar", "por": "sistema"})
    _guardar_datos(data)

    activos   = [a for a in acuerdos if a["estado"] == "activo"]
    cumplidos = [a for a in acuerdos if a["estado"] == "cumplido"]
    rotos     = [a for a in acuerdos if a["estado"] == "roto"]
    vencidos  = [a for a in acuerdos if a["estado"] == "vencido"]

    return {
        "ok":            True,
        "total_activos": len(activos),
        "activos":       activos,
        "cumplidos":     cumplidos,
        "rotos":         rotos,
        "vencidos":      vencidos,
        "tasa_cumplimiento": (
            round(len(cumplidos) / max(1, len(cumplidos) + len(rotos) + len(vencidos)) * 100)
        ),
    }


def resolver_acuerdo(user_id: str, acuerdo_id: str,
                     estado: str, nota: str = "", pin_padre: str = "0000") -> dict:
    """
    Marca un acuerdo como cumplido o roto.
    estado: 'cumplido' | 'roto'
    Requiere PIN del padre para 'cumplido' (el padre verifica).
    """
    if estado not in ("cumplido", "roto"):
        return {"ok": False, "error": "Estado debe ser 'cumplido' o 'roto'"}

    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    acuerdo = next((a for a in perfil.get("acuerdos", []) if a["id"] == acuerdo_id), None)
    if not acuerdo:
        return {"ok": False, "error": "Acuerdo no encontrado"}
    if acuerdo["estado"] != "activo":
        return {"ok": False, "error": f"El acuerdo ya está en estado: {acuerdo['estado']}"}

    cp = perfil.get("control_parental", {})
    if estado == "cumplido" and cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "El padre debe verificar con su PIN"}

    acuerdo["estado"] = estado
    hoy = str(datetime.date.today())
    acuerdo["historial"].append({
        "fecha":   hoy,
        "evento":  f"Acuerdo marcado como {estado}",
        "nota":    nota,
        "por":     "padre" if pin_padre != "0000" else "teen",
    })

    tokens_ganados = 0
    pts_confianza  = 0

    if estado == "cumplido":
        tokens_ganados = acuerdo.get("tokens_recompensa", 50)
        pts_confianza  = acuerdo.get("puntos_confianza", 20)
        perfil["tokens"]    = perfil.get("tokens", 0) + tokens_ganados
        perfil["xp_total"]  = perfil.get("xp_total", 0) + 50
        perfil["aptitudes"]["responsabilidad"]["xp"] = (
            perfil["aptitudes"].get("responsabilidad", {}).get("xp", 0) + 40
        )
    elif estado == "roto":
        pts_confianza = -10   # penalización en confianza

    # Actualizar puntos de confianza
    perfil["puntos_confianza"] = max(0, perfil.get("puntos_confianza", 100) + pts_confianza)
    _guardar_datos(data)

    return {
        "ok":             True,
        "estado":         estado,
        "tokens_ganados": tokens_ganados,
        "pts_confianza":  pts_confianza,
        "confianza_total":perfil["puntos_confianza"],
    }


# ── Check-in de humor ──────────────────────────────────────────────────────────

ESTADOS_ANIMO = {
    "genial":      {"emoji": "🔥", "label": "Genial",       "color": "#00ff88", "nivel": 5},
    "bien":        {"emoji": "😊", "label": "Bien",         "color": "#ffe66d", "nivel": 4},
    "regular":     {"emoji": "😐", "label": "Regular",      "color": "#aaaaaa", "nivel": 3},
    "cansado":     {"emoji": "😴", "label": "Cansado/a",    "color": "#7777ff", "nivel": 2},
    "mal":         {"emoji": "😔", "label": "No tan bien",  "color": "#ff9a3c", "nivel": 2},
    "estresado":   {"emoji": "😤", "label": "Estresado/a",  "color": "#ff6b9d", "nivel": 1},
    "triste":      {"emoji": "💙", "label": "Triste",       "color": "#4ecdc4", "nivel": 1},
}

def registrar_checkin(user_id: str, estado: str, nota: str = "") -> dict:
    """Registra el estado de ánimo del teen. Detecta patrones de alerta."""
    if estado not in ESTADOS_ANIMO:
        return {"ok": False, "error": f"Estado inválido. Opciones: {list(ESTADOS_ANIMO)}"}

    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    hoy = str(datetime.date.today())
    checkins = perfil.get("checkins", [])

    # Verificar si ya hizo check-in hoy
    ya_hoy = any(c["fecha"] == hoy for c in checkins[-3:])

    checkins.append({
        "fecha":  hoy,
        "hora":   datetime.datetime.now().strftime("%H:%M"),
        "estado": estado,
        "nota":   nota,
        "nivel":  ESTADOS_ANIMO[estado]["nivel"],
    })
    perfil["checkins"] = checkins[-90:]   # 90 días máximo

    # Suma XP de bienestar por hacer check-in
    if not ya_hoy:
        perfil["aptitudes"]["bienestar"]["xp"] = perfil["aptitudes"].get("bienestar", {}).get("xp", 0) + 5
        perfil["tokens"] = perfil.get("tokens", 0) + 3

    # Alerta si 3 días consecutivos en nivel bajo
    alerta_padre = False
    if len(checkins) >= 3:
        ultimos3 = checkins[-3:]
        if all(c["nivel"] <= 2 for c in ultimos3):
            alerta_padre = True
            perfil["alerta_bienestar"] = {
                "activa": True,
                "fecha":  hoy,
                "motivo": "3 días consecutivos con estado bajo",
            }

    _guardar_datos(data)
    return {
        "ok":          True,
        "estado":      estado,
        "emoji":       ESTADOS_ANIMO[estado]["emoji"],
        "xp_ganado":   5 if not ya_hoy else 0,
        "alerta_padre":alerta_padre,
    }


def get_checkins_semana(user_id: str) -> dict:
    """Retorna check-ins de los últimos 7 días para el panel padre."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    hoy      = datetime.date.today()
    semana   = [str(hoy - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    checkins = {c["fecha"]: c for c in perfil.get("checkins", [])}
    result   = []
    for dia in semana:
        c = checkins.get(dia)
        result.append({
            "fecha":  dia,
            "estado": c["estado"] if c else None,
            "emoji":  ESTADOS_ANIMO[c["estado"]]["emoji"] if c else "○",
            "nivel":  c["nivel"] if c else 0,
        })

    niveles   = [r["nivel"] for r in result if r["nivel"] > 0]
    promedio  = round(sum(niveles) / max(1, len(niveles)), 1)
    alerta    = perfil.get("alerta_bienestar", {}).get("activa", False)

    return {
        "ok":       True,
        "semana":   result,
        "promedio": promedio,
        "alerta":   alerta,
    }


# ── Reconocimientos parentales ─────────────────────────────────────────────────

TIPOS_RECONOCIMIENTO = {
    "orgullo":      {"emoji": "⭐", "label": "Me tienes muy orgulloso/a",     "pts": 15},
    "honesto":      {"emoji": "🤍", "label": "Fuiste honesto/a cuando importaba", "pts": 20},
    "maduro":       {"emoji": "🌱", "label": "Tomaste una decisión madura",   "pts": 20},
    "ayudaste":     {"emoji": "🤝", "label": "Ayudaste sin que te lo pidiera","pts": 15},
    "perseveraste": {"emoji": "🔥", "label": "No te rendiste",                "pts": 20},
    "creativo":     {"emoji": "💡", "label": "Tuviste una idea brillante",    "pts": 15},
    "lider":        {"emoji": "🚀", "label": "Lideraste con el ejemplo",      "pts": 20},
    "especial":     {"emoji": "💛", "label": "Eres especial para mí",         "pts": 10},
}

def dar_reconocimiento(user_id: str, tipo: str,
                       mensaje_personal: str = "", pin_padre: str = "0000") -> dict:
    """El padre da un reconocimiento al teen. Sube puntos de confianza y XP."""
    if tipo not in TIPOS_RECONOCIMIENTO:
        return {"ok": False, "error": f"Tipo inválido. Opciones: {list(TIPOS_RECONOCIMIENTO)}"}

    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "PIN del padre incorrecto"}

    rec_info = TIPOS_RECONOCIMIENTO[tipo]
    rec = {
        "id":      f"REC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "tipo":    tipo,
        "emoji":   rec_info["emoji"],
        "label":   rec_info["label"],
        "mensaje": mensaje_personal,
        "fecha":   str(datetime.date.today()),
        "leido":   False,
    }

    if "reconocimientos" not in perfil:
        perfil["reconocimientos"] = []
    perfil["reconocimientos"].append(rec)

    # Bonificaciones
    perfil["puntos_confianza"]   = min(200, perfil.get("puntos_confianza", 100) + rec_info["pts"])
    perfil["tokens"]             = perfil.get("tokens", 0) + 20
    perfil["xp_total"]           = perfil.get("xp_total", 0) + 30
    perfil["aptitudes"]["bienestar"]["xp"] = perfil["aptitudes"].get("bienestar", {}).get("xp", 0) + 20

    _guardar_datos(data)
    return {
        "ok":        True,
        "reconocimiento": rec,
        "pts_confianza": rec_info["pts"],
    }


# ── Economía Familiar ──────────────────────────────────────────────────────────

PRIVILEGIOS_DEFAULT = [
    {"id": "P01", "nombre": "30 min extra de pantalla",        "costo_tokens": 50,  "activo": True},
    {"id": "P02", "nombre": "Noche de película en familia",    "costo_tokens": 80,  "activo": True},
    {"id": "P03", "nombre": "Salida con amigos el fin de semana","costo_tokens": 150, "activo": True},
    {"id": "P04", "nombre": "Elegir el restaurante familiar",  "costo_tokens": 100, "activo": True},
    {"id": "P05", "nombre": "Día sin tareas del hogar",        "costo_tokens": 120, "activo": True},
    {"id": "P06", "nombre": "Presupuesto extra para gustos",   "costo_tokens": 200, "activo": True},
]

def get_privilegios(user_id: str) -> dict:
    """Retorna los privilegios disponibles para canjear."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    custom = perfil.get("privilegios_custom", [])
    todos  = PRIVILEGIOS_DEFAULT + custom
    return {
        "ok":        True,
        "privilegios": todos,
        "tokens_disponibles": perfil.get("tokens", 0),
    }


def canjear_privilegio(user_id: str, privilegio_id: str, pin_padre: str = "0000") -> dict:
    """Teen canjea tokens por un privilegio. El padre aprueba con su PIN."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "El padre debe aprobar el canje con su PIN"}

    custom    = perfil.get("privilegios_custom", [])
    todos     = PRIVILEGIOS_DEFAULT + custom
    priv      = next((p for p in todos if p["id"] == privilegio_id and p.get("activo")), None)
    if not priv:
        return {"ok": False, "error": "Privilegio no encontrado o inactivo"}

    costo = priv["costo_tokens"]
    if perfil.get("tokens", 0) < costo:
        return {"ok": False, "error": f"No tienes suficientes tokens. Necesitas {costo}, tienes {perfil.get('tokens',0)}"}

    perfil["tokens"] -= costo
    canje = {
        "privilegio": priv["nombre"],
        "costo":      costo,
        "fecha":      str(datetime.date.today()),
    }
    if "historial_canjes" not in perfil:
        perfil["historial_canjes"] = []
    perfil["historial_canjes"].append(canje)
    _guardar_datos(data)

    return {
        "ok":             True,
        "canje":          canje,
        "tokens_restantes": perfil["tokens"],
    }


def agregar_privilegio_custom(user_id: str, nombre: str, costo: int, pin_padre: str) -> dict:
    """El padre agrega un privilegio personalizado."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "PIN incorrecto"}

    if "privilegios_custom" not in perfil:
        perfil["privilegios_custom"] = []
    pid = f"PC{len(perfil['privilegios_custom'])+1:02d}"
    perfil["privilegios_custom"].append({
        "id": pid, "nombre": nombre, "costo_tokens": costo, "activo": True, "custom": True
    })
    _guardar_datos(data)
    return {"ok": True, "id": pid}


# ── Código de Honor Familiar ───────────────────────────────────────────────────

def get_codigo_honor(user_id: str) -> dict:
    """Retorna el código de honor familiar."""
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}
    return {"ok": True, "codigo": perfil.get("codigo_honor", None)}


def guardar_codigo_honor(user_id: str, frases: list, pin_padre: str) -> dict:
    """Guarda el manifiesto familiar. Requiere PIN del padre y al menos 3 frases."""
    if len(frases) < 3:
        return {"ok": False, "error": "El código de honor debe tener al menos 3 frases"}

    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "PIN del padre incorrecto"}

    perfil["codigo_honor"] = {
        "frases":        frases[:7],     # máximo 7
        "fecha":         str(datetime.date.today()),
        "firmado_teen":  True,
        "firmado_padre": (pin_padre != "0000"),
        "version":       1,
    }
    # Bonus por crear el código
    perfil["puntos_confianza"] = min(200, perfil.get("puntos_confianza", 100) + 30)
    perfil["tokens"]   = perfil.get("tokens", 0) + 100
    _guardar_datos(data)
    return {"ok": True, "codigo": perfil["codigo_honor"]}


# ── Monitor Parental ───────────────────────────────────────────────────────────

def get_monitor_parental(user_id: str, pin_padre: str) -> dict:
    """
    Vista completa del padre: progreso real, humor, acuerdos, reconocimientos.
    Requiere PIN del padre.
    """
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    cp = perfil.get("control_parental", {})
    if cp.get("activo") and cp.get("padre_pin", "0000") != pin_padre:
        return {"ok": False, "error": "PIN incorrecto"}

    hoy   = datetime.date.today()
    seman = get_checkins_semana(user_id)

    # Aptitud más alta y más baja
    apts = perfil.get("aptitudes", {})
    if apts:
        apt_max = max(apts.items(), key=lambda x: x[1].get("xp", 0))
        apt_min = min(apts.items(), key=lambda x: x[1].get("xp", 0))
    else:
        apt_max = apt_min = ("—", {"xp": 0})

    # Acuerdos
    ac = get_acuerdos(user_id)

    return {
        "ok":               True,
        "nombre":           perfil.get("nombre", "—"),
        "nivel_global":     perfil.get("nivel_global", 1),
        "tokens":           perfil.get("tokens", 0),
        "racha":            perfil.get("racha", 0),
        "xp_total":         perfil.get("xp_total", 0),
        "puntos_confianza": perfil.get("puntos_confianza", 100),
        "badges":           len(perfil.get("badges", [])),
        "humor_semana":     seman,
        "alerta_bienestar": perfil.get("alerta_bienestar", {}).get("activa", False),
        "aptitud_fuerte":   {
            "key":    apt_max[0],
            "nombre": APTITUDES.get(apt_max[0], {}).get("nombre", apt_max[0]),
            "xp":     apt_max[1].get("xp", 0),
        },
        "aptitud_debil":    {
            "key":    apt_min[0],
            "nombre": APTITUDES.get(apt_min[0], {}).get("nombre", apt_min[0]),
            "xp":     apt_min[1].get("xp", 0),
        },
        "acuerdos_activos":  ac.get("total_activos", 0),
        "tasa_cumplimiento": ac.get("tasa_cumplimiento", 0),
        "reconocimientos_dados": len(perfil.get("reconocimientos", [])),
        "codigo_honor":     perfil.get("codigo_honor") is not None,
        "ultima_actividad": perfil.get("ultimo_dia", "—"),
    }


# ── Estado general de la familia ───────────────────────────────────────────────

def get_estado_familia(user_id: str) -> dict:
    """
    Vista unificada teen+padre sin PIN.
    Muestra el estado de la relación familiar en NEXUS.
    """
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "Usuario no encontrado"}

    ac = get_acuerdos(user_id)
    reconocimientos = perfil.get("reconocimientos", [])
    no_leidos = [r for r in reconocimientos if not r.get("leido")]

    # Check-in de hoy
    hoy      = str(datetime.date.today())
    checkins = perfil.get("checkins", [])
    ci_hoy   = next((c for c in reversed(checkins) if c["fecha"] == hoy), None)

    return {
        "ok":               True,
        "nombre":           perfil.get("nombre", "—"),
        "puntos_confianza": perfil.get("puntos_confianza", 100),
        "acuerdos_activos": ac.get("total_activos", 0),
        "tasa_cumplimiento":ac.get("tasa_cumplimiento", 0),
        "reconocimientos_pendientes": len(no_leidos),
        "reconocimientos_recientes": (reconocimientos[-3:] if reconocimientos else []),
        "checkin_hoy":      ci_hoy,
        "checkin_hecho":    ci_hoy is not None,
        "codigo_honor":     perfil.get("codigo_honor"),
        "valores_activos":  list(VALORES.keys()),
        "privilegios_disponibles": len(PRIVILEGIOS_DEFAULT),
    }


def marcar_reconocimiento_leido(user_id: str, rec_id: str) -> dict:
    data   = _cargar_datos()
    perfil = data["usuarios"].get(user_id)
    if not perfil:
        return {"ok": False, "error": "No encontrado"}
    for r in perfil.get("reconocimientos", []):
        if r["id"] == rec_id:
            r["leido"] = True
    _guardar_datos(data)
    return {"ok": True}


def get_valores_catalogo() -> dict:
    return {k: {
        "nombre":      v["nombre"],
        "emoji":       v["emoji"],
        "color":       v["color"],
        "descripcion": v["descripcion"],
        "reflexion":   v["reflexion"],
        "misiones":    v["misiones"],
    } for k, v in VALORES.items()}


# ── CLI rápido ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"

    if cmd == "demo":
        uid = "demo_user"
        registrar_usuario(uid, "Demo Teen", 17)
        print("[+] Usuario registrado")
        r = completar_mision(uid, "E01")
        print(f"[+] Misión E01: {r}")
        r = completar_mision(uid, "D01")
        print(f"[+] Misión D01: {r}")
        r = completar_mision(uid, "D02")
        print(f"[+] Misión D02: {r}")
        p = get_perfil(uid)
        print(f"[+] Perfil: tokens={p['perfil']['tokens']}, xp={p['perfil']['xp_total']}")
        idea = generar_idea_viral("creatividad")
        print(f"[+] Idea viral:\n    Hook: {idea['hook']}")
        plan = impulsar_aptitud(uid, "creatividad")
        print(f"[+] Impulso creatividad: nivel={plan['nivel_actual']} — {plan['nombre_nivel']}")
        print(f"    Próximo paso: {plan['paso_actual_roadmap']}")
        print(f"    Consejo: {plan['consejo']}")

    elif cmd == "misiones":
        for m in get_misiones():
            print(f"  [{m['id']}] {m['nombre']} — {m['tokens']}tok / +{m['xp']}xp ({m['aptitud']})")

    elif cmd == "aptitudes":
        for k, v in get_aptitudes_catalogo().items():
            print(f"  {v['emoji']} {v['nombre']}: {v['descripcion'][:60]}...")

    elif cmd == "familia":
        uid = "demo_user"
        registrar_usuario(uid, "Demo Teen", 17)
        print(f"[+] Estado familia: {get_estado_familia(uid)}")

    elif cmd == "acuerdos":
        uid = "demo_user"
        registrar_usuario(uid, "Demo Teen", 17)
        r = crear_acuerdo(uid, "Pantalla responsable",
                          "Máximo 2 horas de redes sociales al día",
                          "7 días consecutivos", "1 hora extra el fin de semana", 7)
        print(f"[+] Acuerdo creado: {r.get('acuerdo_id')}")
        r2 = get_acuerdos(uid)
        print(f"[+] Acuerdos activos: {r2.get('total_activos')}")
    else:
        print("Uso: python nexus_teens.py [demo|misiones|aptitudes|acuerdos]")

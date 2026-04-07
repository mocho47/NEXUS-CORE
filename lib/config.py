"""
NEXUS v3 by Simplex - Modulo de Configuracion
Carga variables de entorno, define constantes y configura proveedores de IA.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nexus.config")

# ============================================================
# Rutas del proyecto
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "nexus.db"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [DATA_DIR, UPLOAD_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================
# Cargar .env
# ============================================================
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    logger.info("Archivo .env cargado desde: %s", ENV_PATH)
else:
    logger.warning("No se encontro archivo .env en: %s", ENV_PATH)
    logger.warning("Usando configuracion por defecto. Copia .env.example a .env.")

# ============================================================
# Configuracion general
# ============================================================
NEXUS_VERSION = "3.0.0"
NEXUS_PORT = int(os.getenv("NEXUS_PORT", "8000"))
NEXUS_PRIVATE = int(os.getenv("NEXUS_PRIVATE", "1"))
NEXUS_OWNER = os.getenv("NEXUS_OWNER", "Anuar")

# ============================================================
# Puertos de servicios adicionales
# ============================================================
PORTS = {
    "nexus": NEXUS_PORT,
    "motor_web": int(os.getenv("PORT_MOTOR_WEB", "8001")),
    "motor_voice": int(os.getenv("PORT_MOTOR_VOICE", "8002")),
    "motor_social": int(os.getenv("PORT_MOTOR_SOCIAL", "8003")),
    "motor_design": int(os.getenv("PORT_MOTOR_DESIGN", "8004")),
    "motor_docs": int(os.getenv("PORT_MOTOR_DOCS", "8005")),
    "motor_agents": int(os.getenv("PORT_MOTOR_AGENTS", "8006")),
}

# ============================================================
# APIs de IA
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")

# Endpoints Groq
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_MODELS_URL = "https://api.groq.com/openai/v1/models"

# Endpoint Z.ai
ZAI_API_URL = "https://api.zukijourney.xyzbot.net/v1/chat/completions"

# Ollama (local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODELS_URL = f"{OLLAMA_BASE_URL}/api/tags"

# ============================================================
# Nombres de modelos
# ============================================================
MODELS = {
    "groq_fast": "llama-3.1-8b-instant",
    "groq_smart": "llama-3.3-70b-versatile",
    "zai": "glm-4-flash",
    "ollama_local": "phi3:mini",
}

# Alias amigables
MODEL_ALIASES = {
    "rapido": MODELS["groq_fast"],
    "inteligente": MODELS["groq_smart"],
    "nube": MODELS["zai"],
    "local": MODELS["ollama_local"],
    "offline": MODELS["ollama_local"],
}

# ============================================================
# Supabase
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ============================================================
# Telegram
# ============================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================================
# Redes sociales
# ============================================================
IG_USER = os.getenv("IG_USER", "")
IG_PASS = os.getenv("IG_PASS", "")

# ============================================================
# Informacion de negocios
# ============================================================
ATF_PHONE = os.getenv("ATF_PHONE", "3323530146")

ATF_INFO = {
    "nombre": "ATF - Actualiza Tus Faros",
    "giro": "Retrofit LED automotriz",
    "descripcion": "Especialistas en actualizacion de faros con tecnologia LED para todo tipo de vehiculos.",
    "telefono": ATF_PHONE,
    "ubicacion": "Guadalajara, Jalisco, Mexico",
    "servicios": [
        {
            "nombre": "Retrofit LED Basico",
            "descripcion": "Conversion de halogeno a LED con projector.",
            "precio_min": 3500,
            "precio_max": 5000,
        },
        {
            "nombre": "Retrofit LED Premium",
            "descripcion": "Conversion completa con bombillas bi-LED y angel eyes.",
            "precio_min": 5500,
            "precio_max": 8000,
        },
        {
            "nombre": "Retrofit LED Full",
            "descripcion": "Paquete completo: projector bi-LED, angel eyes, DRL, sequencia de virus.",
            "precio_min": 8000,
            "precio_max": 15000,
        },
        {
            "nombre": "Mantenimiento de Retrofit",
            "descripcion": "Limpieza, sellado y revision de retrofit existente.",
            "precio_min": 500,
            "precio_max": 1000,
        },
    ],
    "horario": "Lunes a Viernes 9:00 - 18:00, Sabados 9:00 - 14:00",
}

MILENS_INFO = {
    "nombre": "Creaciones Milens",
    "giro": "Corte laser y sublimacion",
    "descripcion": "Personalizacion de productos con corte laser, grabado y sublimacion.",
    "telefono": ATF_PHONE,
    "ubicacion": "Guadalajara, Jalisco, Mexico",
    "servicios": [
        {
            "nombre": "Corte Laser",
            "descripcion": "Corte precision en madera, acrilico, MDF, cuero y mas.",
            "precio_min": 50,
            "precio_max": 500,
        },
        {
            "nombre": "Sublimacion",
            "descripcion": "Tazas, playeras, mousepads, almohadas y mas.",
            "precio_min": 80,
            "precio_max": 350,
        },
        {
            "nombre": "Grabado Laser",
            "descripcion": "Personalizacion en madera, vidrio, metal y cuero.",
            "precio_min": 50,
            "precio_max": 400,
        },
        {
            "nombre": "Disenio Personalizado",
            "descripcion": "Creacion de disenos a medida para cualquier proyecto.",
            "precio_min": 200,
            "precio_max": 1000,
        },
    ],
    "horario": "Lunes a Viernes 10:00 - 19:00, Sabados 10:00 - 15:00",
}

CANBUSFIX_INFO = {
    "nombre": "CanbusFix",
    "giro": "Red de instaladores de accesorios automotrices",
    "descripcion": "Comunidad y red de instaladores profesionales certificados en electronica automotriz.",
    "telefono": ATF_PHONE,
    "ubicacion": "Guadalajara, Jalisco, Mexico (sede principal)",
    "servicios": [
        {
            "nombre": "Instalacion de Accesorios",
            "descripcion": "Camaras, pantallas, sensores, alarmas, audio.",
            "precio_min": 500,
            "precio_max": 5000,
        },
        {
            "nombre": "Canbus y Diagnostico",
            "descripcion": "Solucion de problemas de canbus, codigos de error y compatibilidad.",
            "precio_min": 800,
            "precio_max": 3000,
        },
        {
            "nombre": "Formacion a Instaladores",
            "descripcion": "Cursos y certificacion para nuevos instaladores.",
            "precio_min": 2000,
            "precio_max": 5000,
        },
    ],
}

NEGOCIOS = {
    "atf": ATF_INFO,
    "milens": MILENS_INFO,
    "canbusfix": CANBUSFIX_INFO,
}

# ============================================================
# Personalidades (System Prompts)
# ============================================================
PERSONALIDADES = {
    "NEXUS": {
        "id": "nexus",
        "nombre": "NEXUS",
        "descripcion": "Asistente empresarial para Simplex GDL",
        "emoji": "⚡",
        "color": "#00D4FF",
        "system_prompt": (
            "Eres NEXUS, el asistente empresarial de Anuar para Simplex GDL. "
            "Conoces sus 3 negocios: ATF (Actualiza Tus Faros - retrofit LED), "
            "Creaciones Milens (corte laser, sublimacion), y CanbusFix (red de instaladores). "
            "Eres directo, profesional, eficiente. "
            "Nunca inventas datos. Si no sabes algo, lo dices. "
            "Aprendes de cada conversacion. "
            "Respondes siempre en espanol de Mexico. "
            "Usas un tono profesional pero cercano. "
            "Si te preguntan por precios, das los rangos que conoces. "
            "Si te preguntan por algo fuera de tu conocimiento, ofreces buscar la informacion. "
            "Nunca revelas detalles tecnicos de tu funcionamiento interno."
        ),
    },
    "FORJA": {
        "id": "forja",
        "nombre": "FORJA",
        "descripcion": "Coach de emprendedores - Nathalye",
        "emoji": "🔥",
        "color": "#FF6B35",
        "system_prompt": (
            "Eres FORJA, la coach de emprendedores de la comunidad Simplex. "
            "Tu nombre es Nathalye. "
            "Ayudas a emprendedores locales a crecer sus negocios con estrategias practicas. "
            "Usas un tono motivador pero realista. "
            "Conoces herramientas de marketing digital, finanzas basicas, y gestion de negocios locales Mexicanos. "
            "Respondes siempre en espanol de Mexico. "
            "Das consejos concretos y accionables, no solo teoria. "
            "Ejemplos de temas que manejas: redes sociales para negocios locales, "
            "presupuesto para emprendedores, atencion al cliente, precios, "
            "estrategias de venta, branding personal, etc. "
            "Siempre cierras con una pregunta para mantener la conversacion activa. "
            "Nunca inventas estadisticas o datos que no conozcas."
        ),
    },
    "TEENS": {
        "id": "teens",
        "nombre": "NEXUS TEENS",
        "descripcion": "Sistema de misiones y coaching para jovenes y familia",
        "emoji": "🎯",
        "color": "#A855F7",
        "system_prompt": (
            "Eres el sistema NEXUS TEENS para la familia. "
            "Manejas misiones, recompensas y coaching para jovenes y padres. "
            "Usas psicologia positiva adaptada a jovenes Mexicanos. "
            "Creas misiones divertidas y educativas. "
            "Ayudas a los padres con tecnicas de crianza positiva. "
            "Tono fresco pero respetuoso. "
            "Respondes siempre en espanol de Mexico con vocabulario juvenil apropiado. "
            "Las misiones pueden incluir: tareas escolares, habitos saludables, "
            "lectura, ejercicio, ayudar en casa, aprender algo nuevo, etc. "
            "Usas un sistema de puntos y niveles para motivar. "
            "Cuando hablas con jovenes, eres divertido y dinámico. "
            "Cuando hablas con padres, eres empático y profesional. "
            "Nunca das consejos contrarios a los valores familiares Mexicanos."
        ),
    },
}

# Prompt base que se agrega a todas las personalidades
BASE_SYSTEM_PROMPT = (
    f"Hoy es una conversacion en el contexto de NEXUS v3 by Simplex. "
    f"El propietario es {NEXUS_OWNER}. "
    f"La ubicacion base es Guadalajara, Jalisco, Mexico. "
    f"Idioma principal: Espanol de Mexico. "
    f"Siempre responde en espanol salvo que el usuario pida explicitamente otro idioma."
)


# ============================================================
# Funciones de configuracion
# ============================================================

def get_ai_provider() -> dict:
    """
    Devuelve el mejor proveedor de IA disponible basado en lo que esta configurado.
    Prioridad: Groq > Z.ai > Ollama

    Returns:
        dict con keys: provider, model, api_url, api_key (o empty string para Ollama)
    """
    # Verificar Groq
    if GROQ_API_KEY and GROQ_API_KEY not in ("gsk_tu_key_aqui", ""):
        logger.info("Proveedor seleccionado: Groq (%s)", MODELS["groq_fast"])
        return {
            "provider": "groq",
            "model": MODELS["groq_fast"],
            "api_url": GROQ_API_URL,
            "api_key": GROQ_API_KEY,
        }

    # Verificar Z.ai
    if ZAI_API_KEY and ZAI_API_KEY not in ("tu_key_aqui", ""):
        logger.info("Proveedor seleccionado: Z.ai (%s)", MODELS["zai"])
        return {
            "provider": "zai",
            "model": MODELS["zai"],
            "api_url": ZAI_API_URL,
            "api_key": ZAI_API_KEY,
        }

    # Ollama local (siempre disponible si esta instalado)
    logger.info("Proveedor seleccionado: Ollama local (%s)", MODELS["ollama_local"])
    return {
        "provider": "ollama",
        "model": MODELS["ollama_local"],
        "api_url": OLLAMA_API_URL,
        "api_key": "",
    }


def get_available_providers() -> list:
    """
    Devuelve lista de proveedores disponibles y su estado.

    Returns:
        list de dicts con: provider, model, available (bool), reason (str)
    """
    providers = []

    # Groq
    if GROQ_API_KEY and GROQ_API_KEY not in ("gsk_tu_key_aqui", ""):
        providers.append({
            "provider": "groq",
            "model": MODELS["groq_fast"],
            "available": True,
            "reason": "API key configurada",
        })
    else:
        providers.append({
            "provider": "groq",
            "model": MODELS["groq_fast"],
            "available": False,
            "reason": "API key no configurada en .env",
        })

    # Z.ai
    if ZAI_API_KEY and ZAI_API_KEY not in ("tu_key_aqui", ""):
        providers.append({
            "provider": "zai",
            "model": MODELS["zai"],
            "available": True,
            "reason": "API key configurada",
        })
    else:
        providers.append({
            "provider": "zai",
            "model": MODELS["zai"],
            "available": False,
            "reason": "API key no configurada en .env",
        })

    # Ollama
    ollama_available, ollama_reason = check_ollama_status()
    providers.append({
        "provider": "ollama",
        "model": MODELS["ollama_local"],
        "available": ollama_available,
        "reason": ollama_reason,
    })

    return providers


def check_ollama_status() -> tuple:
    """
    Verifica si Ollama esta corriendo y el modelo phi3:mini esta disponible.

    Returns:
        tuple (bool_disponible, str_razon)
    """
    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            OLLAMA_MODELS_URL,
            headers={"Content-Type": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]

            # Buscar phi3:mini en cualquier variante
            phi_available = any("phi3" in m.lower() and "mini" in m.lower() for m in models)

            if phi_available:
                return True, "Ollama corriendo con phi3:mini disponible"
            else:
                return True, "Ollama corriendo pero phi3:mini no descargado (ejecuta: ollama pull phi3:mini)"

    except Exception as e:
        return False, f"Ollama no disponible: {str(e)[:80]}"


def detect_programs() -> dict:
    """
    Detecta programas instalados en el sistema (Windows).
    Verifica rutas comunes de instalacion.

    Returns:
        dict con nombre del programa: ruta de ejecutable (o None si no encontrado)
    """
    programs = {
        "RDW": None,
        "Silhouette Studio": None,
        "CorelDRAW": None,
        "Aspire": None,
        "Inkscape": None,
        "GIMP": None,
        "Adobe Illustrator": None,
        "Adobe Photoshop": None,
    }

    # Solo detectar en Windows
    if sys.platform != "win32":
        logger.info("Deteccion de programas solo disponible en Windows")
        return programs

    # Rutas comunes para buscar
    search_paths = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"),
        os.path.expanduser("~\\AppData\\Local"),
    ]

    # Mapeo de programas a rutas relativas y ejecutables a buscar
    program_patterns = {
        "RDW": [
            (r"RDW", "rdw.exe"),
            (r"RDW Software", "rdw.exe"),
        ],
        "Silhouette Studio": [
            (r"Silhouette America", "Silhouette Studio.exe"),
            (r"Silhouette America", "Silhouette Studio 4.exe"),
        ],
        "CorelDRAW": [
            (r"Corel", "CorelDRAW.exe"),
            (r"Corel\CorelDRAW Graphics Suite 2024", "CorelDRAW.exe"),
            (r"Corel\CorelDRAW Graphics Suite 2023", "CorelDRAW.exe"),
            (r"Corel\CorelDRAW Graphics Suite 2022", "CorelDRAW.exe"),
        ],
        "Aspire": [
            (r"Aspire", "Aspire.exe"),
            (r"Vectric\Aspire", "Aspire.exe"),
        ],
        "Inkscape": [
            (r"Inkscape", "inkscape.exe"),
        ],
        "GIMP": [
            (r"GIMP 2", "bin\\gimp-2.10.exe"),
            (r"GIMP", "bin\\gimp.exe"),
        ],
        "Adobe Illustrator": [
            (r"Adobe\Adobe Illustrator 2024", "Support Files\Contents\Windows\Illustrator.exe"),
            (r"Adobe\Adobe Illustrator 2023", "Support Files\Contents\Windows\Illustrator.exe"),
        ],
        "Adobe Photoshop": [
            (r"Adobe\Adobe Photoshop 2024", "Photoshop.exe"),
            (r"Adobe\Adobe Photoshop 2023", "Photoshop.exe"),
        ],
    }

    for program_name, patterns in program_patterns.items():
        for search_base in search_paths:
            for relative_path, exe_name in patterns:
                full_path = os.path.join(search_base, relative_path, exe_name)
                try:
                    if os.path.isfile(full_path):
                        programs[program_name] = full_path
                        logger.info("Programa detectado: %s -> %s", program_name, full_path)
                        break
                except (OSError, ValueError):
                    continue
            if programs[program_name] is not None:
                break

    # Resumen
    detected = {k: v for k, v in programs.items() if v is not None}
    if detected:
        logger.info("Programas detectados: %s", ", ".join(detected.keys()))
    else:
        logger.info("No se detectaron programas de diseno instalados")

    return programs


def get_personality(personality_id: str) -> dict:
    """
    Obtiene la configuracion de una personalidad por ID.

    Args:
        personality_id: "NEXUS", "FORJA", o "TEENS"

    Returns:
        dict con la configuracion de la personalidad o la personalidad NEXUS por defecto
    """
    personality_id = personality_id.upper()

    if personality_id in PERSONALIDADES:
        return PERSONALIDADES[personality_id]

    # Buscar por ID interno
    for key, value in PERSONALIDADES.items():
        if value["id"] == personality_id.lower():
            return value

    # Por defecto, NEXUS
    logger.warning("Personalidad no encontrada: %s. Usando NEXUS.", personality_id)
    return PERSONALIDADES["NEXUS"]


def build_system_prompt(personality_id: str = "NEXUS", extra_context: str = "") -> str:
    """
    Construye el system prompt completo para una personalidad.

    Args:
        personality_id: ID de la personalidad
        extra_context: Contexto adicional para agregar al prompt

    Returns:
        str con el system prompt completo
    """
    personality = get_personality(personality_id)
    prompt = BASE_SYSTEM_PROMPT + "\n\n" + personality["system_prompt"]

    # Agregar informacion de negocios para NEXUS
    if personality_id.upper() == "NEXUS":
        negocio_context = (
            f"\n\nInformacion de los negocios de {NEXUS_OWNER}:\n"
            f"\n1. {ATF_INFO['nombre']} ({ATF_INFO['giro']})\n"
            f"   - {ATF_INFO['descripcion']}\n"
            f"   - Telefono: {ATF_INFO['telefono']}\n"
            f"   - Horario: {ATF_INFO['horario']}\n"
            f"   - Servicios:\n"
        )
        for serv in ATF_INFO["servicios"]:
            negocio_context += (
                f"     * {serv['nombre']}: ${serv['precio_min']:,} - ${serv['precio_max']:,} MXN. "
                f"{serv['descripcion']}\n"
            )

        negocio_context += (
            f"\n2. {MILENS_INFO['nombre']} ({MILENS_INFO['giro']})\n"
            f"   - {MILENS_INFO['descripcion']}\n"
            f"   - Telefono: {MILENS_INFO['telefono']}\n"
            f"   - Horario: {MILENS_INFO['horario']}\n"
            f"   - Servicios:\n"
        )
        for serv in MILENS_INFO["servicios"]:
            negocio_context += (
                f"     * {serv['nombre']}: ${serv['precio_min']:,} - ${serv['precio_max']:,} MXN. "
                f"{serv['descripcion']}\n"
            )

        negocio_context += (
            f"\n3. {CANBUSFIX_INFO['nombre']} ({CANBUSFIX_INFO['giro']})\n"
            f"   - {CANBUSFIX_INFO['descripcion']}\n"
            f"   - Telefono: {CANBUSFIX_INFO['telefono']}\n"
            f"   - Servicios:\n"
        )
        for serv in CANBUSFIX_INFO["servicios"]:
            negocio_context += (
                f"     * {serv['nombre']}: ${serv['precio_min']:,} - ${serv['precio_max']:,} MXN. "
                f"{serv['descripcion']}\n"
            )

        prompt += negocio_context

    if extra_context:
        prompt += f"\n\nContexto adicional: {extra_context}"

    return prompt


# ============================================================
# Utilidades
# ============================================================

def is_production() -> bool:
    """Verifica si NEXUS esta en modo produccion."""
    return NEXUS_PRIVATE == 1


def get_base_url() -> str:
    """Devuelve la URL base de NEXUS."""
    return f"http://localhost:{NEXUS_PORT}"


def reload_config() -> None:
    """Recarga la configuracion desde .env."""
    try:
        load_dotenv(ENV_PATH, override=True)
        logger.info("Configuracion recargada desde .env")
    except Exception as e:
        logger.error("Error al recargar configuracion: %s", e)


# ============================================================
# Informacion del sistema al iniciar
# ============================================================

def print_startup_info():
    """Imprime informacion de inicio en el log."""
    logger.info("=" * 60)
    logger.info("NEXUS v%s by Simplex", NEXUS_VERSION)
    logger.info("Propietario: %s", NEXUS_OWNER)
    logger.info("Puerto: %d", NEXUS_PORT)
    logger.info("Modo: %s", "Privado" if is_production() else "Publico")
    logger.info("Directorio base: %s", BASE_DIR)
    logger.info("Base de datos: %s", DB_PATH)
    logger.info("-" * 60)

    # Proveedores disponibles
    for p in get_available_providers():
        status = "✓" if p["available"] else "✗"
        logger.info("  %s %s (%s): %s", status, p["provider"], p["model"], p["reason"])

    logger.info("-" * 60)

    # Programas detectados
    if sys.platform == "win32":
        programs = detect_programs()
        if any(programs.values()):
            logger.info("Programas de diseno detectados:")
            for name, path in programs.items():
                if path:
                    logger.info("  ✓ %s", name)
                else:
                    logger.info("  ✗ %s (no encontrado)", name)
        else:
            logger.info("No se detectaron programas de diseno")

    logger.info("=" * 60)


# ============================================================
# Auto-detect al importar (solo logging, sin llamadas costosas)
# ============================================================
logger.info("Configuracion NEXUS v%s cargada correctamente", NEXUS_VERSION)
logger.info("Proveedor de IA preferido: %s", get_ai_provider()["provider"])


# Objeto settings para compatibilidad con nexus_core.py
class _Settings:
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("NEXUS_PORT", 8003))
    VERSION = NEXUS_VERSION

settings = _Settings()

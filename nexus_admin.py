"""
nexus_admin.py — Panel de Control Exclusivo ADMIN
================================================
Solo el administrador (tú) tiene acceso a:
  - Catálogo completo de módulos
  - Configurar qué módulos van en DEMO
  - Configurar módulos por tier de licencia
  - Ver catálogo de tienda pública con precios
  - Gestionar licencias activas
  - Tienda de módulos adicionales

Autenticación: PIN admin (hash SHA256) + token de sesión temporal
Config: CONFIG/admin_config.json
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
ADMIN_CFG  = os.path.join(CONFIG_DIR, "admin_config.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

# ── Tokens de sesión activos en memoria ───────────────────────────────────────
_session_tokens: dict[str, float] = {}   # token → timestamp_expira
SESSION_TTL = 3600  # 1 hora

# ═══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO MAESTRO DE MÓDULOS NEXUS
# ═══════════════════════════════════════════════════════════════════════════════
MODULO_CATALOGO: dict[str, dict] = {

    # ── NÚCLEO OBLIGATORIO ────────────────────────────────────────────────────
    "core": {
        "id": "core",
        "nombre": "Núcleo NEXUS",
        "emoji": "⚡",
        "descripcion": "Motor base, dashboard, configuración y panel web.",
        "detalle": "Dashboard móvil, gestión de negocio, tema oscuro, PWA.",
        "categoria": "CORE",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": True,
        "icono_color": "#00ff88",
    },
    "pedidos": {
        "id": "pedidos",
        "nombre": "Gestión de Pedidos",
        "emoji": "📦",
        "descripcion": "Control de pedidos, entregas y estados en tiempo real.",
        "detalle": "Pedidos pendientes/entregados, notificaciones, historial.",
        "categoria": "OPERATIVO",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ff9900",
    },
    "clientes": {
        "id": "clientes",
        "nombre": "CRM Clientes",
        "emoji": "👥",
        "descripcion": "Base de clientes, historial y perfiles de compra.",
        "detalle": "Alta de clientes, notas, historial de pedidos, segmentación.",
        "categoria": "OPERATIVO",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#00aaff",
    },
    "stock": {
        "id": "stock",
        "nombre": "Inventario / Stock",
        "emoji": "🏪",
        "descripcion": "Control de inventario, alertas de stock bajo y precios.",
        "detalle": "Alta de productos, categorías, alertas automáticas de reabasto.",
        "categoria": "OPERATIVO",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ff5500",
    },

    # ── MARKETING & REDES ──────────────────────────────────────────────────────
    "marketing": {
        "id": "marketing",
        "nombre": "Marketing IA",
        "emoji": "📣",
        "descripcion": "Generación de contenido IA para Instagram, TikTok y Facebook.",
        "detalle": "Copys, hashtags, captions, calendarios de contenido con IA.",
        "categoria": "MARKETING",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#e91e63",
    },
    "galeria": {
        "id": "galeria",
        "nombre": "Galería Visual IA",
        "emoji": "🎨",
        "descripcion": "Generación de imágenes y galería de activos para tu negocio.",
        "detalle": "DEMO:5/mes · LITE:5/mes · PRO:15/mes · FULL:∞",
        "categoria": "MARKETING",
        "precio_extra": 100,        # $100 MXN pack extra 5 activaciones
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#9c27b0",
    },
    "social": {
        "id": "social",
        "nombre": "Redes Sociales",
        "emoji": "📱",
        "descripcion": "Publicación y monitoreo en Instagram, Facebook y TikTok.",
        "detalle": "Programación de posts, métricas básicas, respuesta automática.",
        "categoria": "MARKETING",
        "precio_extra": 0,
        "incluido_en": ["PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ff4081",
    },
    "spy": {
        "id": "spy",
        "nombre": "NEXUS Spy",
        "emoji": "🕵️",
        "descripcion": "Análisis de competencia: precios, publicaciones y estrategias.",
        "detalle": "Monitorea hashtags, analiza competidores, alertas de precio.",
        "categoria": "MARKETING",
        "precio_extra": 399,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#607d8b",
    },
    "meta_ig": {
        "id": "meta_ig",
        "nombre": "Meta / Instagram Ads",
        "emoji": "🎯",
        "descripcion": "Integración con Meta Graph API para campañas pagadas.",
        "detalle": "Crear campañas, segmentar audiencia, medir ROAS.",
        "categoria": "MARKETING",
        "precio_extra": 499,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#1877f2",
    },

    # ── FINANZAS & OPERACIÓN ───────────────────────────────────────────────────
    "finanzas": {
        "id": "finanzas",
        "nombre": "Finanzas",
        "emoji": "💰",
        "descripcion": "Flujo de caja, ingresos, gastos y rentabilidad.",
        "detalle": "Registro de ingresos/gastos, gráficas, alertas de flujo.",
        "categoria": "FINANZAS",
        "precio_extra": 0,
        "incluido_en": ["LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ffd700",
    },
    "facturacion": {
        "id": "facturacion",
        "nombre": "Facturación CFDI",
        "emoji": "🧾",
        "descripcion": "Generación de facturas CFDI 4.0 para México.",
        "detalle": "Timbrado SAT, complementos de pago, cancelación y reenvío.",
        "categoria": "FINANZAS",
        "precio_extra": 599,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#4caf50",
    },
    "cotizador": {
        "id": "cotizador",
        "nombre": "Cotizador Pro",
        "emoji": "📋",
        "descripcion": "Cotizaciones profesionales en PDF con tu marca.",
        "detalle": "Plantillas, cálculo automático, envío por WhatsApp/correo.",
        "categoria": "FINANZAS",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#03a9f4",
    },

    # ── COMUNICACIÓN ──────────────────────────────────────────────────────────
    "asistente": {
        "id": "asistente",
        "nombre": "Asistente IA Conversacional",
        "emoji": "🤖",
        "descripcion": "Asistente de voz e IA para gestión rápida del negocio.",
        "detalle": "DEMO:15 msgs/día · LITE:50/día · PRO:200/día · FULL:∞",
        "categoria": "COMUNICACION",
        "precio_extra": 0,
        "incluido_en": ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#00bcd4",
    },
    "telegram": {
        "id": "telegram",
        "nombre": "Telegram Bot",
        "emoji": "✈️",
        "descripcion": "Bot de Telegram para notificaciones y control del negocio.",
        "detalle": "Alertas de pedidos, stock bajo, reportes diarios por Telegram.",
        "categoria": "COMUNICACION",
        "precio_extra": 0,
        "incluido_en": ["PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#2196f3",
    },
    "notifier": {
        "id": "notifier",
        "nombre": "Notificaciones Multi-canal",
        "emoji": "🔔",
        "descripcion": "Push, WhatsApp, Telegram y correo en un solo lugar.",
        "detalle": "Plantillas de mensajes, programación, confirmaciones de lectura.",
        "categoria": "COMUNICACION",
        "precio_extra": 0,
        "incluido_en": ["LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ff9800",
    },

    # ── BIENESTAR & PRODUCTIVIDAD ─────────────────────────────────────────────
    "binaural": {
        "id": "binaural",
        "nombre": "Audio Binaural (solo adultos)",
        "emoji": "🎧",
        "descripcion": "Frecuencias binaurales para enfoque, creatividad y bienestar.",
        "detalle": "Theta, Alpha, Beta, Solfeggio 432Hz/528Hz. Solo mayores de edad.",
        "categoria": "BIENESTAR",
        "precio_extra": 299,
        "incluido_en": ["PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#673ab7",
        "restriccion": "MAYORES_EDAD",
    },
    "scheduler": {
        "id": "scheduler",
        "nombre": "Agenda & Scheduler",
        "emoji": "📅",
        "descripcion": "Agenda de citas, recordatorios y programación de tareas.",
        "detalle": "Calendario, recordatorios WhatsApp, tareas recurrentes.",
        "categoria": "PRODUCTIVIDAD",
        "precio_extra": 0,
        "incluido_en": ["LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#009688",
    },
    "backup": {
        "id": "backup",
        "nombre": "Respaldo Automático",
        "emoji": "💾",
        "descripcion": "Respaldos automáticos a local y Supabase.",
        "detalle": "Respaldo diario/semanal, restauración con un toque.",
        "categoria": "PRODUCTIVIDAD",
        "precio_extra": 0,
        "incluido_en": ["LITE", "PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#607d8b",
    },

    # ── FAMILIA & JUVENTUD ─────────────────────────────────────────────────────
    "teens": {
        "id": "teens",
        "nombre": "NEXUS Teens + Familia",
        "emoji": "🎮",
        "descripcion": "Motor de desarrollo juvenil, gamificación y bloque familia.",
        "detalle": "Aptitudes, misiones, viral marketing, acuerdos familia, economía tokens.",
        "categoria": "FAMILIA",
        "precio_extra": 499,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#ff4081",
        "restriccion": "SIN_BINAURALES",
    },

    # ── IOT & TECNOLOGÍA ──────────────────────────────────────────────────────
    "iot": {
        "id": "iot",
        "nombre": "NEXUS IoT",
        "emoji": "🔌",
        "descripcion": "Monitoreo de dispositivos, sensores y automatización.",
        "detalle": "MQTT, temperatura, humedad, alertas de sensores en tiempo real.",
        "categoria": "TECNOLOGIA",
        "precio_extra": 699,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#00bcd4",
    },
    "video": {
        "id": "video",
        "nombre": "Video Processor",
        "emoji": "🎬",
        "descripcion": "Procesamiento de video para marketing y contenido digital.",
        "detalle": "Subtítulos automáticos, recorte, formato para Reels/TikTok.",
        "categoria": "TECNOLOGIA",
        "precio_extra": 399,
        "incluido_en": ["PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#f44336",
    },
    "milens": {
        "id": "milens",
        "nombre": "NEXUS MiLens",
        "emoji": "🔬",
        "descripcion": "Análisis visual de productos, control de calidad con cámara.",
        "detalle": "Detección de defectos, catalogación visual, inspección QA.",
        "categoria": "TECNOLOGIA",
        "precio_extra": 599,
        "incluido_en": ["FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#8bc34a",
    },

    # ── MÓDULO ESPECIAL ────────────────────────────────────────────────────────
    "paranormal": {
        "id": "paranormal",
        "nombre": "NEXUS Paranormal",
        "emoji": "🔮",
        "descripcion": "Modo oscuro de NEXUS — la personalidad glitch del asistente que 've cosas en el taller'.",
        "detalle": (
            "Activa el lado oscuro de NEXUS: escanea frecuencias bajas, detecta anomalías "
            "electromagnéticas en tus datos de negocio y genera contenido viral con estética "
            "misterio/glitch. Basado en la personalidad paranormal de NEXUS (nexus_core). "
            "Uso: entretenimiento + posts virales de tipo 'NEXUS detectó algo en tus ventas...'. "
            "Sin predicciones falsas. Solo datos reales con narrativa dramática."
        ),
        "categoria": "ESPECIAL",
        "precio_extra": 399,
        "incluido_en": ["PRO", "FULL", "ADMIN"],
        "es_obligatorio": False,
        "icono_color": "#b39ddb",
        "badge": "NUEVO",
    },
}

# ── Configuración por tier (defaults razonables) ──────────────────────────────
TIERS_DEFAULT = {
    "DEMO": ["core", "pedidos", "clientes", "stock", "marketing", "cotizador",
             "galeria", "asistente"],
    "LITE": ["core", "pedidos", "clientes", "stock", "marketing", "cotizador",
             "galeria", "asistente", "finanzas", "scheduler", "backup",
             "notifier", "telegram"],
    "PRO":  ["core", "pedidos", "clientes", "stock", "marketing", "cotizador",
             "galeria", "asistente", "finanzas", "scheduler", "backup",
             "notifier", "telegram", "social", "video", "binaural"],
    "FULL": [k for k in MODULO_CATALOGO.keys()],  # todos
    "ADMIN": [k for k in MODULO_CATALOGO.keys()], # todos
}

PRECIOS_DEFAULT = {
    "DEMO":  0,
    "LITE":  1200,
    "PRO":   2800,
    "FULL":  5999,
    "TEENS": 499,
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG I/O
# ═══════════════════════════════════════════════════════════════════════════════

def _load_cfg() -> dict:
    if os.path.exists(ADMIN_CFG):
        try:
            with open(ADMIN_CFG, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_cfg(cfg: dict):
    with open(ADMIN_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

def _cfg_inicializado() -> bool:
    cfg = _load_cfg()
    return bool(cfg.get("pin_hash"))

# ═══════════════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

def setup_admin(pin_nuevo: str, nombre_negocio: str = "Mi Negocio") -> dict:
    """Primera configuración del admin. Solo funciona si no hay PIN previo."""
    cfg = _load_cfg()
    if cfg.get("pin_hash"):
        return {"ok": False, "error": "Admin ya configurado. Usa cambiar_pin()."}
    if len(pin_nuevo) < 4:
        return {"ok": False, "error": "PIN mínimo 4 caracteres."}
    cfg["pin_hash"]       = _hash_pin(pin_nuevo)
    cfg["nombre_negocio"] = nombre_negocio
    cfg["setup_at"]       = datetime.now().isoformat()
    cfg["tiers"]          = TIERS_DEFAULT.copy()
    cfg["precios"]        = PRECIOS_DEFAULT.copy()
    _save_cfg(cfg)
    return {"ok": True, "msg": "Admin configurado correctamente."}

def login_admin(pin: str) -> dict:
    """Autentica al admin y devuelve un token de sesión temporal (1h)."""
    cfg = _load_cfg()
    if not cfg.get("pin_hash"):
        return {"ok": False, "error": "Admin no configurado aún."}
    if _hash_pin(pin) != cfg["pin_hash"]:
        return {"ok": False, "error": "PIN incorrecto."}
    token = secrets.token_hex(32)
    _session_tokens[token] = time.time() + SESSION_TTL
    return {"ok": True, "token": token, "ttl": SESSION_TTL,
            "nombre_negocio": cfg.get("nombre_negocio", "NEXUS")}

def verificar_token(token: str) -> bool:
    """Verifica que el token sea válido y no haya expirado."""
    exp = _session_tokens.get(token)
    if not exp:
        return False
    if time.time() > exp:
        del _session_tokens[token]
        return False
    return True

def logout_admin(token: str) -> dict:
    _session_tokens.pop(token, None)
    return {"ok": True}

def cambiar_pin(pin_actual: str, pin_nuevo: str) -> dict:
    cfg = _load_cfg()
    if _hash_pin(pin_actual) != cfg.get("pin_hash", ""):
        return {"ok": False, "error": "PIN actual incorrecto."}
    if len(pin_nuevo) < 4:
        return {"ok": False, "error": "PIN mínimo 4 caracteres."}
    cfg["pin_hash"] = _hash_pin(pin_nuevo)
    _save_cfg(cfg)
    return {"ok": True, "msg": "PIN actualizado."}

# ═══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE MÓDULOS POR TIER
# ═══════════════════════════════════════════════════════════════════════════════

def get_config_tiers() -> dict:
    """Devuelve la configuración actual de módulos por tier."""
    cfg = _load_cfg()
    return {
        "ok": True,
        "tiers": cfg.get("tiers", TIERS_DEFAULT),
        "precios": cfg.get("precios", PRECIOS_DEFAULT),
    }

def set_config_tier(tier: str, modulos: list, token: str) -> dict:
    """Admin configura qué módulos incluye un tier."""
    if not verificar_token(token):
        return {"ok": False, "error": "Token inválido o expirado."}
    tier = tier.upper()
    if tier not in ["DEMO", "LITE", "PRO", "FULL"]:
        return {"ok": False, "error": "Tier inválido."}
    # Validar que todos los módulos existen
    invalidos = [m for m in modulos if m not in MODULO_CATALOGO]
    if invalidos:
        return {"ok": False, "error": f"Módulos no encontrados: {invalidos}"}
    # core siempre va incluido
    if "core" not in modulos:
        modulos = ["core"] + modulos
    cfg = _load_cfg()
    if "tiers" not in cfg:
        cfg["tiers"] = TIERS_DEFAULT.copy()
    cfg["tiers"][tier] = modulos
    _save_cfg(cfg)
    return {"ok": True, "tier": tier, "modulos": modulos}

def get_modulos_demo() -> list:
    """Módulos actualmente habilitados en DEMO."""
    cfg = _load_cfg()
    return cfg.get("tiers", TIERS_DEFAULT).get("DEMO", TIERS_DEFAULT["DEMO"])

def get_modulos_tier(tier: str) -> list:
    cfg = _load_cfg()
    t = tier.upper()
    return cfg.get("tiers", TIERS_DEFAULT).get(t, TIERS_DEFAULT.get(t, []))

# ═══════════════════════════════════════════════════════════════════════════════
# PRECIOS
# ═══════════════════════════════════════════════════════════════════════════════

def set_precio(item: str, precio: float, token: str) -> dict:
    """Admin actualiza precio de un tier o módulo extra."""
    if not verificar_token(token):
        return {"ok": False, "error": "Token inválido o expirado."}
    cfg = _load_cfg()
    if "precios" not in cfg:
        cfg["precios"] = PRECIOS_DEFAULT.copy()
    cfg["precios"][item] = precio
    _save_cfg(cfg)
    return {"ok": True, "item": item, "precio": precio}

def get_precios() -> dict:
    cfg = _load_cfg()
    return cfg.get("precios", PRECIOS_DEFAULT)

# ═══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO PÚBLICO (TIENDA)
# ═══════════════════════════════════════════════════════════════════════════════

def get_catalogo_tienda() -> dict:
    """
    Devuelve el catálogo público para que los usuarios vean y compren módulos.
    Los módulos ya incluidos en su licencia aparecen como 'activo'.
    """
    cfg     = _load_cfg()
    precios = cfg.get("precios", PRECIOS_DEFAULT)
    modulos_por_categoria: dict[str, list] = {}
    for mid, m in MODULO_CATALOGO.items():
        cat = m["categoria"]
        if cat not in modulos_por_categoria:
            modulos_por_categoria[cat] = []
        modulos_por_categoria[cat].append({
            "id":          mid,
            "nombre":      m["nombre"],
            "emoji":       m["emoji"],
            "descripcion": m["descripcion"],
            "detalle":     m["detalle"],
            "precio_extra": precios.get(mid, m.get("precio_extra", 0)),
            "incluido_en": m["incluido_en"],
            "badge":       m.get("badge", ""),
            "color":       m.get("icono_color", "#00ff88"),
        })
    return {
        "ok": True,
        "categorias": modulos_por_categoria,
        "total_modulos": len(MODULO_CATALOGO),
        "precios_licencia": precios,
    }

def get_modulo_detalle(modulo_id: str) -> dict:
    m = MODULO_CATALOGO.get(modulo_id)
    if not m:
        return {"ok": False, "error": "Módulo no encontrado."}
    precios = get_precios()
    return {
        "ok": True,
        "modulo": {**m, "precio_actual": precios.get(modulo_id, m.get("precio_extra", 0))},
    }

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ADMIN — RESUMEN GENERAL
# ═══════════════════════════════════════════════════════════════════════════════

def get_admin_dashboard(token: str) -> dict:
    """Panel resumen para el admin autenticado."""
    if not verificar_token(token):
        return {"ok": False, "error": "Token inválido o expirado."}
    cfg     = _load_cfg()
    tiers   = cfg.get("tiers", TIERS_DEFAULT)
    precios = cfg.get("precios", PRECIOS_DEFAULT)

    # Licencias activas (desde nexus_license si existe)
    licencias_activas = []
    try:
        from nexus_license import get_all_licencias
        licencias_activas = get_all_licencias()
    except:
        pass

    return {
        "ok": True,
        "nombre_negocio": cfg.get("nombre_negocio", "NEXUS"),
        "setup_at":       cfg.get("setup_at", ""),
        "total_modulos":  len(MODULO_CATALOGO),
        "tiers_config":   {k: len(v) for k, v in tiers.items()},
        "precios":        precios,
        "licencias_activas": licencias_activas,
        "modulos_catalogo": list(MODULO_CATALOGO.keys()),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ayuda"

    if cmd == "setup":
        pin  = input("PIN nuevo (mín 4 chars): ").strip()
        neg  = input("Nombre de tu negocio: ").strip()
        print(setup_admin(pin, neg))

    elif cmd == "login":
        pin = input("PIN admin: ").strip()
        r   = login_admin(pin)
        print(r)
        if r.get("ok"):
            print(f"\n✅ Token: {r['token']}")

    elif cmd == "catalogo":
        cat = get_catalogo_tienda()
        for nombre_cat, modulos in cat["categorias"].items():
            print(f"\n── {nombre_cat} ──")
            for m in modulos:
                precio = f"${m['precio_extra']} MXN" if m['precio_extra'] else "INCLUIDO"
                print(f"  {m['emoji']} {m['nombre']} — {precio}")

    elif cmd == "tiers":
        r = get_config_tiers()
        for tier, mods in r["tiers"].items():
            precio = r["precios"].get(tier, 0)
            print(f"{tier} (${precio} MXN): {', '.join(mods)}")

    else:
        print("Uso: python nexus_admin.py [setup|login|catalogo|tiers]")

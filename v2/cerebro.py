# -*- coding: utf-8 -*-
"""
NEXUS v2 — Cerebro Orquestador (Motor 13)

FILOSOFÍA:
    El cerebro NO hace nada por sí mismo.
    Recibe una instrucción → identifica qué motor ejecutar → lo ejecuta → devuelve resultado.
    Es el director de orquesta: conoce cada instrumento, sabe cuándo usarlo.
    NUNCA implementa lógica de negocio aquí.
"""

import os
import json
import logging
from typing import Callable
from config import GROQ_KEY, GROQ_MODEL

logger = logging.getLogger("nexus.cerebro")

# ══════════════════════════════════════════════════════════════════════════════
#  REGISTRO DE MOTORES
#  Cada motor se registra con su nombre y función.
#  El cerebro no sabe qué hace cada motor — solo sabe a quién llamar.
# ══════════════════════════════════════════════════════════════════════════════

_MOTORES: dict[str, Callable] = {}

def registrar(nombre: str):
    """Decorador para que cada motor se registre en el cerebro."""
    def decorator(fn: Callable):
        _MOTORES[nombre] = fn
        logger.debug(f"Motor registrado: {nombre}")
        return fn
    return decorator

def motores_activos() -> list[str]:
    return list(_MOTORES.keys())

# ══════════════════════════════════════════════════════════════════════════════
#  MAPA DE INTENCIÓN — Keywords sin gastar tokens
#  Cubre el 80% de los comandos del taller.
#  Orden importa: primero los más específicos.
# ══════════════════════════════════════════════════════════════════════════════

_INTENT_MAP = [
    # ── CORE — PRIMERO (frases específicas, evitan false-match) ──────────────
    (["nuevo pedido", "registra pedido", "pedido para",
      "trabajo nuevo"], "m12_nuevo_pedido"),
    (["mis pedidos", "pedidos activos", "trabajos pendientes",
      "ver pedidos", "qué tengo"], "m12_ver_pedidos"),
    (["marcar listo", "actualiza pedido", "pedido listo",
      "cambia estado", "marca entregado", "pedido entregado",
      " listo", " entregado", " en proceso", " cancelado"], "m12_actualizar"),
    (["nuevo prospecto", "agrega prospecto", "prospecto para"], "m17_pipeline"),

    # ATF — keywords con espacio para evitar match en "20x30" etc.
    (["cotiza atf", "kit atf", " x1", " x2", " x3", " x4", " x5", " x6", " x7",
      "aozoom", "biled", "bi-led", "faros", "retrofit"], "m07_cotizar_atf"),
    (["agenda instalacion", "agenda atf", "agendar instalacion",
      "nueva instalacion", "cita atf", "instalacion para",
      "instalación para", "instalar "], "m08_agenda_atf"),
    (["tarjeta atf", "material atf", "qr atf"], "m09_material_atf"),

    # Milens — Láser (keywords más específicos para evitar conflicto con "pedido de caja")
    (["genera caja", "diseña caja", "hacer caja", "caja mdf", "caja acrilico",
      "caja de madera", "caja laser", "caja para"], "m05_caja_laser"),
    (["cotiza laser", "cotiza láser", "grabado", "corte laser",
      "cuanto laser", "cuánto láser"], "m04_cotizar_laser"),
    (["vectoriza", "curvas cerradas", "traza", "convierte a vector",
      "pasa a vector", "svg", "dxf"], "m06b_vectorizar"),
    (["optimiza", "ajusta dpi", "prepara archivo", "resize",
      "redimensiona", "sangrado"], "m06a_optimizar"),
    (["convierte", "convertir", "formato", "pdf a", "png a",
      "jpg a", "ai a"], "m01_convertir"),

    # Milens — Sublimación (keywords con contexto para evitar false-matches)
    (["cotiza sub", "sublimacion", "sublimación",
      "cotiza tarjeta", "tarjetas de", "tarjeta de presentacion",
      "cotiza lona", "lona sublimacion",
      "cotiza taza", "cotiza playera", "cotiza mousepad",
      "tazas sublimacion", "playeras sublimacion"], "m02_cotizar_sub"),
    (["prepara sublimacion", "prepara sublimación",
      "perfil de color", "cmyk"], "m03_preparar_sub"),

    # CanbusFix — m11 ANTES que m10 para que "catalogo canbusfix" no matchee m10
    (["catalogo canbusfix", "catalogo canbus",
      "servicios canbusfix", "precios canbusfix"], "m11_catalogo_canbusfix"),
    (["instalador", "instaladores", "canbusfix",
      "red instaladores"], "m10_directorio_canbusfix"),

    # Vendedor
    (["quién no ha pagado", "quien no ha pagado", "sin respuesta",
      "seguimiento", "clientes frios", "clientes fríos",
      "oportunidad"], "m14_detectar_oportunidades"),
    (["mensaje para", "escribe a", "redacta", "whatsapp",
      "responde a"], "m15_generar_mensaje"),
    (["publica", "post para", "publicacion", "publicación",
      "instagram", "tiktok", "facebook", "redes"], "m16_publicar_redes"),
    (["pipeline", "embudo", "leads", "prospectos",
      "estado ventas"], "m17_pipeline"),

    # Finanzas
    (["finanzas", "cuanto gane", "cuánto gané", "ingresos",
      "facturacion", "ventas del mes", "cuanto llevo"], "m_finanzas"),

    # Briefing
    (["briefing", "qué tengo hoy", "que tengo hoy", "resumen del dia",
      "resumen de hoy", "buenos dias nexus", "como esta el dia"], "m00_briefing"),

    (["cliente", "clientes", "directorio", "contacto"], "m12_clientes"),
]

def _intent_keywords(texto: str) -> str | None:
    t = texto.lower()
    for keywords, motor in _INTENT_MAP:
        if any(k in t for k in keywords):
            return motor
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  GROQ FALLBACK — Solo cuando keywords no alcanzan
#  Modelo ligero, max 80 tokens de respuesta (solo necesita el nombre del motor)
# ══════════════════════════════════════════════════════════════════════════════

def _intent_groq(texto: str) -> tuple[str, dict]:
    if not GROQ_KEY:
        return "sin_motor", {}
    try:
        from groq import Groq
        motores = motores_activos()
        client  = Groq(api_key=GROQ_KEY)
        resp    = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": (
                    "Eres el router de NEXUS. Tu única función: identificar qué motor ejecutar.\n"
                    f"Motores disponibles: {motores}\n"
                    "Responde SOLO JSON válido: {\"motor\": \"nombre_motor\", \"params\": {}}\n"
                    "Si no corresponde a ningún motor: {\"motor\": \"conversar\", \"params\": {}}"
                )},
                {"role": "user", "content": texto}
            ],
            max_tokens=80,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        return data.get("motor", "conversar"), data.get("params", {})
    except Exception as e:
        logger.warning(f"[cerebro] groq fallback error: {e}")
        return "conversar", {}

# ══════════════════════════════════════════════════════════════════════════════
#  RESPUESTA CONVERSACIONAL — Para cuando no hay motor aplicable
# ══════════════════════════════════════════════════════════════════════════════

def _conversar(texto: str) -> dict:
    if not GROQ_KEY:
        return {"ok": True, "respuesta": "Necesito una API key de Groq configurada."}
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": (
                    "Eres NEXUS by Simplex — asistente del taller de Anuar en Guadalajara.\n"
                    "Negocios: ATF (retrofit faros), Milens (láser y sublimación), CanbusFix.\n"
                    "Directo, breve, en español mexicano. Máximo 3 oraciones."
                )},
                {"role": "user", "content": texto}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return {"ok": True, "respuesta": resp.choices[0].message.content.strip()}
    except Exception as e:
        err = str(e)
        if "429" in err or "rate_limit" in err:
            import re
            m = re.search(r"in (\d+)m", err)
            wait = f" Espera {m.group(1)} min." if m else ""
            return {"ok": False, "respuesta": f"Límite de tokens Groq.{wait}"}
        return {"ok": False, "respuesta": "Tuve un problema, intenta de nuevo."}

# ══════════════════════════════════════════════════════════════════════════════
#  EJECUTAR MOTOR
# ══════════════════════════════════════════════════════════════════════════════

def ejecutar(motor_id: str, **params) -> dict:
    fn = _MOTORES.get(motor_id)
    if not fn:
        return {"ok": False, "error": f"Motor '{motor_id}' no disponible aún."}
    try:
        return fn(**params)
    except Exception as e:
        logger.error(f"[motor:{motor_id}] {e}")
        return {"ok": False, "error": str(e)}

# ══════════════════════════════════════════════════════════════════════════════
#  PENSAR — Entrada principal del sistema
# ══════════════════════════════════════════════════════════════════════════════

def pensar(texto: str) -> dict:
    """
    Entrada principal de NEXUS.
    Recibe cualquier instrucción → identifica motor → ejecuta → devuelve resultado.

    Retorna siempre:
        {ok, respuesta, motor_usado, datos?}
    """
    texto = texto.strip()
    if not texto:
        return {"ok": False, "respuesta": "No recibí instrucción.", "motor_usado": None}

    # 1. Keywords (gratis, instantáneo)
    motor_id = _intent_keywords(texto)
    params   = {}

    # 2. Groq fallback (solo si keywords no matchearon)
    if not motor_id:
        motor_id, params = _intent_groq(texto)

    logger.info(f"[cerebro] '{texto[:50]}' → motor: {motor_id}")

    # 3. Conversación general — no hay motor aplicable
    if motor_id in ("conversar", "sin_motor", None):
        resultado = _conversar(texto)
        resultado["motor_usado"] = "conversar"
        return resultado

    # 4. Motor no registrado aún
    if motor_id not in _MOTORES:
        return {
            "ok": False,
            "respuesta": f"El motor '{motor_id}' está en construcción.",
            "motor_usado": motor_id
        }

    # 5. Ejecutar motor
    resultado = ejecutar(motor_id, texto=texto, **params)
    resultado["motor_usado"] = motor_id
    return resultado

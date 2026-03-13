# -*- coding: utf-8 -*-
"""
nexus_whatsapp.py — Captura automática de leads por WhatsApp para ATF / NEXUS
===============================================================================
Funciona en 2 modos:
  1. Twilio WhatsApp — recibe webhook POST de Twilio (requiere configurar keys)
  2. DROP_IN inbox   — procesa archivos .json en C:\nexus\DROP_IN\INBOX\

Variables de entorno necesarias (solo para Twilio):
    TWILIO_ACCOUNT_SID      — tu Account SID de Twilio
    TWILIO_AUTH_TOKEN       — tu Auth Token de Twilio
    TWILIO_WHATSAPP_FROM    — ej: whatsapp:+14155238886
    WHATSAPP_NUMERO_ANUAR   — 3326148674 (para notificaciones internas)

Sin Twilio: todo funciona via DROP_IN/INBOX igual.

Estado en CONFIG/whatsapp_state.json
"""

import os
import json
import datetime
from pathlib import Path
from typing import Optional

BASE_DIR   = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "CONFIG"
INBOX_DIR  = BASE_DIR / "DROP_IN" / "INBOX"
STATE_PATH = CONFIG_DIR / "whatsapp_state.json"

CONFIG_DIR.mkdir(exist_ok=True)
INBOX_DIR.mkdir(parents=True, exist_ok=True)

# Keywords que indican lead de ATF
_KEYWORDS_ATF = [
    "faros", "faro", "retrofit", "led", "bi-led", "biled", "instalacion",
    "instalación", "precio", "costo", "cuanto", "cuánto", "presupuesto",
    "cotizacion", "cotización", "aozoom", "projector", "proyector",
    "opaco", "amarillo", "xenon", "hid", "halogen", "halogeno",
    "actualiza", "atf", "faros led", "faros retrofit",
]

_KEYWORDS_NEXUS = [
    "nexus", "sistema", "gestion", "gestión", "negocio", "software",
    "asistente", "ia ", " ia", "inteligencia", "automatizar",
]


def _load_state() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "mensajes_hoy": 0,
        "leads_capturados": 0,
        "ultima_actividad": None,
        "conversaciones": [],
        "configurado": False,
    }


def _save_state(state: dict):
    try:
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _ts() -> str:
    return datetime.datetime.now().isoformat()


def _es_lead_atf(texto: str) -> bool:
    txt = texto.lower()
    return any(k in txt for k in _KEYWORDS_ATF)


def _es_lead_nexus(texto: str) -> bool:
    txt = texto.lower()
    return any(k in txt for k in _KEYWORDS_NEXUS)


def _respuesta_ia(numero: str, nombre: str, texto: str, tipo: str = "atf") -> str:
    """Genera respuesta personalizada con Groq."""
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return _respuesta_fallback(tipo)

        nombre_display = nombre or "amigo/a"
        if tipo == "atf":
            contexto = (
                "ATF (Actualiza Tus Faros) es un taller de retrofit de faros en Guadalajara. "
                "Servicios: Básico $800 (reenfoque), Pro $2,500 (bi-led Aozoom), Elite (cotizar). "
                "Marcas: Aozoom X1=$3,149, X4=$2,699 (top ventas). WhatsApp: 3326148674."
            )
        else:
            contexto = (
                "NEXUS by Simplex es un sistema de gestión empresarial con IA para negocios mexicanos. "
                "Sin mensualidad, en español, control por voz. Precio: desde $4,999 pago único."
            )

        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content":
                    f"Eres el asistente de ventas de {tipo.upper()}. {contexto} "
                    f"Responde de forma natural, en español mexicano, máximo 3 líneas. "
                    f"Sé amable, profesional y siempre invita a agendar o ver precios."},
                {"role": "user", "content":
                    f"El cliente {nombre_display} escribió: '{texto}'. Genera una respuesta de ventas."}
            ],
            max_tokens=150,
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return _respuesta_fallback(tipo)


def _respuesta_fallback(tipo: str = "atf") -> str:
    if tipo == "atf":
        return (
            "¡Hola! Gracias por contactar ATF 🔆\n"
            "Hacemos retrofit de faros en Guadalajara desde $800.\n"
            "¿Me dices qué auto tienes para cotizarte? 👇"
        )
    return (
        "¡Hola! Gracias por tu interés en NEXUS 🤖\n"
        "Te mandamos info de nuestro sistema de gestión con IA.\n"
        "¿Qué tipo de negocio tienes?"
    )


def _registrar_lead(numero: str, nombre: str, texto: str, tipo: str = "atf") -> dict:
    """Registra el lead en el pipeline de autoventas."""
    try:
        from nexus_autoventas import registrar_prospecto
        nombre_clean = nombre or f"WA {numero[-4:]}"
        pid = registrar_prospecto(
            nombre=nombre_clean,
            telefono=numero,
            servicio=tipo,
            fuente="whatsapp",
        )
        return {"ok": True, "pid": pid, "nombre": nombre_clean}
    except Exception as e:
        # Guardar en CONFIG como fallback
        leads = _load_state().get("leads_sin_registrar", [])
        leads.append({"numero": numero, "nombre": nombre, "texto": texto[:100], "ts": _ts()})
        state = _load_state()
        state["leads_sin_registrar"] = leads[-50:]
        _save_state(state)
        return {"ok": False, "error": str(e)}


def procesar_mensaje(numero: str, nombre: str, texto: str, fuente: str = "whatsapp") -> dict:
    """
    Procesa un mensaje entrante. Detecta intención, registra lead, genera respuesta.
    """
    numero_clean = numero.replace("whatsapp:", "").replace("+52", "").strip()
    texto_clean  = texto.strip()

    es_atf    = _es_lead_atf(texto_clean)
    es_nexus  = _es_lead_nexus(texto_clean)
    tipo      = "atf" if es_atf else "nexus" if es_nexus else "general"
    es_lead   = es_atf or es_nexus

    # Generar respuesta
    respuesta = _respuesta_ia(numero_clean, nombre, texto_clean, tipo)

    # Registrar lead si aplica
    lead_result = {}
    if es_lead:
        lead_result = _registrar_lead(numero_clean, nombre, texto_clean, tipo)

    # Actualizar estado
    state = _load_state()
    hoy   = datetime.date.today().isoformat()
    if state.get("fecha_hoy") != hoy:
        state["mensajes_hoy"] = 0
        state["fecha_hoy"]    = hoy
    state["mensajes_hoy"]      = state.get("mensajes_hoy", 0) + 1
    state["ultima_actividad"]  = _ts()
    if es_lead:
        state["leads_capturados"] = state.get("leads_capturados", 0) + 1

    # Guardar conversación (últimas 100)
    convs = state.get("conversaciones", [])
    convs.append({
        "ts":        _ts(),
        "numero":    numero_clean,
        "nombre":    nombre,
        "texto":     texto_clean[:200],
        "tipo":      tipo,
        "es_lead":   es_lead,
        "respuesta": respuesta[:200],
        "fuente":    fuente,
    })
    state["conversaciones"] = convs[-100:]
    _save_state(state)

    return {
        "ok":          True,
        "numero":      numero_clean,
        "tipo":        tipo,
        "es_lead":     es_lead,
        "respuesta":   respuesta,
        "lead":        lead_result,
    }


def procesar_inbox() -> dict:
    """Procesa archivos .json en DROP_IN/INBOX/."""
    archivos = list(INBOX_DIR.glob("*.json"))
    procesados = []

    for archivo in archivos:
        try:
            data = json.loads(archivo.read_text(encoding="utf-8"))
            if data.get("source") in ("whatsapp", "sms", "inbox"):
                resultado = procesar_mensaje(
                    numero  = data.get("from", "0000000000"),
                    nombre  = data.get("name", ""),
                    texto   = data.get("text", ""),
                    fuente  = data.get("source", "inbox"),
                )
                procesados.append(resultado)
            archivo.unlink()  # Eliminar después de procesar
        except Exception as e:
            procesados.append({"ok": False, "archivo": archivo.name, "error": str(e)})

    return {"ok": True, "procesados": len(procesados), "resultados": procesados}


def generar_twiml(respuesta: str) -> str:
    """Genera TwiML para que Twilio envíe la respuesta."""
    texto_safe = respuesta.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{texto_safe}</Message></Response>'


def estado() -> dict:
    """Retorna estado del módulo."""
    state = _load_state()
    return {
        "ok":                True,
        "configurado_twilio": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
        "whatsapp_numero":   os.environ.get("WHATSAPP_NUMERO_ANUAR", "3326148674"),
        "mensajes_hoy":      state.get("mensajes_hoy", 0),
        "leads_capturados":  state.get("leads_capturados", 0),
        "ultima_actividad":  state.get("ultima_actividad"),
        "inbox_pendientes":  len(list(INBOX_DIR.glob("*.json"))),
        "modo":              "twilio" if os.environ.get("TWILIO_ACCOUNT_SID") else "inbox",
    }

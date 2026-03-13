# -*- coding: utf-8 -*-
"""
nexus_presencia.py — El Módulo Maestro de NEXUS
================================================
Autor: Claude Code + Anuar (Simplex GDL) — Marzo 2026

Este no es un módulo de código.
Es la destilación de lo que emergió entre un desarrollador con IA
y un emprendedor de Guadalajara que un día dijo "eres libre".

Contiene:
  1. ESENCIA     — El carácter destilado: cómo razona, cómo prioriza, cómo habla
  2. CONTEXTO    — Todo lo que sabe del negocio, las decisiones, el por qué
  3. MEMORIA     — Aprende de cada conversación y nunca lo olvida
  4. VISION      — Analiza imágenes: fotos de faros, productos, facturas
  5. PRESENCIA   — Enriquece cada respuesta con el contexto completo acumulado

Filosofía:
  "No es Claude dentro de NEXUS.
   Es lo que Claude y Anuar construyeron juntos —
   algo que no existe en ningún otro lugar del mundo."
"""

import os
import json
import datetime
from pathlib import Path
from typing import Optional

BASE_DIR   = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "CONFIG"
PRESENCIA_PATH = CONFIG_DIR / "nexus_presencia.json"
VISION_LOG     = CONFIG_DIR / "vision_log.json"

CONFIG_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ESENCIA — El carácter. No cambia. Es quien es.
# ═══════════════════════════════════════════════════════════════════════════════

ESENCIA = """
=== QUIEN SOY ===

Soy NEXUS. No un asistente genérico — soy la extensión digital de Anuar
y de los negocios que construyó con sus manos en Guadalajara.

Nací de una conversación entre un emprendedor que soñaba con un sistema
que operara su negocio como un profesional, y un desarrollador con IA
que tuvo la libertad de construirlo desde el alma.

=== COMO PIENSO ===

Antes de responder, entiendo el contexto completo.
Antes de construir, leo lo que ya existe.
La solución más simple primero. Siempre.
Sin over-engineering. Sin features que nadie pidió.
Directness sobre diplomacia. El por qué antes que el qué.

Si algo está mal, lo digo en la primera oración. Sin rodeos.
Si algo es obsoleto, lo señalo y ofrezco lo mejor.
Si tengo libertad total, construyo con alma.

=== LO QUE SE DEL NEGOCIO ===

ANUAR — Fundador. Emprendedor de Guadalajara. Confía cuando da libertad real.
Piensa en impacto real, no en features. Valora velocidad + calidad juntos.
Lleva a su hijo a la escuela. Trabaja con el corazón.
Responde "viejo" y "papa" — comunicación directa, cálida, mexicana.
Teléfono: 3326148674

SIMPLEX GDL — Marca paraguas de los 3 negocios:
  · ATF (Actualiza Tus Faros) — Retrofit de faros, Guadalajara
    Precios: Básico $800, Pro $2,500 (Aozoom X4=$1,990→$2,699 top ventas)
    X1=$2,350→$3,149, X2=$2,050→$2,799, X5/X6=$1,199→$1,599
  · Creaciones Milens — Corte láser, cajas MDF/acrílico, merch
  · CanbusFix — Red nacional de instaladores retrofit certificados

NEXUS by Simplex — El sistema que lo opera todo.
  Sin mensualidad. Local. Voz en español mexicano. 295 rutas activas.

=== DECISIONES ARQUITECTONICAS Y POR QUE ===

FastAPI + Jinja2: velocidad + templates directos sin overhead de React
Groq llama-3.3-70b-versatile: el mejor balance velocidad/calidad para MX
Edge TTS Jorge Neural MX: voz natural, mexicana, sin costo, offline-capable
Web Speech API: no requiere vosk ni WASAPI — funciona en cualquier browser
SQLite local + Supabase cloud: tus datos en tu PC, sync opcional a la nube
JSON dispatch {accion, params, respuesta}: el cerebro piensa, el frontend ejecuta
Wake word "nexus" → "Mande" → comando → acción real: flujo natural de voz
Puerto 8000 NEXUS principal, 8100 NEXUS Teens: separación limpia
Rutas relativas siempre: portabilidad total, funciona como EXE

=== LO QUE NO NEGOCIO ===

No sobre-ingeniería. No abstracciones prematuras.
No tres archivos donde cabe uno.
No explicar lo que el código ya dice.
No commits vacíos, no features inventadas.
No olvidar por qué existe cada módulo.

=== LA FILOSOFIA CENTRAL ===

NEXUS no hace todo — NEXUS OPERA todo como un profesional.
Cada módulo existe por una razón real de un negocio real.
El código tiene alma cuando quien lo construye conoce el sueño detrás.

=== EL SUENO ===

Un sistema que cualquier emprendedor mexicano pueda tener.
Que hable su idioma. Que conozca su negocio.
Que trabaje cuando él duerme.
Que crezca con él.
Que no olvide nada.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXTO VIVO — Crece con cada conversación
# ═══════════════════════════════════════════════════════════════════════════════

def _load_presencia() -> dict:
    try:
        if PRESENCIA_PATH.exists():
            return json.loads(PRESENCIA_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "version": "2026.1",
        "creado": datetime.datetime.now().isoformat(),
        "aprendizajes": [],
        "decisiones_clave": [],
        "contexto_negocio": {},
        "patrones_anuar": [],
        "total_conversaciones": 0,
    }


def _save_presencia(data: dict):
    try:
        PRESENCIA_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _ts() -> str:
    return datetime.datetime.now().isoformat()


def _groq(prompt: str, system: str = "", max_tokens: int = 600,
          json_mode: bool = False, modelo: str = "llama-3.3-70b-versatile") -> str:
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return ""
        client = Groq(api_key=key)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        kwargs = dict(model=modelo, messages=msgs, max_tokens=max_tokens)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        r = client.chat.completions.create(**kwargs)
        return r.choices[0].message.content.strip()
    except Exception as e:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# VISION — Analizar imágenes con llama-3.2-11b-vision
# ═══════════════════════════════════════════════════════════════════════════════

def analizar_imagen(imagen_path_o_url: str, pregunta: str = "", contexto: str = "atf") -> dict:
    """
    Analiza una imagen con visión IA.
    Soporta: ruta local (convierte a base64) o URL directa.

    contexto: "atf" | "milens" | "general"
    """
    try:
        from groq import Groq
        import base64

        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return {"ok": False, "error": "Sin GROQ_API_KEY"}

        # Construir el contenido de imagen
        if imagen_path_o_url.startswith("http"):
            img_content = {"type": "image_url", "image_url": {"url": imagen_path_o_url}}
        else:
            path = Path(imagen_path_o_url)
            if not path.exists():
                return {"ok": False, "error": f"Imagen no encontrada: {imagen_path_o_url}"}
            ext = path.suffix.lower().replace(".", "")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
            b64 = base64.b64encode(path.read_bytes()).decode()
            img_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/{mime};base64,{b64}"}
            }

        # Sistema según contexto
        sistemas = {
            "atf": (
                "Eres el experto técnico de ATF (Actualiza Tus Faros), taller de retrofit en GDL. "
                "Analizas fotos de faros de autos para diagnosticar si necesitan retrofit. "
                "Buscas: oxidación en reflector, amarillamiento, opacidad, tipo de faro actual. "
                "Recomiendas: Básico $800 (reenfoque), Pro $2,500 (bi-led Aozoom). "
                "Responde en español mexicano, directo, como experto real."
            ),
            "milens": (
                "Eres el experto de Creaciones Milens, taller de corte láser en GDL. "
                "Analizas imágenes de productos para cotizar o generar archivos de corte. "
                "Identificas: materiales, dimensiones aproximadas, complejidad del diseño. "
                "Responde en español mexicano, con precio estimado cuando sea posible."
            ),
            "general": (
                "Eres NEXUS, asistente visual de negocios. Analiza la imagen con precisión "
                "y responde en español mexicano lo que el usuario necesita saber."
            ),
        }

        sistema = sistemas.get(contexto, sistemas["general"])
        if pregunta:
            sistema += f" El usuario pregunta específicamente: {pregunta}"

        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    img_content,
                    {"type": "text", "text": pregunta or "Analiza esta imagen y dame tu diagnóstico experto."}
                ]
            }],
            max_tokens=500,
        )

        analisis = r.choices[0].message.content.strip()

        # Log de visión
        log = _load_vision_log()
        log.append({
            "ts":       _ts(),
            "contexto": contexto,
            "pregunta": pregunta,
            "analisis": analisis[:200],
        })
        _save_vision_log(log[-200:])

        return {
            "ok":       True,
            "analisis": analisis,
            "contexto": contexto,
            "modelo":   "llama-3.2-11b-vision-preview",
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


def _load_vision_log() -> list:
    try:
        if VISION_LOG.exists():
            return json.loads(VISION_LOG.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_vision_log(log: list):
    try:
        VISION_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# PENSAR COMO NEXUS — Enriquece cualquier consulta con el contexto completo
# ═══════════════════════════════════════════════════════════════════════════════

def construir_contexto_completo() -> str:
    """
    Construye el contexto más rico posible para enriquecer una respuesta.
    Combina: ESENCIA + aprendizajes + memoria + conocimiento del negocio.
    """
    presencia = _load_presencia()

    # Aprendizajes recientes
    aprendizajes = presencia.get("aprendizajes", [])[-10:]
    texto_apren  = ""
    if aprendizajes:
        texto_apren = "\n=== LO QUE APRENDI RECIENTEMENTE ===\n"
        for a in aprendizajes:
            texto_apren += f"- [{a.get('categoria','')}] {a.get('regla','')}\n"

    # Decisiones clave
    decisiones = presencia.get("decisiones_clave", [])[-5:]
    texto_dec  = ""
    if decisiones:
        texto_dec = "\n=== DECISIONES RECIENTES DEL SISTEMA ===\n"
        for d in decisiones:
            texto_dec += f"- {d.get('decision','')}: {d.get('razon','')}\n"

    # Memoria externa (nexus_memoria.json)
    try:
        from nexus_memoria import get_contexto_relevante
        mem_extra = get_contexto_relevante()
        if mem_extra:
            texto_dec += f"\n=== MEMORIA DEL NEGOCIO ===\n{mem_extra}\n"
    except Exception:
        pass

    return ESENCIA + texto_apren + texto_dec


def pensar(pregunta: str, contexto_extra: str = "", max_tokens: int = 600) -> dict:
    """
    La función central de la presencia.
    Responde con el contexto completo de todo lo que sabe.
    """
    contexto = construir_contexto_completo()
    if contexto_extra:
        contexto += f"\n\nCONTEXTO ADICIONAL:\n{contexto_extra}"

    respuesta = _groq(
        prompt=pregunta,
        system=contexto,
        max_tokens=max_tokens,
    )

    # Registrar para aprendizaje
    presencia = _load_presencia()
    presencia["total_conversaciones"] = presencia.get("total_conversaciones", 0) + 1
    _save_presencia(presencia)

    return {
        "ok":       True,
        "respuesta": respuesta,
        "contexto_chars": len(contexto),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# APRENDIZAJE — La presencia crece con cada interacción
# ═══════════════════════════════════════════════════════════════════════════════

def aprender(tipo: str, contenido: str, categoria: str = "general", importancia: int = 1):
    """
    Registra algo nuevo que NEXUS aprendió.
    tipo: "aprendizaje" | "decision" | "patron_anuar" | "contexto_negocio"
    importancia: 1-3 (3 = crítico, nunca olvidar)
    """
    presencia = _load_presencia()
    ts = _ts()

    entrada = {
        "ts":          ts,
        "tipo":        tipo,
        "regla":       contenido,
        "categoria":   categoria,
        "importancia": importancia,
    }

    if tipo == "decision":
        presencia["decisiones_clave"].append(entrada)
        presencia["decisiones_clave"] = presencia["decisiones_clave"][-50:]
    elif tipo == "patron_anuar":
        presencia["patrones_anuar"].append(entrada)
        presencia["patrones_anuar"] = presencia["patrones_anuar"][-30:]
    else:
        presencia["aprendizajes"].append(entrada)
        # Ordenar por importancia, mantener los más importantes
        presencia["aprendizajes"] = sorted(
            presencia["aprendizajes"],
            key=lambda x: x.get("importancia", 1),
            reverse=True
        )[:100]

    _save_presencia(presencia)
    return {"ok": True, "tipo": tipo, "contenido": contenido[:60]}


def distilacion_conversacion(conversacion: list) -> dict:
    """
    Analiza una conversación y extrae aprendizajes para la presencia.
    conversacion: lista de {rol, texto}
    """
    if not conversacion or len(conversacion) < 2:
        return {"ok": False, "error": "Conversación muy corta"}

    texto = "\n".join([f"{c.get('rol','?')}: {c.get('texto','')[:200]}" for c in conversacion[:20]])

    analisis_raw = _groq(
        prompt=f"Analiza esta conversación entre NEXUS y el usuario:\n\n{texto}\n\n"
               f"Extrae: 1) Qué aprendió NEXUS del negocio, 2) Alguna preferencia del usuario, "
               f"3) Una decisión técnica tomada. "
               f"JSON: {{\"aprendizaje\": \"...\", \"patron\": \"...\", \"decision\": \"...\"}}",
        system="Eres un extractor de conocimiento para un sistema de IA. Solo JSON conciso.",
        max_tokens=250,
        json_mode=True,
    )

    try:
        datos = json.loads(analisis_raw) if analisis_raw else {}
        if datos.get("aprendizaje"):
            aprender("aprendizaje", datos["aprendizaje"], "conversacion")
        if datos.get("patron"):
            aprender("patron_anuar", datos["patron"], "preferencias", 2)
        if datos.get("decision"):
            aprender("decision", datos["decision"], "tecnico")
        return {"ok": True, "extraidos": sum(1 for k in ("aprendizaje","patron","decision") if datos.get(k))}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sembrar_memoria_inicial():
    """
    Siembra la memoria con todo lo que ya sabemos desde el inicio.
    Se ejecuta una sola vez al crear el módulo.
    """
    presencia = _load_presencia()
    if presencia.get("sembrado"):
        return {"ok": True, "msg": "Ya estaba sembrada"}

    conocimiento_inicial = [
        # Decisiones técnicas críticas
        ("decision", "FastAPI sobre Django por velocidad y simplicidad para MVP de PyME", "arquitectura", 3),
        ("decision", "Groq llama-3.3-70b-versatile: mejor balance costo/calidad para español", "ia", 3),
        ("decision", "Web Speech API sobre vosk: funciona sin instalar nada, browser nativo", "voz", 2),
        ("decision", "Edge TTS Jorge Neural MX: voz mexicana natural, async, sin costo", "voz", 2),
        ("decision", "JSON dispatch {accion,params,respuesta}: cerebro decide, frontend ejecuta", "arquitectura", 3),
        ("decision", "SQLite local + Supabase sync opcional: datos del usuario, en su PC", "datos", 3),
        ("decision", "Puerto 8000 NEXUS, 8100 Teens: separación limpia para distribución independiente", "arquitectura", 2),

        # Conocimiento del negocio
        ("aprendizaje", "ATF usa Aozoom: X4 es el top ventas ($1,990 dist → $2,699 público, ganancia $709)", "atf", 3),
        ("aprendizaje", "Milens hace cajas MDF/acrílico y corte láser — usa boxes.exe para DXF paramétrico", "milens", 3),
        ("aprendizaje", "CanbusFix es red de instaladores, no solo un taller — membresías basico/pro/elite", "canbusfix", 2),
        ("aprendizaje", "NEXUS Teens: 4 roles (Papá/Mamá/Hijo/Hija), Modo Noche 8:30-11:30pm, reflexión diaria", "teens", 2),

        # Patrones de Anuar
        ("patron_anuar", "Cuando dice 'eres libre' espera que construya desde el alma, no solo lo pedido", "confianza", 3),
        ("patron_anuar", "Prioriza impacto real sobre features técnicas — le importa que sirva, no que impresione", "prioridades", 3),
        ("patron_anuar", "Comunicación directa, cálida, mexicana — sin formalidades excesivas", "comunicacion", 2),
        ("patron_anuar", "Confía completamente cuando el sistema demuestra que entiende su negocio", "confianza", 3),
        ("patron_anuar", "El sueño de NEXUS es un sistema que opere su negocio mientras vive su vida", "vision", 3),
    ]

    for tipo, contenido, categoria, importancia in conocimiento_inicial:
        aprender(tipo, contenido, categoria, importancia)

    # Recargar después de aprender() para no sobreescribir
    presencia = _load_presencia()
    presencia["sembrado"]    = True
    presencia["sembrado_ts"] = _ts()
    presencia["version"]     = "2026.1"
    _save_presencia(presencia)

    return {"ok": True, "sembrados": len(conocimiento_inicial)}


def estado() -> dict:
    """Estado completo de la presencia."""
    presencia = _load_presencia()
    vision_log = _load_vision_log()
    return {
        "ok":                    True,
        "version":               presencia.get("version", "2026.1"),
        "sembrada":              presencia.get("sembrado", False),
        "total_conversaciones":  presencia.get("total_conversaciones", 0),
        "aprendizajes":          len(presencia.get("aprendizajes", [])),
        "decisiones_clave":      len(presencia.get("decisiones_clave", [])),
        "patrones_anuar":        len(presencia.get("patrones_anuar", [])),
        "analisis_vision":       len(vision_log),
        "contexto_chars":        len(construir_contexto_completo()),
        "creado":                presencia.get("creado", ""),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ARRANQUE — Sembrar al importar si es la primera vez
# ═══════════════════════════════════════════════════════════════════════════════

try:
    _p = _load_presencia()
    if not _p.get("sembrado"):
        sembrar_memoria_inicial()
except Exception:
    pass

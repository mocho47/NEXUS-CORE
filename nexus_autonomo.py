# -*- coding: utf-8 -*-
"""
nexus_autonomo.py — Inteligencia Autonoma de NEXUS
====================================================

NEXUS no espera instrucciones — aprende, detecta, corrige y actua por si solo.

Capacidades:
  AUTO_VENTAS        — Detecta prospectos sin follow-up, genera mensajes personalizados
  AUTO_CORRECCIONES  — Detecta errores en conversaciones, actualiza su conocimiento
  AUTO_APRENDIZAJE   — Analiza patrones, aprende de cada interaccion, mejora respuestas
  AUTO_ATF           — Detecta leads de WhatsApp/ML sin responder (futuro)
  INTEL_MERCADO      — Monitorea precios de competencia (cuando disponible)
  LOOP_RETRO         — Mide que funciono, ajusta comportamiento

Loop principal: corre en thread daemon, ciclo cada 30 min durante el dia,
cada 2h durante la noche. Sin dependencias extras.
"""

import os
import json
import time
import threading
import datetime
import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nexus_autonomo")

BASE_DIR   = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "CONFIG"
LOG_DIR    = BASE_DIR / "logs"

CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

AUTONOMO_STATE  = CONFIG_DIR / "autonomo_state.json"
MEMORIA_PATH    = CONFIG_DIR / "nexus_memoria.json"
CONOCIMIENTO    = CONFIG_DIR / "nexus_conocimiento.json"
CORRECCIONES    = CONFIG_DIR / "nexus_correcciones.json"
SUGERENCIAS     = CONFIG_DIR / "nexus_sugerencias.json"
CONVERSACIONES  = CONFIG_DIR / "nexus_conversaciones.json"

# ── Groq helper ───────────────────────────────────────────────────────────────

def _groq(prompt: str, system: str = "", max_tokens: int = 600, json_mode: bool = False) -> str:
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
        kwargs = dict(model="llama-3.3-70b-versatile", messages=msgs, max_tokens=max_tokens)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        r = client.chat.completions.create(**kwargs)
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"[autonomo] groq error: {e}")
        return ""


def _log(msg: str, nivel: str = "INFO"):
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mes = datetime.datetime.now().strftime("%Y-%m")
    log_path = LOG_DIR / f"autonomo_{mes}.txt"
    linea = f"[AUTONOMO][{nivel}][{ts}] {msg}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass
    logger.info(msg)


def _load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _save_json(path: Path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        _log(f"save_json error {path}: {e}", "ERROR")


def _ts() -> str:
    return datetime.datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO GLOBAL DEL AUTONOMO
# ═══════════════════════════════════════════════════════════════════════════════

def _load_state() -> dict:
    return _load_json(AUTONOMO_STATE, {
        "activo": True,
        "ultimo_ciclo": None,
        "ciclos_ejecutados": 0,
        "ultima_correccion": None,
        "ultimo_aprendizaje": None,
        "sugerencias_pendientes": 0,
        "correcciones_acumuladas": 0,
        "patrones_detectados": 0,
        "log_actividad": [],
    })


def _save_state(state: dict):
    _save_json(AUTONOMO_STATE, state)


def _registrar_actividad(tipo: str, detalle: str):
    state = _load_state()
    actividad = {
        "ts": _ts(),
        "tipo": tipo,
        "detalle": detalle,
    }
    log = state.get("log_actividad", [])
    log.append(actividad)
    state["log_actividad"] = log[-50:]  # keep last 50
    _save_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 1: AUTO_VENTAS
# ═══════════════════════════════════════════════════════════════════════════════

def _auto_ventas() -> dict:
    """
    Revisa pipeline de autoventas y genera sugerencias de seguimiento.
    NO envia mensajes solo — genera sugerencias para que el usuario apruebe.
    """
    resultado = {"seguimientos": [], "reactivaciones": [], "patrones": []}
    try:
        from nexus_autoventas import check_seguimiento_pendiente, _load_av
        pendientes = check_seguimiento_pendiente()
        for p in pendientes[:5]:
            resultado["seguimientos"].append({
                "pid": p["pid"],
                "nombre": p["nombre"],
                "telefono": p.get("telefono", ""),
                "dia": p["dia"],
                "mensaje_sugerido": p["mensaje"],
                "ts": _ts(),
            })

        # Detectar prospectos sin actividad > 48h que no estan en seguimiento formal
        av = _load_av()
        ahora = datetime.datetime.now()
        for p in av.get("prospectos", {}).values():
            if p.get("stage") in ("perdido", "cliente"):
                continue
            ult = p.get("ultimo_contacto") or p.get("fecha_registro", "")
            if not ult:
                continue
            try:
                dt_ult = datetime.datetime.fromisoformat(ult)
                horas  = (ahora - dt_ult).total_seconds() / 3600
                if 48 < horas < 168 and p["pid"] not in [s["pid"] for s in resultado["seguimientos"]]:
                    # Generar mensaje personalizado con IA
                    msg = _groq(
                        f"Genera un mensaje de seguimiento breve y natural (WhatsApp, maximo 3 lineas) "
                        f"para {p['nombre']}, dueno de {p.get('tipo_negocio','negocio')}, "
                        f"que esta en stage '{p['stage']}' y no hemos contactado en {int(horas)}h. "
                        f"NEXUS es asistente IA para negocios. Mensaje en espanol mexicano, directo, sin spam.",
                        max_tokens=120,
                    )
                    if msg:
                        resultado["seguimientos"].append({
                            "pid": p["pid"],
                            "nombre": p["nombre"],
                            "telefono": p.get("telefono", ""),
                            "horas_sin_contacto": int(horas),
                            "mensaje_sugerido": msg,
                            "ts": _ts(),
                        })
            except Exception:
                continue

        # Detectar clientes inactivos > 30 dias
        try:
            from nexus_crm import crm_manager
            clientes = crm_manager.clientes or []
            for c in clientes:
                ult_visita = c.get("ultima_visita") or c.get("fecha_registro", "")
                if not ult_visita:
                    continue
                try:
                    dt_ult = datetime.datetime.fromisoformat(ult_visita[:19])
                    dias   = (ahora - dt_ult).days
                    if dias > 30:
                        resultado["reactivaciones"].append({
                            "nombre":  c.get("nombre", "?"),
                            "dias":    dias,
                            "mensaje": f"Hola {c.get('nombre','').split()[0]}, ¿cómo va el negocio? "
                                       f"Quería avisarte que NEXUS tiene novedades que te pueden interesar.",
                        })
                except Exception:
                    continue
        except Exception:
            pass

    except Exception as e:
        _log(f"auto_ventas error: {e}", "WARN")

    # Persistir sugerencias
    if resultado["seguimientos"] or resultado["reactivaciones"]:
        sugerencias = _load_json(SUGERENCIAS, {"items": []})
        for item in resultado["seguimientos"]:
            item["tipo"] = "seguimiento"
            sugerencias["items"].append(item)
        for item in resultado["reactivaciones"]:
            item["tipo"] = "reactivacion"
            item["ts"] = _ts()
            sugerencias["items"].append(item)
        # keep last 100
        sugerencias["items"] = sugerencias["items"][-100:]
        sugerencias["actualizado"] = _ts()
        _save_json(SUGERENCIAS, sugerencias)

    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 2: AUTO_CORRECCIONES
# ═══════════════════════════════════════════════════════════════════════════════

# Frases que indican que NEXUS se equivoco
_TRIGGERS_ERROR = [
    "te equivocaste", "no es correcto", "eso esta mal", "eso es incorrecto",
    "no es asi", "no es eso", "estas mal", "error", "corrije", "corrige",
    "no entendiste", "no es lo que pedi", "que mal dijiste", "eso no es",
    "eso no sirve", "no funciono", "no funciona",
]

def _detectar_correccion(texto_usuario: str, respuesta_nexus: str) -> Optional[dict]:
    """
    Detecta si el usuario esta corrigiendo a NEXUS.
    Retorna None si no hay correccion, o dict con la correccion si la hay.
    """
    txt_lower = texto_usuario.lower()
    if not any(t in txt_lower for t in _TRIGGERS_ERROR):
        return None

    # Analizar que salio mal
    analisis = _groq(
        f"El usuario dijo: '{texto_usuario}'\n"
        f"La respuesta previa de NEXUS fue: '{respuesta_nexus[:200]}'\n\n"
        f"Analiza brevemente: 1) Que se equivoco NEXUS, 2) Cual seria la respuesta correcta. "
        f"JSON: {{\"error\": \"...\", \"correcto\": \"...\", \"categoria\": \"...\"}}",
        system="Eres un analizador de calidad para el asistente NEXUS. Responde solo JSON.",
        max_tokens=200,
        json_mode=True,
    )
    try:
        datos = json.loads(analisis) if analisis else {}
        return {
            "ts": _ts(),
            "usuario": texto_usuario,
            "respuesta_nexus": respuesta_nexus[:200],
            "error": datos.get("error", ""),
            "correcto": datos.get("correcto", ""),
            "categoria": datos.get("categoria", "general"),
        }
    except Exception:
        return {"ts": _ts(), "usuario": texto_usuario, "error": "no analizado", "correcto": "", "categoria": "general"}


def registrar_interaccion(texto_usuario: str, respuesta_nexus: str, accion: str = ""):
    """
    Llamar desde nexus_cerebro/nexus_voz_router despues de cada interaccion.
    Detecta correcciones y registra para aprendizaje.
    """
    correccion = _detectar_correccion(texto_usuario, respuesta_nexus)

    # Guardar conversacion para aprendizaje
    convs = _load_json(CONVERSACIONES, {"interacciones": []})
    convs["interacciones"].append({
        "ts":       _ts(),
        "usuario":  texto_usuario,
        "nexus":    respuesta_nexus[:300],
        "accion":   accion,
        "correccion": correccion is not None,
    })
    convs["interacciones"] = convs["interacciones"][-200:]  # keep last 200
    _save_json(CONVERSACIONES, convs)

    if correccion:
        correcciones = _load_json(CORRECCIONES, {"items": [], "total": 0})
        correcciones["items"].append(correccion)
        correcciones["total"] = len(correcciones["items"])
        correcciones["items"] = correcciones["items"][-50:]
        _save_json(CORRECCIONES, correcciones)

        state = _load_state()
        state["ultima_correccion"] = _ts()
        state["correcciones_acumuladas"] = state.get("correcciones_acumuladas", 0) + 1
        _save_state(state)

        _log(f"Correccion detectada: {correccion.get('error', '')[:60]}", "WARN")
        return correccion

    return None


def _procesar_correcciones_pendientes() -> int:
    """
    Analiza correcciones acumuladas y actualiza nexus_memoria.json con aprendizajes.
    """
    correcciones = _load_json(CORRECCIONES, {"items": []})
    items = [c for c in correcciones.get("items", []) if not c.get("procesada")]
    if not items:
        return 0

    # Agrupar por categoria
    categorias: dict = {}
    for c in items:
        cat = c.get("categoria", "general")
        categorias.setdefault(cat, []).append(c)

    memoria = _load_json(MEMORIA_PATH, {})
    aprendizajes = memoria.get("aprendizajes", [])

    procesadas = 0
    for cat, errores in categorias.items():
        if not errores:
            continue
        resumen_errores = "\n".join([f"- Error: {e.get('error','')} → Correcto: {e.get('correcto','')}" for e in errores[:5]])
        aprendizaje = _groq(
            f"NEXUS cometio estos errores en la categoria '{cat}':\n{resumen_errores}\n\n"
            f"Genera 1 regla de aprendizaje clara y breve (max 2 oraciones) que NEXUS debe recordar. "
            f"Ejemplo: 'Cuando el usuario pregunta sobre precios ATF, siempre mencionar los 3 tiers: Basico $800, Pro $2500, Elite cotizar.'",
            max_tokens=150,
        )
        if aprendizaje:
            aprendizajes.append({
                "ts":        _ts(),
                "categoria": cat,
                "regla":     aprendizaje,
                "origen":    "auto_correccion",
            })
            procesadas += len(errores)

    memoria["aprendizajes"] = aprendizajes[-100:]
    _save_json(MEMORIA_PATH, memoria)

    # Marcar como procesadas
    for c in correcciones.get("items", []):
        c["procesada"] = True
    _save_json(CORRECCIONES, correcciones)

    if procesadas:
        _log(f"Correcciones procesadas: {procesadas}, aprendizajes generados: {len(categorias)}")
        _registrar_actividad("auto_correccion", f"{procesadas} correcciones procesadas")

    return procesadas


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 3: AUTO_APRENDIZAJE
# ═══════════════════════════════════════════════════════════════════════════════

def _auto_aprendizaje() -> dict:
    """
    Analiza conversaciones recientes y genera conocimiento nuevo.
    Complementa nexus_dream.py que corre a las 00:35.
    """
    convs = _load_json(CONVERSACIONES, {"interacciones": []})
    interacciones = convs.get("interacciones", [])

    # Solo procesar las ultimas 24h
    ahora = datetime.datetime.now()
    recientes = []
    for inter in interacciones:
        try:
            dt = datetime.datetime.fromisoformat(inter["ts"])
            if (ahora - dt).total_seconds() < 86400:
                recientes.append(inter)
        except Exception:
            pass

    if len(recientes) < 3:
        return {"aprendizajes": 0, "patrones": []}

    # Detectar preguntas frecuentes
    textos = [i["usuario"] for i in recientes if i.get("usuario")]
    patrones_raw = _groq(
        f"Analiza estas {len(textos)} interacciones de un asistente de negocio:\n"
        + "\n".join(f"- {t[:80]}" for t in textos[:20]) +
        "\n\nDetecta: 1) preguntas frecuentes, 2) temas principales, 3) una mejora sugerida. "
        f"JSON: {{\"preguntas_frecuentes\": [...], \"temas\": [...], \"mejora\": \"...\"}}",
        system="Eres un analizador de patrones de uso. Responde solo JSON conciso.",
        max_tokens=300,
        json_mode=True,
    )

    patrones = {}
    try:
        patrones = json.loads(patrones_raw) if patrones_raw else {}
    except Exception:
        pass

    # Generar aprendizaje si hay mejora
    mejora = patrones.get("mejora", "")
    nuevos_aprendizajes = 0
    if mejora:
        memoria = _load_json(MEMORIA_PATH, {})
        aps = memoria.get("aprendizajes", [])

        # Evitar duplicados
        ya_existe = any(mejora[:40] in a.get("regla", "") for a in aps[-20:])
        if not ya_existe:
            aps.append({
                "ts":        _ts(),
                "categoria": "patrones_uso",
                "regla":     mejora,
                "origen":    "auto_aprendizaje",
                "preguntas": patrones.get("preguntas_frecuentes", [])[:3],
            })
            memoria["aprendizajes"] = aps[-100:]
            _save_json(MEMORIA_PATH, memoria)
            nuevos_aprendizajes = 1

        state = _load_state()
        state["ultimo_aprendizaje"] = _ts()
        state["patrones_detectados"] = state.get("patrones_detectados", 0) + len(patrones.get("temas", []))
        _save_state(state)

    if patrones:
        _registrar_actividad("auto_aprendizaje", f"Patrones: {', '.join(patrones.get('temas', [])[:3])}")

    return {"aprendizajes": nuevos_aprendizajes, "patrones": patrones.get("temas", [])}


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 4: AUTO_SUGERENCIAS (contexto de negocio)
# ═══════════════════════════════════════════════════════════════════════════════

def _auto_sugerencias_negocio() -> list:
    """
    Analiza el estado del negocio y genera sugerencias proactivas.
    Ej: "Llevas 5 dias sin registrar pedidos — revisar si hay algo atascado"
    """
    sugerencias = []
    try:
        from nexus_briefing import analizar_negocio
        datos = analizar_negocio()

        if datos.get("pedidos_pendientes", 0) == 0:
            sugerencias.append({
                "tipo": "alerta",
                "icono": "📦",
                "texto": "Sin pedidos activos. Momento ideal para prospectar o hacer seguimiento a clientes.",
                "accion": "navegar_pedidos",
            })

        if datos.get("prospectos_activos", 0) > 0 and datos.get("pedidos_pendientes", 0) < 2:
            sugerencias.append({
                "tipo": "oportunidad",
                "icono": "💰",
                "texto": f"Tienes {datos['prospectos_activos']} prospectos activos — buen momento para cerrar una venta.",
                "accion": "navegar_autoventas",
            })

        if datos.get("pedidos_vencen_hoy", 0) > 0:
            sugerencias.append({
                "tipo": "urgente",
                "icono": "🔴",
                "texto": f"URGENTE: {datos['pedidos_vencen_hoy']} pedido(s) con entrega HOY.",
                "accion": "navegar_pedidos",
            })

    except Exception as e:
        _log(f"sugerencias_negocio: {e}", "WARN")

    return sugerencias


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 5: AUTO_SALUD (health self-check)
# ═══════════════════════════════════════════════════════════════════════════════

_MODULOS_CRITICOS = [
    ("groq",         "groq"),
    ("fastapi",      "fastapi"),
    ("jinja2",       "jinja2"),
    ("dotenv",       "dotenv"),
    ("supabase",     "supabase"),
]

_MODULOS_OPCIONALES = [
    ("edge_tts",     "Edge TTS"),
    ("pygame",       "pygame"),
    ("PIL",          "Pillow"),
    ("reportlab",    "reportlab"),
    ("httpx",        "httpx"),
]

def _auto_salud() -> dict:
    """
    Verifica modulos criticos. Si falta algo, intenta auto-instalar.
    """
    import importlib
    import subprocess
    import sys

    resultado = {"criticos_ok": [], "criticos_fail": [], "reparados": [], "opcionales_ok": [], "opcionales_fail": []}

    for mod, nombre in _MODULOS_CRITICOS:
        try:
            importlib.import_module(mod)
            resultado["criticos_ok"].append(nombre)
        except ImportError:
            resultado["criticos_fail"].append(nombre)
            # Intentar instalar
            try:
                _log(f"Auto-instalando modulo critico: {nombre}", "WARN")
                subprocess.check_call([sys.executable, "-m", "pip", "install", nombre, "-q"],
                                      timeout=60)
                resultado["reparados"].append(nombre)
                _log(f"Modulo {nombre} instalado OK")
            except Exception as e:
                _log(f"No se pudo instalar {nombre}: {e}", "ERROR")

    for mod, nombre in _MODULOS_OPCIONALES:
        try:
            importlib.import_module(mod)
            resultado["opcionales_ok"].append(nombre)
        except ImportError:
            resultado["opcionales_fail"].append(nombre)

    if resultado["reparados"]:
        _registrar_actividad("auto_salud", f"Reparados: {', '.join(resultado['reparados'])}")

    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 6: INTEL_MERCADO (scraping basico de precios ML)
# ═══════════════════════════════════════════════════════════════════════════════

def _intel_mercado() -> dict:
    """
    Busca precios de competencia en MercadoLibre para los productos ATF/CanbusFix.
    Guarda en CONFIG/intel_mercado.json.
    Solo corre una vez por dia.
    """
    INTEL_PATH = CONFIG_DIR / "intel_mercado.json"
    intel = _load_json(INTEL_PATH, {"items": [], "ultimo_scan": None})

    # Solo escanear si hace mas de 23h
    ult = intel.get("ultimo_scan")
    if ult:
        try:
            dt_ult = datetime.datetime.fromisoformat(ult)
            if (datetime.datetime.now() - dt_ult).total_seconds() < 82800:
                return {"skip": True, "razon": "scan reciente"}
        except Exception:
            pass

    try:
        import httpx
        busquedas = [
            ("retrofit faros guadalajara", "atf"),
            ("bi-led proyector faro", "atf"),
            ("aozoom lens", "canbusfix"),
        ]
        resultados = []
        for query, categoria in busquedas:
            url = f"https://api.mercadolibre.com/sites/MLM/search?q={query.replace(' ','+')}&limit=5"
            resp = httpx.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("results", [])
                for item in items[:3]:
                    resultados.append({
                        "query": query,
                        "categoria": categoria,
                        "titulo": item.get("title", ""),
                        "precio": item.get("price", 0),
                        "vendedor": item.get("seller", {}).get("nickname", ""),
                        "link": item.get("permalink", ""),
                    })

        intel["items"] = resultados
        intel["ultimo_scan"] = _ts()
        intel["total"] = len(resultados)
        _save_json(INTEL_PATH, intel)

        _log(f"Intel mercado: {len(resultados)} precios de competencia escaneados")
        _registrar_actividad("intel_mercado", f"{len(resultados)} precios escaneados")
        return {"items": len(resultados), "ok": True}

    except Exception as e:
        _log(f"intel_mercado error: {e}", "WARN")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# CICLO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

_autonomo_activo = False
_autonomo_thread: Optional[threading.Thread] = None


def _ciclo_autonomo():
    """Loop principal. Corre cada 30min de dia, cada 2h de noche."""
    global _autonomo_activo
    _log("Ciclo autonomo iniciado.")

    while _autonomo_activo:
        hora = datetime.datetime.now().hour
        es_noche = hora < 7 or hora >= 23

        try:
            state = _load_state()
            if not state.get("activo", True):
                time.sleep(300)
                continue

            _log(f"Iniciando ciclo autonomo #{state.get('ciclos_ejecutados', 0) + 1}")

            # --- Auto-ventas (siempre) ---
            av_res = _auto_ventas()
            seg_total = len(av_res.get("seguimientos", [])) + len(av_res.get("reactivaciones", []))
            if seg_total:
                _log(f"Auto-ventas: {seg_total} sugerencias generadas")

            # --- Auto-correcciones (siempre) ---
            corr = _procesar_correcciones_pendientes()

            # --- Auto-aprendizaje (de dia) ---
            if not es_noche:
                apren = _auto_aprendizaje()
                if apren.get("aprendizajes"):
                    _log(f"Auto-aprendizaje: {apren['aprendizajes']} nuevos aprendizajes")

            # --- Sugerencias de negocio (cada 2 ciclos durante el dia) ---
            if not es_noche:
                sug = _auto_sugerencias_negocio()
                if sug:
                    sugerencias = _load_json(SUGERENCIAS, {"items": []})
                    # Reemplazar sugerencias de negocio (no acumular)
                    sugerencias["items"] = [i for i in sugerencias.get("items", []) if i.get("tipo") not in ("alerta", "oportunidad", "urgente")]
                    for s in sug:
                        s["ts"] = _ts()
                        sugerencias["items"].append(s)
                    sugerencias["actualizado"] = _ts()
                    _save_json(SUGERENCIAS, sugerencias)

            # --- Auto-salud (una vez al dia, de noche) ---
            if es_noche and hora in (1, 2):
                salud = _auto_salud()
                if salud.get("reparados"):
                    _log(f"Auto-salud: reparados {salud['reparados']}")

            # --- Intel mercado (de dia, 10am) ---
            if hora == 10:
                _intel_mercado()

            # --- Ciclo de sueno con nexus_dream (solo si es medianoche) ---
            if hora == 0:
                try:
                    from nexus_dream import sonar
                    sonar()
                    _log("Ciclo de sueno ejecutado via nexus_dream.sonar()")
                except Exception as e:
                    _log(f"Dream cycle error: {e}", "WARN")

            # Actualizar estado
            state["ultimo_ciclo"]       = _ts()
            state["ciclos_ejecutados"]  = state.get("ciclos_ejecutados", 0) + 1
            _save_state(state)

        except Exception as e:
            _log(f"Error en ciclo: {e}", "ERROR")

        # Esperar 30min de dia, 2h de noche
        intervalo = 7200 if es_noche else 1800
        _log(f"Proximo ciclo en {intervalo//60} min.")
        time.sleep(intervalo)


def iniciar(forzar: bool = False):
    """Inicia el loop autonomo en thread daemon."""
    global _autonomo_activo, _autonomo_thread
    if _autonomo_activo and not forzar:
        return {"ok": True, "msg": "Ya activo"}
    _autonomo_activo = True
    _autonomo_thread = threading.Thread(target=_ciclo_autonomo, daemon=True, name="nexus-autonomo")
    _autonomo_thread.start()
    _log("Thread autonomo iniciado.")
    return {"ok": True, "msg": "Autonomo iniciado"}


def detener():
    global _autonomo_activo
    _autonomo_activo = False
    _log("Thread autonomo detenido.")
    return {"ok": True, "msg": "Autonomo detenido"}


def estado() -> dict:
    """Retorna estado completo del sistema autonomo."""
    state     = _load_state()
    sug       = _load_json(SUGERENCIAS, {"items": []})
    corr      = _load_json(CORRECCIONES, {"items": [], "total": 0})
    mem       = _load_json(MEMORIA_PATH, {})
    convs     = _load_json(CONVERSACIONES, {"interacciones": []})

    return {
        "activo":                 _autonomo_activo,
        "ultimo_ciclo":           state.get("ultimo_ciclo"),
        "ciclos_ejecutados":      state.get("ciclos_ejecutados", 0),
        "sugerencias_pendientes": len([s for s in sug.get("items", []) if not s.get("atendida")]),
        "correcciones_total":     corr.get("total", 0),
        "aprendizajes_total":     len(mem.get("aprendizajes", [])),
        "conversaciones_total":   len(convs.get("interacciones", [])),
        "log_reciente":           state.get("log_actividad", [])[-5:],
        "patrones_detectados":    state.get("patrones_detectados", 0),
    }


def sugerencias(solo_pendientes: bool = True) -> list:
    """Retorna sugerencias generadas por el sistema autonomo."""
    sug = _load_json(SUGERENCIAS, {"items": []})
    items = sug.get("items", [])
    if solo_pendientes:
        items = [s for s in items if not s.get("atendida")]
    return sorted(items, key=lambda x: x.get("ts", ""), reverse=True)[:20]


def marcar_atendida(ts_o_pid: str) -> dict:
    """Marca una sugerencia como atendida."""
    sug = _load_json(SUGERENCIAS, {"items": []})
    for item in sug.get("items", []):
        if item.get("ts") == ts_o_pid or item.get("pid") == ts_o_pid:
            item["atendida"] = True
            item["atendida_ts"] = _ts()
    _save_json(SUGERENCIAS, sug)
    return {"ok": True}


def correcciones_recientes(n: int = 10) -> list:
    """Retorna las ultimas N correcciones detectadas."""
    corr = _load_json(CORRECCIONES, {"items": []})
    return corr.get("items", [])[-n:]


def ejecutar_ciclo_ahora() -> dict:
    """Ejecuta un ciclo completo de forma sincrona (para pruebas o llamadas manuales)."""
    _log("Ciclo manual iniciado")
    av  = _auto_ventas()
    cor = _procesar_correcciones_pendientes()
    apr = _auto_aprendizaje()
    sug = _auto_sugerencias_negocio()
    sal = _auto_salud()

    state = _load_state()
    state["ultimo_ciclo"]      = _ts()
    state["ciclos_ejecutados"] = state.get("ciclos_ejecutados", 0) + 1
    _save_state(state)

    return {
        "ok": True,
        "seguimientos":  len(av.get("seguimientos", [])),
        "reactivaciones": len(av.get("reactivaciones", [])),
        "correcciones":  cor,
        "aprendizajes":  apr.get("aprendizajes", 0),
        "sugerencias":   len(sug),
        "salud_reparada": sal.get("reparados", []),
    }

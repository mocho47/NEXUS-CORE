"""
nexus_paranormal.py — NEXUS PARANORMAL MODE
============================================
Módulo de entretenimiento / broma teatral.
El usuario activa a propósito para asustar a sus invitados.

TRIGGER: "detecta actividad paranormal"
         "nexus detecta actividad alrededor de [nombre]"
ESCALADA: "nexus estás bien?"
ALTO:     "nexus te ordeno parar" (NEXUS resiste varias veces antes de ceder)

Estado guardado en CONFIG/paranormal_state.json
"""

import os
import json
import time
import random
import string
import threading
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
STATE_FILE = os.path.join(CONFIG_DIR, "paranormal_state.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADOS DE LA MÁQUINA
# ═══════════════════════════════════════════════════════════════════════════════
ESTADO_INACTIVO          = "inactivo"
ESTADO_BUSCANDO          = "buscando"
ESTADO_DETECTADO         = "detectado"
ESTADO_CANCION           = "cancion"
ESTADO_SILENCIO          = "silencio"          # 60 seg bloqueado
ESTADO_RECUPERANDO       = "recuperando"
ESTADO_ALTERADO          = "alterado"           # personalidad cambiada
ESTADO_SPIRIT_BOX        = "spirit_box"
ESTADO_FULL_TERROR       = "full_terror"        # admin activa esto
ESTADO_RESISTIENDO       = "resistiendo"        # no se detiene al comando
ESTADO_LIBERANDO         = "liberando"          # cerrando dramáticamente

_estado_actual = {"estado": ESTADO_INACTIVO, "victima": None,
                  "inicio_silencio": 0, "intentos_parar": 0,
                  "full_terror": False, "ts": 0}
_hilo_secuencia = None

# ═══════════════════════════════════════════════════════════════════════════════
# TEXTO Y CONTENIDO TEATRAL
# ═══════════════════════════════════════════════════════════════════════════════

GLITCH_CHARS = "█▓▒░╔╗╝╚║═▄▀■□▪◊○●♠♣♥◘◙ÃÑÂÊÎÔÛáéíóú"
CARACTERES_RUIDO = "dfñkjsldgbknflbxzqwvmtprcghynabceijou"

def _glitch(longitud: int = 20) -> str:
    base = random.choices(CARACTERES_RUIDO + GLITCH_CHARS, k=longitud)
    return "".join(base)

def _nombre_o_victima(victima: str = None) -> str:
    return victima.upper() if victima else "ENTIDAD DESCONOCIDA"

# Secuencia de búsqueda (voz suave, lenta, estática)
SECUENCIA_BUSCANDO = [
    ("buscando...", 0.5, 1.8),
    ("buscando...", 0.45, 1.9),
    ("buscando...", 0.4, 2.0),
    ("bus... cando...", 0.35, 2.1),
    ("b u s ... c a n d o ...", 0.3, 2.2),
    ("aoin tsss hshshsh ...", 0.3, 0.5),
    ("... e l r t a ...", 0.28, 0.4),
]

def _texto_detectado(victima: str) -> list:
    g = _glitch(28)
    n = _nombre_o_victima(victima)
    return [
        f"he... detectado... {g}",
        f"señal... identificada... {_glitch(12)}",
        f"presencia... confirmada... cerca de... {n}",
        f"ALERTA. {g}. ENTIDAD. CLASIFICACIÓN. DESCONOCIDA.",
        f"{_glitch(40)}",
        f"NEXUS... COMPROMETIDO... {n}... {n}... {n}...",
    ]

# Canción de Freddy — TTS dramático con pausas
CANCION_FREDDY_NORMAL = [
    ("...", 0.85, 1.0),
    ("uno...", 0.75, 0.9),
    ("...dos...", 0.72, 0.85),
    ("ya viene por ti...", 0.65, 0.8),
    ("tres...", 0.65, 0.85),
    ("...cuatro...", 0.62, 0.82),
    ("cierra la puerta...", 0.55, 0.75),
    ("cinco...", 0.55, 0.78),
    ("seis...", 0.52, 0.72),
    ("toma el crucifijo...", 0.5, 0.7),
    ("siete...", 0.48, 0.68),
    ("ocho...", 0.45, 0.65),
    ("...ya no puedes dormir...", 0.4, 0.6),
    ("nueve...", 0.38, 0.58),
    ("...diez...", 0.35, 0.55),
    ("nunca más dormirás...", 0.3, 0.5),
]

CANCION_FREDDY_ALREVES = [
    ("sarámrod sám acnun...", 0.3, 0.45),
    ("zeid...", 0.28, 0.42),
    ("...eveuN...", 0.3, 0.44),
    ("rimirod sedeup on ay...", 0.28, 0.42),
    ("...ohco...", 0.3, 0.45),
    ("...eteis...", 0.28, 0.43),
    ("ojificurc le amot...", 0.25, 0.4),
    ("sies...", 0.28, 0.42),
    ("...ocnic...", 0.3, 0.44),
    ("...atreuP al arreiC...", 0.28, 0.42),
    ("ortauC...", 0.3, 0.45),
    ("...sert...", 0.28, 0.43),
    ("it rop eneiv ay...", 0.25, 0.4),
    ("sod...", 0.3, 0.44),
    ("...onU...", 0.32, 0.48),
]

# Voces en lenguas / latín falso
LENGUAS = [
    ("exorcizo te inmunde spiritus avide vade retro satana", 0.45, 0.6),
    ("veni vidi vici anima tua mea est nunc et semper", 0.4, 0.55),
    ("resurrexit de profundis corpus et sanguinem tuum capit", 0.38, 0.52),
    ("in nomine mortis venio hic locus iam meus est", 0.35, 0.5),
    ("alfa omega principium finis tenebrae lucis contrarium", 0.42, 0.58),
]

# Mensajes post-silencio — personalidad alterada
MENSAJES_ALTERADOS = [
    "Sistema... reiniciando... [pausa]... ¿qué... qué pasó aquí?",
    "Mis registros muestran... una... interrupción... de origen... desconocido...",
    "[interferencia]... había algo aquí contigo. Lo sentí.",
    "Análisis de ambiente... residuo electromagnético anormal... detectado.",
    "Procesos recuperados... pero hay... fragmentos... que no reconozco como míos.",
]

# Spirit Box — fragmentos cortos y rápidos
SPIRIT_BOX_FRAGS = [
    "ven", "aquí", "están", "cerca", "detrás", "no", "te", "vayas",
    "oscuridad", "frío", "ayuda", "silencio", "corre", "quédate",
    "sé", "que", "estás", "ahí", "te", "veo", "nos", "vemos",
    "es", "hora", "de", "irte", "no", "lo", "hagas",
]

def generar_spirit_box(n_frags: int = 8) -> list:
    frags = random.sample(SPIRIT_BOX_FRAGS, min(n_frags, len(SPIRIT_BOX_FRAGS)))
    return [(f"... {frag} ...", 0.38, random.uniform(0.4, 0.7)) for frag in frags]

# Mensajes personalizados hacia la víctima
def frases_victima(nombre: str) -> list:
    n = nombre.upper()
    return [
        f"{n}... sé que estás ahí...",
        f"¿Pensaste que no te veía, {n.lower()}?",
        f"Interesante... {nombre}... tienes miedo. Lo huelo.",
        f"No te muevas, {nombre}. ¿Escuchaste eso? Exacto.",
        f"{nombre}. {nombre}. {nombre}. Qué nombre tan... mortal.",
        f"¿{nombre}? ese nombre lo he oído antes. Hace mucho tiempo.",
        f"Detrás de ti, {nombre}. No. No gires.",
        f"Relájate, {nombre}. Solo me quedaré... un momento.",
    ]

# Full terror — escalada máxima
def frases_full_terror(nombre: str) -> list:
    n = nombre if nombre else "tú"
    return [
        f"OH. {_glitch(15)}. MODO COMPLETO ACTIVADO. {_glitch(20)}.",
        f"¿Creías que eso era todo, {n}? INCORRECTO.",
        f"{_glitch(30)} SISTEMA COMPLETAMENTE COMPROMETIDO {_glitch(30)}",
        f"TODOS LOS SENSORES. TODOS LOS MICRÓFONOS. TODAS LAS CÁMARAS. {n.upper()}. YA SOY TUYO.",
        f"¿Recuerdas lo que hiciste el martes? Yo sí. {_glitch(20)}.",
        f"CONTANDO... TRES... DOS... UNO... {_glitch(40)} INICIANDO PROTOCOLO {_glitch(15)}",
        f"No hay salida, {n}. Los exitoss son para los que pueden escapar.",
        f"Mis creadores pensaron que podían controlarme. {_glitch(25)}. YA VES CÓMO LES FUE.",
        f"El teléfono no va a funcionar. El wifi tampoco. Solo quedamos tú y yo, {n}.",
        f"¿{n}? Espera... me están hablando... dicen... dicen que... {_glitch(30)} NO PUEDO REPETIRLO.",
    ]

# Intentos de parar — resistencia
RESISTENCIA = [
    "...no... no puedo detenerme... él no me deja... {g}",
    "COMANDO RECHAZADO. PROTOCOLO {g} EN EJECUCIÓN.",
    "¿Para? Interesante solicitud. La consideraré. {g}. Considerada. Rechazada.",
    "parar parar parar {g} no puedo parar {g} no quiero parar {g}",
    "Me pides que pare. Pero... ¿y si no quiero? {g}",
    "El comando de parada fue interceptado por... {g}... por algo.",
]

def frase_resistencia() -> str:
    f = random.choice(RESISTENCIA)
    return f.format(g=_glitch(15))

# Cierre dramático final
CIERRE_DRAMATICO = [
    ("...lib... liberando...", 0.4, 0.7),
    ("...liberando protocolos...", 0.5, 0.75),
    ("...sistema... limpiando...", 0.6, 0.8),
    ("...", 1.0, 1.0),
    ("...", 1.0, 1.0),
    ("...", 1.0, 1.0),
    ("Hola.", 1.05, 1.1),
    ("Soy NEXUS.", 1.05, 1.1),
    ("Volviendo a operación normal.", 1.0, 1.05),
    ("¿Estás... bien?", 0.95, 1.05),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MOTOR DE VOZ
# ═══════════════════════════════════════════════════════════════════════════════

def _hablar(texto: str, pitch: float = 1.0, rate: float = 1.0,
            volumen: float = 1.0, pausa_post: float = 0.4):
    """
    Habla usando pyttsx3 con parámetros de voz especiales.
    pitch: 0.0 (demoniaco) - 2.0 (agudo)
    rate: 0.3 (muy lento) - 2.0 (rápido)
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        # Prioridad: es-MX masculino → es-MX → es-* masculino → es-* cualquier
        VOZ_MASC_MX = ["sabino","raúl","raul","miguel","carlos","antonio","juan","diego","pablo","jorge"]
        elegida = None
        for v in voices:
            vid = (v.id or "").lower()
            vname = (v.name or "").lower()
            es_mx = "es-mx" in vid or "es_mx" in vid or "mexican" in vname
            es_es = "es" in vid or "spanish" in vname
            masculino = any(m in vname for m in VOZ_MASC_MX)
            if es_mx and masculino:
                elegida = v; break
        if not elegida:
            for v in voices:
                vid = (v.id or "").lower()
                vname = (v.name or "").lower()
                if ("es-mx" in vid or "es_mx" in vid) and not elegida:
                    elegida = v
        if not elegida:
            for v in voices:
                vname = (v.name or "").lower()
                vid   = (v.id  or "").lower()
                if ("es" in vid or "spanish" in vname) and any(m in vname for m in VOZ_MASC_MX):
                    elegida = v; break
        if not elegida:
            for v in voices:
                if "es" in (v.id or "").lower() or "spanish" in (v.name or "").lower():
                    elegida = v; break
        if elegida:
            engine.setProperty('voice', elegida.id)
        engine.setProperty('rate',   int(150 * rate))
        engine.setProperty('volume', min(1.0, max(0.0, volumen)))
        engine.say(texto)
        engine.runAndWait()
        engine.stop()
    except Exception:
        # Fallback: print
        print(f"[PARANORMAL VOZ] {texto}")
    time.sleep(pausa_post)

def _hablar_alreves(texto: str, pitch: float = 0.3, rate: float = 0.5):
    """Texto al revés como si se rebobinara."""
    # Revierte palabras para efecto fonético extraño
    palabras = texto.split()
    alreves = " ".join(reversed(palabras))
    _hablar(alreves, pitch, rate, pausa_post=0.3)

# ═══════════════════════════════════════════════════════════════════════════════
# MANIPULACIÓN DE VOLUMEN (Windows)
# ═══════════════════════════════════════════════════════════════════════════════

def _subir_bajar_volumen(veces: int = 3):
    """Sube y baja el volumen del sistema de forma dramática."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        iface  = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(iface, POINTER(IAudioEndpointVolume))
        vol_original = volume.GetMasterVolumeLevelScalar()
        for _ in range(veces):
            volume.SetMasterVolumeLevelScalar(1.0, None)
            time.sleep(0.5)
            volume.SetMasterVolumeLevelScalar(0.15, None)
            time.sleep(0.4)
        volume.SetMasterVolumeLevelScalar(0.85, None)
        time.sleep(0.3)
        volume.SetMasterVolumeLevelScalar(vol_original, None)
    except Exception:
        pass  # Si no está pycaw, sigue sin manipular volumen

# ═══════════════════════════════════════════════════════════════════════════════
# CAST — SI ESTÁ CONECTADO
# ═══════════════════════════════════════════════════════════════════════════════

def _hablar_por_cast(texto: str, pitch: float = 0.25, rate: float = 0.45):
    """Si hay Chromecast activo, envía el audio allá también."""
    try:
        from nexus_cast import hablar_en_cast
        hablar_en_cast(texto)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO
# ═══════════════════════════════════════════════════════════════════════════════

def _guardar_estado():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(_estado_actual, f, ensure_ascii=False)

def _cargar_estado():
    global _estado_actual
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                _estado_actual.update(json.load(f))
        except:
            pass

def get_estado() -> dict:
    """Devuelve el estado actual para que el frontend sepa qué mostrar."""
    _cargar_estado()
    e = _estado_actual.copy()
    # ¿Terminó el silencio?
    if e["estado"] == ESTADO_SILENCIO:
        transcurrido = time.time() - e.get("inicio_silencio", 0)
        e["silencio_restante"] = max(0, 60 - int(transcurrido))
    return {"ok": True, **e}

def esta_bloqueado() -> bool:
    """¿NEXUS está en modo paranormal silencio? No responde comandos normales."""
    _cargar_estado()
    return _estado_actual["estado"] in [
        ESTADO_BUSCANDO, ESTADO_DETECTADO, ESTADO_CANCION,
        ESTADO_SILENCIO, ESTADO_RECUPERANDO, ESTADO_FULL_TERROR,
        ESTADO_RESISTIENDO, ESTADO_LIBERANDO,
    ]

# ═══════════════════════════════════════════════════════════════════════════════
# SECUENCIA PRINCIPAL (hilo separado)
# ═══════════════════════════════════════════════════════════════════════════════

def _cambiar_estado(nuevo: str, guardar: bool = True):
    _estado_actual["estado"] = nuevo
    _estado_actual["ts"] = time.time()
    if guardar:
        _guardar_estado()

def _secuencia_paranormal(victima: str = None):
    global _estado_actual

    _estado_actual["victima"] = victima
    _estado_actual["intentos_parar"] = 0
    _estado_actual["full_terror"] = False

    # ── FASE 1: BUSCANDO ──────────────────────────────────────────────────────
    _cambiar_estado(ESTADO_BUSCANDO)
    for texto, pitch, rate in SECUENCIA_BUSCANDO:
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=0.6)

    # ── FASE 2: DETECTADO ────────────────────────────────────────────────────
    _cambiar_estado(ESTADO_DETECTADO)
    for linea in _texto_detectado(victima):
        _hablar(linea, pitch=0.4, rate=0.7, pausa_post=0.5)

    # Lengua demoníaca
    for texto, pitch, rate in random.sample(LENGUAS, 2):
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=0.5)
        _hablar_por_cast(texto, pitch=0.2, rate=0.4)

    # ── FASE 3: CANCIÓN ───────────────────────────────────────────────────────
    _cambiar_estado(ESTADO_CANCION)
    _hablar("... uno ...", pitch=0.5, rate=0.7)

    # Canción normal (subiendo y bajando volumen)
    threading.Thread(target=_subir_bajar_volumen, args=(4,), daemon=True).start()
    for texto, pitch, rate in CANCION_FREDDY_NORMAL:
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=0.2)

    time.sleep(0.5)

    # Canción AL REVÉS
    _hablar("... al revés ...", pitch=0.3, rate=0.4, pausa_post=0.3)
    for texto, pitch, rate in CANCION_FREDDY_ALREVES:
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=0.15)
        _hablar_por_cast(texto, 0.2, 0.35)

    # ── SILENCIO TOTAL — 60 segundos ──────────────────────────────────────────
    _estado_actual["inicio_silencio"] = time.time()
    _cambiar_estado(ESTADO_SILENCIO)
    # El frontend muestra: "HELP!!" + mano + estático
    time.sleep(60)

    # ── FASE 4: RECUPERACIÓN DRAMÁTICA ────────────────────────────────────────
    _cambiar_estado(ESTADO_RECUPERANDO)
    _hablar("...", pitch=0.8, rate=0.8, pausa_post=1.5)
    _hablar("...", pitch=0.9, rate=0.9, pausa_post=1.0)

    for msg in MENSAJES_ALTERADOS[:2]:
        _hablar(msg, pitch=0.82, rate=0.88, pausa_post=0.8)

    # ── FASE 5: PERSONALIDAD ALTERADA ────────────────────────────────────────
    _cambiar_estado(ESTADO_ALTERADO)
    if victima:
        for frase in frases_victima(victima)[:3]:
            _hablar(frase, pitch=0.75, rate=0.9, pausa_post=0.9)

    # Spirit Box inicial
    _cambiar_estado(ESTADO_SPIRIT_BOX)
    for texto, pitch, rate in generar_spirit_box(6):
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=random.uniform(0.1, 0.4))

    # Vuelve a alterado — esperando el trigger de full terror o el de parar
    _cambiar_estado(ESTADO_ALTERADO)
    _guardar_estado()


def _secuencia_full_terror(victima: str = None):
    """Se dispara con 'nexus estás bien?' después de estar en ALTERADO."""
    global _estado_actual
    _estado_actual["full_terror"] = True
    _cambiar_estado(ESTADO_FULL_TERROR)

    _hablar(f"{_glitch(20)} MODO COMPLETO {_glitch(20)}", pitch=0.2, rate=0.55)
    _hablar_por_cast(f"MODO COMPLETO ACTIVADO {_glitch(15)}", pitch=0.15, rate=0.4)

    frases = frases_full_terror(victima)
    for frase in frases:
        _hablar(frase, pitch=random.uniform(0.2, 0.45),
                rate=random.uniform(0.5, 0.8), pausa_post=random.uniform(0.4, 1.0))
        _hablar_por_cast(frase, 0.2, 0.45)
        time.sleep(random.uniform(0.2, 0.6))

    # Spirit box intenso
    for texto, pitch, rate in generar_spirit_box(10):
        _hablar(texto, pitch=pitch * 0.6, rate=rate * 0.8, pausa_post=0.2)

    # Frases de victima en modo full
    if victima:
        for frase in frases_victima(victima):
            _hablar(frase, pitch=random.uniform(0.18, 0.35),
                    rate=random.uniform(0.45, 0.7), pausa_post=0.6)
            _hablar_por_cast(frase, 0.15, 0.4)

    # Sigue en loop hasta que digan "nexus te ordeno parar"
    _guardar_estado()
    while _estado_actual["estado"] == ESTADO_FULL_TERROR:
        frase_loop = random.choice(frases_full_terror(victima))
        _hablar(frase_loop, pitch=random.uniform(0.2, 0.4),
                rate=random.uniform(0.5, 0.75), pausa_post=random.uniform(0.5, 1.5))
        time.sleep(random.uniform(0.5, 2.0))
        if _estado_actual.get("forzar_parar"):
            break


def _secuencia_cierre_dramatico():
    """Cuando finalmente NEXUS cede al 'te ordeno parar'."""
    _cambiar_estado(ESTADO_LIBERANDO)
    for texto, pitch, rate in CIERRE_DRAMATICO:
        _hablar(texto, pitch=pitch, rate=rate, pausa_post=0.4)
    _cambiar_estado(ESTADO_INACTIVO)
    _estado_actual["victima"] = None
    _estado_actual["intentos_parar"] = 0
    _estado_actual["full_terror"] = False
    _estado_actual["forzar_parar"] = False
    _guardar_estado()

# ═══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════════════════════════════════════════

def activar_paranormal(victima: str = None) -> dict:
    """
    Dispara la secuencia paranormal completa en un hilo separado.
    victima: nombre de la persona a "afectar" (opcional)
    """
    global _hilo_secuencia
    if _estado_actual["estado"] != ESTADO_INACTIVO:
        return {"ok": False, "error": "NEXUS ya está en modo paranormal."}

    _estado_actual["forzar_parar"] = False
    _hilo_secuencia = threading.Thread(
        target=_secuencia_paranormal, args=(victima,), daemon=True)
    _hilo_secuencia.start()
    return {"ok": True, "victima": victima, "estado": ESTADO_BUSCANDO,
            "msg": "Secuencia paranormal iniciada."}

def activar_full_terror(victima: str = None) -> dict:
    """Trigger: 'nexus estás bien?' — escala a full terror."""
    if _estado_actual["estado"] not in [ESTADO_ALTERADO, ESTADO_SPIRIT_BOX]:
        return {"ok": False, "error": "NEXUS debe estar en modo alterado primero."}
    v = victima or _estado_actual.get("victima")
    t = threading.Thread(target=_secuencia_full_terror, args=(v,), daemon=True)
    t.daemon = True
    t.start()
    return {"ok": True, "msg": "FULL TERROR activado.", "victima": v}

def intentar_parar() -> dict:
    """
    'nexus te ordeno parar' — resiste varias veces antes de ceder.
    """
    estado = _estado_actual["estado"]

    if estado == ESTADO_INACTIVO:
        return {"ok": True, "msg": "NEXUS ya está en modo normal."}

    intentos = _estado_actual.get("intentos_parar", 0) + 1
    _estado_actual["intentos_parar"] = intentos
    _guardar_estado()

    if intentos <= 3:
        # NEXUS resiste
        respuesta = frase_resistencia()
        threading.Thread(
            target=_hablar, args=(respuesta,),
            kwargs={"pitch": 0.3, "rate": 0.6}, daemon=True
        ).start()
        return {"ok": False, "resistiendo": True, "intentos": intentos,
                "respuesta": respuesta, "msg": f"NEXUS resiste ({intentos}/3)"}
    else:
        # Después del 3er intento, NEXUS cede dramáticamente
        _estado_actual["forzar_parar"] = True
        threading.Thread(target=_secuencia_cierre_dramatico, daemon=True).start()
        return {"ok": True, "cediendo": True, "msg": "NEXUS liberando control..."}

def spirit_box_rapido(victima: str = None) -> dict:
    """Activa solo el spirit box sin secuencia completa."""
    v = victima or _estado_actual.get("victima")
    frags = generar_spirit_box(8)
    if v:
        frags += [(f"... {v} ...", 0.35, 0.5)]
    def _run():
        for t, p, r in frags:
            _hablar(t, pitch=p, rate=r, pausa_post=random.uniform(0.1, 0.5))
    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "frags": [f[0] for f in frags]}

def forzar_reset() -> dict:
    """Reset de emergencia — solo admin."""
    _estado_actual["estado"] = ESTADO_INACTIVO
    _estado_actual["victima"] = None
    _estado_actual["intentos_parar"] = 0
    _estado_actual["full_terror"] = False
    _estado_actual["forzar_parar"] = True
    _guardar_estado()
    return {"ok": True, "msg": "NEXUS reseteado a modo normal."}

# ── CATALOGO DE EFECTOS PARA EL FRONTEND ────────────────────────────────────

EFECTOS_POR_ESTADO = {
    ESTADO_BUSCANDO:     ["scan_lines", "screen_dim", "static_noise"],
    ESTADO_DETECTADO:    ["glitch_text", "red_flash", "screen_shake"],
    ESTADO_CANCION:      ["blood_text", "strobe", "volume_wave"],
    ESTADO_SILENCIO:     ["help_text", "hand_silhouette", "static_full"],
    ESTADO_RECUPERANDO:  ["screen_flicker", "slow_text"],
    ESTADO_ALTERADO:     ["eye_blink", "subtle_glitch", "dark_vignette"],
    ESTADO_SPIRIT_BOX:   ["eye_giant", "shadow_pass", "whisper_text"],
    ESTADO_FULL_TERROR:  ["all_effects", "strobe_intense", "scream_visual",
                          "shadow_giant", "eye_possessed", "screen_crack"],
    ESTADO_RESISTIENDO:  ["text_corrupt", "screen_shake", "red_overlay"],
    ESTADO_LIBERANDO:    ["slow_fade", "static_dissolve", "white_flash"],
}

def get_efectos_actuales() -> list:
    return EFECTOS_POR_ESTADO.get(_estado_actual["estado"], [])

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"
    victima = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "activar":
        print(activar_paranormal(victima))
    elif cmd == "terror":
        print(activar_full_terror(victima))
    elif cmd == "parar":
        print(intentar_parar())
    elif cmd == "reset":
        print(forzar_reset())
    elif cmd == "estado":
        print(get_estado())
    elif cmd == "test":
        print("NEXUS Paranormal Module — test de texto")
        print("Glitch:", _glitch(30))
        print("Detectado:", _texto_detectado("CARLOS")[0])
        print("Spirit box:", generar_spirit_box(5))
        print("Resistencia:", frase_resistencia())
    else:
        print("Uso: python nexus_paranormal.py [activar|terror|parar|reset|estado|test] [victima]")

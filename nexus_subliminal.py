"""
nexus_subliminal.py — Módulo de persuasión ética y audio binaural para NEXUS.

FILOSOFÍA:
  Estos mensajes NO son subliminalidad engañosa. Son comunicación positiva
  basada en psicología del consumidor: beneficio real, confianza genuina,
  urgencia honesta. El propósito es ayudar al emprendedor a comunicar
  mejor su valor, no manipular.

  Los tonos binaurales son frecuencias de audio reales que ayudan al oyente
  a entrar en estados de receptividad, confianza o energía según el contexto.
  Requieren audífonos para el efecto binaural completo.

Categorías (60 mensajes + 10 promo NEXUS):
  DESEO        → Anhelo genuino de adquirir (528Hz - atracción)
  CONFIANZA    → Credibilidad de marca (396Hz - liberación de dudas)
  URGENCIA     → Decisión sin presión (417Hz - motivación)
  ABUNDANCIA   → Valor premium y prosperidad (432Hz - armonía)
  COMUNIDAD    → Pertenencia e identidad (639Hz - conexión)
  TRANSFORMACION → Cambio y versión mejorada (741Hz - soluciones)
  NEXUS_PROMO  → Para demos y material de ventas del mismo NEXUS (528Hz)

Uso de frecuencias binaurales:
  - Stereo WAV generado con Python estándar (sin dependencias externas)
  - Carrier wave: 200Hz base
  - Beat = diferencia entre canal izquierdo y derecho
  - Usar con audífonos para máximo efecto
"""

import os
import math
import wave
import struct
import datetime
import random

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "TALLER", "SUBLIMINAL")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Biblioteca de 60 mensajes persuasivos éticos ─────────────────────────────

BIBLIOTECA = {
    "deseo": {
        "descripcion": "Activa el deseo genuino de adquirir. Ideal para imágenes de producto y reels de presentación.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   207.83,   # beat: 7.83Hz = Resonancia Schumann (atracción natural)
        "nota":         "Frecuencia 528Hz (amor/atracción) con beat 7.83Hz — Resonancia de la Tierra",
        "mensajes": [
            "Esto es exactamente lo que estabas buscando",
            "Imagina cómo se verá esto en tu vida",
            "Mereces tener lo mejor",
            "Este es el momento de hacerlo realidad",
            "Tu instinto te dice que lo necesitas",
            "Cada detalle fue creado pensando en ti",
            "La calidad que soñabas existe aquí",
            "Esto cambia todo lo que conoces",
            "Tu versión mejorada comienza con esta decisión",
            "Es imposible resistirse cuando la calidad habla por sí sola",
        ]
    },
    "confianza": {
        "descripcion": "Refuerza credibilidad y autoridad de marca. Ideal para testimoniales y posts de proceso.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   210.0,    # beat: 10Hz = Alpha, calma y apertura
        "nota":         "Frecuencia 396Hz (liberación de miedos) con beat 10Hz — Onda Alpha de confianza",
        "mensajes": [
            "Aquí no hay errores, solo resultados garantizados",
            "Miles de clientes confiaron. Tú también puedes.",
            "Detrás de cada pieza hay años de experiencia",
            "Tu inversión está completamente protegida",
            "La calidad que ves es la calidad que recibes",
            "Trabajamos con los mejores materiales disponibles",
            "Cada cliente satisfecho es nuestra mejor carta de presentación",
            "No hacemos promesas que no podemos cumplir",
            "Tu tranquilidad es parte del servicio",
            "Aquí el estándar mínimo es la excelencia",
        ]
    },
    "urgencia": {
        "descripcion": "Activa la toma de decisión sin presión agresiva. Ideal para ofertas y lanzamientos.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   220.0,    # beat: 20Hz = Beta, alerta y energía
        "nota":         "Frecuencia 417Hz (cambio/motivación) con beat 20Hz — Onda Beta de acción",
        "mensajes": [
            "Los que actúan hoy, ganan mañana",
            "Cada hora que pasa es una oportunidad que se cierra",
            "La disponibilidad es limitada por razones de calidad",
            "Tu futuro yo te agradecerá haber decidido hoy",
            "Las mejores decisiones se toman cuando la oportunidad está frente a ti",
            "El costo de esperar siempre supera al de actuar",
            "Esta oportunidad fue creada para quienes reconocen su valor",
            "Quien llega primero tiene la ventaja",
            "No hay mejor momento que este instante",
            "Tu próximo paso importa más de lo que imaginas",
        ]
    },
    "abundancia": {
        "descripcion": "Mentalidad de valor y prosperidad. Ideal para contenido premium y presentación de precios.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   207.0,    # beat: 7Hz = Theta, receptividad
        "nota":         "Frecuencia 432Hz (armonía natural) con beat 7Hz — Onda Theta de prosperidad",
        "mensajes": [
            "Invertir en calidad siempre genera más de lo que cuesta",
            "Lo premium no es un gasto, es una declaración de valores",
            "Tu negocio merece las mejores herramientas",
            "La prosperidad está en cada decisión inteligente que tomas",
            "Cuando pagas bien, recibes mejor",
            "El valor real supera siempre al precio",
            "Rodéate de lo que inspira grandeza",
            "La calidad se paga una vez, el arrepentimiento dura para siempre",
            "Los líderes invierten donde otros solo gastan",
            "Tu éxito refleja la calidad de lo que eliges",
        ]
    },
    "comunidad": {
        "descripcion": "Sentido de pertenencia e identidad compartida. Ideal para contenido de comunidad y clientes frecuentes.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   212.0,    # beat: 12Hz = Alpha alto, conexión social
        "nota":         "Frecuencia 639Hz (conexión/relaciones) con beat 12Hz — Onda Alpha de comunidad",
        "mensajes": [
            "Somos más que un proveedor, somos tu equipo",
            "Aquí cada cliente es parte de la familia",
            "Tu éxito es nuestro éxito",
            "Juntos creamos lo que individualmente no es posible",
            "La comunidad que nos rodea es nuestra mayor fortaleza",
            "Tus amigos ya lo tienen. Tú también lo mereces.",
            "Ser parte de este movimiento te distingue",
            "Cuando creces, crecemos contigo",
            "Aquí encuentras aliados, no solo vendedores",
            "La mejor publicidad la hacen quienes nos han vivido",
        ]
    },
    "transformacion": {
        "descripcion": "Cambio de vida y versión mejorada. Ideal para antes/después y casos de éxito.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   206.0,    # beat: 6Hz = Theta, imaginación y cambio
        "nota":         "Frecuencia 741Hz (expresión/soluciones) con beat 6Hz — Onda Theta de transformación",
        "mensajes": [
            "Esto no es un producto, es un punto de inflexión",
            "La persona que serás después de esto ya está esperándote",
            "Cada transformación comienza con una sola decisión",
            "Antes y después no es solo una foto, es un nuevo camino",
            "Lo que ves en otros también es posible para ti",
            "Tu negocio puede verse exactamente como lo imaginas",
            "El cambio que buscas empieza aquí",
            "No te conformes con lo ordinario cuando lo extraordinario existe",
            "Esta es tu señal para dar el siguiente paso",
            "El mejor momento fue ayer. El segundo mejor es ahora.",
        ]
    },
    "nexus_promo": {
        "descripcion": "Mensajes motivacionales para demos y ventas del mismo NEXUS. Transmiten valor del producto.",
        "hz_izquierdo": 200.0,
        "hz_derecho":   207.83,   # 7.83Hz = Schumann, resonancia natural
        "nota":         "Pista motivacional para demos: genera confianza en el sistema NEXUS",
        "mensajes": [
            "NEXUS trabaja mientras tú descansas",
            "Todo lo que necesitas para crecer en un solo lugar",
            "Tu negocio merece tecnología de clase mundial",
            "Con NEXUS, un emprendedor tiene el poder de una corporación",
            "NEXUS no es un gasto, es tu empleado más dedicado",
            "Automatizar no es el futuro, es hoy mismo con NEXUS",
            "El tiempo que libera NEXUS es tiempo para vivir mejor",
            "De la idea al cliente en minutos con NEXUS",
            "Los negocios que usan NEXUS venden más con menos esfuerzo",
            "Tu competencia ya lo está usando. ¿Tú?",
        ]
    }
}


# ── Generación de audio binaural (WAV puro, sin dependencias) ─────────────────

def generar_binaural_wav(
    archivo_salida: str,
    hz_izquierdo: float = 200.0,
    hz_derecho:   float = 207.83,
    duracion_seg: int   = 60,
    amplitud:     float = 0.25,
    sample_rate:  int   = 44100
) -> str:
    """
    Genera un archivo WAV estéreo con tono binaural real.
    El beat percibido = |hz_derecho - hz_izquierdo|.
    Requiere audífonos para el efecto completo.

    Sin dependencias externas — usa solo módulos estándar de Python.
    """
    n_samples = duracion_seg * sample_rate
    amp = int(amplitud * 32767)

    with wave.open(archivo_salida, "w") as wf:
        wf.setnchannels(2)   # Stereo
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(sample_rate)

        # Escribir en bloques para no saturar la memoria
        bloque = 4096
        for inicio in range(0, n_samples, bloque):
            fin   = min(inicio + bloque, n_samples)
            frames = bytearray()
            for i in range(inicio, fin):
                t     = i / sample_rate
                left  = int(math.sin(2 * math.pi * hz_izquierdo * t) * amp)
                right = int(math.sin(2 * math.pi * hz_derecho   * t) * amp)
                frames += struct.pack("<hh", left, right)
            wf.writeframes(bytes(frames))

    return archivo_salida


# ── API pública ───────────────────────────────────────────────────────────────

def get_pistas() -> list:
    """Lista de categorías disponibles con metadata."""
    return [
        {
            "id":             cat,
            "categoria":      cat,
            "descripcion":    data["descripcion"],
            "beat_hz":        round(data["hz_derecho"] - data["hz_izquierdo"], 2),
            "nota":           data["nota"],
            "total_mensajes": len(data["mensajes"])
        }
        for cat, data in BIBLIOTECA.items()
    ]


def generar_pista(categoria: str, cantidad: int = 10) -> dict:
    """
    Devuelve mensajes persuasivos para la categoría indicada.
    No genera audio — solo texto para usar en contenido.
    """
    cat = categoria.lower().strip()
    if cat not in BIBLIOTECA:
        cat = "deseo"
    data = BIBLIOTECA[cat]
    mensajes = data["mensajes"][:cantidad]
    beat = round(data["hz_derecho"] - data["hz_izquierdo"], 2)

    return {
        "ok":          True,
        "categoria":   cat,
        "descripcion": data["descripcion"],
        "beat_hz":     beat,
        "frecuencia_sugerida": f"{data['hz_izquierdo']:.0f}Hz / {data['hz_derecho']:.2f}Hz",
        "nota":        data["nota"],
        "mensajes":    mensajes,
        "instrucciones_uso": [
            f"Tono binaural: {data['hz_izquierdo']:.0f}Hz oído izquierdo, "
            f"{data['hz_derecho']:.2f}Hz oído derecho (beat percibido: {beat}Hz)",
            "Genera el WAV con: nexus_subliminal.generar_audio_categoria('" + cat + "')",
            "Narra los mensajes con pausa de 3s entre cada uno",
            "Volumen narración subliminal: 20-30% del audio total del video",
            "Coloca entre los segundos 5-15 para mayor receptividad",
            "Voz neutra y calmada, sin dramatismo",
            "Estos mensajes son éticos: comunican valor real del producto"
        ],
        "timestamp": datetime.datetime.now().isoformat()
    }


def generar_audio_categoria(
    categoria: str,
    duracion_seg: int = 60
) -> dict:
    """
    Genera el archivo WAV binaural para una categoría.
    Retorna ruta del archivo generado.
    """
    cat = categoria.lower().strip()
    if cat not in BIBLIOTECA:
        cat = "deseo"
    data = BIBLIOTECA[cat]
    beat = round(data["hz_derecho"] - data["hz_izquierdo"], 2)

    ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    nombre = f"binaural_{cat}_{beat}hz_{duracion_seg}s_{ts}.wav"
    ruta   = os.path.join(OUTPUT_DIR, nombre)

    try:
        generar_binaural_wav(
            archivo_salida = ruta,
            hz_izquierdo   = data["hz_izquierdo"],
            hz_derecho     = data["hz_derecho"],
            duracion_seg   = duracion_seg,
            amplitud       = 0.25
        )
        return {
            "ok":         True,
            "archivo":    ruta,
            "categoria":  cat,
            "beat_hz":    beat,
            "duracion":   f"{duracion_seg}s",
            "nota":       data["nota"],
            "instruccion": "Usa audífonos. Mezcla con narración de mensajes a 20-30% de volumen."
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generar_script_video(
    negocio:    str,
    servicio:   str,
    categoria:  str = "deseo",
    duracion_s: int = 30
) -> dict:
    """
    Genera script completo para video con pista subliminal integrada.
    Incluye estructura por segmentos y mensajes persuasivos.
    """
    cat = categoria.lower().strip()
    if cat not in BIBLIOTECA:
        cat = "deseo"
    data    = BIBLIOTECA[cat]
    msgs    = data["mensajes"][:5]
    beat    = round(data["hz_derecho"] - data["hz_izquierdo"], 2)

    script = f"""=== SCRIPT VIDEO: {negocio.upper()} — {servicio.upper()} ===
Categoría subliminal : {cat.upper()}
Tono binaural        : {beat}Hz ({data['nota']})
Duración total       : {duracion_s}s
Plataformas          : Instagram Reels / TikTok / YouTube Shorts
═══════════════════════════════════════════════════════════

[0-3s]  APERTURA VISUAL
  → Imagen/video del trabajo terminado (primer plano impactante)
  → Sin narración — solo tono binaural suave de fondo
  → Texto en pantalla: "{negocio}"

[3-8s]  HOOK — Primera impresión
  SUBLIMINAL (20% volumen): "{msgs[0]}"
  VISUAL: mostrar el resultado final o proceso clave
  TEXTO PANTALLA: nombre del servicio / producto

[8-18s]  DESARROLLO — Proceso o beneficio
  SUBLIMINAL (20% volumen):
    - "{msgs[1]}"
    - "{msgs[2]}"
  VISUAL: proceso de fabricación / cliente usando el producto
  NARRACIÓN PRINCIPAL (si aplica): explica el beneficio clave

[18-25s]  PRUEBA SOCIAL
  SUBLIMINAL (25% volumen): "{msgs[3]}"
  VISUAL: reacción del cliente / testimonio / antes-después

[25-{duracion_s}s]  CALL TO ACTION
  SUBLIMINAL (30% volumen): "{msgs[4]}"
  VISUAL: Logo + contacto
  TEXTO: "Escríbenos hoy — {negocio}"
  NARRACIÓN: "Contáctanos por WhatsApp / Instagram"

═══════════════════════════════════════════════════════════
NOTAS DE PRODUCCIÓN:
• Genera el tono binaural con: nexus_subliminal.generar_audio_categoria('{cat}', {duracion_s})
• Mezcla en tu editor: pista binaural al 15%, narración al 100%
• Los mensajes subliminales se dicen en voz baja, calmada y neutra
• Para máximo efecto binaural el espectador debe usar audífonos
• Formato exportación: MP4 H.264, 1080x1920 para Reels/TikTok
═══════════════════════════════════════════════════════════
"""

    ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    nombre = f"script_{negocio.replace(' ','_')}_{cat}_{ts}.txt"
    ruta   = os.path.join(OUTPUT_DIR, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(script)

    return {
        "ok":          True,
        "script":      script,
        "archivo":     ruta,
        "categoria":   cat,
        "beat_hz":     beat,
        "mensajes":    msgs,
        "duracion":    f"{duracion_s}s"
    }


def pista_aleatoria(excluir: list = None) -> dict:
    """Devuelve mensajes aleatorios de categorías distintas (para variedad)."""
    cats = [c for c in BIBLIOTECA if c != "nexus_promo" and c not in (excluir or [])]
    elegidas = random.sample(cats, min(3, len(cats)))
    resultado = {}
    for cat in elegidas:
        resultado[cat] = random.choice(BIBLIOTECA[cat]["mensajes"])
    return resultado

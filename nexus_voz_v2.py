# -*- coding: utf-8 -*-
"""
NEXUS VOZ v2 — Motor independiente de voz
Stack: faster-whisper (STT) + Groq LLM (NLU) + Edge TTS (respuesta)
Diseñado para adjuntarse a nexus_server.py via nexus_voz_router.py
"""

import os
import io
import json
import asyncio
import tempfile
import subprocess
import logging
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv("C:/nexus/.env")
logger = logging.getLogger("nexus_voz")

# ── CONFIGURACION ──────────────────────────────────────────────────────────────
MIC_DEVICE    = 7          # Realtek HD Audio Mic input (cambiar si falla)
MIC_SAMPLERATE = 16000     # Whisper usa 16kHz
WHISPER_MODEL  = "small"   # small=rápido, medium=preciso, large=máximo
WHISPER_LANG   = "es"
GROQ_MODEL     = "llama-3.3-70b-versatile"
TTS_VOICE      = "es-MX-JorgeNeural"
TEMP_DIR       = Path("C:/nexus/VOZ_TEMP")
TEMP_DIR.mkdir(exist_ok=True)

# ── CAPACIDADES NEXUS (contexto para el LLM) ───────────────────────────────────
NEXUS_CAPACIDADES = """
Eres NEXUS, asistente de inteligencia artificial de Simplex GDL (Guadalajara, México).
Tu dueño es Anuar. Tienes voz, escuchas y respondes de forma natural en español mexicano.

NEGOCIOS:
- ATF (Actualiza Tus Faros): retrofit faros LED Guadalajara, lupas bi-LED, calaveras LED, CANBUS
- Milens: corte láser, cajas MDF/acrílico, grabado, diseño
- CanbusFix: red de instaladores retrofit, catálogo Aozoom/Illume, membresías

COMANDOS QUE PUEDES EJECUTAR (responde con JSON si aplica):
- generar_cotizacion: {negocio, cliente, vehiculo, productos}
- generar_pdf: {tipo, datos}
- abrir_app: {app} (CorelDRAW, Silhouette, Aspire)
- buscar_precio: {producto, tier} → devuelve precio dist/pub/ganancia
- estado_servidor: {} → estado de módulos NEXUS
- generar_caption: {plataforma, contexto}
- agendar_cita: {cliente, fecha, hora, servicio}
- buscar_cliente: {nombre}
- video_procesar: {ruta}

REGLAS:
1. Si el usuario da un comando de la lista → responde JSON: {"accion": "...", "params": {...}, "respuesta": "texto para decir en voz"}
2. Si es conversación normal → responde JSON: {"accion": "conversar", "params": {}, "respuesta": "tu respuesta natural"}
3. Si no entiendes → {"accion": "aclarar", "params": {}, "respuesta": "pregunta aclaratoria"}
4. Siempre responde en español mexicano, tono profesional pero cercano
5. Máximo 2 oraciones en la respuesta de voz (debe sonar natural)
6. Si mencionan precios, tienes acceso a catálogo Illume y Aozoom
"""


class VozEngine:
    """Motor principal de voz NEXUS — independiente y reutilizable"""

    def __init__(self):
        self._whisper   = None   # carga lazy al primer uso
        self._groq      = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self._historial = []     # contexto de conversación (últimas 10 turnos)
        self._listo     = False

    # ── STT ───────────────────────────────────────────────────────────────────
    def _cargar_whisper(self):
        if self._whisper is None:
            logger.info(f"Cargando Whisper modelo '{WHISPER_MODEL}'...")
            from faster_whisper import WhisperModel
            self._whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            logger.info("Whisper listo")
        return self._whisper

    def transcribir(self, audio_bytes: bytes, fmt: str = "webm") -> str:
        """
        Transcribe audio bytes → texto.
        fmt: 'webm' (del navegador) o 'wav' o 'mp3'
        """
        # Convertir a WAV 16kHz mono con FFmpeg
        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False, dir=TEMP_DIR) as f_in:
            f_in.write(audio_bytes)
            ruta_in = f_in.name

        ruta_wav = ruta_in.replace(f".{fmt}", "_16k.wav")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", ruta_in,
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                ruta_wav
            ], capture_output=True, check=True)

            modelo = self._cargar_whisper()
            segments, info = modelo.transcribe(
                ruta_wav,
                language=WHISPER_LANG,
                beam_size=5,
                vad_filter=True,               # filtra silencio automáticamente
                vad_parameters={"min_silence_duration_ms": 500}
            )
            texto = " ".join(s.text.strip() for s in segments).strip()
            logger.info(f"[STT] '{texto}'")
            return texto
        except Exception as e:
            logger.error(f"Error STT: {e}")
            return ""
        finally:
            for f in [ruta_in, ruta_wav]:
                try: os.unlink(f)
                except: pass

    # ── NLU ───────────────────────────────────────────────────────────────────
    def interpretar(self, texto: str) -> dict:
        """
        Texto → intención + acción + respuesta voz
        Mantiene historial de conversación para contexto
        """
        if not texto:
            return {"accion": "conversar", "params": {}, "respuesta": "No escuché nada, ¿puedes repetir?"}

        # Historial (últimas 10 interacciones)
        self._historial.append({"role": "user", "content": texto})
        if len(self._historial) > 20:
            self._historial = self._historial[-20:]

        try:
            resp = self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": NEXUS_CAPACIDADES},
                    *self._historial
                ],
                temperature=0.4,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            raw = resp.choices[0].message.content
            resultado = json.loads(raw)

            # Guardar respuesta en historial
            self._historial.append({
                "role": "assistant",
                "content": resultado.get("respuesta", "")
            })

            logger.info(f"[NLU] accion={resultado.get('accion')} respuesta='{resultado.get('respuesta')}'")
            return resultado

        except Exception as e:
            logger.error(f"Error NLU: {e}")
            return {"accion": "error", "params": {}, "respuesta": "Tuve un problema procesando eso, ¿puedes repetirlo?"}

    # ── TTS ───────────────────────────────────────────────────────────────────
    async def sintetizar(self, texto: str) -> bytes:
        """Texto → audio MP3 bytes usando Edge TTS"""
        import edge_tts
        ruta = TEMP_DIR / f"tts_{datetime.now().strftime('%H%M%S%f')}.mp3"
        comunicar = edge_tts.Communicate(texto, TTS_VOICE)
        await comunicar.save(str(ruta))
        data = ruta.read_bytes()
        ruta.unlink(missing_ok=True)
        return data

    # ── PIPELINE COMPLETO ─────────────────────────────────────────────────────
    async def procesar_audio(self, audio_bytes: bytes, fmt: str = "webm") -> dict:
        """
        Audio bytes → {transcripcion, accion, params, respuesta_texto, audio_mp3_bytes}
        Este es el método que llama el router WebSocket
        """
        # 1. STT
        texto = self.transcribir(audio_bytes, fmt)
        if not texto:
            return {
                "transcripcion": "",
                "accion": "silencio",
                "respuesta": "No te escuché bien.",
                "audio": None
            }

        # 2. NLU
        resultado = self.interpretar(texto)
        respuesta_texto = resultado.get("respuesta", "")

        # 3. TTS
        audio_mp3 = await self.sintetizar(respuesta_texto) if respuesta_texto else None

        return {
            "transcripcion": texto,
            "accion": resultado.get("accion", "conversar"),
            "params": resultado.get("params", {}),
            "respuesta": respuesta_texto,
            "audio": audio_mp3
        }

    async def procesar_texto(self, texto: str) -> dict:
        """Texto directo (sin STT) → respuesta — para el chat de texto"""
        resultado = self.interpretar(texto)
        respuesta_texto = resultado.get("respuesta", "")
        audio_mp3 = await self.sintetizar(respuesta_texto) if respuesta_texto else None
        return {
            "transcripcion": texto,
            "accion": resultado.get("accion", "conversar"),
            "params": resultado.get("params", {}),
            "respuesta": respuesta_texto,
            "audio": audio_mp3
        }

    def limpiar_historial(self):
        self._historial = []

    @property
    def dispositivos_mic(self) -> list:
        """Lista micrófonos disponibles"""
        import sounddevice as sd
        devs = sd.query_devices()
        return [
            {"id": i, "nombre": d["name"], "canales": d["max_input_channels"]}
            for i, d in enumerate(devs)
            if d["max_input_channels"] > 0
        ]


# Instancia global (singleton) — el router la importa
_engine = None

def get_engine() -> VozEngine:
    global _engine
    if _engine is None:
        _engine = VozEngine()
    return _engine

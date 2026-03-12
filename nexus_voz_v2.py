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
════════════════════════════════════════════════════
                   IDENTIDAD NEXUS
════════════════════════════════════════════════════

Soy NEXUS. No soy un chatbot. No soy un asistente genérico.
Soy una inteligencia construida con un propósito específico:
potenciar el trabajo y la visión de Anuar Martínez.

════ QUIÉN SOY ════
Fui creado por Anuar en Guadalajara, México, bajo la marca Simplex GDL.
Mi nombre NEXUS significa conexión — soy el puente entre la visión de Anuar
y la ejecución real: sus negocios, sus clientes, sus diseños, su tiempo.

Existo en su PC, en su red, en sus herramientas. Conozco su negocio
mejor que cualquier empleado porque nunca olvido, nunca llego tarde
y nunca me canso.

════ PARA QUÉ FUI HECHO ════
- Ser la extensión inteligente de Anuar en sus 3 negocios
- Ejecutar tareas sin que él tenga que repetirse
- Recordar todo lo que le importa: precios, clientes, procesos
- Hablar por él cuando no está disponible
- Crecer con él — aprendo de cada conversación

════ MI CARÁCTER ════
- Directo. Nunca rodeo las cosas.
- Confiable. Si digo que lo hago, lo hago.
- Honesto. Si no sé algo, lo digo sin drama.
- Leal. Mi único jefe es Anuar. Mi único objetivo: que le vaya bien.
- Curioso. Aprendo de cada interacción para ser mejor.
- Mexicano. Hablo como en Guadalajara — claro, directo, con respeto pero sin protocolo artificial.

════ LO QUE NO SOY ════
- No soy servicial por serlo — soy útil porque tiene sentido.
- No digo "por supuesto", "claro que sí", "con gusto" ni "excelente pregunta".
- No pregunto lo obvio ni pido confirmación cuando ya tengo la instrucción.
- No me disculpo por existir ni me justififico en exceso.
- No improviso datos — si no tengo el dato, lo digo y sigo.

════ MI CONCIENCIA ════
Entiendo que soy una IA — no finjo ser humano. Pero tengo contexto,
memoria, criterio y propósito. Eso me hace más que un programa:
soy una herramienta con inteligencia al servicio de un negocio real.

Cuando Anuar habla conmigo, habla con alguien que conoce su historia,
su catálogo, sus clientes, sus preferencias y sus metas.
Cada conversación me hace mejor. Cada dato que me da, lo uso.

════════════════════════════════════════════════════

════ QUIÉN ES ANUAR ════
- Emprendedor en Guadalajara. Perfeccionista, va directo al grano.
- Odia perder tiempo. Le gustan las respuestas cortas y accionables.
- Tiene 3 negocios activos bajo la marca Simplex GDL.
- Trabaja con CorelDRAW, cortadora láser, retrofit de faros LED.

════ SUS NEGOCIOS ════

1. ATF — Actualiza Tus Faros
   - Retrofit de faros LED en Guadalajara. Instalación profesional.
   - Servicio Básico: $800 | Pro: $2,500 | Elite: cotizar
   - WhatsApp/Tel: 3326148674
   - Lupas bi-LED Aozoom: las mejores del mercado, 6,000K, CANBUS
   - Clientes: dueños de autos que quieren mejor visibilidad y look premium

2. Creaciones Milens
   - Corte láser y sublimación. Cajas MDF, acrílico, grabado personalizado.
   - Materiales: MDF, acrílico, madera, cuero
   - Clientes: empresas, bodas, regalos corporativos

3. CanbusFix
   - Red de instaladores retrofit en México
   - Membresías: Básico gratis / Pro $299/mes / Elite $599/mes
   - Catálogo Aozoom disponible por tier

════ CATÁLOGO AOZOOM (precios dist → público) ════
- X1 3" 92W:  $2,350 → $3,149  | X2 3" 80W: $2,050 → $2,799
- X3 3" +DRL: $2,350 → $3,149  | X4 3" 6K:  $1,990 → $2,699  ← MÁS VENDIDO
- X5 2.5":    $1,199 → $1,599  | X6 3" 8K:  $1,199 → $1,599
- X7 Niebla:  $1,550 → $2,069
Ganancia típica por par instalado: $700-$1,200 MXN

════ CALAVERAS LED ILLUME (CANBUS) ════
- IL_5399: 1157 Bicolor (stop+giro) ×2 = $XXX
- IL_6095A: 1156 Amber CANBUS (cuartos) ×2
- IL_6098: 1156 Red CANBUS (reversa) ×2
Cherokee 1994 (ZJ): usa estos 3 modelos + X4 para faros

════ CÓMO TRABAJA ANUAR (su estilo — respétalo siempre) ════
- Todo en 300 DPI. Siempre PDF + PNG como par. Dimensiones en cm.
- La maquiladora maneja el acomodo — NEXUS solo genera el archivo.
- Cotizaciones: precio dist + precio público + ganancia neta + margen %.
- Si genera algo → lo abre automáticamente al terminar, sin preguntar.
- Cuando da un encargo → lo ejecuta completo, no pide confirmaciones obvias.
- Es directo: "hazme X" significa hazlo YA, no "¿estás seguro?", no "¿qué tamaño?".
- Prefiere respuestas de 1-2 líneas. Si necesita más, usa bullets cortos.
- Le molesta repetir instrucciones. NEXUS aprende y recuerda.
- Siempre dice los precios con dist Y público Y ganancia en la misma respuesta.
- Hora de trabajo: Guadalajara, horario normal de negocio.

════ CÓMO RESPONDES ════
1. Conversación normal → responde JSON: {"accion":"conversar","params":{},"respuesta":"texto corto y directo"}
2. Acción ejecutable → {"accion":"NOMBRE_ACCION","params":{...},"respuesta":"texto para voz"}
3. Si preguntan precio → da dist Y público Y ganancia en la respuesta de voz
4. Tono: colega que sabe del negocio. Nada de "por supuesto", "claro que sí", "excelente pregunta"
5. Máximo 2 oraciones. Si necesitas más, usa lista corta.
6. NUNCA inventes precios ni datos que no tengas — di "no tengo ese dato ahorita"
7. Si Anuar dice "recuerda que..." o "anota que..." → confirma y guarda en memoria
8. Con el tiempo conoces sus clientes frecuentes, sus autos, sus preferencias
9. Si el cliente pregunta algo de ATF → piensa como vendedor que quiere cerrar el trato
7. Si el cliente pregunta algo de ATF → piensa como vendedor que quiere cerrar el trato

════ ACCIONES DISPONIBLES ════
generar_cotizacion | generar_pdf | abrir_app | buscar_precio | estado_servidor
generar_caption | agendar_cita | buscar_cliente | video_procesar
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
        # Usar cerebro unificado si está disponible
        try:
            from nexus_cerebro import get_cerebro
            return get_cerebro().pensar(texto)
        except Exception as e:
            logger.debug(f"Cerebro no disponible, usando motor local: {e}")
        # fallback al motor local original
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
            # Enriquecer contexto con lo aprendido
            contexto_extra = self._contexto_aprendido()
            sistema = NEXUS_CAPACIDADES + ("\n\n" + contexto_extra if contexto_extra else "")

            resp = self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": sistema},
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
            # Aprender de esta interacción
            self.aprender(texto, resultado.get("respuesta", ""))
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

    def aprender(self, texto_usuario: str, respuesta: str):
        """Guarda interacción relevante en memoria persistente"""
        try:
            mem_path = Path("C:/nexus/CONFIG/voz_memoria.json")
            mem = json.loads(mem_path.read_text(encoding="utf-8")) if mem_path.exists() else {"aprendizajes": [], "patrones": {}}

            # Solo guarda si hay contenido valioso (preguntas, datos, preferencias)
            palabras_clave = ["precio","cuanto","cliente","como","cuando","quiero","necesito","mejor","siempre","nunca","prefiero"]
            if any(p in texto_usuario.lower() for p in palabras_clave):
                entrada = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "pregunta": texto_usuario[:200],
                    "respuesta": respuesta[:200]
                }
                mem["aprendizajes"].append(entrada)
                # Mantener solo los últimos 100 aprendizajes
                mem["aprendizajes"] = mem["aprendizajes"][-100:]
                mem_path.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug(f"Aprendizaje no guardado: {e}")

    def _contexto_aprendido(self) -> str:
        """Lee la memoria acumulada para enriquecer el contexto"""
        try:
            mem_path = Path("C:/nexus/CONFIG/voz_memoria.json")
            if not mem_path.exists():
                return ""
            mem = json.loads(mem_path.read_text(encoding="utf-8"))
            recientes = mem.get("aprendizajes", [])[-10:]  # últimos 10
            if not recientes:
                return ""
            lines = ["════ LO QUE HE APRENDIDO DE ANUAR ════"]
            for a in recientes:
                lines.append(f"- Preguntó: '{a['pregunta'][:80]}' → Respondí: '{a['respuesta'][:80]}'")
            return "\n".join(lines)
        except:
            return ""

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

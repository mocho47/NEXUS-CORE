"""
NEXUS — Módulo de Escucha de Voz
Wake word: "nexus" → responde "Mande" → escucha comando → procesa con Groq
Funciona en background, expone estado via cola de mensajes
"""

import os
import threading
import queue
import time
import json
from datetime import datetime

try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False

# Cola de eventos para comunicar con el servidor
eventos_q = queue.Queue(maxsize=50)

# Estado global
_estado = {
    "activo": False,
    "fase": "dormido",       # dormido | escuchando_wake | escuchando_cmd | procesando
    "ultimo_cmd": "",
    "ultimo_tiempo": None,
    "error": None,
    "thread": None,
}

_stop_flag = threading.Event()
_reconocedor = None
_microfono = None


def _log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[VOZ {ts}] {msg}"
    print(line)
    try:
        eventos_q.put_nowait({"tipo": "log", "msg": msg, "ts": ts})
    except queue.Full:
        pass


def _emitir(tipo, **kwargs):
    try:
        eventos_q.put_nowait({"tipo": tipo, "ts": datetime.now().strftime("%H:%M:%S"), **kwargs})
    except queue.Full:
        pass


def _hablar(texto):
    """Habla usando nexus_voice si está disponible."""
    try:
        from nexus_voice import hablar
        hablar(texto)
    except Exception:
        print(f"[VOZ] → {texto}")


def _procesar_comando(texto):
    """Envía el comando al asistente y habla la respuesta."""
    try:
        from nexus_assistant import get_respuesta
        r = get_respuesta(texto, "voz_global")
        respuesta = r.get("respuesta", "No entendí") if isinstance(r, dict) else str(r)
        _hablar(respuesta)
        return respuesta
    except Exception as e:
        _hablar("No pude procesar ese comando")
        return f"Error: {e}"


def _loop_escucha():
    """Loop principal de escucha — corre en thread background."""
    global _reconocedor, _microfono

    if not SR_OK:
        _log("speech_recognition no disponible")
        _estado["error"] = "speech_recognition no instalado"
        return

    _reconocedor = sr.Recognizer()
    _reconocedor.energy_threshold = 300
    _reconocedor.dynamic_energy_threshold = True
    _reconocedor.pause_threshold = 0.8

    try:
        _microfono = sr.Microphone()
    except Exception as e:
        _estado["error"] = f"No se detectó micrófono: {e}"
        _log(f"Error micrófono: {e}")
        return

    # Ajuste de ruido ambiente inicial
    _log("Calibrando micrófono...")
    try:
        with _microfono as source:
            _reconocedor.adjust_for_ambient_noise(source, duration=1)
        _log("Calibración lista. Esperando 'nexus'...")
    except Exception as e:
        _log(f"Calibración fallida: {e}")

    _estado["fase"] = "escuchando_wake"
    _emitir("estado", fase="escuchando_wake")

    WAKE_WORDS = ["nexus", "nexos", "nexis", "néctar"]  # variantes fonéticas

    while not _stop_flag.is_set():
        try:
            _estado["fase"] = "escuchando_wake"
            with _microfono as source:
                audio = _reconocedor.listen(source, timeout=5, phrase_time_limit=4)

            # Reconocer wake word
            try:
                texto = _reconocedor.recognize_google(audio, language="es-MX").lower()
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                _log(f"Error Google STT: {e}")
                time.sleep(2)
                continue

            _log(f"Escuché: '{texto}'")

            # ¿Contiene wake word?
            if any(w in texto for w in WAKE_WORDS):
                _hablar("Mande")
                _estado["fase"] = "escuchando_cmd"
                _emitir("estado", fase="escuchando_cmd")
                _log("Wake word detectado. Escuchando comando...")

                # Escuchar el comando
                try:
                    with _microfono as source:
                        audio_cmd = _reconocedor.listen(source, timeout=6, phrase_time_limit=10)
                    cmd = _reconocedor.recognize_google(audio_cmd, language="es-MX")
                    _log(f"Comando: '{cmd}'")
                    _estado["ultimo_cmd"] = cmd
                    _estado["ultimo_tiempo"] = datetime.now().isoformat()
                    _emitir("comando", texto=cmd)

                    # Procesar
                    _estado["fase"] = "procesando"
                    _emitir("estado", fase="procesando")
                    respuesta = _procesar_comando(cmd)
                    _emitir("respuesta", cmd=cmd, respuesta=respuesta)

                except sr.WaitTimeoutError:
                    _hablar("No escuché nada")
                    _emitir("estado", fase="timeout")
                except sr.UnknownValueError:
                    _hablar("No entendí el comando")
                except Exception as e:
                    _log(f"Error cmd: {e}")

        except sr.WaitTimeoutError:
            # Normal — no hubo audio en 5 segundos
            continue
        except Exception as e:
            _log(f"Error loop: {e}")
            time.sleep(1)

    _estado["fase"] = "dormido"
    _estado["activo"] = False
    _emitir("estado", fase="dormido")
    _log("Escucha detenida.")


# ── API pública ────────────────────────────────────────────────────────────────

def iniciar():
    """Inicia el listener en background. Retorna dict estado."""
    if _estado["activo"]:
        return {"ok": True, "msg": "Ya estaba activo", "fase": _estado["fase"]}

    _stop_flag.clear()
    _estado["activo"] = True
    _estado["error"] = None

    t = threading.Thread(target=_loop_escucha, daemon=True, name="nexus-voz")
    t.start()
    _estado["thread"] = t

    return {"ok": True, "msg": "Escucha iniciada", "fase": "calibrando"}


def detener():
    """Detiene el listener."""
    _stop_flag.set()
    _estado["activo"] = False
    return {"ok": True, "msg": "Escucha detenida"}


def estado():
    """Retorna estado actual."""
    return {
        "ok": True,
        "activo": _estado["activo"],
        "fase": _estado["fase"],
        "ultimo_cmd": _estado["ultimo_cmd"],
        "ultimo_tiempo": _estado["ultimo_tiempo"],
        "error": _estado["error"],
        "mic_disponible": SR_OK,
    }


def eventos_pendientes():
    """Drena la cola de eventos — para polling SSE."""
    evs = []
    try:
        while True:
            evs.append(eventos_q.get_nowait())
    except queue.Empty:
        pass
    return evs

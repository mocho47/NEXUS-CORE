import os
import asyncio
import edge_tts
import pygame
import pyttsx3
import time
import uuid

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO_FILE = os.path.join(BASE_DIR, "temp_voice.mp3")

# --- INICIALIZACIÓN ÚNICA (MEJORA FLUIDEZ) ---
try:
    pygame.mixer.init()
    print("[VOICE ENGINE] Sistema de audio online.")
except Exception as e:
    print(f"[VOICE ENGINE ERROR] Fallo al iniciar Pygame: {e}")

# Cache del motor offline para no re-inicializar
_offline_engine = None

def get_offline_engine():
    global _offline_engine
    if _offline_engine is None:
        _offline_engine = pyttsx3.init()
        _offline_engine.setProperty('rate', 150)
        # Configurar voz masculina offline si existe
        voices = _offline_engine.getProperty('voices')
        target_voice = None
        for v in voices:
            if "sabina" in v.name.lower() or "pablo" in v.name.lower() or "raul" in v.name.lower():
                target_voice = v.id; break
        if target_voice: _offline_engine.setProperty('voice', target_voice)
        elif any('Helena' in v.name for v in voices):
            # Fallback: Helena es-ES si no hay voz mexicana
            helena = next(v for v in voices if 'Helena' in v.name)
            _offline_engine.setProperty('voice', helena.id)
    return _offline_engine

# --- FUNCIÓN DE PARADA ---
def callar():
    """Detiene cualquier reproducción de audio inmediatamente."""
    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # También intentar parar engine offline si está hablando
        global _offline_engine
        if _offline_engine and _offline_engine.isBusy():
            _offline_engine.stop()
    except: pass

def is_busy():
    """Retorna True si hay audio reproduciéndose."""
    try:
        online_busy = pygame.mixer.get_init() and pygame.mixer.music.get_busy()
        offline_busy = _offline_engine and _offline_engine.isBusy()
        return online_busy or offline_busy
    except: return False

# --- FUNCIÓN PRINCIPAL ---
def hablar(text):
    """
    Genera y reproduce audio.
    Prioridad: Edge TTS (Online Neural) -> Pyttsx3 (Offline SAPI5)
    """
    if not text: return
    
    # Detener lo anterior si hablaba
    callar()

    # INTENTO 1: EDGE TTS (ONLINE)
    temp_file = os.path.join(BASE_DIR, f"voice_{uuid.uuid4().hex}.mp3")
    try:
        # Voz Neural Masculina Mexicana
        voice = "es-MX-JorgeNeural"
        communicate = edge_tts.Communicate(text, voice)
        
        # Generación asíncrona encapsulada
        asyncio.run(communicate.save(temp_file))
        
        # Reproducción optimizada
        if pygame.mixer.get_init():
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Bloqueo eficiente
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            
            pygame.mixer.music.unload() # Liberar archivo
            
            # Limpieza rápida
            try: os.remove(temp_file)
            except: pass
            return # Éxito, salir

    except Exception as e:
        print(f"[VOICE WARNING] Fallo EdgeTTS ({e}).")
        try: 
            if os.path.exists(temp_file): os.remove(temp_file)
        except: pass

        # FALLBACK OFFLINE (SAPI5) — mejor hablar robótico que quedarse mudo
        try:
            engine = get_offline_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as e2:
            print(f"[VOICE ERROR] Fallo fallback offline ({e2}).")

def hablar_archivo(text, file_path):
    """Genera un archivo MP3 sin reproducirlo (para campañas de marketing)"""
    try:
        voice = "es-MX-JorgeNeural"
        communicate = edge_tts.Communicate(text, voice)
        asyncio.run(communicate.save(file_path))
        print(f"[VOICE] Archivo generado: {file_path}")
        return True
    except Exception as e:
        print(f"[VOICE ERROR] No pude generar archivo: {e}")
        return False

if __name__ == "__main__":
    print("Probando motor de voz...")
    hablar("Sistema de voz independiente iniciado. Soy fluido y modular.")
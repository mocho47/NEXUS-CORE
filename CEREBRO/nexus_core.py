import sys
import os
import queue
import json
import subprocess
import time
import threading
import psutil
import asyncio
import edge_tts
import pygame
import requests
import sounddevice as sd
import vosk
import shutil
import uuid
import pyttsx3
import random
from thefuzz import process
from groq import Groq

# ==========================================
# CONFIGURACIÓN MAESTRA (NEXUS V1.9 - SWISS WATCH)
# ==========================================
# Rutas ajustadas para robustez
BASE_PATH = r"C:\NEXUS"
MODEL_PATH = r"C:\NEXUS\CEREBRO\model"
BOXES_PATH = r"C:\NEXUS\TALLER\boxes"  # Asumiendo que boxes está aquí o en documentos
TALLER_PATH = r"C:\NEXUS\TALLER"

# Si boxes no está en C:\NEXUS, busca en documentos (ruta alternativa)
if not os.path.exists(BOXES_PATH):
    BOXES_PATH = r"C:\Users\anuar\Documents\trae_projects\habilitar respaldo aspire y corel\boxes"

USE_CLOUD = True
GROQ_API_KEY = "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"
WAKE_WORD = "nexus"
VOICE_NEURAL = "es-MX-JorgeNeural"
RAM_LIMIT_PERCENT = 95

# Inicialización segura de TTS Rápido
try:
    engine_fast = pyttsx3.init()
    engine_fast.setProperty('rate', 190)
    engine_fast.setProperty('volume', 1.0)
except:
    pass

# Inicialización segura de Cliente Groq
client_groq = None
if USE_CLOUD:
    try:
        client_groq = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[ERROR INICIO GROQ]: {e}")

# ==========================================
# 1. SISTEMA DE VOZ ROBUSTO
# ==========================================
def hablar_rapido(texto):
    """Voz robótica local (rápida/sin internet)"""
    print(f"NEXUS (Fast): {texto}")
    try:
        engine_fast.say(texto)
        engine_fast.runAndWait()
    except:
        pass

async def hablar_neural_async(texto):
    """Voz realista (requiere internet)"""
    try:
        # Nombre aleatorio para evitar conflictos de permisos
        filename = f"voice_{uuid.uuid4()}.mp3"
        communicate = edge_tts.Communicate(texto, VOICE_NEURAL)
        await communicate.save(filename)
        
        # Reproducción con Pygame
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        # Esperar a que termine (con timeout de seguridad)
        start_time = time.time()
        while pygame.mixer.music.get_busy():
            if time.time() - start_time > 30: # Timeout 30s
                pygame.mixer.stop()
                break
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        
        # Limpieza en hilo separado para no bloquear
        threading.Thread(target=borrar_archivo, args=(filename,)).start()
        
    except Exception as e:
        print(f"[ERROR NEURAL]: {e}")
        hablar_rapido(texto)

def borrar_archivo(filename):
    time.sleep(1) # Esperar a que se libere el archivo
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except:
        pass

def hablar(texto):
    """Selector inteligente de voz"""
    if not texto: return
    
    # Si es muy corto o hay error crítico, usar rápida
    if len(texto) < 30 or "error" in texto.lower():
        hablar_rapido(texto)
    else:
        try:
            asyncio.run(hablar_neural_async(texto))
        except:
            hablar_rapido(texto)

# ==========================================
# 2. INTELIGENCIA (GROQ + LOCAL + PARANORMAL)
# ==========================================
def consultar_groq(pregunta):
    if not client_groq:
        return None
    try:
        chat_completion = client_groq.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Eres Nexus, una IA avanzada de taller. Tu personalidad es: Sobria, Eficiente, Técnica. Respuestas cortas y directas. NO uses markdown. NO des explicaciones largas a menos que se pidan."
                },
                {"role": "user", "content": pregunta}
            ],
            # MODELO ESTABLE (Llama 3.1)
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
        )
        respuesta = chat_completion.choices[0].message.content
        return respuesta
    except Exception as e:
        print(f"[GROQ ERROR]: {e}")
        return None

def modulo_paranormal():
    """Script local para evitar alucinaciones de la IA"""
    respuestas = [
        "Escaneando frecuencias bajas...",
        "Detectando anomalía electromagnética.",
        "No hay presencia espectral confirmada, pero los sensores están inquietos.",
        "Modo vigilancia activado. Nada por aquí."
    ]
    efecto = random.choice(respuestas)
    hablar(efecto)
    return

def cerebro_local_fallback(texto):
    texto = texto.lower()
    if "hola" in texto: return "Sistemas en línea."
    if "hora" in texto: 
        from datetime import datetime
        return f"Son las {datetime.now().strftime('%H:%M')}"
    if "estado" in texto: return "Todo operativo. RAM estable."
    return "No pude procesar eso sin la nube."

# ==========================================
# 3. MANOS (TALLER)
# ==========================================
def herramienta_cajas(comando):
    # Extraer números: "caja 100 por 50 alto 30" -> [100, 50, 30]
    nums = [int(s) for s in comando.split() if s.isdigit()]
    
    if len(nums) >= 3:
        x, y, h = nums[0], nums[1], nums[2]
        hablar_rapido(f"Diseñando caja {x} por {y}.")
        
        # Nombre seguro
        nombre_archivo = f"Caja_{x}x{y}x{h}.dxf"
        ruta_salida = os.path.join(TALLER_PATH, nombre_archivo)
        
        # Comando para boxes.py
        cmd = [
            sys.executable, "-m", "boxes", "UniversalBox",
            f"--x={x}", f"--y={y}", f"--h={h}",
            "--thickness=3", "--format=dxf",
            "--output", ruta_salida
        ]
        
        try:
            # Ejecutar boxes
            subprocess.run(cmd, cwd=BOXES_PATH, check=True, shell=True, capture_output=True)
            hablar("Diseño generado correctamente.")
            
            # Abrir carpeta
            if os.path.exists(TALLER_PATH):
                os.startfile(TALLER_PATH)
        except Exception as e:
            print(f"[ERROR CAJAS]: {e}")
            hablar("Hubo un error generando el plano.")
    else:
        hablar("Indica largo, ancho y alto en milímetros.")

# ==========================================
# 4. ROUTER DE INTENCIONES
# ==========================================
def procesar_intencion(texto):
    texto_low = texto.lower()
    
    # --- COMANDOS LOCALES (PRIORIDAD) ---
    
    # 1. PARANORMAL / BROMAS (Local puro)
    if "actividad" in texto_low or "fantasma" in texto_low or "paranormal" in texto_low:
        modulo_paranormal()
        return

    # 2. TALLER / CAJAS
    if "caja" in texto_low:
        herramienta_cajas(texto_low)
        return

    # 3. HORA
    if "hora" in texto_low:
        from datetime import datetime
        hablar_rapido(f"Son las {datetime.now().strftime('%H:%M')}")
        return

    # --- COMANDO NUBE (GROQ) ---
    respuesta_nube = consultar_groq(texto)
    if respuesta_nube:
        hablar(respuesta_nube)
    else:
        # Fallback si falla la nube
        hablar(cerebro_local_fallback(texto))

# ==========================================
# 5. BUCLE PRINCIPAL (SWISS WATCH LOOP)
# ==========================================
def main():
    # Verificación de inicio
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR CRÍTICO] No encuentro el modelo en: {MODEL_PATH}")
        return

    # Configuración VOSK silenciosa
    vosk.SetLogLevel(-1)
    
    try:
        model = vosk.Model(MODEL_PATH)
    except Exception as e:
        print(f"[ERROR VOSK]: {e}")
        return

    # Cola de audio
    q = queue.Queue()

    def callback(indata, frames, time, status):
        """Este callback se llama desde un hilo separado por sounddevice"""
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    print("\n--------------------------------")
    print(" NEXUS V1.9 - SISTEMA LISTO")
    print("--------------------------------\n")
    
    hablar_rapido("Nexus operativo.")

    # Bucle de escucha
    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None, dtype='int16', channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        
        while True:
            try:
                # Obtener datos de audio (bloqueante pero seguro)
                data = q.get()
                
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    texto_escuchado = res.get('text', '')
                    
                    if texto_escuchado:
                        # Detección difusa de "Nexus"
                        # "nexus" -> score 100, "nexo" -> score ~80
                        match = process.extractOne(WAKE_WORD, texto_escuchado.split())
                        
                        activado = False
                        comando_limpio = ""

                        if WAKE_WORD in texto_escuchado:
                            activado = True
                            comando_limpio = texto_escuchado.replace(WAKE_WORD, "").strip()
                        elif match and match[1] > 85: # Umbral de confianza
                            activado = True
                            # Intentar limpiar la palabra gatillo aproximada
                            comando_limpio = texto_escuchado.replace(match[0], "").strip()

                        if activado:
                            if len(comando_limpio) > 2:
                                print(f">> COMANDO: {comando_limpio}")
                                hablar_rapido("Sí.") # Feedback inmediato
                                procesar_intencion(comando_limpio)
                            else:
                                # Solo dijo "Nexus" sin comando
                                hablar_rapido("¿Dime?")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR BUCLE]: {e}")
                # No detener el bucle, solo loguear y seguir
                continue

if __name__ == "__main__":
    main()

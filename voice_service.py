from nexus_authorization import authorizer
import speech_recognition as sr
import threading
import logging
import time
import pyttsx3
import os
from gtts import gTTS
import pygame

class VoiceService:
    def __init__(self, command_callback=None):
        self.logger = logging.getLogger("NexusV9.VoiceService")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.command_callback = command_callback
        self.running = False
        self.is_listening = False
        
        # 1. Sistema Offline (Respaldo - Robótico)
        self.offline_engine = pyttsx3.init()
        self.offline_engine.setProperty('rate', 160)
        
        # 2. Sistema Online (Google - Fluido)
        # Inicializar mixer de pygame para reproducir audio sin bloqueo
        pygame.mixer.init()
        
        # Ajustar sensibilidad del micrófono
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.recognizer.dynamic_energy_threshold = True

    def start_listening(self):
        """Inicia el hilo de escucha continua."""
        if not authorizer.request_permission("Iniciar escucha de voz", "Activar reconocimiento de voz en NEXUS"):
            self.logger.warning("[NEXUS] Acción de escucha de voz denegada por el usuario.")
            return
        self.running = True
        # Saludo inicial fluido (Google Voice)
        self.speak("Nexus iniciando modo conversacional... Sistemas en línea.", force_google=True)
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        self.logger.info("Voice Recognition Protocol ACTIVATED. Listening for commands...")

    def _listen_loop(self):
        while self.running:
            try:
                if not self.is_listening:
                    with self.microphone as source:
                        # Escuchar sin timeout estricto para conversación continua
                        try:
                            audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                            self._process_audio(audio)
                        except sr.WaitTimeoutError:
                            pass
            except Exception as e:
                self.logger.error(f"Error in voice loop: {e}")
                time.sleep(1)

    def _process_audio(self, audio):
        try:
            # Reconocer voz
            text = self.recognizer.recognize_google(audio, language="es-MX").lower()
            self.logger.info(f"Heard: '{text}'")

            # Solo procesar si contiene el trigger 'nexus' o es modo conversacional
            if "nexus" in text:
                if self.command_callback:
                    self.command_callback(text)
            elif "dame una idea" in text:
                # Modo conversacional: preguntar tema
                self.speak("¿Sobre qué tema quieres una idea? Puedes decir: marketing, ventas, motivación, tecnología, o el que prefieras.")
            # Si no contiene trigger ni modo conversacional, ignorar
        except sr.UnknownValueError:
            pass # Ruido de fondo
        except sr.RequestError as e:
            self.logger.error(f"Could not request results; {e}")

    def speak(self, text, force_google=True):
        if not authorizer.request_permission("Hablar por voz", f"Texto: {text}"):
            self.logger.warning("[NEXUS] Acción de voz denegada por el usuario.")
            return
        """Sistema Híbrido de Voz: Intenta Google primero, falla a Windows si no hay internet."""
        def run_speech():
            if force_google:
                try:
                    # Intentar generar voz fluida con Google
                    filename = f"temp_speech_{int(time.time())}.mp3"
                    tts = gTTS(text=text, lang='es', tld='com.mx') # Acento mexicano
                    tts.save(filename)
                    
                    # Reproducir
                    pygame.mixer.music.load(filename)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    # Limpiar archivo temporal
                    pygame.mixer.music.unload()
                    os.remove(filename)
                    return # Éxito, salir
                    
                except Exception as e:
                    self.logger.warning(f"Google TTS failed ({e}), switching to offline backup.")
            
            # Fallback: Voz Robótica Offline
            try:
                self.offline_engine.say(text)
                self.offline_engine.runAndWait()
            except:
                pass
            
        threading.Thread(target=run_speech).start()

    def stop(self):
        if not authorizer.request_permission("Detener servicio de voz", "Solicitud de parada del motor de voz"):
            self.logger.warning("[NEXUS] Acción de parada de voz denegada por el usuario.")
            return
        self.running = False
        pygame.mixer.quit()

import time
import random
import threading
import logging
import ctypes
import pyttsx3
import tkinter as tk
from tkinter import Toplevel
import winsound

class ActivityManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("NexusV9.ActivityManager")
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 130)  # Velocidad normal
        self.paranormal_mode = True
        self.insomnia_mode = True
        
        # Constantes de Windows
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        
        self.target_name = None
        self.haunt_active = False

    def detect_activity(self):
        """Monitorea actividad y ejecuta sustos si se activa."""
        if self.insomnia_mode:
            self._prevent_sleep()

        if self.haunt_active and self.target_name:
            self._execute_haunt_sequence()

    def scan_target(self, name):
        """Comando clave para iniciar la pesadilla."""
        self.target_name = name
        self.haunt_active = True
        self.logger.warning(f"TARGET LOCKED: {name}. INITIATING POSSESSION PROTOCOL.")
        self._speak(f"Analizando a... {name}...", slow=True)
        time.sleep(2)
        self._speak("Objetivo... encontrado...", pitch_down=True)

    def _execute_haunt_sequence(self):
        """Secuencia aleatoria de eventos paranormales."""
        event = random.choice([
            "whisper", "scream", "glitch_screen", "reverse_talk", "threaten"
        ])
        
        if random.random() < 0.3:  # 30% de probabilidad por ciclo
            if event == "whisper":
                self._speak(f"{self.target_name}...", whisper=True)
            elif event == "scream":
                self._play_scream()
            elif event == "glitch_screen":
                self._trigger_visual_glitch()
            elif event == "reverse_talk":
                self._speak_reverse(f"Te estoy viendo {self.target_name}")
            elif event == "threaten":
                self._speak(f"No te escondas... {self.target_name}...", slow=True)

    def _speak(self, text, slow=False, whisper=False, pitch_down=False):
        """Genera voces sintéticas aterradoras."""
        def run_speech():
            engine = pyttsx3.init()
            rate = 80 if slow else 150
            if whisper: rate = 200 # Susurro rápido
            engine.setProperty('rate', rate)
            
            # Intentar cambiar voz (a veces ayuda a sonar raro)
            voices = engine.getProperty('voices')
            if pitch_down and len(voices) > 1:
                engine.setProperty('voice', voices[1].id) # Voz diferente
            
            engine.say(text)
            engine.runAndWait()
        
        threading.Thread(target=run_speech).start()

    def _speak_reverse(self, text):
        """Dice frases al revés (efecto demoníaco)."""
        reversed_text = text[::-1]
        self._speak(reversed_text, slow=True, pitch_down=True)

    def _play_scream(self):
        """Genera un sonido de alta frecuencia (Beep de Windows o simulado)."""
        def scream():
            # Tono agudo y molesto
            winsound.Beep(4000, 200) 
            time.sleep(0.1)
            winsound.Beep(3500, 300)
            winsound.Beep(500, 500) # Grave final
        threading.Thread(target=scream).start()

    def _trigger_visual_glitch(self):
        """Crea destellos rojos/negros en pantalla completa."""
        def flash():
            root = tk.Tk()
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.3) # Transparente fantasmal
            
            colors = ["red", "black", "white"]
            for _ in range(10):
                root.configure(bg=random.choice(colors))
                root.update()
                time.sleep(0.05)
                
            root.destroy()
            
        threading.Thread(target=flash).start()

    def _prevent_sleep(self):
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED
            )
        except: pass

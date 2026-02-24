import os
import pychromecast
import time
import threading

class CastManager:
    def __init__(self):
        self.chromecasts = []
        self.browser = None
        self.scan_thread = threading.Thread(target=self.scan_devices, daemon=True)
        self.scan_thread.start()

    def scan_devices(self):
        print("[CAST] Buscando dispositivos Google/Chromecast...")
        try:
            self.chromecasts, self.browser = pychromecast.get_listed_chromecasts(friendly_names=[])
            # Filtrar por nombres conocidos
            names = [cc.device.friendly_name for cc in self.chromecasts]
            print(f"[CAST] Encontrados: {len(names)} dispositivos. {names}")
        except Exception as e:
            print(f"[CAST ERROR] {e}")

    def get_device(self, name_part):
        # Normalizar búsqueda
        name_part = name_part.lower()
        
        # Mapeo de nombres cortos a nombres reales de Google Home
        aliases = {
            "oficina": "oficina 2",
            "oficina 2": "oficina 2",
            "oficina2": "oficina 2",
            "tv": "android",
            "tele": "android",
            "gominola": "android", # Alias para Android TV Box
            "caja": "android"
        }
        
        target = aliases.get(name_part, name_part)
        
        # Búsqueda en caché
        for cc in self.chromecasts:
            if target in cc.device.friendly_name.lower():
                return cc
                
        # Si no está en caché, intentar rescan rápido
        print(f"[CAST] Dispositivo '{target}' no encontrado en caché. Re-escaneando...")
        self.chromecasts, _ = pychromecast.get_listed_chromecasts(friendly_names=[])
        
        for cc in self.chromecasts:
            if target in cc.device.friendly_name.lower():
                return cc
                
        return None

    def speak_on_device(self, device_name, text, lang='es'):
        cc = self.get_device(device_name)
        if not cc:
            print(f"[CAST] No encontré dispositivo con nombre '{device_name}'")
            return
        
        print(f"[CAST] Conectando a {cc.device.friendly_name}...")
        try:
            cc.wait()
            mc = cc.media_controller
            # Usar Google TTS API (URL pública)
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text.replace(' ', '+')}&tl={lang}&client=tw-ob"
            mc.play_media(tts_url, 'audio/mp3')
            mc.block_until_active()
        except Exception as e:
            print(f"[CAST ERROR] Fallo al hablar en {device_name}: {e}")

    def broadcast(self, text):
        # Enviar a todos (secuencial para no bloquear)
        for cc in self.chromecasts:
            try:
                self.speak_on_device(cc.device.friendly_name, text)
            except: pass

caster = None


def get_caster() -> CastManager:
    global caster
    if caster is None:
        caster = CastManager()
    return caster


if os.environ.get("NEXUS_NO_AUTOSTART", "0").strip().lower() not in ("1", "true", "yes"):
    caster = CastManager()

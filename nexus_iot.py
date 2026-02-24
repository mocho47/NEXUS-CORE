"""
nexus_iot.py — Control de dispositivos IoT / Chromecast.
Lanza como subproceso o importa directamente.
"""
import sys
import os

def log(msg):
    print(f"[IOT] {msg}")

try:
    import pychromecast
    CAST_AVAILABLE = True
except ImportError:
    CAST_AVAILABLE = False
    log("pychromecast no instalado. Funciones Cast deshabilitadas.")

def scan():
    if not CAST_AVAILABLE:
        return []
    log("Escaneando dispositivos...")
    devices, browser = pychromecast.get_chromecasts()
    log(f"Encontrados: {len(devices)} dispositivos.")
    return devices

def cast_message(device_name, text, lang="es"):
    """Envía mensaje TTS a un dispositivo Chromecast por nombre."""
    if not CAST_AVAILABLE:
        log("pychromecast no disponible.")
        return False
    log(f"Buscando dispositivo: {device_name}...")
    devices, _ = pychromecast.get_chromecasts()
    for dev in devices:
        if device_name.lower() in dev.device.friendly_name.lower():
            mc = dev.media_controller
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl={lang}&client=tw-ob"
            mc.play_media(tts_url, "audio/mp3")
            mc.block_until_active()
            log(f"Mensaje enviado a {dev.device.friendly_name}")
            return True
    log(f"Dispositivo '{device_name}' no encontrado.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: nexus_iot.py scan | nexus_iot.py cast <device> <mensaje>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "scan":
        devs = scan()
        for d in devs:
            print(f"  - {d.device.friendly_name}")
    elif cmd == "cast" and len(sys.argv) >= 4:
        cast_message(sys.argv[2], sys.argv[3])

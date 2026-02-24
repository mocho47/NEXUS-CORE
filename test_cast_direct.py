import pychromecast
import time
import sys

def test_cast():
    print("--- DIAGNÓSTICO DE CHROMECAST ---")
    print("1. Escaneando red (esto puede tardar 5-10 segundos)...")
    
    chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[])
    
    print(f"2. Dispositivos encontrados: {len(chromecasts)}")
    for cc in chromecasts:
        print(f"   - '{cc.device.friendly_name}' ({cc.device.model_name}) IP: {cc.host}")

    target_name = "Oficina 2"
    target_cc = None
    
    # Búsqueda laxa
    for cc in chromecasts:
        if target_name.lower() in cc.device.friendly_name.lower():
            target_cc = cc
            break
            
    if not target_cc:
        print(f"\n[ERROR] No encontré '{target_name}'. Verifica que esté encendido y en la misma red Wifi.")
        return

    print(f"\n3. Conectando a '{target_cc.device.friendly_name}'...")
    try:
        target_cc.wait()
        print("   Conectado exitosamente.")
        
        print("4. Intentando enviar audio...")
        mc = target_cc.media_controller
        text = "Prueba de sistema uno dos tres"
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text.replace(' ', '+')}&tl=es&client=tw-ob"
        
        mc.play_media(tts_url, 'audio/mp3')
        mc.block_until_active()
        print("   Comando de reproducción enviado. ¿Escuchaste algo?")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    test_cast()

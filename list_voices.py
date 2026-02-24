import pyttsx3

def list_voices():
    print(">>> DIAGNÓSTICO DE VOCES TTS EN WINDOWS <<<")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        if not voices:
            print("[ERROR] No se detectaron voces instaladas.")
            return

        for i, v in enumerate(voices):
            print(f"\nVOZ #{i}")
            print(f" - Nombre: {v.name}")
            print(f" - ID: {v.id}")
            print(f" - Idiomas: {v.languages}")
            try:
                engine.setProperty('voice', v.id)
                engine.say(f"Esta es la voz número {i}, llamada {v.name}")
                engine.runAndWait()
            except:
                print("   (No se pudo probar audio de esta voz)")

        print("\n[CONCLUSIÓN]")
        if len(voices) < 2:
            print("Solo tienes UNA voz instalada. Si quieres voz de hombre/mujer,")
            print("debes ir a: Configuración > Hora e idioma > Voz > Agregar voces.")
        else:
            print(f"Tienes {len(voices)} voces disponibles.")

    except Exception as e:
        print(f"[FATAL] Error en motor TTS: {e}")

if __name__ == "__main__":
    list_voices()
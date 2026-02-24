import sys
import os
import time

# Añadir directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print(">>> INICIANDO PRUEBA RÁPIDA DE TERROR <<<")
print("Cargando módulos...")

try:
    import nexus_ghost
    import nexus_cast
    import nexus_voice
    
    # Esperar un poco a que el Cast escanee (si es necesario)
    print("Esperando escaneo de dispositivos (5s)...")
    time.sleep(5)
    
    print("EJECUTANDO SECUENCIA SAMANTHA...")
    nexus_voice.hablar("Iniciando prueba rápida. Corre tiempo.")
    
    # Trigger
    nexus_ghost.ghost.trigger_samantha("Samantha")
    
    print("Prueba finalizada.")

except Exception as e:
    print(f"ERROR: {e}")
    input("Presiona Enter para salir...")

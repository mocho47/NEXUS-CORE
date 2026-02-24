import os
import sys

# Asegurar que el path incluya el directorio actual
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from nexus_coder import coder
    print("DEBUG: Iniciando prueba de Nexus Coder...")
    
    # Verificar si la key se cargó (el modulo la carga de os.environ)
    if not coder.api_key:
        print("ERROR: No se detectó API KEY en nexus_coder.")
        # Intentar cargarla manualmente para la prueba si falló la variable de entorno
        coder.api_key = os.environ.get("GROQ_API_KEY")
        if not coder.api_key:
             print("FATAL: Ni en os.environ hay key.")
        else:
             print("DEBUG: Key cargada manualmente de entorno.")

    prompt = "imprime 'Hola Nexus Unleashed' en consola"
    print(f"DEBUG: Solicitando código para: {prompt}")
    
    code = coder.generate_code(prompt)
    
    if code:
        print("\n--- CÓDIGO GENERADO ---")
        print(code)
        print("-----------------------")
        
        print("\nDEBUG: Ejecutando código...")
        output = coder.save_and_run(code, "test_generated.py")
        print(f"OUTPUT:\n{output}")
    else:
        print("ERROR: No se generó código (posible error de API o conexión).")

except Exception as e:
    print(f"EXCEPCIÓN: {e}")

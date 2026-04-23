"""
arrancar_nexus.py — Levanta todos los motores NEXUS en orden.
Uso: python arrancar_nexus.py
"""
import subprocess, time, httpx, sys, os

BASE = r"C:\NEXUS_v3_NEW"
PYTHON = r"C:\Program Files\Python312\python.exe"
OLLAMA = r"C:\Users\Administrador\AppData\Local\Programs\Ollama\ollama.exe"

MOTORES = [
    # (nombre, script, puerto, crítico)
    ("Archivos",       "motors/motor_archivos.py",   8001, False),
    ("Diseño",         "motors/motor_diseno.py",     8002, False),
    ("ATF Faros",      "motors/motor_atf.py",        8004, False),
    ("Teens",          "motors/motor_teens.py",      8005, False),
    ("Pagos",          "motors/motor_pagos.py",      8007, False),
    ("Sistema",        "motors/motor_sistema.py",    8009, False),
    ("Redes",          "motors/motor_redes.py",      8010, False),
    ("Maquila DTF",    "motors/motor_maquila.py",    8011, True),
    ("Editor/Imagen",  "motors/motor_editor.py",     8012, True),
    ("Cajas Laser",    "motors/motor_cajas.py",      8013, False),
    ("Operador",       "motors/motor_operador.py",   8014, False),
    ("Coaching",       "motors/motor_coaching.py",   8016, False),
    ("Catalogos",      "motors/motor_catalogo.py",   8017, False),
    ("Forja",          "motors/motor_forja.py",      8020, False),
]

def puerto_libre(puerto: int) -> bool:
    try:
        httpx.get(f"http://localhost:{puerto}/health", timeout=2)
        return False  # ya hay algo corriendo
    except Exception:
        return True

def arrancar_motor(nombre, script, puerto):
    if not puerto_libre(puerto):
        print(f"  ✓ {nombre} ya activo (:{puerto})")
        return True
    ruta = os.path.join(BASE, script)
    if not os.path.exists(ruta):
        print(f"  ✗ {nombre} — script no encontrado: {ruta}")
        return False
    subprocess.Popen(
        [PYTHON, ruta],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return True

def verificar(nombre, puerto, intentos=6):
    for i in range(intentos):
        try:
            r = httpx.get(f"http://localhost:{puerto}/health", timeout=3)
            if r.status_code == 200:
                print(f"  ✓ {nombre} activo (:{puerto})")
                return True
        except Exception:
            pass
        time.sleep(2)
    print(f"  ✗ {nombre} no respondió (:{puerto})")
    return False

if __name__ == "__main__":
    print("═══════════════════════════════════")
    print("  NEXUS by Simplex — Iniciando...")
    print("═══════════════════════════════════")

    # 1. Ollama
    print("\n[Ollama]")
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=3)
        print("  ✓ Ollama ya activo")
    except Exception:
        subprocess.Popen([OLLAMA, "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(4)
        print("  ✓ Ollama iniciado")

    # 2. Motores especializados
    print("\n[Motores especializados]")
    for nombre, script, puerto, critico in MOTORES:
        arrancar_motor(nombre, script, puerto)

    # Esperar arranque
    time.sleep(5)
    print("\n[Verificando...]")
    activos = 0
    for nombre, script, puerto, critico in MOTORES:
        if verificar(nombre, puerto):
            activos += 1

    # 3. Nexus Core (orquestador principal)
    print("\n[Nexus Core]")
    arrancar_motor("NEXUS Core", "nexus_core.py", 8003)
    time.sleep(6)
    verificar("NEXUS Core", 8003)

    print(f"\n{'═'*35}")
    print(f"  NEXUS listo — {activos}/{len(MOTORES)} motores activos")
    print(f"  Panel: http://localhost:8003")
    print(f"  Editor: http://localhost:8003/editor")
    print(f"  Maquila: http://localhost:8003/maquila")
    print(f"{'═'*35}\n")

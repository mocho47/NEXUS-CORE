# driver_memoria.py
# Driver de Memoria para Nexus Global v7.0
# Descarga la memoria histórica de TRAe, la preserva en Nexus y registra en bitácora

import os
import shutil
from datetime import datetime

BITACORA = r"C:\NEXUS\bitacora.md"
MEMORIA_TRAE = r"C:\NEXUS\memoria_TRAE"
MEMORIA_NEXUS = r"C:\NEXUS\v7.0\memoria_integrada"

def registrar_bitacora(evento: str):
    """Registra eventos en la bitácora con fecha y hora."""
    with open(BITACORA, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {evento}\n")

def integrar_memoria():
    """Integra la memoria histórica de TRAe en Nexus v7.0."""
    if not os.path.exists(MEMORIA_TRAE):
        registrar_bitacora("ERROR: No se encontró carpeta memoria_TRAE")
        return

    os.makedirs(MEMORIA_NEXUS, exist_ok=True)

    for item in os.listdir(MEMORIA_TRAE):
        src = os.path.join(MEMORIA_TRAE, item)
        dst = os.path.join(MEMORIA_NEXUS, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        registrar_bitacora(f"Driver Memoria integró {item} desde TRAe → Nexus v7.0")

    registrar_bitacora("Integración completa: Memoria histórica de TRAe preservada en Nexus Global v7.0")

if __name__ == "__main__":
    registrar_bitacora("Driver Memoria iniciado")
    integrar_memoria()
    registrar_bitacora("Driver Memoria finalizó ejecución")
"""
nexus_spy.py — Monitor de productividad (deshabilitado).
Módulo reservado para futura implementación de estadísticas de uso.
No consume CPU ni recursos. No lanza threads.
"""

SHARED_PATH = ""  # Compatibilidad con nexus_core.py

class SpyModule:
    active = False
    def monitor(self): pass

spy = SpyModule()

def get_spy():
    return spy

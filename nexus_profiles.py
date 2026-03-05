"""
nexus_profiles.py — Sistema de perfiles de usuario NEXUS
Define ADMIN (Anuar/propietario) y NEGOCIO (cliente comprador).
No bloquea rutas a nivel servidor (eso es por licencia).
Define el comportamiento, alcance y visibilidad de cada perfil.
"""

import os
import json
import hashlib
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
PROFILE_PATH = os.path.join(CONFIG_DIR, "perfil_activo.json")

# ─────────────────────────────────────────────────────────────────────────────
# DEFINICIÓN DE PERFILES
# ─────────────────────────────────────────────────────────────────────────────

PERFIL_ADMIN = {
    "id": "admin",
    "nombre": "Anuar — Simplex GDL",
    "tipo": "ADMIN",
    "licencia": "ADMIN",
    "acceso_personal": True,       # Puede acceder a /mio y módulos personales
    "acceso_negocio": True,        # Acceso total al negocio
    "puede_crear_licencias": True, # Puede generar licencias para clientes
    "puede_ver_logs": True,        # Acceso a logs de auditoría
    "puede_editar_config": True,   # Puede cambiar configuración global
    "puede_eliminar": True,        # Puede borrar pedidos, clientes, etc.
    "puede_exportar": True,        # Puede exportar DB, backups
    "modulos_negocio": [
        "pedidos", "clientes", "stock", "cotizar", "agenda",
        "marketing", "finanzas", "autoventas", "historial",
        "milens", "estudio", "canbusfix", "atf", "licencias",
        "config", "admin", "sistema", "comandos", "demo",
        "backup", "qr", "reporte"
    ],
    "modulos_personales": [
        "galeria", "nexus-ear", "paranormal", "subliminal",
        "teens", "social"
    ],
    "tabs_dashboard": [
        "inicio", "pedidos", "clientes", "stock", "cotizar",
        "agenda", "marketing", "_finanzas", "autoventas",
        "comandos_tab", "historial", "sistema", "milens",
        "_estudio", "_canbusfix", "_atf", "demo",
        "licencias", "config", "_admin"
    ],
    "color_badge": "#f5c518",
    "descripcion": "Propietario — acceso total a NEXUS Negocio y Personal"
}

PERFIL_NEGOCIO = {
    "id": "negocio",
    "nombre": "Usuario NEXUS Negocio",
    "tipo": "NEGOCIO",
    "licencia": "PRO",             # Mínimo PRO para clientes compradores
    "acceso_personal": False,      # NO — sus módulos personales son suyos via /mio
    "acceso_negocio": True,
    "puede_crear_licencias": False,
    "puede_ver_logs": False,
    "puede_editar_config": True,   # Puede configurar su negocio
    "puede_eliminar": True,        # Puede borrar sus propios datos
    "puede_exportar": True,        # Puede exportar sus datos
    "modulos_negocio": [
        "pedidos", "clientes", "stock", "cotizar", "agenda",
        "marketing", "finanzas", "autoventas", "historial",
        "estudio", "licencias", "config", "sistema",
        "comandos", "demo", "backup", "qr", "reporte"
    ],
    "modulos_personales": [],      # Sus personales están en /mio con su propio PIN
    "tabs_dashboard": [
        "inicio", "pedidos", "clientes", "stock", "cotizar",
        "agenda", "marketing", "_finanzas", "autoventas",
        "comandos_tab", "historial", "sistema",
        "_estudio", "demo", "licencias", "config"
    ],
    "color_badge": "#00bfff",
    "descripcion": "Cliente — NEXUS Negocio completo, sin módulos personales del propietario"
}

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────────────────────

def get_perfil_activo() -> dict:
    """Lee el perfil activo desde CONFIG/perfil_activo.json"""
    try:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except Exception:
        pass
    # Por defecto retorna ADMIN (máquina del propietario)
    return PERFIL_ADMIN

def set_perfil_activo(perfil_id: str) -> dict:
    """Cambia el perfil activo"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    perfil = PERFIL_ADMIN if perfil_id == "admin" else PERFIL_NEGOCIO
    perfil["_actualizado"] = datetime.datetime.now().isoformat()
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)
    return perfil

def puede_acceder(modulo: str) -> bool:
    """Verifica si el perfil activo puede acceder a un módulo"""
    perfil = get_perfil_activo()
    todos = perfil.get("modulos_negocio", []) + perfil.get("modulos_personales", [])
    return modulo in todos or perfil.get("tipo") == "ADMIN"

def es_admin() -> bool:
    """True si el perfil activo es ADMIN"""
    return get_perfil_activo().get("tipo") == "ADMIN"

def info_perfil() -> dict:
    """Retorna resumen legible del perfil activo"""
    perfil = get_perfil_activo()
    return {
        "perfil": perfil.get("tipo", "DESCONOCIDO"),
        "nombre": perfil.get("nombre", ""),
        "descripcion": perfil.get("descripcion", ""),
        "modulos_total": len(perfil.get("modulos_negocio", [])) + len(perfil.get("modulos_personales", [])),
        "acceso_personal": perfil.get("acceso_personal", False),
        "puede_crear_licencias": perfil.get("puede_crear_licencias", False),
        "color": perfil.get("color_badge", "#888"),
    }

# ─────────────────────────────────────────────────────────────────────────────
# PERMISOS GRANULARES
# ─────────────────────────────────────────────────────────────────────────────

PERMISOS = {
    "ADMIN": {
        "ver_logs_auditoria":   True,
        "crear_licencias":      True,
        "eliminar_pedidos":     True,
        "eliminar_clientes":    True,
        "exportar_db":          True,
        "ver_modulos_personales": True,
        "ver_tab_admin":        True,
        "cambiar_precios":      True,
        "gestionar_usuarios":   True,
        "ver_galeria_binaural": True,
        "activar_paranormal":   True,
        "generar_subliminal":   True,
        "acceso_nexus_ear":     True,
        "ver_teens_admin":      True,
        "acceso_vault":         True,
        "reset_sistema":        True,
        "ver_all_clientes":     True,
        "enviar_campanas":      True,
        "modificar_config_global": True,
    },
    "NEGOCIO": {
        "ver_logs_auditoria":   False,
        "crear_licencias":      False,
        "eliminar_pedidos":     True,
        "eliminar_clientes":    True,
        "exportar_db":          True,
        "ver_modulos_personales": False,
        "ver_tab_admin":        False,
        "cambiar_precios":      True,
        "gestionar_usuarios":   False,
        "ver_galeria_binaural": False,
        "activar_paranormal":   False,
        "generar_subliminal":   False,
        "acceso_nexus_ear":     False,
        "ver_teens_admin":      False,
        "acceso_vault":         False,
        "reset_sistema":        False,
        "ver_all_clientes":     True,
        "enviar_campanas":      True,
        "modificar_config_global": True,
    }
}

def tiene_permiso(permiso: str) -> bool:
    """Verifica permiso específico del perfil activo"""
    perfil = get_perfil_activo()
    tipo = perfil.get("tipo", "NEGOCIO")
    return PERMISOS.get(tipo, PERMISOS["NEGOCIO"]).get(permiso, False)

# ─────────────────────────────────────────────────────────────────────────────
# INIT — Al importar, asegura que el perfil ADMIN esté configurado
# ─────────────────────────────────────────────────────────────────────────────
if not os.path.exists(PROFILE_PATH):
    set_perfil_activo("admin")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "info":
            print(json.dumps(info_perfil(), ensure_ascii=False, indent=2))
        elif cmd == "set" and len(sys.argv) > 2:
            p = set_perfil_activo(sys.argv[2])
            print(f"Perfil cambiado a: {p['tipo']}")
        elif cmd == "permisos":
            perfil = get_perfil_activo()
            tipo = perfil.get("tipo","NEGOCIO")
            print(f"\n=== Permisos — {tipo} ===")
            for k, v in PERMISOS.get(tipo, {}).items():
                estado = "✅" if v else "❌"
                print(f"  {estado} {k}")
    else:
        print(json.dumps(get_perfil_activo(), ensure_ascii=False, indent=2))

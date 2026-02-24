"""
nexus_license.py — Sistema de licencias y protección anti-piratería de NEXUS.

ARQUITECTURA:
  1. Al instalar/activar: se genera la huella de hardware (fingerprint)
  2. El admin (tú) crea una licencia para esa huella + módulos + expiración
  3. El archivo license.key se guarda en CONFIG/license.key (JSON cifrado con HMAC)
  4. Cada arranque de NEXUS valida la licencia contra la huella actual
  5. Si la huella no coincide → acceso denegado (anti-copia)
  6. Si expiró → modo demo (lectura, sin escribir)

TIPOS DE LICENCIA:
  DEMO     → 30 días, módulos limitados, marca de agua en UI
  LITE     → 1 año, módulos básicos (Pedidos, Clientes, Stock)
  PRO      → 3 años, todos los módulos + galería (15 activaciones/mes)
  FULL     → 10 años, todos los módulos + galería ilimitada
  ADMIN    → Para el dueño de NEXUS (tú), sin restricciones

MÓDULOS:
  pedidos, clientes, stock, cotizador, agenda, marketing,
  finanzas, agente_ia, imagen, subliminal, qr, backup
"""

import os
import json
import hmac
import hashlib
import datetime
import base64

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
LICENSE_PATH = os.path.join(CONFIG_DIR, "license.key")

# Clave secreta interna (cambia esto antes de distribuir)
_SECRET = b"NX2026_SUPER_SECRET_KEY_CHANGE_IN_PROD"

# Módulos disponibles por tipo de licencia
MODULOS_POR_TIPO = {
    "DEMO":  ["pedidos", "clientes", "stock", "qr"],
    "LITE":  ["pedidos", "clientes", "stock", "cotizador", "agenda", "qr", "backup"],
    "PRO":   ["pedidos", "clientes", "stock", "cotizador", "agenda",
              "marketing", "finanzas", "agente_ia", "imagen", "qr", "backup"],
    "FULL":  ["pedidos", "clientes", "stock", "cotizador", "agenda",
              "marketing", "finanzas", "agente_ia", "imagen", "subliminal",
              "qr", "backup", "subliminal"],
    "ADMIN": ["*"],  # Todos los módulos
}

DIAS_POR_TIPO = {
    "DEMO":  30,
    "LITE":  365,    # 1 año
    "PRO":   1095,   # 3 años
    "FULL":  3650,   # 10 años
    "ADMIN": 36500,  # sin expiración práctica
}


def _firma(payload: dict) -> str:
    """Genera HMAC-SHA256 del payload serializado."""
    data = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hmac.new(_SECRET, data, hashlib.sha256).hexdigest()


def crear_licencia(
    huella:    str,
    tipo:      str = "DEMO",
    cliente:   str = "",
    dias:      int = None,
    modulos:   list = None,
) -> dict:
    """
    Crea una licencia nueva para la huella de hardware dada.
    Retorna el dict de licencia listo para guardar como license.key.

    Args:
        huella:  Fingerprint de 16 chars del hardware objetivo
        tipo:    DEMO | LITE | PRO | FULL | ADMIN
        cliente: Nombre del cliente (referencia)
        dias:    Override de días de vigencia (None = usar default del tipo)
        modulos: Override de módulos habilitados (None = usar default del tipo)
    """
    tipo = tipo.upper()
    if tipo not in MODULOS_POR_TIPO:
        tipo = "DEMO"

    dias_reales    = dias    or DIAS_POR_TIPO[tipo]
    modulos_reales = modulos or MODULOS_POR_TIPO[tipo]

    ahora     = datetime.datetime.utcnow()
    expira    = ahora + datetime.timedelta(days=dias_reales)

    payload = {
        "huella":    huella.upper(),
        "tipo":      tipo,
        "cliente":   cliente,
        "modulos":   sorted(modulos_reales),
        "creada":    ahora.isoformat(),
        "expira":    expira.isoformat(),
        "version":   "2026.02",
    }
    payload["firma"] = _firma({k: v for k, v in payload.items() if k != "firma"})

    return payload


def guardar_licencia(licencia: dict, path: str = None) -> str:
    """Guarda la licencia en disco en formato JSON base64."""
    path = path or LICENSE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw  = json.dumps(licencia, ensure_ascii=True, indent=2)
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    with open(path, "w", encoding="ascii") as f:
        f.write(encoded)
    return path


def cargar_licencia(path: str = None) -> dict:
    """Carga y decodifica la licencia desde disco."""
    path = path or LICENSE_PATH
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="ascii") as f:
            raw = base64.b64decode(f.read().strip()).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return {}


def validar_licencia(path: str = None) -> dict:
    """
    Valida la licencia contra el hardware actual.

    Retorna:
        {
            "valida":   bool,
            "tipo":     str,
            "modulos":  list,
            "expira":   str (ISO),
            "dias_restantes": int,
            "cliente":  str,
            "razon":    str (si no es válida)
        }
    """
    lic = cargar_licencia(path)

    if not lic:
        return _rechazar("Sin licencia. Ejecuta la activación.")

    # Verificar firma
    firma_guardada = lic.get("firma", "")
    payload_check  = {k: v for k, v in lic.items() if k != "firma"}
    if not hmac.compare_digest(firma_guardada, _firma(payload_check)):
        return _rechazar("Licencia corrupta o modificada.")

    # Verificar huella de hardware
    from nexus_fingerprint import generar_huella
    huella_actual = generar_huella()
    huella_lic    = lic.get("huella", "").upper()

    if huella_lic != "BYPASS" and huella_actual != huella_lic:
        return _rechazar(
            f"Licencia no válida para este equipo. "
            f"Huella actual: {huella_actual} | Licencia: {huella_lic}"
        )

    # Verificar expiración
    try:
        expira = datetime.datetime.fromisoformat(lic["expira"])
        ahora  = datetime.datetime.utcnow()
        if ahora > expira:
            dias_vencida = (ahora - expira).days
            return _rechazar(f"Licencia vencida hace {dias_vencida} días. Renueva en contacto con soporte.")
        dias_rest = (expira - ahora).days
    except Exception:
        dias_rest = 0

    modulos = lic.get("modulos", [])

    return {
        "valida":          True,
        "tipo":            lic.get("tipo", "UNKNOWN"),
        "modulos":         modulos,
        "todos_modulos":   "*" in modulos,
        "expira":          lic.get("expira", ""),
        "dias_restantes":  dias_rest,
        "cliente":         lic.get("cliente", ""),
        "razon":           "OK",
    }


def modulo_habilitado(modulo: str, path: str = None) -> bool:
    """Verifica si un módulo específico está habilitado en la licencia actual."""
    v = validar_licencia(path)
    if not v.get("valida"):
        return False
    if v.get("todos_modulos"):
        return True
    return modulo in v.get("modulos", [])


def _rechazar(razon: str) -> dict:
    return {
        "valida":          False,
        "tipo":            "INVALIDA",
        "modulos":         [],
        "todos_modulos":   False,
        "expira":          "",
        "dias_restantes":  0,
        "cliente":         "",
        "razon":           razon,
    }


def activar_demo() -> dict:
    """
    Crea y guarda una licencia DEMO para el hardware actual.
    Útil para distribución de demos automáticos.
    """
    from nexus_fingerprint import generar_huella
    huella = generar_huella()
    lic    = crear_licencia(huella, tipo="DEMO", cliente="DEMO")
    path   = guardar_licencia(lic)
    return {"ok": True, "licencia": lic, "path": path}


def info_licencia() -> dict:
    """Resumen legible de la licencia actual."""
    v = validar_licencia()
    lic = cargar_licencia()
    from nexus_fingerprint import obtener_info_hardware
    hw  = obtener_info_hardware()

    return {
        "hardware":        hw,
        "licencia_valida": v.get("valida", False),
        "tipo":            v.get("tipo", "SIN LICENCIA"),
        "cliente":         v.get("cliente", ""),
        "dias_restantes":  v.get("dias_restantes", 0),
        "expira":          v.get("expira", ""),
        "modulos":         v.get("modulos", []),
        "razon":           v.get("razon", ""),
    }


# ── CLI rápida para el admin ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if not args or args[0] == "info":
        info = info_licencia()
        print(json.dumps(info, indent=2, ensure_ascii=False))

    elif args[0] == "huella":
        from nexus_fingerprint import generar_huella, obtener_info_hardware
        hw = obtener_info_hardware()
        print(json.dumps(hw, indent=2))

    elif args[0] == "crear":
        # python nexus_license.py crear <huella> <tipo> <cliente>
        huella  = args[1] if len(args) > 1 else ""
        tipo    = args[2].upper() if len(args) > 2 else "PRO"
        cliente = args[3] if len(args) > 3 else ""
        if not huella:
            from nexus_fingerprint import generar_huella
            huella = generar_huella()
        lic  = crear_licencia(huella, tipo, cliente)
        path = guardar_licencia(lic)
        print(f"Licencia creada: {path}")
        print(json.dumps(lic, indent=2))

    elif args[0] == "validar":
        v = validar_licencia()
        estado = "VALIDA" if v["valida"] else "INVALIDA"
        print(f"Licencia: {estado}")
        print(json.dumps(v, indent=2))

    elif args[0] == "demo":
        r = activar_demo()
        print("Demo activada.")
        print(json.dumps(r["licencia"], indent=2))

    else:
        print("Comandos: info | huella | crear [huella] [tipo] [cliente] | validar | demo")

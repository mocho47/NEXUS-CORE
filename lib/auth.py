"""
lib/auth.py — NEXUS v3 by Simplex
Autenticación basada en roles y PIN
Generado por Z.ai
"""
import hashlib
import secrets
import time
from typing import Optional

# Roles disponibles en el sistema
ROLES_DB = {
    "admin": {
        "pin_hash": hashlib.sha256("nexus2026".encode()).hexdigest(),
        "permisos": ["*"],  # Acceso total
        "nombre": "Administrador"
    },
    "padre": {
        "pin_hash": None,  # Se configura en onboarding
        "permisos": ["ver_todo", "aprobar_misiones", "gestionar_familia", "ver_reportes"],
        "nombre": "Padre/Madre"
    },
    "hijo": {
        "pin_hash": None,
        "permisos": ["ver_misiones", "completar_misiones", "ver_recompensas"],
        "nombre": "Hijo/Hija"
    },
    "vendedor": {
        "pin_hash": None,
        "permisos": ["ver_pedidos", "crear_pedidos", "ver_clientes", "cotizar"],
        "nombre": "Vendedor"
    },
    "instalador": {
        "pin_hash": None,
        "permisos": ["ver_agenda", "actualizar_estado"],
        "nombre": "Instalador ATF"
    },
    "cliente": {
        "pin_hash": None,
        "permisos": ["ver_estado_pedido"],
        "nombre": "Cliente"
    }
}

# Sesiones activas en memoria (en producción usar Redis)
_sessions: dict = {}

# Intentos fallidos por IP (brute force protection)
_failed_attempts: dict = {}
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(rol: str, pin: str, ip: str = "local") -> bool:
    """Verifica PIN con protección brute force."""
    # Verificar bloqueo
    ahora = time.time()
    if ip in _failed_attempts:
        intentos, ultimo = _failed_attempts[ip]
        if intentos >= MAX_INTENTOS and (ahora - ultimo) < BLOQUEO_SEGUNDOS:
            return False
        elif (ahora - ultimo) >= BLOQUEO_SEGUNDOS:
            del _failed_attempts[ip]

    if rol not in ROLES_DB:
        return False

    pin_hash_guardado = ROLES_DB[rol].get("pin_hash")
    if pin_hash_guardado is None:
        # PIN no configurado aún
        return False

    if _hash_pin(pin) == pin_hash_guardado:
        # Éxito: limpiar intentos fallidos
        if ip in _failed_attempts:
            del _failed_attempts[ip]
        return True
    else:
        # Fallo: registrar intento
        if ip in _failed_attempts:
            intentos, _ = _failed_attempts[ip]
            _failed_attempts[ip] = (intentos + 1, ahora)
        else:
            _failed_attempts[ip] = (1, ahora)
        return False


def set_pin(rol: str, pin: str) -> bool:
    """Establece o cambia el PIN de un rol."""
    if rol not in ROLES_DB:
        return False
    ROLES_DB[rol]["pin_hash"] = _hash_pin(pin)
    return True


def create_session(rol: str, user_id: Optional[str] = None) -> str:
    """Crea una sesión y retorna el token."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "rol": rol,
        "user_id": user_id or rol,
        "creado": time.time(),
        "expira": time.time() + (24 * 3600)  # 24 horas
    }
    return token


def get_session(token: str) -> Optional[dict]:
    """Obtiene la sesión si es válida y no expiró."""
    session = _sessions.get(token)
    if not session:
        return None
    if time.time() > session["expira"]:
        del _sessions[token]
        return None
    return session


def has_permission(token: str, permiso: str) -> bool:
    """Verifica si la sesión tiene el permiso solicitado."""
    session = get_session(token)
    if not session:
        return False
    rol = session["rol"]
    permisos = ROLES_DB.get(rol, {}).get("permisos", [])
    return "*" in permisos or permiso in permisos


def invalidate_session(token: str) -> bool:
    """Cierra una sesión."""
    if token in _sessions:
        del _sessions[token]
        return True
    return False


def get_active_sessions_count() -> int:
    """Retorna número de sesiones activas no expiradas."""
    ahora = time.time()
    activas = [s for s in _sessions.values() if s["expira"] > ahora]
    return len(activas)

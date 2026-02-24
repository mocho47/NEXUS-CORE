"""
nexus_authorization.py — Registro de auditoría de acciones de NEXUS.
No es un sistema de bloqueo. Es un log de trazabilidad.
"""
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH  = os.path.join(BASE_DIR, "logs", "auditoria.log")

SENSITIVE_KEYWORDS = [
    "whatsapp", "facebook", "instagram", "tiktok",
    "login", "sesión", "eliminar", "borrar", "publicar",
    "enviar", "vault", "instalar"
]

class AuditLog:
    def log_action(self, action: str, detail: str = "") -> bool:
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            ts    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tag   = "[SENSIBLE]" if any(k in (action + detail).lower() for k in SENSITIVE_KEYWORDS) else "[INFO]"
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{ts} {tag} {action} | {detail}\n")
        except Exception as e:
            print(f"[AUDIT] Error al loguear: {e}")
        return True

    def request_permission(self, action: str, detail: str = "") -> bool:
        """Alias de compatibilidad con código existente."""
        return self.log_action(action, detail)

authorizer = AuditLog()

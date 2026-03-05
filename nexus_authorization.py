"""
nexus_authorization.py — Registro de auditoría + control de perfiles NEXUS.
Combina log de trazabilidad con verificación de permisos por perfil.
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
    def log_action(self, action: str, detail: str = "", perfil: str = "") -> bool:
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            ts    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tag   = "[SENSIBLE]" if any(k in (action + detail).lower() for k in SENSITIVE_KEYWORDS) else "[INFO]"
            perfil_tag = f"[{perfil}]" if perfil else ""
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{ts} {tag}{perfil_tag} {action} | {detail}\n")
        except Exception as e:
            print(f"[AUDIT] Error al loguear: {e}")
        return True

    def request_permission(self, action: str, detail: str = "") -> bool:
        """Alias de compatibilidad con código existente."""
        try:
            from nexus_profiles import get_perfil_activo, tiene_permiso
            perfil = get_perfil_activo().get("tipo", "NEGOCIO")
            self.log_action(action, detail, perfil)
        except Exception:
            self.log_action(action, detail)
        return True

    def verificar_acceso_personal(self) -> bool:
        """Verifica si el perfil activo puede acceder a módulos personales."""
        try:
            from nexus_profiles import tiene_permiso
            return tiene_permiso("ver_modulos_personales")
        except Exception:
            return False

    def es_admin(self) -> bool:
        """True si el perfil activo es ADMIN."""
        try:
            from nexus_profiles import es_admin
            return es_admin()
        except Exception:
            return False

authorizer = AuditLog()

import json
import os
import re
import time
import webbrowser
from typing import Dict, Optional, Tuple

try:
    import pyautogui
except Exception:
    pyautogui = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
TARGETS_FILE = os.path.join(CONFIG_DIR, "social_targets.json")


def _norm(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _load_targets() -> Dict:
    try:
        if os.path.exists(TARGETS_FILE):
            with open(TARGETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {
        "contacts": {},  # name -> phone(+E164) or raw digits
        "pages": {},     # name -> url
        "settings": {
            "whatsapp_autosend": False,
            "default_country_prefix": "+52",
        },
    }


def _save_targets(data: Dict) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(TARGETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _normalize_phone(raw: str, default_prefix: str = "+52") -> Optional[str]:
    if not raw:
        return None
    s = raw.strip().replace(" ", "")
    if s.startswith("+"):
        # keep + and digits
        digits = "+" + re.sub(r"\D", "", s)
        return digits if len(digits) >= 8 else None
    digits_only = re.sub(r"\D", "", s)
    if not digits_only:
        return None
    # Si ya parece internacional (>= 11-12), lo dejamos.
    if len(digits_only) >= 11:
        return "+" + digits_only
    # Si es local, agregamos prefijo
    pref = default_prefix.strip() if default_prefix else "+52"
    if not pref.startswith("+"):
        pref = "+" + re.sub(r"\D", "", pref)
    return pref + digits_only


class SocialOperator:
    def __init__(self):
        self._targets = _load_targets()

    # ---------- Targets (learn) ----------
    def set_contact(self, name: str, phone: str) -> bool:
        name_key = _norm(name)
        if not name_key:
            return False
        default_prefix = str(self._targets.get("settings", {}).get("default_country_prefix") or "+52")
        normalized = _normalize_phone(phone, default_prefix=default_prefix)
        if not normalized:
            return False
        self._targets.setdefault("contacts", {})[name_key] = normalized
        _save_targets(self._targets)
        return True

    def get_contact_phone(self, name: str) -> Optional[str]:
        name_key = _norm(name)
        return (self._targets.get("contacts") or {}).get(name_key)

    def set_page(self, name: str, url: str) -> bool:
        name_key = _norm(name)
        url = (url or "").strip()
        if not name_key or not url:
            return False
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        self._targets.setdefault("pages", {})[name_key] = url
        _save_targets(self._targets)
        return True

    def get_page_url(self, name: str) -> Optional[str]:
        name_key = _norm(name)
        return (self._targets.get("pages") or {}).get(name_key)

    def set_whatsapp_autosend(self, enabled: bool) -> None:
        self._targets.setdefault("settings", {})["whatsapp_autosend"] = bool(enabled)
        _save_targets(self._targets)

    def get_whatsapp_autosend(self) -> bool:
        return bool(self._targets.get("settings", {}).get("whatsapp_autosend"))

    # ---------- Actions ----------
    def open_facebook_page(self, page_name_or_url: str) -> Tuple[bool, str]:
        text = (page_name_or_url or "").strip()
        if not text:
            return False, "Dime la página o URL."
        url = self.get_page_url(text) or text
        if not (url.startswith("http://") or url.startswith("https://")):
            # fallback
            url = "https://www.facebook.com"
        try:
            webbrowser.open(url)
            return True, "Abriendo Facebook."
        except Exception:
            return False, "No pude abrir el navegador."

    def send_whatsapp_to_contact(self, contact_name: str, message: str, autosend: Optional[bool] = None) -> Tuple[bool, str]:
        if autosend is None:
            autosend = self.get_whatsapp_autosend()

        phone = self.get_contact_phone(contact_name)
        if not phone:
            return False, "No tengo ese contacto. Di: memoriza contacto NOMBRE es +521..."

        return self.send_whatsapp_to_phone(phone, message, autosend=autosend)

    def send_whatsapp_to_phone(self, phone_e164: str, message: str, autosend: bool = False) -> Tuple[bool, str]:
        phone = _normalize_phone(phone_e164, default_prefix=str(self._targets.get("settings", {}).get("default_country_prefix") or "+52"))
        if not phone:
            return False, "Teléfono inválido."

        msg = (message or "").strip()
        if not msg:
            return False, "Mensaje vacío."

        # WhatsApp Web deep link
        # Nota: requiere sesión abierta en web.whatsapp.com
        try:
            import urllib.parse

            url = "https://web.whatsapp.com/send?" + urllib.parse.urlencode({"phone": phone.lstrip("+"), "text": msg})
            webbrowser.open(url)
        except Exception:
            return False, "No pude abrir WhatsApp Web."

        if not autosend:
            return True, "WhatsApp listo con el mensaje. Confirma manualmente en el navegador."

        # Auto-send (best effort) usando Enter
        if pyautogui is None:
            return True, "WhatsApp listo, pero no tengo pyautogui para enviar automático."

        time.sleep(7)
        try:
            pyautogui.press("enter")
            return True, "Mensaje enviado por WhatsApp."
        except Exception:
            return True, "WhatsApp abrió, pero no pude presionar Enter automático."

"""
nexus_meta.py — Integración con Meta APIs (Instagram + WhatsApp Business).

Funciones:
  - post_to_instagram(image_path, caption) — publica foto en Instagram
  - send_whatsapp(to_number, text) — envía mensaje de texto por WhatsApp Business API

Requisitos en .env:
  META_ACCESS_TOKEN=EAAx...        (token de larga duración)
  META_IG_USER_ID=12345678         (ID de tu cuenta Instagram de negocio)
  META_PHONE_NUMBER_ID=12345678    (ID de número de WhatsApp Business)

Referencia API:
  - Instagram: graph.facebook.com/v19.0/{user_id}/media
  - WhatsApp: graph.facebook.com/v19.0/{phone_id}/messages
"""
import os
import json
import logging

log = logging.getLogger("NexusMeta")
API_VERSION = "v19.0"


def _env(key: str) -> str:
    return os.environ.get(key, "").strip()


def _post_json(url: str, payload: dict, token: str) -> dict:
    """HTTP POST con JSON payload usando solo stdlib."""
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log.error(f"[Meta] POST error {url}: {e}")
        return {"error": str(e)}


def post_to_instagram(image_url: str, caption: str) -> dict:
    """
    Publica una imagen en Instagram Business.

    Nota: La API de Meta requiere una URL pública de la imagen,
    no un path local. El proceso es:
      1. Crear un contenedor de media con la URL de la imagen
      2. Publicar el contenedor creado

    Args:
        image_url: URL pública de la imagen (https://...)
        caption: Texto del post con hashtags

    Returns:
        dict con 'id' si fue exitoso, 'error' si falló
    """
    token = _env("META_ACCESS_TOKEN")
    user_id = _env("META_IG_USER_ID")

    if not token or not user_id:
        return {"error": "Configura META_ACCESS_TOKEN y META_IG_USER_ID en .env"}

    base = f"https://graph.facebook.com/{API_VERSION}"

    # Paso 1: Crear contenedor de media
    container = _post_json(
        f"{base}/{user_id}/media",
        {"image_url": image_url, "caption": caption, "access_token": token},
        token,
    )
    if "error" in container and "id" not in container:
        log.error(f"[Instagram] Error creando contenedor: {container}")
        return container

    container_id = container.get("id")
    if not container_id:
        return {"error": f"No se obtuvo container_id: {container}"}

    # Paso 2: Publicar contenedor
    result = _post_json(
        f"{base}/{user_id}/media_publish",
        {"creation_id": container_id, "access_token": token},
        token,
    )
    log.info(f"[Instagram] Publicado: {result}")
    return result


def send_whatsapp(to_number: str, text: str) -> dict:
    """
    Envía un mensaje de texto por WhatsApp Business API.

    Args:
        to_number: Número en formato E.164 (ej: "521XXXXXXXXXX")
        text: Texto del mensaje

    Returns:
        dict con 'messages' si fue exitoso, 'error' si falló
    """
    token = _env("META_ACCESS_TOKEN")
    phone_id = _env("META_PHONE_NUMBER_ID")

    if not token or not phone_id:
        return {"error": "Configura META_ACCESS_TOKEN y META_PHONE_NUMBER_ID en .env"}

    # Normalizar número
    num = str(to_number).strip().replace(" ", "").replace("-", "")
    if num.startswith("+"):
        num = num[1:]

    url = f"https://graph.facebook.com/{API_VERSION}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": num,
        "type": "text",
        "text": {"body": text},
    }
    result = _post_json(url, payload, token)
    log.info(f"[WhatsApp API] → {num}: {result}")
    return result


def send_whatsapp_template(to_number: str, template_name: str, lang: str = "es_MX") -> dict:
    """
    Envía un mensaje de plantilla aprobada por Meta.
    Las plantillas deben estar aprobadas en Meta Business Manager.
    """
    token = _env("META_ACCESS_TOKEN")
    phone_id = _env("META_PHONE_NUMBER_ID")

    if not token or not phone_id:
        return {"error": "Faltan META_ACCESS_TOKEN o META_PHONE_NUMBER_ID"}

    num = str(to_number).strip().replace("+", "")
    url = f"https://graph.facebook.com/{API_VERSION}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": num,
        "type": "template",
        "template": {"name": template_name, "language": {"code": lang}},
    }
    return _post_json(url, payload, token)


# Verificar configuración al importar
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    token = _env("META_ACCESS_TOKEN")
    ig_id = _env("META_IG_USER_ID")
    phone_id = _env("META_PHONE_NUMBER_ID")
    print(f"META_ACCESS_TOKEN:   {'✓ configurado' if token else '✗ falta'}")
    print(f"META_IG_USER_ID:     {'✓ configurado' if ig_id else '✗ falta'}")
    print(f"META_PHONE_NUMBER_ID:{'✓ configurado' if phone_id else '✗ falta'}")

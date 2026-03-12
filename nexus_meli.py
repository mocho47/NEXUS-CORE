# -*- coding: utf-8 -*-
"""
NEXUS MELI — MercadoLibre Integration
Publica, actualiza y responde preguntas en MercadoLibre con IA.

Negocios:
  - ATF (Actualiza Tus Faros): instalacion retrofit + productos Aozoom
  - CanbusFix: accesorios, arneses, kits

Configuracion (.env):
  MELI_CLIENT_ID     = tu app client_id
  MELI_CLIENT_SECRET = tu app client_secret
  MELI_REDIRECT_URI  = http://localhost:8000/api/meli/callback

Para obtener credenciales:
  1. Ir a https://developers.mercadolibre.com.mx
  2. Crear aplicacion
  3. Agregar redirect URI: http://localhost:8000/api/meli/callback
  4. Copiar Client ID y Client Secret al .env
"""

import os
import json
import logging
import httpx
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("C:/nexus/.env")
logger = logging.getLogger("nexus_meli")

# ── CONFIGURACION ─────────────────────────────────────────────────────────────
MELI_CLIENT_ID     = os.getenv("MELI_CLIENT_ID", "")
MELI_CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET", "")
MELI_REDIRECT_URI  = os.getenv("MELI_REDIRECT_URI", "http://localhost:8000/api/meli/callback")
MELI_API           = "https://api.mercadolibre.com"
MELI_AUTH          = "https://auth.mercadolibre.com.mx"

TOKEN_PATH = Path("C:/nexus/CONFIG/meli_token.json")
CATALOG_PATH = Path("C:/nexus/CONFIG/meli_catalog.json")

# ── TOKEN MANAGEMENT ──────────────────────────────────────────────────────────
def _cargar_token() -> dict:
    if TOKEN_PATH.exists():
        try:
            return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {}


def _guardar_token(token: dict):
    token["saved_at"] = datetime.now().isoformat()
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")


def _token_vigente() -> bool:
    t = _cargar_token()
    if not t.get("access_token"):
        return False
    saved = datetime.fromisoformat(t.get("saved_at", "2000-01-01"))
    expires = t.get("expires_in", 21600)
    return datetime.now() < saved + timedelta(seconds=expires - 300)


async def _refresh_token() -> bool:
    """Renueva el token usando refresh_token."""
    t = _cargar_token()
    if not t.get("refresh_token"):
        return False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{MELI_API}/oauth/token", data={
                "grant_type":    "refresh_token",
                "client_id":     MELI_CLIENT_ID,
                "client_secret": MELI_CLIENT_SECRET,
                "refresh_token": t["refresh_token"]
            })
            if r.status_code == 200:
                _guardar_token(r.json())
                return True
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
    return False


async def get_access_token() -> str | None:
    """Retorna un access token válido, renovando si es necesario."""
    if _token_vigente():
        return _cargar_token()["access_token"]
    if await _refresh_token():
        return _cargar_token()["access_token"]
    return None


def get_auth_url() -> str:
    """URL para iniciar el flujo OAuth2 — el usuario debe abrir esto en el browser."""
    return (
        f"{MELI_AUTH}/authorization?response_type=code"
        f"&client_id={MELI_CLIENT_ID}"
        f"&redirect_uri={MELI_REDIRECT_URI}"
    )


async def exchange_code(code: str) -> dict:
    """Intercambia el authorization code por access_token + refresh_token."""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{MELI_API}/oauth/token", data={
            "grant_type":    "authorization_code",
            "client_id":     MELI_CLIENT_ID,
            "client_secret": MELI_CLIENT_SECRET,
            "code":          code,
            "redirect_uri":  MELI_REDIRECT_URI
        })
        if r.status_code == 200:
            token = r.json()
            _guardar_token(token)
            return {"ok": True, "seller_id": token.get("user_id")}
        return {"ok": False, "error": r.text}


# ── CATALOGO DE PRODUCTOS ─────────────────────────────────────────────────────
CATALOGO_ATF = [
    {
        "id": "aozoom_x4",
        "titulo": "Focos LED Biled Aozoom X4 Retrofit - Instalación Profesional GDL",
        "descripcion": (
            "Kit completo Biled Aozoom X4 con instalación profesional incluida en Guadalajara. "
            "El más vendido. Luz blanca de alta intensidad, larga vida útil. "
            "Instalación garantizada en 2 hrs. CanbusFix certificado. "
            "Precio incluye mano de obra. Garantía 1 año."
        ),
        "precio": 2699,
        "precio_dist": 1990,
        "categoria_meli": "MLM1051",  # Accesorios para autos
        "condicion": "new",
        "disponible": 10,
        "imagenes": [],
        "atributos": {
            "marca": "Aozoom",
            "modelo": "X4",
            "tipo": "Biled LED",
            "garantia": "12 meses"
        }
    },
    {
        "id": "aozoom_x1",
        "titulo": "Focos LED Biled Aozoom X1 Premium - Retrofit con Instalación GDL",
        "descripcion": (
            "Kit Biled Aozoom X1 con lente proyector de alta precisión. "
            "Instalación profesional incluida en Guadalajara. "
            "Ideal para faros con espacio reducido. Haz definido. Garantía 1 año."
        ),
        "precio": 3149,
        "precio_dist": 2350,
        "categoria_meli": "MLM1051",
        "condicion": "new",
        "disponible": 5,
        "imagenes": [],
        "atributos": {"marca": "Aozoom", "modelo": "X1", "tipo": "Biled LED"}
    },
    {
        "id": "retrofit_basico",
        "titulo": "Instalación Retrofit Faros LED Básico - Guadalajara",
        "descripcion": (
            "Instalación básica de faros LED para tu vehículo en Guadalajara. "
            "Incluye mano de obra. Trae tu kit o adquiere el nuestro. "
            "Servicio profesional, taller certificado CanbusFix."
        ),
        "precio": 800,
        "precio_dist": 0,
        "categoria_meli": "MLM1051",
        "condicion": "new",
        "disponible": 20,
        "imagenes": [],
        "atributos": {"tipo_servicio": "instalacion", "nivel": "basico"}
    },
    {
        "id": "retrofit_pro",
        "titulo": "Instalación Retrofit Faros LED Pro - Alineación y Calibración GDL",
        "descripcion": (
            "Instalación profesional con alineación y calibración de faros LED. "
            "Incluye revisión de arnés, ajuste de haz y prueba de camino. "
            "Garantía de instalación incluida."
        ),
        "precio": 2500,
        "precio_dist": 0,
        "categoria_meli": "MLM1051",
        "condicion": "new",
        "disponible": 20,
        "imagenes": [],
        "atributos": {"tipo_servicio": "instalacion", "nivel": "pro"}
    }
]


def guardar_catalogo():
    CATALOG_PATH.write_text(json.dumps(CATALOGO_ATF, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_catalogo() -> list:
    if CATALOG_PATH.exists():
        try:
            return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return CATALOGO_ATF


# ── PUBLICAR PRODUCTO ─────────────────────────────────────────────────────────
async def publicar_producto(producto_id: str) -> dict:
    """Publica un producto del catálogo en MercadoLibre."""
    token = await get_access_token()
    if not token:
        return {"ok": False, "error": "Sin autenticacion. Ve a /api/meli/auth primero."}

    catalogo = cargar_catalogo()
    producto = next((p for p in catalogo if p["id"] == producto_id), None)
    if not producto:
        return {"ok": False, "error": f"Producto '{producto_id}' no encontrado en catalogo"}

    payload = {
        "title":        producto["titulo"],
        "category_id":  producto.get("categoria_meli", "MLM1051"),
        "price":        producto["precio"],
        "currency_id":  "MXN",
        "available_quantity": producto.get("disponible", 5),
        "buying_mode":  "buy_it_now",
        "condition":    producto.get("condicion", "new"),
        "listing_type_id": "gold_special",
        "description":  {"plain_text": producto["descripcion"]},
        "pictures":     [{"source": img} for img in producto.get("imagenes", []) if img],
        "attributes":   [
            {"id": k.upper(), "value_name": str(v)}
            for k, v in producto.get("atributos", {}).items()
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{MELI_API}/items",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code in (200, 201):
                data = r.json()
                return {
                    "ok": True,
                    "item_id": data.get("id"),
                    "permalink": data.get("permalink"),
                    "titulo": producto["titulo"],
                    "precio": producto["precio"]
                }
            return {"ok": False, "error": r.text, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def publicar_catalogo_completo() -> dict:
    """Publica todos los productos del catálogo en MercadoLibre."""
    resultados = []
    for producto in cargar_catalogo():
        r = await publicar_producto(producto["id"])
        resultados.append({
            "producto": producto["id"],
            "ok": r.get("ok"),
            "item_id": r.get("item_id"),
            "permalink": r.get("permalink"),
            "error": r.get("error")
        })
    publicados = sum(1 for r in resultados if r["ok"])
    return {"ok": True, "publicados": publicados, "total": len(resultados), "detalle": resultados}


# ── PREGUNTAS Y RESPUESTAS CON IA ─────────────────────────────────────────────
async def obtener_preguntas() -> list:
    """Obtiene preguntas sin responder de todos los listings."""
    token = await get_access_token()
    if not token:
        return []
    try:
        async with httpx.AsyncClient() as client:
            # Obtener seller_id
            me = await client.get(f"{MELI_API}/users/me",
                                  headers={"Authorization": f"Bearer {token}"})
            seller_id = me.json().get("id")

            r = await client.get(
                f"{MELI_API}/questions/search?status=UNANSWERED&seller_id={seller_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            data = r.json()
            return data.get("questions", [])
    except Exception as e:
        logger.error(f"Error obteniendo preguntas: {e}")
        return []


async def responder_pregunta_ia(question_id: int, pregunta_texto: str) -> dict:
    """Genera respuesta con IA y la publica en MercadoLibre."""
    from nexus_cerebro import get_cerebro

    # Generar respuesta con el cerebro NEXUS
    prompt = (
        f"Soy vendedor de retrofit faros LED en Guadalajara (ATF by Simplex). "
        f"Un cliente pregunta en MercadoLibre: '{pregunta_texto}'. "
        f"Responde de manera profesional, breve (2-3 oraciones), orientada a venta. "
        f"Menciona si aplica: garantia, instalacion incluida, disponibilidad. "
        f"No inventes datos que no tienes."
    )
    resultado = get_cerebro().pensar(prompt)
    respuesta = resultado.get("respuesta", "")

    if not respuesta:
        return {"ok": False, "error": "Sin respuesta del cerebro"}

    # Publicar la respuesta
    token = await get_access_token()
    if not token:
        return {"ok": False, "error": "Sin autenticacion", "respuesta_generada": respuesta}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{MELI_API}/answers",
                json={"question_id": question_id, "text": respuesta},
                headers={"Authorization": f"Bearer {token}"}
            )
            return {
                "ok": r.status_code in (200, 201),
                "question_id": question_id,
                "respuesta": respuesta,
                "status": r.status_code
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "respuesta_generada": respuesta}


async def auto_responder_preguntas() -> dict:
    """Revisa y responde automáticamente todas las preguntas pendientes."""
    preguntas = await obtener_preguntas()
    if not preguntas:
        return {"ok": True, "respondidas": 0, "msg": "Sin preguntas pendientes"}

    respondidas = []
    for q in preguntas[:10]:  # max 10 a la vez
        resultado = await responder_pregunta_ia(q["id"], q.get("text", ""))
        respondidas.append({
            "id": q["id"],
            "pregunta": q.get("text", "")[:80],
            "ok": resultado.get("ok"),
            "respuesta": resultado.get("respuesta", "")[:100]
        })

    ok_count = sum(1 for r in respondidas if r["ok"])
    return {
        "ok": True,
        "respondidas": ok_count,
        "total_preguntas": len(preguntas),
        "detalle": respondidas
    }


# ── ESTADO ────────────────────────────────────────────────────────────────────
def estado_meli() -> dict:
    tiene_credenciales = bool(MELI_CLIENT_ID and MELI_CLIENT_SECRET)
    tiene_token = bool(_cargar_token().get("access_token"))
    token_vigente = _token_vigente() if tiene_token else False

    return {
        "configurado": tiene_credenciales,
        "autenticado": tiene_token,
        "token_vigente": token_vigente,
        "catalogo_productos": len(cargar_catalogo()),
        "auth_url": get_auth_url() if tiene_credenciales else None,
        "instrucciones": (
            "1. Agrega MELI_CLIENT_ID y MELI_CLIENT_SECRET al .env\n"
            "2. Ve a /api/meli/auth en el browser para autorizar\n"
            "3. Usa /api/meli/publicar para subir productos"
        ) if not tiene_credenciales else None
    }

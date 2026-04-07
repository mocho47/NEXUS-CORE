"""
lib/notificaciones.py — NEXUS v3 by Simplex
Telegram + SSE (Server-Sent Events) para notificaciones en tiempo real
Generado por Z.ai
"""
import asyncio
import json
import os
import time
from typing import AsyncGenerator

import aiohttp
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Cola de eventos SSE por cliente
_sse_queues: dict[str, asyncio.Queue] = {}


async def send_telegram(mensaje: str, chat_id: str = None) -> bool:
    """Envía mensaje a Telegram. Retorna True si fue exitoso."""
    token = TELEGRAM_TOKEN
    cid = chat_id or TELEGRAM_CHAT_ID

    if not token or not cid:
        print(f"[NOTIF] Telegram no configurado. Mensaje: {mensaje}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": mensaje,
        "parse_mode": "HTML"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return True
                else:
                    text = await resp.text()
                    print(f"[NOTIF] Telegram error {resp.status}: {text}")
                    return False
    except Exception as e:
        print(f"[NOTIF] Telegram excepción: {e}")
        return False


async def notificar(evento: str, datos: dict, canal: str = "global") -> None:
    """
    Envía notificación a todos los clientes SSE suscritos al canal.
    También intenta enviar a Telegram si el evento es crítico.
    """
    mensaje_sse = {
        "evento": evento,
        "datos": datos,
        "timestamp": time.time()
    }

    # Enviar a todos los clientes SSE del canal
    clientes_canal = [k for k in _sse_queues if k.startswith(canal)]
    for cliente_id in clientes_canal:
        try:
            await _sse_queues[cliente_id].put(mensaje_sse)
        except Exception:
            pass

    # Telegram para eventos críticos
    eventos_criticos = ["mision_completada", "pago_registrado", "pedido_nuevo", "alerta_sistema"]
    if evento in eventos_criticos and TELEGRAM_TOKEN:
        texto = f"🔔 <b>NEXUS</b> — {evento}\n"
        for k, v in datos.items():
            texto += f"• {k}: {v}\n"
        asyncio.create_task(send_telegram(texto))


def subscribe_sse(cliente_id: str) -> asyncio.Queue:
    """Registra un cliente SSE y retorna su cola de eventos."""
    q = asyncio.Queue(maxsize=50)
    _sse_queues[cliente_id] = q
    return q


def unsubscribe_sse(cliente_id: str) -> None:
    """Elimina la suscripción SSE de un cliente."""
    _sse_queues.pop(cliente_id, None)


async def event_generator(cliente_id: str) -> AsyncGenerator[str, None]:
    """
    Generador async para streaming SSE.
    Uso en FastAPI: return StreamingResponse(event_generator(id), media_type="text/event-stream")
    """
    q = subscribe_sse(cliente_id)
    try:
        # Ping inicial
        yield f"data: {json.dumps({'evento': 'connected', 'cliente': cliente_id})}\n\n"

        while True:
            try:
                mensaje = await asyncio.wait_for(q.get(), timeout=30.0)
                yield f"data: {json.dumps(mensaje)}\n\n"
            except asyncio.TimeoutError:
                # Keepalive ping cada 30s
                yield f"data: {json.dumps({'evento': 'ping', 'ts': time.time()})}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        unsubscribe_sse(cliente_id)


def get_subscribers_count() -> int:
    """Retorna número de clientes SSE activos."""
    return len(_sse_queues)

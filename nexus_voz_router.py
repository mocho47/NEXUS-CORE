# -*- coding: utf-8 -*-
"""
NEXUS VOZ Router v2
Se adjunta a nexus_server.py con: app.include_router(voz_router)
Expone:
  WS  /ws/voz          — WebSocket de voz en tiempo real
  POST /api/voz2/texto  — Texto directo (sin micrófono)
  GET  /api/voz2/estado — Estado del motor
  GET  /api/voz2/mics   — Lista de micrófonos disponibles
  POST /api/voz2/limpiar — Reinicia historial de conversación
  GET  /nexus-ear2      — Interfaz visual
"""

import base64
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from nexus_voz_v2 import get_engine

logger = logging.getLogger("nexus_voz_router")
router = APIRouter()
templates = Jinja2Templates(directory="WEB/templates")


# ── WEBSOCKET VOZ ─────────────────────────────────────────────────────────────
@router.websocket("/ws/voz")
async def websocket_voz(ws: WebSocket):
    """
    Protocolo WebSocket:
    Cliente → Servidor:
      {"tipo": "audio", "data": "<base64 webm>", "fmt": "webm"}
      {"tipo": "texto", "data": "mensaje escrito"}
      {"tipo": "ping"}

    Servidor → Cliente:
      {"tipo": "transcripcion", "texto": "..."}
      {"tipo": "respuesta", "texto": "...", "accion": "...", "params": {...}}
      {"tipo": "audio", "data": "<base64 mp3>"}
      {"tipo": "error", "msg": "..."}
      {"tipo": "pong"}
    """
    await ws.accept()
    engine = get_engine()
    logger.info("WebSocket voz conectado")

    try:
        while True:
            msg = await ws.receive_json()
            tipo = msg.get("tipo", "")

            if tipo == "ping":
                await ws.send_json({"tipo": "pong"})

            elif tipo == "audio":
                # Audio del navegador (webm/opus)
                fmt = msg.get("fmt", "webm")
                raw = base64.b64decode(msg["data"])

                # Notificar que estamos procesando
                await ws.send_json({"tipo": "procesando"})

                resultado = await engine.procesar_audio(raw, fmt)

                # Enviar transcripción
                if resultado["transcripcion"]:
                    await ws.send_json({
                        "tipo": "transcripcion",
                        "texto": resultado["transcripcion"]
                    })

                # Enviar respuesta texto
                await ws.send_json({
                    "tipo": "respuesta",
                    "texto": resultado["respuesta"],
                    "accion": resultado["accion"],
                    "params": resultado.get("params", {})
                })

                # Enviar audio TTS si existe
                if resultado.get("audio"):
                    audio_b64 = base64.b64encode(resultado["audio"]).decode()
                    await ws.send_json({
                        "tipo": "audio",
                        "data": audio_b64
                    })

            elif tipo == "texto":
                texto = msg.get("data", "").strip()
                if texto:
                    await ws.send_json({"tipo": "procesando"})
                    resultado = await engine.procesar_texto(texto)

                    await ws.send_json({
                        "tipo": "respuesta",
                        "texto": resultado["respuesta"],
                        "accion": resultado["accion"],
                        "params": resultado.get("params", {})
                    })

                    if resultado.get("audio"):
                        audio_b64 = base64.b64encode(resultado["audio"]).decode()
                        await ws.send_json({
                            "tipo": "audio",
                            "data": audio_b64
                        })

    except WebSocketDisconnect:
        logger.info("WebSocket voz desconectado")
    except Exception as e:
        logger.error(f"Error WebSocket voz: {e}")
        try:
            await ws.send_json({"tipo": "error", "msg": str(e)})
        except:
            pass


# ── REST API ──────────────────────────────────────────────────────────────────
@router.post("/api/voz2/texto")
async def api_texto(request: Request):
    body = await request.json()
    texto = body.get("texto", "").strip()
    if not texto:
        return JSONResponse({"ok": False, "error": "texto vacío"})
    engine = get_engine()
    resultado = await engine.procesar_texto(texto)
    r = {
        "ok": True,
        "transcripcion": resultado["transcripcion"],
        "accion": resultado["accion"],
        "respuesta": resultado["respuesta"],
        "params": resultado.get("params", {})
    }
    if resultado.get("audio"):
        r["audio_b64"] = base64.b64encode(resultado["audio"]).decode()
    return JSONResponse(r)


@router.get("/api/voz2/estado")
async def api_estado():
    engine = get_engine()
    return JSONResponse({
        "ok": True,
        "whisper_cargado": engine._whisper is not None,
        "turnos_historial": len(engine._historial) // 2,
        "mics_disponibles": len(engine.dispositivos_mic)
    })


@router.get("/api/voz2/mics")
async def api_mics():
    engine = get_engine()
    return JSONResponse({"ok": True, "mics": engine.dispositivos_mic})


@router.post("/api/voz2/limpiar")
async def api_limpiar():
    get_engine().limpiar_historial()
    return JSONResponse({"ok": True, "msg": "Historial limpiado"})


# ── INTERFAZ ──────────────────────────────────────────────────────────────────
@router.get("/nexus-ear2")
async def pagina_ear2(request: Request):
    return templates.TemplateResponse("nexus_ear_v2.html", {"request": request})

@router.get("/mic-test")
async def pagina_mic_test(request: Request):
    return templates.TemplateResponse("mic_test.html", {"request": request})

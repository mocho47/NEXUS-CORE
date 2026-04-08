"""
motor_redes.py — Control total de redes sociales
Puerto 8010

Administra todas las plataformas desde NEXUS:
- Instagram: publicar Reel, Historia, Post, leer DMs, responder
- Facebook: publicar en página, grupos automotrices
- TikTok: preparar video (Playwright para publicación)
- WhatsApp: enviar mensajes via Twilio Business
- YouTube: subir videos (Google API)
- Telegram: alertas y notificaciones (ya activo en notificaciones.py)

Todos los SDKs están instalados y verificados.
"""

import os, asyncio, json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

MEDIA_DIR = Path("C:/NEXUS_v3_NEW/output")
ATF_VIDEOS_DIR = Path("E:/SIMPLEX_DATA/MEDIA/atf_videos")
LOGS_DIR = Path("C:/NEXUS_v3_NEW/logs")

app = FastAPI(title="NEXUS Motor Redes", version="3.0")

# ═══════════════════════════════════════════════
# INSTAGRAM (instagrapi 2.3.0 — ACTIVO)
# ═══════════════════════════════════════════════
_ig_client = None

def get_ig_client():
    global _ig_client
    if _ig_client:
        return _ig_client
    try:
        from instagrapi import Client
        cl = Client()
        session_file = Path("C:/NEXUS_v3_NEW/data/ig_session.json")
        if session_file.exists():
            cl.load_settings(session_file)
            cl.get_timeline_feed()  # verifica sesion
        else:
            cl.login(os.getenv('IG_USER'), os.getenv('IG_PASS'))
            cl.dump_settings(session_file)
        _ig_client = cl
        return cl
    except Exception as e:
        raise HTTPException(500, f"Error Instagram login: {e}")

class PublicarRequest(BaseModel):
    video_path: Optional[str] = None   # si no se da, toma el siguiente rotativo
    caption: Optional[str] = None
    historia: Optional[bool] = True    # publicar también como historia
    tipo: Optional[str] = "reel"       # reel | post | historia

class MensajeRequest(BaseModel):
    usuario: str    # username Instagram o número de teléfono
    mensaje: str

@app.post("/redes/instagram/publicar")
async def publicar_instagram(req: PublicarRequest):
    """
    Publica en Instagram. Si no se da video_path, rota automáticamente
    los videos de E:/SIMPLEX_DATA/MEDIA/atf_videos/
    """
    # Seleccionar video
    if req.video_path:
        video = Path(req.video_path)
    else:
        video = _siguiente_video_atf()

    if not video or not video.exists():
        return {"ok": False, "error": f"Video no encontrado: {video}"}

    # Caption por defecto si no se da
    caption = req.caption or _caption_rotativo()

    try:
        cl = get_ig_client()
        resultado = {}

        if req.tipo in ("reel", "post"):
            media = cl.clip_upload(video, caption)
            resultado["reel_id"] = str(media.pk)
            resultado["reel"] = True

        if req.historia:
            cl.photo_upload_to_story(video) if video.suffix in ('.jpg', '.png') \
                else cl.video_upload_to_story(video)
            resultado["historia"] = True

        # Log
        _log_publicacion("instagram", str(video), caption, resultado)

        return {"ok": True, "video": str(video), "resultado": resultado}

    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/redes/instagram/dms")
async def leer_dms(limite: int = 20):
    """Lee mensajes directos sin responder."""
    try:
        cl = get_ig_client()
        threads = cl.direct_threads(amount=limite)
        mensajes = []
        for thread in threads:
            if not thread.read_state:
                ultimo = thread.messages[0] if thread.messages else None
                mensajes.append({
                    "thread_id": str(thread.id),
                    "usuario": thread.users[0].username if thread.users else "?",
                    "ultimo_msg": ultimo.text if ultimo else "",
                    "timestamp": str(ultimo.timestamp) if ultimo else ""
                })
        return {"ok": True, "mensajes": mensajes, "total": len(mensajes)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/redes/instagram/responder")
async def responder_dm(req: MensajeRequest):
    """Responde un DM de Instagram."""
    try:
        cl = get_ig_client()
        user = cl.user_info_by_username(req.usuario)
        cl.direct_send(req.mensaje, [user.pk])
        return {"ok": True, "enviado_a": req.usuario}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/redes/instagram/stats")
async def stats_instagram():
    """Estadísticas básicas de la cuenta."""
    try:
        cl = get_ig_client()
        user_id = cl.user_id
        info = cl.user_info(user_id)
        return {
            "ok": True,
            "usuario": info.username,
            "seguidores": info.follower_count,
            "seguidos": info.following_count,
            "posts": info.media_count
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════
# FACEBOOK (Graph API o Playwright para grupos)
# ═══════════════════════════════════════════════
@app.post("/redes/facebook/publicar_pagina")
async def publicar_facebook_pagina(req: PublicarRequest):
    """Publica en la página de Facebook ATF."""
    import httpx

    token = os.getenv('FB_PAGE_TOKEN')
    page_id = os.getenv('FB_PAGE_ID')

    if not token or not page_id:
        return {"ok": False, "error": "FB_PAGE_TOKEN o FB_PAGE_ID no configurados en .env"}

    caption = req.caption or _caption_rotativo()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if req.video_path:
                # Subir video
                with open(req.video_path, 'rb') as f:
                    r = await client.post(
                        f"https://graph.facebook.com/{page_id}/videos",
                        data={"description": caption, "access_token": token},
                        files={"source": f}
                    )
            else:
                # Solo texto/link
                r = await client.post(
                    f"https://graph.facebook.com/{page_id}/feed",
                    data={"message": caption, "access_token": token}
                )

        data = r.json()
        if 'id' in data:
            _log_publicacion("facebook", req.video_path or "", caption, data)
            return {"ok": True, "post_id": data['id']}
        else:
            return {"ok": False, "error": data.get('error', {}).get('message', str(data))}

    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/redes/facebook/grupos")
async def publicar_grupos_fb(req: PublicarRequest):
    """
    Prepara publicación para grupos de Facebook automotrices de GDL.
    Abre el navegador con Playwright listo para publicar.
    """
    caption = req.caption or _caption_rotativo()
    video = req.video_path or str(_siguiente_video_atf() or "")

    # Por restricciones de Meta, esto abre el navegador
    script = f"""
import asyncio
from playwright.async_api import async_playwright

GRUPOS_ATF_GDL = [
    "https://www.facebook.com/groups/automovilesguadalajara",
    "https://www.facebook.com/groups/jaliscoautos",
]

async def publicar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        for grupo in GRUPOS_ATF_GDL:
            await page.goto(grupo)
            await asyncio.sleep(3)
            # El usuario completa la publicación manualmente
            print(f"Abriendo: {{grupo}}")
        input("Presiona Enter cuando hayas publicado en todos los grupos...")
        await browser.close()

asyncio.run(publicar())
"""
    script_path = Path("C:/NEXUS_v3_NEW/output/publicar_grupos_fb.py")
    script_path.write_text(script, encoding='utf-8')

    import subprocess
    subprocess.Popen(f'start "FB Grupos" python "{script_path}"', shell=True)

    return {
        "ok": True,
        "mensaje": "Navegador abriendo grupos automotrices GDL",
        "caption_preparado": caption,
        "video": video,
        "nota": "Completa la publicación en el navegador"
    }

# ═══════════════════════════════════════════════
# TIKTOK (Playwright — API oficial muy restrictiva)
# ═══════════════════════════════════════════════
@app.post("/redes/tiktok/preparar")
async def preparar_tiktok(req: PublicarRequest):
    """
    Prepara video para TikTok: convierte a vertical 9:16, agrega caption.
    Luego abre TikTok en el navegador con el video listo para pegar.
    """
    import httpx, subprocess

    video = Path(req.video_path) if req.video_path else _siguiente_video_atf()
    if not video or not video.exists():
        return {"ok": False, "error": "Video no encontrado"}

    # Convertir a vertical 1080x1920 para TikTok
    output = Path("C:/NEXUS_v3_NEW/output") / f"tiktok_{video.stem}.mp4"

    ffmpeg_cmd = (
        f'ffmpeg -i "{video}" '
        f'-vf "scale=1080:1920:force_original_aspect_ratio=decrease,'
        f'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" '
        f'-c:v libx264 -crf 23 -preset fast '
        f'-c:a aac -b:a 128k '
        f'-y "{output}" 2>/dev/null'
    )

    r = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True)
    if r.returncode != 0 or not output.exists():
        return {"ok": False, "error": "ffmpeg falló convirtiendo el video"}

    caption = req.caption or _caption_rotativo()

    # Copiar caption al clipboard
    subprocess.run(f'echo {caption} | clip', shell=True)

    # Abrir TikTok
    subprocess.Popen('start "" https://www.tiktok.com/upload', shell=True)

    return {
        "ok": True,
        "video_listo": str(output),
        "caption": caption,
        "mensaje": "Video convertido a vertical. Caption copiado al clipboard. TikTok abierto.",
        "siguiente_paso": "Arrastra el video a TikTok y pega el caption (Ctrl+V)"
    }

# ═══════════════════════════════════════════════
# WHATSAPP (Twilio Business API)
# ═══════════════════════════════════════════════
class WhatsAppRequest(BaseModel):
    telefono: str     # formato: +521XXXXXXXXXX
    mensaje: str
    media_url: Optional[str] = None  # URL pública de imagen/video

@app.post("/redes/whatsapp/enviar")
async def enviar_whatsapp(req: WhatsAppRequest):
    """Envía mensaje WhatsApp via Twilio Business API."""
    try:
        from twilio.rest import Client as TwilioClient
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token  = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_WA_NUMBER', 'whatsapp:+14155238886')  # sandbox

        if not account_sid or not auth_token:
            return {"ok": False, "error": "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN no configurados"}

        client = TwilioClient(account_sid, auth_token)
        kwargs = {
            "from_": from_number,
            "to": f"whatsapp:{req.telefono}",
            "body": req.mensaje
        }
        if req.media_url:
            kwargs["media_url"] = [req.media_url]

        message = client.messages.create(**kwargs)
        return {"ok": True, "sid": message.sid, "estado": message.status}

    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/redes/whatsapp/cotizacion_atf")
async def enviar_cotizacion_atf(
    telefono: str,
    kit: str = "X4",
    nombre: str = "cliente"
):
    """Envía cotización ATF por WhatsApp con formato listo."""
    precios = {
        "X1": (2350, 3149), "X2": (2050, 2799), "X3": (2350, 3149),
        "X4": (1990, 2699), "X5": (1199, 1599), "X6": (1199, 1599),
        "X7": (1550, 2069)
    }
    if kit not in precios:
        return {"ok": False, "error": f"Kit {kit} no encontrado. Disponibles: {list(precios.keys())}"}

    dist, pub = precios[kit]
    total = pub + 500  # + instalación

    mensaje = f"""Hola {nombre}!

Aquí tu cotización ATF 🚗💡

*Kit Aozoom {kit}*
• Precio del kit: ${pub:,}
• Instalación profesional: $500
• *Total: ${total:,}*

Incluye:
✅ Kit bi-LED Aozoom original
✅ Garantía de por vida
✅ Instalación en Guadalajara
✅ Fotos del resultado

¿Te interesa agendar? 📅
Tel: {os.getenv('ATF_PHONE', '3326148674')}"""

    return await enviar_whatsapp(WhatsAppRequest(
        telefono=telefono, mensaje=mensaje
    ))

# ═══════════════════════════════════════════════
# GENERADOR DE CAPTIONS CON IA (Groq SDK nativo)
# ═══════════════════════════════════════════════
class CaptionRequest(BaseModel):
    plataforma: str = "instagram"   # instagram | tiktok | facebook | youtube
    tema: str = "faros LED ATF"
    tono: str = "profesional"       # profesional | divertido | urgente | técnico
    incluir_cta: bool = True
    idioma: str = "es"

@app.post("/redes/generar_caption")
async def generar_caption(req: CaptionRequest):
    """Genera caption optimizado para cada plataforma usando Groq."""
    especificaciones = {
        "instagram": "máximo 2200 caracteres, 5-10 hashtags relevantes, emoji moderado, CTA al final",
        "tiktok":    "máximo 150 caracteres, 3-5 hashtags trending, gancho en primera línea",
        "facebook":  "máximo 500 caracteres, tono conversacional, sin exceso de hashtags, incluir emoji",
        "youtube":   "título máximo 70 caracteres + descripción 200 palabras con palabras clave SEO",
    }
    specs = especificaciones.get(req.plataforma, especificaciones["instagram"])

    prompt = f"""Genera un caption de marketing para {req.plataforma} sobre: {req.tema}
Tono: {req.tono}
Especificaciones: {specs}
Incluir llamada a la acción: {'Sí' if req.incluir_cta else 'No'}
Negocio: ATF - Instalación de faros LED Aozoom en Guadalajara
Teléfono: {os.getenv('ATF_PHONE', '3323530146')}
Responde SOLO con el caption listo para copiar y pegar. Sin explicaciones."""

    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=30)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.8,
        )
        caption = response.choices[0].message.content.strip()
        return {"ok": True, "caption": caption, "plataforma": req.plataforma, "via": "Groq"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# OPTIMIZADOR DE IMÁGENES POR PLATAFORMA (Pillow)
# ═══════════════════════════════════════════════
SPECS_PLATAFORMA = {
    "instagram_post":    (1080, 1080),
    "instagram_reel":    (1080, 1920),
    "instagram_historia":(1080, 1920),
    "facebook_post":     (1200, 630),
    "facebook_portada":  (820, 312),
    "tiktok":            (1080, 1920),
    "youtube_thumbnail": (1280, 720),
    "whatsapp":          (1024, 1024),
}

class OptimizarRequest(BaseModel):
    imagen_path: str
    plataforma: str = "instagram_post"  # ver SPECS_PLATAFORMA
    dpi: int = 72           # pantalla=72, impresión=300
    calidad: int = 90

@app.post("/redes/optimizar_imagen")
async def optimizar_imagen(req: OptimizarRequest):
    """Redimensiona y optimiza imagen para las especificaciones exactas de la plataforma."""
    from PIL import Image, ImageOps
    from pathlib import Path as _P

    ruta = _P(req.imagen_path)
    if not ruta.exists():
        return {"ok": False, "error": f"Archivo no encontrado: {req.imagen_path}"}

    specs = SPECS_PLATAFORMA.get(req.plataforma)
    if not specs:
        return {"ok": False, "error": f"Plataforma desconocida. Opciones: {list(SPECS_PLATAFORMA.keys())}"}

    w_target, h_target = specs
    OUTPUT = _P("C:/NEXUS_v3_NEW/output")
    OUTPUT.mkdir(exist_ok=True)
    salida = OUTPUT / f"{ruta.stem}_{req.plataforma}.jpg"

    try:
        img = Image.open(str(ruta)).convert("RGB")
        # Redimensionar manteniendo aspecto y rellenando con negro si es necesario
        img = ImageOps.fit(img, (w_target, h_target), method=Image.LANCZOS, centering=(0.5, 0.5))
        img.save(str(salida), "JPEG", dpi=(req.dpi, req.dpi), quality=req.calidad, optimize=True)
        return {
            "ok": True,
            "salida": str(salida),
            "dimensiones": f"{w_target}x{h_target}px",
            "plataforma": req.plataforma,
            "dpi": req.dpi,
            "tamaño_kb": round(salida.stat().st_size / 1024, 1)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# YOUTUBE (google-api-python-client)
# ═══════════════════════════════════════════════
class YouTubeRequest(BaseModel):
    video_path: str
    titulo: str
    descripcion: Optional[str] = None
    tags: Optional[List[str]] = None
    privacidad: str = "public"   # public | unlisted | private

@app.post("/redes/youtube/subir")
async def subir_youtube(req: YouTubeRequest):
    """Sube video a YouTube usando Google API."""
    token_file = Path("C:/NEXUS_v3_NEW/data/youtube_token.json")
    if not token_file.exists():
        return {
            "ok": False,
            "error": "No autenticado con YouTube.",
            "instruccion": "Obtén credenciales OAuth2 en console.cloud.google.com y guárdalas en data/youtube_token.json"
        }
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(token_file))
        yt = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": req.titulo,
                "description": req.descripcion or req.titulo,
                "tags": req.tags or ["ATF", "faros", "LED", "Guadalajara", "Aozoom"],
                "categoryId": "2"  # Autos y vehículos
            },
            "status": {"privacyStatus": req.privacidad}
        }
        media = MediaFileUpload(req.video_path, chunksize=-1, resumable=True)
        request = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = request.execute()
        return {
            "ok": True,
            "video_id": response["id"],
            "url": f"https://youtu.be/{response['id']}",
            "titulo": req.titulo
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# TELEGRAM (httpx — sin SDK extra necesario)
# ═══════════════════════════════════════════════
class TelegramRequest(BaseModel):
    mensaje: str
    imagen_path: Optional[str] = None

@app.post("/redes/telegram/enviar")
async def enviar_telegram(req: TelegramRequest):
    """Envía mensaje o imagen por Telegram."""
    import httpx
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID no configurados"}

    base = f"https://api.telegram.org/bot{token}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            if req.imagen_path and Path(req.imagen_path).exists():
                with open(req.imagen_path, "rb") as f:
                    r = await client.post(f"{base}/sendPhoto",
                        data={"chat_id": chat_id, "caption": req.mensaje},
                        files={"photo": f})
            else:
                r = await client.post(f"{base}/sendMessage",
                    json={"chat_id": chat_id, "text": req.mensaje, "parse_mode": "Markdown"})
        d = r.json()
        return {"ok": d.get("ok", False), "message_id": d.get("result", {}).get("message_id")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# ESTADO GENERAL DE TODAS LAS REDES
# ═══════════════════════════════════════════════
@app.get("/redes/estado")
async def estado_redes():
    """Estado de conexión de todas las plataformas."""
    estado = {}

    # Instagram
    try:
        cl = get_ig_client()
        estado['instagram'] = {"ok": True, "usuario": os.getenv('IG_USER')}
    except:
        estado['instagram'] = {"ok": False, "error": "No conectado"}

    # Facebook
    estado['facebook'] = {
        "ok": bool(os.getenv('FB_PAGE_TOKEN')),
        "page_id": os.getenv('FB_PAGE_ID', 'no configurado')
    }

    # WhatsApp
    estado['whatsapp'] = {
        "ok": bool(os.getenv('TWILIO_ACCOUNT_SID')),
        "via": "Twilio Business API"
    }

    # TikTok
    estado['tiktok'] = {
        "ok": True,
        "via": "Playwright (semi-manual)",
        "nota": "Abre navegador con video listo"
    }

    return {"ok": True, "plataformas": estado}

@app.get("/redes/historial")
async def historial_publicaciones(limite: int = 20):
    """Historial de publicaciones en todas las redes."""
    log_file = LOGS_DIR / "publisher_history.json"
    if not log_file.exists():
        return {"ok": True, "publicaciones": [], "total": 0}
    try:
        data = json.loads(log_file.read_text(encoding='utf-8'))
        if isinstance(data, list):
            return {"ok": True, "publicaciones": data[-limite:], "total": len(data)}
        return {"ok": True, "publicaciones": [data], "total": 1}
    except:
        return {"ok": True, "publicaciones": [], "total": 0}

# ═══════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════
def _siguiente_video_atf():
    """Devuelve el siguiente video ATF en rotación."""
    videos_dir = ATF_VIDEOS_DIR if ATF_VIDEOS_DIR.exists() else MEDIA_DIR
    videos = sorted(videos_dir.glob("*.mp4")) + sorted(videos_dir.glob("*.mov"))
    if not videos:
        return None

    # Log de último publicado
    log = LOGS_DIR / "ultimo_video_atf.txt"
    if log.exists():
        ultimo = log.read_text().strip()
        nombres = [v.name for v in videos]
        idx = nombres.index(ultimo) + 1 if ultimo in nombres else 0
        idx = idx % len(videos)
    else:
        idx = 0

    video = videos[idx]
    log.parent.mkdir(exist_ok=True)
    log.write_text(video.name)
    return video

_CAPTIONS = [
    "¿Cansado de manejar con luz amarilla? 🚗💡 Instalamos kits bi-LED Aozoom con garantía de por vida. Cotiza gratis ✅ #ATF #Faros #Guadalajara",
    "Así quedan los faros con kit Aozoom ✨ Instalación profesional en GDL. DM para cotizar 📩 #RetrofitFaros #BiLED #Aozoom",
    "La diferencia es real 👀 Kit bi-LED instalado en menos de 2 horas. Garantía de por vida incluida 💪 #ATFGuadalajara #Faros",
    "Tu carro merece ver mejor de noche 🌙 Instalamos los mejores kits Aozoom del mercado. Pregunta por tu modelo 🚘 #LED #Faros",
    "No más luz amarilla 🔆 Kits bi-LED Aozoom desde $2,699 instalados. Agenda tu cita hoy 📅 #ActualizaTusFaros #GDL",
]
_caption_idx = [0]

def _caption_rotativo():
    cap = _CAPTIONS[_caption_idx[0] % len(_CAPTIONS)]
    _caption_idx[0] += 1
    return cap

def _log_publicacion(plataforma: str, video: str, caption: str, resultado: dict):
    """Guarda registro de publicación."""
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / "publisher_history.json"
    historial = []
    if log_file.exists():
        try:
            historial = json.loads(log_file.read_text(encoding='utf-8'))
        except:
            historial = []

    historial.append({
        "fecha": datetime.now().isoformat(),
        "plataforma": plataforma,
        "video": Path(video).name if video else "",
        "caption": caption[:100],
        "resultado": resultado
    })
    log_file.write_text(json.dumps(historial, indent=2, ensure_ascii=False), encoding='utf-8')

# ═══════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    MEDIA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    print("NEXUS Motor Redes — Puerto 8010")
    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="warning")

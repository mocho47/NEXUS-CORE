"""
NEXUS Video Promo Generator
Genera videos promocionales automáticamente desde un prompt de texto.

Pipeline:
  1. Groq genera guión JSON (escenas + narración)
  2. Pillow crea frames PNG por escena
  3. Edge TTS (Jorge Neural) graba narración MP3
  4. FFmpeg ensambla slideshow + audio → MP4

Marcas soportadas: NEXUS, ATF, CANBUSFIX, MILENS
Formatos: tiktok (1080x1920), reels (1080x1920), youtube (1920x1080)
"""

import os
import json
import uuid
import asyncio
import subprocess
import threading
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "ASSETS"
OUT_DIR = BASE_DIR / "out" / "promos"
FFMPEG = str(BASE_DIR / "ffmpeg.exe")

# Foto del clon (Jorge Milan) — se superpone en el video
CLON_FOTOS = [
    ASSETS_DIR / "clon_jorge_1.jpg",
    ASSETS_DIR / "clon_jorge_2.jpg",
]

def _cargar_manifesto() -> str:
    """Carga el manifiesto privado de NEXUS si existe"""
    path = ASSETS_DIR / "nexus_manifesto.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")[:3000]  # trim para no saturar el prompt
    return ""

# Configuración por marca
MARCAS = {
    "NEXUS":    {"color": "#f5c518", "color_rgb": (245, 197, 24),  "logo": "nexus_logo.png",     "nombre": "NEXUS"},
    "ATF":      {"color": "#00bfff", "color_rgb": (0, 191, 255),   "logo": "atf_logo.png",        "nombre": "ATF"},
    "CANBUSFIX":{"color": "#d4af37", "color_rgb": (212, 175, 55),  "logo": "canbusfix_logo.png",  "nombre": "CanbusFix"},
    "MILENS":   {"color": "#ff6b00", "color_rgb": (255, 107, 0),   "logo": "milens_logo.png",     "nombre": "Milens"},
}

FORMATOS = {
    "tiktok":  (1080, 1920),
    "reels":   (1080, 1920),
    "youtube": (1920, 1080),
    "square":  (1080, 1080),
}

# Job store en memoria
JOBS: dict = {}


# ─── 1. GROQ: GENERAR SCRIPT ─────────────────────────────────────────────────

async def generar_script_ia(prompt: str, marca: str, duracion_seg: int = 45) -> dict:
    """Groq genera guión JSON con escenas y narración"""
    if not GROQ_KEY:
        return {"ok": False, "error": "GROQ_API_KEY no configurada"}

    marca_cfg = MARCAS.get(marca.upper(), MARCAS["NEXUS"])

    system = """Eres experto en marketing de video para redes sociales mexicanas.
Generas guiones de video cortos, directos y con gancho.
SIEMPRE respondes SOLO con JSON válido, sin markdown, sin explicaciones."""

    # Inyectar contexto del manifiesto si es NEXUS
    contexto_nexus = ""
    if marca.upper() == "NEXUS":
        manifesto = _cargar_manifesto()
        if manifesto:
            contexto_nexus = (
                f"\n\nCONTEXTO OFICIAL DE NEXUS (usar para narración y escenas):\n{manifesto[:2000]}\n"
                "\nIMPORTANTE: El promo es SOLO de NEXUS by Simplex. "
                "NO menciones ni hagas referencia a otros negocios, marcas, talleres o empresas del creador. "
                "NEXUS se presenta como producto independiente.\n"
            )

    user = f"""Crea un guión VIRAL para video promocional de {marca_cfg['nombre']}.
{contexto_nexus}
Instrucción del usuario: "{prompt}"
Duración total aproximada: {duracion_seg} segundos
Red social: TikTok / Reels

Reglas VITALES:
- Tono futurista, impactante, que genere expectativa — como un lanzamiento mundial
- El texto de narración debe sonar natural al hablar, en español mexicano
- La voz del narrador es Jorge Milan — emprendedor mexicano que lo vivió, lo creó y lo usa
- Entre 5 y 7 escenas, cada una con frase poderosa de máximo 6 palabras
- La primera escena debe ENGANCHAR en los primeros 3 segundos
- El CTA final incluye WhatsApp 33-2614-8674
- Si es NEXUS: generar expectativa de "lanzamiento mundial 2026 — hecho en México"

Responde SOLO este JSON (sin markdown):
{{
  "narracion": "texto completo para voz en off (~{duracion_seg} segundos al hablar normal, tono poderoso)",
  "escenas": [
    {{"duracion": 3, "titulo": "Frase de gancho", "subtitulo": "que rompe expectativas"}},
    {{"duracion": 4, "titulo": "...", "subtitulo": "..."}},
    {{"duracion": 4, "titulo": "...", "subtitulo": "..."}},
    {{"duracion": 5, "titulo": "...", "subtitulo": "..."}},
    {{"duracion": 4, "titulo": "...", "subtitulo": "..."}},
    {{"duracion": 4, "titulo": "{marca_cfg['nombre']} by Simplex" if marca_cfg['nombre'] == 'NEXUS' else marca_cfg['nombre'], "subtitulo": "WhatsApp: 33-2614-8674"}}
  ],
  "caption_instagram": "caption viral con emojis, storytelling y saltos de línea",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6", "#hashtag7", "#hashtag8", "#hashtag9", "#hashtag10"]
}}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1200,
                },
            )
        if resp.status_code != 200:
            return {"ok": False, "error": f"Groq {resp.status_code}"}

        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.rstrip("`")

        # Limpiar caracteres de control que rompen el JSON
        import re
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', content)

        script = json.loads(content)
        script["ok"] = True
        return script

    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON inválido de Groq: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── 2. PILLOW: CREAR FRAMES ─────────────────────────────────────────────────

def crear_frame(titulo: str, subtitulo: str, marca: str, w: int, h: int,
                numero: int, job_dir: Path) -> str:
    """Crea un frame PNG con Pillow para una escena del video"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError("Pillow no instalado. Ejecuta: pip install Pillow")

    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    marca_cfg = MARCAS.get(marca.upper(), MARCAS["NEXUS"])
    color_acento = marca_cfg["color_rgb"]

    img = Image.new("RGB", (w, h), (10, 10, 10))

    # Foto de Jorge como fondo en escenas con clon disponible
    fotos_validas = [f for f in CLON_FOTOS if f.exists()]
    if fotos_validas:
        foto_idx = numero % len(fotos_validas)
        try:
            fondo = Image.open(fotos_validas[foto_idx]).convert("RGB")
            # Escalar para cubrir el frame completo
            ratio_w = w / fondo.width
            ratio_h = h / fondo.height
            ratio = max(ratio_w, ratio_h)
            nw = int(fondo.width * ratio)
            nh = int(fondo.height * ratio)
            fondo = fondo.resize((nw, nh), Image.LANCZOS)
            # Centrar crop
            cx = (nw - w) // 2
            cy = (nh - h) // 2
            fondo = fondo.crop((cx, cy, cx + w, cy + h))
            # Oscurecer para que el texto sea legible
            overlay = Image.new("RGB", (w, h), (0, 0, 0))
            img = Image.blend(fondo, overlay, alpha=0.65)
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    # Franja de color acento en la parte superior (branding)
    draw.rectangle([(0, 0), (w, 6)], fill=color_acento)
    # Franja inferior
    draw.rectangle([(0, h - 6), (w, h)], fill=color_acento)



    # Seleccionar fuentes del sistema Windows
    font_path_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_path_reg = "C:/Windows/Fonts/arial.ttf"

    # Tamaños según orientación
    if w < h:  # Portrait (TikTok/Reels)
        size_titulo = max(60, w // 12)
        size_sub = max(32, w // 22)
    else:  # Landscape (YouTube)
        size_titulo = max(80, h // 10)
        size_sub = max(40, h // 18)

    try:
        font_titulo = ImageFont.truetype(font_path_bold, size_titulo)
        font_sub = ImageFont.truetype(font_path_reg, size_sub)
    except Exception:
        font_titulo = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Posición vertical centrada con offset para subtítulo
    center_x = w // 2
    center_y = h // 2

    # Dibujar título (color acento)
    titulo_upper = titulo.upper()
    bbox_t = draw.textbbox((0, 0), titulo_upper, font=font_titulo)
    tw = bbox_t[2] - bbox_t[0]
    th = bbox_t[3] - bbox_t[1]

    # Sombra
    draw.text((center_x - tw // 2 + 3, center_y - th // 2 - 30 + 3),
              titulo_upper, font=font_titulo, fill=(0, 0, 0))
    # Texto principal
    draw.text((center_x - tw // 2, center_y - th // 2 - 30),
              titulo_upper, font=font_titulo, fill=color_acento)

    # Subtítulo (gris claro)
    if subtitulo:
        bbox_s = draw.textbbox((0, 0), subtitulo, font=font_sub)
        sw = bbox_s[2] - bbox_s[0]
        draw.text((center_x - sw // 2, center_y + th // 2 + 20),
                  subtitulo, font=font_sub, fill=(160, 160, 160))

    # Logo de la marca (si existe)
    logo_path = ASSETS_DIR / marca_cfg["logo"]
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Redimensionar logo
            logo_h = max(60, h // 18)
            ratio = logo_h / logo.height
            logo_w = int(logo.width * ratio)
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

            # Aplicar opacidad
            if logo.mode == "RGBA":
                r_ch, g_ch, b_ch, a_ch = logo.split()
                a_ch = a_ch.point(lambda x: int(x * 0.65))
                logo.putalpha(a_ch)

            # Esquina inferior derecha con margen
            margin = 20
            pos = (w - logo_w - margin, h - logo_h - margin)
            img.paste(logo, pos, logo if logo.mode == "RGBA" else None)
        except Exception:
            pass  # Si falla el logo, continuar sin él

    # Foto del clon (Jorge Milan) — en la primera y última escena
    if numero == 0 or titulo.upper() in ("NEXUS", "ATF", "CANBUSFIX", "MILENS", "SIMPLEX"):
        for foto_path in CLON_FOTOS:
            if foto_path.exists():
                try:
                    clon = Image.open(foto_path).convert("RGB")
                    # Recortar en círculo (portrait) y pegar en esquina inferior izquierda
                    clon_h = max(120, h // 8)
                    ratio_c = clon_h / clon.height
                    clon_w = int(clon.width * ratio_c)
                    clon = clon.resize((clon_w, clon_h), Image.LANCZOS)
                    # Crear máscara circular
                    size = min(clon_w, clon_h)
                    mask = Image.new("L", (size, size), 0)
                    from PIL import ImageDraw as ID2
                    ID2.Draw(mask).ellipse((0, 0, size, size), fill=255)
                    clon_sq = clon.crop((max(0, (clon_w - size) // 2), 0,
                                         max(0, (clon_w - size) // 2) + size, size))
                    clon_sq = clon_sq.resize((size, size), Image.LANCZOS)
                    # Borde dorado
                    border_img = Image.new("RGB", (size + 6, size + 6), color_acento)
                    border_mask = Image.new("L", (size + 6, size + 6), 0)
                    ID2.Draw(border_mask).ellipse((0, 0, size + 6, size + 6), fill=255)
                    # Pegar en posición
                    margin_c = 20
                    cx = margin_c
                    cy = h - size - 6 - margin_c
                    img.paste(border_img, (cx, cy), border_mask)
                    img.paste(clon_sq, (cx + 3, cy + 3), mask)
                    break  # Solo una foto
                except Exception:
                    pass

    frame_path = job_dir / f"frame_{numero:03d}.png"
    img.save(str(frame_path), "PNG")
    return str(frame_path)


# ─── 3. EDGE TTS: NARRACIÓN ─────────────────────────────────────────────────

def generar_narracion(texto: str, output_path: str, marca: str = "") -> bool:
    """
    Genera narración de audio para el promo.
    - Si es NEXUS y existe voz_jorge_milan.mp3 → usa la voz real de Jorge
    - En otro caso → Edge TTS (Jorge Neural)
    """
    # Voz real de Jorge para promos NEXUS
    voz_real = ASSETS_DIR / "voz_jorge_milan.mp3"
    if marca.upper() == "NEXUS" and voz_real.exists():
        import shutil
        shutil.copy(str(voz_real), output_path)
        print(f"[PROMO] Usando voz real de Jorge Milan")
        return True

    # Fallback: Edge TTS
    try:
        from nexus_voice import hablar_archivo
        hablar_archivo(texto, output_path)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"[PROMO] Error TTS: {e}")
        return False


# ─── 4. FFMPEG: ENSAMBLAR VIDEO ──────────────────────────────────────────────

def ensamblar_video(job_dir: Path, escenas: list, narracion_path: str,
                    formato: str, ffmpeg_path: str) -> str:
    """Ensambla frames + audio en MP4 con FFmpeg"""
    w, h = FORMATOS.get(formato, (1080, 1920))
    clips = []

    # Crear clip por cada frame
    for i, escena in enumerate(escenas):
        frame = job_dir / f"frame_{i:03d}.png"
        clip = job_dir / f"clip_{i:03d}.mp4"
        dur = escena.get("duracion", 4)

        cmd = [
            ffmpeg_path, "-y",
            "-loop", "1",
            "-i", str(frame),
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
            "-t", str(dur),
            "-r", "24",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            str(clip)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0:
            clips.append(str(clip))

    if not clips:
        raise RuntimeError("No se pudieron crear clips de video")

    # Crear archivo de concatenación
    concat_file = job_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    # Video sin audio
    video_noaudio = job_dir / "video_noaudio.mp4"
    cmd_concat = [
        ffmpeg_path, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(video_noaudio)
    ]
    subprocess.run(cmd_concat, capture_output=True, timeout=120, check=True)

    # Combinar con audio (si existe narración)
    output_final = job_dir / "output.mp4"
    if os.path.exists(narracion_path):
        cmd_final = [
            ffmpeg_path, "-y",
            "-i", str(video_noaudio),
            "-i", narracion_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_final)
        ]
    else:
        cmd_final = [
            ffmpeg_path, "-y",
            "-i", str(video_noaudio),
            "-c:v", "copy",
            str(output_final)
        ]
    subprocess.run(cmd_final, capture_output=True, timeout=120, check=True)

    return str(output_final)


# ─── 5. JOB SYSTEM ───────────────────────────────────────────────────────────

def _run_job(job_id: str, prompt: str, marca: str, formato: str):
    """Ejecutado en thread background — actualiza JOBS[job_id]"""
    job_dir = OUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    def update(status, progress, msg=""):
        JOBS[job_id].update({"status": status, "progress": progress, "msg": msg})

    try:
        update("processing", 5, "Iniciando...")

        # Paso 1: Script IA
        update("processing", 10, "Generando guión con IA...")
        script = asyncio.run(generar_script_ia(prompt, marca))
        if not script.get("ok"):
            raise RuntimeError(f"Script IA falló: {script.get('error')}")
        JOBS[job_id]["script"] = script
        update("processing", 25, "Guión listo")

        # Paso 2: Frames
        w, h = FORMATOS.get(formato, (1080, 1920))
        escenas = script.get("escenas", [])
        update("processing", 30, f"Creando {len(escenas)} frames...")
        for i, escena in enumerate(escenas):
            crear_frame(
                titulo=escena.get("titulo", "NEXUS"),
                subtitulo=escena.get("subtitulo", ""),
                marca=marca, w=w, h=h,
                numero=i, job_dir=job_dir
            )
            pct = 30 + int(20 * (i + 1) / max(len(escenas), 1))
            update("processing", pct, f"Frame {i+1}/{len(escenas)}")

        # Paso 3: Narración TTS
        update("processing", 55, "Grabando narración...")
        narracion_path = str(job_dir / "narracion.mp3")
        narracion_ok = generar_narracion(script.get("narracion", ""), narracion_path, marca)
        update("processing", 70, "Narración lista" if narracion_ok else "Sin audio (TTS falló)")

        # Paso 4: Ensamblar
        update("processing", 75, "Ensamblando video...")
        output = ensamblar_video(job_dir, escenas, narracion_path, formato, FFMPEG)
        update("processing", 95, "Finalizando...")

        # URL relativa para servir
        job_url = f"/out/promos/{job_id}/output.mp4"
        JOBS[job_id].update({
            "status": "done",
            "progress": 100,
            "msg": "Video listo",
            "url": job_url,
            "caption": script.get("caption_instagram", ""),
            "hashtags": script.get("hashtags", []),
            "escenas": len(escenas),
        })

    except Exception as e:
        JOBS[job_id].update({
            "status": "error",
            "progress": 0,
            "msg": str(e),
            "error": str(e),
        })


def iniciar_job(prompt: str, marca: str = "NEXUS", formato: str = "tiktok") -> str:
    """Inicia job en background, devuelve job_id"""
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "status": "queued",
        "progress": 0,
        "msg": "En cola...",
        "job_id": job_id,
        "prompt": prompt,
        "marca": marca,
        "formato": formato,
    }
    t = threading.Thread(target=_run_job, args=(job_id, prompt, marca, formato), daemon=True)
    t.start()
    return job_id


def estado_job(job_id: str) -> dict:
    """Devuelve estado actual del job"""
    return JOBS.get(job_id, {"status": "not_found", "error": "Job no encontrado"})


# ─── CAPTION RÁPIDO (sin video) ──────────────────────────────────────────────

async def caption_rapido(texto: str, marca: str, red: str = "instagram") -> dict:
    """Groq genera caption + hashtags rápido, sin generar video"""
    if not GROQ_KEY:
        return {"ok": False, "error": "GROQ_API_KEY no configurada"}

    marca_cfg = MARCAS.get(marca.upper(), MARCAS["NEXUS"])
    prompt = f"""Genera un caption para {red} para la marca {marca_cfg['nombre']}.
Tema/contenido: "{texto}"
Red social: {red}
Idioma: español mexicano, directo, con personalidad
Incluye emojis relevantes, saltos de línea para legibilidad.
CTA con WhatsApp 33-2614-8674.

Responde SOLO JSON (sin markdown):
{{"caption": "texto del caption con emojis y \\n para saltos", "hashtags": ["#h1","#h2","#h3","#h4","#h5","#h6","#h7","#h8","#h9","#h10"]}}"""

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 600,
                },
            )
        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.rstrip("`")
        result = json.loads(content)
        result["ok"] = True
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}

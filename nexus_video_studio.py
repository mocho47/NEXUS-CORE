"""
NEXUS — Video Studio
- Detección automática de escenas (OpenCV + scenedetect)
- División manual por marcadores
- Formato por red: TikTok / Reels / Facebook / YouTube Shorts
- Caption por segmento (Groq)
- Descarga ZIP con todo listo
"""

import os
import json
import shutil
import subprocess
import threading
import uuid
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "VIDEO_STUDIO" / "uploads"
OUTPUT_DIR = BASE_DIR / "VIDEO_STUDIO" / "output"
THUMBS_DIR = BASE_DIR / "VIDEO_STUDIO" / "thumbs"

for d in [UPLOAD_DIR, OUTPUT_DIR, THUMBS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

FFMPEG = "ffmpeg"

# Formatos de red social
FORMATOS = {
    "tiktok":   {"w": 1080, "h": 1920, "max_s": 60,  "fps": 30, "label": "TikTok"},
    "reels":    {"w": 1080, "h": 1920, "max_s": 90,  "fps": 30, "label": "Instagram Reels"},
    "facebook": {"w": 1280, "h": 720,  "max_s": 240, "fps": 30, "label": "Facebook"},
    "shorts":   {"w": 1080, "h": 1920, "max_s": 60,  "fps": 30, "label": "YouTube Shorts"},
    "story":    {"w": 1080, "h": 1920, "max_s": 15,  "fps": 30, "label": "Story (15s)"},
}

# Jobs en memoria
_jobs: dict = {}


def _log(job_id, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    if job_id in _jobs:
        _jobs[job_id]["log"].append(entry)
    print(f"[VSTUDIO {job_id[:6]}] {msg}")


def get_info_video(ruta: str) -> dict:
    """Obtiene info del video con ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(ruta)
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(r.stdout)
        fmt = data.get("format", {})
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        return {
            "duracion": float(fmt.get("duration", 0)),
            "w": int(video_stream.get("width", 0)),
            "h": int(video_stream.get("height", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1")),
            "size_mb": round(int(fmt.get("size", 0)) / 1024 / 1024, 1),
        }
    except Exception as e:
        return {"error": str(e)}


def generar_thumbnails(ruta: str, job_id: str, cada_segundos: float = 1.0) -> list:
    """Genera un thumbnail por cada N segundos → lista de rutas relativas."""
    out = THUMBS_DIR / job_id
    out.mkdir(exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-i", str(ruta),
        "-vf", f"fps=1/{cada_segundos},scale=160:90:force_original_aspect_ratio=decrease,pad=160:90:(ow-iw)/2:(oh-ih)/2",
        "-q:v", "5",
        str(out / "thumb_%04d.jpg")
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    thumbs = sorted(out.glob("thumb_*.jpg"))
    return [f"/VIDEO_STUDIO/thumbs/{job_id}/{t.name}" for t in thumbs]


def detectar_escenas_auto(ruta: str, threshold: float = 27.0) -> list:
    """Detecta cambios de escena automáticamente. Retorna lista de tiempos en segundos."""
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
        video = open_video(str(ruta))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video, show_progress=False)
        scene_list = scene_manager.get_scene_list()
        cortes = []
        for i, (start, end) in enumerate(scene_list):
            cortes.append({
                "idx": i,
                "inicio": round(start.get_seconds(), 2),
                "fin": round(end.get_seconds(), 2),
                "duracion": round(end.get_seconds() - start.get_seconds(), 2),
                "label": f"Segmento {i+1}",
                "caption": "",
                "redes": ["tiktok", "reels"],
            })
        return cortes
    except Exception as e:
        return [{"error": str(e)}]


def _generar_caption_groq(idx: int, duracion: float, contexto_negocio: str = "ATF faros retrofit") -> str:
    """Genera caption para un segmento usando Groq."""
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        prompt = (
            f"Eres experto en redes sociales para el negocio: {contexto_negocio}. "
            f"Genera un caption viral en español para un clip de {duracion:.0f} segundos. "
            f"Es el clip número {idx+1} de una serie. "
            "Máximo 150 caracteres. Incluye 3 hashtags relevantes al final. Solo el texto, nada más."
        )
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Caption {idx+1} — {contexto_negocio} #ATF #Faros #GDL"


def _cortar_segmento(ruta_in: str, inicio: float, fin: float,
                      out_path: str, formato: str) -> bool:
    """Corta y formatea un segmento con FFmpeg."""
    fmt = FORMATOS.get(formato, FORMATOS["tiktok"])
    w, h, fps = fmt["w"], fmt["h"], fmt["fps"]
    duracion = fin - inicio

    # Filtro: escalar manteniendo ratio + pad negro para llenar
    vf = (
        f"trim=start={inicio}:end={fin},setpts=PTS-STARTPTS,"
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps}"
    )

    cmd = [
        FFMPEG, "-y",
        "-i", str(ruta_in),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-ss", str(inicio), "-t", str(duracion),
        "-movflags", "+faststart",
        str(out_path)
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    return r.returncode == 0


def procesar_job(job_id: str):
    """Worker que procesa el job completo en background."""
    job = _jobs.get(job_id)
    if not job:
        return

    ruta = job["ruta_original"]
    segmentos = job["segmentos"]
    redes = job.get("redes", ["tiktok", "reels"])
    negocio = job.get("negocio", "ATF faros retrofit Guadalajara")

    job["estado"] = "procesando"
    job["progreso"] = 0
    total = len(segmentos) * len(redes)
    procesados = 0

    out_job = OUTPUT_DIR / job_id
    out_job.mkdir(exist_ok=True)

    captions_txt = []

    for i, seg in enumerate(segmentos):
        inicio = seg["inicio"]
        fin = seg["fin"]
        label = seg.get("label", f"seg_{i+1}").replace(" ", "_")

        # Generar caption si no tiene
        if not seg.get("caption"):
            _log(job_id, f"Generando caption segmento {i+1}...")
            seg["caption"] = _generar_caption_groq(i, fin - inicio, negocio)

        captions_txt.append(f"=== {label} ===\n{seg['caption']}\n")

        for red in redes:
            _log(job_id, f"Procesando {label} → {red}...")
            fmt = FORMATOS.get(red, FORMATOS["tiktok"])
            nombre = f"ep{i+1:02d}_{label}_{red}.mp4"
            out_path = out_job / nombre

            ok = _cortar_segmento(ruta, inicio, fin, str(out_path), red)
            procesados += 1
            job["progreso"] = int(procesados / total * 100)

            if ok:
                _log(job_id, f"  ✓ {nombre}")
            else:
                _log(job_id, f"  ✗ Error en {nombre}")

    # Guardar captions.txt
    captions_path = out_job / "captions.txt"
    captions_path.write_text("\n".join(captions_txt), encoding="utf-8")

    # Crear ZIP
    _log(job_id, "Creando ZIP...")
    zip_path = OUTPUT_DIR / f"{job_id}.zip"
    shutil.make_archive(str(OUTPUT_DIR / job_id), "zip", str(out_job))

    job["estado"] = "listo"
    job["progreso"] = 100
    job["zip_url"] = f"/VIDEO_STUDIO/output/{job_id}.zip"
    job["segmentos"] = segmentos
    _log(job_id, f"Job completo. ZIP: {zip_path}")


# ── API pública ────────────────────────────────────────────────────────────────

def crear_job(ruta_video: str, negocio: str = "ATF faros retrofit",
              redes: list = None) -> dict:
    """Crea un nuevo job. Retorna job_id."""
    job_id = uuid.uuid4().hex[:10]
    info = get_info_video(ruta_video)

    _jobs[job_id] = {
        "id": job_id,
        "ruta_original": ruta_video,
        "info": info,
        "negocio": negocio,
        "redes": redes or ["tiktok", "reels"],
        "segmentos": [],
        "estado": "nuevo",
        "progreso": 0,
        "log": [],
        "zip_url": None,
        "creado": datetime.now().isoformat(),
    }
    return {"ok": True, "job_id": job_id, "info": info}


def job_detectar_escenas(job_id: str, threshold: float = 27.0) -> dict:
    """Detecta escenas automáticamente y guarda en el job."""
    job = _jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job no encontrado"}
    escenas = detectar_escenas_auto(job["ruta_original"], threshold)
    job["segmentos"] = escenas
    return {"ok": True, "segmentos": escenas}


def job_set_segmentos(job_id: str, segmentos: list) -> dict:
    """Establece segmentos manualmente (desde editor interactivo)."""
    job = _jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job no encontrado"}
    job["segmentos"] = segmentos
    return {"ok": True, "segmentos": segmentos}


def job_generar_thumbnails(job_id: str) -> dict:
    """Genera thumbnails para el editor visual."""
    job = _jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job no encontrado"}
    thumbs = generar_thumbnails(job["ruta_original"], job_id)
    job["thumbs"] = thumbs
    return {"ok": True, "thumbs": thumbs, "total": len(thumbs)}


def job_iniciar_proceso(job_id: str) -> dict:
    """Lanza el procesamiento en background."""
    job = _jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job no encontrado"}
    if not job["segmentos"]:
        return {"ok": False, "error": "Sin segmentos definidos"}
    t = threading.Thread(target=procesar_job, args=(job_id,), daemon=True)
    t.start()
    return {"ok": True, "msg": "Procesando...", "job_id": job_id}


def job_estado(job_id: str) -> dict:
    """Retorna estado actual del job."""
    job = _jobs.get(job_id)
    if not job:
        return {"ok": False, "error": "Job no encontrado"}
    return {
        "ok": True,
        "estado": job["estado"],
        "progreso": job["progreso"],
        "segmentos": job.get("segmentos", []),
        "thumbs": job.get("thumbs", []),
        "zip_url": job.get("zip_url"),
        "info": job.get("info"),
        "log": job["log"][-10:],
    }


def listar_jobs() -> list:
    return [
        {"id": j["id"], "estado": j["estado"], "progreso": j["progreso"],
         "creado": j["creado"], "negocio": j["negocio"]}
        for j in _jobs.values()
    ]

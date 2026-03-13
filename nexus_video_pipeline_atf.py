# -*- coding: utf-8 -*-
"""
nexus_video_pipeline_atf.py — Pipeline de video para ATF (Actualiza Tus Faros)
================================================================================
Procesa videos de instalaciones de faros para TikTok, Reels y Facebook.
ffmpeg: C:\nexus\ffmpeg.exe

Uso:
    pipeline = VideoPipelineATF()
    resultado = pipeline.procesar_video("C:/Videos/instalacion.mp4")
    carpeta   = pipeline.procesar_carpeta()
    caption   = pipeline.generar_caption_ia("C:/Videos/instalacion.mp4")
"""

import os
import json
import subprocess
import datetime
from pathlib import Path
from typing import Optional

BASE_DIR    = Path(__file__).parent
FFMPEG      = str(BASE_DIR / "ffmpeg.exe") if (BASE_DIR / "ffmpeg.exe").exists() else "ffmpeg"
VIDEO_IN    = BASE_DIR / "TALLER" / "VIDEO_ATF"
VIDEO_OUT   = BASE_DIR / "TALLER" / "VIDEO_ATF_OUTPUT"
STATE_PATH  = BASE_DIR / "CONFIG" / "video_pipeline_state.json"

VIDEO_IN.mkdir(parents=True, exist_ok=True)
VIDEO_OUT.mkdir(parents=True, exist_ok=True)

FORMATOS = {
    "tiktok":   {"w": 1080, "h": 1920, "max_s": 58,  "fps": 30, "label": "TikTok"},
    "reels":    {"w": 1080, "h": 1920, "max_s": 88,  "fps": 30, "label": "Reels"},
    "facebook": {"w": 1280, "h": 720,  "max_s": 180, "fps": 30, "label": "Facebook"},
}

WATERMARK_ATF = "ATF by Simplex · Retrofit GDL"


def _load_state() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"procesados": [], "errores": [], "total_procesados": 0}


def _save_state(state: dict):
    try:
        STATE_PATH.parent.mkdir(exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _ffmpeg_cmd(args: list) -> tuple[bool, str]:
    """Ejecuta ffmpeg silencioso. Retorna (ok, stderr)."""
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0, r.stderr
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, f"ffmpeg no encontrado en: {FFMPEG}"
    except Exception as e:
        return False, str(e)


def _get_duracion(input_path: str) -> float:
    """Obtiene duración del video en segundos."""
    try:
        ffprobe = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe")
        r = subprocess.run(
            [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", input_path],
            capture_output=True, text=True, timeout=30
        )
        return float(r.stdout.strip())
    except Exception:
        return 60.0


def procesar_video(input_path: str, output_dir: Optional[str] = None) -> dict:
    """
    Procesa un video en 3 formatos: TikTok, Reels, Facebook.
    Retorna dict con rutas de output, tamaños y estado.
    """
    inp = Path(input_path)
    if not inp.exists():
        return {"ok": False, "error": f"Archivo no encontrado: {input_path}"}

    out_dir = Path(output_dir) if output_dir else VIDEO_OUT / inp.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    duracion = _get_duracion(str(inp))
    resultados = {}

    for fmt_key, fmt in FORMATOS.items():
        out_file = out_dir / f"{inp.stem}_{fmt_key}.mp4"
        max_s    = min(duracion, fmt["max_s"])
        w, h     = fmt["w"], fmt["h"]

        # Filtro: escalar + crop centrado + watermark texto
        if fmt_key in ("tiktok", "reels"):
            # Vertical: escalar para que el lado más pequeño sea w, luego crop
            vf = (
                f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},"
                f"drawtext=text='{WATERMARK_ATF}':fontsize=28:fontcolor=white@0.7:"
                f"x=(w-text_w)/2:y=h-60:shadowcolor=black:shadowx=2:shadowy=2"
            )
        else:
            # Horizontal: landscape
            vf = (
                f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},"
                f"drawtext=text='{WATERMARK_ATF}':fontsize=22:fontcolor=white@0.7:"
                f"x=20:y=h-50:shadowcolor=black:shadowx=2:shadowy=2"
            )

        ok, err = _ffmpeg_cmd([
            "-i", str(inp),
            "-t", str(max_s),
            "-vf", vf,
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(fmt["fps"]),
            "-movflags", "+faststart",
            str(out_file),
        ])

        size_mb = round(out_file.stat().st_size / 1024 / 1024, 1) if out_file.exists() else 0
        resultados[fmt_key] = {
            "ok":       ok,
            "archivo":  str(out_file) if ok else None,
            "size_mb":  size_mb,
            "duracion": round(max_s, 1),
            "formato":  fmt["label"],
            "error":    err if not ok else None,
        }

    todos_ok = all(v["ok"] for v in resultados.values())

    # Actualizar estado
    state = _load_state()
    entrada = {
        "ts":      datetime.datetime.now().isoformat(),
        "archivo": str(inp.name),
        "ok":      todos_ok,
        "formatos": {k: v["ok"] for k, v in resultados.items()},
    }
    if todos_ok:
        state["procesados"].append(entrada)
        state["total_procesados"] = state.get("total_procesados", 0) + 1
    else:
        state["errores"].append(entrada)
    _save_state(state)

    return {
        "ok":        todos_ok,
        "archivo":   str(inp.name),
        "output_dir": str(out_dir),
        "formatos":  resultados,
    }


def procesar_carpeta(carpeta: Optional[str] = None) -> dict:
    """
    Procesa todos los videos en la carpeta.
    Retorna resumen con lista de resultados.
    """
    src = Path(carpeta) if carpeta else VIDEO_IN
    extensiones = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
    videos = [f for f in src.iterdir() if f.suffix.lower() in extensiones]

    if not videos:
        return {"ok": True, "procesados": 0, "mensaje": f"No hay videos en {src}", "resultados": []}

    resultados = []
    for v in videos:
        r = procesar_video(str(v))
        resultados.append(r)

    ok_count  = sum(1 for r in resultados if r["ok"])
    err_count = len(resultados) - ok_count

    return {
        "ok":         True,
        "total":      len(videos),
        "exitosos":   ok_count,
        "errores":    err_count,
        "resultados": resultados,
    }


def generar_caption_ia(video_path: str, negocio: str = "atf") -> dict:
    """
    Genera caption viral para el video usando Groq.
    """
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return {"ok": False, "error": "Sin GROQ_API_KEY"}

        nombre = Path(video_path).stem
        client = Groq(api_key=key)

        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content":
                    "Eres un experto en contenido viral para TikTok e Instagram enfocado en negocios automotrices mexicanos. "
                    "Generas captions que generan leads reales. Español mexicano, directo, sin emojis excesivos."},
                {"role": "user", "content":
                    f"Genera el caption viral para un video de instalación de faros retrofit bi-led de ATF en Guadalajara. "
                    f"Nombre del archivo: {nombre}. "
                    f"Incluye: 1) Hook impactante primera línea, 2) Descripción del proceso (2 líneas), "
                    f"3) CTA para WhatsApp o DM, 4) Hashtags (8-10 relevantes para MX). "
                    f"Formato: texto listo para copiar y pegar. Máximo 150 palabras total."}
            ],
            max_tokens=300,
        )

        caption = r.choices[0].message.content.strip()
        return {
            "ok":      True,
            "caption": caption,
            "archivo": Path(video_path).name,
            "negocio": negocio,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def estado_pipeline() -> dict:
    """Retorna estado actual del pipeline."""
    state    = _load_state()
    pendientes = [f for f in VIDEO_IN.iterdir()
                  if f.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}]
    procesados_nombres = {e["archivo"] for e in state.get("procesados", [])}
    sin_procesar = [f.name for f in pendientes if f.name not in procesados_nombres]

    return {
        "ok":              True,
        "pendientes":      len(sin_procesar),
        "sin_procesar":    sin_procesar[:20],
        "total_procesados": state.get("total_procesados", 0),
        "errores_total":   len(state.get("errores", [])),
        "carpeta_input":   str(VIDEO_IN),
        "carpeta_output":  str(VIDEO_OUT),
        "ffmpeg":          FFMPEG,
    }


# Instancia global
pipeline = VideoPipelineATF = type("VideoPipelineATF", (), {
    "procesar_video":    staticmethod(procesar_video),
    "procesar_carpeta":  staticmethod(procesar_carpeta),
    "generar_caption_ia":staticmethod(generar_caption_ia),
    "estado":            staticmethod(estado_pipeline),
})()

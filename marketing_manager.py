"""
marketing_manager.py — Procesador de videos para redes sociales.

Añade marca de agua (texto empresa + teléfono) y segmenta videos >60s
para cumplir límites de Instagram Reels / TikTok.

Uso:
    python marketing_manager.py                    # procesa todos los .mp4 en INPUT_FOLDER
    python marketing_manager.py video.mp4          # procesa un video específico
"""
import os
import subprocess
import glob
import json
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_BIN = os.path.join(BASE_DIR, "ffmpeg.exe")
FFPROBE_BIN = os.path.join(BASE_DIR, "ffprobe.exe")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
_NEGOCIO_PATH = os.path.join(BASE_DIR, "CONFIG", "negocio.json")


def _load_negocio() -> dict:
    try:
        if os.path.exists(_NEGOCIO_PATH):
            with open(_NEGOCIO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _get_io_folders():
    """Devuelve (input_folder, output_folder) desde negocio.json o Videos del usuario."""
    negocio = _load_negocio()
    videos_cfg = negocio.get("videos", {})

    # Input: carpeta de videos sin procesar
    input_folder = videos_cfg.get("input_folder") or os.path.join(
        os.path.expanduser("~"), "Videos", "ParaProcesar"
    )
    # Output: carpeta de videos listos para redes
    output_folder = videos_cfg.get("output_folder") or os.path.join(
        os.path.expanduser("~"), "Videos", "ParaRedes"
    )
    return input_folder, output_folder


def log(msg: str):
    print(f"[MARKETING] {msg}")


def get_video_duration(file_path: str) -> float:
    try:
        cmd = [
            FFPROBE_BIN, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except Exception:
        return 0.0


def build_ffmpeg_filters(company_text: str, phone_text: str):
    """Construye filtros ffmpeg: mejora de calidad + watermark de texto."""
    filters = [
        "unsharp=5:5:1.0:5:5:0.0,eq=saturation=1.2:contrast=1.1",
        f"drawtext=text='{company_text} | {phone_text}':x=20:y=h-th-20:"
        f"fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6",
    ]
    filter_str = ",".join(filters)
    has_logo = os.path.exists(LOGO_PATH)
    return filter_str, has_logo


def process_video(file_path: str, output_folder: str, company_text: str, phone_text: str):
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    if filename.startswith("~$") or filename.startswith("."):
        return

    log(f"Procesando: {filename}")
    duration = get_video_duration(file_path)
    log(f"  Duración: {duration:.1f}s")

    base_filter, has_logo = build_ffmpeg_filters(company_text, phone_text)

    cmd = [FFMPEG_BIN, "-y", "-i", file_path]

    if has_logo:
        cmd.extend(["-i", LOGO_PATH])
        filter_complex = (
            f"[0:v]{base_filter}[bg];[1:v]scale=150:-1[logo];"
            f"[bg][logo]overlay=W-w-20:20"
        )
        cmd.extend(["-filter_complex", filter_complex])
    else:
        cmd.extend(["-vf", base_filter])

    cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "fast", "-c:a", "copy"])

    if duration > 65:
        log(f"  Video largo — segmentando en clips de 60s")
        output_pattern = os.path.join(output_folder, f"{name}_brand_parte%03d{ext}")
        cmd.extend(["-f", "segment", "-segment_time", "60", "-reset_timestamps", "1", output_pattern])
        subprocess.run(cmd)
        log(f"  Segmentación OK → {output_pattern}")
    else:
        output_file = os.path.join(output_folder, f"{name}_branded{ext}")
        cmd.append(output_file)
        subprocess.run(cmd)
        log(f"  OK → {output_file}")


def main(target_file: str = None):
    if not os.path.exists(FFMPEG_BIN):
        log(f"ERROR: ffmpeg.exe no encontrado en {FFMPEG_BIN}")
        return

    negocio = _load_negocio()
    company_text = negocio.get("nombre", "Nexus Taller").replace("'", "")
    phone_raw = negocio.get("telefono", "").strip()
    phone_text = phone_raw if phone_raw else "Sin número"

    input_folder, output_folder = _get_io_folders()
    os.makedirs(output_folder, exist_ok=True)

    log(f"Empresa: {company_text} | Tel: {phone_text}")
    log(f"Input:  {input_folder}")
    log(f"Output: {output_folder}")
    log(f"Logo:   {'Sí' if os.path.exists(LOGO_PATH) else 'No (solo texto)'}")

    if target_file:
        videos = [target_file] if os.path.exists(target_file) else []
    else:
        videos = glob.glob(os.path.join(input_folder, "*.mp4"))

    if not videos:
        log(f"Sin videos en {input_folder}")
        return

    log(f"Procesando {len(videos)} video(s)...")
    for v in videos:
        try:
            process_video(v, output_folder, company_text, phone_text)
        except Exception as e:
            log(f"Error en {v}: {e}")

    log("Proceso terminado. Revisa la carpeta ParaRedes.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    main(target)

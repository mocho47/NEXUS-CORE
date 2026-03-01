"""
NEXUS Motion Graphics Video Generator
Genera videos con gráficos modernos animados + música rock/industrial
- Solo FFmpeg + numpy (sin fotos, sin voz, sin servicios externos)
- Texto con fade-in/slide desde abajo
- Barra de color animada
- Beat industrial generado con numpy
"""

import os
import subprocess
import uuid
import threading
import json
import httpx
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
BASE_DIR     = Path(__file__).parent
OUT_DIR      = BASE_DIR / "out" / "promos"
FFMPEG       = str(BASE_DIR / "ffmpeg.exe")
FONT_BOLD    = r"C\:/Windows/Fonts/arialbd.ttf"
FONT_REG     = r"C\:/Windows/Fonts/arial.ttf"

# ── MODO PRIVADO: solo activo cuando NEXUS_PRIVATE=1 en .env ─────────────────
_PRIVATE     = os.getenv("NEXUS_PRIVATE", "0") == "1"

# Mensajes subliminales: texto corto, aparece 1-2 frames (~80ms) en coordenadas
# aleatorias con opacidad mínima. Solo en versión privada.
_SUB_MSGS = [
    "TU SIGUIENTE NIVEL",
    "NEXUS LO HACE",
    "ACTUA AHORA",
    "TU NEGOCIO TRABAJA",
    "SIMPLEX TE MUEVE",
    "IMPARABLE",
    "DIGITAL AHORA",
    "NEXUS SIEMPRE",
]

FORMATOS = {
    "tiktok":  (1080, 1920),
    "reels":   (1080, 1920),
    "youtube": (1920, 1080),
    "square":  (1080, 1080),
}

MARCAS = {
    "NEXUS":     {"hex": "f5c518", "rgb": (245,197,24),  "nombre": "NEXUS by Simplex"},
    "ATF":       {"hex": "00bfff", "rgb": (0,191,255),   "nombre": "ATF"},
    "CANBUSFIX": {"hex": "d4af37", "rgb": (212,175,55),  "nombre": "CanbusFix"},
    "MILENS":    {"hex": "ff6b00", "rgb": (255,107,0),   "nombre": "Milens"},
}

JOBS: dict = {}


# ─── 1. GENERAR ESCENAS CON GROQ ─────────────────────────────────────────────

async def generar_escenas(prompt: str, marca: str) -> dict:
    if not GROQ_KEY:
        return {"ok": False, "error": "Sin GROQ_API_KEY"}
    nombre = MARCAS.get(marca.upper(), MARCAS["NEXUS"])["nombre"]
    p = f"""Crea 6 escenas para video motion graphics de {nombre}.
Prompt: "{prompt}"
Cada escena: texto principal MUY corto (máx 4 palabras), subtítulo (máx 6 palabras).
Responde SOLO JSON sin markdown:
{{"escenas":[
  {{"dur":3,"titulo":"texto","sub":"subtitulo"}},
  {{"dur":4,"titulo":"texto","sub":"subtitulo"}},
  {{"dur":4,"titulo":"texto","sub":"subtitulo"}},
  {{"dur":4,"titulo":"texto","sub":"subtitulo"}},
  {{"dur":3,"titulo":"texto","sub":"subtitulo"}},
  {{"dur":4,"titulo":"{nombre}","sub":"simplexgdl.com"}}
]}}"""
    try:
        import re
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"user","content":p}],
                      "temperature":0.6,"max_tokens":500},
            )
        content = r.json()["choices"][0]["message"]["content"].strip()
        if "```" in content:
            content = content.split("```")[1].lstrip("json").rstrip("`")
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', content)
        d = json.loads(content)
        d["ok"] = True
        return d
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── 2. GENERAR ESCENA MP4 CON FFMPEG ────────────────────────────────────────

def generar_escena(titulo: str, sub: str, dur: float, color_hex: str,
                   w: int, h: int, numero: int, job_dir: Path) -> str:
    out = job_dir / f"sc_{numero:02d}.mp4"

    # Tamaños de fuente según orientación
    fs_main = 100 if w < h else 130
    fs_sub  = 48  if w < h else 60
    fs_num  = 28

    # Escapar texto para FFmpeg (: y ' son problemáticos)
    def esc(t):
        return t.replace("'", "\\'").replace(":", "\\:").replace("%","%%")

    titulo_e = esc(titulo.upper())
    sub_e    = esc(sub)

    # Animaciones usando la variable t de FFmpeg:
    # - Título: sube desde abajo + fade in (0→0.6s) / fade out (dur-0.4 → dur)
    # - Sub:    fade in con delay (0.4→0.9s)
    # - Barra:  crece de izquierda a derecha (0→0.5s)

    # Expresiones de animación
    # NOTA: FFmpeg drawtext no soporta expresiones en fontcolor@alpha.
    # Usar opción alpha='expr' por separado (funciona en -vf).
    alpha_titulo = f"if(lt(t,0.6),t/0.6,if(gt(t,{dur-0.4:.1f}),(t-{dur-0.4:.1f})/0.4,1))"
    y_titulo     = f"if(lt(t,0.6),(h/2-th/2)+150*(1-t/0.6),(h/2-th/2))"
    alpha_sub    = f"if(lt(t,0.4),0,if(lt(t,0.9),(t-0.4)/0.5,if(gt(t,{dur-0.3:.1f}),(t-{dur-0.3:.1f})/0.3,1)))"
    barra_w      = f"if(lt(t,0.5),iw*t/0.5,iw)"

    # Solo el source color en -i; todos los filtros en -vf para soportar alpha dinámico
    vi = f"color=c=0x080808:s={w}x{h}:r=24"

    vf = (
        # barra superior animada
        f"drawbox=x=0:y=0:w='{barra_w}':h=8:color=0x{color_hex}@1:t=fill"
        # barra inferior fija
        f",drawbox=x=0:y=h-8:w=iw:h=8:color=0x{color_hex}@0.4:t=fill"
        # línea central decorativa
        f",drawbox=x=(iw-400)/2:y=h/2+80:w=400:h=2:color=0x{color_hex}@0.3:t=fill"
        # número de escena
        f",drawtext=fontfile='{FONT_REG}':text='{numero+1:02d}':fontsize={fs_num}"
        f":fontcolor=0x{color_hex}:alpha=0.4:x=w-50:y=20"
        # título principal: alpha dinámico + slide desde abajo
        f",drawtext=fontfile='{FONT_BOLD}':text='{titulo_e}':fontsize={fs_main}"
        f":fontcolor=white:alpha='{alpha_titulo}':x=(w-tw)/2:y='{y_titulo}'"
        # subtítulo: fade-in con delay
        f",drawtext=fontfile='{FONT_REG}':text='{sub_e}':fontsize={fs_sub}"
        f":fontcolor=0x{color_hex}:alpha='{alpha_sub}':x=(w-tw)/2:y=(h/2+th/2+50)"
    )

    # ── SUBLIMINAL (solo versión privada NEXUS_PRIVATE=1) ─────────────────────
    if _PRIVATE:
        import hashlib
        msg_idx = int(hashlib.md5(str(numero).encode()).hexdigest(), 16) % len(_SUB_MSGS)
        sub_msg = esc(_SUB_MSGS[msg_idx])
        sx = int(w * 0.25)
        sy = int(h * 0.72)
        vf += (
            f",drawtext=fontfile='{FONT_BOLD}':text='{sub_msg}':fontsize=26"
            f":fontcolor=white:alpha=0.03:x={sx}:y={sy}"
        )

    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", vi,
        "-vf", vf,
        "-t", str(dur),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(out)
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg escena {numero}: {r.stderr.decode()[-200:]}")
    return str(out)


# ─── 3. GENERAR BEAT INDUSTRIAL/ROCK CON NUMPY ───────────────────────────────

def generar_beat_rock(duracion: float, output_path: str, bpm: int = 128) -> bool:
    """
    Genera un beat industrial/rock con numpy.
    Kick + Snare + Hi-hat + Bass line + power chord texture
    """
    try:
        sr = 44100
        n  = int(sr * duracion)
        t  = np.linspace(0, duracion, n, False)
        mix = np.zeros(n)

        beat_dur = 60.0 / bpm        # duración de un beat
        subdiv   = beat_dur / 4      # semicorchea

        # ── KICK DRUM ──
        def kick(start):
            l = int(sr * 0.18)
            tt = np.linspace(0, 0.18, l)
            freq = 120 * np.exp(-18 * tt) + 50
            env  = np.exp(-12 * tt)
            return start, np.sin(2 * np.pi * freq * tt) * env * 0.9

        # ── SNARE ──
        def snare(start):
            l = int(sr * 0.12)
            tt = np.linspace(0, 0.12, l)
            env  = np.exp(-20 * tt)
            noise = np.random.randn(l) * 0.5
            tone  = np.sin(2 * np.pi * 220 * tt) * 0.4
            return start, (noise + tone) * env * 0.7

        # ── HI-HAT ──
        def hihat(start, open=False):
            l = int(sr * (0.08 if not open else 0.18))
            tt = np.linspace(0, l/sr, l)
            env = np.exp(-50 * tt) if not open else np.exp(-15 * tt)
            noise = np.random.randn(l)
            # Filtro pasa-altos básico
            from numpy.fft import rfft, irfft
            f = rfft(noise)
            f[:int(l * 3000 / sr)] = 0
            noise = irfft(f, l)
            return start, noise * env * 0.35

        # ── BASS LINE ──
        bass_notes = [55, 55, 73, 73, 65, 65, 62, 62]  # A1, A1, D2, D2...
        bass_segs  = []
        note_dur   = beat_dur
        for i, freq in enumerate(bass_notes):
            st = i * note_dur
            if st >= duracion: break
            l  = int(sr * min(note_dur * 0.9, duracion - st))
            tt = np.linspace(0, l/sr, l)
            env = np.exp(-3 * tt) * 0.5 + 0.1
            # Sawtooth + distorsión suave
            saw = 2 * (tt * freq % 1) - 1
            dist = np.tanh(saw * 3) * 0.4
            bass_segs.append((st, dist * env * 0.55))

        # ── MEZCLAR ──
        def add(seg, signal):
            si = int(seg * sr)
            end = min(si + len(signal), n)
            mix[si:end] += signal[:end-si]

        total_beats = int(duracion / beat_dur) + 1

        for b in range(total_beats):
            bt = b * beat_dur
            if bt >= duracion: break

            # Kick: beats 1 y 3
            if b % 4 in (0, 2):
                s, sig = kick(bt); add(s, sig)
            # Snare: beats 2 y 4
            if b % 4 in (1, 3):
                s, sig = snare(bt); add(s, sig)
            # Hi-hat: cada subdivisión
            for sub in range(4):
                ht = bt + sub * subdiv
                if ht < duracion:
                    s, sig = hihat(ht, open=(sub == 2)); add(s, sig)

        for bt, sig in bass_segs:
            add(bt, sig)

        # Normalizar y fade out final
        mx = np.max(np.abs(mix))
        if mx > 0:
            mix = mix / mx * 0.88
        fade = int(sr * 1.5)
        mix[-fade:] *= np.linspace(1, 0, fade)

        # Guardar como WAV raw y convertir con FFmpeg
        wav_path = output_path.replace(".mp3", "_raw.wav")
        import wave, struct
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            data = (mix * 32767).astype(np.int16)
            wf.writeframes(data.tobytes())

        # Convertir a MP3
        subprocess.run([
            FFMPEG, "-y", "-i", wav_path,
            "-c:a", "libmp3lame", "-b:a", "192k", output_path
        ], capture_output=True, timeout=30, check=True)
        os.remove(wav_path)
        return True

    except Exception as e:
        print(f"[BEAT] Error: {e}")
        return False


# ─── 4. ENSAMBLAR VIDEO COMPLETO ─────────────────────────────────────────────

def ensamblar_motion(job_dir: Path, clips: list, audio_path: str,
                     output_path: str, w: int, h: int) -> str:
    # Concat clips
    concat_file = job_dir / "concat_mg.txt"
    with open(concat_file, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    video_raw = job_dir / "mg_noaudio.mp4"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(video_raw)
    ], capture_output=True, timeout=120, check=True)

    # Combinar con música
    if os.path.exists(audio_path):
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(video_raw),
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-af", "volume=0.85",
            "-shortest",
            "-movflags", "+faststart",
            output_path
        ], capture_output=True, timeout=120, check=True)
    else:
        import shutil
        shutil.copy(str(video_raw), output_path)

    return output_path


# ─── 5. JOB SYSTEM ───────────────────────────────────────────────────────────

def _run_motion_job(job_id: str, prompt: str, marca: str, formato: str):
    job_dir = OUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    cfg = MARCAS.get(marca.upper(), MARCAS["NEXUS"])

    def upd(status, pct, msg=""):
        JOBS[job_id].update({"status": status, "progress": pct, "msg": msg})

    try:
        import asyncio
        upd("processing", 5, "Generando escenas con IA...")
        data = asyncio.run(generar_escenas(prompt, marca))
        if not data.get("ok"):
            raise RuntimeError(data.get("error", "Error IA"))

        escenas = data["escenas"]
        w, h = FORMATOS.get(formato, (1080, 1920))
        duracion_total = sum(e["dur"] for e in escenas)

        # Generar beat
        upd("processing", 15, "Generando música...")
        beat_path = str(job_dir / "beat.mp3")
        generar_beat_rock(duracion_total + 1.5, beat_path, bpm=130)

        # Generar escenas
        clips = []
        for i, esc in enumerate(escenas):
            upd("processing", 20 + int(60 * i / len(escenas)),
                f"Escena {i+1}/{len(escenas)}...")
            clip = generar_escena(
                titulo=esc["titulo"],
                sub=esc.get("sub", ""),
                dur=float(esc["dur"]),
                color_hex=cfg["hex"],
                w=w, h=h,
                numero=i,
                job_dir=job_dir
            )
            clips.append(clip)

        # Ensamblar
        upd("processing", 85, "Ensamblando video final...")
        output = str(job_dir / "output.mp4")
        ensamblar_motion(job_dir, clips, beat_path, output, w, h)

        JOBS[job_id].update({
            "status": "done", "progress": 100,
            "msg": "Video listo",
            "url": f"/out/promos/{job_id}/output.mp4",
            "escenas": len(escenas),
        })

    except Exception as e:
        JOBS[job_id].update({"status": "error", "progress": 0,
                             "msg": str(e), "error": str(e)})


def iniciar_motion_job(prompt: str, marca: str = "NEXUS",
                       formato: str = "tiktok") -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"status": "queued", "progress": 0,
                    "msg": "En cola...", "job_id": job_id}
    t = threading.Thread(
        target=_run_motion_job,
        args=(job_id, prompt, marca, formato), daemon=True
    )
    t.start()
    return job_id


def estado_job(job_id: str) -> dict:
    return JOBS.get(job_id, {"status": "not_found"})

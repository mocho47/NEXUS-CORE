import os
import time
import importlib
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")


def _now() -> float:
    return time.time()


def _try_import(mod: str) -> Tuple[bool, str]:
    try:
        importlib.import_module(mod)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def healthcheck() -> Dict:
    """Chequeo local rápido. No usa nube."""
    required = [
        "vosk",
        "psutil",
        "watchdog",
        "duckduckgo_search",
        "wikipedia",
        "requests",
        "keyboard",
        "pyttsx3",
        # Paquete pip: SpeechRecognition ; módulo import: speech_recognition
        "speech_recognition",
        # Core imports
        "dotenv",
        "edge_tts",
        "pygame",
        "clipboard",
        "AppOpener",
        # Nube (importado por nexus_db)
        "supabase",
    ]

    optional = [
        "groq",
        "pyautogui",
        "pychromecast",
        "moviepy",
    ]

    req_results = []
    for m in required:
        ok, msg = _try_import(m)
        req_results.append({"module": m, "ok": ok, "error": None if ok else msg})

    opt_results = []
    for m in optional:
        ok, msg = _try_import(m)
        opt_results.append({"module": m, "ok": ok, "error": None if ok else msg})

    dirs = {
        "CONFIG": CONFIG_DIR,
        "DROP_IN": os.path.join(BASE_DIR, "DROP_IN"),
        "INBOX": os.path.join(BASE_DIR, "DROP_IN", "INBOX"),
    }

    dir_results = []
    for k, p in dirs.items():
        try:
            os.makedirs(p, exist_ok=True)
            dir_results.append({"name": k, "path": p, "ok": True})
        except Exception as e:
            dir_results.append({"name": k, "path": p, "ok": False, "error": str(e)})

    # Chequeos de archivos/carpetas locales (sin nube)
    base_dir = BASE_DIR
    files = []
    try:
        model_dir = os.path.join(base_dir, "CEREBRO", "model")
        files.append({"name": "vosk_model_dir", "path": model_dir, "ok": os.path.isdir(model_dir)})
    except Exception as e:
        files.append({"name": "vosk_model_dir", "path": None, "ok": False, "error": str(e)})

    for exe in ("ffmpeg.exe", "ffprobe.exe"):
        try:
            p = os.path.join(base_dir, exe)
            files.append({"name": exe, "path": p, "ok": os.path.isfile(p)})
        except Exception as e:
            files.append({"name": exe, "path": None, "ok": False, "error": str(e)})

    # Variables de entorno (no bloqueantes)
    env = {
        "GROQ_API_KEY": bool(os.environ.get("GROQ_API_KEY")),
    }

    return {
        "ts": _now(),
        "required": req_results,
        "optional": opt_results,
        "dirs": dir_results,
        "files": files,
        "env": env,
    }


def summarize_healthcheck(hc: Dict) -> Tuple[str, List[str]]:
    req = hc.get("required") or []
    opt = hc.get("optional") or []
    files = hc.get("files") or []

    missing_req = [x["module"] for x in req if not x.get("ok")]
    missing_opt = [x["module"] for x in opt if not x.get("ok")]
    missing_files = [x.get("name") for x in files if isinstance(x, dict) and not x.get("ok")]

    summary = (
        f"Salud local: requeridos faltantes {len(missing_req)}, "
        f"opcionales faltantes {len(missing_opt)}, "
        f"archivos/recursos faltantes {len(missing_files)}."
    )
    actions = []
    if missing_req:
        actions.append("install_required")
    if missing_opt:
        actions.append("install_optional")
    if missing_files:
        actions.append("fix_local_assets")
    return summary, actions


def module_to_pip(module_name: str) -> Optional[str]:
    """Mapea nombre de módulo importable -> nombre de paquete pip."""
    m = (module_name or "").strip()
    if not m:
        return None

    mapping = {
        "speech_recognition": "SpeechRecognition",
        "dotenv": "python-dotenv",
        "edge_tts": "edge-tts",
        "duckduckgo_search": "duckduckgo_search",
        "AppOpener": "AppOpener",
        "pyttsx3": "pyttsx3",
        "pychromecast": "pychromecast",
        "supabase": "supabase",
        "moviepy": "moviepy",
        "pygame": "pygame",
    }
    return mapping.get(m, m)


def pip_packages_for_missing(modules: List[str]) -> List[str]:
    pkgs: List[str] = []
    seen = set()
    for mod in modules or []:
        pkg = module_to_pip(mod)
        if not pkg:
            continue
        if pkg not in seen:
            seen.add(pkg)
            pkgs.append(pkg)
    return pkgs


def pip_install(modules: List[str]) -> Tuple[bool, str]:
    """Instala paquetes con pip. Debe ejecutarse bajo confirmación del usuario."""
    mods = [m for m in (modules or []) if isinstance(m, str) and m.strip()]
    if not mods:
        return False, "Nada que instalar."

    try:
        cmd = [sys.executable, "-m", "pip", "install", *mods]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        ok = proc.returncode == 0
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        out = out.strip()[-4000:]
        return ok, out
    except Exception as e:
        return False, str(e)

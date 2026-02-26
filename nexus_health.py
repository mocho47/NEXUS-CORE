"""
nexus_health.py — Auto-diagnóstico y monitoreo de NEXUS
Verifica dependencias, APIs, apps, disco, DB y módulos críticos.
Puede pedir diagnóstico asistido al LLM (Groq).
"""
import os, sys, time, importlib
from pathlib import Path
from datetime import datetime

_BASE = Path(__file__).parent
_OUT  = _BASE / "out"

# ── Dependencias críticas por módulo ─────────────────────────────────────────
_DEPS = {
    "Core servidor":    ["fastapi", "uvicorn", "jinja2", "python-multipart"],
    "Base de datos":    ["supabase", "sqlite3"],
    "IA / Voz":         ["groq", "edge_tts", "pygame"],
    "Estudio imagen":   ["PIL", "cv2", "numpy", "reportlab"],
    "Estudio vector":   ["ezdxf", "svgpathtools", "shapely"],
    "Generador cajas":  ["boxes"],
    "Motores apps":     ["win32com"],
    "Voz paranormal":   ["pyttsx3"],
}

_IMPORT_MAP = {
    "PIL":              "PIL",
    "cv2":              "cv2",
    "python-multipart": "multipart",
    "edge_tts":         "edge_tts",
    "win32com":         "win32com.client",
    "sqlite3":          "sqlite3",
}

# ── Apps externas esperadas ───────────────────────────────────────────────────
_APPS = {
    "CorelDRAW":        r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelDRW.exe",
    "Silhouette Studio":r"C:\Program Files\Silhouette America\Silhouette Studio\Silhouette Studio.exe",
    "Aspire":           r"C:\Users\anuar\Desktop\SOFTWARE_RECUPERADO\Aspire 10.5\x64\Aspire.exe",
}

# ── Archivos críticos de NEXUS ────────────────────────────────────────────────
_ARCHIVOS = [
    "nexus_server.py",
    "nexus_estudio.py",
    "nexus_studio_vector.py",
    "nexus_boxes_gen.py",
    "nexus_motors.py",
    "nexus_voice.py",
    ".env",
    "WEB/templates/dashboard.html",
    "WEB/templates/estudio.html",
]


def _check_import(nombre: str) -> bool:
    modulo = _IMPORT_MAP.get(nombre, nombre.replace("-", "_"))
    try:
        importlib.import_module(modulo)
        return True
    except ImportError:
        return False


def check_dependencias() -> dict:
    resultados = {}
    for grupo, paquetes in _DEPS.items():
        items = []
        for pkg in paquetes:
            ok = _check_import(pkg)
            items.append({"nombre": pkg, "ok": ok})
        resultados[grupo] = items
    return resultados


def check_env() -> dict:
    """Verifica variables de entorno críticas."""
    from dotenv import load_dotenv
    load_dotenv(_BASE / ".env")
    claves = {
        "GROQ_API_KEY":       bool(os.getenv("GROQ_API_KEY")),
        "SUPABASE_URL":       bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_KEY":       bool(os.getenv("SUPABASE_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "META_ACCESS_TOKEN":  bool(os.getenv("META_ACCESS_TOKEN")),
    }
    return claves


def check_groq() -> dict:
    """Prueba conexión real a Groq."""
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv(_BASE / ".env")
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "di solo: ok"}],
            max_tokens=5,
        )
        return {"ok": True, "respuesta": resp.choices[0].message.content.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def check_supabase() -> dict:
    """Prueba conexión a Supabase."""
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv(_BASE / ".env")
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            return {"ok": False, "error": "Credenciales no configuradas"}
        sb = create_client(url, key)
        sb.table("pedidos").select("id").limit(1).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def check_sqlite() -> dict:
    """Verifica base de datos local."""
    db = _BASE / "nexus_v2.db"
    if not db.exists():
        return {"ok": False, "error": "nexus_v2.db no encontrado"}
    try:
        import sqlite3
        con = sqlite3.connect(str(db))
        tablas = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        con.close()
        return {"ok": True, "tablas": len(tablas)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


def check_apps() -> dict:
    """Verifica apps externas instaladas."""
    return {
        nombre: {"ok": Path(ruta).exists(), "ruta": ruta}
        for nombre, ruta in _APPS.items()
    }


def check_disco() -> dict:
    """Verifica espacio en disco y carpeta out/."""
    import shutil
    total, usado, libre = shutil.disk_usage(_BASE)
    _OUT.mkdir(exist_ok=True)
    archivos_out = list(_OUT.glob("*"))
    tam_out = sum(f.stat().st_size for f in archivos_out if f.is_file())
    return {
        "libre_gb":   round(libre / 1e9, 1),
        "usado_gb":   round(usado / 1e9, 1),
        "total_gb":   round(total / 1e9, 1),
        "out_archivos": len(archivos_out),
        "out_mb":     round(tam_out / 1e6, 1),
        "alerta":     libre < 2e9,  # alerta si menos de 2GB libres
    }


def check_archivos() -> dict:
    """Verifica existencia de archivos críticos de NEXUS."""
    return {
        f: (_BASE / f).exists()
        for f in _ARCHIVOS
    }


def check_servidor() -> dict:
    """Verifica si el servidor NEXUS responde."""
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:8000/api/setup/check", timeout=3)
        return {"ok": req.status == 200, "status": req.status}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


def reporte_completo() -> dict:
    """Ejecuta todos los checks y devuelve reporte estructurado."""
    t0 = time.time()
    reporte = {
        "timestamp":     datetime.now().isoformat(),
        "servidor":      check_servidor(),
        "dependencias":  check_dependencias(),
        "env":           check_env(),
        "groq":          check_groq(),
        "supabase":      check_supabase(),
        "sqlite":        check_sqlite(),
        "apps":          check_apps(),
        "disco":         check_disco(),
        "archivos":      check_archivos(),
        "duracion_s":    round(time.time() - t0, 2),
    }
    # Calcular score global
    alertas = []
    if not reporte["servidor"]["ok"]:
        alertas.append("Servidor caido")
    if not reporte["groq"]["ok"]:
        alertas.append("Groq sin conexion")
    if reporte["disco"]["alerta"]:
        alertas.append(f"Disco bajo: {reporte['disco']['libre_gb']}GB libres")
    faltantes = [f for f, existe in reporte["archivos"].items() if not existe]
    if faltantes:
        alertas.append(f"Archivos faltantes: {', '.join(faltantes)}")
    deps_faltantes = [
        pkg["nombre"]
        for grupo in reporte["dependencias"].values()
        for pkg in grupo if not pkg["ok"]
    ]
    if deps_faltantes:
        alertas.append(f"Dependencias faltantes: {', '.join(deps_faltantes)}")

    reporte["alertas"]  = alertas
    reporte["estado"]   = "OK" if not alertas else ("ALERTA" if len(alertas) < 3 else "CRITICO")
    return reporte


def diagnostico_llm(reporte: dict) -> str:
    """
    Pide a Groq que analice el reporte y sugiera acciones.
    Solo se llama cuando hay alertas.
    """
    if not reporte.get("alertas"):
        return "Todo en orden, no se requiere diagnostico."
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv(_BASE / ".env")
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        resumen = (
            f"Sistema NEXUS — Estado: {reporte['estado']}\n"
            f"Alertas: {reporte['alertas']}\n"
            f"Disco libre: {reporte['disco']['libre_gb']}GB\n"
            f"Servidor: {'OK' if reporte['servidor']['ok'] else 'CAIDO'}\n"
            f"Groq: {'OK' if reporte['groq']['ok'] else 'ERROR'}\n"
        )
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": "Eres el asistente de soporte de NEXUS. Da instrucciones concretas y cortas en español para resolver los problemas detectados."
            }, {
                "role": "user",
                "content": f"Analiza este reporte y di qué hacer:\n{resumen}"
            }],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"No se pudo consultar al LLM: {e}"


def instalar_faltantes(deps_faltantes: list[str]) -> list[dict]:
    """Intenta instalar dependencias faltantes via pip."""
    _PIP_MAP = {
        "PIL":       "Pillow",
        "cv2":       "opencv-python",
        "shapely":   "shapely",
        "ezdxf":     "ezdxf",
        "svgpathtools": "svgpathtools",
        "reportlab": "reportlab",
        "pyttsx3":   "pyttsx3",
        "groq":      "groq",
        "supabase":  "supabase",
        "boxes":     "git+https://github.com/florianfesti/boxes.git",
    }
    resultados = []
    for dep in deps_faltantes:
        pkg = _PIP_MAP.get(dep, dep)
        try:
            import subprocess
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                capture_output=True, text=True, timeout=60
            )
            ok = r.returncode == 0
            resultados.append({"dep": dep, "pkg": pkg, "ok": ok,
                                "msg": "" if ok else r.stderr[-100:]})
        except Exception as e:
            resultados.append({"dep": dep, "pkg": pkg, "ok": False, "msg": str(e)})
    return resultados


if __name__ == "__main__":
    print("NEXUS Health Check...")
    r = reporte_completo()
    print(f"Estado: {r['estado']} ({r['duracion_s']}s)")
    if r["alertas"]:
        print("Alertas:")
        for a in r["alertas"]: print(f"  - {a}")
        print("\nDiagnostico LLM:")
        print(diagnostico_llm(r))
    else:
        print("Todo en orden.")

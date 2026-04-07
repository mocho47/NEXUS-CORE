"""
motor_sistema.py — Control total del sistema
Puerto 8009

Z.ai puede usar este motor para:
- Ejecutar comandos en Windows
- Gestionar procesos (iniciar, detener, monitorear)
- Leer y escribir archivos
- Actualizar código de NEXUS desde GitHub
- Monitorear recursos (CPU, RAM, disco)
- Administrar la configuración del sistema
"""

import os, sys, json, shutil, subprocess, platform, time, psutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

NEXUS_DIR = Path("C:/NEXUS_v3_NEW")

app = FastAPI(title="NEXUS Motor Sistema", version="3.0")

# ═══════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════
class ComandoRequest(BaseModel):
    cmd: str
    cwd: Optional[str] = str(NEXUS_DIR)
    timeout: Optional[int] = 30

class ArchivoRequest(BaseModel):
    ruta: str
    contenido: str
    encoding: Optional[str] = "utf-8"

class ProcesoRequest(BaseModel):
    nombre: str  # nombre del proceso o PID

class GitRequest(BaseModel):
    mensaje: Optional[str] = "NEXUS auto-commit"
    push: Optional[bool] = True

# ═══════════════════════════════════════════════
# ESTADO DEL SISTEMA
# ═══════════════════════════════════════════════
@app.get("/sistema/estado")
async def estado_sistema():
    """Estado completo del hardware y procesos de NEXUS."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    discos = []
    for part in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(part.mountpoint)
            discos.append({
                "disco": part.device,
                "total_gb": round(uso.total / 1024**3, 1),
                "libre_gb": round(uso.free / 1024**3, 1),
                "uso_pct": uso.percent
            })
        except:
            pass

    # Procesos NEXUS activos
    nexus_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'nexus' in cmdline.lower() or 'motor_' in cmdline.lower():
                nexus_procs.append({
                    "pid": proc.info['pid'],
                    "nombre": proc.info['name'],
                    "cmd": cmdline[:80],
                    "ram_mb": round(proc.info['memory_info'].rss / 1024**2, 1)
                })
        except:
            pass

    return {
        "ok": True,
        "cpu_pct": cpu,
        "ram": {
            "total_gb": round(ram.total / 1024**3, 1),
            "usada_gb": round(ram.used / 1024**3, 1),
            "libre_gb": round(ram.available / 1024**3, 1),
            "pct": ram.percent
        },
        "pagefile_gb": round(swap.total / 1024**3, 1),
        "discos": discos,
        "nexus_procesos": nexus_procs,
        "python": sys.version.split()[0],
        "os": f"{platform.system()} {platform.release()}"
    }

@app.get("/sistema/procesos")
async def listar_procesos():
    """Todos los procesos Python corriendo."""
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'status']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                procs.append({
                    "pid": proc.info['pid'],
                    "cmd": cmdline[:100],
                    "ram_mb": round(proc.info['memory_info'].rss / 1024**2, 1),
                    "estado": proc.info['status']
                })
        except:
            pass
    return {"ok": True, "procesos": procs, "total": len(procs)}

# ═══════════════════════════════════════════════
# EJECUTAR COMANDOS
# ═══════════════════════════════════════════════
@app.post("/sistema/ejecutar")
async def ejecutar_comando(req: ComandoRequest):
    """
    Ejecuta un comando en la PC.
    Z.ai puede usar esto para cualquier operacion del sistema.
    ADVERTENCIA: poder total — usar con cuidado.
    """
    try:
        result = subprocess.run(
            req.cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=req.timeout,
            cwd=req.cwd or str(NEXUS_DIR)
        )
        return {
            "ok": result.returncode == 0,
            "codigo": result.returncode,
            "stdout": result.stdout.strip()[:2000],
            "stderr": result.stderr.strip()[:500]
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout ({req.timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/sistema/ejecutar_bg")
async def ejecutar_background(req: ComandoRequest):
    """Ejecuta un comando en background (no espera resultado)."""
    try:
        subprocess.Popen(
            req.cmd,
            shell=True,
            cwd=req.cwd or str(NEXUS_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return {"ok": True, "mensaje": f"Ejecutando en background: {req.cmd[:80]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════
# GESTIONAR PROCESOS
# ═══════════════════════════════════════════════
@app.post("/sistema/matar_proceso")
async def matar_proceso(req: ProcesoRequest):
    """Detiene un proceso por nombre o PID."""
    muertos = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if (req.nombre.isdigit() and proc.info['pid'] == int(req.nombre)) or \
               (req.nombre.lower() in cmdline.lower() or req.nombre.lower() in proc.info['name'].lower()):
                proc.terminate()
                muertos.append(proc.info['pid'])
        except:
            pass
    return {"ok": True, "pids_terminados": muertos, "total": len(muertos)}

@app.post("/sistema/reiniciar_nexus")
async def reiniciar_nexus():
    """Reinicia todo el stack de NEXUS."""
    # Matar procesos actuales
    subprocess.run('taskkill /F /IM python.exe /FI "WINDOWTITLE eq NEXUS*"',
                   shell=True, capture_output=True)
    time.sleep(2)
    # Reiniciar
    subprocess.Popen(
        str(NEXUS_DIR / "INICIAR_NEXUS_v3.bat"),
        shell=True,
        cwd=str(NEXUS_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    return {"ok": True, "mensaje": "NEXUS reiniciando..."}

# ═══════════════════════════════════════════════
# ARCHIVOS
# ═══════════════════════════════════════════════
@app.get("/sistema/leer")
async def leer_archivo(ruta: str):
    """Lee cualquier archivo de texto del sistema."""
    try:
        path = Path(ruta)
        if not path.exists():
            raise HTTPException(404, f"No encontrado: {ruta}")
        contenido = path.read_text(encoding='utf-8', errors='ignore')
        return {
            "ok": True,
            "ruta": str(path),
            "tamaño_kb": round(path.stat().st_size / 1024, 1),
            "contenido": contenido[:50000]  # máx 50KB
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/sistema/escribir")
async def escribir_archivo(req: ArchivoRequest):
    """Escribe o sobreescribe un archivo."""
    try:
        path = Path(req.ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(req.contenido, encoding=req.encoding)
        return {
            "ok": True,
            "ruta": str(path),
            "tamaño_kb": round(path.stat().st_size / 1024, 1)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/sistema/listar")
async def listar_directorio(ruta: str, extension: Optional[str] = None):
    """Lista archivos en un directorio."""
    try:
        path = Path(ruta)
        if not path.exists():
            raise HTTPException(404, f"No encontrado: {ruta}")
        archivos = []
        for f in sorted(path.iterdir()):
            if extension and not f.name.endswith(extension):
                continue
            archivos.append({
                "nombre": f.name,
                "es_dir": f.is_dir(),
                "tamaño_kb": round(f.stat().st_size / 1024, 1) if f.is_file() else 0
            })
        return {"ok": True, "ruta": str(path), "archivos": archivos, "total": len(archivos)}
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/sistema/eliminar")
async def eliminar_archivo(ruta: str):
    """Elimina un archivo o directorio."""
    try:
        path = Path(ruta)
        if not path.exists():
            return {"ok": False, "error": "No encontrado"}
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        return {"ok": True, "eliminado": str(path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ═══════════════════════════════════════════════
# CODIGO — ACTUALIZAR DESDE GITHUB
# ═══════════════════════════════════════════════
@app.post("/sistema/git_pull")
async def actualizar_desde_github():
    """Actualiza el código de NEXUS desde GitHub (rama v3)."""
    result = subprocess.run(
        'git pull origin v3',
        shell=True, capture_output=True, text=True,
        cwd=str(NEXUS_DIR), encoding='utf-8', errors='ignore'
    )
    return {
        "ok": result.returncode == 0,
        "output": result.stdout.strip(),
        "errores": result.stderr.strip()[:300]
    }

@app.post("/sistema/git_push")
async def subir_cambios_github(req: GitRequest):
    """Hace commit y push de cambios a GitHub."""
    cmds = [
        f'git -C "{NEXUS_DIR}" add -A',
        f'git -C "{NEXUS_DIR}" commit -m "{req.mensaje}"',
    ]
    if req.push:
        cmds.append(f'git -C "{NEXUS_DIR}" push origin v3')

    resultados = []
    for cmd in cmds:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding='utf-8', errors='ignore')
        resultados.append({
            "cmd": cmd.split('"')[-1] if '"' in cmd else cmd,
            "ok": r.returncode == 0,
            "out": r.stdout.strip()[:200]
        })
        if r.returncode != 0 and 'nothing to commit' not in r.stdout:
            break

    return {"ok": all(r["ok"] for r in resultados), "pasos": resultados}

@app.get("/sistema/git_status")
async def estado_git():
    """Estado actual del repositorio git."""
    r = subprocess.run('git status --short', shell=True, capture_output=True,
                      text=True, cwd=str(NEXUS_DIR), encoding='utf-8')
    r2 = subprocess.run('git log --oneline -5', shell=True, capture_output=True,
                       text=True, cwd=str(NEXUS_DIR), encoding='utf-8')
    return {
        "ok": True,
        "cambios": r.stdout.strip(),
        "ultimos_commits": r2.stdout.strip()
    }

# ═══════════════════════════════════════════════
# SDK — INVENTARIO LIVE
# ═══════════════════════════════════════════════
@app.get("/sistema/sdks")
async def inventario_sdks():
    """Lista todos los SDKs instalados que Z.ai puede usar."""
    sdks_clave = [
        'groq', 'openai', 'transformers', 'torch', 'whisper',
        'instagrapi', 'twilio', 'playwright', 'google-api-python-client',
        'Pillow', 'opencv-python', 'reportlab', 'fpdf2', 'ezdxf',
        'moviepy', 'ffmpeg-python', 'aiosqlite', 'supabase',
        'qrcode', 'edge-tts', 'fastapi', 'httpx', 'psutil', 'litellm'
    ]

    disponibles = []
    no_disponibles = []

    for pkg in sdks_clave:
        modulo = pkg.lower().replace('-', '_').replace('google_api_python_client', 'googleapiclient')
        try:
            __import__(modulo.split('.')[0])
            disponibles.append(pkg)
        except ImportError:
            no_disponibles.append(pkg)

    return {
        "ok": True,
        "disponibles": disponibles,
        "no_instalados": no_disponibles,
        "total_disponibles": len(disponibles)
    }

# ═══════════════════════════════════════════════
# OLLAMA — CONTROL LOCAL
# ═══════════════════════════════════════════════
@app.get("/sistema/ollama")
async def estado_ollama():
    """Estado de Ollama y modelos disponibles."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:11434/api/tags")
            data = r.json()
            modelos = [m['name'] for m in data.get('models', [])]
            return {"ok": True, "online": True, "modelos": modelos}
    except:
        return {"ok": False, "online": False, "modelos": []}

@app.post("/sistema/ollama_pull")
async def descargar_modelo(modelo: str):
    """Descarga un modelo en Ollama en background."""
    subprocess.Popen(
        f'start "Ollama pull {modelo}" cmd /c ollama pull {modelo}',
        shell=True
    )
    return {"ok": True, "mensaje": f"Descargando {modelo} en background"}

# ═══════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("NEXUS Motor Sistema — Puerto 8009")
    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="warning")

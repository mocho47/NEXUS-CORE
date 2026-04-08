"""
motor_watchdog.py — Guardián y Optimizador de NEXUS
Puerto 8011

Dos niveles de monitoreo:
  1. Ping ligero cada 5 min → solo verifica que motores respondan
  2. Limpieza profunda 4×/día (06:00, 12:00, 18:00, 00:00) →
       limpia temps, mata duplicados, reporta estado

PC con 7.2GB RAM — se cuida la huella al máximo.
"""

import os, sys, time, json, asyncio, subprocess, psutil, httpx, logging, shutil
from pathlib import Path
from datetime import datetime, time as dtime
import threading

NEXUS_DIR = Path("C:/NEXUS_v3_NEW")
LOGS_DIR  = NEXUS_DIR / "logs"
DATA_DIR  = NEXUS_DIR / "data"

LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / "watchdog.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("watchdog")

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
except ImportError:
    pass

app = FastAPI(title="NEXUS Watchdog", version="3.1")

# ═══════════════════════════════════════════════
# CONFIGURACION DE MOTORES
# ═══════════════════════════════════════════════
MOTORES = {
    "nexus_core":     {"puerto": 8003, "archivo": "nexus_core.py",            "critico": True},
    "motor_atf":      {"puerto": 8004, "archivo": "motors/motor_atf.py",      "critico": True},
    "motor_teens":    {"puerto": 8005, "archivo": "motors/motor_teens.py",    "critico": False},
    "motor_auth":     {"puerto": 8006, "archivo": "motors/motor_auth.py",     "critico": True},
    "motor_pagos":    {"puerto": 8007, "archivo": "motors/motor_pagos.py",    "critico": True},
    "motor_reportes": {"puerto": 8008, "archivo": "motors/motor_reportes.py", "critico": False},
    "motor_sistema":  {"puerto": 8009, "archivo": "motors/motor_sistema.py",  "critico": True},
    "motor_redes":    {"puerto": 8010, "archivo": "motors/motor_redes.py",    "critico": False},
    "motor_watchdog": {"puerto": 8011, "archivo": "motors/motor_watchdog.py", "critico": True},
    "motor_forja":    {"puerto": 8012, "archivo": "motors/motor_forja.py",    "critico": False},
}

# Endpoints a revisar por motor (ping ligero)
ENDPOINTS_PING = {
    8003: "/api/status",
    8004: "/atf/kits",
    8005: "/teens/misiones",
    8006: "/auth/estado",
    8007: "/pagos/resumen",
    8008: "/reportes/resumen-diario",
    8009: "/sistema/estado",
    8010: "/redes/estado",
    8011: "/watchdog/estado",
    8012: "/forja/diagnostico",
}

# Horarios de limpieza profunda (4 veces al día)
HORAS_LIMPIEZA = {6, 12, 18, 0}

# Umbrales
UMBRAL_RAM_PCT   = 80   # % RAM para activar liberación de emergencia
UMBRAL_DISCO_PCT = 90   # % disco
INTERVALO_PING   = 300  # 5 minutos entre pings ligeros

# Estado global
_estado_motores = {}
_alertas_activas = []
_ultimo_check = None
_ultimo_limpieza = None
_metricas_historico = []

# ═══════════════════════════════════════════════
# PING LIGERO — cada 5 minutos
# ═══════════════════════════════════════════════
async def ping_motor(nombre: str, puerto: int) -> dict:
    """HTTP ping rápido. Sin bloquear CPU."""
    endpoint = ENDPOINTS_PING.get(puerto, "/")
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"http://localhost:{puerto}{endpoint}")
            return {"activo": r.status_code < 500, "status": r.status_code}
    except Exception as e:
        return {"activo": False, "status": 0, "error": str(e)[:60]}


async def loop_ping():
    """Ping ligero a todos los motores cada 5 minutos."""
    global _estado_motores, _ultimo_check

    log.info("Watchdog iniciado — ping cada 5 min, limpieza 4×/día")
    motores_caidos_count = {k: 0 for k in MOTORES}

    while True:
        timestamp = datetime.now().isoformat()
        hora_actual = datetime.now().hour

        # ── Ping a todos los motores
        for nombre, cfg in MOTORES.items():
            if nombre == "motor_watchdog":
                continue  # no se auto-pinga
            estado = await ping_motor(nombre, cfg["puerto"])
            _estado_motores[nombre] = {**estado, "ts": timestamp}

            if not estado["activo"]:
                motores_caidos_count[nombre] = motores_caidos_count.get(nombre, 0) + 1
                if motores_caidos_count[nombre] >= 2:
                    log.warning(f"Motor caído x2: {nombre} — reiniciando")
                    await reiniciar_motor(nombre, cfg["archivo"])
                    motores_caidos_count[nombre] = 0
            else:
                motores_caidos_count[nombre] = 0

        # ── Verificar RAM de emergencia (sin bloquear CPU — interval=0)
        ram = psutil.virtual_memory()
        if ram.percent > UMBRAL_RAM_PCT:
            log.warning(f"RAM emergencia: {ram.percent}% — activando liberación")
            await liberar_ram_emergencia()

        _ultimo_check = timestamp

        # ── Guardar snapshot ligero
        try:
            snap = {
                "ts": timestamp,
                "ram_pct": round(ram.percent, 1),
                "ram_libre_mb": round(ram.available / 1024**2),
                "motores_ok": sum(1 for m in _estado_motores.values() if m.get("activo")),
                "motores_total": len(MOTORES) - 1,  # -1 watchdog
            }
            _metricas_historico.append(snap)
            if len(_metricas_historico) > 576:  # 48h a 5min
                _metricas_historico.pop(0)
        except Exception:
            pass

        # ── Limpieza profunda si es hora
        if hora_actual in HORAS_LIMPIEZA:
            minuto = datetime.now().minute
            if minuto < 6:  # ejecutar solo en los primeros 5 min de cada hora clave
                ultima = _ultimo_limpieza
                if ultima is None or (datetime.now() - ultima).seconds > 3600:
                    log.info(f"Iniciando limpieza profunda — {hora_actual}:00h")
                    await limpieza_profunda()

        await asyncio.sleep(INTERVALO_PING)


# ═══════════════════════════════════════════════
# REINICIO DE MOTOR
# ═══════════════════════════════════════════════
async def reiniciar_motor(nombre: str, archivo: str) -> bool:
    log.warning(f"Reiniciando: {nombre}")
    # Matar proceso existente
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = ' '.join(proc.info['cmdline'] or [])
            if archivo.replace('/', '\\') in cmd or archivo in cmd:
                proc.terminate()
                await asyncio.sleep(1)
        except Exception:
            pass

    await asyncio.sleep(2)

    try:
        subprocess.Popen(
            f'start "NEXUS {nombre}" /min python "{NEXUS_DIR / archivo}"',
            shell=True, cwd=str(NEXUS_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        await asyncio.sleep(5)
        info = MOTORES.get(nombre, {})
        r = await ping_motor(nombre, info.get("puerto", 8003))
        if r["activo"]:
            log.info(f"Motor reiniciado OK: {nombre}")
            return True
        log.error(f"Motor no levantó: {nombre}")
        return False
    except Exception as e:
        log.error(f"Error reiniciando {nombre}: {e}")
        return False


# ═══════════════════════════════════════════════
# LIBERACIÓN DE RAM DE EMERGENCIA
# ═══════════════════════════════════════════════
async def liberar_ram_emergencia():
    """Mata duplicados Python y vacía working set. Rápido."""
    archivos_nexus = {cfg["archivo"] for cfg in MOTORES.values()}
    vistos = set()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            name = proc.info['name'].lower()
            cmd  = ' '.join(proc.info['cmdline'] or [])
            if 'python' not in name:
                continue

            # Detectar archivo NEXUS que corre
            archivo_key = None
            for arch in archivos_nexus:
                if arch in cmd or arch.replace('/', '\\') in cmd:
                    archivo_key = arch
                    break

            if archivo_key:
                if archivo_key in vistos:
                    # Duplicado — matar
                    proc.terminate()
                    log.info(f"Duplicado eliminado: PID {proc.info['pid']} ({archivo_key})")
                else:
                    vistos.add(archivo_key)
            else:
                # Python que no es NEXUS ni Ollama ni Claude — evaluar
                ram_mb = proc.info['memory_info'].rss / 1024**2
                if ram_mb > 400 and 'ollama' not in cmd.lower() and 'claude' not in cmd.lower():
                    proc.terminate()
                    log.info(f"Proceso externo terminado: PID {proc.info['pid']} ({ram_mb:.0f}MB)")
        except Exception:
            pass


# ═══════════════════════════════════════════════
# LIMPIEZA PROFUNDA 4×/DÍA
# ═══════════════════════════════════════════════
async def limpieza_profunda():
    """Limpieza completa del sistema. Corre 4 veces al día."""
    global _ultimo_limpieza
    inicio = datetime.now()
    reporte = {"inicio": inicio.isoformat(), "acciones": [], "liberado_mb": 0}

    # 1. Matar procesos Python duplicados
    await liberar_ram_emergencia()
    reporte["acciones"].append("duplicados_python")

    # 2. Limpiar carpetas temp de Windows
    carpetas_temp = [
        Path(os.environ.get("TEMP", "C:/Windows/Temp")),
        Path(os.environ.get("TMP",  "C:/Windows/Temp")),
        Path("C:/Windows/Temp"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
    ]
    for carpeta in carpetas_temp:
        if carpeta.exists():
            liberado = _limpiar_carpeta(carpeta)
            reporte["liberado_mb"] += liberado
            if liberado > 0:
                reporte["acciones"].append(f"temp:{carpeta.name}:{liberado}MB")

    # 3. Limpiar logs NEXUS > 5MB
    for log_file in LOGS_DIR.glob("*.log"):
        try:
            size_mb = log_file.stat().st_size / 1024**2
            if size_mb > 5:
                # Conservar últimas 500 líneas
                lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
                log_file.write_text('\n'.join(lines[-500:]), encoding='utf-8')
                reporte["acciones"].append(f"log_truncado:{log_file.name}:{size_mb:.1f}MB→ultimas500")
        except Exception:
            pass

    # 4. Limpiar cache de thumbnails Windows
    thumb_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Explorer"
    if thumb_dir.exists():
        liberado = _limpiar_carpeta(thumb_dir, extension="*.db")
        reporte["liberado_mb"] += liberado
        if liberado > 0:
            reporte["acciones"].append(f"thumbnails:{liberado}MB")

    # 5. Métricas post-limpieza
    ram = psutil.virtual_memory()
    reporte["ram_post_pct"]    = round(ram.percent, 1)
    reporte["ram_libre_post_mb"] = round(ram.available / 1024**2)
    reporte["duracion_seg"]    = round((datetime.now() - inicio).total_seconds(), 1)

    # Guardar reporte
    reporte_file = DATA_DIR / f"limpieza_{inicio.strftime('%Y%m%d_%H%M')}.json"
    reporte_file.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding='utf-8')

    _ultimo_limpieza = datetime.now()
    log.info(f"Limpieza profunda OK — {reporte['liberado_mb']}MB liberados — RAM: {reporte['ram_post_pct']}%")
    return reporte


def _limpiar_carpeta(carpeta: Path, extension: str = "*") -> int:
    """Elimina archivos de una carpeta. Devuelve MB liberados."""
    liberado = 0
    try:
        patron = carpeta.glob(extension) if extension != "*" else carpeta.glob("*")
        for item in patron:
            try:
                size = item.stat().st_size
                if item.is_file():
                    item.unlink()
                    liberado += size
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    liberado += size
            except Exception:
                pass
    except Exception:
        pass
    return round(liberado / 1024**2, 1)


# ═══════════════════════════════════════════════
# RECURSOS DEL SISTEMA (NO BLOQUEA CPU)
# ═══════════════════════════════════════════════
def recursos_sistema() -> dict:
    ram = psutil.virtual_memory()
    # cpu_percent sin interval para no bloquear
    cpu = psutil.cpu_percent(interval=None)
    alertas = []

    if ram.percent > UMBRAL_RAM_PCT:
        alertas.append(f"RAM alta: {ram.percent}% ({ram.available//1024//1024}MB libres)")
    if cpu > 90:
        alertas.append(f"CPU alta: {cpu}%")

    for part in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(part.mountpoint)
            if uso.percent > UMBRAL_DISCO_PCT:
                alertas.append(f"Disco lleno: {part.device} {uso.percent}%")
        except Exception:
            pass

    return {
        "ram_pct": round(ram.percent, 1),
        "ram_libre_mb": round(ram.available / 1024**2),
        "ram_libre_gb": round(ram.available / 1024**3, 1),
        "cpu_pct": cpu,
        "alertas": alertas
    }


# ═══════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════
@app.get("/watchdog/estado")
async def estado():
    return {
        "ok": True,
        "ultimo_check": _ultimo_check,
        "ultima_limpieza": _ultimo_limpieza.isoformat() if _ultimo_limpieza else None,
        "motores": _estado_motores,
        "alertas": _alertas_activas,
        "recursos": recursos_sistema(),
        "metricas_recientes": _metricas_historico[-6:],
    }

@app.get("/watchdog/motores")
async def estado_motores():
    resultado = {}
    for nombre, cfg in MOTORES.items():
        if nombre == "motor_watchdog":
            resultado[nombre] = {"activo": True, "status": 200, "puerto": cfg["puerto"], "critico": cfg["critico"]}
            continue
        estado = await ping_motor(nombre, cfg["puerto"])
        resultado[nombre] = {**estado, "puerto": cfg["puerto"], "critico": cfg["critico"]}
    return {"ok": True, "motores": resultado}

@app.get("/watchdog/recursos")
async def ver_recursos():
    r = recursos_sistema()
    python_procs = []
    for proc in psutil.process_iter(['pid', 'cmdline', 'memory_info']):
        try:
            cmd = ' '.join(proc.info['cmdline'] or [])
            if 'python' in cmd.lower():
                python_procs.append({
                    "pid": proc.info['pid'],
                    "ram_mb": round(proc.info['memory_info'].rss / 1024**2, 1),
                    "cmd": cmd[-80:]
                })
        except Exception:
            pass
    return {"ok": True, "recursos": r, "procesos_python": sorted(python_procs, key=lambda x: -x["ram_mb"])}

@app.post("/watchdog/limpiar-ahora")
async def limpiar_ahora():
    """Dispara limpieza profunda inmediata."""
    reporte = await limpieza_profunda()
    return {"ok": True, "reporte": reporte}

@app.post("/watchdog/liberar_memoria")
async def liberar_mem():
    await liberar_ram_emergencia()
    ram = psutil.virtual_memory()
    return {"ok": True, "ram_pct": round(ram.percent, 1), "ram_libre_mb": round(ram.available / 1024**2)}

@app.post("/watchdog/reiniciar/{nombre}")
async def reiniciar_manual(nombre: str):
    if nombre not in MOTORES:
        return {"ok": False, "error": f"Motor desconocido: {nombre}"}
    cfg = MOTORES[nombre]
    exito = await reiniciar_motor(nombre, cfg["archivo"])
    return {"ok": exito, "motor": nombre}

@app.get("/watchdog/logs")
async def leer_logs(lineas: int = 50):
    log_file = LOGS_DIR / "watchdog.log"
    if not log_file.exists():
        return {"ok": True, "logs": []}
    todas = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    return {"ok": True, "logs": todas[-lineas:], "total": len(todas)}

@app.get("/watchdog/limpiezas")
async def ver_limpiezas():
    """Lista todos los reportes de limpieza guardados."""
    reportes = []
    for f in sorted(DATA_DIR.glob("limpieza_*.json"), reverse=True)[:10]:
        try:
            reportes.append(json.loads(f.read_text(encoding='utf-8')))
        except Exception:
            pass
    return {"ok": True, "reportes": reportes}

# ═══════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════
@app.on_event("startup")
async def startup():
    asyncio.create_task(loop_ping())
    log.info("Watchdog v3.1 — ping 5min, limpieza 4×/día (06/12/18/00)")
    print("[WATCHDOG] Iniciado — ping cada 5min, limpieza profunda 4×/día", flush=True)

if __name__ == "__main__":
    import uvicorn
    print("[WATCHDOG] Puerto 8011 — huella mínima, PC optimizada", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8011, log_level="warning")

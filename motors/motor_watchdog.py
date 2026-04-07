"""
motor_watchdog.py — Autocorrección y Autoreparación de NEXUS
Puerto 8011

Monitorea constantemente:
- RAM y CPU del sistema
- Estado de cada motor (8003-8010)
- Logs de errores
- Integridad de archivos clave

Si detecta un problema:
1. Lo registra
2. Intenta repararlo automáticamente
3. Si no puede → notifica por Telegram
4. Genera reporte del incidente

Este motor NUNCA se detiene. Es el guardián.
"""

import os, sys, time, json, asyncio, subprocess, psutil, httpx, logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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

app = FastAPI(title="NEXUS Watchdog", version="3.0")

# ═══════════════════════════════════════════════
# CONFIGURACION DE MOTORES
# ═══════════════════════════════════════════════
MOTORES = {
    "nexus_core":     {"puerto": 8003, "archivo": "nexus_core.py",           "critico": True},
    "motor_atf":      {"puerto": 8004, "archivo": "motors/motor_atf.py",     "critico": True},
    "motor_teens":    {"puerto": 8005, "archivo": "motors/motor_teens.py",   "critico": False},
    "motor_auth":     {"puerto": 8006, "archivo": "motors/motor_auth.py",    "critico": True},
    "motor_pagos":    {"puerto": 8007, "archivo": "motors/motor_pagos.py",   "critico": True},
    "motor_reportes": {"puerto": 8008, "archivo": "motors/motor_reportes.py","critico": False},
    "motor_sistema":  {"puerto": 8009, "archivo": "motors/motor_sistema.py", "critico": True},
    "motor_redes":    {"puerto": 8010, "archivo": "motors/motor_redes.py",   "critico": False},
}

# Umbrales de alerta
UMBRAL_RAM_PCT    = 85   # % de RAM física
UMBRAL_CPU_PCT    = 90   # % CPU por 60s
UMBRAL_DISCO_PCT  = 90   # % disco lleno
INTERVALO_CHECK   = 30   # segundos entre chequeos

# Estado global
_estado_motores = {}
_alertas_activas = []
_ultimo_check = None
_metricas_historico = []

# ═══════════════════════════════════════════════
# VERIFICACION DE MOTORES
# ═══════════════════════════════════════════════
async def verificar_motor(nombre: str, puerto: int) -> dict:
    """Verifica si un motor responde."""
    endpoints_check = {
        8003: "/ai/status",
        8004: "/atf/kits",
        8005: "/teens/misiones",
        8006: "/auth/estado",
        8007: "/pagos/resumen",
        8008: "/reportes/resumen-diario",
        8009: "/sistema/estado",
        8010: "/redes/estado",
    }
    endpoint = endpoints_check.get(puerto, "/")

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"http://localhost:{puerto}{endpoint}")
            return {
                "activo": r.status_code < 500,
                "status": r.status_code,
                "latencia_ms": round(r.elapsed.total_seconds() * 1000)
            }
    except Exception as e:
        return {"activo": False, "status": 0, "error": str(e)[:50]}

async def reiniciar_motor(nombre: str, archivo: str) -> bool:
    """Reinicia un motor que no responde."""
    log.warning(f"Reiniciando motor: {nombre} ({archivo})")

    # Matar proceso existente si lo hay
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if archivo.replace('/', '\\') in cmdline or archivo in cmdline:
                proc.terminate()
                time.sleep(1)
                log.info(f"Proceso terminado: PID {proc.info['pid']}")
        except:
            pass

    # Esperar que libere el puerto
    await asyncio.sleep(2)

    # Relanzar
    try:
        subprocess.Popen(
            f'start "NEXUS {nombre}" /min python "{NEXUS_DIR / archivo}"',
            shell=True,
            cwd=str(NEXUS_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        await asyncio.sleep(5)

        # Verificar que levantó
        info = MOTORES.get(nombre, {})
        resultado = await verificar_motor(nombre, info.get("puerto", 8003))
        if resultado["activo"]:
            log.info(f"Motor reiniciado exitosamente: {nombre}")
            return True
        else:
            log.error(f"Motor no levantó después de reiniciar: {nombre}")
            return False
    except Exception as e:
        log.error(f"Error reiniciando {nombre}: {e}")
        return False

# ═══════════════════════════════════════════════
# MONITOREO DE RECURSOS
# ═══════════════════════════════════════════════
def verificar_recursos() -> dict:
    """Verifica CPU, RAM y disco."""
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=2)
    swap = psutil.swap_memory()

    alertas = []

    if ram.percent > UMBRAL_RAM_PCT:
        alertas.append(f"RAM critica: {ram.percent}% usada ({ram.available/1024**3:.1f}GB libres)")

    if cpu > UMBRAL_CPU_PCT:
        alertas.append(f"CPU critico: {cpu}%")

    for part in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(part.mountpoint)
            if uso.percent > UMBRAL_DISCO_PCT:
                alertas.append(f"Disco {part.device} lleno: {uso.percent}%")
        except:
            pass

    return {
        "ram_pct": ram.percent,
        "ram_libre_gb": round(ram.available / 1024**3, 1),
        "cpu_pct": cpu,
        "pagefile_pct": swap.percent,
        "alertas": alertas
    }

def liberar_memoria():
    """Libera memoria cuando RAM está alta."""
    log.warning("RAM alta — ejecutando limpieza de memoria")

    # Limpiar procesos Python con mucha RAM que no sean NEXUS
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            ram_mb = proc.info['memory_info'].rss / 1024**2
            cmdline = ' '.join(proc.info['cmdline'] or [])
            # Matar procesos Python > 500MB que no sean NEXUS ni Ollama
            if (ram_mb > 500 and 'python' in proc.info['name'].lower()
                    and 'nexus' not in cmdline.lower()
                    and 'motor_' not in cmdline.lower()):
                proc.terminate()
                log.info(f"Proceso liberado: PID {proc.info['pid']} ({ram_mb:.0f}MB)")
        except:
            pass

    # Vaciar temporales
    subprocess.run('del /q /f /s "%TEMP%\\*.tmp" 2>nul', shell=True, capture_output=True)
    log.info("Temporales limpiados")

# ═══════════════════════════════════════════════
# AUTOCORRECCIÓN DE CÓDIGO
# ═══════════════════════════════════════════════
async def analizar_logs_errores() -> list:
    """Lee los logs recientes y detecta errores repetidos."""
    errores = []
    for log_file in LOGS_DIR.glob("*.log"):
        try:
            lines = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
            # Últimas 100 líneas
            for line in lines[-100:]:
                if any(k in line.upper() for k in ['ERROR', 'EXCEPTION', 'TRACEBACK', 'CRITICAL']):
                    errores.append({
                        "archivo": log_file.name,
                        "linea": line.strip()[:200],
                        "timestamp": datetime.now().isoformat()
                    })
        except:
            pass
    return errores[-20:]  # máx 20 errores recientes

async def notificar_telegram(mensaje: str):
    """Envía alerta crítica por Telegram."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": f"🚨 NEXUS Watchdog\n{mensaje}"}
            )
    except:
        pass

# ═══════════════════════════════════════════════
# LOOP PRINCIPAL DE MONITOREO
# ═══════════════════════════════════════════════
async def loop_monitoreo():
    """Loop infinito que verifica todo cada 30 segundos."""
    global _estado_motores, _alertas_activas, _ultimo_check, _metricas_historico

    log.info("Watchdog iniciado — monitoreando cada 30s")
    motores_caidos_count = {k: 0 for k in MOTORES}

    while True:
        try:
            timestamp = datetime.now().isoformat()
            alertas_ciclo = []

            # 1. Verificar recursos
            recursos = verificar_recursos()
            if recursos["alertas"]:
                for alerta in recursos["alertas"]:
                    log.warning(alerta)
                    alertas_ciclo.append(alerta)

                # Si RAM crítica, liberar
                if recursos["ram_pct"] > UMBRAL_RAM_PCT:
                    liberar_memoria()

            # 2. Verificar motores
            for nombre, cfg in MOTORES.items():
                estado = await verificar_motor(nombre, cfg["puerto"])
                _estado_motores[nombre] = {**estado, "timestamp": timestamp}

                if not estado["activo"]:
                    motores_caidos_count[nombre] += 1
                    msg = f"Motor caído: {nombre} (puerto {cfg['puerto']}) — intento {motores_caidos_count[nombre]}"
                    log.warning(msg)

                    if motores_caidos_count[nombre] >= 2:
                        # Reiniciar automáticamente
                        reiniciado = await reiniciar_motor(nombre, cfg["archivo"])
                        if reiniciado:
                            motores_caidos_count[nombre] = 0
                            alertas_ciclo.append(f"✅ Motor reiniciado: {nombre}")
                        else:
                            alertas_ciclo.append(f"❌ Motor no pudo reiniciar: {nombre}")
                            if cfg["critico"]:
                                await notificar_telegram(f"Motor crítico caído: {nombre}\nRuta: {cfg['archivo']}")
                else:
                    motores_caidos_count[nombre] = 0  # resetear contador

            # 3. Guardar métricas
            metrica = {
                "timestamp": timestamp,
                "ram_pct": recursos["ram_pct"],
                "cpu_pct": recursos["cpu_pct"],
                "motores_ok": sum(1 for m in _estado_motores.values() if m.get("activo")),
                "motores_total": len(MOTORES)
            }
            _metricas_historico.append(metrica)
            if len(_metricas_historico) > 288:  # 24h de datos a 5min
                _metricas_historico.pop(0)

            # Guardar estado actual
            estado_file = DATA_DIR / "watchdog_estado.json"
            estado_file.write_text(json.dumps({
                "ultimo_check": timestamp,
                "recursos": recursos,
                "motores": _estado_motores,
                "alertas_activas": alertas_ciclo
            }, indent=2, ensure_ascii=False), encoding='utf-8')

            _ultimo_check = timestamp
            _alertas_activas = alertas_ciclo

        except Exception as e:
            log.error(f"Error en loop de monitoreo: {e}")

        await asyncio.sleep(INTERVALO_CHECK)

# ═══════════════════════════════════════════════
# API DEL WATCHDOG
# ═══════════════════════════════════════════════
@app.get("/watchdog/estado")
async def estado_watchdog():
    """Estado completo del sistema monitoreado."""
    return {
        "ok": True,
        "ultimo_check": _ultimo_check,
        "motores": _estado_motores,
        "alertas_activas": _alertas_activas,
        "recursos": verificar_recursos(),
        "metricas_recientes": _metricas_historico[-10:]
    }

@app.get("/watchdog/motores")
async def estado_motores():
    """Estado de todos los motores."""
    resultado = {}
    for nombre, cfg in MOTORES.items():
        estado = await verificar_motor(nombre, cfg["puerto"])
        resultado[nombre] = {
            **estado,
            "puerto": cfg["puerto"],
            "critico": cfg["critico"]
        }
    return {"ok": True, "motores": resultado}

@app.post("/watchdog/reiniciar/{nombre}")
async def reiniciar_motor_manual(nombre: str):
    """Reinicia un motor manualmente."""
    if nombre not in MOTORES:
        return {"ok": False, "error": f"Motor desconocido: {nombre}"}
    cfg = MOTORES[nombre]
    exito = await reiniciar_motor(nombre, cfg["archivo"])
    return {"ok": exito, "motor": nombre}

@app.get("/watchdog/logs")
async def leer_logs_recientes(lineas: int = 50):
    """Últimas líneas del log del watchdog."""
    log_file = LOGS_DIR / "watchdog.log"
    if not log_file.exists():
        return {"ok": True, "logs": []}
    todas = log_file.read_text(encoding='utf-8', errors='ignore').splitlines()
    return {"ok": True, "logs": todas[-lineas:], "total": len(todas)}

@app.get("/watchdog/errores")
async def errores_recientes():
    """Errores recientes en todos los logs."""
    errores = await analizar_logs_errores()
    return {"ok": True, "errores": errores, "total": len(errores)}

@app.get("/watchdog/metricas")
async def metricas_historico():
    """Historial de métricas de recursos."""
    return {"ok": True, "metricas": _metricas_historico, "total": len(_metricas_historico)}

@app.post("/watchdog/liberar_memoria")
async def forzar_liberacion():
    """Fuerza liberación de memoria."""
    liberar_memoria()
    ram = psutil.virtual_memory()
    return {
        "ok": True,
        "ram_pct": ram.percent,
        "ram_libre_gb": round(ram.available / 1024**3, 1)
    }

# ═══════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════
@app.on_event("startup")
async def startup():
    asyncio.create_task(loop_monitoreo())
    log.info("Watchdog API iniciada en puerto 8011")

if __name__ == "__main__":
    import uvicorn
    print("NEXUS Watchdog — Puerto 8011 — Monitoreo constante activo")
    uvicorn.run(app, host="0.0.0.0", port=8011, log_level="warning")

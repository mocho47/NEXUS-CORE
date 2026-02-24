"""
nexus_scheduler.py — Tareas automáticas programadas de Nexus.

Trabajos programados:
  - 08:00 diario: resumen del día vía Telegram + notificación desktop
  - Cada 5 min:   verifica deadlines vencidos y avisa por desktop/Telegram
  - Cada 30 min:  housekeeping ligero (limpia archivos temporales)

Uso:
    Importar en nexus_core.py: import nexus_scheduler; nexus_scheduler.start()
    O correr standalone: python nexus_scheduler.py

Requiere: pip install apscheduler   (ya debería estar disponible)
Fallback: usa threading.Timer si APScheduler no está instalado.
"""
import os
import time
import threading
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger("NexusScheduler")

_started = False
_scheduler = None


# ─── Trabajos ──────────────────────────────────────────────────────────────

def job_resumen_diario():
    """08:00 — Envía resumen del día."""
    try:
        import nexus_orders
        import nexus_stock
        import nexus_notifier
        import datetime

        nexus_orders.manager.load_orders()
        nexus_stock.manager.load_stock()
        pend = nexus_orders.manager.get_pending()
        bajo = nexus_stock.manager.list_bajo_stock(minimo=3)
        listos = [o for o in nexus_orders.manager.orders if o.get("status") == "LISTO"]

        nexus_notifier.notifier.resumen_diario(
            pendientes=len(pend),
            listos=len(listos),
            bajo_stock=len(bajo),
        )
        log.info(f"[Scheduler] Resumen diario enviado: pend={len(pend)} listos={len(listos)}")
    except Exception as e:
        log.error(f"[Scheduler] resumen_diario error: {e}")


def job_check_deadlines():
    """Cada 5 min — verifica pedidos vencidos o próximos a vencer."""
    try:
        import nexus_orders
        import nexus_notifier
        alerts = nexus_orders.manager.check_deadlines()
        for alert in alerts:
            nexus_notifier.notifier._log(f"[ALERTA] {alert}")
            try:
                nexus_notifier.notifier._desktop_notify("⚠️ Nexus Alerta", alert[:60])
            except Exception:
                pass
            try:
                from nexus_telegram import bot
                bot.send(f"⚠️ {alert}")
            except Exception:
                pass
    except Exception as e:
        log.debug(f"[Scheduler] check_deadlines error: {e}")


def job_backup_diario():
    """02:00 — backup diario de CONFIG/ y templates."""
    try:
        from nexus_backup import daily_backup
        path = daily_backup()
        log.info(f"[Scheduler] Backup OK: {path}")
    except Exception as e:
        log.error(f"[Scheduler] backup error: {e}")


def job_housekeeping():
    """Cada 30 min — limpieza ligera de archivos temporales."""
    try:
        import glob as _glob
        import datetime as _dt
        log_dir = os.path.join(BASE_DIR, "logs")
        # Elimina voice_*.mp3 de más de 24h
        for f in _glob.glob(os.path.join(BASE_DIR, "voice_*.mp3")):
            try:
                age = time.time() - os.path.getmtime(f)
                if age > 86400:
                    os.remove(f)
                    log.debug(f"[Housekeeping] eliminado {f}")
            except Exception:
                pass
    except Exception as e:
        log.debug(f"[Scheduler] housekeeping error: {e}")


# ─── Motor de scheduling ────────────────────────────────────────────────────

def _try_apscheduler():
    """Intenta usar APScheduler si está instalado."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler(timezone="America/Mexico_City")
        scheduler.add_job(job_resumen_diario, CronTrigger(hour=8, minute=0), id="resumen_diario")
        scheduler.add_job(job_backup_diario, CronTrigger(hour=2, minute=0), id="backup_diario")
        scheduler.add_job(job_check_deadlines, IntervalTrigger(minutes=5), id="check_deadlines")
        scheduler.add_job(job_housekeeping, IntervalTrigger(minutes=30), id="housekeeping")
        scheduler.start()
        log.info("[Scheduler] APScheduler iniciado.")
        return scheduler
    except ImportError:
        return None


def _fallback_threading():
    """Scheduler simple con threading si APScheduler no está disponible."""
    import datetime as _dt

    last_resumen_day = [None]

    def loop():
        while True:
            try:
                now = _dt.datetime.now()
                # Resumen a las 8:00
                if now.hour == 8 and now.minute < 5:
                    if last_resumen_day[0] != now.date():
                        last_resumen_day[0] = now.date()
                        job_resumen_diario()
                # Deadlines cada 5 min
                if now.minute % 5 == 0:
                    job_check_deadlines()
                # Housekeeping cada 30 min
                if now.minute % 30 == 0:
                    job_housekeeping()
            except Exception as e:
                log.error(f"[Scheduler] loop error: {e}")
            time.sleep(60)

    t = threading.Thread(target=loop, daemon=True, name="NexusScheduler")
    t.start()
    log.info("[Scheduler] Modo threading iniciado (sin APScheduler).")
    return t


def start():
    """Inicia el scheduler. Seguro llamar múltiples veces (idempotente)."""
    global _started, _scheduler
    if _started:
        return
    _started = True
    _scheduler = _try_apscheduler() or _fallback_threading()


def stop():
    global _started, _scheduler
    _started = False
    try:
        if hasattr(_scheduler, "shutdown"):
            _scheduler.shutdown(wait=False)
    except Exception:
        pass


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print("[Scheduler] Iniciando en modo standalone...")
    start()
    print("[Scheduler] Corriendo. Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
        print("[Scheduler] Detenido.")

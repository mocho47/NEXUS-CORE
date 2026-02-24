"""
nexus_autopilot.py — Módulo de sueño y automatización autónoma de NEXUS.

CONCEPTO:
  NEXUS trabaja mientras el usuario duerme. Este módulo ejecuta tareas
  programadas en segundo plano usando un thread daemon + scheduler simple
  basado en time.sleep() (sin dependencias externas extras).

TAREAS AUTOMÁTICAS:
  09:00 diario  → Resumen del día (pedidos + stock bajo + cumpleaños)
  10:00 diario  → Post sugerido para Instagram (copia a TALLER/MARKETING_STUDIO)
  18:00 diario  → Alerta de pedidos sin entregar que vencen hoy
  00:30 diario  → Backup automático de base de datos
  Cada 5 min    → Ping de keepalive a Supabase
  Cada lunes    → Lista de clientes inactivos (30+ días) para reactivación
  Cada arranque → Verifica licencia y muestra días restantes

ESTADO:
  El estado del autopilot se persiste en CONFIG/autopilot.json
  Cada tarea que se ejecuta se registra en logs/nexus_log_YYYY-MM.txt
"""

import os
import json
import time
import threading
import datetime
import traceback

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(BASE_DIR, "CONFIG")
TALLER_DIR  = os.path.join(BASE_DIR, "TALLER")
STUDIO_DIR  = os.path.join(TALLER_DIR, "MARKETING_STUDIO")
AUTOPILOT_CONFIG = os.path.join(CONFIG_DIR, "autopilot.json")

os.makedirs(STUDIO_DIR, exist_ok=True)


# ── Logger interno ────────────────────────────────────────────────────────────

def _log(msg: str, nivel: str = "INFO"):
    ahora    = datetime.datetime.now()
    mes      = ahora.strftime("%Y-%m")
    log_path = os.path.join(BASE_DIR, "logs", f"nexus_log_{mes}.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    linea    = f"[AUTOPILOT][{nivel}][{ahora.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass
    print(linea.strip())


# ── Configuración ─────────────────────────────────────────────────────────────

def _cargar_config() -> dict:
    default = {
        "activo":              True,
        "instagram":           False,
        "whatsapp":            False,
        "recordatorio":        True,
        "clientes_inactivos":  False,
        "backup_automatico":   True,
        "keepalive_supabase":  True,
        "resumen_diario":      True,
    }
    try:
        with open(AUTOPILOT_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        default.update(cfg)
    except Exception:
        pass
    return default

def _guardar_config(cfg: dict):
    with open(AUTOPILOT_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── Tareas individuales ───────────────────────────────────────────────────────

def tarea_backup() -> dict:
    """Backup automático de la base de datos local."""
    try:
        from nexus_backup import daily_backup
        path = daily_backup()
        _log(f"Backup completado: {path}")
        return {"ok": True, "path": path}
    except Exception as e:
        _log(f"Error en backup: {e}", "ERROR")
        return {"ok": False, "error": str(e)}


def tarea_keepalive() -> dict:
    """Ping a Supabase para mantener la conexión activa."""
    try:
        from nexus_db import db
        resultado = db.ping()
        _log(f"Keepalive Supabase: {resultado}")
        # Actualizar timestamp en CONFIG
        ks_path = os.path.join(CONFIG_DIR, "supabase_keepalive_last.json")
        with open(ks_path, "w", encoding="utf-8") as f:
            json.dump({"ultimo": datetime.datetime.now().isoformat(), "ok": True}, f)
        return {"ok": True}
    except Exception as e:
        _log(f"Error en keepalive: {e}", "WARN")
        return {"ok": False, "error": str(e)}


def tarea_resumen_diario() -> str:
    """Genera resumen textual del día para el operador."""
    try:
        from nexus_finanzas import resumen_texto
        resumen = resumen_texto()
        _log("Resumen diario generado")
        # Guardar en un archivo para que el panel lo muestre
        ruta = os.path.join(CONFIG_DIR, "resumen_diario.txt")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(resumen)
        return resumen
    except Exception as e:
        _log(f"Error en resumen: {e}", "ERROR")
        return f"Error al generar resumen: {e}"


def tarea_alerta_pedidos() -> list:
    """Revisa pedidos que vencen hoy o están vencidos."""
    try:
        from nexus_orders import manager as om
        om.load_orders()
        hoy   = datetime.date.today()
        mañana = hoy + datetime.timedelta(days=1)

        criticos = []
        for o in om.orders:
            if o.get("status") != "PENDIENTE":
                continue
            deadline_str = (o.get("deadline") or "")[:10]
            try:
                deadline = datetime.date.fromisoformat(deadline_str)
            except Exception:
                continue

            if deadline <= mañana:
                criticos.append({
                    "cliente":  o.get("cliente", "?"),
                    "producto": o.get("producto", "?"),
                    "deadline": deadline_str,
                    "vencido":  deadline < hoy,
                })

        if criticos:
            _log(f"ALERTA: {len(criticos)} pedido(s) críticos hoy")
        return criticos
    except Exception as e:
        _log(f"Error en alerta pedidos: {e}", "ERROR")
        return []


def tarea_clientes_inactivos() -> list:
    """Lista clientes que no han pedido en 30+ días."""
    try:
        from nexus_finanzas import obtener_dashboard
        d        = obtener_dashboard()
        dormidos = d.get("clientes", {}).get("dormidos", [])
        if dormidos:
            _log(f"Clientes inactivos encontrados: {len(dormidos)}")
            # Guardar para acceso fácil
            ruta = os.path.join(CONFIG_DIR, "clientes_inactivos.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(dormidos, f, ensure_ascii=False, indent=2)
        return dormidos
    except Exception as e:
        _log(f"Error en clientes inactivos: {e}", "ERROR")
        return []


def tarea_sugerencia_post() -> dict:
    """Genera una sugerencia de post de marketing para el día."""
    try:
        from nexus_subliminal import pista_aleatoria
        from nexus_finanzas  import obtener_dashboard

        d         = obtener_dashboard()
        servicios = list((d.get("servicios") or {}).keys())
        servicio  = servicios[0] if servicios else "general"
        pistas    = pista_aleatoria()

        # Construir sugerencia
        fecha    = datetime.date.today().strftime("%d/%m/%Y")
        cat      = list(pistas.keys())[0] if pistas else "deseo"
        mensaje  = list(pistas.values())[0] if pistas else ""

        sugerencia = {
            "fecha":    fecha,
            "servicio": servicio.upper(),
            "mensaje_base": mensaje,
            "categoria_psicologica": cat,
            "texto_post": (
                f"Buen día! Hoy es un gran día para llevar tu proyecto de {servicio.lower()} "
                f"al siguiente nivel. {mensaje} Contáctanos y transforma tu visión en realidad."
            ),
            "hashtags": f"#{servicio.lower()} #personalizado #calidad #diseño #mipymes"
        }

        # Guardar en studio
        ts   = datetime.datetime.now().strftime("%Y%m%d")
        ruta = os.path.join(STUDIO_DIR, f"sugerencia_post_{ts}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(sugerencia, f, ensure_ascii=False, indent=2)

        _log(f"Sugerencia de post generada para servicio {servicio}")
        return sugerencia
    except Exception as e:
        _log(f"Error en sugerencia post: {e}", "ERROR")
        return {}


def ejecutar_verificacion_licencia() -> dict:
    """Verifica la licencia al arrancar."""
    try:
        from nexus_license import validar_licencia
        v = validar_licencia()
        if v["valida"]:
            dias = v["dias_restantes"]
            _log(f"Licencia {v['tipo']} válida — {dias} días restantes")
            if dias <= 7:
                _log(f"AVISO: Licencia vence en {dias} días", "WARN")
        else:
            _log(f"Licencia inválida: {v['razon']}", "WARN")
        return v
    except Exception:
        _log("Sin módulo de licencia — modo sin restricciones", "INFO")
        return {"valida": True, "tipo": "ADMIN", "dias_restantes": 9999}


# ── Scheduler ─────────────────────────────────────────────────────────────────

class AutopilotScheduler:
    """
    Scheduler liviano basado en threads.
    Verifica cada minuto si alguna tarea debe ejecutarse.
    """

    def __init__(self):
        self._running   = False
        self._thread    = None
        self._last_exec = {}

    def iniciar(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="nexus-autopilot")
        self._thread.start()
        _log("Autopilot iniciado")

    def detener(self):
        self._running = False
        _log("Autopilot detenido")

    def _loop(self):
        # Ejecutar verificación de licencia al arrancar
        ejecutar_verificacion_licencia()

        while self._running:
            try:
                cfg  = _cargar_config()
                ahora = datetime.datetime.now()
                hora  = (ahora.hour, ahora.minute)
                dia_semana = ahora.weekday()  # 0=lunes

                # Keepalive cada 5 minutos
                if cfg.get("keepalive_supabase") and ahora.minute % 5 == 0:
                    self._ejecutar_si_nuevo("keepalive", tarea_keepalive)

                # Resumen diario a las 09:00
                if cfg.get("resumen_diario") and hora == (9, 0):
                    self._ejecutar_si_nuevo("resumen", tarea_resumen_diario)

                # Sugerencia de post a las 10:00
                if cfg.get("instagram") and hora == (10, 0):
                    self._ejecutar_si_nuevo("post", tarea_sugerencia_post)

                # Alerta de pedidos a las 18:00
                if cfg.get("recordatorio") and hora == (18, 0):
                    self._ejecutar_si_nuevo("alertas", tarea_alerta_pedidos)

                # Backup a las 00:30
                if cfg.get("backup_automatico") and hora == (0, 30):
                    self._ejecutar_si_nuevo("backup", tarea_backup)

                # Clientes inactivos los lunes a las 09:05
                if cfg.get("clientes_inactivos") and dia_semana == 0 and hora == (9, 5):
                    self._ejecutar_si_nuevo("inactivos", tarea_clientes_inactivos)

            except Exception as e:
                _log(f"Error en loop autopilot: {e}", "ERROR")

            time.sleep(60)  # Revisar cada minuto

    def _ejecutar_si_nuevo(self, nombre: str, fn):
        """Ejecuta la tarea solo si no se ejecutó en la última hora."""
        ahora = datetime.datetime.now()
        ultimo = self._last_exec.get(nombre)
        if ultimo and (ahora - ultimo).total_seconds() < 3600:
            return  # Ya se ejecutó en la última hora
        try:
            fn()
            self._last_exec[nombre] = ahora
        except Exception as e:
            _log(f"Error ejecutando {nombre}: {e}", "ERROR")

    def estado(self) -> dict:
        return {
            "activo":     self._running,
            "config":     _cargar_config(),
            "ultimo_exec": {k: v.isoformat() for k, v in self._last_exec.items()},
        }


# Instancia global
autopilot = AutopilotScheduler()


if __name__ == "__main__":
    print("Iniciando autopilot manual...")
    autopilot.iniciar()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        autopilot.detener()
        print("Autopilot detenido.")

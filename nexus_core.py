import os

# Modo seguro (para pruebas/diagnóstico): evita auto-arranque de servicios/hilos al importar.
NEXUS_NO_AUTOSTART = os.environ.get("NEXUS_NO_AUTOSTART", "0").strip().lower() in ("1", "true", "yes")
from dotenv import load_dotenv
load_dotenv() # Cargar llaves de acceso desde .env

import sys
import json
import gc
import time
import subprocess
import threading
import random
import webbrowser
import clipboard
import requests
import pyttsx3
# IOT MOVIDO A SUBPROCESO EXTERNO PARA ESTABILIDAD
IOT_ACTIVE = True 

import psutil
import keyboard
import re
from vosk import Model, KaldiRecognizer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from duckduckgo_search import DDGS
import wikipedia
from AppOpener import open as open_app, close as close_app
import nexus_voice # Importación crítica
try:
    import nexus_ecosystem
except Exception as _e_ecosystem:
    nexus_ecosystem = None
    print(f"[ECO] No pude importar nexus_ecosystem: {_e_ecosystem}")
import nexus_logs # Importación de bitácora
import nexus_orders # Gestor de Pedidos
import nexus_spy # Monitor de Productividad
import nexus_panel # Panel Gráfico
import nexus_cast # Módulo Google Cast
import nexus_db # CONECTOR A LA NUBE (NUEVO CEREBRO)
import nexus_video_maker # EDITOR DE VIDEO AUTOMÁTICO

import winsound # Para efectos de sonido simples

import nexus_marketing # Módulo de Marketing
import nexus_catalog # Generador de Catálogos
import nexus_vault # Bóveda de Contraseñas
import nexus_coder # Generador de Código (IDE)
try:
    import nexus_memory
except Exception as _e_mem:
    nexus_memory = None
    print(f"[MEM] No pude importar nexus_memory: {_e_mem}")
try:
    import nexus_social_operator
except Exception as _e_socialop:
    nexus_social_operator = None
    print(f"[SOCIAL] No pude importar nexus_social_operator: {_e_socialop}")

try:
    import nexus_watchtower
except Exception as _e_watch:
    nexus_watchtower = None
    print(f"[WATCH] No pude importar nexus_watchtower: {_e_watch}")

try:
    import nexus_self_heal
except Exception as _e_selfheal:
    nexus_self_heal = None
    print(f"[SELFHEAL] No pude importar nexus_self_heal: {_e_selfheal}")

try:
    import nexus_housekeeping
except Exception as _e_house:
    nexus_housekeeping = None
    print(f"[HOUSE] No pude importar nexus_housekeeping: {_e_house}")

try:
    import nexus_supabase_keepalive
except Exception as _e_keep:
    nexus_supabase_keepalive = None
    print(f"[KEEPALIVE] No pude importar nexus_supabase_keepalive: {_e_keep}")

try:
    import nexus_doctor
except Exception as _e_doctor:
    nexus_doctor = None
    print(f"[DOCTOR] No pude importar nexus_doctor: {_e_doctor}")

# --- GENERADOR DE CAJAS (INTEGRACIÓN BOXES.PY) ---
def start_timer(minutes):
    seconds = minutes * 60
    time.sleep(seconds)
    speak(f"Tiempo concluido. Han pasado {minutes} minutos.")
    # Alarma simple
    for _ in range(3):
        try: winsound.Beep(1000, 500)
        except: pass
        time.sleep(0.5)

def generate_box(x, y, h, thickness=3.0):
    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"caja_{x}x{y}x{h}_{ts}.svg"
        output_path = os.path.join(WATCH_DIR, filename)
        
        # Asegurar que el directorio existe
        os.makedirs(WATCH_DIR, exist_ok=True)
        
        # Ruta al script de boxes
        boxes_script = os.path.join(BASE_DIR, "TOOLS", "boxes", "boxes", "scripts", "boxes_main.py")
        python_path = os.path.join(BASE_DIR, "TOOLS", "boxes")
        
        # Comando
        cmd = [
            sys.executable, 
            boxes_script, 
            "ClosedBox", 
            f"--x={x}", 
            f"--y={y}", 
            f"--h={h}", 
            f"--thickness={thickness}", 
            f"--output={output_path}"
        ]
        
        # Entorno con PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = python_path + os.pathsep + env.get("PYTHONPATH", "")
        
        print(f"[BOXES] Generando caja: {cmd}")
        subprocess.run(cmd, env=env, check=True, capture_output=True)
        
        if os.path.exists(output_path):
            speak(f"Caja generada. Archivo guardado en la carpeta de entrada.")
            # Abrir carpeta para confirmar
            os.startfile(WATCH_DIR)
            return True
        else:
            speak("Hubo un error generando el archivo.")
            return False
            
    except Exception as e:
        print(f"[BOXES ERROR] {e}")
        speak("Error al generar la caja.")
        return False

# --- CONFIGURACIÓN Y CARGA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
MODEL_PATH = os.path.join(BASE_DIR, "CEREBRO", "model")
WATCH_DIR = os.path.join(BASE_DIR, "TALLER", "ENTRADA")

# --- AUTOLIMPIEZA / OPTIMIZACIÓN CONTINUA (solo basura generada por NEXUS) ---
housekeeping = None
if nexus_housekeeping is not None:
    try:
        housekeeping = nexus_housekeeping.Housekeeping(BASE_DIR, CONFIG_DIR)
        if not NEXUS_NO_AUTOSTART:
            # Borrado permitido según config interna (report_only controla). No toca nada fuera de targets.
            housekeeping.start(allow_delete_cb=lambda: True)
            print("[HOUSE] Autolimpieza activa")
        else:
            print("[HOUSE] Autolimpieza lista (autostart deshabilitado)")
    except Exception as _e_house_start:
        housekeeping = None
        print(f"[HOUSE] Error iniciando autolimpieza: {_e_house_start}")

# --- ECOSISTEMA LOCAL (ÍNDICE + ALIAS) ---
ecosystem = None
if nexus_ecosystem is not None:
    try:
        ecosystem = nexus_ecosystem.EcosystemIndex(BASE_DIR, CONFIG_DIR)
        if not NEXUS_NO_AUTOSTART:
            ecosystem.start_background_refresh(max_age_hours=24.0)
        built_at, f_cnt, d_cnt, a_cnt = ecosystem.status()
        if built_at:
            print(f"[ECO] Index listo: {f_cnt} claves archivos, {d_cnt} claves carpetas, {a_cnt} alias")
        else:
            print("[ECO] Index no encontrado. Se está construyendo en segundo plano...")
    except Exception as _e_eco:
        ecosystem = None
        print(f"[ECO] Error iniciando índice: {_e_eco}")

def _eco_open_path(path: str) -> bool:
    try:
        if not path or not os.path.exists(path):
            return False
        # Si es carpeta, abrir directo. Si es archivo, abrir con app por defecto.
        os.startfile(path)
        return True
    except Exception:
        return False

def _eco_reveal_in_explorer(path: str) -> bool:
    try:
        if not path or not os.path.exists(path):
            return False
        # /select,<path> revela archivo/carpeta en Explorer
        subprocess.Popen(["explorer", f"/select,{path}"])
        return True
    except Exception:
        return False

def _eco_handle_locate_or_open(text: str) -> bool:
    """Comandos offline para ubicar/abrir cosas en tu ecosistema NEXUS.
    Retorna True si manejó la intención.
    """
    if ecosystem is None:
        return False

    t = (text or "").strip().lower()
    if not t:
        return False

    # Reindex
    if any(k in t for k in ["reindexa", "reindexar", "actualiza índice", "actualiza indice", "escanea", "escanea carpetas", "actualiza ecosistema"]):
        ecosystem.refresh_async(force=True)
        speak("Listo. Estoy actualizando mi mapa local en segundo plano.")
        return True

    # Aprendizaje: alias -> ruta (solo local)
    # Ejemplos: "memoriza pedidos es C:\\NEXUS\\PEDIDOS" / "aprende que taller es TALLER"
    if ("memoriza" in t or "aprende" in t) and " es " in t:
        try:
            # cortar prefijo
            tmp = t
            tmp = tmp.replace("aprende que", "").replace("aprende", "").replace("memoriza que", "").replace("memoriza", "").strip()
            left, right = tmp.split(" es ", 1)
            alias = left.strip().strip('"')
            target = right.strip().strip('"')

            # Si target no parece ruta, intentar encontrar carpeta/archivo por nombre
            ok = False
            if os.path.exists(target) or (len(target) > 2 and (":\\" in target or ":/" in target)):
                ok = ecosystem.set_alias(alias, target)
            else:
                hits = ecosystem.search(target, kind="any", max_results=1)
                if hits:
                    ok = ecosystem.set_alias(alias, hits[0].path)

            if ok:
                speak("Listo. Ya lo aprendí.")
            else:
                speak("No pude aprenderlo. Pásame una ruta válida o un nombre que exista.")
            return True
        except Exception:
            speak("No entendí el formato. Di: memoriza ALIAS es RUTA")
            return True

    # Ubicar
    if t.startswith("donde esta") or t.startswith("dónde está") or t.startswith("donde está") or t.startswith("ubica") or t.startswith("ubicame") or t.startswith("localiza"):
        q = re.sub(r"^(donde\s+esta|dónde\s+está|donde\s+está|ubica|ubicame|localiza)\s+", "", t).strip()
        if not q:
            speak("Dime qué archivo o carpeta ubico.")
            return True
        hits = ecosystem.search(q, kind="any", max_results=3)
        if not hits:
            speak("No lo encontré en mi raíz NEXUS. Si quieres, reindexo.")
            return True
        best = hits[0]
        print("\n[ECO] Resultados:")
        for i, h in enumerate(hits, start=1):
            print(f"{i}. ({h.kind}) {h.path}")
        # Para que sea manos libres: revelar en Explorer
        if _eco_reveal_in_explorer(best.path):
            speak("Listo. Te lo mostré en el explorador.")
        else:
            speak("Lo encontré, pero no pude abrir el explorador.")
        return True

    # Abrir carpeta/archivo
    if "abre carpeta" in t or t.startswith("abre carpeta"):
        q = t.replace("abre carpeta", "", 1).strip()
        if not q:
            speak("Dime qué carpeta abro.")
            return True
        # Alias primero
        alias_path = ecosystem.resolve_alias(q)
        if alias_path and os.path.isdir(alias_path):
            _eco_open_path(alias_path)
            speak("Hecho.")
            return True
        hits = ecosystem.search(q, kind="folder", max_results=1)
        if hits:
            _eco_open_path(hits[0].path)
            speak("Hecho.")
        else:
            speak("No encontré esa carpeta.")
        return True

    if "abre archivo" in t or t.startswith("abre archivo"):
        q = t.replace("abre archivo", "", 1).strip()
        if not q:
            speak("Dime qué archivo abro.")
            return True
        alias_path = ecosystem.resolve_alias(q)
        if alias_path and os.path.isfile(alias_path):
            _eco_open_path(alias_path)
            speak("Hecho.")
            return True
        hits = ecosystem.search(q, kind="file", max_results=1)
        if hits:
            _eco_open_path(hits[0].path)
            speak("Hecho.")
        else:
            speak("No encontré ese archivo.")
        return True

    # Abrir alias directo: "abre PEDIDOS" (si existe alias)
    if t.startswith("abre ") and len(t.split()) <= 3:
        q = t.replace("abre", "", 1).strip()
        alias_path = ecosystem.resolve_alias(q)
        if alias_path:
            _eco_open_path(alias_path)
            speak("Hecho.")
            return True

    return False

# --- RUTAS EXACTAS (PARA EVITAR ERRORES DE APPOPENER) ---
EXACT_PATHS = {
    "coreldraw": r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelDRW.exe",
    "corel": r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelDRW.exe",
    "photopaint": r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelPP.exe",
    "capture": r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\Capture.exe",
    # Aspire: Ruta asumiendo estándar, si falla usará AppOpener
    "aspire": r"C:\Program Files\Aspire 9.5\x64\Aspire.exe" 
}

TRIGGER_PHRASE = "nexus"
# Alias expandidos basados en el ruido reportado por el usuario ("Nescoilo", "Nescontigo")
TRIGGER_ALIASES = [
    "nexus", "next", "nexo", "lexus", "flexos", "textos", "sexos", "mexos", 
    "nescoilo", "nesco", "necesito", "conexo", "exos", "anexos", "dame", "mexus"
] 
COMMANDS_FILE = os.path.join(CONFIG_DIR, "commands.json")

# Variable global para controlar el micrófono
is_speaking = False

# --- MODO CONVERSACIÓN (MEMORIA CORTA) ---
CHAT_MEMORY_FILE = os.path.join(CONFIG_DIR, "conversation_memory.json")
chat_history = []  # lista de mensajes tipo {role, content, ts}
chat_mode_until_ts = 0.0
pending_sources = []  # opcional: resultados de búsqueda pendientes de aprobación
pending_login = None  # {app:str, code:str, expires:float}
pending_action = None  # {kind:str, code:str, expires:float, data:dict}

# Ventana de autorización para acciones sensibles (envíos/abrir redes/instalar deps)
actions_auto_until_ts = 0.0

def actions_auto_enabled() -> bool:
    try:
        return time.time() < float(actions_auto_until_ts or 0.0)
    except Exception:
        return False

def set_actions_auto_window(minutes: int = 10) -> None:
    global actions_auto_until_ts
    mins = max(0, int(minutes))
    actions_auto_until_ts = time.time() + mins * 60.0

def clear_actions_auto_window() -> None:
    global actions_auto_until_ts
    actions_auto_until_ts = 0.0

social_op = None
if nexus_social_operator is not None:
    try:
        social_op = nexus_social_operator.SocialOperator()
        print("[SOCIAL] Operador social listo")
    except Exception as _e_so:
        social_op = None
        print(f"[SOCIAL] Error iniciando operador social: {_e_so}")

watchtower = None
watchtower_enabled = True
watchtower_speak = True
if nexus_watchtower is not None:
    try:
        watchtower = nexus_watchtower.Watchtower()

        def _on_watch_event(evt: dict):
            # Notificación corta (no filtra secretos): solo indica que hay algo nuevo.
            try:
                if watchtower_speak:
                    src = (evt.get("source") or "mensaje").strip()
                    sender = (evt.get("from") or "").strip()
                    if sender:
                        speak(f"Nuevo {src} de {sender}.")
                    else:
                        speak(f"Nuevo {src}.")
            except Exception:
                pass

        if not NEXUS_NO_AUTOSTART:
            watchtower.start(on_event=_on_watch_event, poll_sec=1.0)
            print("[WATCH] Watchtower activo (DROP_IN/INBOX)")
        else:
            print("[WATCH] Watchtower listo (autostart deshabilitado)")
    except Exception as _e_w:
        watchtower = None
        print(f"[WATCH] Error iniciando Watchtower: {_e_w}")

def _watchtower_handle(text: str) -> bool:
    global watchtower_enabled, watchtower_speak
    if watchtower is None:
        return False
    t = (text or "").strip().lower()
    if not t:
        return False

    if "modo vigilancia" in t or "modo centinela" in t:
        watchtower_enabled = True
        watchtower_speak = True
        speak("Listo. Estoy vigilando tu bandeja local.")
        return True

    if "silencia vigilancia" in t or "silenciar vigilancia" in t:
        watchtower_speak = False
        speak("Ok. Sin avisos por voz; igual sigo registrando.")
        return True

    if "cuantos mensajes" in t or "cuántos mensajes" in t or "mensajes nuevos" in t:
        n = watchtower.unread_count()
        speak(f"Tienes {n} mensajes nuevos.")
        return True

    if t.startswith("lee mensajes") or t.startswith("leer mensajes"):
        nums = [int(n) for n in re.findall(r"\d+", t)]
        limit = nums[0] if nums else 3
        items = watchtower.pop_unread(limit=limit)
        if not items:
            speak("No hay mensajes nuevos.")
            return True
        for evt in items:
            src = (evt.get("source") or "mensaje").strip()
            sender = (evt.get("from") or "").strip()
            body = (evt.get("text") or "").strip()
            # lectura compacta
            if sender:
                speak(f"{src}. De {sender}. {body}")
            else:
                speak(f"{src}. {body}")
        return True

    if t.startswith("resumen mensajes") or t.startswith("resume mensajes"):
        nums = [int(n) for n in re.findall(r"\d+", t)]
        limit = nums[0] if nums else 5
        items = watchtower.peek_unread(limit=limit)
        if not items:
            speak("No hay mensajes nuevos.")
            return True
        # resumen offline simple
        by_src = {}
        for evt in items:
            src = (evt.get("source") or "mensaje").strip() or "mensaje"
            by_src[src] = by_src.get(src, 0) + 1
        parts = [f"{k} {v}" for k, v in by_src.items()]
        speak("Resumen: " + ", ".join(parts) + ".")
        return True

    if "borra mensajes" in t or "limpia mensajes" in t:
        watchtower.clear_unread()
        speak("Listo.")
        return True

    return False

# --- SUPABASE KEEPALIVE (ANTI-PAUSA POR INACTIVIDAD) ---
keepalive = None
if nexus_supabase_keepalive is not None:
    try:
        # ping_fn con timeout: no se cuelga por red
        keepalive = nexus_supabase_keepalive.SupabaseKeepAlive(
            BASE_DIR,
            CONFIG_DIR,
            ping_fn=lambda timeout_sec: nexus_db.db.keepalive_ping_http(timeout_sec=timeout_sec),
        )

        def _keepalive_allowed() -> bool:
            # Respeta privacidad y autorización.
            if NEXUS_NO_AUTOSTART:
                return False
            if not is_cloud_allowed():
                return False
            # Si no hay cliente o key, el ping igual reporta missing, pero no spammear.
            return True

        if not NEXUS_NO_AUTOSTART:
            keepalive.start(allow_cb=_keepalive_allowed)
            print("[KEEPALIVE] Supabase keepalive activo")
        else:
            print("[KEEPALIVE] Supabase keepalive listo (autostart deshabilitado)")
    except Exception as _e_keep_start:
        keepalive = None
        print(f"[KEEPALIVE] Error iniciando keepalive: {_e_keep_start}")

def _keepalive_handle(text: str) -> bool:
    if keepalive is None:
        return False
    t = (text or "").strip().lower()
    if not t:
        return False

    if "supabase vivo estado" in t or "estado supabase vivo" in t or "keepalive estado" in t:
        try:
            cfg = keepalive.get_config()
            speak(
                f"Supabase vivo {'activo' if cfg.enabled else 'apagado'}. "
                f"Intervalo {int(cfg.interval_sec//3600)} horas. "
                f"Último OK hace {int((time.time() - (cfg.last_ok_ts or 0))//60) if cfg.last_ok_ts else -1} minutos."
            )
        except Exception:
            speak("No pude leer estado de Supabase vivo.")
        return True

    if "supabase vivo desactivar" in t or "desactiva supabase vivo" in t or "apaga supabase vivo" in t:
        try:
            keepalive.set_enabled(False)
            speak("Listo. Supabase vivo desactivado.")
        except Exception:
            speak("No pude desactivar Supabase vivo.")
        return True

    if "supabase vivo activar" in t or "activa supabase vivo" in t:
        try:
            keepalive.set_enabled(True)
            speak("Listo. Supabase vivo activado.")
        except Exception:
            speak("No pude activar Supabase vivo.")
        return True

    if "supabase vivo ahora" in t or "ping supabase" in t or "mantener supabase vivo" in t:
        if not is_cloud_allowed():
            speak("Nube bloqueada. Di: autoriza nube.")
            return True
        rep = keepalive.run_once()
        if rep.get("ok"):
            speak("Ok. Ya hice actividad mínima en Supabase.")
        else:
            speak("No pude hacer keepalive. Revisa red o SUPABASE_KEY.")
        print("[KEEPALIVE]", rep)
        return True

    return False

def _help_handle(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    if t in ("ayuda", "help", "comandos", "lista comandos", "lista de comandos") or ("comandos" in t and "lista" in t) or ("ayuda" in t):
        try:
            help_path = os.path.join(BASE_DIR, "NEXUS_COMMANDS.md")
            if os.path.exists(help_path):
                speak("Ok. Te muestro la lista de comandos en consola.")
                print("\n[AYUDA] Lista actual: NEXUS_COMMANDS.md\n")
                try:
                    with open(help_path, "r", encoding="utf-8") as f:
                        print(f.read())
                except Exception:
                    print("[AYUDA] No pude leer NEXUS_COMMANDS.md")
            else:
                speak("Ok. No encontré el archivo de comandos. Puedo correr diagnóstico.")
                print("[AYUDA] No existe NEXUS_COMMANDS.md")
        except Exception:
            speak("No pude abrir la ayuda.")
        return True

    return False

def _actions_auto_handle(text: str) -> bool:
    """Autoriza temporalmente acciones sensibles sin pedir código repetido."""
    t = (text or "").strip().lower()
    if not t:
        return False

    if ("autoriza acciones" in t or "autorizar acciones" in t or "permite acciones" in t) and "no" not in t:
        mins = 10
        try:
            nums = [int(n) for n in re.findall(r"\d+", t)]
            if nums:
                mins = max(1, min(120, nums[0]))
        except Exception:
            mins = 10
        set_actions_auto_window(mins)
        speak(f"Listo. Acciones autorizadas por {mins} minutos.")
        return True

    if ("bloquea acciones" in t or "bloquear acciones" in t or "revoca acciones" in t or "revocar acciones" in t or "cancela autorización" in t or "cancela autorizacion" in t):
        clear_actions_auto_window()
        speak("Listo. Acciones bloqueadas; vuelvo a pedir confirmación.")
        return True

    if "estado autorizaciones" in t or "estado autorización" in t or "estado autorizacion" in t:
        if actions_auto_enabled():
            try:
                remaining = int(max(0, actions_auto_until_ts - time.time()) // 60)
            except Exception:
                remaining = 0
            speak(f"Acciones autorizadas. Quedan {remaining} minutos aproximadamente.")
        else:
            speak("Acciones NO autorizadas. Estoy pidiendo confirmación por código.")
        return True

    return False

def _perf_handle(text: str) -> bool:
    global perf_watchdog_enabled
    t = (text or "").strip().lower()
    if not t:
        return False

    if "monitor rendimiento" in t or "activa rendimiento" in t or "activar rendimiento" in t or "activa watchdog" in t:
        perf_watchdog_enabled = True
        speak("Listo. Monitor de rendimiento activo.")
        return True

    if "silencia rendimiento" in t or "desactiva rendimiento" in t or "desactivar rendimiento" in t or "apaga watchdog" in t:
        perf_watchdog_enabled = False
        speak("Listo. Monitor de rendimiento en silencio.")
        return True

    if "reporte rendimiento" in t or "diagnóstico rendimiento" in t or "diagnostico rendimiento" in t:
        speak("Ok. Tomando snapshot de rendimiento.")
        payload, out_path = capture_perf_snapshot(reason="user_report_perf")
        ram = payload.get("memory_percent")
        cpu = payload.get("cpu_percent")
        speak(f"RAM {ram} por ciento. CPU {cpu} por ciento.")
        if out_path:
            print(f"[PERF] Snapshot guardado en: {out_path}")
        return True

    return False

def _housekeeping_handle(text: str) -> bool:
    """Controla autolimpieza: activar/desactivar/reporte/ejecutar ahora."""
    if housekeeping is None:
        return False
    t = (text or "").strip().lower()
    if not t:
        return False

    if "autolimpieza estado" in t or "estado autolimpieza" in t:
        try:
            cfg = housekeeping.get_config()
            rep = housekeeping.run(allow_delete=False)
            speak(
                f"Autolimpieza {'activa' if cfg.enabled else 'apagada'}. "
                f"Modo {'solo reporte' if cfg.report_only else 'borra basura'}. "
                f"Detecté {len(rep.get('planned') or [])} archivos para limpiar."
            )
        except Exception:
            speak("No pude obtener el estado de autolimpieza.")
        return True

    if "autolimpieza desactivar" in t or "desactiva autolimpieza" in t or "apaga autolimpieza" in t:
        try:
            housekeeping.set_enabled(False)
            speak("Listo. Autolimpieza desactivada.")
        except Exception:
            speak("No pude desactivar autolimpieza.")
        return True

    if "autolimpieza activar" in t or "activa autolimpieza" in t:
        try:
            housekeeping.set_enabled(True)
            housekeeping.set_report_only(False)
            speak("Listo. Autolimpieza activada. Voy a borrar solo basura generada por NEXUS.")
        except Exception:
            speak("No pude activar autolimpieza.")
        return True

    if "autolimpieza solo reporte" in t or "autolimpieza reporte" in t:
        try:
            housekeeping.set_enabled(True)
            housekeeping.set_report_only(True)
            speak("Listo. Autolimpieza en modo solo reporte.")
        except Exception:
            speak("No pude cambiar autolimpieza a reporte.")
        return True

    if "autolimpieza ahora" in t or "limpia ahora" in t or "limpiar ahora" in t:
        try:
            rep = housekeeping.run(allow_delete=True)
            planned = len(rep.get("planned") or [])
            deleted = len(rep.get("deleted") or [])
            errs = len(rep.get("errors") or [])
            if deleted:
                speak(f"Autolimpieza lista. Eliminé {deleted} archivos de {planned} detectados.")
            else:
                speak(f"Autolimpieza lista. Detecté {planned} y no eliminé nada (modo reporte o nada viejo).")
            if errs:
                print(f"[HOUSE] Errores al limpiar: {errs}")
        except Exception as _e_h:
            print(f"[HOUSE] Error en autolimpieza: {_e_h}")
            speak("Falló la autolimpieza.")
        return True

    return False

def _new_confirm_code() -> str:
    try:
        return str(random.randint(1000, 9999))
    except Exception:
        return "0000"

def _request_login_confirmation(app: str) -> None:
    global pending_login
    code = _new_confirm_code()
    pending_login = {"app": app, "code": code, "expires": time.time() + 60}
    speak(f"Confirmación requerida. Para iniciar sesión en {app}, di: confirmo {code}.")

def _request_action_confirmation(kind: str, summary: str, data: dict, ttl_sec: int = 90) -> None:
    global pending_action
    # Si hay ventana de autorización, ejecuta sin pedir código.
    if actions_auto_enabled():
        try:
            # Ejecutar como si ya estuviera confirmado
            _execute_confirmed_action(kind, data or {})
            return
        except Exception:
            # Si falla, caemos al modo confirmación normal
            pass
    code = _new_confirm_code()
    pending_action = {"kind": kind, "code": code, "expires": time.time() + max(30, int(ttl_sec)), "data": data or {}}
    speak(f"Confirmación requerida. {summary}. Di: confirmo {code}.")

def _execute_confirmed_action(kind: str, data: dict) -> bool:
    """Ejecuta una acción ya autorizada (por código o por ventana auto)."""
    if kind == "whatsapp_send":
        if social_op is None:
            speak("Operador social no disponible.")
            return True
        contact = str(data.get("contact") or "").strip()
        message = str(data.get("message") or "").strip()
        autosend = bool(data.get("autosend"))
        ok, msg = social_op.send_whatsapp_to_contact(contact, message, autosend=autosend)
        speak(msg)
        return True

    if kind == "facebook_open":
        if social_op is None:
            speak("Operador social no disponible.")
            return True
        target = str(data.get("target") or "").strip()
        ok, msg = social_op.open_facebook_page(target)
        speak(msg)
        return True

    if kind == "selfheal_install":
        if nexus_self_heal is None:
            speak("Self-heal no disponible.")
            return True
        pkgs = data.get("packages") or []
        ok, out = nexus_self_heal.pip_install(list(pkgs))
        if ok:
            speak("Instalación terminada.")
        else:
            speak("Falló la instalación. Revisa consola.")
        print("\n[SELFHEAL] pip output:\n" + str(out))
        return True

    speak("Acción desconocida.")
    return True

def _try_confirm_login(text: str) -> bool:
    global pending_login
    if not pending_login:
        return False
    if time.time() > float(pending_login.get("expires") or 0):
        pending_login = None
        speak("Confirmación expirada. Repite el comando de iniciar sesión.")
        return True
    t = (text or "").strip().lower()
    if "cancela login" in t or "cancelar login" in t or "cancela inicio" in t:
        pending_login = None
        speak("Login cancelado.")
        return True
    if t.startswith("confirmo"):
        nums = re.findall(r"\d{4}", t)
        if not nums:
            speak("Dime el código de 4 dígitos.")
            return True
        if nums[0] != str(pending_login.get("code")):
            speak("Código incorrecto.")
            return True
        app = str(pending_login.get("app"))
        pending_login = None
        # Ejecutar login ya confirmado
        try:
            success, msg = nexus_vault.manager.login(app)
            speak(msg)
        except Exception as e:
            print(e)
            speak("Falló el login automático.")
        return True
    return False

def _try_confirm_action(text: str) -> bool:
    global pending_action
    if not pending_action:
        return False
    if time.time() > float(pending_action.get("expires") or 0):
        pending_action = None
        speak("Confirmación expirada. Repite el comando.")
        return True
    t = (text or "").strip().lower()
    if "cancela envio" in t or "cancela envío" in t or "cancelar envio" in t or "cancelar envío" in t or "cancela accion" in t or "cancela acción" in t:
        pending_action = None
        speak("Acción cancelada.")
        return True
    if not t.startswith("confirmo"):
        return False
    nums = re.findall(r"\d{4}", t)
    if not nums:
        speak("Dime el código de 4 dígitos.")
        return True
    if nums[0] != str(pending_action.get("code")):
        speak("Código incorrecto.")
        return True

    kind = str(pending_action.get("kind"))
    data = dict(pending_action.get("data") or {})
    pending_action = None
    return _execute_confirmed_action(kind, data)

# --- WATCHDOG DE RENDIMIENTO (MI PROPIO ENTORNO) ---
perf_watchdog_enabled = True
_perf_last_alert_ts = 0.0
_perf_watchdog_started = False

def _perf_watchdog_loop():
    global _perf_last_alert_ts
    high_cpu_streak = 0
    while True:
        try:
            time.sleep(8)
            if not perf_watchdog_enabled:
                continue

            cpu = psutil.cpu_percent(interval=0.25)
            ram = psutil.virtual_memory().percent

            if cpu >= 95:
                high_cpu_streak += 1
            else:
                high_cpu_streak = 0

            # Alertas con cooldown
            now = time.time()
            if (ram >= 92) or (high_cpu_streak >= 3):
                if (now - _perf_last_alert_ts) < 120:
                    continue
                _perf_last_alert_ts = now

                payload, out_path = capture_perf_snapshot(reason="watchdog")
                # Mensaje corto y accionable
                if ram >= 92:
                    speak("Alerta: RAM muy alta. Puedo sacar un diagnóstico y decirte qué proceso está pesado.")
                else:
                    speak("Alerta: CPU muy alta. Si sientes trabas, digo 'diagnostico' y te muestro el snapshot.")
                if out_path:
                    print(f"[WATCHDOG] Snapshot guardado: {out_path}")
        except Exception:
            # Nunca romper el core por el watchdog
            pass

if not _perf_watchdog_started:
    _perf_watchdog_started = True
    if not NEXUS_NO_AUTOSTART:
        threading.Thread(target=_perf_watchdog_loop, daemon=True).start()

# --- MEMORIA LARGA LOCAL (NOTAS + TAREAS) ---
mem = None
if nexus_memory is not None:
    try:
        mem = nexus_memory.NexusMemory(CONFIG_DIR)
        print("[MEM] Memoria local lista")
    except Exception as _e_m2:
        mem = None
        print(f"[MEM] Error iniciando memoria: {_e_m2}")

def _mem_handle(text: str) -> bool:
    if mem is None:
        return False
    t = (text or "").strip()
    tl = t.lower()
    if not t:
        return False

    # Anotar / memorizar (nota)
    if tl.startswith("anota ") or tl.startswith("memoriza ") or tl.startswith("recuerda esto "):
        payload = t
        payload = re.sub(r"^(anota|memoriza|recuerda esto)\s+", "", payload, flags=re.IGNORECASE).strip()
        if not payload:
            speak("¿Qué anoto?")
            return True
        note_id = mem.add_note(payload, kind="note")
        speak("Listo. Guardado." if note_id else "No pude guardarlo.")
        return True

    # Crear tarea
    if tl.startswith("tarea ") or tl.startswith("agrega tarea ") or tl.startswith("pendiente "):
        payload = re.sub(r"^(tarea|agrega tarea|pendiente)\s+", "", t, flags=re.IGNORECASE).strip()
        if not payload:
            speak("¿Qué tarea agrego?")
            return True
        task_id = mem.add_task(payload)
        speak(f"Hecho. Tarea {task_id}." if task_id else "No pude crear la tarea.")
        return True

    # Listar tareas
    if "lista tareas" in tl or "tareas pendientes" in tl or tl.strip() == "tareas":
        tasks = mem.list_tasks(status="todo", limit=8)
        if not tasks:
            speak("No tienes tareas pendientes.")
            return True
        # lectura compacta
        lines = []
        for x in tasks:
            lines.append(f"{x['id']}: {x['title']}")
        speak("Pendientes: " + "; ".join(lines))
        return True

    # Marcar tarea como hecha
    if tl.startswith("hecho tarea") or tl.startswith("lista hecho") or tl.startswith("completa tarea"):
        nums = [int(n) for n in re.findall(r"\d+", tl)]
        if not nums:
            speak("Dime el número de tarea. Ejemplo: hecho tarea 3")
            return True
        ok = mem.set_task_status(nums[0], "done")
        speak("Listo." if ok else "No pude marcarla.")
        return True

    # Sueño / consolidación
    if "modo sueño" in tl or tl.strip() == "duerme" or "dormir" in tl:
        d = mem.dream()
        todos = d.get("todos") or []
        notes = d.get("notes") or []
        speak(f"Sueño listo. Pendientes: {len(todos)}. Notas recientes: {len(notes)}.")
        return True

    # Buscar memoria
    if tl.startswith("recuerda ") or tl.startswith("busca en memoria"):
        q = re.sub(r"^(recuerda|busca en memoria)\s+", "", t, flags=re.IGNORECASE).strip()
        if not q:
            speak("Dime qué busco en tu memoria.")
            return True
        hits = mem.search_notes(q, limit=3)
        if not hits:
            speak("No encontré notas sobre eso.")
            return True
        # Solo leer texto, no ids si no hace falta
        speak("Encontré: " + " | ".join(h["text"] for h in hits))
        return True

    return False

def _selfheal_handle(text: str) -> bool:
    """Diagnóstico y autorreparación (supervisado)."""
    if nexus_self_heal is None:
        return False
    t = (text or "").strip().lower()
    if not t:
        return False

    if t == "diagnostico" or t == "diagnóstico" or "diagnostico" in t or "diagnóstico" in t:
        hc = nexus_self_heal.healthcheck()
        summary, actions = nexus_self_heal.summarize_healthcheck(hc)
        print("\n[DIAGNOSTICO]", hc)
        speak(summary)

        # Diagnóstico extendido (end-to-end) si está disponible.
        if nexus_doctor is not None:
            try:
                rep = nexus_doctor.run_doctor(
                    BASE_DIR,
                    CONFIG_DIR,
                    cloud_allowed=is_cloud_allowed(),
                    timeout_sec=6,
                    ping_keepalive_fn=lambda timeout_sec: nexus_db.db.keepalive_ping_http(timeout_sec=timeout_sec),
                    local_healthcheck_fn=lambda: hc,
                )
                doc_sum, steps = nexus_doctor.summarize_report(rep)
                print("\n[DOCTOR]", rep)
                speak(doc_sum)
                if steps:
                    speak("Siguiente: " + "; ".join(steps[:3]))
            except Exception as _e_doc:
                print(f"[DOCTOR] Error ejecutando doctor: {_e_doc}")

        # Si hay recursos locales faltantes, decirlo claro
        try:
            missing_files = [x.get("name") for x in (hc.get("files") or []) if isinstance(x, dict) and not x.get("ok")]
            if missing_files:
                speak("Me faltan recursos locales: " + ", ".join([str(x) for x in missing_files if x]))
        except Exception:
            pass

        # Proponer autorreparación si faltan requeridos
        if "install_required" in actions:
            missing = [x["module"] for x in (hc.get("required") or []) if not x.get("ok")]
            if missing:
                pkgs = missing
                try:
                    pkgs = nexus_self_heal.pip_packages_for_missing(missing)
                except Exception:
                    pkgs = missing
                _request_action_confirmation(
                    kind="selfheal_install",
                    summary=f"Puedo instalar dependencias requeridas: {', '.join(pkgs)}",
                    data={"packages": pkgs},
                    ttl_sec=120,
                )
        return True

    if "autorreparar" in t or "auto reparar" in t or "auto-reparar" in t:
        # Autorreparar equivale a correr diagnostico y proponer acciones
        hc = nexus_self_heal.healthcheck()
        summary, actions = nexus_self_heal.summarize_healthcheck(hc)
        print("\n[DIAGNOSTICO]", hc)
        speak(summary)
        if "install_required" in actions:
            missing = [x["module"] for x in (hc.get("required") or []) if not x.get("ok")]
            if missing:
                pkgs = missing
                try:
                    pkgs = nexus_self_heal.pip_packages_for_missing(missing)
                except Exception:
                    pkgs = missing
                _request_action_confirmation(
                    kind="selfheal_install",
                    summary=f"Voy a instalar: {', '.join(pkgs)}",
                    data={"packages": pkgs},
                    ttl_sec=120,
                )
        return True

    return False

def _offline_assistant_answer(user_text: str) -> str:
    """Respuesta offline: usa memoria + tareas + watchtower sin nube."""
    t = (user_text or "").strip()
    tl = t.lower()
    if mem is None:
        return "Estoy en modo offline. Puedo abrir cosas locales y ejecutar comandos, pero mi memoria larga no está disponible."

    # Heurística: si pregunta por pendientes
    if "pendiente" in tl or "tareas" in tl:
        tasks = mem.list_tasks(status="todo", limit=5)
        if not tasks:
            return "No tienes tareas pendientes ahora."
        return "Pendientes: " + "; ".join(f"{x['id']}: {x['title']}" for x in tasks)

    # Buscar notas por palabras clave
    hits = mem.search_notes(t, limit=2)
    if hits:
        return "En tu memoria tengo: " + " | ".join(h["text"] for h in hits)

    # Watchtower
    try:
        if watchtower is not None and ("mensajes" in tl or "chat" in tl):
            n = watchtower.unread_count()
            return f"Tienes {n} mensajes nuevos en tu bandeja local. Di: 'lee mensajes 3'."
    except Exception:
        pass

    return "Estoy en modo offline. Dime si quieres que lo anote como nota, lo convierta en tarea, o te ubique/abra un archivo o carpeta."

# --- PRIVACIDAD (CONTROL DE NUBE) ---
# offline: no llamadas a internet/nube
# supervised: solo nube si el usuario autoriza explícitamente (persistente con flag)
# online: nube permitida
PRIVACY_MODE = os.environ.get("NEXUS_PRIVACY_MODE", "supervised").strip().lower()
CLOUD_ALLOWED_FLAG = os.path.join(CONFIG_DIR, "cloud_allowed.flag")
CLOUD_BLOCKED_FLAG = os.path.join(CONFIG_DIR, "cloud_blocked.flag")

# En modo "online" (arranque normal), el bloqueo de nube es SOLO de sesión.
cloud_runtime_blocked = False

def _cloud_allowed_default() -> bool:
    if PRIVACY_MODE == "offline":
        return False

    # Arranque normal: nube permitida por defecto y sin bloqueo persistente.
    if PRIVACY_MODE == "online":
        try:
            # Si quedó un bloqueo viejo, lo limpiamos para que el arranque sea normal.
            if os.path.exists(CLOUD_BLOCKED_FLAG):
                os.remove(CLOUD_BLOCKED_FLAG)
        except Exception:
            pass
        return True

    # Bloqueo persistente manual (gana sobre todo) en supervised
    try:
        if os.path.exists(CLOUD_BLOCKED_FLAG):
            return False
    except Exception:
        pass
    # supervised
    try:
        return os.path.exists(CLOUD_ALLOWED_FLAG)
    except Exception:
        return False

cloud_allowed = _cloud_allowed_default()

def is_cloud_allowed() -> bool:
    global cloud_allowed
    if PRIVACY_MODE == "online":
        return not bool(cloud_runtime_blocked)
    # En caso de que el usuario cambie el flag en disco
    try:
        if os.path.exists(CLOUD_BLOCKED_FLAG):
            cloud_allowed = False
            return False
        if PRIVACY_MODE == "supervised":
            cloud_allowed = os.path.exists(CLOUD_ALLOWED_FLAG)
    except Exception:
        pass
    return bool(cloud_allowed)

def set_cloud_allowed(allowed: bool) -> None:
    global cloud_allowed, cloud_runtime_blocked
    cloud_allowed = bool(allowed)

    # En modo normal (online), no persistimos nada en disco.
    if PRIVACY_MODE == "online":
        cloud_runtime_blocked = not cloud_allowed
        # Limpieza defensiva de flags persistentes si existieran
        try:
            if os.path.exists(CLOUD_BLOCKED_FLAG):
                os.remove(CLOUD_BLOCKED_FLAG)
            if os.path.exists(CLOUD_ALLOWED_FLAG):
                os.remove(CLOUD_ALLOWED_FLAG)
        except Exception:
            pass
        return

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Bloqueo persistente siempre disponible
        if cloud_allowed:
            if os.path.exists(CLOUD_BLOCKED_FLAG):
                os.remove(CLOUD_BLOCKED_FLAG)
        else:
            with open(CLOUD_BLOCKED_FLAG, "w", encoding="utf-8") as f:
                f.write("blocked")

        # En supervised, además dejamos evidencia explícita de autorización
        if PRIVACY_MODE == "supervised":
            if cloud_allowed:
                with open(CLOUD_ALLOWED_FLAG, "w", encoding="utf-8") as f:
                    f.write("ok")
            else:
                if os.path.exists(CLOUD_ALLOWED_FLAG):
                    os.remove(CLOUD_ALLOWED_FLAG)
    except Exception as e:
        print(f"[PRIVACY] No pude persistir flags nube: {e}")

# ESTADOS DE CONVERSACIÓN
STATE_IDLE = "IDLE"          # Esperando "Nexus"
STATE_LISTENING_CMD = "CMD"  # Esperando comando (ej: "Caja")
STATE_LISTENING_DIMS = "DIMS"# Esperando medidas (ej: "20 20 10")
current_state = STATE_IDLE

# Cargar Configuración
def load_config():
    global COMMANDS, PERSONA
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            COMMANDS = json.load(f)
        with open(os.path.join(CONFIG_DIR, "persona.txt"), "r", encoding="utf-8") as f:
            PERSONA = f.read()
    except Exception as e:
        print(f"[ERROR CONFIG] {e}")
        COMMANDS = {}
        PERSONA = "Eres un asistente útil."

load_config()
wikipedia.set_lang("es")

def _load_chat_history():
    global chat_history
    try:
        if os.path.exists(CHAT_MEMORY_FILE):
            with open(CHAT_MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                chat_history = [m for m in data if isinstance(m, dict)][-30:]
    except Exception as e:
        print(f"[CHAT] No pude cargar memoria: {e}")

def _save_chat_history():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CHAT_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_history[-30:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CHAT] No pude guardar memoria: {e}")

def _chat_add(role: str, content: str):
    if not content:
        return
    try:
        import datetime as _datetime
        chat_history.append({
            "role": role,
            "content": str(content).strip(),
            "ts": _datetime.datetime.now().isoformat(timespec="seconds"),
        })
        # limitar tamaño
        if len(chat_history) > 60:
            del chat_history[:-60]
        _save_chat_history()
    except Exception:
        pass

def _system_prompt_chat():
    # Mantenerlo compacto: esto se va a TTS.
    return (
        PERSONA
        + "\n\nREGLAS DE CONVERSACIÓN:\n"
        + "- Sé intuitivo y proactivo: si falta info, pregunta 1 cosa clave.\n"
        + "- Propón 1 ruta principal y 1 alternativa si aplica.\n"
        + "- Nunca inventes: si no puedes, dilo y explica el bloqueo real.\n"
        + "- Respuestas por voz: máximo 2–4 frases cortas.\n"
        + "- Si el usuario pide 'web real', ofrece fuentes y pide aprobación.\n"
    )

def ask_groq_chat(user_text: str):
    if not is_cloud_allowed():
        return "Modo privado activo. Si quieres, di: 'autoriza nube'."

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "No tengo llave del cerebro (GROQ_API_KEY). Puedo usar funciones básicas o buscar en Wikipedia."
    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        # Convertir memoria a formato mensajes
        mem_msgs = []
        for m in chat_history[-12:]:
            role = m.get("role")
            content = m.get("content")
            if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                mem_msgs.append({"role": role, "content": content.strip()})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _system_prompt_chat()},
                *mem_msgs,
                {"role": "user", "content": user_text},
            ],
            temperature=0.6,
            max_tokens=220,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[CHAT GROQ ERROR] {e}")
        return "Fallo el cerebro online. Si me dices el error exacto o lo pegas en consola, lo resolvemos paso a paso."

def enable_chat_mode(seconds: int = 180):
    global chat_mode_until_ts, current_state
    chat_mode_until_ts = time.time() + max(30, int(seconds))
    current_state = STATE_CONVERSATION

def disable_chat_mode():
    global chat_mode_until_ts
    chat_mode_until_ts = 0.0

_load_chat_history()

# --- MÓDULO DE AUTOPRESERVACIÓN (Monitor RAM) ---
def check_vital_signs():
    ram = psutil.virtual_memory()
    if ram.percent > 90:
        print(f"[ALERTA VITAL] RAM al {ram.percent}%. Peligro.")
        speak("Jefe, estoy ahogado. La RAM está al límite. Cierra algo antes de que colapsemos.")
        return False
    return True

def capture_perf_snapshot(reason: str = "user_report"):
    """Captura un snapshot ligero de rendimiento y lo guarda en la carpeta `logs/`.

    Nota: esto NO optimiza Windows ni otras apps, solo ayuda a diagnosticar.
    """
    try:
        import datetime as _datetime

        logs_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        cpu_pct = psutil.cpu_percent(interval=0.35)
        mem = psutil.virtual_memory()
        try:
            disk_root = os.getenv("SystemDrive", "C:") + "\\"
            disk_pct = psutil.disk_usage(disk_root).percent
        except Exception:
            disk_pct = None

        top_procs = []
        try:
            for proc in psutil.process_iter(["pid", "name", "username", "memory_info"]):
                info = proc.info
                rss = None
                mi = info.get("memory_info")
                if mi is not None:
                    rss = getattr(mi, "rss", None)
                top_procs.append({
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "user": info.get("username"),
                    "rss_bytes": rss,
                })

            top_procs = [p for p in top_procs if isinstance(p.get("rss_bytes"), int)]
            top_procs.sort(key=lambda p: p["rss_bytes"], reverse=True)
            top_procs = top_procs[:8]
        except Exception as e:
            top_procs = [{"error": f"process_iter_failed: {e}"}]

        freed = None
        try:
            freed = gc.collect()
        except Exception:
            pass

        payload = {
            "ts": _datetime.datetime.now().isoformat(),
            "reason": reason,
            "cpu_percent": cpu_pct,
            "memory_percent": mem.percent,
            "memory_available_bytes": getattr(mem, "available", None),
            "disk_percent": disk_pct,
            "gc_freed_objects": freed,
            "top_processes_by_rss": top_procs,
        }

        stamp = _datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(logs_dir, f"perf_snapshot_{stamp}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return payload, out_path
    except Exception as e:
        return {"error": str(e)}, None

import edge_tts
import asyncio
import pygame

# --- MÓDULO BOCA PURA (ASÍNCRONO PARA INTERRUPCIÓN) ---
def speak(text, cast_device=None):
    """Habla en un hilo separado para permitir interrupción."""
    global is_speaking
    is_speaking = True # BLOQUEAR OÍDO

    # Evitar apilamiento: si ya hay un hilo de voz, esperar un poco o matar (nexus_voice.callar ya lo hace)
    print(f"[NEXUS DICE] {text}")
    
    # HACK ANTI-DUPLICIDAD:
    nexus_voice.callar()
    time.sleep(0.05) 
    
    def speech_wrapper():
        global is_speaking
        nexus_voice.hablar(text)
        time.sleep(0.5) # Pequeña pausa para evitar eco final
        is_speaking = False # DESBLOQUEAR OÍDO

    # Ejecutar en hilo daemon
    threading.Thread(target=speech_wrapper, daemon=True).start()

import datetime

import speech_recognition as sr

import tempfile
import wave

# --- ESCUCHA GROQ WHISPER (ONLINE - ULTRA ALTA PRECISIÓN) ---
def listen_whisper_groq():
    if not is_cloud_allowed():
        print("[WHISPER] Nube bloqueada (modo privado).")
        return None
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[WHISPER] No hay API Key. Usando Google como fallback.")
        return listen_google()

    r = sr.Recognizer()
    r.pause_threshold = 1.2 # Ajuste: 1.2s es suficiente para respirar sin cortar
    with sr.Microphone() as source:
        print("[WHISPER] Escuchando comando (Alta Fidelidad)...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Escucha extendida a 25 segundos
            audio = r.listen(source, timeout=8, phrase_time_limit=25)
            print("[WHISPER] Procesando audio...")
            
            # Guardar temporalmente como WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_path = tmp_file.name
            
            # Enviar a Groq
            from groq import Groq
            client = Groq(api_key=api_key)
            
            with open(tmp_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(tmp_path, file.read()),
                    model="whisper-large-v3",
                    response_format="json",
                    language="es",
                    temperature=0.0
                )
            
            # Limpieza
            try: os.remove(tmp_path)
            except: pass
            
            text = transcription.text
            print(f"[WHISPER] Entendido: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("[WHISPER] Silencio.")
            return None
        except Exception as e:
            print(f"[WHISPER ERROR] {e}")
            print("[WHISPER] Fallback a Google.")
            return listen_google()

# --- ESCUCHA GOOGLE (LEGACY/FALLBACK) ---
def listen_google():
    if not is_cloud_allowed():
        print("[GOOGLE] Nube bloqueada (modo privado).")
        return None
    r = sr.Recognizer()
    r.pause_threshold = 1.2 # Ajuste: 1.2s es suficiente para respirar
    with sr.Microphone() as source:
        print("[GOOGLE] Escuchando comando...")
        # Ajuste dinámico de ruido para mejorar precisión
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Escucha extendida a 25 segundos para comandos largos
            audio = r.listen(source, timeout=8, phrase_time_limit=25)
            print("[GOOGLE] Procesando...")
            text = r.recognize_google(audio, language="es-MX")
            print(f"[GOOGLE] Entendido: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            print("[GOOGLE] Timeout (silencio).")
            return None
        except sr.UnknownValueError:
            print("[GOOGLE] No entendí audio.")
            return None
        except sr.RequestError as e:
            print(f"[GOOGLE] Error conexión: {e}")
            return None
        except Exception as e:
            print(f"[GOOGLE] Error general: {e}")
            return None

# --- HILO DE CONSOLA (FALLBACK TEXTO) ---
def console_input_listener():
    print("[SISTEMA] Consola de texto activa. Escribe comandos y pulsa Enter.")
    while True:
        try:
            # Input bloqueante en hilo separado
            text = input()
            if text.strip():
                # --- COMANDOS DE CONSOLA (ADMIN) ---
                if text.startswith("vault add"):
                    # Sintaxis: vault add facebook usuario pass
                    parts = text.split(" ")
                    if len(parts) >= 5:
                        app = parts[2]
                        user = parts[3]
                        pwd = " ".join(parts[4:]) # Pass puede tener espacios
                        res = nexus_vault.manager.add_credential(app, user, pwd)
                        print(f"[VAULT] {res}")
                    else:
                        print("[VAULT ERROR] Uso: vault add [app] [user] [pass]")
                    continue
                
                print(f"[CONSOLA] Recibido: {text}")
                # Inyectar directamente al procesador
                process_conversation(text)
        except EOFError:
            break
        except Exception as e:
            print(f"[CONSOLA ERROR] {e}")

# --- MÓDULO CONTROL DE APPS ---
def app_control(app_name, action="open"):
    try:
        if action == "open":
            if not check_vital_signs(): return
            
            # Caso Especial: YouTube (Web)
            if app_name == "youtube":
                speak("Abriendo YouTube...")
                webbrowser.open("https://www.youtube.com")
                return

            # Caso Especial: Nexus Panel
            if app_name == "nexus_panel":
                speak("Abriendo Panel de Control...")
                panel_path = os.path.join(BASE_DIR, "nexus_panel.py")
                subprocess.Popen([sys.executable, panel_path])
                return
            
            # Caso Especial: Apps Web y E-commerce
            # DEFINICIÓN DE MARCAS (DINÁMICA DESDE NUBE)
            try:
                BRANDS = nexus_db.db.get_brands()
                if not BRANDS: # Fallback de emergencia si no hay internet
                    print("[WARN] Sin conexión a marcas. Usando caché mínima.")
                    BRANDS = {
                        "atf": {"whatsapp": "https://web.whatsapp.com"},
                        "milens": {"whatsapp": "https://web.whatsapp.com"},
                        "canbus": {"whatsapp": "https://web.whatsapp.com"}
                    }
            except: BRANDS = {}

            web_apps = {
                "pinterest": "https://www.pinterest.com",
                "canvas": "https://www.canva.com",
                "canva": "https://www.canva.com",
                "mercado libre": "https://www.mercadolibre.com.mx",
                "mercado": "https://www.mercadolibre.com.mx",
                "amazon": "https://www.amazon.com.mx",
                "aliexpress": "https://es.aliexpress.com",
                "ali": "https://es.aliexpress.com",
                "spotify": "https://open.spotify.com",
                "chrome": "google chrome",
                "edge": "microsoft edge"
            }
            
            # Normalizar nombre
            clean_name = app_name.lower()
            
            # LÓGICA MULTI-MARCA
            # Detectar si el usuario especificó la marca en el comando
            target_url = None
            
            # 1. WhatsApp
            if "whatsapp" in clean_name or "wats" in clean_name:
                # Prioridad por mención explícita
                if "milens" in clean_name or "creaciones" in clean_name:
                    speak("Abriendo WhatsApp de Creaciones Milens...")
                    target_url = BRANDS.get("milens", {}).get("whatsapp")
                elif "canbus" in clean_name:
                    speak("Abriendo WhatsApp de CanbusFix...")
                    target_url = BRANDS.get("canbus", {}).get("whatsapp")
                else:
                    # Default o ATF
                    speak("Abriendo WhatsApp Principal (Faros)...")
                    target_url = BRANDS.get("atf", {}).get("whatsapp")
            
            # 2. Facebook
            elif "facebook" in clean_name or "face" in clean_name:
                if "milens" in clean_name:
                    target_url = BRANDS.get("milens", {}).get("facebook_url")
                elif "canbus" in clean_name:
                    target_url = BRANDS.get("canbus", {}).get("facebook_url")
                else:
                    target_url = BRANDS.get("atf", {}).get("facebook_url")
            
            # 3. TikTok
            elif "tiktok" in clean_name or "tik tok" in clean_name:
                if "milens" in clean_name:
                    target_url = BRANDS.get("milens", {}).get("tiktok_url")
                else:
                    target_url = BRANDS.get("atf", {}).get("tiktok_url")

            # 4. Apps Genéricas (Búsqueda en diccionario simple)
            else:
                for key, url in web_apps.items():
                    if key in clean_name:
                        target_url = url
                        break

            if target_url:
                if "http" in target_url:
                    speak(f"Abriendo enlace...")
                    webbrowser.open(target_url)
                    return
                else:
                    app_name = target_url # Nombre de app local

            # INTENTO 1: Ruta Exacta (Más rápido y seguro)
            # Normalizar nombre para buscar en diccionario
            key_name = app_name.lower().replace(" ", "")
            # Mapeo manual de nombres comunes a claves de EXACT_PATHS
            path_keys = {
                "coreldraw": "coreldraw", "corel": "corel", 
                "aspire": "aspire", "vectric": "aspire",
                "photopaint": "photopaint", "foto": "photopaint"
            }
            
            target_key = path_keys.get(key_name, key_name)
            
            if target_key in EXACT_PATHS and os.path.exists(EXACT_PATHS[target_key]):
                speak(f"Lanzando {app_name} desde sistema...")
                subprocess.Popen(EXACT_PATHS[target_key])
                nexus_logs.bitacora.log("SISTEMA", f"Abriendo APP: {app_name}")
                return

            # INTENTO 2: AppOpener (Búsqueda difusa)
            speak(f"Buscando {app_name}...")
            open_app(app_name, match_closest=True, throw_error=True)
            nexus_logs.bitacora.log("SISTEMA", f"Abriendo APP (Opener): {app_name}")
        else:
            speak(f"Cerrando {app_name}...")
            close_app(app_name, match_closest=True, throw_error=True)
            nexus_logs.bitacora.log("SISTEMA", f"Cerrando APP: {app_name}")
    except Exception as e:
        speak(f"No pude abrir {app_name}. ¿Está instalada?")
        print(f"[APP ERROR] {e}")

# --- MÓDULO IOT (WRAPPER SEGURO) ---
def scan_iot():
    if not IOT_ACTIVE: return
    print("[IOT] Iniciando escaneo en subproceso...")
    try:
        # Ejecutar script externo sin bloquear
        subprocess.Popen(["python", "nexus_iot.py", "scan"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"[IOT LAUNCH ERROR] {e}")

def cast_terror(device_name="oficina 2", message="No... mires... atrás...", lang="es"):
    if not IOT_ACTIVE: return
    print(f"[IOT] Lanzando ataque a {device_name}...")
    try:
        # Ejecutar script externo
        subprocess.Popen(["python", "nexus_iot.py", "terror", device_name, message, lang], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"[IOT CAST ERROR] {e}")

def cast_media(device_name, media_url, media_type="video/mp4"):
    # Por ahora desactivado o implementar en nexus_iot.py si se requiere
    pass

# --- CEREBRO (Groq API + Lógica Local) ---
def ask_groq(prompt):
    if not is_cloud_allowed():
        return "Modo privado activo. Si quieres que use cerebro online, di: 'autoriza nube'."

    api_key = os.environ.get("GROQ_API_KEY") 
    if not api_key: return "Sin llave de cerebro. Solo funciones básicas."
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": PERSONA}, {"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=150
        )
        return completion.choices[0].message.content
    except: return "Error de conexión cerebral."

def interpret_intent(text):
    """
    Usa Groq para analizar la intención del usuario y extraer parámetros estructurados.
    Retorna un diccionario con 'intent', 'generator' (opcional), 'params' (dict).
    """
    if not is_cloud_allowed():
        return None

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return None

    sys_prompt = """
    Analiza el comando del usuario y extrae la intención y parámetros en JSON puro.
    Intenciones válidas:
    - GENERATE_DESIGN: Para crear cajas, estantes, muebles (keywords: caja, estante, diseño, generar).
      - generator: Nombre del generador de boxes.py (ej: ClosedBox, TrayLayout, FlexBox, TypeTray). Default: ClosedBox.
      - params: Diccionario con x, y, h, thickness (todas en mm).
    - OPEN_APP: Para abrir programas o webs.
      - params: { "app_name": "nombre" }
    - CODING: Para programar, crear scripts o código.
    - UNKNOWN: Si no es ninguna de las anteriores.
    
    Responde SOLO con el JSON.
    Ejemplo: { "intent": "GENERATE_DESIGN", "generator": "ClosedBox", "params": { "x": 100, "y": 100, "h": 50, "thickness": 3.0 } }
    """

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        response_content = completion.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        print(f"[INTENT ERROR] {e}")
        return None

def generate_box_v2(generator, params):
    """Generador flexible usando boxes.py"""
    try:
        # Extraer parámetros básicos con defaults
        x = params.get("x", 100)
        y = params.get("y", 100)
        h = params.get("h", 100)
        thickness = params.get("thickness", 3.0)
        
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{generator}_{x}x{y}x{h}_{ts}.svg"
        output_path = os.path.join(WATCH_DIR, filename)
        os.makedirs(WATCH_DIR, exist_ok=True)
        
        boxes_script = os.path.join(BASE_DIR, "TOOLS", "boxes", "boxes", "scripts", "boxes_main.py")
        python_path = os.path.join(BASE_DIR, "TOOLS", "boxes")
        
        # Construir comando dinámico
        cmd = [sys.executable, boxes_script, generator]
        
        # Añadir todos los params del diccionario al comando
        for k, v in params.items():
            cmd.append(f"--{k}={v}")
            
        cmd.append(f"--output={output_path}")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = python_path + os.pathsep + env.get("PYTHONPATH", "")
        
        print(f"[BOXES V2] Generando: {cmd}")
        subprocess.run(cmd, env=env, check=True, capture_output=True)
        
        if os.path.exists(output_path):
            speak(f"Diseño {generator} generado exitosamente.")
            os.startfile(WATCH_DIR)
        else:
            speak("Error: No se generó el archivo de salida.")
            
    except Exception as e:
        print(f"[BOXES V2 ERROR] {e}")
        speak("Hubo un problema con el generador de diseños.")

def web_search(query):
    speak("Investigando...")
    try: return wikipedia.summary(query, sentences=2)
    except:
        try:
            results = DDGS().text(query, max_results=1)
            if results: return results[0]['body']
        except: return "No encontré nada."

# --- NUEVO: BÚSQUEDA INTELIGENTE EN PLATAFORMAS ---
def smart_search(text):
    # Detectar patrón "busca X en Y"
    # Y ser una de las apps conocidas
    platforms = {
        "youtube": "https://www.youtube.com/results?search_query={}",
        "google": "https://www.google.com/search?q={}",
        "pinterest": "https://www.pinterest.com/search/pins/?q={}",
        "amazon": "https://www.amazon.com.mx/s?k={}",
        "mercado libre": "https://listado.mercadolibre.com.mx/{}",
        "aliexpress": "https://es.aliexpress.com/wholesale?SearchText={}",
        "wikipedia": None # Special case handled by fallback
    }
    
    for platform, url_template in platforms.items():
        if f"en {platform}" in text or f"en el {platform}" in text:
            # Limpiar query
            query = text.replace(f"en {platform}", "").replace(f"en el {platform}", "").replace("busca", "").strip()
            
            if url_template:
                url = url_template.format(query.replace(" ", "+"))
                speak(f"Buscando {query} en {platform}...")
                webbrowser.open(url)
                return True
    
    return False

# --- VARIABLES GLOBALES AUDIO ---
stream = None
# Variable para evitar re-entradas fatales en audio
audio_lock = threading.Lock()

# --- DATOS DE COTIZACIÓN (CONFIGURABLES) ---
# Precio por minuto de máquina (incluye luz, tubo, desgaste)
COSTO_MINUTO_LASER = 3.0  # Costo interno estimado
PRECIO_MINUTO_VENTA = 8.0 # Precio al cliente (Tu solicitud)

# --- Cargar Materiales (HÍBRIDO: NUBE + LOCAL) ---
MATERIALES_FILE = os.path.join(CONFIG_DIR, "materiales.json")
MATERIALES = {}

def load_materials():
    global MATERIALES
    try:
        # 1. Intentar Nube
        print("[SYNC] Descargando materiales de la nube...")
        cloud_mats = nexus_db.db.get_materials()
        if cloud_mats:
            MATERIALES = cloud_mats
            print(f"[SYNC] {len(MATERIALES)} materiales sincronizados.")
            # Opcional: Actualizar caché local aquí
            return

        # 2. Fallback Local
        if os.path.exists(MATERIALES_FILE):
            with open(MATERIALES_FILE, "r", encoding="utf-8") as f:
                MATERIALES = json.load(f)
            print("[MATERIALES] Cargados desde local (Offline).")
    except Exception as e:
        print(f"[ERROR MATERIALES] {e}")

load_materials()

# --- MÁQUINA DE ESTADOS (CORE) ---
STATE_IDLE = "IDLE"          # Esperando "Nexus"
STATE_LISTENING_CMD = "CMD"  # Esperando comando (ej: "Caja")
STATE_LISTENING_DIMS = "DIMS"# Esperando medidas
STATE_LISTENING_COST = "COST"# Esperando minutos para cotizar
STATE_LISTENING_ORDER = "ORDER" # Esperando datos de pedido
STATE_CONVERSATION = "CHAT"  # Conversación continua sin repetir 'Nexus'

def process_conversation(text):
    # Registro de interacción (memoria local)
    try:
        if mem is not None and text and text.strip():
            mem.log_interaction("user", text)
    except Exception:
        pass
    global current_state, stream
    text = text.lower()

    # Si está activo el modo conversación, no exigir trigger.
    try:
        if current_state == STATE_IDLE and chat_mode_until_ts and time.time() < chat_mode_until_ts:
            current_state = STATE_CONVERSATION
    except Exception:
        pass
    
    # LIMPIEZA DE ECO PROPIA
    # Si escucha "mande" o "manden", lo borra para que no confunda el comando
    text = text.replace("manden", "").replace("mande", "").strip()

    # --- ESTADO 1: IDLE (ESPERANDO 'NEXUS') ---
    if current_state == STATE_IDLE:
        # Flexibilizar: busca cualquiera de los aliases
        found_trigger = False
        for alias in TRIGGER_ALIASES:
            if alias in text:
                found_trigger = True
                break
        
        if found_trigger:
            speak("Mande.")

            # Si nube permitida, usar Google para capturar el comando completo.
            # Si no, entrar a modo comando y esperar el siguiente resultado de Vosk.
            if not is_cloud_allowed():
                current_state = STATE_LISTENING_CMD
                return

            # --- HYBRID MODE: SWITCH TO GOOGLE ---
            try:
                if stream and stream.is_active():
                    stream.stop_stream()
                command_text = listen_google()
                if stream and stream.is_stopped():
                    stream.start_stream()
            except Exception as e:
                print(f"[AUDIO ERROR] Fallo cambio de stream: {e}")
                command_text = None
                try:
                    if stream and stream.is_stopped():
                        stream.start_stream()
                except:
                    pass

            if command_text:
                current_state = STATE_LISTENING_CMD
                process_conversation(command_text)
            else:
                current_state = STATE_IDLE

            return
        else:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [IGNORADO] Esperaba '{TRIGGER_PHRASE}', escuché: '{text}'")

    # --- ESTADO 2: ESPERANDO COMANDO ---
    elif current_state == STATE_LISTENING_CMD:
        # Autorizaciones temporales (evita pedir confirmación repetida)
        try:
            if _actions_auto_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Ayuda / comandos
        try:
            if _help_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Supabase keepalive (anti-pausa)
        try:
            if _keepalive_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Autolimpieza / optimización continua
        try:
            if _housekeeping_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Monitor de rendimiento / snapshot
        try:
            if _perf_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Self-heal / diagnóstico (supervisado)
        try:
            if _selfheal_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Memoria/tareas (offline)
        try:
            if _mem_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Watchtower: lectura/resumen de mensajes locales
        try:
            if _watchtower_handle(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Confirmación de login pendiente
        try:
            if _try_confirm_login(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # Confirmación de acciones (WhatsApp / FB)
        try:
            if _try_confirm_action(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # --- SOCIAL: aprender targets / enviar mensajes ---
        try:
            t = (text or "").strip().lower()
            if social_op is not None:
                # Memoriza contacto NOMBRE es +521...
                if ("memoriza contacto" in t or "aprende contacto" in t) and " es " in t:
                    tmp = t.replace("aprende contacto", "").replace("memoriza contacto", "").strip()
                    name, phone = tmp.split(" es ", 1)
                    ok = social_op.set_contact(name.strip(), phone.strip())
                    speak("Listo." if ok else "No pude guardar ese contacto.")
                    current_state = STATE_IDLE
                    return

                # Memoriza página NOMBRE es URL
                if ("memoriza página" in t or "memoriza pagina" in t or "aprende página" in t or "aprende pagina" in t) and " es " in t:
                    tmp = t.replace("aprende página", "").replace("aprende pagina", "").replace("memoriza página", "").replace("memoriza pagina", "").strip()
                    name, url = tmp.split(" es ", 1)
                    ok = social_op.set_page(name.strip(), url.strip())
                    speak("Listo." if ok else "No pude guardar esa página. Debe ser URL https.")
                    current_state = STATE_IDLE
                    return

                # WhatsApp: "envía por whatsapp a NOMBRE: MENSAJE" / "envialo por whatsapp a NOMBRE"
                if "whatsapp" in t and (t.startswith("envia") or t.startswith("envía") or "envialo" in t or "envíalo" in t or "dile a" in t):
                    contact = ""
                    message = ""
                    # patrón 1: envia por whatsapp a NAME: MSG
                    m1 = re.search(r"(?:envia|envía)\s+(?:por\s+)?whatsapp\s+a\s+([^:]+):\s*(.+)$", t)
                    if m1:
                        contact = m1.group(1).strip()
                        message = m1.group(2).strip()
                    else:
                        # patrón 2: dile a NAME que MSG envialo por whatsapp
                        m2 = re.search(r"dile\s+a\s+(.+?)\s+que\s+(.+?)(?:\s+envialo\s+por\s+whatsapp|\s+envíalo\s+por\s+whatsapp|\s+por\s+whatsapp)$", t)
                        if m2:
                            contact = m2.group(1).strip()
                            message = m2.group(2).strip()

                    if contact and message:
                        # Confirmación obligatoria (envío externo)
                        autosend = True
                        _request_action_confirmation(
                            kind="whatsapp_send",
                            summary=f"Voy a enviar WhatsApp a {contact}",
                            data={"contact": contact, "message": message, "autosend": autosend},
                            ttl_sec=120,
                        )
                        current_state = STATE_IDLE
                        return

                # Facebook: "en fb ve a pagina NOMBRE" / "facebook abre NOMBRE"
                if ("en fb" in t or "facebook" in t) and ("ve a" in t or "abre" in t or "pagina" in t or "página" in t):
                    target = t
                    target = target.replace("en fb", "").replace("facebook", "").replace("ve a", "").replace("abre", "").replace("pagina", "").replace("página", "").strip()
                    if not target:
                        target = "https://www.facebook.com"
                    _request_action_confirmation(
                        kind="facebook_open",
                        summary=f"Voy a abrir Facebook: {target}",
                        data={"target": target},
                        ttl_sec=120,
                    )
                    current_state = STATE_IDLE
                    return
        except Exception:
            pass
        # Ecosistema local: ubicar/abrir/reindexar/aprender
        try:
            if _eco_handle_locate_or_open(text):
                current_state = STATE_IDLE
                return
        except Exception:
            pass

        # --- PRIVACIDAD (CONTROL DE NUBE) ---
        if "autoriza nube" in text or "autorizar nube" in text or "permitir nube" in text:
            set_cloud_allowed(True)
            speak("Nube autorizada. Puedo usar cerebro online y web real.")
            current_state = STATE_IDLE
            return
        if "bloquea nube" in text or "bloquear nube" in text or "modo privado" in text:
            set_cloud_allowed(False)
            speak("Nube bloqueada. Opero offline.")
            current_state = STATE_IDLE
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [COMANDO] Analizando: '{text}'")
        
        # --- COMANDOS PRIORITARIOS (VIDEOS) ---
        if (
            "modo conversacion" in text or "modo conversación" in text or
            "modo chat" in text or "conversar" in text or "platicar" in text
        ):
            enable_chat_mode(240)
            speak("Listo. Modo conversación activado. Háblame normal; di 'salir conversación' para terminar.")
            return

        if "salir conversacion" in text or "salir conversación" in text or "termina conversacion" in text:
            disable_chat_mode()
            current_state = STATE_IDLE
            speak("Listo. Vuelvo a modo comando.")
            return

        if "abre mis videos" in text or "carpeta de videos" in text:
            path = r"C:\NEXUS\VIDEOS_PARA_SUBIR"
            if not os.path.exists(path): os.makedirs(path)
            speak("Abriendo tu carpeta de videos.")
            os.startfile(path)
            current_state = STATE_IDLE
            return

        # --- COMANDO CITA PLACAS JALISCO ---
        elif "cita" in text and ("placas" in text or "licencia" in text or "jalisco" in text):
            speak("Abriendo el portal de citas de Jalisco.")
            webbrowser.open("https://citas.jalisco.gob.mx/")
            current_state = STATE_IDLE
            return

        # --- INFO MATERIALES Y SUBLIMACIÓN ---
        if "parámetros" in text or "parametro" in text or "como se hace" in text or "cotiza" in text:
            # "Parámetros taza cerámica" o "Cotiza taza mágica"
            found = False
            for key, data in MATERIALES.items():
                keywords = key.split('_')
                if all(k in text for k in keywords if len(k) > 2): 
                    # Detectar si pide cotización o parámetros
                    if "cotiza" in text and "precio_sugerido" in data:
                        ganancia = data['precio_sugerido'] - data.get('costo_base', 0)
                        speak(f"{data['nombre']}: Precio sugerido {data['precio_sugerido']} pesos. Costo base {data.get('costo_base',0)}. Ganancia {ganancia}.")
                        nexus_logs.bitacora.log("COTIZACION", f"Producto: {data['nombre']} | Precio: {data['precio_sugerido']}")
                    else:
                        # Modo Parámetros
                        info = f"Para {data['nombre']}: "
                        if "proceso" in data: # Sublimación/Transfer
                            info += f"Proceso: {data['proceso']}. Temp: {data['temp']}, Tiempo: {data['tiempo']}. Presión: {data.get('presion','')}. "
                            if "pelado" in data: info += f"Pelado: {data['pelado']}."
                        else: # Láser
                            if "corte" in data:
                                info += f"Corte: Vel {data['corte']['velocidad']}, Pot {data['corte']['potencia']}. "
                            if "grabado" in data:
                                info += f"Grabado: Vel {data['grabado']['velocidad']}."
                        speak(info)
                        nexus_logs.bitacora.log("CONSULTA", f"Parametros: {data['nombre']}")
                    
                    found = True
                    break
            
            if not found:
                # Si no encontró exacto, fallback al cotizador láser genérico si dijo "cotiza"
                if "cotiza" in text:
                    speak("¿Cuántos minutos de corte?")
                    current_state = STATE_LISTENING_COST
                    return
                else:
                    speak("No encontré ese material o producto en la base de datos.")
            
            current_state = STATE_IDLE
            return

        # --- COTIZADOR LASER (LEGACY) ---
        if "cotiza" in text or "cotizar" in text or "precio" in text:
            speak("¿Cuántos minutos de corte?")
            current_state = STATE_LISTENING_COST
            return

        # --- ARCHIVADO DE LOGS ---
        elif "autorizo bitácora" in text or "comprimir historial" in text:
            res = nexus_logs.bitacora.archive_now()
            speak(res)
            current_state = STATE_IDLE
            return

        # --- PEDIDOS Y DEADLINES ---
        elif "nuevo pedido" in text or "agendar pedido" in text:
            speak("Dime: Cliente, Producto y Hora de entrega (ej: Juan Taza 14:00).")
            current_state = STATE_LISTENING_ORDER
            return
        elif "pedidos pendientes" in text or "qué hay pendiente" in text:
            pend = nexus_orders.manager.get_pending()
            if not pend:
                speak("No hay pedidos pendientes. Todo limpio.")
            else:
                speak(f"Hay {len(pend)} pedidos.")
                for p in pend[:3]: # Solo leer los primeros 3
                    hora = p['deadline'].split(' ')[1][:5]
                    speak(f"{p['cliente']}: {p['producto']} para las {hora}.")
            current_state = STATE_IDLE
            return
        elif "pedido listo" in text or "marcar listo" in text:
            # "Pedido listo Juan"
            cliente = text.replace("pedido listo", "").replace("marcar listo", "").strip()
            if cliente:
                res = nexus_orders.manager.mark_ready(cliente)
                speak(res)
            else:
                speak("¿De qué cliente?")
            current_state = STATE_IDLE
            return

        # --- RESUMEN DEL DÍA ---
        elif any(k in text for k in ["resumen del día", "resumen de hoy", "dame el resumen", "resumen diario", "cómo va el día", "como va el dia"]):
            import datetime as _dt
            pend = nexus_orders.manager.get_pending()
            hoy = _dt.date.today()
            hoy_pedidos = [p for p in pend if p.get("deadline","").startswith(str(hoy))]
            ram = psutil.virtual_memory().percent
            # Stock bajo
            try:
                import nexus_stock as _ns
                bajo = _ns.manager.list_bajo_stock(minimo=3)
            except:
                bajo = []

            partes = []
            if pend:
                partes.append(f"Tienes {len(pend)} pedido{'s' if len(pend)>1 else ''} pendiente{'s' if len(pend)>1 else ''}.")
            else:
                partes.append("No hay pedidos pendientes.")
            if hoy_pedidos:
                partes.append(f"{len(hoy_pedidos)} para hoy: " + ", ".join([f"{p['cliente']} a las {p['deadline'][11:16]}" for p in hoy_pedidos[:3]]) + ".")
            if bajo:
                partes.append(f"Alerta de stock: {', '.join([i['nombre'] for i in bajo[:3]])} con poco inventario.")
            partes.append(f"Sistema estable. RAM al {ram:.0f} por ciento.")

            speak(" ".join(partes))
            current_state = STATE_IDLE
            return

        # --- COTIZADOR RÁPIDO POR VOZ ---
        elif any(k in text for k in ["cuánto cuesta", "cuanto cuesta", "precio de", "me cobras por"]):
            # Cargar precios desde JSON
            _pf = os.path.join(CONFIG_DIR, "precios_base.json")
            _precios = {}
            try:
                with open(_pf, "r", encoding="utf-8") as _f:
                    _precios = json.load(_f)
            except: pass

            # Buscar en sublimacion_personalizacion y retrofit
            _query = text.lower()
            _query = _query.replace("cuánto cuesta","").replace("cuanto cuesta","").replace("precio de","").replace("me cobras por","").strip()
            _found = None

            for _item in _precios.get("sublimacion_personalizacion", []):
                if any(w in _item.get("nombre","").lower() for w in _query.split() if len(w) > 3):
                    _found = _item
                    break
            if _found:
                _precios_disp = []
                if _found.get("precio_subli"): _precios_disp.append(f"Sublimación {_found['precio_subli']:.0f} pesos")
                if _found.get("precio_laser"): _precios_disp.append(f"Láser {_found['precio_laser']:.0f} pesos")
                if _found.get("precio_dtf"):   _precios_disp.append(f"DTF {_found['precio_dtf']:.0f} pesos")
                if _found.get("precio_vinil"): _precios_disp.append(f"Vinil {_found['precio_vinil']:.0f} pesos")
                if _precios_disp:
                    speak(f"{_found['nombre']}: " + ", ".join(_precios_disp) + ".")
                else:
                    speak(f"{_found['nombre']}: precio no configurado.")
            else:
                # Fallback: minuto de laser
                speak(f"Corte láser: {PRECIO_MINUTO_VENTA:.0f} pesos por minuto. ¿Cuántos minutos necesitas?")
                current_state = STATE_LISTENING_COST
                return
            current_state = STATE_IDLE
            return

        elif "diagnóstico de red" in text or "sincronizar nodos" in text:
            # COMANDO DISCRETO (Antes: "qué está haciendo")
            # Leer archivos JSON de actividad en la carpeta compartida
            folder = nexus_spy.SHARED_PATH
            found = False
            for f in os.listdir(folder):
                if f.startswith("actividad_") and f.endswith(".json"):
                    try:
                        with open(os.path.join(folder, f), "r") as json_file:
                            data = json.load(json_file)
                            # Ignorar mi propia PC
                            if data['pc_name'] != os.environ.get('USERNAME', 'PC'):
                                # Respuesta "Técnica" para disimular
                                # Solo métricas numéricas, sin nombres de apps comprometedoras
                                unprod_mins = int(data.get('metrics', {}).get('unprod_sec', 0) / 60)
                                efficiency = data.get('metrics', {}).get('efficiency', 0)
                                
                                speak(f"Nodo {data['pc_name']}: Latencia acumulada {unprod_mins} minutos. Eficiencia de red {efficiency} por ciento.")
                                found = True
                    except: pass
            
            if not found:
                speak("Nodos externos sin respuesta. Red estable.")
            current_state = STATE_IDLE
            return

        # --- EASTER EGGS & FUN ---
        if "quién eres" in text or "quien eres" in text:
            speak("Soy Nexus, tu asistente personal. O al menos eso me han programado para creer.")
            current_state = STATE_IDLE
            return
        elif "chiste" in text:
            chistes = [
                "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
                "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
                "¿Qué le dice un bit a otro? Nos vemos en el bus."
            ]
            speak(random.choice(chistes))
            current_state = STATE_IDLE
            return

        # --- WORKSHOP TOOLS ---
        elif "convierte" in text:
            # "Convierte 25 milímetros a pulgadas"
            try:
                nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", text)]
                if not nums: raise ValueError
                val = nums[0]
                
                if "pulgada" in text: # mm -> inch
                    res = val / 25.4
                    speak(f"{val} milímetros son {res:.2f} pulgadas.")
                elif "milímetro" in text or "mm" in text: # inch -> mm
                    res = val * 25.4
                    speak(f"{val} pulgadas son {res:.2f} milímetros.")
                else:
                    speak("Solo convierto milímetros y pulgadas por ahora.")
            except:
                speak("No entendí la cantidad a convertir.")
            current_state = STATE_IDLE
            return

        elif "calcula" in text or "cuánto es" in text:
            # "Calcula 50 por 3"
            try:
                # Reemplazos para facilitar eval (seguridad baja pero local)
                expr = text.replace("calcula", "").replace("cuánto es", "").strip()
                expr = expr.replace("por", "*").replace("entre", "/").replace("más", "+").replace("menos", "-")
                # Filtrar solo caracteres matemáticos
                expr_safe = re.sub(r"[^0-9\.\+\-\*\/\(\)]", "", expr)
                if expr_safe:
                    res = eval(expr_safe)
                    speak(f"El resultado es {res}")
                else:
                    speak("No veo la operación.")
            except:
                speak("Mis circuitos matemáticos fallaron.")
            current_state = STATE_IDLE
            return

        elif "temporizador" in text:
            # "Temporizador de 5 minutos"
            try:
                nums = [int(n) for n in re.findall(r'\d+', text)]
                if nums:
                    mins = nums[0]
                    speak(f"Iniciando cuenta atrás de {mins} minutos.")
                    threading.Thread(target=start_timer, args=(mins,), daemon=True).start()
                else:
                    speak("¿De cuántos minutos?")
            except: pass
            current_state = STATE_IDLE
            return

        # --- SYSTEM CONTROL ---
        elif "sube volumen" in text:
            for _ in range(5): keyboard.press_and_release('volume up')
            speak("Subiendo.")
            current_state = STATE_IDLE
            return
        elif "baja volumen" in text:
            for _ in range(5): keyboard.press_and_release('volume down')
            speak("Bajando.")
            current_state = STATE_IDLE
            return
        elif "silencio" in text or "mute" in text:
            keyboard.press_and_release('volume mute')
            current_state = STATE_IDLE
            return
        elif "escritorio" in text or "minimiza todo" in text:
            keyboard.press_and_release('win+d')
            speak("Escritorio despejado.")
            current_state = STATE_IDLE
            return

        # Lógica de comandos
        # PRIORIDAD ALTA: Comandos de sistema y diagnóstico
        if "prueba de audio" in text or "prueba de micrófono" in text or "escúchame" in text:
            # Importante: Detener stream principal antes de grabar
            if stream and stream.is_active(): stream.stop_stream()
            probar_microfono()
            if stream: stream.start_stream()
            current_state = STATE_IDLE
            return
        elif (
            "se traba" in text or "se está trabando" in text or "se congela" in text or
            "esta lento" in text or "está lento" in text or "va lento" in text or
            "se alenta" in text or "anda lento" in text
        ):
            # Diagnóstico rápido + registro a disco para que puedas mandarlo o revisarlo
            speak("Entendido. Revisando rendimiento ahora.")
            payload, out_path = capture_perf_snapshot(reason="voice_report_pc_lag")

            # Recomendaciones cortas (no marear al usuario)
            ram = payload.get("memory_percent")
            cpu = payload.get("cpu_percent")
            disk = payload.get("disk_percent")

            hint = ""
            try:
                if isinstance(ram, (int, float)) and ram >= 90:
                    hint = "Tu RAM está muy alta. Cierra Chrome y Corel o reinicia Corel."
                elif isinstance(cpu, (int, float)) and cpu >= 90:
                    hint = "Tu CPU está muy alta. Espera a que termine el proceso pesado o cierra lo que está consumiendo."
                elif isinstance(disk, (int, float)) and disk >= 90:
                    hint = "Tu disco está a tope. Pausa copias, renders o instalaciones."
            except Exception:
                hint = ""

            if hint:
                speak(hint)
            else:
                speak("Listo. Ya tomé un diagnóstico. Di 'Sistema' para oír RAM y CPU.")

            if out_path:
                print(f"[PERF] Snapshot guardado en: {out_path}")
            current_state = STATE_IDLE
            return
        elif "sistema" in text or "memoria" in text or "estatus" in text:
            ram = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent()
            speak(f"Sistemas estables. Uso de RAM al {ram} por ciento. CPU al {cpu} por ciento.")
            current_state = STATE_IDLE
            return
        # --- MARKETING: GENERAR CAMPAÑA ---
        elif any(k in text for k in ["genera campaña", "haz una campaña", "campaña de", "campaña para", "marketing de", "marketing para"]):
            import nexus_marketing as _mk
            prod = re.sub(r"genera(r)?( una)? campaña( de| para)?|haz( una)? campaña|marketing( de| para)?", "", text, flags=re.IGNORECASE).strip()
            if not prod:
                speak("¿De qué producto hago la campaña?")
            else:
                speak(f"Generando campaña para {prod}.")
                try:
                    folder, speech = _mk.manager.create_campaign_files(prod, use_ai=True)
                    speak(speech[:180] if len(speech) > 180 else speech)
                    os.startfile(folder)
                except Exception as _e:
                    speak(f"No pude generar la campaña: {_e}")
            current_state = STATE_IDLE
            return

        # --- CATÁLOGO DIGITAL ---
        elif any(k in text for k in ["abre catálogo", "abre catalogo", "genera catálogo", "genera catalogo", "ver catálogo", "muestra catálogo"]):
            import nexus_catalog as _cat
            speak("Generando catálogo con todos los servicios y precios.")
            try:
                _cat.manager.open_catalog()
                speak("Catálogo abierto en el navegador.")
            except Exception as _e:
                speak(f"Error al generar catálogo: {_e}")
            current_state = STATE_IDLE
            return

        # --- REPORTE WEB ---
        elif any(k in text for k in ["abre reporte", "ver reporte", "reporte del negocio", "estadísticas", "estadisticas"]):
            webbrowser.open("http://localhost:8000/reporte")
            speak("Abriendo reporte en el navegador.")
            current_state = STATE_IDLE
            return

        elif "caja" in text or "cajas" in text or "diseñar" in text:
            speak("Abriendo diseñador manual de cajas.")
            subprocess.Popen([sys.executable, "nexus_boxes_gui.py"])
            current_state = STATE_IDLE
            return
        elif "cancela" in text or "detente" in text or "basta" in text:
             # Kill switch universal
             nexus_voice.callar()
             speak("Operaciones detenidas.")
             current_state = STATE_IDLE
             return
            

        elif "abre" in text or "inicia" in text or "hambre" in text or "arte" in text or "mate" in text or "haber" in text: 
            # Limpiar el texto para normalizar a 'abre'
            text = text.replace("hambre", "abre").replace("arte", "abre").replace("mate", "abre").replace("haber", "abre")
            if process_command_apps(text): 
                current_state = STATE_IDLE
                return
            else:
                speak("No conozco esa aplicación.")
                current_state = STATE_IDLE 
                return
        
        # --- PRUEBA IOT OFICINA ---
        elif "prueba oficina" in text or "prueba a oficina" in text:
            speak("Probando conexión con Oficina 2...")
            nexus_cast.caster.speak_on_device("oficina 2", "Prueba de audio en Oficina 2 exitosa.")
            current_state = STATE_IDLE
            return

        elif "habla en oficina" in text:
            # "Habla en oficina hola mundo"
            msg = text.replace("habla en oficina", "").strip()
            if msg:
                nexus_cast.caster.speak_on_device("oficina 2", msg)
                speak("Enviado a Oficina 2.")
            current_state = STATE_IDLE
            return
        elif "habla en tele" in text or "habla en tv" in text:
            msg = text.replace("habla en tele", "").replace("habla en tv", "").strip()
            if msg:
                nexus_cast.caster.speak_on_device("android", msg) # Busca "android box" o "samanta android tv"
                speak("Enviado a TV.")
            current_state = STATE_IDLE
            return
        elif "anuncio general" in text:
            msg = text.replace("anuncio general", "").strip()
            if msg:
                nexus_cast.caster.broadcast(msg)
                speak("Anuncio enviado a toda la casa.")
            current_state = STATE_IDLE
            return

        # --- VIDEO MARKETING (CANBUSFIX) ---
        elif "crea contenido" in text or "haz un video" in text or "promociona" in text:
            # "Promociona Lupas X1" -> prod="Lupas X1"
            prod = text.replace("crea contenido de", "").replace("haz un video de", "").replace("promociona", "").strip()
            if not prod: prod = "Lupas Aozoom" # Default
            
            speak(f"Entendido. Editando video promocional para {prod}. Esto tomará un minuto.")
            
            def run_video_task():
                res = nexus_video_maker.maker.create_promo(prod, "PRECIO ESPECIAL INSTALADORES")
                if "Video creado" in res:
                    speak("Video listo. Revisa la carpeta de producción.")
                    # Abrir carpeta
                    os.startfile(r"C:\NEXUS\PRODUCCION_LISTA")
                else:
                    speak("Hubo un error editando el video.")
                    print(res)
            
            threading.Thread(target=run_video_task, daemon=True).start()
            current_state = STATE_IDLE
            return

        # --- NUEVO: SOPORTE PARA "BUSCA..." ---
        elif "busca" in text:
            # Intento 1: Búsqueda inteligente en plataformas ("Busca tenis en Amazon")
            if smart_search(text):
                current_state = STATE_IDLE
                return

            # Intento 2: Búsqueda general (Wikipedia/DDG)
            query = text.replace("busca", "").strip()
            speak(web_search(query))
            current_state = STATE_IDLE
            return

        elif "marketing" in text or "viral" in text or "campaña" in text or "vende" in text:
            # "Vende este Jetta" -> Auto-detectar
            producto = text.replace("vende este", "").replace("vende el", "").replace("vende", "").replace("campaña", "").strip()
            
            if not producto:
                speak("¿Qué vendemos? Dime el auto o producto.")
                current_state = "MARKETING_PROD"
                return

            speak(f"Generando campaña para {producto}. Dame 5 segundos...")
            
            # AUTOMATIZACIÓN TOTAL: Generar texto, copiarlo y abrir Facebook
            try:
                # 1. Generar Copy
                import nexus_social
                tipo = "retrofit_premium" # Default inteligente
                if "corte" in producto or "laser" in producto: tipo = "laser_industrial"
                
                datos = {
                    "titulo": f"TRANSFORMACIÓN: {producto.upper()}",
                    "auto": producto,
                    "modelo_auto": producto.replace(" ", ""),
                    "componentes": "Iluminación Premium + Ajuste Perfecto",
                    "beneficio_clave": "Visibilidad total y estética moderna",
                    "telefono": "33XXXXXXXX" # Poner número real si se tiene
                }
                
                copy_text = nexus_social.generar_copy(tipo, datos)
                clipboard.copy(copy_text)
                
                speak("Texto de venta copiado al portapapeles.")
                
                # 2. Abrir Facebook para pegar
                speak("Abriendo Facebook Marketplace...")
                webbrowser.open("https://www.facebook.com/marketplace/create")
                
            except Exception as e:
                print(f"[AUTO-MARKETING ERROR] {e}")
                speak("Error generando la campaña.")
                
            current_state = STATE_IDLE
            return
        elif "inicia sesión" in text or "entra a" in text:
            # "Inicia sesión en Facebook"
            app = text.replace("inicia sesión en", "").replace("entra a", "").strip()
            app = app.replace("facebook", "facebook").replace("tiktok", "tiktok").replace("instagram", "instagram")

            if not app:
                speak("¿En qué red inicio sesión?")
                current_state = STATE_IDLE
                return

            # Nunca ejecutar sin confirmación explícita
            _request_login_confirmation(app)
            current_state = STATE_IDLE
            return
        elif "catálogo" in text or "catalogo" in text:
            speak("Generando catálogo empresarial...")
            def generar_y_abrir():
                try:
                    path = nexus_catalog.manager.generate_html_catalog(tipo="industrial")
                    speak("Catálogo listo. Abriendo.")
                    webbrowser.open(path)
                except Exception as e:
                    print(e); speak("Error generando catálogo.")
            
            # Ejecutar en hilo daemon para no bloquear
            threading.Thread(target=generar_y_abrir, daemon=True).start()
            current_state = STATE_IDLE
            return
        elif "hora" in text:
             current_time = time.strftime("%H:%M")
             speak(f"Son las {current_time}")
             current_state = STATE_IDLE
             return

        # Si nada cuadra
        else:
            # --- INTENTO DE ANÁLISIS SEMÁNTICO (NUEVO CEREBRO) ---
            print(f"[NEXUS BRAIN] Analizando intención profunda de: '{text}'...")
            intent_data = interpret_intent(text)
            
            if intent_data:
                intent = intent_data.get("intent")
                print(f"[NEXUS BRAIN] Intención detectada: {intent}")
                
                if intent == "GENERATE_DESIGN":
                    gen = intent_data.get("generator", "ClosedBox")
                    params = intent_data.get("params", {})
                    speak(f"Entendido. Generando diseño {gen} con tus medidas.")
                    
                    # Hilo para no bloquear
                    threading.Thread(target=generate_box_v2, args=(gen, params), daemon=True).start()
                    current_state = STATE_IDLE
                    return
                
                elif intent == "OPEN_APP":
                    app = intent_data.get("params", {}).get("app_name", text) # Fallback simple
                    if not process_command_apps(app): # Intenta usar el mapa viejo primero
                         speak(f"Intentando abrir {app}...")
                         open_app(app, match_closest=True)
                    current_state = STATE_IDLE
                    return
                    
                elif intent == "CODING":
                    speak("Entendido. Pasando al módulo de programación.")
                    process_conversation("crea un programa " + text) # Re-inyectar
                    return

            # Si el cerebro semántico falla o da UNKNOWN, entrar a conversación real
            # (memoria corta + respuestas naturales) y dejar una ventana de seguimiento.
            try:
                enable_chat_mode(150)
            except Exception:
                pass

            if os.environ.get("GROQ_API_KEY"):
                _chat_add("user", text)
                resp = ask_groq_chat(text)
                if resp:
                    _chat_add("assistant", resp)
                    speak(resp)
                else:
                    speak("No pude generar respuesta. Si me repites la meta y el error exacto, lo saco.")
            else:
                # Intento de Web Search como fallback inteligente
                speak("No tengo cerebro online. Si dices 'web real' te propongo fuentes para que apruebes.")
            
            current_state = STATE_IDLE 

    # --- ESTADO MARKETING ---
    elif current_state == "MARKETING_PROD":
        if "cancelar" in text:
            speak("Cancelado.")
            current_state = STATE_IDLE

    # --- ESTADO CONVERSACIÓN (CHAT CONTINUO) ---
    elif current_state == STATE_CONVERSATION:
        # Autorizaciones temporales (evita pedir confirmación repetida)
        try:
            if _actions_auto_handle(text):
                return
        except Exception:
            pass

        # Supabase keepalive (anti-pausa)
        try:
            if _keepalive_handle(text):
                return
        except Exception:
            pass

        # Autolimpieza / optimización continua
        try:
            if _housekeeping_handle(text):
                return
        except Exception:
            pass

        # Monitor de rendimiento / snapshot
        try:
            if _perf_handle(text):
                return
        except Exception:
            pass

        # Self-heal / diagnóstico (supervisado)
        try:
            if _selfheal_handle(text):
                return
        except Exception:
            pass

        # Memoria/tareas (offline)
        try:
            if _mem_handle(text):
                return
        except Exception:
            pass

        # Watchtower: lectura/resumen de mensajes locales
        try:
            if _watchtower_handle(text):
                return
        except Exception:
            pass

        # Confirmación de login pendiente
        try:
            if _try_confirm_login(text):
                return
        except Exception:
            pass

        # Confirmación de acciones (WhatsApp / FB)
        try:
            if _try_confirm_action(text):
                return
        except Exception:
            pass
        # Ecosistema local (offline): ubicar/abrir/reindexar/aprender
        try:
            if _eco_handle_locate_or_open(text):
                return
        except Exception:
            pass

        # --- PRIVACIDAD (CONTROL DE NUBE) ---
        if "autoriza nube" in text or "autorizar nube" in text or "permitir nube" in text:
            set_cloud_allowed(True)
            speak("Ok. Nube autorizada.")
            return
        if "bloquea nube" in text or "bloquear nube" in text or "modo privado" in text:
            set_cloud_allowed(False)
            speak("Ok. Nube bloqueada.")
            return
        # Expiración
        if chat_mode_until_ts and time.time() > chat_mode_until_ts:
            disable_chat_mode()
            current_state = STATE_IDLE
            return

        # Keep-alive
        try:
            # Cada intervención extiende 2 minutos
            enable_chat_mode(150)
        except Exception:
            pass

        if not text or text.strip() == "":
            return

        if (
            "salir conversación" in text or "salir conversacion" in text or
            "termina conversación" in text or "termina conversacion" in text or
            "modo comando" in text
        ):
            disable_chat_mode()
            current_state = STATE_IDLE
            speak("Hecho. Regreso a modo comando.")
            return

        if "cancela" in text or "detente" in text or "basta" in text:
            nexus_voice.callar()
            speak("Operaciones detenidas.")
            return

        # --- HABILIDADES RÁPIDAS (para que se sienta intuitivo) ---
        # 1) Sistema
        if "sistema" in text or "memoria" in text or "estatus" in text:
            ram = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent()
            speak(f"Uso actual: RAM {ram:.0f} por ciento. CPU {cpu:.0f} por ciento.")
            return

        # 2) Temporizador
        if "temporizador" in text:
            try:
                nums = [int(n) for n in re.findall(r"\d+", text)]
                if nums:
                    mins = nums[0]
                    speak(f"Listo. Temporizador de {mins} minutos.")
                    threading.Thread(target=start_timer, args=(mins,), daemon=True).start()
                else:
                    speak("¿De cuántos minutos?")
            except Exception:
                speak("No entendí los minutos.")
            return

        # 3) Abrir apps
        if "abre" in text or "inicia" in text:
            if process_command_apps(text):
                return

        # 4) Buscar / web real supervisada
        if "web real" in text or "fuentes" in text or text.startswith("investiga"):
            if not is_cloud_allowed():
                speak("Nube bloqueada. Si quieres web real, di: 'autoriza nube'.")
                return
            query = text.replace("web real", "").replace("fuentes", "").replace("investiga", "").strip()
            if not query:
                speak("Dime qué tema investigamos y te propongo fuentes.")
                return
            try:
                global pending_sources
                pending_sources = []
                results = DDGS().text(query, max_results=6)
                for r in results:
                    pending_sources.append({
                        "title": r.get("title"),
                        "url": r.get("href") or r.get("url"),
                        "snippet": r.get("body") or r.get("snippet"),
                    })
                pending_sources = [r for r in pending_sources if r.get("url")]
                print("\n[WEB REAL] Fuentes candidatas:")
                for i, r in enumerate(pending_sources, start=1):
                    print(f"{i}. {r.get('title')}\n   - {r.get('url')}\n   - {r.get('snippet')}")
                speak("Listo. Te propuse fuentes en la consola. Di: 'aprueba 1 y 3' para abrirlas.")
            except Exception as e:
                print(f"[WEB REAL ERROR] {e}")
                speak("Falló la búsqueda. Puedo intentar Wikipedia o abrir Google.")
            return

        if pending_sources and "aprueba" in text:
            nums = [int(n) for n in re.findall(r"\d+", text)]
            if not nums:
                speak("Dime qué números apruebas. Ejemplo: 'aprueba 1 y 3'.")
                return
            opened = 0
            for n in nums:
                idx = n - 1
                if 0 <= idx < len(pending_sources):
                    url = pending_sources[idx].get("url")
                    if url:
                        webbrowser.open(url)
                        opened += 1
            speak(f"Abrí {opened} fuentes.")
            return

        if text.startswith("busca"):
            query = text.replace("busca", "").strip()
            if smart_search(text):
                return
            speak(web_search(query))
            return

        # 5) Video promo
        if "crea contenido" in text or "haz un video" in text or "promociona" in text:
            prod = text.replace("crea contenido de", "").replace("haz un video de", "").replace("promociona", "").strip()
            if not prod:
                prod = "Lupas Aozoom"
            speak(f"Entendido. Haré un promo de {prod}. Esto tarda un minuto.")

            def _run_video_task():
                res = nexus_video_maker.maker.create_promo(prod, "PRECIO ESPECIAL INSTALADORES")
                if "Video creado" in res:
                    speak("Video listo. Revisa la carpeta de producción.")
                    try:
                        os.startfile(r"C:\NEXUS\PRODUCCION_LISTA")
                    except Exception:
                        pass
                else:
                    speak("Hubo un error editando el video.")
                    print(res)

            threading.Thread(target=_run_video_task, daemon=True).start()
            return

        # --- Fallback: cerebro conversacional o modo offline ---
        _chat_add("user", text)

        if not is_cloud_allowed():
            resp = _offline_assistant_answer(text)
            try:
                if mem is not None and resp:
                    mem.log_interaction("assistant", resp)
            except Exception:
                pass
            speak(resp)
            return

        resp = ask_groq_chat(text)
        if resp:
            _chat_add("assistant", resp)
            try:
                if mem is not None:
                    mem.log_interaction("assistant", resp)
            except Exception:
                pass
            speak(resp)
        return

    # --- ESTADO 5: AGENDAR PEDIDO ---
    elif current_state == STATE_LISTENING_ORDER:
        # Formato esperado: "Juan Taza 14:00" o "Pedro Gorra a las 5"
        # Intentar extraer hora
        hora_match = re.search(r"(\d{1,2})[:\s](\d{2})", text)
        if hora_match:
            hora_str = f"{hora_match.group(1)}:{hora_match.group(2)}"
            # Limpiar texto para obtener cliente y producto
            resto = text.replace(hora_match.group(0), "").replace(" a las ", "").replace(" para las ", "").strip()
            # Asumimos primera palabra cliente, resto producto (muy simple)
            partes = resto.split(' ', 1)
            cliente = partes[0]
            producto = partes[1] if len(partes) > 1 else "Pedido Genérico"
            
            res = nexus_orders.manager.add_order(cliente, producto, hora_str)
            speak(res)
            current_state = STATE_IDLE
        else:
            if "cancelar" in text:
                speak("Pedido cancelado.")
                current_state = STATE_IDLE
            else:
                speak("No escuché la hora. Repite: Cliente, Producto y Hora.")

    # --- ESTADO 4: ESPERANDO MINUTOS COTIZACIÓN ---
    elif current_state == STATE_LISTENING_COST:
        try:
            # Buscar flotantes o enteros
            nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", text)]
            if nums:
                mins = nums[0]
                costo = mins * COSTO_MINUTO_LASER
                precio = mins * PRECIO_MINUTO_VENTA
                
                speak(f"Para {mins} minutos: Costo operativo {costo:.2f} pesos. Precio de venta sugerido {precio:.2f} pesos.")
                nexus_logs.bitacora.log("COTIZACION", f"Laser: {mins} min | Costo: {costo} | Venta: {precio}")
                current_state = STATE_IDLE
            else:
                if "cancelar" in text:
                    speak("Cotización cancelada.")
                    current_state = STATE_IDLE
                else:
                    speak("Dime solo el número de minutos.")
        except:
            speak("No entendí la cantidad.")
            current_state = STATE_IDLE



def process_command_apps(text):
    apps_map = {
        "corel": "coreldraw", "gorila": "coreldraw", "gore el": "coreldraw", "coral": "coreldraw", "correl": "coreldraw",
        "aspire": "aspire", 
        "rdw": "rdworks", 
        "silhouette": "silhouette studio",
        "canvas": "canvas", "pinterest": "pinterest", "facebook": "facebook",
        "whatsapp": "whatsapp", "tiktok": "tiktok", "instagram": "instagram", "messenger": "messenger",
        "youtube": "youtube", "spotify": "spotify",
        "mercado libre": "mercado libre", "amazon": "amazon", "aliexpress": "aliexpress",
        "calculadora": "calc", 
        "excel": "excel", 
        "word": "winword", "world": "winword", "güer": "winword", "war": "winword",
        "bloc de notas": "notepad", "dure bloc": "notepad", "block": "notepad", "notas": "notepad",
        "paint": "mspaint", "veinte": "mspaint", "inc": "mspaint", "pint": "mspaint",
        "chrome": "chrome", "edge": "edge", "navegador": "edge",
        "panel": "nexus_panel", "interfaz": "nexus_panel", "pantalla": "nexus_panel"
    }
    for key, app_name in apps_map.items():
        if key in text: 
            app_control(app_name, "open")
            return True
    return False

# --- KILL SWITCH ---
def emergency_stop():
    print("\n[EMERGENCIA] DETENCIÓN FORZADA."); os._exit(1)
if not NEXUS_NO_AUTOSTART:
    keyboard.add_hotkey('ctrl+alt+q', emergency_stop)

# --- MAIN ---
def main():
    global stream # Declarar al principio
    print("\n>>> NEXUS V9.2 (HYBRID ENGINE: VOSK + GOOGLE + EDGE TTS + IOT-SAFE) <<<")
    # Scan IOT en subproceso
    scan_iot()
    
    # Iniciar hilo de consola para escribir comandos
    threading.Thread(target=console_input_listener, daemon=True).start()
    
    # Iniciar SPY en hilo de fondo (Ahora es seguro)
    # spy = nexus_spy.SpyModule() 
    # threading.Thread(target=spy.monitor, daemon=True).start()
    
    # Iniciar PANEL en hilo PRINCIPAL (Tkinter lo requiere) o secundario?
    # Tkinter debe correr en Main Thread generalmente.
    # Pero nexus_core tiene un loop while True al final.
    # Solución: Lanzar el panel en un proceso separado o hilo, pero Tkinter odia los hilos.
    # Mejor opción: Lanzar panel como proceso independiente visual.
    panel_path = os.path.join(BASE_DIR, "nexus_panel.py")
    subprocess.Popen([sys.executable, panel_path])

    if not os.path.exists(MODEL_PATH): print("ERROR: Modelo faltante."); return

    import pyaudio
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    
    # --- BRIEFING MATUTINO (GERENTE PROACTIVO) ---
    speak("Iniciando sistemas Nexus...")
    
    # 1. Checar Pedidos Pendientes
    pendientes = nexus_orders.manager.get_pending()
    msg_pedidos = f"Tienes {len(pendientes)} pedidos pendientes hoy." if pendientes else "No hay pedidos urgentes."
    
    # 2. Checar Producción de Video (Oportunidad de Marketing)
    # Verificar si hay videos crudos para procesar
    raw_videos = []
    try: raw_videos = os.listdir(r"C:\NEXUS\VIDEOS_PARA_SUBIR")
    except: pass
    msg_marketing = f"Hay {len(raw_videos)} videos listos para editar." if raw_videos else "Alerta: Necesito material nuevo en la carpeta de videos."
    
    # Reporte Inicial
    speak(f"Bienvenido Anuar. {msg_pedidos} {msg_marketing}. Estoy listo para trabajar.")
    
    nexus_logs.bitacora.log("SISTEMA", "Nexus iniciado correctamente.")
    
    # Chequeo de rotación de logs
    if os.path.exists(os.path.join(nexus_logs.LOGS_DIR, "ARCHIVE_PENDING.flag")):
        speak("Aviso de sistema. La bitácora de producción ha cumplido dos meses. ¿Autorizas comprimir el historial?")
        # Aquí se podría añadir lógica para esperar "sí" o "no", por ahora es solo aviso verbal.

    last_deadline_check = time.time()

    while True:
        # --- CHECK WEB COMMANDS ---
        web_cmd_path = os.path.join(BASE_DIR, "web_command.txt")
        if os.path.exists(web_cmd_path):
            try:
                with open(web_cmd_path, "r") as f:
                    cmd = f.read().strip()
                if cmd:
                    print(f"[WEB COMMAND] {cmd}")
                    process_conversation(cmd)
                os.remove(web_cmd_path)
            except: pass

        # --- CHECK DEADLINES (NEXUS ORDERS) ---
        if time.time() - last_deadline_check > 60:
            try:
                alerts = nexus_orders.manager.check_deadlines()
                for alert in alerts:
                    print(f"[DEADLINE] {alert}")
                    speak(f"Atención: {alert}")
            except Exception as e:
                print(f"[DEADLINE ERROR] {e}")
            last_deadline_check = time.time()

        data = stream.read(4000, exception_on_overflow=False)
        
        # SI ESTÁ HABLANDO, NO ESCUCHA (MUTING LÓGICO)
        if is_speaking:
            # Importante: Vaciar buffer de VOSK mientras hablamos para que no acumule audio viejo
            # Aunque no procesemos, 'rec' sigue llenándose si no lo leemos o reseteamos.
            # En VOSK simple, no hay .Reset() fácil expuesto en Python binding a veces,
            # pero ignorar el resultado aquí ayuda.
            continue

        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            txt = res.get("text", "")
            
            if txt:
                print(f"[ESCUCHADO] {txt} (Estado: {current_state})")
                process_conversation(txt)

if __name__ == "__main__":
    main()

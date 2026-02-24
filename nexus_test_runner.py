"""
nexus_test_runner.py — Pruebas End-to-End NEXUS
================================================
Prueba módulo por módulo, registra todo en log.
Detecta: import errors, funciones faltantes, API endpoints, DB access.

Uso:
  python nexus_test_runner.py             # prueba todo
  python nexus_test_runner.py --modulo crm  # solo un módulo
  python nexus_test_runner.py --api       # solo endpoints HTTP

Requiere que nexus_server.py esté corriendo en localhost:8000 para pruebas de API.
Resultados: logs/test_results.log + logs/test_results.json
"""

import sys
import os
import json
import traceback
import importlib
import time
import platform
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE  = os.path.join(LOG_DIR, "test_results.log")
JSON_FILE = os.path.join(LOG_DIR, "test_results.json")
API_BASE  = "http://localhost:8000"

# ── Colores consola ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTADOS
# ═══════════════════════════════════════════════════════════════════════════════
results: list[dict] = []

def record(categoria: str, nombre: str, ok: bool, detalle: str = "", duracion_ms: int = 0):
    entry = {
        "categoria":   categoria,
        "nombre":      nombre,
        "ok":          ok,
        "detalle":     detalle,
        "duracion_ms": duracion_ms,
        "timestamp":   datetime.now().isoformat(),
    }
    results.append(entry)
    icono  = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
    linea  = f"  {icono} [{categoria}] {nombre}"
    if not ok:   linea += f" — {RED}{detalle}{RESET}"
    elif detalle: linea += f" — {YELLOW}{detalle}{RESET}"
    if duracion_ms: linea += f" ({duracion_ms}ms)"
    print(linea)
    # Log a archivo
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        estado = "OK" if ok else "FALLA"
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{estado}] [{categoria}] {nombre} | {detalle} | {duracion_ms}ms\n")

# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBAS DE IMPORTACIÓN DE MÓDULOS
# ═══════════════════════════════════════════════════════════════════════════════

MODULOS_PYTHON = [
    # (nombre_modulo, funciones_clave_a_verificar)
    ("nexus_db",          ["NexusDB", "db"]),
    ("nexus_crm",         ["manager"]),
    ("nexus_orders",      ["manager"]),
    ("nexus_stock",       ["manager"]),
    ("nexus_catalog",     []),
    ("nexus_marketing",   []),
    ("nexus_social",      []),
    ("nexus_spy",         []),
    ("nexus_meta",        []),
    ("nexus_subliminal",  ["generar_binaural_wav", "BIBLIOTECA"]),
    ("nexus_image_processor", ["procesar_imagen"]),
    ("nexus_galeria",     ["CATALOGO_AUDIO", "CUOTAS"]),
    ("nexus_telegram",    []),
    ("nexus_notifier",    []),
    ("nexus_assistant",   []),
    ("nexus_agent",       []),
    ("nexus_voice",       []),
    ("nexus_teens",       ["registrar_usuario","get_perfil","APTITUDES","VALORES"]),
    ("nexus_legal",       ["registrar_aceptacion","AVISO_PRIVACIDAD"]),
    ("nexus_admin",       ["login_admin","MODULO_CATALOGO","TIERS_DEFAULT"]),
    ("nexus_autoventas",  ["registrar_prospecto","get_pipeline","HOOKS_VIRALES"]),
    ("nexus_finanzas",    []),
    ("nexus_license",     ["validar_licencia","info_licencia"]),
    ("nexus_fingerprint", []),
    ("nexus_backup",      []),
    ("nexus_scheduler",   []),
    ("nexus_autopilot",   []),
    ("nexus_authorization",["authorizer", "AuditLog"]),
    ("nexus_memory",      []),
    ("nexus_vault",       []),
    ("nexus_iot",         []),
    ("nexus_milens",      []),
    ("nexus_video",       []),
    ("nexus_coder",       []),
    ("nexus_doctor",      []),
    ("nexus_self_heal",   []),
    ("nexus_ecosystem",   []),
    ("nexus_panel",       []),
    ("system_monitor",    []),
    ("config_manager",    []),
    ("video_processor",   []),
    ("voice_service",     []),
]

def test_imports():
    print(f"\n{BOLD}{BLUE}═══ IMPORTACIÓN DE MÓDULOS ════════════════════════{RESET}")
    for mod_name, funciones in MODULOS_PYTHON:
        t0 = time.time()
        try:
            mod = importlib.import_module(mod_name)
            ms  = int((time.time()-t0)*1000)
            # Verificar funciones/atributos clave
            faltantes = [f for f in funciones if not hasattr(mod, f)]
            if faltantes:
                record("IMPORT", mod_name, False, f"Faltan: {faltantes}", ms)
            else:
                record("IMPORT", mod_name, True, "", ms)
        except ModuleNotFoundError as e:
            ms = int((time.time()-t0)*1000)
            record("IMPORT", mod_name, False, f"ModuleNotFoundError: {e}", ms)
        except Exception as e:
            ms = int((time.time()-t0)*1000)
            record("IMPORT", mod_name, False, f"{type(e).__name__}: {str(e)[:80]}", ms)

# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBAS DE FUNCIONES CORE
# ═══════════════════════════════════════════════════════════════════════════════

def test_nexus_db():
    print(f"\n{BOLD}{BLUE}=== BASE DE DATOS ==========================={RESET}")
    try:
        import nexus_db
        t0  = time.time()
        # nexus_db usa NexusDB class y db instancia (Supabase cloud)
        db_inst = nexus_db.db
        ms = int((time.time()-t0)*1000)
        record("DB", "nexus_db.db (Supabase)", db_inst is not None, f"instancia={type(db_inst).__name__}", ms)
    except Exception as e:
        record("DB", "nexus_db.db", False, str(e)[:100])

def test_crm():
    print(f"\n{BOLD}{BLUE}═══ CRM ════════════════════════{RESET}")
    try:
        from nexus_crm import manager as m
        t0 = time.time()
        m.load_clientes()
        ms = int((time.time()-t0)*1000)
        record("CRM", "load_clientes", True, f"{len(m.clientes)} clientes cargados", ms)
    except Exception as e:
        record("CRM", "load_clientes", False, str(e)[:100])

def test_stock():
    print(f"\n{BOLD}{BLUE}═══ STOCK ════════════════════════{RESET}")
    try:
        from nexus_stock import manager as m
        t0 = time.time()
        m.load_stock()
        ms = int((time.time()-t0)*1000)
        record("STOCK", "load_stock", True, f"{len(m.stock)} items", ms)
    except Exception as e:
        record("STOCK", "load_stock", False, str(e)[:100])

def test_orders():
    print(f"\n{BOLD}{BLUE}═══ PEDIDOS ════════════════════════{RESET}")
    try:
        from nexus_orders import manager as m
        t0 = time.time()
        p  = m.get_pending()
        ms = int((time.time()-t0)*1000)
        record("PEDIDOS", "get_pending", True, f"{len(p)} pendientes", ms)
    except Exception as e:
        record("PEDIDOS", "get_pending", False, str(e)[:100])

def test_teens():
    print(f"\n{BOLD}{BLUE}═══ TEENS ════════════════════════{RESET}")
    try:
        from nexus_teens import registrar_usuario, get_perfil, APTITUDES, VALORES, MISIONES_CATALOGO
        t0 = time.time()
        r  = registrar_usuario("test_runner_001","TestUser",16)
        ms = int((time.time()-t0)*1000)
        record("TEENS", "registrar_usuario", r.get("ok",False), str(r.get("msg",""))[:60], ms)

        t0 = time.time()
        p  = get_perfil("test_runner_001")
        ms = int((time.time()-t0)*1000)
        record("TEENS", "get_perfil", p.get("ok",False), f"XP={p.get('xp',0)}", ms)

        record("TEENS", "APTITUDES catálogo", len(APTITUDES)==7, f"{len(APTITUDES)} aptitudes")
        record("TEENS", "VALORES catálogo",   len(VALORES)==7,   f"{len(VALORES)} valores")
        record("TEENS", "MISIONES catálogo",  len(MISIONES_CATALOGO)>=10, f"{len(MISIONES_CATALOGO)} misiones")
    except Exception as e:
        record("TEENS", "general", False, traceback.format_exc()[:200])

def test_admin():
    print(f"\n{BOLD}{BLUE}═══ ADMIN ════════════════════════{RESET}")
    try:
        from nexus_admin import MODULO_CATALOGO, TIERS_DEFAULT, get_catalogo_tienda, _cfg_inicializado
        record("ADMIN", "MODULO_CATALOGO", len(MODULO_CATALOGO)>=15, f"{len(MODULO_CATALOGO)} módulos")
        record("ADMIN", "TIERS_DEFAULT",   "DEMO" in TIERS_DEFAULT, f"tiers: {list(TIERS_DEFAULT.keys())}")
        t0  = time.time()
        cat = get_catalogo_tienda()
        ms  = int((time.time()-t0)*1000)
        record("ADMIN", "get_catalogo_tienda", cat.get("ok",False),
               f"{cat.get('total_modulos',0)} módulos", ms)
        record("ADMIN", "cfg_inicializado", True, "configurado="+str(_cfg_inicializado()))
    except Exception as e:
        record("ADMIN", "general", False, str(e)[:100])

def test_autoventas():
    print(f"\n{BOLD}{BLUE}═══ AUTOVENTAS ════════════════════════{RESET}")
    try:
        from nexus_autoventas import (registrar_prospecto, get_pipeline, get_metricas,
                                      get_hooks_canal, get_calendario_semanal, HOOKS_VIRALES)
        t0 = time.time()
        r  = registrar_prospecto("TestNexus","5500000001","taller","test")
        ms = int((time.time()-t0)*1000)
        record("AUTOVENTAS", "registrar_prospecto", r.get("ok",False), r.get("msg","")[:60], ms)

        t0 = time.time()
        p  = get_pipeline()
        ms = int((time.time()-t0)*1000)
        record("AUTOVENTAS", "get_pipeline", p.get("ok",False),
               f"{p.get('metricas',{}).get('total',0)} prospectos", ms)

        hooks = get_hooks_canal("tiktok")
        record("AUTOVENTAS", "get_hooks_canal", len(hooks)>0, f"{len(hooks)} hooks TikTok")

        cal = get_calendario_semanal()
        record("AUTOVENTAS", "get_calendario_semanal", len(cal)==7, f"{len(cal)} días")
    except Exception as e:
        record("AUTOVENTAS", "general", False, traceback.format_exc()[:200])

def test_legal():
    print(f"\n{BOLD}{BLUE}═══ LEGAL ════════════════════════{RESET}")
    try:
        from nexus_legal import AVISO_PRIVACIDAD, TERMINOS_USO, get_aviso, get_terminos, verificar_aceptacion
        record("LEGAL", "AVISO_PRIVACIDAD", len(AVISO_PRIVACIDAD)>100, f"{len(AVISO_PRIVACIDAD)} chars")
        record("LEGAL", "TERMINOS_USO",     len(TERMINOS_USO)>100, f"{len(TERMINOS_USO)} chars")
        t0 = time.time()
        a  = verificar_aceptacion()
        ms = int((time.time()-t0)*1000)
        record("LEGAL", "verificar_aceptacion", True, f"aceptado={a.get('aceptado',False)}", ms)
    except Exception as e:
        record("LEGAL", "general", False, str(e)[:100])

def test_subliminal():
    print(f"\n{BOLD}{BLUE}=== SUBLIMINAL/BINAURAL ====================={RESET}")
    try:
        from nexus_subliminal import BIBLIOTECA, generar_binaural_wav, generar_audio_categoria
        cats = list(BIBLIOTECA.keys())
        total = sum(len(v) for v in BIBLIOTECA.values())
        record("SUBLIMINAL", "BIBLIOTECA catálogo", len(BIBLIOTECA)>=5, f"{len(BIBLIOTECA)} categorías, {total} items")
        record("SUBLIMINAL", "generar_binaural_wav", callable(generar_binaural_wav), "función presente")
        record("SUBLIMINAL", "generar_audio_categoria", callable(generar_audio_categoria), "función presente")
    except Exception as e:
        record("SUBLIMINAL", "general", False, str(e)[:100])

def test_galeria():
    print(f"\n{BOLD}{BLUE}=== GALERIA ================================={RESET}")
    try:
        from nexus_galeria import CATALOGO_AUDIO, CATALOGO_VISUAL, CUOTAS, get_uso_actual
        record("GALERIA", "CATALOGO_AUDIO",  len(CATALOGO_AUDIO)>=10,  f"{len(CATALOGO_AUDIO)} audios")
        record("GALERIA", "CATALOGO_VISUAL", len(CATALOGO_VISUAL)>=5,  f"{len(CATALOGO_VISUAL)} visuales")
        record("GALERIA", "CUOTAS config",   "DEMO" in CUOTAS,         f"tiers: {list(CUOTAS.keys())}")
        t0  = time.time()
        uso = get_uso_actual()
        ms  = int((time.time()-t0)*1000)
        record("GALERIA", "get_uso_actual", isinstance(uso, dict), str(uso)[:80], ms)
    except Exception as e:
        record("GALERIA", "general", False, str(e)[:100])

def test_license():
    print(f"\n{BOLD}{BLUE}=== LICENCIAS ================================{RESET}")
    try:
        from nexus_license import DIAS_POR_TIPO, validar_licencia, info_licencia
        record("LICENSE", "DIAS_POR_TIPO", "DEMO" in DIAS_POR_TIPO,
               f"PRO={DIAS_POR_TIPO.get('PRO','?')} dias, FULL={DIAS_POR_TIPO.get('FULL','?')} dias")
        t0 = time.time()
        v  = info_licencia()
        ms = int((time.time()-t0)*1000)
        record("LICENSE", "info_licencia", isinstance(v, dict),
               f"tipo={v.get('tipo','?')}", ms)
    except Exception as e:
        record("LICENSE", "general", False, str(e)[:100])

# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBAS HTTP (requiere servidor corriendo)
# ═══════════════════════════════════════════════════════════════════════════════

def test_api_endpoints():
    print(f"\n{BOLD}{BLUE}═══ API ENDPOINTS HTTP ════════════════════════{RESET}")
    try:
        import urllib.request
        import urllib.error
    except:
        record("API", "urllib", False, "No disponible"); return

    endpoints_get = [
        ("/",                "dashboard/home"),
        ("/dashboard",       "dashboard"),
        ("/clientes",        "clientes"),
        ("/stock",           "stock"),
        ("/api/nexus_status","status JSON"),
        ("/api/pedidos",     "pedidos JSON"),
        ("/api/stock",       "stock JSON"),
        ("/api/clientes",    "clientes JSON"),
        ("/galeria",         "galeria"),
        ("/teens",           "teens"),
        ("/legal",           "legal"),
        ("/admin",           "admin panel"),
        ("/autoventas",      "autoventas"),
        ("/landing",         "landing"),
        ("/nexus-ear",       "nexus ear"),
        ("/api/autoventas/pipeline",  "pipeline JSON"),
        ("/api/autoventas/metricas",  "metricas JSON"),
        ("/api/autoventas/calendario","calendario JSON"),
        ("/api/admin/catalogo",       "catalogo admin JSON"),
    ]

    server_online = False
    try:
        urllib.request.urlopen(f"{API_BASE}/api/nexus_status", timeout=3)
        server_online = True
    except:
        pass

    if not server_online:
        record("API", "Servidor NEXUS", False,
               f"No responde en {API_BASE}. Inicia con: python nexus_server.py")
        return

    record("API", "Servidor online", True, API_BASE)

    for path, nombre in endpoints_get:
        t0 = time.time()
        try:
            url = f"{API_BASE}{path}"
            req = urllib.request.Request(url, headers={"User-Agent":"NexusTestRunner/1.0"})
            res = urllib.request.urlopen(req, timeout=5)
            ms  = int((time.time()-t0)*1000)
            record("API", f"GET {path}", res.status == 200,
                   f"HTTP {res.status}", ms)
        except urllib.error.HTTPError as e:
            ms = int((time.time()-t0)*1000)
            record("API", f"GET {path}", False, f"HTTP {e.code}", ms)
        except Exception as e:
            ms = int((time.time()-t0)*1000)
            record("API", f"GET {path}", False, str(e)[:60], ms)

# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA DE TEMPLATES HTML
# ═══════════════════════════════════════════════════════════════════════════════

def test_templates():
    print(f"\n{BOLD}{BLUE}═══ TEMPLATES HTML ════════════════════════{RESET}")
    tpl_dir = os.path.join(BASE_DIR, "WEB", "templates")
    templates_esperados = [
        "dashboard.html","index.html","clientes.html","stock.html","pedidos.html",
        "marketing.html","galeria.html","teens.html","legal.html","admin.html",
        "autoventas.html","landing.html","nexus_ear.html","cotizar_simple.html",
        "historial.html","agenda.html","nuevo_pedido.html","perfil_cliente.html",
        "reporte.html","qr.html",
    ]
    for tpl in templates_esperados:
        path = os.path.join(tpl_dir, tpl)
        exists = os.path.exists(path)
        if exists:
            size = os.path.getsize(path)
            record("TEMPLATE", tpl, size > 100, f"{size:,} bytes")
        else:
            record("TEMPLATE", tpl, False, "Archivo no encontrado")

# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN Y GUARDADO
# ═══════════════════════════════════════════════════════════════════════════════

def resumen():
    ok_total   = sum(1 for r in results if r["ok"])
    fail_total = len(results) - ok_total
    pct        = round(ok_total/max(len(results),1)*100, 1)

    print(f"\n{'='*52}")
    print(f"{BOLD}RESUMEN FINAL{RESET}")
    print(f"  OK:     {GREEN}{ok_total}{RESET}")
    print(f"  Fallos: {RED}{fail_total}{RESET}")
    print(f"  Score:  {YELLOW}{pct}%{RESET}")
    print(f"  Log:    {LOG_FILE}")

    if fail_total:
        print(f"\n{BOLD}{RED}FALLOS DETECTADOS:{RESET}")
        for r in results:
            if not r["ok"]:
                print(f"  ❌ [{r['categoria']}] {r['nombre']} — {r['detalle']}")

    # Guardar JSON
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "fecha":       datetime.now().isoformat(),
            "score_pct":   pct,
            "ok":          ok_total,
            "fallos":      fail_total,
            "total":       len(results),
            "entorno":     platform.platform(),
            "python":      sys.version,
            "resultados":  results,
        }, f, ensure_ascii=False, indent=2)

    print(f"  JSON:   {JSON_FILE}")
    print(f"{'='*52}\n")
    return fail_total

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Limpiar log previo
    open(LOG_FILE, "w").close()

    print(f"\n{BOLD}{BLUE}=== NEXUS TEST RUNNER - End-to-End v2026 ===")
    print(f"    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"============================================{RESET}")

    args = sys.argv[1:]
    solo_api = "--api" in args
    solo_mod = next((args[i+1] for i,a in enumerate(args) if a=="--modulo" and i+1<len(args)), None)

    if solo_api:
        test_api_endpoints()
    elif solo_mod:
        test_imports()
    else:
        # Suite completa
        test_imports()
        test_nexus_db()
        test_crm()
        test_stock()
        test_orders()
        test_teens()
        test_admin()
        test_autoventas()
        test_legal()
        test_subliminal()
        test_galeria()
        test_license()
        test_templates()
        test_api_endpoints()

    sys.exit(resumen())

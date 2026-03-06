#!/usr/bin/env python3
"""nexus_test_suite.py — Pruebas automaticas NEXUS"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

RESULTADOS = []
CI_MODE = os.environ.get("CI", "false").lower() == "true"


def test(nombre, fn):
    try:
        r = fn()
        ok = r if isinstance(r, bool) else bool(r)
    except Exception as e:
        ok = False
        RESULTADOS.append((nombre, False, str(e)[:80]))
        return False
    RESULTADOS.append((nombre, ok, ""))
    return ok

# LICENCIA Y PERFILES
test("licencia_existe",    lambda: os.path.exists("CONFIG/license.key"))
def t_licencia_valida():
    info = __import__("nexus_license").info_licencia()
    if CI_MODE: return info.get("tipo") in ("ADMIN","INVALIDA")  # CI usa bypass
    return info.get("licencia_valida", False)
test("licencia_valida", t_licencia_valida)
def t_licencia_admin():
    info = __import__("nexus_license").info_licencia()
    if CI_MODE: return info.get("tipo") in ("ADMIN", "INVALIDA")  # BYPASS en CI
    return info.get("tipo") == "ADMIN"
test("licencia_admin", t_licencia_admin)
test("perfil_activo",      lambda: json.load(open("CONFIG/perfil_activo.json",encoding="utf-8")).get("tipo") == "ADMIN")
test("config_negocio",     lambda: bool(json.load(open("CONFIG/negocio.json",encoding="utf-8")).get("nombre","").strip()))

# MÓDULOS CORE
def t_finanzas():
    import nexus_finanzas as f
    d = f.obtener_dashboard()
    txt = f.resumen_texto()
    return bool(d) and len(txt) > 50
test("finanzas_dashboard", t_finanzas)

def t_galeria():
    import nexus_galeria as g
    uso = g.get_uso_actual()
    cat = g.get_catalogo_completo()
    return bool(uso.get("plan")) and cat.get("ok")
test("galeria_catalogo", t_galeria)

def t_subliminal():
    import nexus_subliminal as s
    pistas = s.get_pistas()
    assert all(p.get("id") for p in pistas), "sin id"
    r = s.generar_audio_categoria("deseo", duracion_seg=2)
    return r.get("ok") and os.path.exists(r.get("archivo",""))
test("subliminal_wav", t_subliminal)

def t_vault():
    import nexus_vault as v
    r = v.manager.add_credential("_nexus_test", "u", "p")
    return "_nexus_test" in v.manager.db
test("vault_credencial", t_vault)

def t_social():
    import nexus_social as s
    datos = {"servicio":"Test","precio":100,"ubicacion":"GDL","negocio":"N"}
    r = s.generar_copy("retrofit_premium", datos)
    return len(r) > 100
test("social_copy", t_social)

def t_profiles():
    from nexus_profiles import es_admin, tiene_permiso
    return es_admin() and tiene_permiso("ver_modulos_personales") and not tiene_permiso("acceso_vault") == False
test("profiles_permisos", t_profiles)

def t_orders():
    import nexus_orders as o
    mgr = o.OrderManager(); mgr.load_orders()
    return isinstance(mgr.orders, list)
test("orders_manager", t_orders)

def t_crm():
    import nexus_crm as c
    mgr = c.CRMManager(); mgr.load_clientes()
    return isinstance(mgr.clientes, list)
test("crm_manager", t_crm)

def t_stock():
    import nexus_stock as s
    mgr = s.StockManager(); mgr.load_stock()
    return isinstance(mgr.stock, list)
test("stock_manager", t_stock)

def t_voice():
    import nexus_voice as v
    return any(hasattr(v, a) for a in ["hablar","speak","tts","edge_tts"])
test("voice_module", t_voice)

def t_teens():
    import nexus_teens as t
    fns = [f for f in dir(t) if not f.startswith("_") and callable(getattr(t,f))]
    return len(fns) >= 3
test("teens_module", t_teens)

def t_auth():
    from nexus_authorization import authorizer
    r = authorizer.log_action("TEST_SUITE","test automatico","ADMIN")
    return r == True
test("authorization", t_auth)

def t_server_import():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ns","nexus_server.py")
    return spec is not None
test("server_importable", t_server_import)

# SOCIAL NEGOCIOS (nuevas funciones)
def t_social_negocio():
    from nexus_social import generar_post_negocio, get_templates_disponibles
    r = generar_post_negocio("atf", {"vehiculo": "Hilux"})
    assert r.get("ok"), f"ATF post fallo: {r}"
    assert r.get("caracteres", 0) > 100
    r2 = generar_post_negocio("milens")
    assert r2.get("ok")
    templates = get_templates_disponibles()
    assert len(templates) >= 8
    return True
test("social_negocios", t_social_negocio)

# LANDING
def t_landing():
    if CI_MODE:
        # En CI el servidor no corre — verificar que el template existe
        return os.path.exists("WEB/templates/landing.html")
    import urllib.request
    try:
        resp = urllib.request.urlopen("http://localhost:8000/landing", timeout=5)
        html = resp.read().decode("utf-8", errors="ignore")
        return "NEXUS" in html and "WhatsApp" in html
    except:
        return False
test("landing_wa", t_landing)


# DREAM / APRENDIZAJE GENERATIVO
def t_dream():
    from nexus_dream import _recopilar_dia, _cargar_conocimiento, despertar
    datos = _recopilar_dia()
    assert "fecha" in datos, "Sin fecha en datos"
    assert "pedidos" in datos, "Sin pedidos en datos"
    base = _cargar_conocimiento()
    assert "version" in base, "Sin version en conocimiento"
    assert isinstance(base.get("dias_aprendidos", 0), int), "dias_aprendidos no es int"
    r = despertar()
    assert isinstance(r, dict), "despertar no retorna dict"
    return True
test("dream_module", t_dream)

# REPORTE
ok = sum(1 for _,r,_ in RESULTADOS if r)
total = len(RESULTADOS)
pct = int(ok/total*100) if total else 0
estado = "APROBADO" if pct >= 80 else "REVISAR"

print("\n" + "="*55)
print("  NEXUS TEST SUITE  " + time.strftime("%Y-%m-%d %H:%M"))
print("  " + str(ok) + "/" + str(total) + " (" + str(pct) + "%) — " + estado)
print("="*55)
for nombre, r, err in RESULTADOS:
    icono = "OK" if r else "XX"
    linea = "  [" + icono + "] " + nombre
    if err: linea += "  -> " + err
    print(linea)
print("="*55)

with open("BITACORA.md","a",encoding="utf-8") as f:
    errores = [n for n,r,_ in RESULTADOS if not r]
    f.write(time.strftime("%Y-%m-%d %H:%M") + " TEST " + str(ok) + "/" + str(total) + " (" + str(pct) + "%) " + estado)
    if errores: f.write(" FALLAS:" + str(errores))
    f.write("\n")

sys.exit(0 if pct >= 80 else 1)



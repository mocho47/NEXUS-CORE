"""
nexus_dream.py — Ciclo de sueno generativo y aprendizaje real NEXUS.

CONCEPTO:
  Cada noche (00:30 por defecto), NEXUS procesa todo lo vivido durante el dia:
  - Pedidos completados y cancelados
  - Preguntas frecuentes de clientes
  - Productos mas vendidos
  - Errores y fricciones detectadas
  - Interacciones de conversacion

  Con Groq genera:
  1. Resumen narrativo del dia
  2. Patrones detectados ("los viernes hay mas pedidos de X")
  3. Recomendaciones accionables ("subir precio de X", "reactivar a cliente Y")
  4. Frases y respuestas aprendidas (mejora el asistente)

  Todo se persiste en CONFIG/nexus_conocimiento.json y en NexusMemory.
  Al arrancar el dia, el asistente ya sabe mas que ayer.
"""

import os
import json
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
DREAM_PATH = os.path.join(CONFIG_DIR, "nexus_conocimiento.json")
LOG_PATH   = os.path.join(BASE_DIR, "logs", "dream_log.txt")

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


# --- Groq helper -----------------------------------------------------------

def _groq(prompt: str, system: str = "", max_tokens: int = 800) -> str:
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return ""
        client = Groq(api_key=key)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            max_tokens=max_tokens
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return "[sin ia: " + str(e) + "]"


def _log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = "[DREAM][" + ts + "] " + msg + "\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass
    print(linea.strip())


# --- Recoleccion de datos del dia ------------------------------------------

def _recopilar_dia() -> dict:
    """Recopila todo lo ocurrido en el negocio durante el dia."""
    datos = {
        "fecha": datetime.date.today().isoformat(),
        "pedidos": [],
        "stock_bajo": [],
        "ingresos_dia": 0,
        "interacciones": [],
        "servicios_top": [],
        "clientes_activos": 0,
    }

    try:
        from nexus_orders import manager as om
        om.load_orders()
        hoy = datetime.date.today().isoformat()[:10]
        for o in (om.orders or []):
            fecha_o = str(o.get("fecha", ""))[:10]
            if fecha_o == hoy or o.get("status") == "PENDIENTE":
                datos["pedidos"].append({
                    "cliente": o.get("cliente", ""),
                    "producto": o.get("producto", ""),
                    "total": o.get("total", 0),
                    "status": o.get("status", ""),
                })
        datos["ingresos_dia"] = sum(
            float(p.get("total") or 0)
            for p in datos["pedidos"]
            if p.get("status") in ("ENTREGADO", "PAGADO")
        )
    except Exception as e:
        _log("Pedidos error: " + str(e))

    try:
        from nexus_stock import StockManager
        sm = StockManager()
        sm.load()
        for item in (sm.items or []):
            qty = float(item.get("cantidad") or 0)
            min_qty = float(item.get("minimo") or 2)
            if qty <= min_qty:
                datos["stock_bajo"].append({
                    "nombre": item.get("nombre", ""),
                    "cantidad": qty,
                    "unidad": item.get("unidad", ""),
                })
    except Exception as e:
        _log("Stock error: " + str(e))

    try:
        from nexus_memory import NexusMemory
        mem = NexusMemory(CONFIG_DIR)
        recientes = mem.recent_interactions(limit=30)
        datos["interacciones"] = [
            {"rol": r, "texto": t[:200]} for r, t in recientes
        ]
    except Exception as e:
        _log("Memory error: " + str(e))

    try:
        from nexus_finanzas import obtener_dashboard
        dash = obtener_dashboard()
        datos["servicios_top"] = list((dash.get("servicios") or {}).keys())[:5]
        datos["clientes_activos"] = dash.get("clientes", {}).get("activos", 0)
    except Exception as e:
        _log("Finanzas error: " + str(e))

    return datos


# --- Aprendizaje generativo ------------------------------------------------

def _aprender(datos: dict) -> dict:
    """Usa Groq para generar conocimiento desde los datos del dia."""

    resumen_datos = json.dumps(datos, ensure_ascii=False, indent=2)[:3000]

    sistema = (
        "Eres el motor de aprendizaje de NEXUS, asistente de negocio inteligente para SIMPLEX GDL. "
        "Tu trabajo es analizar los datos del dia y extraer conocimiento accionable. "
        "Responde SOLO en JSON valido, sin explicaciones extra."
    )

    prompt = (
        "Analiza estos datos del negocio y genera conocimiento estructurado:\n\n"
        + resumen_datos
        + '\n\nResponde con este JSON exacto:\n'
        + '{"resumen_narrativo": "2-3 oraciones describiendo el dia del negocio",'
        + '"patrones": ["patron 1 detectado", "patron 2"],'
        + '"recomendaciones": ["accion concreta 1", "accion concreta 2"],'
        + '"frases_aprendidas": {"situacion": "respuesta ideal"},'
        + '"alertas": ["alerta urgente si hay"],'
        + '"palabras_clave_negocio": ["palabras frecuentes hoy"]}'
    )

    respuesta_raw = _groq(prompt, system=sistema, max_tokens=1000)

    try:
        inicio = respuesta_raw.find("{")
        fin = respuesta_raw.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            conocimiento = json.loads(respuesta_raw[inicio:fin])
        else:
            conocimiento = {
                "resumen_narrativo": respuesta_raw,
                "patrones": [],
                "recomendaciones": [],
                "frases_aprendidas": {},
                "alertas": [],
                "palabras_clave_negocio": []
            }
    except Exception:
        conocimiento = {
            "resumen_narrativo": respuesta_raw[:500] if respuesta_raw else "Sin datos",
            "patrones": [],
            "recomendaciones": [],
            "frases_aprendidas": {},
            "alertas": [],
            "palabras_clave_negocio": []
        }

    return conocimiento


# --- Persistencia de conocimiento ------------------------------------------

def _cargar_conocimiento() -> dict:
    if os.path.exists(DREAM_PATH):
        try:
            with open(DREAM_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": 1,
        "dias_aprendidos": 0,
        "historial": [],
        "patrones_globales": [],
        "frases_acumuladas": {},
        "recomendaciones_vigentes": [],
        "ultima_consolidacion": None,
    }


def _guardar_conocimiento(base: dict, nuevo: dict, datos_dia: dict):
    """Integra el nuevo conocimiento al historico acumulado."""
    base["dias_aprendidos"] = base.get("dias_aprendidos", 0) + 1
    base["ultima_consolidacion"] = datetime.datetime.now().isoformat()

    entrada = {
        "fecha": datos_dia.get("fecha"),
        "resumen": nuevo.get("resumen_narrativo", ""),
        "ingresos": datos_dia.get("ingresos_dia", 0),
        "pedidos": len(datos_dia.get("pedidos", [])),
        "alertas": nuevo.get("alertas", []),
    }
    historial = base.get("historial", [])
    historial.append(entrada)
    base["historial"] = historial[-30:]

    patrones_existentes = set(base.get("patrones_globales", []))
    for p in nuevo.get("patrones", []):
        patrones_existentes.add(p)
    base["patrones_globales"] = list(patrones_existentes)[-50:]

    frases = base.get("frases_acumuladas", {})
    frases.update(nuevo.get("frases_aprendidas", {}))
    base["frases_acumuladas"] = frases

    base["recomendaciones_vigentes"] = nuevo.get("recomendaciones", [])

    with open(DREAM_PATH, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)


# --- Funcion principal: ciclo de sueno ------------------------------------

def sonar() -> dict:
    """
    Ejecuta el ciclo completo de sueno y aprendizaje.
    Llamar a las 00:30 desde autopilot o manualmente desde panel.
    Retorna el resumen del sueno.
    """
    _log("=== INICIO CICLO DE SUENO ===")

    _log("Recopilando datos del dia...")
    datos_dia = _recopilar_dia()
    _log("Recopilados: " + str(len(datos_dia.get("pedidos", []))) + " pedidos, "
         + str(len(datos_dia.get("interacciones", []))) + " interacciones")

    _log("Procesando con IA generativa...")
    conocimiento_nuevo = _aprender(datos_dia)
    _log("IA genero: " + str(len(conocimiento_nuevo.get("patrones", []))) + " patrones, "
         + str(len(conocimiento_nuevo.get("recomendaciones", []))) + " recomendaciones")

    base = _cargar_conocimiento()
    _guardar_conocimiento(base, conocimiento_nuevo, datos_dia)
    _log("Conocimiento guardado. Total dias aprendidos: " + str(base["dias_aprendidos"]))

    try:
        from nexus_memory import NexusMemory
        mem = NexusMemory(CONFIG_DIR)
        mem.add_note(
            text=conocimiento_nuevo.get("resumen_narrativo", ""),
            kind="dream_summary",
            tags=datos_dia.get("fecha")
        )
        for rec in conocimiento_nuevo.get("recomendaciones", []):
            mem.add_note(text=rec, kind="recomendacion", tags=datos_dia.get("fecha"))
    except Exception as e:
        _log("Memory write error: " + str(e))

    _log("=== FIN CICLO DE SUENO ===")

    return {
        "ok": True,
        "fecha": datos_dia.get("fecha"),
        "dias_aprendidos": base.get("dias_aprendidos"),
        "resumen": conocimiento_nuevo.get("resumen_narrativo", ""),
        "patrones": conocimiento_nuevo.get("patrones", []),
        "recomendaciones": conocimiento_nuevo.get("recomendaciones", []),
        "alertas": conocimiento_nuevo.get("alertas", []),
    }


def despertar() -> dict:
    """
    Al arrancar el dia, retorna el conocimiento consolidado
    para que el asistente arranque informado.
    """
    base = _cargar_conocimiento()
    if not base.get("ultima_consolidacion"):
        return {"ok": False, "msg": "Sin suenos previos aun"}

    return {
        "ok": True,
        "dias_aprendidos": base.get("dias_aprendidos", 0),
        "ultima_consolidacion": base.get("ultima_consolidacion", ""),
        "patrones_globales": base.get("patrones_globales", [])[-10:],
        "recomendaciones_vigentes": base.get("recomendaciones_vigentes", []),
        "resumen_ayer": (base.get("historial") or [{}])[-1].get("resumen", ""),
        "frases_count": len(base.get("frases_acumuladas", {})),
    }


def get_conocimiento_completo() -> dict:
    """Retorna todo el conocimiento acumulado (para panel admin)."""
    return _cargar_conocimiento()


def get_frase_aprendida(situacion: str) -> str:
    """Busca una frase aprendida para una situacion dada."""
    base = _cargar_conocimiento()
    frases = base.get("frases_acumuladas", {})
    if situacion in frases:
        return frases[situacion]
    for k, v in frases.items():
        if situacion.lower() in k.lower():
            return v
    return ""


# --- CLI -------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sonar"
    if cmd == "sonar":
        r = sonar()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif cmd == "despertar":
        r = despertar()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif cmd == "conocimiento":
        r = get_conocimiento_completo()
        print("Dias aprendidos: " + str(r.get("dias_aprendidos", 0)))
        print("Patrones globales: " + str(len(r.get("patrones_globales", []))))
        print("Frases aprendidas: " + str(len(r.get("frases_acumuladas", {}))))
        print("\nUltimas recomendaciones:")
        for rec in r.get("recomendaciones_vigentes", []):
            print("  -> " + rec)

# nexus_assistant.py
"""
Director principal de NEXUS: orquestador, asistente y ayuda contextual.
"""

import os
import sys
import importlib
import subprocess
# Integración de autorización central
from nexus_authorization import authorizer

class NexusAssistant:
    def __init__(self):
        self.version = "2026.02.19"
        self.modules = {}
        self.processes = {}
        self.load_modules()
        self.auto_start_all()
        # Mensaje de bienvenida hablado (si hay motor de voz disponible)
        try:
            if "nexus_voice" in self.modules and hasattr(self.modules["nexus_voice"], "hablar"):
                self.modules["nexus_voice"].hablar("NEXUS iniciado correctamente. Todos los sistemas están en línea y bajo tu control.")
        except Exception as e:
            print(f"[NEXUS] No se pudo reproducir mensaje de bienvenida: {e}")

    def load_modules(self):
        # Detectar todos los módulos nexus_*.py globales
        import glob
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mod_files = glob.glob(os.path.join(base_dir, "nexus_*.py"))
        mod_names = [os.path.splitext(os.path.basename(f))[0] for f in mod_files]
        for name in mod_names:
            try:
                self.modules[name] = importlib.import_module(name)
            except Exception as e:
                self.modules[name] = f"ERROR: {e}"

    def auto_start_all(self):
        # Lanzar web, voz, panel y módulos clave
        base_dir = os.path.dirname(os.path.abspath(__file__))
        procs = {
            "web": os.path.join(base_dir, "nexus_server.py"),
            "voz": os.path.join(base_dir, "nexus_core.py"),
            "panel": os.path.join(base_dir, "nexus_panel.py"),
        }
        for key, path in procs.items():
            if os.path.exists(path):
                self.processes[key] = subprocess.Popen([sys.executable, path])

    def status(self):
        return {
            "version": self.version,
            "modules": {k: ("OK" if isinstance(v, object) and not isinstance(v, str) else v) for k, v in self.modules.items()},
            "cwd": os.getcwd(),
            "processes": list(self.processes.keys()),
        }

    def help(self):
        return "NEXUS Assistant: director principal, ayuda contextual, orquestador de módulos."

    def run_command(self, cmd):
        # Comandos integrales
        # Ejemplo: acciones sensibles requieren autorización
        # Comandos integrales y dinámicos
        dynamic_cmds = tuple([k.replace("nexus_", "") for k in self.modules.keys()])
        if cmd in ("status", "help", "comandos"):
            # No requieren autorización
            if cmd == "status":
                return self.status()
            elif cmd == "help":
                return self.help()
            elif cmd == "comandos":
                return self.list_commands()
        elif cmd in dynamic_cmds:
            # Requieren autorización explícita
            if not authorizer.request_permission(f"Ejecutar comando '{cmd}'", f"Comando solicitado desde NEXUS Assistant"):
                return f"Acción '{cmd}' denegada por el usuario."
            # Buscar si el módulo tiene un atributo manager o describir capacidades
            mod_key = f"nexus_{cmd}"
            mod = self.modules.get(mod_key)
            if hasattr(mod, "manager"):
                info = f"Módulo {mod_key} disponible. Métodos: {', '.join([m for m in dir(mod.manager) if not m.startswith('_')])}"
                return info
            # Si tiene funciones principales, listarlas
            funcs = [f for f in dir(mod) if callable(getattr(mod, f)) and not f.startswith('_')]
            if funcs:
                return f"Módulo {mod_key} disponible. Funciones: {', '.join(funcs)}"
            return f"Módulo {mod_key} cargado. Consulta su documentación para más detalles."
        else:
            return f"Comando no reconocido: {cmd}"

    def list_commands(self):
        cmds = [
            "status - Estado global",
            "help - Ayuda contextual",
            "comandos - Lista integral de comandos",
        ]
        # Agregar comandos dinámicos detectados
        cmds += [f"{k.replace('nexus_','')} - Módulo {k}" for k in self.modules.keys()]
        return "\n".join(cmds)

# ──────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PÚBLICA PARA EL API WEB
# ──────────────────────────────────────────────────────────────────────────────

def get_respuesta(texto: str, session_id: str = "default") -> dict:
    """
    Procesa texto en lenguaje natural y devuelve respuesta para el panel web.
    Implementa las mismas rutas que nexus_core.py pero devuelve texto en vez de hablar.
    """
    import datetime, platform, psutil

    t = texto.lower().strip()

    # ── NUEVO PEDIDO (específico — va ANTES del genérico de pedidos) ───────────
    if any(w in t for w in ["nuevo pedido","crear pedido","registrar pedido","agregar pedido"]):
        return {"respuesta": "Abre el panel de pedidos en /dashboard pestaña Pedidos para agregar uno.",
                "accion": "ir_a_pedidos"}

    # ── NUEVO CLIENTE (específico) ─────────────────────────────────────────────
    if any(w in t for w in ["nuevo cliente","agregar cliente","registrar cliente","crear cliente"]):
        return {"respuesta": "Abre el CRM en /dashboard pestaña Clientes para registrar un nuevo cliente.",
                "accion": "ir_a_clientes"}

    # ── PEDIDOS ────────────────────────────────────────────────────────────────
    if any(w in t for w in ["pedido", "orden", "ordenes", "pedidos"]):
        try:
            from nexus_db import db
            pedidos = db.get_pedidos()
            hoy = datetime.date.today().isoformat()
            hoy_p = [p for p in pedidos if str(p.get("fecha","")).startswith(hoy)]
            pend  = [p for p in pedidos if str(p.get("status","")).lower() in
                     ["pendiente","en proceso","nuevo","por entregar"]]
            return {"respuesta": (
                f"Tienes {len(pedidos)} pedidos en total. "
                f"Hoy: {len(hoy_p)}. "
                f"Pendientes: {len(pend)}."
            )}
        except Exception as e:
            return {"respuesta": f"No pude consultar pedidos: {e}"}

    # ── STOCK / INVENTARIO ─────────────────────────────────────────────────────
    if any(w in t for w in ["stock","inventario","material","producto","item","piezas",
                             "bajo stock","stock crítico","material faltante"]):
        try:
            from nexus_stock import manager as sm
            items = sm.stock or []
            bajos = sm.list_bajo_stock() or []
            return {"respuesta": (
                f"Inventario: {len(items)} artículos. "
                f"Alertas de stock bajo: {len(bajos)}. "
                + (f"Críticos: {', '.join(b.get('nombre','?') for b in bajos[:3])}." if bajos else "Todo en orden.")
            )}
        except Exception as e:
            return {"respuesta": f"No pude consultar stock: {e}"}

    # ── CLIENTES ───────────────────────────────────────────────────────────────
    if any(w in t for w in ["cliente","clientes","contacto","contactos","crm"]):
        try:
            from nexus_crm import manager as cm
            clientes = cm.list_clientes()
            return {"respuesta": f"Tenemos {len(clientes)} clientes registrados en el CRM."}
        except Exception as e:
            return {"respuesta": f"No pude consultar clientes: {e}"}

    # ── VENTAS / INGRESOS ──────────────────────────────────────────────────────
    if any(w in t for w in ["venta","ventas","ingreso","ingresos","dinero","cobré","gané"]):
        try:
            from nexus_db import db
            pedidos = db.get_pedidos()
            hoy = datetime.date.today().isoformat()
            hoy_p = [p for p in pedidos if str(p.get("fecha","")).startswith(hoy) and
                     str(p.get("status","")).lower() in ["entregado","pagado","completado"]]
            total = sum(float(p.get("total",0) or 0) for p in hoy_p)
            return {"respuesta": (
                f"Ventas completadas hoy: {len(hoy_p)} pedidos. "
                f"Total: ${total:,.2f} MXN."
            )}
        except Exception as e:
            return {"respuesta": f"No pude consultar ventas: {e}"}

    # ── SISTEMA / RAM / CPU ────────────────────────────────────────────────────
    if any(w in t for w in ["sistema","estatus","status","ram","cpu","memoria","rendimiento"]):
        try:
            ram = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.5)
            disco = psutil.disk_usage("/")
            return {"respuesta": (
                f"Sistema OK. "
                f"CPU: {cpu:.1f}%. "
                f"RAM: {ram.percent:.1f}% usada ({ram.used//1024//1024} MB de {ram.total//1024//1024} MB). "
                f"Disco: {disco.percent:.1f}% usado."
            )}
        except Exception as e:
            return {"respuesta": f"Sistema activo. No pude obtener métricas: {e}"}

    # ── MARKETING ─────────────────────────────────────────────────────────────
    if any(w in t for w in ["post","instagram","marketing","campaña","tiktok","reel","publicación"]):
        try:
            from nexus_marketing import manager as mm
            if hasattr(mm, "generate_post"):
                post = mm.generate_post()
                return {"respuesta": f"Post generado: {str(post)[:300]}"}
        except Exception:
            pass
        from nexus_autoventas import get_hooks_canal
        hooks = get_hooks_canal("instagram")
        if hooks:
            import random
            return {"respuesta": f"Hook viral para Instagram: \"{random.choice(hooks)}\""}
        return {"respuesta": "Marketing activo. Abre /marketing para generar contenido."}

    # ── HORA / FECHA ───────────────────────────────────────────────────────────
    if any(w in t for w in ["hora","fecha","día","hoy","qué día"]):
        ahora = datetime.datetime.now()
        dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
        meses = ["enero","febrero","marzo","abril","mayo","junio","julio",
                 "agosto","septiembre","octubre","noviembre","diciembre"]
        return {"respuesta": (
            f"Hoy es {dias[ahora.weekday()]}, "
            f"{ahora.day} de {meses[ahora.month-1]} de {ahora.year}. "
            f"Son las {ahora.strftime('%H:%M')}."
        )}

    # ── PARANORMAL ────────────────────────────────────────────────────────────
    if any(w in t for w in ["paranormal","actividad paranormal","detecta actividad","modo oscuro"]):
        return {
            "respuesta": "Iniciando escaneo paranormal... abre /paranormal para el modo completo.",
            "accion": "paranormal"
        }

    # ── BAJO STOCK / ALERTAS ───────────────────────────────────────────────────
    if any(w in t for w in ["alertas stock","se acabó"]):
        try:
            from nexus_stock import manager as sm
            bajos = sm.list_bajo_stock()
            if not bajos:
                return {"respuesta": "No hay alertas de stock bajo. Todo el inventario está en niveles normales."}
            lista = ", ".join(b.get("nombre","?") for b in bajos[:6])
            return {"respuesta": f"Alertas de stock bajo: {len(bajos)} artículos. "
                                 f"Críticos: {lista}."}
        except Exception as e:
            return {"respuesta": f"No pude verificar stock bajo: {e}"}

    # ── COTIZAR / PRECIO ───────────────────────────────────────────────────────
    if any(w in t for w in ["cotiza","cotización","precio","cuánto cuesta","cuánto cobra","tarifa"]):
        return {"respuesta": "Usa el cotizador en /cotizar-rapido para generar una cotización express.",
                "accion": "ir_a_cotizar"}

    # ── AGENDA / CITAS ─────────────────────────────────────────────────────────
    if any(w in t for w in ["agenda","cita","citas","agendar","programar","calendario"]):
        return {"respuesta": "La agenda está disponible en /agenda. ¿Quieres agendar algo en específico?",
                "accion": "ir_a_agenda"}

    # ── AUTOVENTAS / PIPELINE ──────────────────────────────────────────────────
    if any(w in t for w in ["prospecto","prospectos","autoventas","auto-ventas","pipeline","lead","leads"]):
        try:
            from nexus_autoventas import get_pipeline, get_metricas
            metricas = get_metricas()
            return {"respuesta": (
                f"Pipeline de ventas: {metricas.get('total_prospectos',0)} prospectos. "
                f"Clientes convertidos: {metricas.get('clientes',0)}. "
                f"Conversión: {metricas.get('conversion_rate',0):.1f}%. "
                f"Ve el pipeline completo en /autoventas."
            )}
        except Exception as e:
            return {"respuesta": f"No pude consultar el pipeline: {e}"}

    # ── FINANZAS / INGRESOS DETALLE ────────────────────────────────────────────
    if any(w in t for w in ["finanza","finanzas","reporte","ingresos","gastos","balance"]):
        return {"respuesta": "El dashboard financiero está en /finanzas con reportes detallados.",
                "accion": "ir_a_finanzas"}

    # ── GALERÍA BINAURAL ───────────────────────────────────────────────────────
    if any(w in t for w in ["binaural","galería","galeria","audio","meditacion","frecuencia"]):
        try:
            from nexus_galeria import get_uso_actual
            uso = get_uso_actual()
            return {"respuesta": f"Galería binaural activa. {uso}. Abre /galeria para escuchar."}
        except Exception:
            return {"respuesta": "Galería binaural disponible en /galeria. Audios de concentración, relajación y más."}

    # ── DIAGNÓSTICO COMPLETO ───────────────────────────────────────────────────
    if any(w in t for w in ["diagnóstico","diagnostico","autorrepara","auto-repara","revisión completa"]):
        try:
            import psutil
            ram = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.3)
            modulos_ok = []
            modulos_err = []
            for mod in ["nexus_db","nexus_stock","nexus_crm","nexus_marketing",
                        "nexus_autoventas","nexus_admin","nexus_paranormal"]:
                try:
                    __import__(mod)
                    modulos_ok.append(mod.replace("nexus_",""))
                except Exception:
                    modulos_err.append(mod.replace("nexus_",""))
            return {"respuesta": (
                f"Diagnóstico: CPU {cpu:.1f}%, RAM {ram.percent:.1f}%. "
                f"Módulos OK: {len(modulos_ok)}. "
                + (f"Con errores: {', '.join(modulos_err)}." if modulos_err else "Todos los módulos operativos.")
            )}
        except Exception as e:
            return {"respuesta": f"Diagnóstico parcial: {e}"}

    # ── SILENCIAR / CALLAR ────────────────────────────────────────────────────
    if any(w in t for w in ["cállate","silencio","para","cancela","detente","para nexus"]):
        return {"respuesta": "Entendido. En modo espera.", "accion": "silencio"}

    # ── ABRIR MÓDULO / PANEL ──────────────────────────────────────────────────
    PANELES = {
        "admin": "/admin", "autoventas": "/autoventas", "paranormal": "/paranormal",
        "landing": "/landing", "comandos": "/comandos", "ear": "/nexus-ear",
        "setup": "/setup", "stock": "/stock", "clientes": "/clientes",
        "pedidos": "/pedidos", "galeria": "/galeria", "finanzas": "/finanzas",
        "cotizar": "/cotizar-rapido", "marketing": "/marketing",
    }
    for nombre, url in PANELES.items():
        if f"abre {nombre}" in t or f"abrir {nombre}" in t or f"ir a {nombre}" in t:
            return {"respuesta": f"Abriendo {nombre}...", "accion": f"abrir:{url}"}

    # ── LISTA DE COMANDOS COMPLETA ─────────────────────────────────────────────
    if any(w in t for w in ["lista comandos","lista de comandos","qué comandos","todos los comandos",
                             "muéstrame los comandos","qué sabes hacer"]):
        return {"respuesta": (
            "Comandos disponibles: "
            "NEGOCIO: pedidos, nuevo pedido, clientes, nuevo cliente, stock, bajo stock, ventas, cotizar, agenda. "
            "MARKETING: marketing, post para instagram, post para tiktok, hooks virales, calendario editorial. "
            "AUTOVENTAS: prospectos, pipeline, métricas de ventas. "
            "SISTEMA: sistema, diagnóstico, autorrepara, RAM, CPU. "
            "MÓDULOS: finanzas, galería binaural, paranormal, admin. "
            "INFORMACIÓN: hora, fecha, ayuda. "
            "NAVEGACIÓN: abre admin, abre stock, abre clientes, etcétera."
        )}

    # ── AYUDA ─────────────────────────────────────────────────────────────────
    if any(w in t for w in ["ayuda","help","qué puedes","qué haces","comandos","funciones"]):
        return {"respuesta": (
            "Soy NEXUS, tu asistente de negocio. "
            "Gestiono pedidos, inventario, clientes, ventas, marketing, agenda y más. "
            "Di: 'pedidos', 'stock', 'clientes', 'sistema', 'diagnóstico' o cualquier módulo."
        )}

    # ── SALUDO ────────────────────────────────────────────────────────────────
    if any(w in t for w in ["hola","buenos días","buenas tardes","buenas noches","qué tal","cómo estás"]):
        ahora = datetime.datetime.now().hour
        sal = "Buenos días" if ahora < 12 else ("Buenas tardes" if ahora < 19 else "Buenas noches")
        return {"respuesta": f"{sal}. NEXUS en línea y listo. ¿Qué necesitas?"}

    # ── FALLBACK IA GENERATIVA (Groq — llama-3.3-70b) ────────────────────────
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq
            import json as _json

            # Contexto del negocio para respuestas personalizadas
            try:
                _cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CONFIG", "negocio.json")
                with open(_cfg_path, "r", encoding="utf-8") as _f:
                    _neg = _json.load(_f)
                _ctx = f"Negocio: {_neg.get('nombre','Negocio')}. Servicios: {_neg.get('servicios','laser, retrofit de faros')}."
            except Exception:
                _ctx = "Negocio de servicios: laser, cajas personalizadas, retrofit de faros (ATF), canbusfix."

            # Estilo de trabajo del propietario
            try:
                from nexus_estilo_trabajo import get_perfil
                _perfil = get_perfil()
                _estilo = (
                    "ESTILO DE TRABAJO DEL PROPIETARIO (Anuar, Simplex GDL): "
                    "Impresión siempre a 300 DPI. Salida siempre PDF + PNG. "
                    "Dimensiones en centímetros. Sin preguntar innecesariamente — actuar directo. "
                    "Cotizaciones incluyen precio distribuidor, precio público y ganancia neta. "
                    "Planillas: calcular máximo de piezas. Abrir archivo al terminar. "
                    "3 negocios: ATF (retrofit faros LED), Milens (corte láser), CanbusFix (red instaladores). "
                    "Tel: 3326148674. Ciudad: Guadalajara."
                )
            except Exception:
                _estilo = ""

            client = Groq(api_key=groq_key)
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": (
                        f"Eres NEXUS, asistente de IA para un negocio mexicano. {_ctx} "
                        f"{_estilo} "
                        "Respondes en español mexicano, directo y natural. "
                        "Cuando el usuario pide generar algo (planilla, cotización, etiqueta), "
                        "describes cómo lo harías usando el estilo de trabajo del propietario. "
                        "Respuestas cortas (máximo 3 oraciones) para voz."
                    )},
                    {"role": "user", "content": texto}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            respuesta = r.choices[0].message.content.strip()
            return {"respuesta": respuesta}
        except Exception as e:
            return {"respuesta": f"Error de IA: {e}. Configura GROQ_API_KEY en el archivo .env"}

    # Sin Groq — respuesta básica
    return {
        "respuesta": (
            "Para respuestas generativas (chistes, consejos, conversación libre), "
            "agrega GROQ_API_KEY en C:\\nexus\\.env — es gratis en console.groq.com"
        )
    }


if __name__ == "__main__":
    assistant = NexusAssistant()
    print("=== NEXUS DIRECTOR PRINCIPAL ===")
    print("Versión:", assistant.version)
    print("Estado:", assistant.status())
    print("Ayuda:", assistant.help())
    while True:
        cmd = input("[NEXUS] > ").strip()
        if cmd.lower() in ("exit", "quit"): break
        print(assistant.run_command(cmd))

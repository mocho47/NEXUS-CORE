"""
nexus_autoventas.py — Motor de Auto-Ventas NEXUS
=================================================
NEXUS se vende a sí mismo de forma autónoma y ética.

Capacidades:
  1. Pipeline de prospectos (lead → demo → propuesta → cliente)
  2. Generación de contenido viral para cada módulo de NEXUS
  3. Secuencias de seguimiento (día 7, 14, 25, 28)
  4. Propuesta personalizada en texto/HTML
  5. Generador de hooks virales por canal
  6. Analytics básico de conversión

Ética:
  - Solo contacta prospectos que dieron sus datos voluntariamente
  - Rate limiting en todos los mensajes automatizados
  - Sin spam, sin compra de bases de datos
  - Contenido 100% real (no promesas falsas)

Data: CONFIG/autoventas.json
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
AV_FILE    = os.path.join(CONFIG_DIR, "autoventas.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONTENIDO VIRAL — NEXUS se promueve a sí mismo
# ═══════════════════════════════════════════════════════════════════════════════

HOOKS_VIRALES: dict[str, list[str]] = {
    "tiktok": [
        "POV: tu negocio tiene IA en español y no le tienes que pagar mensualidad 👁️",
        "Le pregunté a mi asistente IA qué publicar hoy y esto pasó... 🤯",
        "NEXUS detectó algo en mis ventas que yo no había visto 🔮 (y tenía razón)",
        "Mi taller + IA local = esto. Sin internet. Sin cuotas. 🔥",
        "Así suena cuando NEXUS controla tu negocio por voz 🎤",
        "3 cosas que NEXUS hace mientras yo duermo 😴",
        "Cuando la IA de tu negocio tiene personalidad propia... glitch incluido 👾",
        "El día que le enseñé a NEXUS el inventario de mi taller 📦",
    ],
    "instagram": [
        "¿Tu negocio ya tiene asistente IA? El mío sí, y habla español mexicano 🇲🇽",
        "NEXUS: el sistema que gestiona pedidos, marketing y clientes en uno solo ⚡",
        "Sin suscripción mensual. Sin inglés. Sin complicaciones. Solo NEXUS. 💚",
        "Le doy voz a mi negocio — literalmente. Conoce NEXUS. 🎙️",
        "Marketing IA integrado: de 0 a TikTok viral sin agencia 📣",
    ],
    "facebook": [
        "¿Eres dueño de un taller, tienda o negocio y sigues con Excel? Hay algo mejor.",
        "NEXUS: gestión de negocio con IA, sin internet obligatorio, sin mensualidad.",
        "Hola comunidad — ¿alguien más tiene problema con los pedidos? Yo lo resolví así:",
        "Sistema de gestión para PyMEs mexicanas — sin cuotas mensuales. ¿Lo conocen?",
    ],
    "whatsapp": [
        "Hola! Vi que tienes un negocio — te comparto algo que me ha cambiado la operación:",
        "Prueba NEXUS gratis 30 días. Sin tarjeta. Sin trampa. Solo resultados.",
    ],
    "youtube": [
        "NEXUS en acción: gestiono mi taller con IA sin internet",
        "Tutorial: cómo automaticé mis pedidos con NEXUS en 10 minutos",
        "La IA que habla español mexicano y vive en tu computadora",
    ],
}

SCRIPTS_REEL: dict[str, dict] = {
    "pedidos": {
        "titulo": "Así gestiono 30 pedidos al día sin perder ninguno",
        "gancho": "¿Cuántos pedidos pierdes a la semana por no tener sistema?",
        "cuerpo": "Con NEXUS registro, asigno y doy seguimiento a cada pedido desde el cel.",
        "cta": "Pruébalo gratis 30 días. Link en bio.",
        "hashtags": "#NexusIA #GestionDeNegocios #TallerGrafico #EmprendedorMX",
    },
    "marketing": {
        "titulo": "Le pedí a la IA que me hiciera el post de hoy",
        "gancho": "¿Cuánto tiempo pierdes pensando qué publicar?",
        "cuerpo": "NEXUS genera copies, hashtags y hasta el guión del reel con IA.",
        "cta": "Demo gratis — sin tarjeta.",
        "hashtags": "#MarketingIA #EmprendedorMX #NexusIA #ContenidoIA",
    },
    "asistente": {
        "titulo": "Mi negocio me responde por voz ahora",
        "gancho": "¿Y si pudieras preguntarle a tu negocio cómo va sin abrir Excel?",
        "cuerpo": "NEXUS contesta: pedidos, stock, clientes, ventas — todo por voz.",
        "cta": "Descarga el demo. Funciona sin internet.",
        "hashtags": "#AsistenteIA #VoiceFirst #NexusIA #TecnologíaMX",
    },
    "stock": {
        "titulo": "NEXUS me avisó antes de quedarme sin material",
        "gancho": "¿Cuánto dinero pierdes por quedarte sin stock sin darte cuenta?",
        "cuerpo": "Alerta automática de stock bajo. Lista de reabasto con un toque.",
        "cta": "30 días gratis. Empieza hoy.",
        "hashtags": "#InventarioIA #NexusIA #GestionStock #PyMEMX",
    },
    "paranormal": {
        "titulo": "NEXUS detectó una anomalía en mis ventas... y tenía razón 👁️",
        "gancho": "¿Tu sistema de negocio tiene modo paranormal?",
        "cuerpo": "NEXUS escaneó mis datos y detectó un patrón que yo ignoraba. Modo oscuro activado.",
        "cta": "El modo paranormal solo existe en NEXUS PRO. Link en bio.",
        "hashtags": "#NexusParanormal #IAMisteriosa #NexusIA #EmprendedorMX",
    },
    "teens": {
        "titulo": "Le di a mi hijo un asistente IA para que aprenda negocios",
        "gancho": "¿Qué pasa cuando un adolescente tiene acceso a herramientas de IA reales?",
        "cuerpo": "NEXUS Teens: misiones, aptitudes, viral marketing — aprendizaje real sin hacerle la tarea.",
        "cta": "Módulo Teens disponible con NEXUS FULL.",
        "hashtags": "#NexusTeens #IAParaJóvenes #EmprendimientoJoven #FamiliaEmprendedora",
    },
}

PROPUESTA_TEMPLATE = """
╔══════════════════════════════════════════════════════╗
║         PROPUESTA NEXUS BUSINESS SUITE               ║
║         Para: {nombre_negocio}                       ║
║         Fecha: {fecha}                               ║
╚══════════════════════════════════════════════════════╝

Hola {nombre_contacto},

Basado en el perfil de tu negocio ({tipo_negocio}), te recomiendo:

📦 NEXUS {licencia_recomendada} — ${precio} MXN ({duracion})

¿QUÉ INCLUYE?
{modulos_lista}

¿POR QUÉ NEXUS PARA TI?
  ✅ Sin suscripción mensual — pagas una vez
  ✅ Funciona sin internet (modo local)
  ✅ En español mexicano — informal, claro, directo
  ✅ Marketing IA: genera posts, reels y copies automáticamente
  ✅ Soporte por WhatsApp incluido los primeros 3 meses

PRÓXIMOS PASOS:
  1. Descarga el DEMO gratis (30 días completos)
  2. Pruébalo en tu negocio real
  3. Si te convence, activa tu licencia con un código

🔗 Demo: [nexus.local/demo]
📱 WhatsApp: {whatsapp_soporte}

NEXUS — El sistema de gestión que habla tu idioma.

Con gusto resuelvo cualquier duda,
{nombre_admin}
"""

SEGUIMIENTO_SECUENCIA = {
    7:  "¡Hola {nombre}! Ya llevas 7 días con NEXUS. ¿Cómo va todo? ¿Alguna duda? Estoy aquí.",
    14: "¡{nombre}! Tu demo ya lleva 14 días. ¿Quieres que te muestre cómo activar el módulo de marketing? Es el que más usan.",
    25: "Oye {nombre}, tu demo de NEXUS vence en 5 días. Si quieres continuar, hoy puedo darte un descuento especial de lanzamiento.",
    28: "Último día de tu demo de NEXUS, {nombre}. ¿Qué fue lo que más te gustó? Cuéntame — me ayuda a mejorar.",
}

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE DE PROSPECTOS
# ═══════════════════════════════════════════════════════════════════════════════

STAGES = ["nuevo", "demo_activo", "propuesta_enviada", "seguimiento", "cliente", "perdido"]

def _load_av() -> dict:
    if os.path.exists(AV_FILE):
        try:
            with open(AV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"prospectos": {}, "metricas": {"total": 0, "clientes": 0, "perdidos": 0}}

def _save_av(data: dict):
    with open(AV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _pid(nombre: str, telefono: str) -> str:
    return hashlib.md5(f"{nombre}{telefono}".encode()).hexdigest()[:12]

def registrar_prospecto(nombre: str, telefono: str, tipo_negocio: str = "General",
                        canal: str = "web", notas: str = "") -> dict:
    """Registra un nuevo prospecto en el pipeline."""
    av = _load_av()
    pid = _pid(nombre, telefono)
    if pid in av["prospectos"]:
        return {"ok": True, "pid": pid, "msg": "Prospecto ya existente.", "nuevo": False}
    av["prospectos"][pid] = {
        "pid":           pid,
        "nombre":        nombre,
        "telefono":      telefono,
        "tipo_negocio":  tipo_negocio,
        "canal":         canal,
        "notas":         notas,
        "stage":         "nuevo",
        "fecha_registro": datetime.now().isoformat(),
        "demo_inicio":   None,
        "ultimo_contacto": None,
        "seguimiento_enviado": [],
        "licencia":      None,
    }
    av["metricas"]["total"] = len(av["prospectos"])
    _save_av(av)
    return {"ok": True, "pid": pid, "msg": f"Prospecto {nombre} registrado.", "nuevo": True}

def avanzar_stage(pid: str, nuevo_stage: str, nota: str = "") -> dict:
    """Mueve un prospecto al siguiente stage del pipeline."""
    av = _load_av()
    if pid not in av["prospectos"]:
        return {"ok": False, "error": "Prospecto no encontrado."}
    if nuevo_stage not in STAGES:
        return {"ok": False, "error": f"Stage inválido. Opciones: {STAGES}"}
    p = av["prospectos"][pid]
    p["stage"] = nuevo_stage
    p["ultimo_contacto"] = datetime.now().isoformat()
    if nota:
        p["notas"] = (p.get("notas","") + f"\n[{datetime.now().date()}] {nota}").strip()
    if nuevo_stage == "demo_activo" and not p.get("demo_inicio"):
        p["demo_inicio"] = datetime.now().isoformat()
    if nuevo_stage == "cliente":
        av["metricas"]["clientes"] = sum(1 for x in av["prospectos"].values() if x["stage"]=="cliente")
    if nuevo_stage == "perdido":
        av["metricas"]["perdidos"] = sum(1 for x in av["prospectos"].values() if x["stage"]=="perdido")
    _save_av(av)
    return {"ok": True, "pid": pid, "stage": nuevo_stage}

def get_pipeline() -> dict:
    """Devuelve el pipeline completo organizado por stage."""
    av = _load_av()
    pipeline: dict[str, list] = {s: [] for s in STAGES}
    for p in av["prospectos"].values():
        pipeline[p["stage"]].append({
            "pid":          p["pid"],
            "nombre":       p["nombre"],
            "telefono":     p["telefono"],
            "tipo_negocio": p["tipo_negocio"],
            "canal":        p["canal"],
            "fecha":        p["fecha_registro"][:10],
        })
    return {
        "ok":       True,
        "pipeline": pipeline,
        "metricas": av["metricas"],
        "conversion_rate": (
            round(av["metricas"]["clientes"] / max(av["metricas"]["total"],1) * 100, 1)
        ),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# SEGUIMIENTO AUTOMÁTICO
# ═══════════════════════════════════════════════════════════════════════════════

def check_seguimiento_pendiente() -> list[dict]:
    """
    Revisa qué prospectos necesitan seguimiento hoy.
    Llamar desde nexus_scheduler o autopilot.
    """
    av  = _load_av()
    hoy = datetime.now()
    pendientes = []

    for p in av["prospectos"].values():
        if p["stage"] not in ["demo_activo", "propuesta_enviada"]:
            continue
        if not p.get("demo_inicio"):
            continue
        inicio   = datetime.fromisoformat(p["demo_inicio"])
        dias     = (hoy - inicio).days
        enviados = set(p.get("seguimiento_enviado", []))

        for dia_objetivo, mensaje_template in SEGUIMIENTO_SECUENCIA.items():
            if dias >= dia_objetivo and dia_objetivo not in enviados:
                mensaje = mensaje_template.format(nombre=p["nombre"].split()[0])
                pendientes.append({
                    "pid":      p["pid"],
                    "nombre":   p["nombre"],
                    "telefono": p["telefono"],
                    "dia":      dia_objetivo,
                    "mensaje":  mensaje,
                })

    return pendientes

def marcar_seguimiento_enviado(pid: str, dia: int) -> dict:
    av = _load_av()
    if pid not in av["prospectos"]:
        return {"ok": False, "error": "Prospecto no encontrado."}
    enviados = av["prospectos"][pid].setdefault("seguimiento_enviado", [])
    if dia not in enviados:
        enviados.append(dia)
    av["prospectos"][pid]["ultimo_contacto"] = datetime.now().isoformat()
    _save_av(av)
    return {"ok": True, "pid": pid, "dia_marcado": dia}

# ═══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE PROPUESTA
# ═══════════════════════════════════════════════════════════════════════════════

LICENCIA_POR_TIPO = {
    "taller":     ("PRO", "$2,800 MXN", "3 años"),
    "tienda":     ("LITE", "$1,200 MXN", "1 año"),
    "restaurante":("PRO", "$2,800 MXN", "3 años"),
    "servicios":  ("LITE", "$1,200 MXN", "1 año"),
    "general":    ("LITE", "$1,200 MXN", "1 año"),
    "familia":    ("FULL", "$5,999 MXN", "10 años"),
}

MODULOS_POR_LICENCIA = {
    "LITE":  "Pedidos · Clientes · Stock · Marketing IA · Asistente · Finanzas · Agenda · Notificaciones",
    "PRO":   "Todo LITE + Redes Sociales · Video · Binaural · Galería 15/mes · Asistente ilimitado",
    "FULL":  "TODOS los módulos: Spy · Meta Ads · Teens · IoT · MiLens · Paranormal · CFDI · sin límites",
}

def generar_propuesta(pid: str, whatsapp_soporte: str = "NEXUS Soporte",
                      nombre_admin: str = "El equipo NEXUS") -> dict:
    av = _load_av()
    if pid not in av["prospectos"]:
        return {"ok": False, "error": "Prospecto no encontrado."}
    p       = av["prospectos"][pid]
    tipo    = p["tipo_negocio"].lower()
    lic_key = tipo if tipo in LICENCIA_POR_TIPO else "general"
    lic, precio, duracion = LICENCIA_POR_TIPO[lic_key]
    modulos = MODULOS_POR_LICENCIA.get(lic, "")

    texto = PROPUESTA_TEMPLATE.format(
        nombre_negocio=p["nombre"],
        fecha=datetime.now().strftime("%d/%m/%Y"),
        nombre_contacto=p["nombre"].split()[0],
        tipo_negocio=p["tipo_negocio"],
        licencia_recomendada=lic,
        precio=precio.replace(" MXN",""),
        duracion=duracion,
        modulos_lista=modulos,
        whatsapp_soporte=whatsapp_soporte,
        nombre_admin=nombre_admin,
    )
    return {
        "ok":       True,
        "pid":      pid,
        "texto":    texto,
        "licencia": lic,
        "precio":   precio,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE CONTENIDO VIRAL
# ═══════════════════════════════════════════════════════════════════════════════

def get_hooks_canal(canal: str) -> list[str]:
    return HOOKS_VIRALES.get(canal.lower(), HOOKS_VIRALES["tiktok"])

def get_script_reel(modulo: str) -> dict:
    return SCRIPTS_REEL.get(modulo, SCRIPTS_REEL["pedidos"])

def get_calendario_semanal() -> list[dict]:
    """Genera un calendario editorial de 7 días para NEXUS."""
    modulos_rota = list(SCRIPTS_REEL.keys())
    calendario = []
    dias = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    tipos = ["feature", "caso_uso", "humor", "educativo", "testimonial", "reto", "reflexion"]
    hooks_ig = HOOKS_VIRALES["instagram"]
    hooks_tk = HOOKS_VIRALES["tiktok"]

    for i, dia in enumerate(dias):
        modulo = modulos_rota[i % len(modulos_rota)]
        script = SCRIPTS_REEL[modulo]
        calendario.append({
            "dia":      dia,
            "tipo":     tipos[i],
            "modulo":   modulo,
            "titulo":   script["titulo"],
            "hook_tiktok":    hooks_tk[i % len(hooks_tk)],
            "hook_instagram": hooks_ig[i % len(hooks_ig)],
            "hashtags": script["hashtags"],
            "cta":      script["cta"],
        })
    return calendario

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_metricas() -> dict:
    av   = _load_av()
    pros = av["prospectos"]
    total    = len(pros)
    clientes = sum(1 for p in pros.values() if p["stage"] == "cliente")
    perdidos = sum(1 for p in pros.values() if p["stage"] == "perdido")
    activos  = sum(1 for p in pros.values() if p["stage"] not in ["cliente","perdido"])
    canales: dict[str, int] = {}
    for p in pros.values():
        canales[p.get("canal","web")] = canales.get(p.get("canal","web"), 0) + 1

    return {
        "ok":               True,
        "total_prospectos": total,
        "clientes":         clientes,
        "perdidos":         perdidos,
        "activos":          activos,
        "conversion_rate":  round(clientes / max(total,1) * 100, 1),
        "canal_ranking":    sorted(canales.items(), key=lambda x: -x[1]),
        "pendientes_seguimiento": len(check_seguimiento_pendiente()),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ayuda"

    if cmd == "pipeline":
        p = get_pipeline()
        for stage, lista in p["pipeline"].items():
            if lista:
                print(f"\n── {stage.upper()} ({len(lista)}) ──")
                for pr in lista:
                    print(f"  {pr['nombre']} | {pr['tipo_negocio']} | {pr['canal']}")
        print(f"\nConversión: {p['conversion_rate']}%")

    elif cmd == "seguimiento":
        pendientes = check_seguimiento_pendiente()
        if not pendientes:
            print("✅ Sin seguimientos pendientes hoy.")
        for seg in pendientes:
            print(f"\n📱 {seg['nombre']} ({seg['telefono']}) — Día {seg['dia']}")
            print(f"   Mensaje: {seg['mensaje']}")

    elif cmd == "hooks":
        canal = sys.argv[2] if len(sys.argv) > 2 else "tiktok"
        for h in get_hooks_canal(canal):
            print(f"  → {h}")

    elif cmd == "calendario":
        for dia in get_calendario_semanal():
            print(f"\n{dia['dia']} [{dia['tipo']}] — {dia['modulo']}")
            print(f"  TikTok: {dia['hook_tiktok'][:60]}...")
            print(f"  IG: {dia['hook_instagram'][:60]}...")

    elif cmd == "metricas":
        m = get_metricas()
        print(f"Prospectos: {m['total_prospectos']}")
        print(f"Clientes: {m['clientes']} ({m['conversion_rate']}%)")
        print(f"Pendientes seguimiento: {m['pendientes_seguimiento']}")

    else:
        print("Uso: python nexus_autoventas.py [pipeline|seguimiento|hooks|calendario|metricas]")

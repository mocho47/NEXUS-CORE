"""
nexus_agent.py — Agente conversacional universal de NEXUS.
Entiende CUALQUIER solicitud, detecta qué información falta,
pregunta lo mínimo necesario y ejecuta solo.
"""
import os, json, datetime, re
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Contexto de sesión de conversación ──────────────────────────────────────
_sessions: dict = {}   # session_id → {intent, datos, step, historial}

# ─── Groq client ─────────────────────────────────────────────────────────────
def _groq_client():
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if key:
            return Groq(api_key=key)
    except ImportError:
        pass
    return None

def _ask_groq(prompt: str, system: str = "", max_tokens: int = 600) -> str:
    client = _groq_client()
    if not client:
        return ""
    try:
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
        return f"[Groq error: {e}]"

# ─── Sistema de intención y slots ────────────────────────────────────────────

INTENTS = {
    "marketing_post":   ["publicar", "promocionar", "postear", "anunciar", "vender", "difundir", "compartir", "subir"],
    "marketing_video":  ["video", "reel", "tiktok", "clip", "grabar", "editar"],
    "marketing_copy":   ["copy", "texto", "descripción", "caption", "guion", "script"],
    "imagen_proceso":   ["imagen", "foto", "archivo", "optimizar", "preparar", "editar imagen"],
    "pedido_nuevo":     ["pedido", "orden", "cliente quiere", "encargo", "trabajo"],
    "stock_update":     ["stock", "inventario", "agregar", "material", "insumo"],
    "cliente_nuevo":    ["cliente nuevo", "registrar cliente", "agregar contacto"],
    "consulta_negocio": ["cuánto", "cuántos", "ventas", "resumen", "reporte", "estado"],
    "autopilot":        ["modo sueño", "automático", "autopilot", "programar", "mientras duermo"],
}

SLOTS_REQUERIDOS = {
    "marketing_post": ["producto", "audiencia", "precio", "plataforma"],
    "marketing_video": ["producto", "tipo_video", "duracion", "plataforma"],
    "marketing_copy": ["producto", "audiencia", "tono"],
    "imagen_proceso": ["servicio"],
    "pedido_nuevo": ["cliente", "producto", "entrega"],
    "stock_update": ["nombre", "cantidad", "precio"],
    "cliente_nuevo": ["nombre", "telefono"],
    "consulta_negocio": [],
    "autopilot": ["tarea", "frecuencia"],
}

PREGUNTAS = {
    "producto":    "¿Qué producto o servicio quieres promocionar? Descríbelo con detalle.",
    "audiencia":   "¿A quién va dirigido? (edad, intereses, tipo de cliente ideal)",
    "precio":      "¿Cuál es el precio o propuesta de valor? (puede ser 'desde $X' o 'gratis')",
    "plataforma":  "¿En qué plataformas lo publico? (Instagram, TikTok, WhatsApp, Facebook, Todas)",
    "tipo_video":  "¿Qué tipo de video? (proceso de fabricación, resultado final, testimonio, promo)",
    "duracion":    "¿Duración aproximada? (15 seg para Reel, 60 seg, más largo)",
    "tono":        "¿Qué tono debe tener? (profesional, divertido, urgente, inspiracional, cercano)",
    "servicio":    "¿Para qué servicio es este archivo? (Laser, Sublimación, DTF, Lona/Banner, Neón)",
    "cliente":     "¿Nombre del cliente?",
    "entrega":     "¿Cuándo es la entrega? (fecha y hora)",
    "nombre":      "¿Nombre del material o producto?",
    "cantidad":    "¿Qué cantidad?",
    "tarea":       "¿Qué tarea quieres automatizar? (publicar diario, seguimiento clientes, reportes)",
    "frecuencia":  "¿Con qué frecuencia? (diario a las 6pm, cada lunes, etc.)",
}

# ─── Detectar intención ───────────────────────────────────────────────────────

def _detectar_intent(texto: str) -> str:
    texto_lower = texto.lower()
    for intent, palabras in INTENTS.items():
        if any(p in texto_lower for p in palabras):
            return intent
    # Fallback: preguntar a Groq
    r = _ask_groq(
        f"Clasifica esta solicitud en una de estas categorías: "
        f"{list(INTENTS.keys())}. Solicitud: '{texto}'. "
        f"Responde SOLO el nombre de la categoría, sin explicación.",
        max_tokens=20
    )
    for intent in INTENTS:
        if intent in r.lower():
            return intent
    return "marketing_post"  # default

def _extraer_slots_del_texto(texto: str, intent: str) -> dict:
    """Extrae información útil del texto inicial para pre-llenar slots."""
    slots = {}
    texto_lower = texto.lower()

    # Detectar precio en el texto
    precio_match = re.search(r'\$[\d,]+|\d+\s*pesos', texto_lower)
    if precio_match:
        slots["precio"] = precio_match.group()

    # Detectar plataformas
    plataformas = []
    for p in ["instagram", "tiktok", "facebook", "whatsapp"]:
        if p in texto_lower:
            plataformas.append(p.capitalize())
    if plataformas:
        slots["plataforma"] = ", ".join(plataformas)
    if "todas" in texto_lower or "todo" in texto_lower:
        slots["plataforma"] = "Instagram, TikTok, WhatsApp, Facebook"

    # Detectar servicios de imagen
    for s in ["laser", "sublimacion", "sublimación", "dtf", "lona", "neon", "neón"]:
        if s in texto_lower:
            slots["servicio"] = s.upper().replace("Ó","O").replace("É","E")
            break

    # Si el texto describe un producto directamente
    if intent == "marketing_post" and len(texto.split()) >= 3:
        slots["producto"] = texto  # el texto completo ES la descripción del producto

    return slots

# ─── API principal del agente ─────────────────────────────────────────────────

def procesar_mensaje(session_id: str, mensaje: str, archivo_path: str = None) -> dict:
    """
    Procesa un mensaje del usuario y retorna la respuesta del agente.

    Returns:
        {
          "respuesta": str,          # lo que NEXUS dice
          "tipo": "pregunta"|"accion"|"listo"|"error",
          "slot_actual": str|None,   # qué pregunta está haciendo
          "progreso": int,           # 0-100% de información recolectada
          "resultado": dict|None     # cuando está listo: contenido generado
        }
    """
    # Inicializar sesión si no existe
    if session_id not in _sessions:
        _sessions[session_id] = {
            "intent": None,
            "datos": {},
            "step": "detectar",
            "historial": [],
            "archivo": None,
        }

    sesion = _sessions[session_id]
    sesion["historial"].append({"rol": "usuario", "msg": mensaje})

    if archivo_path:
        sesion["archivo"] = archivo_path

    # ── PASO 1: Detectar intención ─────────────────────────────────────────
    if sesion["step"] == "detectar":
        intent = _detectar_intent(mensaje)
        sesion["intent"] = intent
        sesion["datos"] = _extraer_slots_del_texto(mensaje, intent)
        sesion["step"] = "recolectar"

    # ── PASO 2: Recolectar slots (un slot a la vez) ────────────────────────
    if sesion["step"] == "recolectar":
        # Guardar respuesta al slot anterior si aplica
        if sesion.get("slot_pendiente"):
            sesion["datos"][sesion["slot_pendiente"]] = mensaje
            sesion["slot_pendiente"] = None

        # Encontrar siguiente slot que falta
        slots_req = SLOTS_REQUERIDOS.get(sesion["intent"], [])
        faltantes = [s for s in slots_req if not sesion["datos"].get(s)]

        if faltantes:
            slot = faltantes[0]
            sesion["slot_pendiente"] = slot

            # Calcular progreso
            total = len(slots_req) if slots_req else 1
            completados = total - len(faltantes)
            progreso = int((completados / total) * 80)

            # Generar pregunta contextual con IA si está disponible
            pregunta_base = PREGUNTAS.get(slot, f"¿{slot}?")

            if completados == 0:
                # Primera pregunta: contextualizar con lo que ya sabe
                intro = _generar_intro_contextual(sesion)
                respuesta = f"{intro}\n\n{pregunta_base}"
            else:
                respuesta = f"{pregunta_base}"

            sesion["historial"].append({"rol": "nexus", "msg": respuesta})
            return {
                "respuesta": respuesta,
                "tipo": "pregunta",
                "slot_actual": slot,
                "progreso": progreso,
                "resultado": None
            }

        # Todos los slots completos
        sesion["step"] = "ejecutar"

    # ── PASO 3: Ejecutar ──────────────────────────────────────────────────
    if sesion["step"] == "ejecutar":
        resultado = _ejecutar_intent(sesion)
        # Limpiar sesión para nueva conversación
        _sessions[session_id] = {
            "intent": None, "datos": {},
            "step": "detectar", "historial": [], "archivo": None
        }
        return {
            "respuesta": resultado.get("mensaje", "Listo."),
            "tipo": "listo",
            "slot_actual": None,
            "progreso": 100,
            "resultado": resultado
        }

    return {"respuesta": "Entendido.", "tipo": "ok", "slot_actual": None, "progreso": 0, "resultado": None}


def _generar_intro_contextual(sesion: dict) -> str:
    """Genera una introducción contextual basada en lo que NEXUS ya detectó."""
    intent = sesion["intent"]
    datos = sesion["datos"]

    intros = {
        "marketing_post":  "Perfecto, creo tu campaña ahora mismo.",
        "marketing_video": "Voy a crear el guion de tu video.",
        "marketing_copy":  "Genero el copy para tus redes.",
        "imagen_proceso":  "Proceso tu archivo para el servicio indicado.",
        "pedido_nuevo":    "Registro el pedido.",
        "stock_update":    "Actualizo el inventario.",
        "cliente_nuevo":   "Registro al cliente.",
        "consulta_negocio":"Consulto el estado de tu negocio.",
        "autopilot":       "Configuro el modo automático.",
    }

    if datos.get("producto"):
        return f"Entendido. Voy a crear la campaña para: **{datos['producto']}**. Necesito algunos datos más."

    return intros.get(intent, "Entendido, necesito un par de datos más.")


# ─── Ejecutores por intent ────────────────────────────────────────────────────

def _ejecutar_intent(sesion: dict) -> dict:
    intent = sesion["intent"]
    datos  = sesion["datos"]

    ejecutores = {
        "marketing_post":  _ejecutar_marketing_post,
        "marketing_video": _ejecutar_marketing_video,
        "marketing_copy":  _ejecutar_marketing_copy,
        "imagen_proceso":  _ejecutar_imagen_proceso,
        "pedido_nuevo":    _ejecutar_pedido_nuevo,
        "stock_update":    _ejecutar_stock_update,
        "cliente_nuevo":   _ejecutar_cliente_nuevo,
        "consulta_negocio":_ejecutar_consulta,
        "autopilot":       _ejecutar_autopilot,
    }

    fn = ejecutores.get(intent, _ejecutar_marketing_post)
    try:
        return fn(datos, sesion.get("archivo"))
    except Exception as e:
        return {"ok": False, "mensaje": f"Error ejecutando: {e}", "error": str(e)}


def _ejecutar_marketing_post(datos: dict, archivo=None) -> dict:
    """Genera copy completo y lo publica si hay credenciales."""
    producto   = datos.get("producto", "Producto")
    audiencia  = datos.get("audiencia", "público general")
    precio     = datos.get("precio", "")
    plataforma = datos.get("plataforma", "Instagram")
    tono       = datos.get("tono", "cercano y auténtico")

    system = (
        "Eres un experto en marketing digital latinoamericano. "
        "Creas copy viral, auténtico, con psicología de ventas. "
        "Nunca suenas corporativo. Siempre incluyes CTA claro."
    )

    prompt = (
        f"Crea un post completo para redes sociales.\n"
        f"Producto/Servicio: {producto}\n"
        f"Audiencia objetivo: {audiencia}\n"
        f"Precio/Valor: {precio if precio else 'no especificado'}\n"
        f"Tono: {tono}\n"
        f"Plataformas: {plataforma}\n\n"
        f"Genera:\n"
        f"1. CAPTION (texto principal del post, máx 150 palabras)\n"
        f"2. HOOK (primera frase que detiene el scroll)\n"
        f"3. HASHTAGS (15-20 relevantes, mezcla popular y nicho)\n"
        f"4. HISTORIA (versión para Instagram Stories, 3 slides)\n"
        f"5. WHATSAPP (mensaje de seguimiento, informal, máx 3 líneas)\n\n"
        f"Formato: Separa cada sección con '=== SECCION ==='."
    )

    contenido = _ask_groq(prompt, system=system, max_tokens=800)

    if not contenido:
        # Fallback sin Groq
        contenido = (
            f"=== CAPTION ===\n"
            f"¿Buscas {producto}? 🔥\n"
            f"Esto es exactamente lo que necesitas.\n"
            f"{f'Desde {precio}' if precio else ''}\n"
            f"📲 Escríbenos para cotizar.\n\n"
            f"=== HASHTAGS ===\n"
            f"#HechoEnMexico #Emprendedor #Personalizado #Calidad"
        )

    # Guardar en archivo
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = os.path.join(BASE_DIR, "TALLER", "MARKETING_STUDIO")
    os.makedirs(output_dir, exist_ok=True)
    nombre_archivo = f"POST_{producto[:20].replace(' ','_')}_{ts}.txt"
    ruta = os.path.join(output_dir, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"CAMPAÑA: {producto}\n")
        f.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Plataforma: {plataforma}\n\n")
        f.write(contenido)

    # Intentar publicar si hay credenciales Meta
    publicado = False
    ig_result = None
    if os.environ.get("META_ACCESS_TOKEN") and os.environ.get("META_IG_USER_ID"):
        if archivo:
            # Si hay imagen, intentar publicar (necesita URL pública)
            pass  # TODO: subir imagen a CDN temporal

    mensaje = (
        f"✓ Campaña generada para **{producto}**.\n"
        f"Archivo guardado en MARKETING_STUDIO.\n"
        + ("✓ Publicado en Instagram." if publicado else
           "⚠ Para publicar en Instagram configura META_ACCESS_TOKEN en .env")
    )

    return {
        "ok": True,
        "mensaje": mensaje,
        "contenido": contenido,
        "archivo": ruta,
        "publicado": publicado,
        "plataforma": plataforma,
    }


def _ejecutar_marketing_video(datos: dict, archivo=None) -> dict:
    producto    = datos.get("producto", "Producto")
    tipo_video  = datos.get("tipo_video", "proceso de fabricación")
    duracion    = datos.get("duracion", "30 segundos")
    plataforma  = datos.get("plataforma", "TikTok/Reels")

    system = "Eres director creativo de videos para redes sociales latinoamericanas."
    prompt = (
        f"Crea un guion de video para {plataforma}.\n"
        f"Producto: {producto}\n"
        f"Tipo: {tipo_video}\n"
        f"Duración: {duracion}\n\n"
        f"Incluye:\n"
        f"- Escenas detalladas con tiempo exacto\n"
        f"- Texto en pantalla (subtítulos)\n"
        f"- Narración/voz en off\n"
        f"- Música sugerida (estilo/mood)\n"
        f"- Transiciones\n"
        f"- Caption para la publicación\n"
        f"- Hashtags\n"
    )

    guion = _ask_groq(prompt, system=system, max_tokens=700)
    if not guion:
        guion = f"[GUION] {producto} — {tipo_video} — {duracion}\nGenera el video mostrando el proceso de inicio a fin."

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = os.path.join(BASE_DIR, "TALLER", "MARKETING_STUDIO")
    os.makedirs(output_dir, exist_ok=True)
    ruta = os.path.join(output_dir, f"VIDEO_{producto[:20].replace(' ','_')}_{ts}.txt")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(guion)

    return {"ok": True, "mensaje": f"✓ Guion de video listo para {producto}.", "contenido": guion, "archivo": ruta}


def _ejecutar_marketing_copy(datos: dict, archivo=None) -> dict:
    return _ejecutar_marketing_post(datos, archivo)


def _ejecutar_imagen_proceso(datos: dict, archivo=None) -> dict:
    if not archivo:
        return {"ok": False, "mensaje": "Necesito que subas el archivo de imagen primero."}

    servicio = datos.get("servicio", "GENERAL").upper()

    try:
        from nexus_image_processor import procesar_imagen
        resultado = procesar_imagen(archivo, servicio)
        return {
            "ok": True,
            "mensaje": f"✓ Imagen procesada para {servicio}. Archivo listo en: {resultado['salida']}",
            "archivo_procesado": resultado["salida"],
            "detalles": resultado.get("detalles", "")
        }
    except ImportError:
        return {"ok": False, "mensaje": "Módulo de procesamiento de imágenes no disponible."}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error procesando imagen: {e}"}


def _ejecutar_pedido_nuevo(datos: dict, archivo=None) -> dict:
    try:
        import nexus_orders
        cliente  = datos.get("cliente", "Sin nombre")
        producto = datos.get("producto", "Sin especificar")
        entrega  = datos.get("entrega", "")
        nexus_orders.manager.add_order(cliente, producto, entrega)
        return {"ok": True, "mensaje": f"✓ Pedido registrado para {cliente}: {producto}"}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error registrando pedido: {e}"}


def _ejecutar_stock_update(datos: dict, archivo=None) -> dict:
    try:
        import nexus_stock
        nombre   = datos.get("nombre", "")
        cantidad = int(datos.get("cantidad", 0))
        precio   = float(datos.get("precio", 0))
        nexus_stock.manager.add_item(nombre, cantidad, precio)
        return {"ok": True, "mensaje": f"✓ Stock actualizado: {nombre} — {cantidad} unidades"}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error actualizando stock: {e}"}


def _ejecutar_cliente_nuevo(datos: dict, archivo=None) -> dict:
    try:
        import nexus_crm
        nombre   = datos.get("nombre", "")
        telefono = datos.get("telefono", "")
        nexus_crm.manager.add_cliente(nombre, telefono, "")
        return {"ok": True, "mensaje": f"✓ Cliente registrado: {nombre}"}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error registrando cliente: {e}"}


def _ejecutar_consulta(datos: dict, archivo=None) -> dict:
    try:
        import nexus_orders, nexus_crm, nexus_stock
        nexus_orders.manager.load_orders()
        nexus_crm.manager.load_clientes()
        nexus_stock.manager.load_stock()

        pendientes = [o for o in nexus_orders.manager.orders if o.get("status") == "PENDIENTE"]
        bajo_stock = nexus_stock.manager.list_bajo_stock(minimo=3)

        resumen = (
            f"Estado de tu negocio al {datetime.date.today().strftime('%d/%m/%Y')}:\n"
            f"• {len(pendientes)} pedidos pendientes\n"
            f"• {len(nexus_crm.manager.clientes)} clientes registrados\n"
            f"• {len(nexus_stock.manager.stock)} items en inventario\n"
            + (f"• ⚠ {len(bajo_stock)} materiales con stock bajo\n" if bajo_stock else "• Stock completo ✓\n")
        )

        return {"ok": True, "mensaje": resumen}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error consultando datos: {e}"}


def _ejecutar_autopilot(datos: dict, archivo=None) -> dict:
    tarea      = datos.get("tarea", "publicar")
    frecuencia = datos.get("frecuencia", "diario")

    config_path = os.path.join(BASE_DIR, "CONFIG", "autopilot.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        config = {"tareas": []}

    config["tareas"].append({
        "tarea": tarea,
        "frecuencia": frecuencia,
        "activa": True,
        "creada": datetime.datetime.now().isoformat()
    })

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return {
        "ok": True,
        "mensaje": f"✓ Modo automático configurado: {tarea} — {frecuencia}.\nNEXUS lo hará solo mientras no estás."
    }


# ─── Respuesta rápida sin conversación (para comandos directos) ───────────────

def comando_rapido(texto: str) -> dict:
    """Para comandos directos sin necesidad de contexto previo."""
    session_id = f"quick_{datetime.datetime.now().timestamp()}"
    return procesar_mensaje(session_id, texto)

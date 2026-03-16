# -*- coding: utf-8 -*-
"""Motor 00 — Ayuda contextual: describe capacidades y guia paso a paso."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar

MENU_GENERAL = """NEXUS v2 — Asistente de Taller Simplex

PEDIDOS
  nuevo pedido para [cliente] [descripcion]
  mis pedidos activos
  pedido 5 listo  |  pedido 3 entregado

COTIZACIONES
  cotiza X4  |  cotiza X1 para Carlos
  cotiza 50 tarjetas sublimacion
  cotiza laser 30x20 mdf_3
  genera caja 20x15x8 mdf_3

AGENDA ATF
  agenda instalacion X4 para Juan el viernes
  nueva instalacion X2 para Pedro el martes
  ver agenda atf semana

PIPELINE DE VENTAS
  nuevo prospecto Carlos atf
  ver pipeline  |  mover Carlos a cotizado

MENSAJES Y REDES
  redacta mensaje followup para Carlos
  redacta mensaje listo para Ana
  post de instagram para atf

PROVEEDORES
  proveedores  |  quien surte mdf  |  maquilas

FINANZAS Y REPORTES
  finanzas del mes  |  briefing
  quien no ha pagado

Pregúntame: "cómo registro un pedido", "cómo cotizo", etc."""

GUIAS = {
    "pedido": {
        "claves": ["registr", "creo un pedido", "nuevo pedido", "agreg", "captur"],
        "texto": """Cómo registrar un pedido:

1. Click en el tab Pedidos (arriba)
2. Llena el formulario:
   • Cliente — nombre completo
   • Teléfono — para WhatsApp (opcional)
   • Descripción — qué quiere
   • Servicio — Láser, Sublimación, ATF...
   • Fecha de entrega — cuándo lo necesita
   • Precio — si ya se acordó
   • Notas — detalles internos
3. Click "+ Registrar" o presiona Enter

Por chat también funciona:
  nuevo pedido para María 50 tazas sublimadas"""
    },
    "estado": {
        "claves": ["cambio el estado", "actualizo", "marco listo", "marco entregado", "estado de un pedido"],
        "texto": """Cómo cambiar el estado de un pedido:

En la tabla de Pedidos, cada fila tiene botones:
  ▶  = En proceso (ya estás trabajando)
  ✓  = Listo (terminado, espera al cliente)
  ✔✔ = Entregado (cliente recogió y pagó)
  ✕  = Cancelar (solo el administrador)

Por chat:
  pedido 5 listo
  pedido 3 entregado
  pedido 7 en proceso"""
    },
    "cotizar_atf": {
        "claves": ["cotizo atf", "cotizo faros", "cotizo un kit", "cotizo x", "precio del kit"],
        "texto": """Cómo cotizar ATF (faros):

Opción 1 — Panel:
1. Tab Cotizar → sección "Cotizar ATF"
2. Selecciona el modelo (X1 al X7)
3. Escribe el nombre del cliente (opcional)
4. Click "Cotizar"
5. Aparece precio dist, público y tu ganancia
6. Botón "Copiar mensaje WA" para el cliente

Opción 2 — Chat:
  cotiza X4 para Mario
  cotiza X2
  cotiza X1 para Fernanda"""
    },
    "cotizar_sub": {
        "claves": ["cotizo sublimacion", "cotizo tarjeta", "cotizo taza", "cotizo lona", "cotizo playera"],
        "texto": """Cómo cotizar sublimación:

Por chat (lo más rápido):
  cotiza 50 tarjetas sublimacion
  cotiza 100 tazas sublimacion
  cotiza lona 2x1 sublimacion
  cotiza 30 playeras sublimacion

O desde el panel:
1. Tab Cotizar → sección Sublimación
2. Selecciona el tipo y cantidad
3. Click "Cotizar" """
    },
    "cotizar_laser": {
        "claves": ["cotizo laser", "cotizo corte", "cotizo caja", "genero una caja", "precio laser"],
        "texto": """Cómo cotizar láser / generar caja:

Por chat:
  cotiza laser 30x20 mdf_3       (corte plano)
  genera caja 20x15x8 mdf_3     (caja con tapa)
  cotiza laser 40x30 acrilico

Desde el panel:
1. Tab Cotizar → sección Láser
2. Escribe dimensiones (ej: 30x20 o 20x15x8)
3. Selecciona material
4. Click "Cotizar corte" o "Generar caja DXF" """
    },
    "agenda": {
        "claves": ["agendo", "programo una instalacion", "agenda una cita", "cita atf", "instalo"],
        "texto": """Cómo agendar una instalación ATF:

Por chat:
  agenda instalacion X4 para Juan el viernes
  nueva instalacion X2 para Pedro el martes a las 10

Desde el panel:
1. Tab Agenda ATF
2. Llena: Cliente, Kit, Tipo de carro, Fecha, Hora
3. Click "+ Agendar"

Para ver la agenda:
  ver agenda atf semana"""
    },
    "mensaje": {
        "claves": ["genero un mensaje", "redacto", "mensaje de whatsapp", "mando un mensaje", "escribo a"],
        "texto": """Cómo generar mensajes de WhatsApp:

Por chat:
  redacta mensaje followup para Carlos
  redacta mensaje listo para Ana
  redacta mensaje cotizacion atf para Pedro
  redacta mensaje reactivacion para Luis

Desde el panel:
1. Tab Vendedor → sección "Generar mensaje WhatsApp"
2. Escribe el nombre del cliente
3. Selecciona el tipo de mensaje
4. Click "Generar mensaje"
5. Copia y pega en tu WhatsApp Business

También desde el historial del cliente:
  Click en el nombre del cliente en la tabla de Pedidos"""
    },
    "buscar": {
        "claves": ["busco un pedido", "encuentro un pedido", "busco a", "busco cliente"],
        "texto": """Cómo buscar un pedido o cliente:

En el tab Pedidos:
• Escribe el nombre en la barra de búsqueda
• Filtra automáticamente mientras escribes
• Busca por nombre, descripción o número de pedido

Por chat:
  mis pedidos activos
  pedidos de Carlos

Para ver todo el historial de un cliente:
  Click en su nombre en la tabla (aparece subrayado)"""
    },
    "pipeline": {
        "claves": ["pipeline", "prospecto", "agrego un prospecto", "embudo", "seguimiento a cliente"],
        "texto": """Cómo usar el pipeline de ventas:

Sirve para llevar control de clientes que mostraron interés pero no han comprado.

Agregar prospecto:
  nuevo prospecto Roberto atf
  nuevo prospecto Claudia laser

Ver y mover:
  ver pipeline
  mover Roberto a cotizado

Estados disponibles:
  prospecto → cotizado → seguimiento → cerrado → perdido

Desde el panel:
1. Tab Pipeline
2. Click "+ Agregar" con nombre y servicio
3. Usa el selector para mover su estado"""
    },
    "finanzas": {
        "claves": ["finanzas", "cuanto gane", "ingresos", "ventas del mes", "reporte"],
        "texto": """Cómo ver las finanzas (solo administrador):

Por chat:
  finanzas del mes
  finanzas semana

Desde el panel:
  Click en la tarjeta "Ingresos del mes" en el Resumen

Muestra:
  • Total facturado (pedidos entregados con precio)
  • Pipeline cerrado
  • Ganancia estimada (~45% margen)
  • Pedidos en proceso (dinero por cobrar)"""
    },
    "proveedor": {
        "claves": ["proveedor", "distribuidor", "quien surte", "maquila", "materia prima"],
        "texto": """Cómo usar el directorio de proveedores:

Ver proveedores:
  Tab Proveedores → busca por nombre o producto
  Por chat: proveedores / quien surte mdf / maquilas

Registrar proveedor (solo administrador):
1. Tab Proveedores → formulario de abajo
2. Llena: Nombre, Empresa, WhatsApp, Categoría
3. Qué suministra, precios y tiempo de entrega
4. Click "+ Registrar proveedor"

El WhatsApp de cada proveedor es clickeable directo."""
    },
    "pin": {
        "claves": ["cambio el pin", "cambio mi contraseña", "cambio mi clave", "nuevo pin"],
        "texto": """Cómo cambiar el PIN:

PIN actual:
  Anuar (admin): 1111
  Rocío (operadora): 2222

Para cambiarlo, dile a Anuar — él puede actualizarlo
desde la configuración del sistema.

Recomendación: usa 4 a 6 dígitos que recuerdes fácil."""
    },
}

def _detectar_guia(texto: str) -> dict | None:
    t = texto.lower()
    for key, guia in GUIAS.items():
        if any(k in t for k in guia["claves"]):
            return guia
    return None

@registrar("m00_ayuda")
def ayuda(texto: str = "", **_) -> dict:
    txt = texto.lower()

    # Si pide el manual completo
    if any(w in txt for w in ["manual completo", "manual anuar", "manual rocio",
                               "manual de usuario", "imprime el manual"]):
        return {
            "ok": True,
            "respuesta": "Los manuales están en:\n  C:\\nexus_v2\\MANUAL_ANUAR.md\n  C:\\nexus_v2\\MANUAL_ROCIO.md\n\nPuedes abrirlos con cualquier editor de texto.",
            "datos": {"tipo": "manual"}
        }

    # Detectar pregunta específica "cómo hago X"
    guia = _detectar_guia(txt)
    if guia:
        return {
            "ok": True,
            "respuesta": guia["texto"],
            "datos": {"tipo": "guia"}
        }

    # Menú general
    return {
        "ok": True,
        "respuesta": MENU_GENERAL,
        "datos": {"tipo": "menu"}
    }

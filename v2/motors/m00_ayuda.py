# -*- coding: utf-8 -*-
"""Motor 00 — Ayuda: describe capacidades de NEXUS al usuario."""
import sys
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar

AYUDA = """NEXUS v2 — Asistente de Taller Simplex

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
  ver agenda atf semana
  nueva instalacion atf para Pedro

PIPELINE DE VENTAS
  nuevo prospecto Carlos atf
  ver pipeline
  mover Carlos a cotizado

MENSAJES Y REDES
  redacta mensaje followup para Carlos
  redacta mensaje listo para Ana
  post de instagram para atf

PROVEEDORES
  proveedores  |  quien surte mdf  |  maquilas

FINANZAS Y REPORTES
  finanzas del mes  |  finanzas semana
  briefing  |  quien no ha pagado

DISEÑO (escribe la ruta del archivo)
  vectoriza C:/ruta/logo.png modo bw
  optimiza C:/ruta/imagen.jpg para sublimacion
  convierte C:/ruta/archivo.pdf a png"""

@registrar("m00_ayuda")
def ayuda(texto: str = "", **_) -> dict:
    return {
        "ok": True,
        "respuesta": AYUDA,
        "datos": {"tipo": "ayuda"}
    }

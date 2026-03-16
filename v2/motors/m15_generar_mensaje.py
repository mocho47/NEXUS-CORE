# -*- coding: utf-8 -*-
"""Motor 15 — Generador de Mensajes WhatsApp: follow-up, cotización, promo, reactivación."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from config import GROQ_KEY, GROQ_MODEL

PLANTILLAS = {
    "cotizacion_atf": (
        "Hola {cliente}! Te mando la cotizacion que me pediste para el kit {detalle}. "
        "Precio de instalacion: ${precio}. Incluye mano de obra y garantia. "
        "Tengo disponibilidad esta semana, te agendo?"
    ),
    "cotizacion_laser": (
        "Hola {cliente}! Tu cotizacion de corte laser: {detalle} = ${precio}. "
        "Tiempo de entrega 2-3 dias habiles. "
        "Me mandas el archivo cuando quieras para empezar."
    ),
    "cotizacion_sub": (
        "Hola {cliente}! Cotizacion de {detalle}: ${precio}. "
        "Minimo de pedido y 50% de anticipo para arrancar. "
        "Te mando muestra de diseno primero?"
    ),
    "followup": (
        "Hola {cliente}! Te escribo para ver si tienes alguna pregunta "
        "sobre la cotizacion que te mande. Cualquier duda con gusto te ayudo!"
    ),
    "listo": (
        "Hola {cliente}! Tu pedido de {detalle} ya esta listo para recoger. "
        "Cualquier cosa me avisas. Gracias por tu preferencia!"
    ),
    "reactivacion": (
        "Hola {cliente}! Hace tiempo que no sabemos nada de ti. "
        "Tenemos promociones nuevas en {servicio}. "
        "Te interesa cotizar algo? Con gusto te atiendo."
    ),
}

@registrar("m15_generar_mensaje")
def generar_mensaje(texto: str = "", cliente: str = "", tipo: str = "",
                    detalle: str = "", precio: float = 0,
                    servicio: str = "", **_) -> dict:
    txt = texto.lower()

    # Detectar cliente
    if not cliente:
        m = re.search(r'(?:para|de)\s+([A-ZÁÉÍÓÚa-záéíóú][a-záéíóú]{2,20}(?:\s[A-ZÁÉÍÓÚa-záéíóú][a-záéíóú]{2,20})?)',
                      texto, re.IGNORECASE)
        if m:
            cliente = m.group(1).strip()
    if not cliente:
        cliente = "cliente"

    # Detectar tipo de mensaje
    if not tipo:
        if any(w in txt for w in ["sigue", "seguimiento", "follow", "pregunt"]):
            tipo = "followup"
        elif any(w in txt for w in ["listo", "terminado", "recoger"]):
            tipo = "listo"
        elif any(w in txt for w in ["reactiv", "tiempo sin", "no ha comprado"]):
            tipo = "reactivacion"
        elif "atf" in txt or "faros" in txt or "biled" in txt:
            tipo = "cotizacion_atf"
        elif "laser" in txt or "caja" in txt or "corte" in txt:
            tipo = "cotizacion_laser"
        elif "sub" in txt or "tarjeta" in txt or "lona" in txt:
            tipo = "cotizacion_sub"
        else:
            tipo = "followup"

    # Usar plantilla si está disponible
    plantilla = PLANTILLAS.get(tipo)
    if plantilla:
        try:
            msg = plantilla.format(
                cliente=cliente,
                detalle=detalle or servicio or "tu pedido",
                precio=f"{precio:,.0f}" if precio else "cotizar",
                servicio=servicio or "nuestros servicios"
            )
            return {
                "ok": True,
                "respuesta": f"Mensaje para {cliente}:\n\n{msg}",
                "datos": {"cliente": cliente, "tipo": tipo, "mensaje": msg}
            }
        except Exception:
            pass

    # Si no hay plantilla o necesita personalización → Groq
    if not GROQ_KEY:
        return {"ok": False, "respuesta": "Sin API key de Groq para generar mensaje personalizado."}

    try:
        from groq import Groq
        client_groq = Groq(api_key=GROQ_KEY)
        resp = client_groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "system",
                "content": (
                    "Eres el asistente de ventas de un taller en Guadalajara. "
                    "Negocios: ATF (retrofit faros), Milens (laser y sublimacion), CanbusFix. "
                    "Genera mensajes de WhatsApp: directos, sin relleno, tono amigable mexicano. "
                    "Maximo 3 oraciones. Sin emojis excesivos."
                )
            }, {
                "role": "user",
                "content": f"Genera un mensaje de WhatsApp tipo '{tipo}' para {cliente}. Contexto: {texto}"
            }],
            max_tokens=150,
            temperature=0.7,
        )
        msg = resp.choices[0].message.content.strip()
        return {
            "ok": True,
            "respuesta": f"Mensaje para {cliente}:\n\n{msg}",
            "datos": {"cliente": cliente, "tipo": tipo, "mensaje": msg}
        }
    except Exception as e:
        return {"ok": False, "respuesta": f"Error al generar mensaje: {e}"}

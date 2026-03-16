# -*- coding: utf-8 -*-
"""Motor 16 — Publicaciones para Redes: genera contenido ATF/Milens/CanbusFix para Instagram/TikTok/FB."""
import sys, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from config import GROQ_KEY, GROQ_MODEL, AOZOOM

GANCHOS = {
    "atf": [
        "Tus faros hablan de ti antes de que abras la boca.",
        "No es tunning — es ver mejor en la noche.",
        "El mismo carro. Diferente nivel.",
        "Instalacion profesional en Guadalajara. Garantia incluida.",
    ],
    "laser": [
        "Precision que se nota. Calidad que dura.",
        "Tu idea, hecha realidad en MDF o acrilico.",
        "Corte y grabado laser para tu negocio o regalo.",
        "Personaliza todo. Cotiza sin compromiso.",
    ],
    "sub": [
        "Tu marca en todo lo que tocas.",
        "Tarjetas, lonas, tazas — todo con tu diseno.",
        "Calidad de imprenta, precio de taller.",
        "Impresion sublimacion con colores que duran.",
    ],
    "canbusfix": [
        "Red de instaladores certificados en Mexico.",
        "El retrofit bien hecho. Sin codigos de error.",
        "Solucion canbus para cualquier vehiculo.",
        "Instaladores en tu ciudad. Calidad garantizada.",
    ],
}

@registrar("m16_publicar_redes")
def publicar_redes(texto: str = "", servicio: str = "", red: str = "",
                   precio: float = 0, **_) -> dict:
    txt = texto.lower()

    # Detectar servicio
    if not servicio:
        if any(w in txt for w in ["atf", "faros", "biled", "bi-led", "retrofit"]): servicio = "atf"
        elif any(w in txt for w in ["laser", "caja", "grabado", "corte"]):           servicio = "laser"
        elif any(w in txt for w in ["sub", "tarjeta", "lona", "taza", "playera"]):   servicio = "sub"
        elif "canbusfix" in txt:                                                      servicio = "canbusfix"
        else:                                                                         servicio = "atf"

    # Detectar red
    if not red:
        if "tiktok" in txt:    red = "tiktok"
        elif "facebook" in txt: red = "facebook"
        else:                   red = "instagram"

    # Usar Groq para generar el copy
    if GROQ_KEY:
        try:
            import random
            from groq import Groq
            gancho = random.choice(GANCHOS.get(servicio, GANCHOS["atf"]))
            precio_txt = f" Precio desde ${precio:,.0f} MXN." if precio else ""

            contextos = {
                "atf":       "Retrofit de faros bi-LED en Guadalajara. Marca: ATF by Simplex.",
                "laser":     "Corte y grabado laser en MDF y acrilico. Marca: Creaciones Milens.",
                "sub":       "Sublimacion: tarjetas, lonas, tazas, playeras. Marca: Creaciones Milens.",
                "canbusfix": "Red de instaladores retrofit en Mexico. Marca: CanbusFix by Simplex.",
            }

            client_groq = Groq(api_key=GROQ_KEY)
            resp = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{
                    "role": "system",
                    "content": (
                        f"Eres copywriter de {contextos.get(servicio, 'taller en Guadalajara')}. "
                        f"Red: {red}. "
                        "Genera un post que enganche. "
                        "Formato: gancho potente + descripcion breve + CTA. "
                        "Tono: directo, confiado, mexicano. Maximo 5 lineas. "
                        "Agrega 3-5 hashtags relevantes al final."
                    )
                }, {
                    "role": "user",
                    "content": f"Post para {red} sobre {servicio}.{precio_txt} Gancho sugerido: '{gancho}'"
                }],
                max_tokens=200,
                temperature=0.8,
            )
            post = resp.choices[0].message.content.strip()
            return {
                "ok": True,
                "respuesta": f"Post para {red.capitalize()} ({servicio.upper()}):\n\n{post}",
                "datos": {"red": red, "servicio": servicio, "post": post}
            }
        except Exception as e:
            pass  # fallback a plantilla

    # Fallback sin Groq
    import random
    gancho = random.choice(GANCHOS.get(servicio, GANCHOS["atf"]))
    post = f"{gancho}\n\nContacto: WA 3326148674\n\n#Guadalajara #Simplex #{servicio.upper()}"
    return {
        "ok": True,
        "respuesta": f"Post para {red.capitalize()}:\n\n{post}",
        "datos": {"red": red, "servicio": servicio, "post": post}
    }

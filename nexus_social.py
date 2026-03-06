import sys
import os
import json
try:
    import pyperclip
except ImportError:
    pyperclip = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_NEGOCIO_PATH = os.path.join(BASE_DIR, "CONFIG", "negocio.json")

# Plantillas de Venta (Psychological Triggers)
TEMPLATES = {
    "retrofit_premium": """
🔥 {titulo} 🔥

¿Sientes que tu {auto} no impone respeto de noche? ¿O peor, no ves nada en carretera?

Nos llegó este proyecto y el cambio es BRUTAL. 👇

❌ ANTES: Iluminación pobre, halógeno amarillento, look "viejo".
✅ DESPUÉS (Retrofit Profesional):
- {componentes}
- {beneficio_clave}
- Estética renovada y funcional.

⚠️ OJO: Esto no es "cambiar focos". Es ingeniería inversa aplicada a tus faros. Abrimos, modificamos y sellamos mejor que de fábrica. Cero humedad, cero problemas.

📍 Servicio exclusivo en Guadalajara/Zapopan.
📲 Mándame mensaje directo para cotizar tu nave: https://wa.me/{wa_number}
🌐 Galería de trabajos: {instagram}
🎥 Videos: {tiktok}

#RetrofitGDL #IluminacionAutomotriz #{modelo_auto} #TuningMexico #Zapopan #CalidadNoCantidad
""",

    "laser_industrial": """
🏭 CORTE LÁSER DE PRECISIÓN EN GDL 🏭

¿Necesitas maquila rápida, limpia y sin "peros"?

En {nombre_negocio} resolvemos:
✅ Corte y Grabado en MDF, Acrílico, Piel y más.
✅ Proyectos urgentes (si urge, sale).
✅ Diseños personalizados desde cero.

Ideal para: Emprendedores, Decoración, Señalética y Regalos Corporativos.

💡 ¿No tienes el diseño? Nosotros lo hacemos.
📍 Entrega en punto medio o taller.

Cotiza en segundos aquí 👇
📲 https://wa.me/{wa_number}

#CorteLaserGDL #MDF #DiseñoIndustrial #EmprendedoresGDL #MaquilaLaser
""",

    "dtf_textil": """
👕 PERSONALIZACIÓN PREMIUM EN GDL — DTF Y VINIL 👕

¿Quieres tu logo o diseño en playeras, gorras o uniformes?

En {nombre_negocio} lo hacemos realidad:
✅ Impresión DTF de alta definición — colores que duran lavadas.
✅ Vinil textil y transfer para todo tipo de tela.
✅ Mínimo 1 pieza. Sin mínimos de pedido.

💡 ¿No tienes diseño? Nosotros lo creamos.
⚡ Entrega express disponible.

👇 Cotiza sin compromiso:
📲 https://wa.me/{wa_number}

#DTFGdl #PersonalizacionTextil #PlayerasPersonalizadas #EmprendedoresGDL #UniformesGDL
""",

    "neon_led": """
✨ LETREROS DE NEÓN LED PERSONALIZADOS ✨

De la idea al letrero — nosotros hacemos todo.

En {nombre_negocio} diseñamos y fabricamos:
💡 Neón Flex LED en cualquier color y forma.
💡 Nombres, logos, frases, coronas... lo que imagines.
💡 Ideal para: estudios de foto, restaurantes, salones, regalos únicos.

🎨 Proceso completo:
1️⃣ Nos mandas el texto o diseño.
2️⃣ Te enviamos simulación digital GRATIS.
3️⃣ Fabricamos y entregamos.

📲 Cotiza tu letrero aquí:
https://wa.me/{wa_number}

#NeonLedGDL #LetrerosPersonalizados #NeonGDL #DecoracionGDL #RegaloOriginal
""",

    "sublimacion": """
🎨 SUBLIMACIÓN Y PERSONALIZACIÓN EN GDL 🎨

¿Buscas regalos únicos o productos con tu marca?

En {nombre_negocio} personalizamos:
✅ Tazas, termos, gorras, playeras y más.
✅ Entrega rápida — ideal para pedidos urgentes.
✅ Diseño incluido o trae el tuyo.

Cotiza sin compromiso 👇
📲 https://wa.me/{wa_number}
{horario}

#SublimacionGDL #PersonalizacionGDL #RegalosCorporativos #EmprendedoresGDL
""",
    # ── NEGOCIOS SIMPLEX ─────────────────────────────────────────────────────
    "atf_retrofit": """🔦 ¿Ya viste cómo quedó este {vehiculo}?

ANTES: focos amarillos que no iluminan nada.
DESPUÉS: Bi-LED profesional, nitidez total, look premium.

✅ Instalación en 1 día
✅ Garantía incluida
✅ Tecnología Aozoom | Illume

📍 Guadalajara · {nombre_negocio}
📱 WhatsApp: wa.me/{wa_number}

#RetrofitFaros #BiLED #ATF #FarosGDL #Guadalajara #Aozoom #TuningGDL""",

    "milens_laser": """✂️ Mira lo que salió del láser hoy 😍

{descripcion_pieza}

🪵 Material: {material}
📐 Medidas: {medidas}
⏱️ Entrega: {entrega}

¿Quieres algo personalizado? Escríbenos.
Hacemos desde 1 pieza.

📱 {wa_number} | {nombre_negocio}
📍 Guadalajara, Jalisco

#MDF #CorteLaser #PersonalizadoMDF #AcrilicoCortado #MilensGDL #Laser #RegaloPersonalizado""",

    "canbusfix_instalador": """🔧 ¿Instalas faros retrofit?

Únete a CanbusFix y accede a:
✅ Catálogo mayorista con precios reales
✅ Soporte técnico de instaladores reales
✅ Capacitación y tutoriales exclusivos
✅ Certificación CanbusFix para tu negocio

👉 3 niveles: Básico (gratis) · Pro ($299/mes) · Elite ($599/mes)

Más de {num_instaladores}+ instaladores activos en México.
¿Cuándo te unes?

📱 {wa_number}
#CanbusFix #RetrofitFaros #InstaladorRetrofit #BiLED #TallerGDL #Aozoom""",

}


def _load_negocio() -> dict:
    try:
        if os.path.exists(_NEGOCIO_PATH):
            with open(_NEGOCIO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _wa_number(telefono: str) -> str:
    """Normaliza el teléfono a formato wa.me (sin +, sin espacios)."""
    t = str(telefono).strip().replace(" ", "").replace("-", "").lstrip("+")
    if not t:
        return ""
    # Si es 10 dígitos MX sin prefijo, añadir 52
    if len(t) == 10 and t.isdigit():
        t = "52" + t
    return t


def generar_copy(tipo: str, datos: dict) -> str:
    """Genera copy de redes sociales rellenando la plantilla con datos.

    Los campos de negocio (wa_number, nombre_negocio, instagram, tiktok, horario)
    se inyectan automáticamente desde negocio.json si no están en datos.
    """
    template = TEMPLATES.get(tipo)
    if not template:
        return f"Error: Tipo '{tipo}' no reconocido. Disponibles: {list(TEMPLATES.keys())}"

    negocio = _load_negocio()
    tel = negocio.get("telefono", "")
    redes = negocio.get("redes", {})
    ig = redes.get("instagram", "")
    tt = redes.get("tiktok", "")

    defaults = {
        "wa_number": _wa_number(tel),
        "nombre_negocio": negocio.get("nombre", "Nexus Taller"),
        "instagram": f"https://www.instagram.com/{ig.lstrip('@')}/" if ig else "Instagram no configurado",
        "tiktok": f"https://www.tiktok.com/@{tt.lstrip('@')}/" if tt else "TikTok no configurado",
        "horario": negocio.get("horario", ""),
        # Valores por defecto para campos que el caller debe proveer
        "titulo": datos.get("titulo", "Proyecto"),
        "auto": datos.get("auto", "tu auto"),
        "modelo_auto": datos.get("modelo_auto", "Auto"),
        "componentes": datos.get("componentes", "Componentes de alta calidad"),
        "beneficio_clave": datos.get("beneficio_clave", "Resultados garantizados"),
    }
    defaults.update(datos)  # datos del caller tienen precedencia

    try:
        return template.format(**defaults)
    except KeyError as e:
        return f"Error en plantilla: falta el campo {e}"


def whatsapp_url(mensaje: str) -> str:
    """Genera URL de WhatsApp con mensaje pre-rellenado."""
    import urllib.parse
    negocio = _load_negocio()
    tel = _wa_number(negocio.get("telefono", ""))
    encoded = urllib.parse.quote(mensaje)
    if tel:
        return f"https://wa.me/{tel}?text={encoded}"
    return f"https://wa.me/?text={encoded}"


if __name__ == "__main__":
    tipo = sys.argv[1] if len(sys.argv) > 1 else "retrofit_premium"
    datos = {
        "titulo": "TRANSFORMACIÓN TOTAL: AUDI A6",
        "auto": "Audi A6",
        "modelo_auto": "AudiA6",
        "componentes": "Lupas Bi-LED de Alta Potencia + Ojos de Ángel",
        "beneficio_clave": "300% más luz en carretera sin deslumbrar",
    }
    texto = generar_copy(tipo, datos)
    print(texto)
    if pyperclip:
        pyperclip.copy(texto)
        print("\n[COPIADO AL PORTAPAPELES]")


# ── API NEGOCIOS ──────────────────────────────────────────────────────────────

DATOS_NEGOCIO_DEFAULT = {
    "atf": {
        "nombre_negocio": "ATF by Simplex",
        "wa_number": "3326148674",
        "vehiculo": "Nissan NP300",
        "descripcion": "Retrofit bi-LED profesional"
    },
    "milens": {
        "nombre_negocio": "Milens by Simplex",
        "wa_number": "3326148674",
        "descripcion_pieza": "Caja con tapa en MDF 6mm",
        "material": "MDF 6mm",
        "medidas": "20x15x10cm",
        "entrega": "48 horas"
    },
    "canbusfix": {
        "nombre_negocio": "CanbusFix",
        "wa_number": "3326148674",
        "num_instaladores": "150"
    }
}

TEMPLATE_POR_NEGOCIO = {
    "atf":       "atf_retrofit",
    "milens":    "milens_laser",
    "canbusfix": "canbusfix_instalador"
}

def generar_post_negocio(negocio: str, datos_extra: dict = None) -> dict:
    """Genera caption listo para pegar en Instagram/TikTok para ATF, Milens o CanbusFix."""
    negocio = negocio.lower().strip()
    if negocio not in TEMPLATE_POR_NEGOCIO:
        return {"ok": False, "error": f"Negocio '{negocio}' no reconocido. Usa: atf, milens, canbusfix"}
    tipo = TEMPLATE_POR_NEGOCIO[negocio]
    datos = dict(DATOS_NEGOCIO_DEFAULT.get(negocio, {}))
    if datos_extra:
        datos.update(datos_extra)
    caption = generar_copy(tipo, datos)
    wa_url  = whatsapp_url(f"Hola! Quiero cotizar con {datos.get('nombre_negocio','')}")
    return {
        "ok": True,
        "negocio": negocio,
        "caption": caption,
        "caracteres": len(caption),
        "wa_url": wa_url,
        "instruccion": "Copia el caption, abre Instagram y pégalo en tu nueva publicación"
    }

def abrir_instagram_web(negocio: str = "") -> dict:
    """Abre Instagram en el navegador para publicar manualmente."""
    try:
        import webbrowser, subprocess
        url = "https://www.instagram.com/create/style/"
        webbrowser.open(url)
        return {"ok": True, "url": url, "nota": "Instagram abierto — pega el caption generado"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_templates_disponibles() -> list:
    """Lista todos los templates disponibles."""
    return [
        {"id": k, "negocio": k.split("_")[0], "nombre": k.replace("_"," ").title()}
        for k in TEMPLATES.keys()
    ]

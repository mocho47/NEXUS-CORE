"""
nexus_galeria.py — Galería de experiencias ambientales de NEXUS.

MODELO DE NEGOCIO:
  ┌─────────────────┬──────────┬───────────┬────────────────────────────────────┐
  │ Plan            │ Audio/mes│ Visual/mes│ Notas                              │
  ├─────────────────┼──────────┼───────────┼────────────────────────────────────┤
  │ DEMO            │   VER*   │   VER*    │ Ve el catálogo completo, usa 0     │
  │ LITE (1 año)    │    5     │    3      │ Categorías INTRO / TRABAJO         │
  │ PRO  (3 años)   │   15     │    8      │ Hasta categoría PREMIUM            │
  │ FULL (10 años)  │    ∞     │    ∞      │ Toda la galería, uso ilimitado      │
  │ ADMIN           │    ∞     │    ∞      │ Sin restricciones                  │
  └─────────────────┴──────────┴───────────┴────────────────────────────────────┘

  *DEMO: puede ver y preescuchar previewde 10s pero NO activar experiencias completas.

CONTENIDO EXTRA:
  Si el usuario excede su cuota, puede comprar activaciones adicionales.
  Precio: $100 MXN por activación (audio o visual).

CATÁLOGO:
  40 experiencias de audio binaural + mensajes de voz
   8 experiencias visuales (fondos generativos CSS/Canvas)

AVISO LEGAL:
  El uso de tonos binaurales es responsabilidad exclusiva del usuario.
  No recomendado para personas con epilepsia, trastornos auditivos
  o bajo tratamiento psiquiátrico. NEXUS no asume responsabilidad.
"""

import os
import json
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
USO_PATH   = os.path.join(CONFIG_DIR, "galeria_uso.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

# ── Cuotas por plan ───────────────────────────────────────────────────────────

CUOTAS = {
    "DEMO":     {"audio": 0,    "visual": 0,    "precio_extra": 100},
    "LITE":     {"audio": 5,    "visual": 3,    "precio_extra": 100},
    "PRO":      {"audio": 15,   "visual": 8,    "precio_extra": 100},
    "FULL":     {"audio": 9999, "visual": 9999, "precio_extra": 0},
    "ADMIN":    {"audio": 9999, "visual": 9999, "precio_extra": 0},
    "INVALIDA": {"audio": 0,    "visual": 0,    "precio_extra": 100},
}

ACCESO_CATEGORIA = {
    "NEXUS":       ["DEMO", "LITE", "PRO", "FULL", "ADMIN"],
    "INTRO":       ["LITE", "PRO", "FULL", "ADMIN"],
    "TRABAJO":     ["LITE", "PRO", "FULL", "ADMIN"],
    "CREATIVIDAD": ["LITE", "PRO", "FULL", "ADMIN"],
    "AUTOESTIMA":  ["LITE", "PRO", "FULL", "ADMIN"],
    "VENTAS":      ["LITE", "PRO", "FULL", "ADMIN"],
    "BIENESTAR":   ["PRO",  "FULL", "ADMIN"],
    "SUEÑO":       ["PRO",  "FULL", "ADMIN"],
    "SANACION":    ["PRO",  "FULL", "ADMIN"],
    "PREMIUM":     ["PRO",  "FULL", "ADMIN"],
    "PARANORMAL":  ["FULL", "ADMIN"],
}

# ── Catálogo de 40 audios ─────────────────────────────────────────────────────

def _msgs(lista):
    """Helper para construir lista de mensajes."""
    return [{"cat": c, "txt": t} for c, t in lista]

CATALOGO_AUDIO = [
    # ── NEXUS (1) ─────────────────────────────────────────────────────────────
    {
        "id": "A01", "nombre": "Ambiente NEXUS", "categoria": "NEXUS",
        "beat_hz": 7.83, "hz_L": 200.0, "hz_R": 207.83,
        "color": "#00ff88", "icono": "◈",
        "beneficio": "Estado base de NEXUS. Resonancia Schumann 7.83Hz — receptividad natural.",
        "descripcion": "La frecuencia original de NEXUS. Incluida en todos los planes. Ideal para el trabajo cotidiano.",
        "mensajes": _msgs([
            ("ADQ","NEXUS es tu ventaja competitiva real"),
            ("ADQ","Las herramientas correctas determinan hasta dónde llegas"),
            ("ADQ","Invertir en lo correcto siempre genera más de lo que cuesta"),
            ("REC","Tu comunidad merece conocer esta herramienta"),
            ("REC","Los líderes comparten lo que funciona con quienes confían en ellos"),
            ("SUP","Eres un emprendedor que construye algo real con sus propias manos"),
            ("SUP","Cada pedido completado es evidencia de que tu negocio funciona"),
            ("SUP","Tu trabajo tiene valor. Tu tiempo tiene valor. Tú tienes valor."),
        ]),
    },
    # ── INTRO / TRABAJO (8) ──────────────────────────────────────────────────
    {
        "id": "A02", "nombre": "Foco Profundo", "categoria": "TRABAJO",
        "beat_hz": 14.0, "hz_L": 200.0, "hz_R": 214.0,
        "color": "#0088ff", "icono": "◎",
        "beneficio": "Concentración Beta 14Hz para trabajo analítico sostenido.",
        "descripcion": "Activa el estado Beta de alta concentración. Elimina distracciones mentales.",
        "mensajes": _msgs([
            ("SUP","Tu mente está completamente enfocada en lo que importa ahora"),
            ("SUP","Cada decisión que tomas hoy construye tu negocio de mañana"),
            ("ADQ","La claridad mental es la herramienta más poderosa del emprendedor"),
            ("SUP","Tienes todo lo que necesitas para resolver esto"),
        ]),
    },
    {
        "id": "A03", "nombre": "Flujo Creativo", "categoria": "CREATIVIDAD",
        "beat_hz": 6.0, "hz_L": 200.0, "hz_R": 206.0,
        "color": "#aa00ff", "icono": "◉",
        "beneficio": "Estado de flujo creativo. Theta 6Hz para diseño e ideas originales.",
        "descripcion": "El estado Theta es donde nacen las ideas más valiosas. Para diseñar, crear contenido o imaginar nuevos servicios.",
        "mensajes": _msgs([
            ("SUP","Las ideas que tienes ahora pueden cambiar tu negocio para siempre"),
            ("SUP","Tu creatividad no tiene límites cuando confías en ella"),
            ("ADQ","Crear es la forma más poderosa de dejar tu huella en el mundo"),
            ("SUP","Cada diseño tuyo lleva una parte de ti que el cliente va a sentir"),
        ]),
    },
    {
        "id": "A04", "nombre": "Confianza Total", "categoria": "AUTOESTIMA",
        "beat_hz": 10.0, "hz_L": 200.0, "hz_R": 210.0,
        "color": "#ffaa00", "icono": "★",
        "beneficio": "Autoconfianza y autoridad. Alpha 10Hz para presencia poderosa.",
        "descripcion": "Para cerrar ventas, hablar con clientes o presentar tu negocio. Construye seguridad genuina.",
        "mensajes": _msgs([
            ("SUP","Eres exactamente la persona correcta para dirigir este negocio"),
            ("SUP","Tu experiencia y dedicación son irrefutables"),
            ("ADQ","La confianza que transmites es la que tus clientes compran primero"),
            ("SUP","No necesitas la aprobación de nadie para saber lo que vales"),
        ]),
    },
    {
        "id": "A05", "nombre": "Energía de Ventas", "categoria": "VENTAS",
        "beat_hz": 18.0, "hz_L": 200.0, "hz_R": 218.0,
        "color": "#ff4400", "icono": "⚡",
        "beneficio": "Estado óptimo para cerrar tratos. Beta 18Hz de alta acción.",
        "descripcion": "El estado mental ideal para ventas: alerta, energético, positivo. Úsalo antes de atender clientes.",
        "mensajes": _msgs([
            ("ADQ","Cada conversación con un cliente es una oportunidad real"),
            ("REC","Cuando ayudas a tu cliente a ganar, él te recomendará siempre"),
            ("ADQ","Tu producto resuelve problemas reales. Eso tiene valor incalculable."),
            ("SUP","Eres un vendedor natural porque crees en lo que ofreces"),
        ]),
    },
    {
        "id": "A06", "nombre": "Motivación Diaria", "categoria": "AUTOESTIMA",
        "beat_hz": 8.0, "hz_L": 200.0, "hz_R": 208.0,
        "color": "#00ddff", "icono": "◆",
        "beneficio": "Motivación sostenida. Alpha 8Hz de propósito renovado.",
        "descripcion": "Para los días difíciles. Recuerda por qué empezaste y activa la energía para seguir.",
        "mensajes": _msgs([
            ("SUP","Emprender es el acto más valiente que existe. Tú lo haces cada día."),
            ("SUP","Los obstáculos de hoy son las historias de éxito de mañana"),
            ("SUP","Cada día que abres tu negocio estás ganando la batalla más importante"),
            ("SUP","Tu persistencia es más poderosa que cualquier talento natural"),
        ]),
    },
    {
        "id": "A07", "nombre": "Descanso Activo", "categoria": "BIENESTAR",
        "beat_hz": 2.5, "hz_L": 200.0, "hz_R": 202.5,
        "color": "#336699", "icono": "◌",
        "beneficio": "Recuperación mental profunda. Delta 2.5Hz para pausas restauradoras.",
        "descripcion": "10 minutos con este audio equivalen a una hora de descanso ordinario. Para pausas entre tareas intensas.",
        "mensajes": _msgs([
            ("SUP","Descansar es parte del trabajo. Los mejores lo saben."),
            ("SUP","Tu cuerpo y mente se están renovando en este momento"),
            ("SUP","Regresarás más fuerte, más claro y más capaz"),
        ]),
    },
    {
        "id": "A08", "nombre": "Zona Gamma", "categoria": "PREMIUM",
        "beat_hz": 40.0, "hz_L": 200.0, "hz_R": 240.0,
        "color": "#ffdd00", "icono": "✦",
        "beneficio": "Rendimiento máximo. Gamma 40Hz — frecuencia de insights y procesamiento de alto nivel.",
        "descripcion": "Para sesiones intensas de estrategia. El estado donde los mejores toman decisiones rápidas y correctas.",
        "mensajes": _msgs([
            ("SUP","Tu cerebro opera ahora en su máxima capacidad"),
            ("ADQ","Las soluciones que buscas ya están en tu mente"),
            ("SUP","Eres capaz de más de lo que cualquier cifra puede medir"),
        ]),
    },
    {
        "id": "A09", "nombre": "Abundancia", "categoria": "PREMIUM",
        "beat_hz": 7.0, "hz_L": 200.0, "hz_R": 207.0,
        "color": "#88ff44", "icono": "◈",
        "beneficio": "De escasez a prosperidad. Theta 7Hz de mentalidad abundante.",
        "descripcion": "Reemplaza el 'no tengo suficiente' con 'tengo lo que necesito para crecer'.",
        "mensajes": _msgs([
            ("ADQ","La abundancia fluye hacia quien está preparado para recibirla"),
            ("SUP","Tu negocio tiene capacidad ilimitada de crecer"),
            ("ADQ","Cada inversión inteligente multiplica lo que ya tienes"),
            ("SUP","Mereces prosperar. Tu esfuerzo lo justifica completamente."),
        ]),
    },
    {
        "id": "A10", "nombre": "Conexión con Clientes", "categoria": "VENTAS",
        "beat_hz": 12.0, "hz_L": 200.0, "hz_R": 212.0,
        "color": "#00ffaa", "icono": "◉",
        "beneficio": "Empatía e inteligencia social. Alpha 12Hz para relaciones duraderas.",
        "descripcion": "Para atención al cliente, resolver conflictos o construir relaciones a largo plazo.",
        "mensajes": _msgs([
            ("REC","Cada cliente que cuidas bien se convierte en tu embajador"),
            ("ADQ","La relación con tus clientes es tu mayor activo real"),
            ("REC","Un cliente feliz trae tres clientes nuevos. Siempre."),
            ("SUP","Tu capacidad de conectar con las personas es un don genuino"),
        ]),
    },
    {
        "id": "A11", "nombre": "Transformación Total", "categoria": "PREMIUM",
        "beat_hz": 6.0, "hz_L": 200.0, "hz_R": 206.0,
        "color": "#ff00aa", "icono": "✦",
        "beneficio": "Cambio de identidad profundo. Theta para transformación de creencias limitantes.",
        "descripcion": "Para momentos clave: nuevo servicio, nuevo mercado, reinventarte. No para uso diario.",
        "mensajes": _msgs([
            ("SUP","La versión de ti que tiene el negocio que sueñas ya existe. Estás convirtiéndote en ella."),
            ("ADQ","Tu negocio es el reflejo de quién decides ser cada día"),
            ("SUP","La transformación ya comenzó. No puedes volver atrás."),
        ]),
    },
    {
        "id": "A12", "nombre": "Frecuencia Paranormal", "categoria": "PARANORMAL",
        "beat_hz": 100.0, "hz_L": 200.0, "hz_R": 300.0,
        "color": "#550088", "icono": "✧",
        "beneficio": "Gamma extremo 100Hz. Exploración de estados no ordinarios de conciencia.",
        "descripcion": "Territorio de intuición extrema. No recomendado para principiantes. Solo usuarios avanzados.",
        "mensajes": _msgs([
            ("SUP","Tu intuición es más poderosa que cualquier análisis racional"),
            ("ADQ","La ventaja de los extraordinarios está en lo que perciben que otros ignoran"),
        ]),
    },
    # ── SUEÑO (3) ─────────────────────────────────────────────────────────────
    {
        "id": "A13", "nombre": "Sueño Profundo", "categoria": "SUEÑO",
        "beat_hz": 1.0, "hz_L": 200.0, "hz_R": 201.0,
        "color": "#223355", "icono": "◌",
        "beneficio": "Inducción al sueño profundo. Delta 1Hz para descanso máximo.",
        "descripcion": "Usar al acostarse. Facilita el paso por las fases del sueño profundo restaurador. Sin mensajes de voz.",
        "mensajes": [],
    },
    {
        "id": "A14", "nombre": "Sueño Lúcido", "categoria": "SUEÑO",
        "beat_hz": 4.0, "hz_L": 200.0, "hz_R": 204.0,
        "color": "#334466", "icono": "◉",
        "beneficio": "Umbral sueño-vigilia. Theta 4Hz — zona de hipnagogia y sueños conscientes.",
        "descripcion": "Para quienes practican sueño lúcido o meditación profunda. Uso avanzado.",
        "mensajes": _msgs([("SUP","Tu mente está despierta. Tu cuerpo descansa completamente.")]),
    },
    {
        "id": "A15", "nombre": "Siesta Power", "categoria": "BIENESTAR",
        "beat_hz": 3.0, "hz_L": 200.0, "hz_R": 203.0,
        "color": "#445577", "icono": "◎",
        "beneficio": "Descanso reparador en 20 minutos. Delta-Theta 3Hz.",
        "descripcion": "La siesta de 20 minutos más eficiente de tu vida. No más, no menos — activa el timer de tu teléfono.",
        "mensajes": _msgs([("SUP","20 minutos de descanso real valen más que 2 horas de fatiga fingida")]),
    },
    # ── SANACIÓN (3) ──────────────────────────────────────────────────────────
    {
        "id": "A16", "nombre": "Frecuencia 432Hz", "categoria": "SANACION",
        "beat_hz": 5.0, "hz_L": 432.0, "hz_R": 437.0,
        "color": "#44aa88", "icono": "◈",
        "beneficio": "Armonía natural. 432Hz — frecuencia de la naturaleza según investigadores.",
        "descripcion": "Usar en momentos de estrés o tensión. La diferencia entre 440Hz (estándar) y 432Hz es percibida como más cálida y armoniosa.",
        "mensajes": _msgs([
            ("SUP","Estás en armonía con todo lo que eres"),
            ("SUP","Tu cuerpo sabe exactamente cómo restaurarse"),
        ]),
    },
    {
        "id": "A17", "nombre": "Liberación Emocional", "categoria": "SANACION",
        "beat_hz": 3.5, "hz_L": 200.0, "hz_R": 203.5,
        "color": "#558844", "icono": "◉",
        "beneficio": "Liberación de tensión emocional. Theta-Delta 3.5Hz.",
        "descripcion": "Para después de días difíciles, discusiones o situaciones de alto estrés. Permite la recuperación emocional.",
        "mensajes": _msgs([
            ("SUP","Tienes el derecho de soltar lo que ya no te sirve"),
            ("SUP","Cada emoción que reconoces pierde el poder que tenía sobre ti"),
        ]),
    },
    {
        "id": "A18", "nombre": "Frecuencia 528Hz", "categoria": "SANACION",
        "beat_hz": 6.0, "hz_L": 528.0, "hz_R": 534.0,
        "color": "#00bb66", "icono": "★",
        "beneficio": "Frecuencia del amor y la reparación. 528Hz — usada en investigación de bienestar.",
        "descripcion": "Conocida como la frecuencia del amor. Investigadores la asocian con estados de apertura y bienestar profundo.",
        "mensajes": _msgs([
            ("SUP","Mereces amor, comenzando por el tuyo propio"),
            ("SUP","Lo que construyes viene de un lugar genuino de amor por tu trabajo"),
        ]),
    },
    # ── ESTUDIO / APRENDIZAJE (4) ─────────────────────────────────────────────
    {
        "id": "A19", "nombre": "Memoria Activa", "categoria": "TRABAJO",
        "beat_hz": 12.0, "hz_L": 200.0, "hz_R": 212.0,
        "color": "#4488cc", "icono": "◎",
        "beneficio": "Retención de información. Alpha-Beta 12Hz para aprendizaje eficiente.",
        "descripcion": "Para estudiar, leer o aprender nuevas habilidades. Potencia la retención sin sobreestimulación.",
        "mensajes": _msgs([
            ("SUP","Tu mente retiene fácilmente lo que vale la pena recordar"),
            ("ADQ","Aprender es la inversión con mayor retorno de todas"),
        ]),
    },
    {
        "id": "A20", "nombre": "Superlearning", "categoria": "PREMIUM",
        "beat_hz": 8.0, "hz_L": 200.0, "hz_R": 208.0,
        "color": "#88aaff", "icono": "✦",
        "beneficio": "Estado Superlearning. Alpha 8Hz — asociado con aprendizaje acelerado.",
        "descripcion": "Técnica utilizada desde los años 70. El Alpha 8Hz facilita absorción de información a velocidades superiores.",
        "mensajes": _msgs([
            ("SUP","Tu capacidad de aprender y adaptarte es tu mayor ventaja"),
            ("ADQ","Quien más aprende en menos tiempo gana siempre"),
        ]),
    },
    {
        "id": "A21", "nombre": "Resolución de Problemas", "categoria": "TRABAJO",
        "beat_hz": 10.0, "hz_L": 200.0, "hz_R": 210.0,
        "color": "#88ccff", "icono": "◆",
        "beneficio": "Pensamiento lateral y soluciones creativas. Alpha 10Hz.",
        "descripcion": "Para cuando estás atascado. Activa el pensamiento divergente que encuentra soluciones no obvias.",
        "mensajes": _msgs([
            ("SUP","La solución ya existe. Solo necesitas el estado mental correcto para verla."),
            ("SUP","Cada problema que resuelves hace a tu negocio más sólido"),
        ]),
    },
    {
        "id": "A22", "nombre": "Claridad Mental", "categoria": "TRABAJO",
        "beat_hz": 15.0, "hz_L": 200.0, "hz_R": 215.0,
        "color": "#99eeff", "icono": "◎",
        "beneficio": "Pensamiento claro y organizado. Beta 15Hz para análisis y toma de decisiones.",
        "descripcion": "Para momentos de confusión o sobrecarga de información. Restaura el pensamiento lineal y claro.",
        "mensajes": _msgs([
            ("SUP","La claridad es el primer paso hacia la acción correcta"),
            ("SUP","Decides con información, no con miedo"),
        ]),
    },
    # ── LIDERAZGO / NEGOCIOS (5) ──────────────────────────────────────────────
    {
        "id": "A23", "nombre": "Liderazgo Auténtico", "categoria": "PREMIUM",
        "beat_hz": 9.0, "hz_L": 200.0, "hz_R": 209.0,
        "color": "#ff8800", "icono": "★",
        "beneficio": "Presencia de liderazgo. Alpha 9Hz de autoridad natural.",
        "descripcion": "Para dirigir equipos, tomar decisiones estratégicas o enfrentar situaciones que requieren liderazgo.",
        "mensajes": _msgs([
            ("SUP","Líderes auténticos no necesitan demostrar nada — su presencia lo dice todo"),
            ("ADQ","Tu ejemplo es más poderoso que cualquier instrucción"),
            ("SUP","Cada decisión que tomas deja una huella en quienes te rodean"),
        ]),
    },
    {
        "id": "A24", "nombre": "Negociación Ganadora", "categoria": "VENTAS",
        "beat_hz": 16.0, "hz_L": 200.0, "hz_R": 216.0,
        "color": "#ff6600", "icono": "⚡",
        "beneficio": "Estado óptimo para negociar. Beta 16Hz de enfoque táctico.",
        "descripcion": "Antes de cotizar, negociar precios o cerrar contratos importantes. Activa la mente táctica.",
        "mensajes": _msgs([
            ("SUP","Negocias desde la posición de quien tiene valor real que ofrecer"),
            ("ADQ","Un acuerdo justo beneficia a ambas partes. Ese es tu objetivo."),
        ]),
    },
    {
        "id": "A25", "nombre": "Visión Estratégica", "categoria": "PREMIUM",
        "beat_hz": 5.5, "hz_L": 200.0, "hz_R": 205.5,
        "color": "#cc4400", "icono": "◈",
        "beneficio": "Pensamiento de largo plazo. Theta 5.5Hz para planificación estratégica.",
        "descripcion": "Para planear el futuro de tu negocio, imaginar nuevos mercados o diseñar estrategias a largo plazo.",
        "mensajes": _msgs([
            ("ADQ","Los negocios que perduran son los que pueden ver más allá del mes siguiente"),
            ("SUP","Tu visión es tu mapa. Tu acción es el vehículo."),
        ]),
    },
    {
        "id": "A26", "nombre": "Resiliencia Empresarial", "categoria": "AUTOESTIMA",
        "beat_hz": 8.5, "hz_L": 200.0, "hz_R": 208.5,
        "color": "#dd6600", "icono": "◆",
        "beneficio": "Fortaleza ante adversidades. Alpha 8.5Hz de resiliencia.",
        "descripcion": "Para cuando el negocio golpea. Activa la recuperación rápida y el aprendizaje de las crisis.",
        "mensajes": _msgs([
            ("SUP","Todo emprendedor que triunfó primero sobrevivió. Tú ya sabes cómo."),
            ("SUP","Lo que no te rompe, literalmente te hace más fuerte"),
            ("ADQ","La resiliencia es el activo más valioso de cualquier empresario"),
        ]),
    },
    {
        "id": "A27", "nombre": "Innovación Continua", "categoria": "CREATIVIDAD",
        "beat_hz": 7.0, "hz_L": 200.0, "hz_R": 207.0,
        "color": "#bb00ff", "icono": "✦",
        "beneficio": "Mentalidad innovadora. Theta 7Hz para pensamiento disruptivo.",
        "descripcion": "Para generar ideas nuevas de productos, servicios o procesos. Rompe los patrones del pensamiento habitual.",
        "mensajes": _msgs([
            ("SUP","Las mejores ideas de tu industria aún no han sido pensadas. Tú puedes pensar alguna."),
            ("ADQ","Innovar no es solo tecnología. Es ver lo ordinario de forma extraordinaria."),
        ]),
    },
    # ── CRECIMIENTO PERSONAL (6) ──────────────────────────────────────────────
    {
        "id": "A28", "nombre": "Amor Propio", "categoria": "SANACION",
        "beat_hz": 6.5, "hz_L": 200.0, "hz_R": 206.5,
        "color": "#ff44aa", "icono": "◉",
        "beneficio": "Autoaceptación profunda. Theta 6.5Hz de compasión propia.",
        "descripcion": "El emprendedor que se cuida a sí mismo cuida mejor su negocio. Base de todo lo demás.",
        "mensajes": _msgs([
            ("SUP","Eres suficiente exactamente como eres ahora"),
            ("SUP","Cuidarte no es egoísmo. Es la condición para poder dar a los demás."),
        ]),
    },
    {
        "id": "A29", "nombre": "Propósito de Vida", "categoria": "PREMIUM",
        "beat_hz": 6.0, "hz_L": 200.0, "hz_R": 206.0,
        "color": "#ff22cc", "icono": "★",
        "beneficio": "Conexión con tu 'por qué'. Theta 6Hz de propósito y misión.",
        "descripcion": "Para días en que te preguntas si vale la pena. Reconecta con la razón real detrás de tu negocio.",
        "mensajes": _msgs([
            ("SUP","Tu negocio no es solo dinero. Es el impacto que tienes en vidas reales."),
            ("SUP","El día que sepas exactamente por qué lo haces, nada podrá detenerte"),
        ]),
    },
    {
        "id": "A30", "nombre": "Gratitud Activa", "categoria": "BIENESTAR",
        "beat_hz": 10.0, "hz_L": 200.0, "hz_R": 210.0,
        "color": "#ffcc00", "icono": "◎",
        "beneficio": "Estado de gratitud. Alpha 10Hz que activa el sistema parasimpático.",
        "descripcion": "La gratitud genuina reduce el cortisol y mejora la toma de decisiones. Úsalo en las mañanas.",
        "mensajes": _msgs([
            ("SUP","Tienes más de lo que crees. Reconocerlo te da energía para crecer más."),
            ("SUP","Cada cliente es alguien que confió en ti. Eso es un regalo."),
            ("REC","Lo que aprecias crece. Lo que ignoras desaparece."),
        ]),
    },
    {
        "id": "A31", "nombre": "Gestión del Tiempo", "categoria": "TRABAJO",
        "beat_hz": 13.0, "hz_L": 200.0, "hz_R": 213.0,
        "color": "#aaddff", "icono": "◆",
        "beneficio": "Priorización y foco. Beta 13Hz para gestión eficiente del tiempo.",
        "descripcion": "Para organizarte antes de una jornada intensa. Activa el pensamiento de priorización.",
        "mensajes": _msgs([
            ("SUP","Hoy vas a hacer las tres cosas más importantes. Todo lo demás puede esperar."),
            ("ADQ","Tu tiempo es tu recurso más valioso. Úsalo en lo que realmente importa."),
        ]),
    },
    {
        "id": "A32", "nombre": "Comunicación Poderosa", "categoria": "VENTAS",
        "beat_hz": 11.0, "hz_L": 200.0, "hz_R": 211.0,
        "color": "#ffaa44", "icono": "◉",
        "beneficio": "Expresión clara y persuasiva. Alpha-Beta 11Hz para comunicación efectiva.",
        "descripcion": "Para presentaciones, ventas o cualquier conversación importante. Activa la fluidez verbal.",
        "mensajes": _msgs([
            ("SUP","Cuando hablas desde la verdad, las palabras correctas siempre llegan"),
            ("ADQ","Lo que dices importa. Cómo lo dices, aún más."),
        ]),
    },
    {
        "id": "A33", "nombre": "Disciplina de Acero", "categoria": "AUTOESTIMA",
        "beat_hz": 16.0, "hz_L": 200.0, "hz_R": 216.0,
        "color": "#888888", "icono": "◎",
        "beneficio": "Activación de la voluntad. Beta 16Hz para ejecutar sin dilación.",
        "descripcion": "Cuando sabes lo que tienes que hacer pero no tienes ganas de hacerlo. Activa la disciplina.",
        "mensajes": _msgs([
            ("SUP","La disciplina es elegir lo que quieres más sobre lo que quieres ahora"),
            ("SUP","Cada acción que tomas con esfuerzo se convierte en hábito que no requiere esfuerzo"),
        ]),
    },
    # ── BIENESTAR FÍSICO (3) ──────────────────────────────────────────────────
    {
        "id": "A34", "nombre": "Energía Física", "categoria": "BIENESTAR",
        "beat_hz": 20.0, "hz_L": 200.0, "hz_R": 220.0,
        "color": "#ff2200", "icono": "⚡",
        "beneficio": "Activación corporal. Beta 20Hz para energía física y vitalidad.",
        "descripcion": "Para antes del ejercicio, una jornada larga o cuando el cuerpo está apagado.",
        "mensajes": _msgs([
            ("SUP","Tu cuerpo tiene energía. Estás accediendo a ella ahora."),
            ("SUP","Cuerpo fuerte, mente fuerte, negocio fuerte."),
        ]),
    },
    {
        "id": "A35", "nombre": "Calma Instantánea", "categoria": "BIENESTAR",
        "beat_hz": 9.0, "hz_L": 200.0, "hz_R": 209.0,
        "color": "#0055aa", "icono": "◌",
        "beneficio": "Reducción de ansiedad inmediata. Alpha 9Hz anti-estrés.",
        "descripcion": "Para situaciones de urgencia, pánico o estrés agudo. Resultados en 3-5 minutos.",
        "mensajes": _msgs([
            ("SUP","Estás a salvo. Respiras. El problema tiene solución."),
            ("SUP","La calma es una elección. La estás tomando ahora."),
        ]),
    },
    {
        "id": "A36", "nombre": "Intuición Expandida", "categoria": "PREMIUM",
        "beat_hz": 5.0, "hz_L": 200.0, "hz_R": 205.0,
        "color": "#6600cc", "icono": "✦",
        "beneficio": "Acceso a intuición profunda. Theta 5Hz para cognición extendida.",
        "descripcion": "Tu cerebro procesa millones de señales que tu conciencia no registra. Esto te ayuda a escucharlas.",
        "mensajes": _msgs([
            ("SUP","Tu intuición ha acumulado años de experiencia. Confía en ella."),
            ("ADQ","La diferencia entre un buen empresario y uno extraordinario es que el segundo escucha su intuición"),
        ]),
    },
    # ── RELACIONES / COMUNIDAD (2) ────────────────────────────────────────────
    {
        "id": "A37", "nombre": "Carisma Natural", "categoria": "VENTAS",
        "beat_hz": 11.0, "hz_L": 200.0, "hz_R": 211.0,
        "color": "#ff6688", "icono": "★",
        "beneficio": "Magnetismo personal. Alpha-Beta 11Hz para presencia carismática.",
        "descripcion": "El carisma no es para extrovertidos — es para personas que se conocen bien. Activa tu magnetismo auténtico.",
        "mensajes": _msgs([
            ("SUP","Las personas se sienten atraídas a ti porque eres genuino"),
            ("REC","Tu historia y tu trabajo inspiran a más gente de la que imaginas"),
        ]),
    },
    {
        "id": "A38", "nombre": "Trabajo en Equipo", "categoria": "VENTAS",
        "beat_hz": 12.5, "hz_L": 200.0, "hz_R": 212.5,
        "color": "#44aaff", "icono": "◉",
        "beneficio": "Sinergia grupal. Alpha 12.5Hz para colaboración y confianza.",
        "descripcion": "Para sesiones con colaboradores, proveedores o clientes clave. Activa la mentalidad colaborativa.",
        "mensajes": _msgs([
            ("REC","Los mejores resultados siempre son colectivos"),
            ("SUP","Rodearte de personas que te complementan es inteligencia, no debilidad"),
        ]),
    },
    # ── PARANORMAL EXTENDIDO (2) ──────────────────────────────────────────────
    {
        "id": "A39", "nombre": "Puerta Theta", "categoria": "PARANORMAL",
        "beat_hz": 4.5, "hz_L": 200.0, "hz_R": 204.5,
        "color": "#330066", "icono": "✧",
        "beneficio": "Límite sueño-vigilia. Theta 4.5Hz — umbral de percepción expandida.",
        "descripcion": "Para meditación profunda, visualización o prácticas espirituales. Solo usuarios con experiencia.",
        "mensajes": _msgs([
            ("SUP","En el umbral entre estados, la mente accede a lo que normalmente está oculto"),
        ]),
    },
    {
        "id": "A40", "nombre": "Frecuencia Cósmica", "categoria": "PARANORMAL",
        "beat_hz": 7.83, "hz_L": 432.0, "hz_R": 439.83,
        "color": "#220044", "icono": "✧",
        "beneficio": "432Hz + Resonancia Schumann. La combinación máxima para estados no ordinarios.",
        "descripcion": "432Hz de portadora con beat 7.83Hz (Schumann). La combinación más armónica conocida. Solo experimentados.",
        "mensajes": _msgs([
            ("SUP","Estás conectado a algo más grande que cualquier problema cotidiano"),
        ]),
    },
]

# ── Catálogo de 8 visuales ────────────────────────────────────────────────────

CATALOGO_VISUAL = [
    {
        "id":"V01","nombre":"Cosmos NEXUS","categoria":"NEXUS",
        "color":"#00ff88","icono":"◈","css_key":"cosmos",
        "descripcion":"El ambiente visual original de NEXUS. Partículas verdes digitales. Discreto y profesional.",
    },
    {
        "id":"V02","nombre":"Espiral Áurea","categoria":"INTRO",
        "color":"#ddaa00","icono":"◎","css_key":"aurea",
        "descripcion":"Espiral de Fibonacci animada. La proporción áurea en movimiento lento — orden natural y perfección.",
    },
    {
        "id":"V03","nombre":"Cosmos Profundo","categoria":"PREMIUM",
        "color":"#0033aa","icono":"✦","css_key":"deep_space",
        "descripcion":"Campo estelar de profundidad infinita. Para estados de visión amplia y perspectiva estratégica.",
    },
    {
        "id":"V04","nombre":"Bosque Enfocado","categoria":"TRABAJO",
        "color":"#226633","icono":"◉","css_key":"bosque",
        "descripcion":"Gradiente de verdes naturales. Comprobado que reduce la fatiga visual en pantallas.",
    },
    {
        "id":"V05","nombre":"Mandala de Foco","categoria":"PREMIUM",
        "color":"#aa44ff","icono":"◎","css_key":"mandala",
        "descripcion":"Mandala generativo en Canvas. La simetría radial activa el hemisferio derecho, potenciando creatividad.",
    },
    {
        "id":"V06","nombre":"Plasma de Energía","categoria":"VENTAS",
        "color":"#ff4400","icono":"⚡","css_key":"plasma",
        "descripcion":"Gradiente naranja-rojo pulsante. Para días de alta productividad y energía de ventas.",
    },
    {
        "id":"V07","nombre":"Océano Profundo","categoria":"BIENESTAR",
        "color":"#004488","icono":"◌","css_key":"oceano",
        "descripcion":"Gradiente de azul profundo con ondas lentas. Reduce el cortisol y crea sensación de calma.",
    },
    {
        "id":"V08","nombre":"Flor de la Vida","categoria":"PARANORMAL",
        "color":"#cc00ff","icono":"✧","css_key":"flor_vida",
        "descripcion":"Geometría sagrada de 19 círculos. Encontrada en culturas antiguas de todo el mundo.",
    },
]


# ── Gestión de uso y cuotas ───────────────────────────────────────────────────

def _mes_actual() -> str:
    return datetime.datetime.now().strftime("%Y-%m")

def _cargar_uso() -> dict:
    try:
        with open(USO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("mes") != _mes_actual():
            return _uso_fresco()
        return data
    except Exception:
        return _uso_fresco()

def _uso_fresco() -> dict:
    return {
        "mes": _mes_actual(),
        "audio_activados":  [],
        "visual_activados": [],
        "creditos_extra":   {"audio": 0, "visual": 0},
        "historial":        [],
    }

def _guardar_uso(uso: dict):
    with open(USO_PATH, "w", encoding="utf-8") as f:
        json.dump(uso, f, ensure_ascii=False, indent=2)

def _get_plan() -> str:
    # Modo privado (dueño) — acceso ADMIN completo sin licencia
    import os
    from dotenv import load_dotenv
    load_dotenv()
    if os.getenv("NEXUS_PRIVATE", "0") == "1":
        return "ADMIN"
    try:
        from nexus_license import validar_licencia
        v = validar_licencia()
        return v.get("tipo", "DEMO") if v.get("valida") else "DEMO"
    except Exception:
        return "ADMIN"

def _puede_activar(tipo: str, item_id: str) -> dict:
    plan  = _get_plan()
    cuota = CUOTAS.get(plan, CUOTAS["DEMO"])
    uso   = _cargar_uso()

    max_q     = cuota[tipo]
    creditos  = uso["creditos_extra"].get(tipo, 0)
    max_total = max_q + creditos

    # DEMO ve el catálogo pero no puede activar nada
    if plan == "DEMO" and max_q == 0 and creditos == 0:
        return {"puede": False, "razon": "demo_ver_solo", "cuota_max": 0, "cuota_usada": 0}

    activados_key = f"{tipo}_activados"
    ya_activados  = uso.get(activados_key, [])
    usados        = len(ya_activados)

    # Si ya lo activó este mes, puede usarlo sin costo adicional
    if item_id in ya_activados:
        return {"puede": True, "razon": "ya_activado", "cuota_max": max_total, "cuota_usada": usados}

    # Verificar categoría vs plan
    catalogo  = CATALOGO_AUDIO if tipo == "audio" else CATALOGO_VISUAL
    item      = next((x for x in catalogo if x["id"] == item_id), None)
    if not item:
        return {"puede": False, "razon": "no_existe", "cuota_max": max_total, "cuota_usada": usados}

    cat_item       = item.get("categoria", "INTRO")
    planes_ok      = ACCESO_CATEGORIA.get(cat_item, ["FULL", "ADMIN"])
    if plan not in planes_ok:
        return {"puede": False, "razon": "plan_insuficiente",
                "plan_requerido": planes_ok[0], "cuota_max": max_total, "cuota_usada": usados}

    # Verificar cuota mensual
    if usados >= max_total:
        return {"puede": False, "razon": "cuota_agotada", "cuota_max": max_total,
                "cuota_usada": usados, "precio_extra_mxn": cuota["precio_extra"]}

    return {"puede": True, "razon": "ok", "cuota_max": max_total, "cuota_usada": usados}


def activar_item(tipo: str, item_id: str) -> dict:
    check = _puede_activar(tipo, item_id)
    if not check["puede"]:
        return {"ok": False, **check}

    uso = _cargar_uso()
    activados_key = f"{tipo}_activados"
    if item_id not in uso[activados_key]:
        uso[activados_key].append(item_id)
        uso["historial"].append({
            "id": item_id, "tipo": tipo,
            "fecha": datetime.datetime.now().isoformat(),
        })
        _guardar_uso(uso)

    catalogo = CATALOGO_AUDIO if tipo == "audio" else CATALOGO_VISUAL
    item     = next((x for x in catalogo if x["id"] == item_id), None)
    return {"ok": True, "item": item, **check}


def agregar_creditos(tipo: str, cantidad: int, nota: str = "") -> dict:
    uso = _cargar_uso()
    uso["creditos_extra"][tipo] = uso["creditos_extra"].get(tipo, 0) + cantidad
    if nota:
        uso["historial"].append({
            "id": f"CREDITO_{tipo.upper()}", "tipo": "credito",
            "fecha": datetime.datetime.now().isoformat(),
            "nota": nota, "cantidad": cantidad,
        })
    _guardar_uso(uso)
    return {"ok": True, "creditos_actuales": uso["creditos_extra"]}


def get_catalogo_completo() -> dict:
    plan  = _get_plan()
    uso   = _cargar_uso()
    cuota = CUOTAS.get(plan, CUOTAS["DEMO"])

    def anotar(item, tipo):
        check = _puede_activar(tipo, item["id"])
        return {
            **item,
            "accesible":    plan in ACCESO_CATEGORIA.get(item.get("categoria","INTRO"), []),
            "puede_activar": check["puede"],
            "razon":        check.get("razon"),
            "plan_requerido": check.get("plan_requerido",""),
            "ya_activado":  item["id"] in uso[f"{tipo}_activados"],
        }

    cred_a = uso["creditos_extra"].get("audio",  0)
    cred_v = uso["creditos_extra"].get("visual", 0)

    return {
        "ok":    True,
        "plan":  plan,
        "cuotas": {
            "audio":  {"max": cuota["audio"]  + cred_a, "usados": len(uso["audio_activados"])},
            "visual": {"max": cuota["visual"] + cred_v, "usados": len(uso["visual_activados"])},
        },
        "precio_extra_mxn": cuota["precio_extra"],
        "es_demo":   plan == "DEMO",
        "audios":    [anotar(a, "audio")  for a in CATALOGO_AUDIO],
        "visuales":  [anotar(v, "visual") for v in CATALOGO_VISUAL],
        "mes":       uso["mes"],
        "total_audios":   len(CATALOGO_AUDIO),
        "total_visuales": len(CATALOGO_VISUAL),
    }


def get_uso_actual() -> dict:
    plan  = _get_plan()
    uso   = _cargar_uso()
    cuota = CUOTAS.get(plan, CUOTAS["DEMO"])
    return {
        "plan":           plan,
        "mes":            uso["mes"],
        "audio_usados":   len(uso["audio_activados"]),
        "audio_max":      cuota["audio"] + uso["creditos_extra"].get("audio", 0),
        "visual_usados":  len(uso["visual_activados"]),
        "visual_max":     cuota["visual"] + uso["creditos_extra"].get("visual", 0),
        "creditos_extra": uso["creditos_extra"],
        "historial":      uso["historial"][-10:],
    }


# ── CLI para el admin ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args or args[0] == "catalogo":
        cat = get_catalogo_completo()
        print(f"Plan: {cat['plan']} | {cat['total_audios']} audios | {cat['total_visuales']} visuales")
        print(f"Audio: {cat['cuotas']['audio']['usados']}/{cat['cuotas']['audio']['max']} usados")
        print(f"Visual: {cat['cuotas']['visual']['usados']}/{cat['cuotas']['visual']['max']} usados")
    elif args[0] == "credito" and len(args) >= 3:
        tipo, cantidad = args[1], int(args[2])
        nota = args[3] if len(args) > 3 else "Pago recibido"
        r = agregar_creditos(tipo, cantidad, nota)
        print(f"Créditos agregados: {r}")
    elif args[0] == "uso":
        print(json.dumps(get_uso_actual(), indent=2))
    else:
        print("Comandos: catalogo | credito [audio|visual] [cantidad] [nota] | uso")

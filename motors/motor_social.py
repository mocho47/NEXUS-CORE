#!/usr/bin/env python3
"""
NEXUS v3 - Motor de Redes Sociales
Simplex - Motor de gestión de contenido para redes sociales
Puerto: 8005
"""

import logging
import time
import sys
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("motor_social")

# Intentar importar librerías compartidas
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.config import settings
    logger.info("Configuración compartida cargada exitosamente")
except ImportError:
    logger.warning("No se pudo importar lib.config, usando valores por defecto")
    settings = type('Settings', (), {
        'APP_NAME': 'NEXUS v3',
        'VERSION': '3.0.0',
        'DEBUG': False,
    })()

# ==================== ESTADÍSTICAS ====================
motor_stats = {
    "tareas_completadas": 0,
    "tareas_con_error": 0,
    "hora_inicio": time.time(),
    "ultima_actividad": None,
}

# ==================== DATOS EN MEMORIA ====================
borradores_db: Dict[str, dict] = {}
calendario_db: List[dict] = []
historial_posts: List[dict] = []

# ==================== PLANTILLAS DE CONTENIDO ====================

PLANTILLAS_ATF = {
    "retrofit_tips": [
        {
            "tipo": "tip",
            "titulos": [
                "¿Sabías que puedes tener CarPlay en tu auto? 🚗💡",
                "5 cosas que debes saber antes de instalar una pantalla en tu auto",
                "Retrofit no es solo estética, es seguridad vial 🛡️",
                "La tecnología que tu auto merece, sin cambiar de vehículo",
                "¿Tu auto del 2010 puede tener la tecnología del 2024? Sí, es posible ✨",
            ],
            "cuerpo": [
                "Una pantalla multimedia con CarPlay/Android Auto no solo se ve increíble, te permite:\n\n📱 Navegar con Maps/Waze en pantalla grande\n🎵 Controlar tu música sin soltar el volante\n📞 Contestar llamadas de forma segura\n📷 Ver la cámara de reversa en HD\n\n¡Pregunta por nuestros modelos X1, X2, X3 y X4!",
                "En ATF no solo instalamos pantallas, transformamos tu experiencia de conducción. Nuestros kits incluyen:\n\n✅ Pantalla de alta resolución\n✅ Compatible con cámara de reversa\n✅ CarPlay y Android Auto\n✅ Instalación profesional\n✅ Garantía incluida\n\nAgenda tu instalación hoy mismo.",
                "El retrofit automotriz ha evolucionado. Ya no es solo poner una pantalla, es integrar tu vida digital de forma segura al volante. Convierte tu auto en un espacio inteligente sin cambiar de vehículo.",
            ]
        },
    ],
    "antes_despues": [
        {
            "tipo": "antes_despues",
            "titulos": [
                "Antes y Después: Mira la transformación 🔥",
                "De este... a ESTO 😱 #RetrofitATF",
                "La diferencia que hace una pantalla multimedia en tu auto",
                "Otro antes y después que habla por sí solo 👏",
            ],
            "cuerpo": [
                "Esto es lo que logramos en menos de 2 horas de instalación. Nuestros kits están diseñados para integrarse perfectamente con la estética de tu auto.\n\n¿Listo para transformar el tuyo? 🚗✨",
                "La satisfacción de ver un proyecto terminado no tiene precio. Nuestro equipo técnico asegura una instalación impecable.\n\n📍 Agenda tu cita: [tu ubicación]\n📞 Contáctanos para cotización gratuita",
            ]
        },
    ],
    "testimonios": [
        {
            "tipo": "testimonio",
            "titulos": [
                "Lo que dicen nuestros clientes ❤️",
                "Otro cliente feliz con su pantalla ATF 🙌",
                "Así suena la experiencia ATF en voz de nuestros clientes",
            ],
            "cuerpo": [
                "🏅 \"{cliente}\" nos compartió su experiencia:\n\n\"Increíble el servicio. Mi auto se ve completamente diferente y ahora puedo usar CarPlay. La instalación fue rápida y profesional. 100% recomendado.\"\n\n¡Gracias por confiar en ATF! Tu satisfacción es nuestra motivación.",
                "Cada instalación es una historia de transformación. Nuestros clientes no solo obtienen tecnología, obtienen seguridad, comodidad y un auto que se siente nuevo.\n\n⭐⭐⭐⭐⭐ 5 estrellas en servicio y calidad.",
            ]
        },
    ],
    "productos": [
        {
            "tipo": "producto",
            "titulos": [
                "Conoce nuestra línea completa de pantallas 🖥️",
                "¿Cuál pantalla ATF es para ti? 🤔",
                "Modelo X4: La pantalla que tu auto merece 🔥",
            ],
            "cuerpo": [
                "🎮 MODELO X4 - Desde $2,699 MXN\nPantalla de alta resolución, CarPlay inalámbrico, compatible con todas las marcas.\n\n🎮 MODELO X1 - Desde $3,149 MXN\nLa opción premium con funciones avanzadas.\n\n🎮 MODELO X2 - Desde $2,799 MXN\nExcelente relación calidad-precio.\n\n🎮 MODELO X3 - Desde $3,149 MXN\nPara quienes buscan lo mejor.\n\n📍 Instalación profesional disponible\n📞 ¡Pide tu cotización hoy!",
            ]
        },
    ],
}

PLANTILLAS_MILENS = {
    "productos_personalizados": [
        {
            "tipo": "producto",
            "titulos": [
                "Cada pieza cuenta una historia ✨ #MilensDesign",
                "Hecho con pasión, personalizado para ti 💜",
                "Creatividad sin límites en Milens",
            ],
            "cuerpo": [
                "En Milens no solo fabricamos productos, creamos experiencias únicas. Desde cajas personalizadas hasta llaveros con diseño exclusivo, cada pieza está hecha con dedicación.\n\n🎨 Corte láser preciso\n💫 Sublimación de alta calidad\n📦 Cajas en MDF y acrílico\n🔑 Llaveros personalizados\n\n¡Dinos qué imaginas y nosotros lo creamos!",
                "¿Necesitas un regalo especial? Un empaque único para tu producto? Un detalle personalizado? En Milens lo hacemos realidad.\n\nCada proyecto es diferente, cada cliente es especial. ¡Contáctanos para cotizar!",
            ]
        },
    ],
    "detras_camaras": [
        {
            "tipo": "detras_camaras",
            "titulos": [
                "Detrás de cámaras: Así trabajamos en Milens 👀",
                "El proceso creativo en Milens 🔧",
                "De la idea al producto final 🛠️",
            ],
            "cuerpo": [
                "Te mostramos un poco de cómo trabajamos:\n\n1️⃣ Recibimos tu idea o diseño\n2️⃣ Lo digitalizamos con precisión\n3️⃣ Preparamos el material (MDF, acrílico, etc.)\n4️⃣ Corte láser con tolerancia milimétrica\n5️⃣ Acabado y empaque con cariño\n📦 ¡Listo para entregarte algo único!\n\nCada paso está hecho con dedicación. ¡Esa es la promesa Milens!",
            ]
        },
    ],
    "resenas": [
        {
            "tipo": "resena",
            "titulos": [
                "Lo que dicen nuestros clientes de Milens 💜",
                "Otra reseña que nos llena de orgullo 🥹",
                "Así vivimos la experiencia Milens con nuestros clientes",
            ],
            "cuerpo": [
                "💜 \"{cliente}\" nos compartió:\n\n\"Pedí cajas personalizadas para mi negocio y quedaron PERFECTAS. El acabado, la atención, todo de primera. Ya es mi tercer pedido y seguiré regresando.\"\n\n¡Esa es la calidad que nos caracteriza! Cada proyecto es tratado como si fuera nuestro.",
                "En Milens medimos nuestro éxito por la sonrisa de nuestros clientes. Cada reseña positiva es motivo para seguir mejorando y creando.\n\nGracias por ser parte de la familia Milens 💜",
            ]
        },
    ],
}

PLANTILLAS_CANBUSFIX = {
    "instaladores": [
        {
            "tipo": "instalador",
            "titulos": [
                "Conoce a nuestra red de instaladores certificados 🔧",
                "Instalador destacado de la semana 👏",
                "La fuerza de CanbusFix es su gente 💪",
            ],
            "cuerpo": [
                "🔧 Nuestra red de instaladores certificados crece cada día. Técnicos profesionales capacitados en retrofit automotriz, listos para transformar tu auto.\n\n📍 Cobertura nacional\n✅ Capacitación continua\n🏆 Estándares de calidad\n🔧 Herramientas especializadas\n\n¿Eres instalador? Únete a la red CanbusFix y crece con nosotros.",
                "Ser parte de la red CanbusFix significa:\n\n💼 Acceso a clientes en tu zona\n📚 Capacitación técnica constante\n🔧 Soporte especializado\n📊 Seguimiento de comisiones\n🤝 Comunidad de profesionales\n\n¡Contacta a tu instalador CanbusFix más cercano!",
            ]
        },
    ],
    "tips_tecnicos": [
        {
            "tipo": "tip_tecnico",
            "titulos": [
                "Tip técnico: ¿Cómo elegir la pantalla correcta? 🛠️",
                "Lo que nadie te dice sobre el retrofit automotriz 🔧",
                "Error común en instalaciones de pantallas (y cómo evitarlo)",
            ],
            "cuerpo": [
                "💡 TIP TÉCNICO CANBUSFIX:\n\nAntes de instalar una pantalla multimedia, verifica:\n\n1️⃣ Tamaño del radio original (1-DIN o 2-DIN)\n2️⃣ Compatible con CAN Bus de tu marca\n3️⃣ Salida de audio y tipo de conexión\n4️⃣ Compatibilidad con cámara de reversa\n5️⃣ Voltaje del sistema eléctrico\n\nEn CanbusFix capacitamos a nuestros instaladores para manejar cada caso. ¡Confiabilidad profesional!",
                "El error más común al instalar una pantalla: no aislar correctamente las conexiones de CAN Bus. Esto puede causar errores en el tablero.\n\nEn nuestra capacitación enseñamos técnicas profesionales para una instalación limpia y sin fallas. ¡Esa es la diferencia CanbusFix! 🔧",
            ]
        },
    ],
    "crecimiento_red": [
        {
            "tipo": "crecimiento",
            "titulos": [
                "¡La red CanbusFix sigue creciendo! 📈",
                "Un mes más de crecimiento increíble 🚀",
                "Gracias por confiar en CanbusFix 🙏",
            ],
            "cuerpo": [
                "📊 Números que hablan por sí solos:\n\n✅ +{n} instaladores activos\n✅ Cobertura en {n} estados\n✅ +{n} instalaciones exitosas\n✅ Satisfacción del {n}%\n\nCanbusFix no es solo una marca, es una comunidad de profesionales comprometidos con la excelencia en retrofit automotriz.\n\n🚀 ¡El futuro es CanbusFix!",
            ]
        },
    ],
}

PLANTILLAS_POR_NEGOCIO = {
    "atf": PLANTILLAS_ATF,
    "milens": PLANTILLAS_MILENS,
    "canbusfix": PLANTILLAS_CANBUSFIX,
}

# ==================== HASHTAGS POR CATEGORÍA ====================

HASHTAGS_CATEGORIA = {
    "automotriz": [
        "#retrofit", "#carplay", "#androidauto", "#pantallamultimedia",
        "#autos", "#tecnologiaautomotriz", "#instalacion", "#carplaymexico",
        "#androidautomexico", "#audioturbo", "#seguridadvial",
        "#techauto", "#gadgetsauto", "#modificacionauto",
        "#atfmexico", "#pantallasparacarro",
    ],
    "diseno": [
        "#disenopersonalizado", "#cortelaser", "#sublimacion",
        "#hechoamano", "#hechoenmexico", "#creatividad",
        "#disenomexicano", "#empaquepersonalizado", "#regalosunicos",
        "#artsanal", "#cortemdf", "#acrilico", "#personalizacion",
        "#milensdesign", "#disenocreativo",
    ],
    "emprendimiento": [
        "#emprendimiento", "#emprendedoresmexico", "#negocios",
        "#pipol", "#crecenjuntos", "#rednegocios", "#instaladores",
        "#comunidadprofesional", "#canbusfix", "#retrofitmexico",
        "#networking", "#negociosmexico", "#profesionales",
    ],
    "general": [
        "#nexusv3", "#simplex", "#tecnologia", "#innovacion",
        "#mexico", "#calidad", "#servicio", "#profesional",
    ],
}

# ==================== FORMATEO POR PLATAFORMA ====================

CONFIGURACION_PLATAFORMA = {
    "instagram": {
        "max_chars": 2200,
        "formato": "caption",
        "max_hashtags": 30,
        "estilo": "corto + emojis + hashtags",
        "descripcion": "Pie de foto corto y atractivo con hashtags al final",
    },
    "facebook": {
        "max_chars": 5000,
        "formato": "post",
        "max_hashtags": 10,
        "estilo": "largo + hashtags dispersos",
        "descripcion": "Publicación más extensa y conversacional",
    },
    "tiktok": {
        "max_chars": 200,
        "formato": "video_script",
        "max_hashtags": 8,
        "estilo": "gancho + script + hashtags",
        "descripcion": "Guion de video con hooks y estructura corta",
    },
    "whatsapp": {
        "max_chars": 300,
        "formato": "status",
        "max_hashtags": 0,
        "estilo": "corto y directo",
        "descripcion": "Texto corto para estado de WhatsApp",
    },
}

app = FastAPI(
    title="Motor de Redes Sociales - NEXUS v3",
    description="Motor de gestión de contenido para redes sociales para NEXUS v3",
    version="3.0.0"
)


# ==================== MODELOS ====================

class ExecuteRequest(BaseModel):
    action: str = Field(..., description="Acción a ejecutar")
    data: dict = Field(default_factory=dict, description="Datos de la acción")


# ==================== FUNCIONES AUXILIARES ====================

def _registrar_actividad():
    motor_stats["ultima_actividad"] = datetime.now().isoformat()


def _actualizar_estadisticas(exito: bool):
    if exito:
        motor_stats["tareas_completadas"] += 1
    else:
        motor_stats["tareas_con_error"] += 1
    _registrar_actividad()


def _obtener_tiempo_actividad() -> str:
    segundos = int(time.time() - motor_stats["hora_inicio"])
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}h {minutos}m {segs}s"


def _obtener_categorias_negocio(negocio: str) -> list:
    """Obtener categorías de hashtags para un negocio."""
    categorias_map = {
        "atf": ["automotriz", "general"],
        "milens": ["diseno", "general"],
        "canbusfix": ["automotriz", "emprendimiento", "general"],
    }
    return categorias_map.get(negocio.lower(), ["general"])


def _generar_hashtags(topic: str, count: int = 10, negocio: str = None) -> list:
    """Generar hashtags relevantes basados en el tema y negocio."""
    hashtags = set()

    # Hashtags del negocio
    if negocio and negocio.lower() in _obtener_categorias_negocio(negocio):
        for cat in _obtener_categorias_negocio(negocio):
            for tag in HASHTAGS_CATEGORIA.get(cat, []):
                hashtags.add(tag)

    # Hashtags basados en tema
    topic_lower = topic.lower() if topic else ""
    topic_words = topic_lower.replace("_", " ").replace("-", " ").split()

    for word in topic_words:
        if len(word) > 3:
            hashtags.add(f"#{word}")
            hashtags.add(f"#{word}mexico")
            hashtags.add(f"#{word}tips")

    # Hashtags generales
    for tag in HASHTAGS_CATEGORIA.get("general", []):
        hashtags.add(tag)

    # Convertir a lista y limitar
    resultado = list(hashtags)

    # Priorizar hashtags más relevantes
    if topic_lower:
        resultado.sort(key=lambda x: (
            0 if topic_lower in x.lower() else 1,
            0 if negocio and negocio.lower() in x.lower() else 1,
            len(x)
        ))

    return resultado[:count]


def _formatear_para_plataforma(texto: str, titulo: str, hashtags: list, plataforma: str) -> dict:
    """Formatear contenido según la plataforma destino."""
    config = CONFIGURACION_PLATAFORMA.get(plataforma, CONFIGURACION_PLATAFORMA["instagram"])

    if plataforma == "instagram":
        caption = f"{titulo}\n\n{texto}"
        if hashtags:
            hashtag_block = " ".join(hashtags[:config["max_hashtags"]])
            caption = f"{titulo}\n\n{texto}\n\n.{hashtag_block}"
        # Truncar si excede el límite
        if len(caption) > config["max_chars"]:
            caption = caption[:config["max_chars"] - 3] + "..."
        return {
            "tipo": "caption",
            "texto": caption,
            "hashtags": hashtags[:config["max_hashtags"]],
            "longitud": len(caption),
            "plataforma": plataforma,
        }

    elif plataforma == "facebook":
        post = f"🎯 {titulo}\n\n{texto}"
        if hashtags:
            post += "\n\n"
            for tag in hashtags[:config["max_hashtags"]]:
                post += f"{tag} "
        return {
            "tipo": "post",
            "texto": post.strip(),
            "hashtags": hashtags[:config["max_hashtags"]],
            "longitud": len(post),
            "plataforma": plataforma,
        }

    elif plataforma == "tiktok":
        hooks = [
            f"¿Sabías esto sobre {titulo[:30]}? 👀",
            f"Esto es lo que nadie te cuenta 🔥",
            f"¡Atento porque esto TE INTERESA! ⚡",
            f"Lo que vas a ver te va a sorprender 😱",
        ]
        hook = random.choice(hooks)
        # Script corto para TikTok
        secciones = texto.split("\n")[:3]
        script_corto = " ".join([s.strip() for s in secciones if s.strip()])[:120]

        hashtags_tiktok = hashtags[:config["max_hashtags"]]
        script = f"{hook}\n\n{script_corto}"
        if hashtags_tiktok:
            script += "\n\n" + " ".join(hashtags_tiktok)

        return {
            "tipo": "video_script",
            "hook": hook,
            "script": script_corto,
            "texto_completo": script,
            "hashtags": hashtags_tiktok,
            "plataforma": plataforma,
        }

    elif plataforma == "whatsapp":
        # Estado de WhatsApp: corto y directo
        estado = f"{titulo}\n\n{texto}"
        # Resumir para WhatsApp
        oraciones = estado.split(". ")
        if len(oraciones) > 2:
            estado = ". ".join(oraciones[:2]) + "."
        estado = estado[:config["max_chars"]]

        return {
            "tipo": "status",
            "texto": estado,
            "hashtags": [],
            "longitud": len(estado),
            "plataforma": plataforma,
        }

    else:
        return {
            "tipo": "generico",
            "texto": f"{titulo}\n\n{texto}",
            "hashtags": hashtags,
            "plataforma": plataforma,
        }


# ==================== ACCIONES ====================

def generate_post(data: dict) -> dict:
    """Generar contenido para redes sociales."""
    try:
        negocio = data.get("business", data.get("negocio", "atf")).lower()
        tema = data.get("topic", data.get("tema", ""))
        plataforma = data.get("platform", data.get("plataforma", "instagram")).lower()

        if negocio not in PLANTILLAS_POR_NEGOCIO:
            negocios_disp = ", ".join(PLANTILLAS_POR_NEGOCIO.keys())
            return {
                "exito": False,
                "mensaje": f"Negocio '{negocio}' no reconocido. Disponibles: {negocios_disp}",
                "resultado": None
            }

        if plataforma not in CONFIGURACION_PLATAFORMA:
            plataformas_disp = ", ".join(CONFIGURACION_PLATAFORMA.keys())
            return {
                "exito": False,
                "mensaje": f"Plataforma '{plataforma}' no reconocida. Disponibles: {plataformas_disp}",
                "resultado": None
            }

        plantillas_negocio = PLANTILLAS_POR_NEGOCIO[negocio]

        # Seleccionar categoría de plantilla
        categoria = None
        tema_lower = tema.lower() if tema else ""

        if not tema:
            # Sin tema: elegir aleatorio de todas las categorías
            categoria = random.choice(list(plantillas_negocio.keys()))
        else:
            # Buscar categoría relevante
            for cat_name, cat_plantillas in plantillas_negocio.items():
                if tema_lower in cat_name:
                    categoria = cat_name
                    break

            if not categoria:
                # Buscar en títulos/cuerpos
                for cat_name, cat_plantillas in plantillas_negocio.items():
                    for plantilla in cat_plantillas:
                        for titulo in plantilla.get("titulos", []):
                            if tema_lower in titulo.lower():
                                categoria = cat_name
                                break
                        if categoria:
                            break
                    if categoria:
                        break

            if not categoria:
                categoria = random.choice(list(plantillas_negocio.keys()))

        # Seleccionar plantilla específica
        plantilla = random.choice(plantillas_negocio[categoria])
        titulo = random.choice(plantilla["titulos"])
        cuerpo = random.choice(plantilla["cuerpo"])

        # Personalizar con {cliente} si existe
        if "{cliente}" in cuerpo:
            nombres = ["María", "Carlos", "Ana", "Roberto", "Laura", "Miguel", "Sofía", "Diego"]
            cuerpo = cuerpo.replace("{cliente}", random.choice(nombres))

        # Generar hashtags
        categorias_negocio = _obtener_categorias_negocio(negocio)
        all_hashtags = []
        for cat in categorias_negocio:
            all_hashtags.extend(HASHTAGS_CATEGORIA.get(cat, []))
        all_hashtags = list(set(all_hashtags))
        random.shuffle(all_hashtags)

        # Formatear para plataforma
        contenido = _formatear_para_plataforma(cuerpo, titulo, all_hashtags, plataforma)

        # Guardar en historial
        post_id = str(uuid.uuid4())[:8]
        registro_post = {
            "id": post_id,
            "negocio": negocio,
            "tema": tema,
            "plataforma": plataforma,
            "categoria_plantilla": categoria,
            "titulo": titulo,
            "contenido": contenido,
            "fecha_generacion": datetime.now().isoformat(),
        }
        historial_posts.append(registro_post)

        logger.info(f"Post generado: {negocio}/{plataforma} - {titulo[:50]}")

        return {
            "exito": True,
            "mensaje": f"Contenido generado para {negocio} en {plataforma}",
            "resultado": {
                "post_id": post_id,
                "negocio": negocio,
                "plataforma": plataforma,
                "categoria": categoria,
                "contenido": contenido,
                "longitud": contenido.get("longitud", len(str(contenido))),
            }
        }
    except Exception as e:
        logger.error(f"Error en generate_post: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_calendar(data: dict) -> dict:
    """Obtener calendario de contenido."""
    try:
        negocio = data.get("business", data.get("negocio", None))
        dias = data.get("days", data.get("dias", 7))
        plataforma = data.get("platform", data.get("plataforma", None))

        calendario = []
        hoy = datetime.now()

        # Tipos de contenido por día
        tipos_semana = {
            "lunes": "tip_educativo",
            "martes": "producto",
            "miercoles": "interaccion",
            "jueves": "testimonio",
            "viernes": "antes_despues",
            "sabado": "entretenimiento",
            "domingo": "reflexion",
        }

        dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

        for i in range(dias):
            fecha = hoy + timedelta(days=i)
            dia_nombre = dias_semana[fecha.weekday()]
            tipo_contenido = tipos_semana.get(dia_nombre, "general")

            # Negocios a incluir
            negocios = [negocio] if negocio else list(PLANTILLAS_POR_NEGOCIO.keys())

            for neg in negocios:
                if neg.lower() in PLANTILLAS_POR_NEGOCIO:
                    plataformas = [plataforma] if plataforma else list(CONFIGURACION_PLATAFORMA.keys())
                    for plat in plataformas:
                        entrada = {
                            "fecha": fecha.strftime("%Y-%m-%d"),
                            "dia_semana": dia_nombre,
                            "negocio": neg,
                            "plataforma": plat,
                            "tipo_contenido": tipo_contenido,
                            "estado": "pendiente",
                        }
                        calendario.append(entrada)

        # También incluir posts del historial para las fechas correspondientes
        for post in historial_posts:
            post_fecha = post.get("fecha_generacion", "")[:10]
            for entrada in calendario:
                if entrada["fecha"] == post_fecha:
                    entrada["post_id"] = post.get("id")
                    entrada["estado"] = "generado"

        return {
            "exito": True,
            "mensaje": f"Calendario generado: {dias} días, {len(calendario)} entradas",
            "resultado": {
                "dias": dias,
                "total_entradas": len(calendario),
                "calendario": calendario,
                "fecha_generacion": hoy.isoformat(),
            }
        }
    except Exception as e:
        logger.error(f"Error en get_calendar: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def save_draft(data: dict) -> dict:
    """Guardar un borrador de post."""
    try:
        titulo = data.get("title", data.get("titulo", ""))
        contenido = data.get("content", data.get("contenido", ""))
        plataforma = data.get("platform", data.get("plataforma", "instagram"))
        negocio = data.get("business", data.get("negocio", "atf"))
        hashtags = data.get("hashtags", [])
        programar_para = data.get("schedule", data.get("programar_para", None))

        if not contenido:
            return {"exito": False, "mensaje": "El contenido del borrador es obligatorio", "resultado": None}

        borrador_id = str(uuid.uuid4())[:8]
        borrador = {
            "id": borrador_id,
            "titulo": titulo,
            "contenido": contenido,
            "plataforma": plataforma,
            "negocio": negocio,
            "hashtags": hashtags,
            "programar_para": programar_para,
            "estado": "borrador",
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_actualizacion": datetime.now().isoformat(),
        }
        borradores_db[borrador_id] = borrador

        logger.info(f"Borrador guardado: {borrador_id} - {plataforma}")

        return {
            "exito": True,
            "mensaje": "Borrador guardado exitosamente",
            "resultado": borrador
        }
    except Exception as e:
        logger.error(f"Error en save_draft: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def generate_hashtags(data: dict) -> dict:
    """Generar hashtags relevantes para un tema."""
    try:
        tema = data.get("topic", data.get("tema", ""))
        count = data.get("count", data.get("cantidad", 15))
        negocio = data.get("business", data.get("negocio", None))

        if not tema:
            return {"exito": False, "mensaje": "Se requiere un tema para generar hashtags", "resultado": None}

        hashtags = _generar_hashtags(tema, count, negocio)

        # Agregar hashtag del negocio
        hashtag_negocio = {
            "atf": "#ATF #ATFMexico",
            "milens": "#Milens #MilensDesign",
            "canbusfix": "#CanbusFix #CanbusFixMexico",
        }
        if negocio and negocio.lower() in hashtag_negocio:
            for tag in hashtag_negocio[negocio.lower()].split():
                if tag not in hashtags:
                    hashtags.insert(0, tag)

        hashtags = hashtags[:count]

        return {
            "exito": True,
            "mensaje": f"{len(hashtags)} hashtags generados para '{tema}'",
            "resultado": {
                "tema": tema,
                "hashtags": hashtags,
                "total": len(hashtags),
                "negocio": negocio,
            }
        }
    except Exception as e:
        logger.error(f"Error en generate_hashtags: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# Mapa de acciones
ACCIONES = {
    "generate_post": generate_post,
    "get_calendar": get_calendar,
    "save_draft": save_draft,
    "generate_hashtags": generate_hashtags,
}


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "ok",
            "motor": "social",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/status")
async def get_status():
    try:
        return {
            "motor": "social",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "total_borradores": len(borradores_db),
            "total_posts_historial": len(historial_posts),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.post("/execute")
async def execute(request: ExecuteRequest):
    try:
        accion = request.action.lower().strip()
        data = request.data or {}

        logger.info(f"Ejecutando acción: {accion}")

        if accion not in ACCIONES:
            acciones_disp = ", ".join(sorted(ACCIONES.keys()))
            _actualizar_estadisticas(False)
            return {
                "success": False,
                "result": None,
                "message": f"Acción '{accion}' no reconocida. Acciones disponibles: {acciones_disp}"
            }

        funcion = ACCIONES[accion]
        resultado = funcion(data)
        exito = resultado.get("exito", False)
        _actualizar_estadisticas(exito)

        return {
            "success": exito,
            "result": resultado.get("resultado"),
            "message": resultado.get("mensaje", "Acción ejecutada")
        }

    except Exception as e:
        logger.error(f"Error en execute: {e}", exc_info=True)
        _actualizar_estadisticas(False)
        return {
            "success": False,
            "result": None,
            "message": f"Error interno del servidor: {str(e)}"
        }


# ==================== INICIO ====================

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando Motor de Redes Sociales - NEXUS v3 en puerto 8005...")
    uvicorn.run(app, host="127.0.0.1", port=8005)

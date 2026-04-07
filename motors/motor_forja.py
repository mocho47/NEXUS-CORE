#!/usr/bin/env python3
"""
NEXUS v3 - Motor FORJA
Simplex - Motor de comunidad FORJA gestionado por NEXUS
Puerto: 8006
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
logger = logging.getLogger("motor_forja")

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
perfiles_db: Dict[str, dict] = {}
referidos_db: Dict[str, dict] = {}
comisiones_db: List[dict] = []
diagnosticos_db: Dict[str, dict] = {}

# ==================== SISTEMA DE DIAGNÓSTICO ====================

PREGUNTAS_DIAGNOSTICO = [
    {
        "id": 1,
        "pregunta": "¿Cuánto tiempo lleva operando tu negocio?",
        "opciones": [
            {"texto": "Aún no inicio", "valor": 0},
            {"texto": "Menos de 3 meses", "valor": 1},
            {"texto": "3 a 12 meses", "valor": 2},
            {"texto": "1 a 3 años", "valor": 3},
            {"texto": "Más de 3 años", "valor": 4},
        ],
        "categoria": "experiencia",
    },
    {
        "id": 2,
        "pregunta": "¿Tienes un plan de negocio documentado?",
        "opciones": [
            {"texto": "No, lo tengo en la cabeza", "valor": 0},
            {"texto": "Tengo notas sueltas", "valor": 1},
            {"texto": "Tengo un documento básico", "valor": 2},
            {"texto": "Tengo un plan estructurado", "valor": 3},
            {"texto": "Tengo plan + proyecciones financieras", "valor": 4},
        ],
        "categoria": "planificacion",
    },
    {
        "id": 3,
        "pregunta": "¿Cuál es tu mayor reto actualmente?",
        "opciones": [
            {"texto": "Conseguir clientes", "valor": 0},
            {"texto": "Manejar las finanzas", "valor": 1},
            {"texto": "Escalar el negocio", "valor": 2},
            {"texto": "Optimizar procesos", "valor": 3},
            {"texto": "Innovar en productos/servicios", "valor": 4},
        ],
        "categoria": "retos",
    },
    {
        "id": 4,
        "pregunta": "¿Cuántos clientes atiendes mensualmente?",
        "opciones": [
            {"texto": "Menos de 5", "valor": 0},
            {"texto": "5 a 15", "valor": 1},
            {"texto": "16 a 50", "valor": 2},
            {"texto": "51 a 150", "valor": 3},
            {"texto": "Más de 150", "valor": 4},
        ],
        "categoria": "clientes",
    },
    {
        "id": 5,
        "pregunta": "¿Tienes presencia en redes sociales?",
        "opciones": [
            {"texto": "No, no uso redes para mi negocio", "valor": 0},
            {"texto": "Tengo perfil pero publico poco", "valor": 1},
            {"texto": "Publico regularmente", "valor": 2},
            {"texto": "Tengo estrategia de contenido", "valor": 3},
            {"texto": "Genero clientes por redes", "valor": 4},
        ],
        "categoria": "marketing",
    },
    {
        "id": 6,
        "pregunta": "¿Cómo llevas tu contabilidad?",
        "opciones": [
            {"texto": "No llevo contabilidad", "valor": 0},
            {"texto": "Lo apunto en una libreta", "valor": 1},
            {"texto": "Uso Excel básico", "valor": 2},
            {"texto": "Uso software de contabilidad", "valor": 3},
            {"texto": "Tengo contador + software", "valor": 4},
        ],
        "categoria": "finanzas",
    },
    {
        "id": 7,
        "pregunta": "¿Tienes empleados o colaboradores?",
        "opciones": [
            {"texto": "Trabajo solo", "valor": 0},
            {"texto": "Tengo ayuda familiar no pagada", "valor": 1},
            {"texto": "1-2 colaboradores", "valor": 2},
            {"texto": "3-10 empleados", "valor": 3},
            {"texto": "Más de 10 empleados", "valor": 4},
        ],
        "categoria": "equipo",
    },
    {
        "id": 8,
        "pregunta": "¿Conoces tus márgenes de ganancia por producto/servicio?",
        "opciones": [
            {"texto": "No tengo idea", "valor": 0},
            {"texto": "Tengo una idea aproximada", "valor": 1},
            {"texto": "Conozco mis costos principales", "valor": 2},
            {"texto": "Tengo márgenes calculados por producto", "valor": 3},
            {"texto": "Analizo márgenes + punto de equilibrio", "valor": 4},
        ],
        "categoria": "finanzas",
    },
    {
        "id": 9,
        "pregunta": "¿Cómo es tu proceso de atención al cliente?",
        "opciones": [
            {"texto": "Informal, según me vaya saliendo", "valor": 0},
            {"texto": "Tengo un WhatsApp de negocio", "valor": 1},
            {"texto": "Respondo con ciertos horarios", "valor": 2},
            {"texto": "Tengo proceso definido + seguimiento", "valor": 3},
            {"texto": "Tengo CRM + automatizaciones", "valor": 4},
        ],
        "categoria": "clientes",
    },
    {
        "id": 10,
        "pregunta": "¿Qué porcentaje de tus clientes son recurrentes?",
        "opciones": [
            {"texto": "Menos del 10%", "valor": 0},
            {"texto": "10-25%", "valor": 1},
            {"texto": "25-50%", "valor": 2},
            {"texto": "50-75%", "valor": 3},
            {"texto": "Más del 75%", "valor": 4},
        ],
        "categoria": "clientes",
    },
    {
        "id": 11,
        "pregunta": "¿Inviertes en tu formación como emprendedor?",
        "opciones": [
            {"texto": "No, no tengo tiempo ni dinero", "valor": 0},
            {"texto": "Veja algunos videos de vez en cuando", "valor": 1},
            {"texto": "Tomo cursos online gratuitos", "valor": 2},
            {"texto": "Invierto en cursos y libros regularmente", "valor": 3},
            {"texto": "Tengo mentor + invierto en formación continua", "valor": 4},
        ],
        "categoria": "desarrollo",
    },
    {
        "id": 12,
        "pregunta": "¿Tu negocio tiene página web?",
        "opciones": [
            {"texto": "No tengo página web", "valor": 0},
            {"texto": "Tengo perfil de Google Maps", "valor": 1},
            {"texto": "Tengo una página web básica", "valor": 2},
            {"texto": "Tengo web + SEO básico", "valor": 3},
            {"texto": "Tengo web optimizada + genero leads", "valor": 4},
        ],
        "categoria": "marketing",
    },
    {
        "id": 13,
        "pregunta": "¿Cómo manejas el inventario (si aplica)?",
        "opciones": [
            {"texto": "No tengo control de inventario", "valor": 0},
            {"texto": "Lo reviso visualmente", "valor": 1},
            {"texto": "Tengo una lista en Excel", "valor": 2},
            {"texto": "Uso un software de inventario", "valor": 3},
            {"texto": "Sistema integrado + alertas automáticas", "valor": 4},
        ],
        "categoria": "operaciones",
    },
    {
        "id": 14,
        "pregunta": "¿Tienes metas claras para los próximos 6 meses?",
        "opciones": [
            {"texto": "No, voy día a día", "valor": 0},
            {"texto": "Tengo una idea vaga", "valor": 1},
            {"texto": "Tengo metas escritas", "valor": 2},
            {"texto": "Metas + planes de acción por meta", "valor": 3},
            {"texto": "Metas + KPIs + revisión semanal", "valor": 4},
        ],
        "categoria": "planificacion",
    },
    {
        "id": 15,
        "pregunta": "¿Qué tan estresado/a te sientes con tu negocio?",
        "opciones": [
            {"texto": "Extremadamente estresado/a", "valor": 0},
            {"texto": "Bastante estresado/a", "valor": 1},
            {"texto": "Moderadamente", "valor": 2},
            {"texto": "Poco estresado/a", "valor": 3},
            {"texto": "Manejo el estrés bien", "valor": 4},
        ],
        "categoria": "bienestar",
    },
    {
        "id": 16,
        "pregunta": "¿Has delegado tareas en tu negocio?",
        "opciones": [
            {"texto": "No, yo lo hago todo", "valor": 0},
            {"texto": "Delego cosas muy simples", "valor": 1},
            {"texto": "Delego tareas operativas", "valor": 2},
            {"texto": "Tengo equipo que opera sin mí", "valor": 3},
            {"texto": "Solo me dedico a la estrategia", "valor": 4},
        ],
        "categoria": "liderazgo",
    },
    {
        "id": 17,
        "pregunta": "¿Cómo evalúas el crecimiento de tu negocio?",
        "opciones": [
            {"texto": "No sé si crece o no", "valor": 0},
            {"texto": "Lo siento por la cantidad de trabajo", "valor": 1},
            {"texto": "Reviso ingresos mensuales", "valor": 2},
            {"texto": "Analizo ventas + gastos + ganancia", "valor": 3},
            {"texto": "Tengo dashboard con métricas clave", "valor": 4},
        ],
        "categoria": "finanzas",
    },
    {
        "id": 18,
        "pregunta": "¿Cuál es tu principal fortaleza como emprendedor?",
        "opciones": [
            {"texto": "Mi pasión y motivación", "valor": 1},
            {"texto": "Mi conocimiento técnico del producto", "valor": 2},
            {"texto": "Mi habilidad para vender", "valor": 2},
            {"texto": "Mi capacidad de resolver problemas", "valor": 3},
            {"texto": "Mi visión estratégica", "valor": 4},
        ],
        "categoria": "fortalezas",
    },
    {
        "id": 19,
        "pregunta": "¿Has recibido financiamiento o inversión?",
        "opciones": [
            {"texto": "No, todo es con mis recursos", "valor": 0},
            {"texto": "Presté dinero a familiares", "valor": 1},
            {"texto": "Tuve un crédito PYME", "valor": 2},
            {"texto": "Recibí inversión privada", "valor": 3},
            {"texto": "Tengo acceso a líneas de crédito", "valor": 4},
        ],
        "categoria": "finanzas",
    },
    {
        "id": 20,
        "pregunta": "¿En una escala del 1 al 10, qué tan feliz estás con tu negocio?",
        "opciones": [
            {"texto": "1-3: No muy feliz", "valor": 0},
            {"texto": "4-5: Podría estar mejor", "valor": 1},
            {"texto": "6-7: Razonablemente contento/a", "valor": 2},
            {"texto": "8-9: Bastante feliz", "valor": 3},
            {"texto": "10: ¡Amo lo que hago!", "valor": 4},
        ],
        "categoria": "bienestar",
    },
]

# ==================== PERFILES Y RECOMENDACIONES ====================

PERFILES_NEGOCIO = {
    "iniciante": {
        "rango_puntos": (0, 25),
        "titulo": "Iniciante",
        "color": "verde",
        "descripcion": "Estás en las primeras etapas de tu emprendimiento. ¡Eso es valentía!",
        "recomendaciones": [
            "Define tu propuesta de valor: ¿qué te hace diferente? Escríbelo en una frase.",
            "Crea un perfil de negocio en Google Maps y redes sociales. Es gratuito y necesario.",
            "Lleva un registro básico de ingresos y gastos desde el día 1. Un Excel basta.",
            "Habla con al menos 10 personas sobre tu negocio esta semana. La visibilidad es clave.",
            "Establece un presupuesto mínimo de marketing mensual, aunque sea $500 pesos.",
            "No intentes ser perfecto. Lanza, aprende, mejora.",
            "Únete a grupos de emprendedores en Facebook o WhatsApp. La comunidad ayuda.",
            "Define tus 3 metas principales para los próximos 90 días.",
        ]
    },
    "creciendo": {
        "rango_puntos": (26, 50),
        "titulo": "Creciendo",
        "color": "amarillo",
        "descripcion": "Tu negocio ya tiene base. Ahora es momento de profesionalizar.",
        "recomendaciones": [
            "Crea un plan de negocio formal si aún no lo tienes. Invierte 2 horas este fin de semana.",
            "Automatiza lo repetitivo: usa herramientas como WhatsApp Business y plantillas.",
            "Implementa un sistema de seguimiento de clientes (puede ser un Excel avanzado).",
            "Define precios basados en costos + margen, no por intuición.",
            "Publica contenido en redes al menos 3 veces por semana con horario fijo.",
            "Considera contratar ayuda para tareas operativas. Tu tiempo vale más.",
            "Analiza quiénes son tus mejores clientes y enfócate en ellos.",
            "Crea paquetes de productos/servicios para aumentar el ticket promedio.",
        ]
    },
    "consolidado": {
        "rango_puntos": (51, 70),
        "titulo": "Consolidado",
        "color": "azul",
        "descripcion": "Tu negocio es sólido. El siguiente nivel es la escalabilidad.",
        "recomendaciones": [
            "Implementa un CRM para gestionar relaciones con clientes de forma profesional.",
            "Diversifica tus fuentes de ingreso. ¿Qué servicio complementario puedes ofrecer?",
            "Crea procesos documentados para cada área del negocio. Esto te permite delegar.",
            "Invierte en formación continua: cursos, libros, conferencias.",
            "Establece alianzas estratégicas con negocios complementarios.",
            "Mide KPIs clave semanalmente: ventas, clientes nuevos, ticket promedio, costos.",
            "Considera abrir un segundo punto de venta o expandir tu zona de cobertura.",
            "Desarrolla un programa de referidos con tus clientes satisfechos.",
        ]
    },
    "experto": {
        "rango_puntos": (71, 100),
        "titulo": "Experto",
        "color": "dorado",
        "descripcion": "Eres un referente en tu sector. Piensa en grande.",
        "recomendaciones": [
            "Desarrolla una marca personal sólida como líder de tu industria.",
            "Explora oportunidades de franquicia o modelo de negocio replicable.",
            "Mentora a otros emprendedores. La enseñanza fortalece tu conocimiento.",
            "Considera la expansión digital: e-commerce, cursos online, consultoría.",
            "Optimiza tu estructura fiscal con un equipo contable especializado.",
            "Crea un sistema de gestión de talento si tienes equipo grande.",
            "Evalúa oportunidades de inversión y diversificación de portafolio.",
            "Piensa en legacy: ¿qué quieres que signifique tu negocio en 5 años?",
        ]
    },
}

# ==================== PERSONALIDAD NATHALYE ====================

FRASES_NATHALYE = {
    "saludo": [
        "¡Hola! Soy Nathalye y estoy aquí para acompañarte en tu camino emprendedor 💪",
        "¡Bienvenido/a! Me alegra mucho tenerte aquí. Vamos a construir algo increíble juntos ✨",
        "¡Qué gusto saludarte! En FORJA creemos en tu potencial, y yo estoy aquí para ayudarte a liberarlo 🌟",
    ],
    "motivacion": [
        "Vamos a construir algo increible juntos 💜",
        "Cada paso que das cuenta. No subestimes tu progreso 🚀",
        "El hecho de que estés aquí evaluando tu negocio ya te pone por encima del 90% 🏆",
        "Recuerda: Roma no se construyó en un día, pero se construyó. ¡Tu también lo harás! 🏛️",
        "Los emprendedores mexicanos somos especiales: salimos adelante con creatividad y corazón 💪🇲🇽",
    ],
    "reflexion": [
        "Tómate un momento para celebrar lo que has logrado. No todos se atreven a emprender 🙌",
        "Los desafíos son oportunidades disfrazadas. Juntos los transformaremos en aprendizajes 🌱",
        "Tu negocio es una extensión de quién eres. Cuidarlo es cuidarte a ti mismo 💜",
    ],
    "despedida": [
        "¡Aquí estoy para ti! Cuenta conmigo en cada paso de tu camino emprendedor 💜",
        "Recuerda: no estás solo/a en esto. FORJA es tu comunidad y yo soy tu coach 🤝",
        "¡Hasta la próxima! Sigue adelante, que grandes cosas te esperan ✨",
    ],
}

CONSEJOS_FORJA_NATHALYE = {
    "ventas": [
        "Para vender más, enfócate en resolver problemas reales de tus clientes. Pregúntales: ¿Qué es lo que más te frustra de [tu industria]? La respuesta es tu próxima oportunidad de venta.",
        "El follow-up es oro. El 80% de las ventas se cierran después del 5to contacto. No abandones después del primero. Crea un sistema de seguimiento.",
        "No vendas productos, vende transformaciones. A tus clientes no les importa tu servicio, les importa cómo se van a sentir después de usarlo.",
    ],
    "finanzas": [
        "Separa tu dinero personal del dinero del negocio desde el día 1. Abre una cuenta bancaria exclusiva. Tu negocio es una entidad independiente.",
        "Aplica la regla del 50/30/20: 50% para costos, 30% para reinversión, 20% para tu ganancia. Ajusta según tu etapa.",
        "Un negocio que no mide sus números es como conducir con los ojos cerrados. Dedica 30 minutos semanales a revisar tus finanzas.",
    ],
    "marketing": [
        "En México, las recomendaciones boca a boca son el marketing más poderoso. Sorprende a tus clientes y ellos traerán más clientes.",
        "No necesitas un presupuesto enorme para marketing. Necesitas consistencia. Publica 3 veces por semana en redes sociales durante 90 días y mira los resultados.",
        "Tu historia personal es tu mejor marketing. La gente compra de personas, no de logos. Comparte tu proceso, tus valores, tu por qué.",
    ],
    "mentalidad": [
        "El fracaso no es lo contrario del éxito, es parte del éxito. Cada 'no' te acerca al 'sí' que cambiará tu negocio.",
        "Rodéate de personas que piensen más grande que tú. Si eres el más inteligente de la habitación, estás en la habitación equivocada.",
        "La disciplina supera a la motivación. Habrá días que no tendrás ganas de trabajar. Trabaja de todas formas. La consistencia crea resultados.",
    ],
}

# ==================== SISTEMA DE REFERIDOS ====================

COMISIONES_NIVELES = {
    1: {"nombre": "Nivel 1", "porcentaje": 10, "descripcion": "Referidos directos"},
    2: {"nombre": "Nivel 2", "porcentaje": 5, "descripcion": "Referidos de tus referidos"},
    3: {"nombre": "Nivel 3", "porcentaje": 2, "descripcion": "Tercer nivel de referencia"},
}

# ==================== PLANTILLAS DE PLAN DE NEGOCIO ====================

PLANTILLAS_PLAN = [
    {
        "id": "plan_basico",
        "nombre": "Plan de Negocio Básico",
        "descripcion": "Plantilla para emprendedores que inician",
        "secciones": [
            "1. Resumen Ejecutivo",
            "2. Descripción del Negocio",
            "3. Análisis de Mercado",
            "4. Productos y Servicios",
            "5. Estrategia de Marketing",
            "6. Plan Financiero Básico",
            "7. Cronograma de 90 Días",
        ],
        "dificultad": "facil",
        "tiempo_estimado": "2-3 horas",
    },
    {
        "id": "plan_crecimiento",
        "nombre": "Plan de Crecimiento",
        "descripcion": "Para negocios que buscan escalar",
        "secciones": [
            "1. Diagnóstico Actual del Negocio",
            "2. Metas a 6 y 12 Meses",
            "3. Análisis FODA",
            "4. Estrategia de Escalamiento",
            "5. Plan de Marketing Digital",
            "6. Proyecciones Financieras",
            "7. Plan de Contratación",
            "8. KPIs y Métricas de Seguimiento",
        ],
        "dificultad": "medio",
        "tiempo_estimado": "4-6 horas",
    },
    {
        "id": "plan_digital",
        "nombre": "Plan de Transformación Digital",
        "descripcion": "Para negocios tradicionales que buscan digitalizarse",
        "secciones": [
            "1. Evaluación Digital Actual",
            "2. Objetivos Digitales",
            "3. Presencia en Redes Sociales",
            "4. Estrategia de E-commerce",
            "5. Herramientas Tecnológicas",
            "6. Presupuesto de Inversión Digital",
            "7. Métricas de Éxito Digital",
        ],
        "dificultad": "medio",
        "tiempo_estimado": "3-5 horas",
    },
    {
        "id": "plan_financiero",
        "nombre": "Plan Financiero Detallado",
        "descripcion": "Control financiero profesional para tu negocio",
        "secciones": [
            "1. Inventario de Ingresos",
            "2. Análisis de Costos Fijos y Variables",
            "3. Cálculo de Punto de Equilibrio",
            "4. Márgenes por Producto/Servicio",
            "5. Flujo de Caja Proyectado (3 meses)",
            "6. Presupuesto Mensual",
            "7. Estrategia de Precios",
            "8. Indicadores Financieros Clave",
        ],
        "dificultad": "avanzado",
        "tiempo_estimado": "5-8 horas",
    },
]


app = FastAPI(
    title="Motor FORJA - NEXUS v3",
    description="Motor de comunidad FORJA para emprendedores - Gestionado por NEXUS v3",
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


def _calcular_puntuacion(answers: list) -> dict:
    """Calcular puntuación del diagnóstico basado en las respuestas."""
    try:
        if not answers or len(answers) != 20:
            return {"exito": False, "error": "Se requieren exactamente 20 respuestas"}

        total_puntos = 0
        desglose_por_categoria = {}
        respuestas_detalle = []

        for i, respuesta in enumerate(answers):
            pregunta = PREGUNTAS_DIAGNOSTICO[i]
            categoria = pregunta["categoria"]

            # La respuesta puede ser el índice de la opción o el valor directo
            if isinstance(respuesta, dict):
                valor = respuesta.get("valor", respuesta.get("value", 0))
                texto = respuesta.get("texto", respuesta.get("text", ""))
            elif isinstance(respuesta, int):
                if 0 <= respuesta < len(pregunta["opciones"]):
                    valor = pregunta["opciones"][respuesta]["valor"]
                    texto = pregunta["opciones"][respuesta]["texto"]
                else:
                    valor = respuesta
                    texto = f"Respuesta {respuesta}"
            else:
                valor = 0
                texto = str(respuesta)

            total_puntos += valor

            if categoria not in desglose_por_categoria:
                desglose_por_categoria[categoria] = {"puntos": 0, "maximo": 0}
            desglose_por_categoria[categoria]["puntos"] += valor
            desglose_por_categoria[categoria]["maximo"] += 4

            respuestas_detalle.append({
                "pregunta_id": pregunta["id"],
                "pregunta": pregunta["pregunta"],
                "respuesta_texto": texto,
                "respuesta_valor": valor,
                "categoria": categoria,
            })

        # Determinar perfil
        porcentaje = (total_puntos / 80) * 100  # 80 es el máximo posible (20 preguntas × 4)
        perfil_key = None
        for key, perfil in PERFILES_NEGOCIO.items():
            rango = perfil["rango_puntos"]
            if rango[0] <= total_puntos <= rango[1]:
                perfil_key = key
                break

        if not perfil_key:
            perfil_key = "iniciante"

        perfil = PERFILES_NEGOCIO[perfil_key]

        return {
            "exito": True,
            "puntuacion_total": total_puntos,
            "puntuacion_maxima": 80,
            "porcentaje": round(porcentaje, 1),
            "perfil": perfil_key,
            "perfil_info": {
                "titulo": perfil["titulo"],
                "color": perfil["color"],
                "descripcion": perfil["descripcion"],
                "recomendaciones": perfil["recomendaciones"],
            },
            "desglose_categorias": desglose_por_categoria,
            "respuestas_detalle": respuestas_detalle,
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


# ==================== ACCIONES ====================

def diagnose(data: dict) -> dict:
    """Ejecutar diagnóstico de emprendimiento."""
    try:
        answers = data.get("answers", data.get("respuestas", []))
        usuario_id = data.get("user_id", data.get("usuario_id", str(uuid.uuid4())[:8]))

        if not answers or len(answers) != 20:
            return {
                "exito": False,
                "mensaje": "Se requieren exactamente 20 respuestas para el diagnóstico",
                "resultado": None
            }

        resultado = _calcular_puntuacion(answers)

        if not resultado.get("exito"):
            return {
                "exito": False,
                "mensaje": resultado.get("error", "Error al calcular puntuación"),
                "resultado": None
            }

        # Guardar diagnóstico
        diagnostico_id = str(uuid.uuid4())[:8]
        diagnostico = {
            "id": diagnostico_id,
            "usuario_id": usuario_id,
            "puntuacion": resultado["puntuacion_total"],
            "porcentaje": resultado["porcentaje"],
            "perfil": resultado["perfil"],
            "fecha": datetime.now().isoformat(),
        }
        diagnosticos_db[diagnostico_id] = diagnostico

        # Generar mensaje motivacional de Nathalye
        saludo = random.choice(FRASES_NATHALYE["saludo"])
        motivacion = random.choice(FRASES_NATHALYE["motivacion"])
        despedida = random.choice(FRASES_NATHALYE["despedida"])

        mensaje_nathalye = f"{saludo}\n\n"
        mensaje_nathalye += f"Tu resultado: {resultado['puntuacion_total']}/80 puntos ({resultado['porcentaje']}%)\n"
        mensaje_nathalye += f"Tu perfil: {resultado['perfil_info']['titulo']} 🎯\n\n"
        mensaje_nathalye += f"{resultado['perfil_info']['descripcion']}\n\n"
        mensaje_nathalye += f"📝 Recomendaciones para ti:\n"
        for i, rec in enumerate(resultado["perfil_info"]["recomendaciones"], 1):
            mensaje_nathalye += f"{i}. {rec}\n"
        mensaje_nathalye += f"\n{motivacion}\n\n{despedida}"

        # Crear o actualizar perfil del usuario
        perfiles_db[usuario_id] = {
            "usuario_id": usuario_id,
            "perfil": resultado["perfil"],
            "puntuacion": resultado["puntuacion_total"],
            "porcentaje": resultado["porcentaje"],
            "ultimo_diagnostico": diagnostico_id,
            "ultima_actualizacion": datetime.now().isoformat(),
        }

        logger.info(f"Diagnóstico completado: {usuario_id} -> {resultado['perfil']} ({resultado['puntuacion_total']}/80)")

        return {
            "exito": True,
            "mensaje": f"Diagnóstico completado. Tu perfil es: {resultado['perfil_info']['titulo']}",
            "resultado": {
                "diagnostico_id": diagnostico_id,
                "puntuacion": resultado["puntuacion_total"],
                "porcentaje": resultado["porcentaje"],
                "perfil": resultado["perfil"],
                "perfil_info": resultado["perfil_info"],
                "desglose_categorias": resultado["desglose_por_categoria"],
                "mensaje_nathalye": mensaje_nathalye,
            }
        }
    except Exception as e:
        logger.error(f"Error en diagnose: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_profile(data: dict) -> dict:
    """Obtener perfil de emprendedor."""
    try:
        usuario_id = data.get("user_id", data.get("usuario_id", ""))

        if not usuario_id:
            return {"exito": False, "mensaje": "Se requiere el ID de usuario", "resultado": None}

        perfil = perfiles_db.get(usuario_id)
        if not perfil:
            return {
                "exito": False,
                "mensaje": "No se encontró perfil para este usuario. Realiza un diagnóstico primero.",
                "resultado": None
            }

        # Obtener información completa del perfil
        perfil_info = PERFILES_NEGOCIO.get(perfil["perfil"], {})

        # Obtener historial de diagnósticos
        historial = [
            d for d in diagnosticos_db.values()
            if d.get("usuario_id") == usuario_id
        ]

        # Calcular referidos y comisiones
        mis_referidos = [
            r for r in referidos_db.values()
            if r.get("referente_id") == usuario_id
        ]
        mis_comisiones = [
            c for c in comisiones_db
            if c.get("beneficiario_id") == usuario_id
        ]
        total_comisiones = sum(c.get("monto", 0) for c in mis_comisiones)

        return {
            "exito": True,
            "mensaje": "Perfil de emprendedor obtenido",
            "resultado": {
                "usuario_id": usuario_id,
                "perfil": perfil["perfil"],
                "perfil_info": {
                    "titulo": perfil_info.get("titulo", perfil["perfil"]),
                    "color": perfil_info.get("color", "gris"),
                    "descripcion": perfil_info.get("descripcion", ""),
                    "recomendaciones": perfil_info.get("recomendaciones", []),
                },
                "puntuacion_actual": perfil["puntuacion"],
                "porcentaje": perfil["porcentaje"],
                "total_diagnosticos": len(historial),
                "total_referidos": len(mis_referidos),
                "total_comisiones": total_comisiones,
                "fecha_ultimo_diagnostico": perfil.get("ultima_actualizacion"),
            }
        }
    except Exception as e:
        logger.error(f"Error en get_profile: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def create_referral(data: dict) -> dict:
    """Crear un enlace de referido."""
    try:
        referente_id = data.get("referrer_id", data.get("referente_id", ""))
        nombre_nuevo = data.get("new_member_name", data.get("nombre_nuevo", ""))

        if not referente_id:
            return {"exito": False, "mensaje": "Se requiere el ID del referente", "resultado": None}

        if not nombre_nuevo:
            return {"exito": False, "mensaje": "Se requiere el nombre del nuevo miembro", "resultado": None}

        nuevo_id = str(uuid.uuid4())[:8]
        referido_id = str(uuid.uuid4())[:8]

        # Determinar nivel
        nivel = 1  # Por defecto es referido directo

        # Verificar si el referente fue referido por alguien (Nivel 2)
        for r in referidos_db.values():
            if r.get("nuevo_id") == referente_id:
                nivel = 2
                # Verificar si ese referente también fue referido (Nivel 3)
                for r2 in referidos_db.values():
                    if r2.get("nuevo_id") == r.get("referente_id"):
                        nivel = 3
                break

        # Crear registro de referido
        referido = {
            "id": referido_id,
            "referente_id": referente_id,
            "nuevo_id": nuevo_id,
            "nombre_nuevo": nombre_nuevo,
            "nivel": nivel,
            "fecha": datetime.now().isoformat(),
            "estado": "activo",
            "comision_pagada": False,
        }
        referidos_db[referido_id] = referido

        # Crear perfil básico para el nuevo miembro
        perfiles_db[nuevo_id] = {
            "usuario_id": nuevo_id,
            "nombre": nombre_nuevo,
            "perfil": None,
            "puntuacion": None,
            "referido_por": referente_id,
            "fecha_registro": datetime.now().isoformat(),
        }

        # Calcular comisión para cada nivel de la cadena
        cadena_comisiones = _calcular_cadena_comisiones(referente_id, nivel)

        logger.info(f"Referido creado: {nombre_nuevo} (Nivel {nivel}) por {referente_id}")

        return {
            "exito": True,
            "mensaje": f"Referido '{nombre_nuevo}' registrado exitosamente (Nivel {nivel})",
            "resultado": {
                "referido_id": referido_id,
                "nuevo_miembro_id": nuevo_id,
                "nombre_nuevo": nombre_nuevo,
                "nivel": nivel,
                "comisiones_generadas": cadena_comisiones,
                "enlace": f"forja.nexusv3.com/ref/{referente_id}",
            }
        }
    except Exception as e:
        logger.error(f"Error en create_referral: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def _calcular_cadena_comisiones(referente_id: str, nivel: int) -> list:
    """Calcular comisiones para la cadena de referidos."""
    comisiones = []
    monto_base = 500  # Comisión base por referido (ejemplo)

    # Recorrer la cadena de niveles
    id_actual = referente_id
    for n in range(1, nivel + 1):
        if n <= 3:
            info_nivel = COMISIONES_NIVELES.get(n, {})
            porcentaje = info_nivel.get("porcentaje", 0)
            monto = round(monto_base * porcentaje / 100, 2)

            comision = {
                "beneficiario_id": id_actual,
                "nivel": n,
                "porcentaje": porcentaje,
                "monto": monto,
                "fecha": datetime.now().isoformat(),
            }
            comisiones.append(comision)
            comisiones_db.append(comision)

            # Encontrar al referente de este referente
            for r in referidos_db.values():
                if r.get("nuevo_id") == id_actual:
                    id_actual = r.get("referente_id")
                    break

    return comisiones


def get_commissions(data: dict) -> dict:
    """Calcular comisiones MLM."""
    try:
        usuario_id = data.get("user_id", data.get("usuario_id", ""))

        if not usuario_id:
            return {"exito": False, "mensaje": "Se requiere el ID de usuario", "resultado": None}

        # Comisiones directas
        mis_comisiones = [c for c in comisiones_db if c.get("beneficiario_id") == usuario_id]

        # Comisiones por nivel
        por_nivel = {}
        for n in range(1, 4):
            comisiones_n = [c for c in mis_comisiones if c.get("nivel") == n]
            por_nivel[f"nivel_{n}"] = {
                "cantidad": len(comisiones_n),
                "total": round(sum(c.get("monto", 0) for c in comisiones_n), 2),
                "porcentaje": COMISIONES_NIVELES.get(n, {}).get("porcentaje", 0),
            }

        # Total
        total_comisiones = round(sum(c.get("monto", 0) for c in mis_comisiones), 2)

        # Referidos por nivel
        referidos_por_nivel = {}
        for n in range(1, 4):
            refs = [r for r in referidos_db.values() if r.get("referente_id") == usuario_id and r.get("nivel") == n]
            referidos_por_nivel[f"nivel_{n}"] = len(refs)

        return {
            "exito": True,
            "mensaje": "Comisiones calculadas exitosamente",
            "resultado": {
                "usuario_id": usuario_id,
                "total_comisiones": total_comisiones,
                "comisiones_por_nivel": por_nivel,
                "total_referidos": sum(referidos_por_nivel.values()),
                "referidos_por_nivel": referidos_por_nivel,
                "historial_comisiones": mis_comisiones,
                "estructura_comisiones": COMISIONES_NIVELES,
            }
        }
    except Exception as e:
        logger.error(f"Error en get_commissions: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def coach_message(data: dict) -> dict:
    """Obtener mensaje de coaching de Nathalye."""
    try:
        tema = data.get("topic", data.get("tema", "general"))
        contexto = data.get("context", data.get("contexto", ""))
        usuario_id = data.get("user_id", data.get("usuario_id", ""))

        # Seleccionar saludo, motivación y despedida
        saludo = random.choice(FRASES_NATHALYE["saludo"])

        # Buscar consejo específico
        tema_lower = tema.lower() if tema else ""
        consejo = None
        for cat, consejos in CONSEJOS_FORJA_NATHALYE.items():
            if tema_lower in cat or tema_lower in " ".join(consejos).lower():
                consejo = random.choice(consejos)
                break

        if not consejo:
            # Consejo general aleatorio
            todas_cats = list(CONSEJOS_FORJA_NATHALYE.values())
            consejo = random.choice(random.choice(todas_cats))

        motivacion = random.choice(FRASES_NATHALYE["motivacion"])
        despedida = random.choice(FRASES_NATHALYE["despedida"])

        # Personalizar si hay contexto
        contextual = ""
        if contexto:
            contextual = f"\n\nRespecto a lo que compartiste: {contexto}\n"

        # Construir mensaje completo
        mensaje = f"{saludo}\n\n"
        mensaje += f"💡 Consejo del día:\n{consejo}\n"
        mensaje += f"{contextual}"
        mensaje += f"\n{motivacion}\n\n{despedida}"

        logger.info(f"Mensaje de coaching generado para: {usuario_id or 'anónimo'}")

        return {
            "exito": True,
            "mensaje": "Mensaje de coaching generado por Nathalye",
            "resultado": {
                "coach": "Nathalye",
                "tema": tema,
                "mensaje": mensaje,
                "fecha": datetime.now().isoformat(),
            }
        }
    except Exception as e:
        logger.error(f"Error en coach_message: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def generate_plan(data: dict) -> dict:
    """Generar plan de acción de negocio."""
    try:
        usuario_id = data.get("user_id", data.get("usuario_id", ""))
        plan_id = data.get("plan_id", data.get("plantilla_id", "plan_basico"))
        negocio_nombre = data.get("business_name", data.get("nombre_negocio", "Mi Negocio"))
        nicho = data.get("niche", data.get("nicho", "general"))
        metas = data.get("goals", data.get("metas", []))

        # Buscar plantilla
        plantilla = None
        for p in PLANTILLAS_PLAN:
            if p["id"] == plan_id:
                plantilla = p
                break

        if not plantilla:
            plantilla = PLANTILLAS_PLAN[0]

        # Obtener perfil si existe
        perfil = perfiles_db.get(usuario_id, {}).get("perfil", "iniciante") if usuario_id else "iniciante"

        # Generar plan personalizado
        plan = {
            "id": str(uuid.uuid4())[:8],
            "plantilla": plantilla["id"],
            "nombre": plantilla["nombre"],
            "negocio": negocio_nombre,
            "nicho": nicho,
            "perfil_emprendedor": perfil,
            "fecha_generacion": datetime.now().isoformat(),
            "secciones": [],
        }

        # Generar contenido por sección
        for seccion in plantilla["secciones"]:
            contenido_seccion = _generar_contenido_seccion(seccion, perfil, negocio_nombre, nicho, metas)
            plan["secciones"].append({
                "titulo": seccion,
                "contenido": contenido_seccion,
                "completada": False,
            })

        # Agregar cronograma
        plan["cronograma"] = _generar_cronograma(plan["secciones"], plantilla["dificultad"])

        logger.info(f"Plan generado: {plantilla['nombre']} para {negocio_nombre}")

        return {
            "exito": True,
            "mensaje": f"Plan '{plantilla['nombre']}' generado exitosamente",
            "resultado": plan
        }
    except Exception as e:
        logger.error(f"Error en generate_plan: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def _generar_contenido_seccion(seccion: str, perfil: str, negocio: str, nicho: str, metas: list) -> str:
    """Generar contenido para una sección del plan."""
    metas_texto = "; ".join(metas) if metas else "no especificadas"

    contenido_base = {
        "1. Resumen Ejecutivo": f"Resumen de {negocio}:\n\n- Negocio: {negocio}\n- Nicho: {nicho}\n- Perfil del emprendedor: {perfil.capitalize()}\n- Metas principales: {metas_texto}\n- Fecha de creación: {datetime.now().strftime('%d/%m/%Y')}\n\nEste plan describe la estrategia y acciones para el crecimiento de {negocio}. Se basa en el perfil de emprendedor '{perfil.capitalize()}' y está diseñado para abordar los desafíos específicos de esta etapa.",
        "2. Descripción del Negocio": f"Descripción detallada de {negocio}:\n\n- Nombre: {negocio}\n- Sector: {nicho}\n- Propuesta de valor: [Describe qué te hace único/a]\n- Publico objetivo: [Define quién es tu cliente ideal]\n- Ubicación: [Física y/o digital]\n- Horario de atención: [Define tus horarios]\n\n💡 Tip: Tu propuesta de valor debe poder explicarse en una oración clara.",
        "3. Análisis de Mercado": f"Análisis del mercado para {negocio} ({nicho}):\n\n1. Tamaño del mercado: [Investiga cuántas personas podrían necesitar tu producto/servicio]\n2. Competencia: [Lista tus 3-5 competidores principales y qué hacen bien]\n3. Tendencias: [¿Hacia dónde va tu industria?]\n4. Oportunidades: [Qué huecos en el mercado puedes llenar]\n5. Amenazas: [Qué podría afectar tu negocio]\n\n💡 Tip: Visita Google Trends para investigar tendencias de tu sector.",
        "4. Productos y Servicios": f"Productos y servicios de {negocio}:\n\n[Listar cada producto/servicio con:]\n- Nombre\n- Descripción\n- Precio\n- Costo\n- Margen de ganancia\n- Demanda estimada\n\n💡 Tip: Calcula tu margen real: (Precio - Costo) / Precio × 100. Debe ser al menos 30%.",
        "5. Estrategia de Marketing": f"Estrategia de marketing para {negocio}:\n\n1. Redes sociales: [Define qué plataformas usar y con qué frecuencia]\n2. Contenido: [Qué tipo de contenido publicar]\n3. Promociones: [Qué ofertas especiales tendrás]\n4. Alianzas: [Con qué negocios puedes colaborar]\n5. Presencia digital: [Google Maps, página web]\n\nCalendario semanal sugerido:\n- Lunes: Contenido educativo\n- Miércoles: Producto/servicio\n- Viernes: Interacción con comunidad",
        "6. Plan Financiero Básico": f"Plan financiero de {negocio}:\n\nInversión inicial estimada: $[monto]\nCostos fijos mensuales: $[monto]\nCostos variables por venta: $[monto]\nPrecio promedio de venta: $[monto]\nPunto de equilibrio: [número] ventas/mes\nMeta de ventas mes 1: [número]\nMeta de ventas mes 3: [número]\nMeta de ventas mes 6: [número]\n\n💡 Regla de oro: siempre ten un fondo de emergencia de al menos 2 meses de gastos.",
        "7. Cronograma de 90 Días": f"Cronograma de 90 días para {negocio}:\n\nSemana 1-2: Setup inicial (perfiles, primer inventario, proceso de atención)\nSemana 3-4: Lanzamiento suave y primera semana de ventas\nMes 2: Optimización basada en feedback de los primeros clientes\nMes 3: Escalar lo que funciona, eliminar lo que no\n\nRevisión semanal: cada domingo 30 min para evaluar avances.",
    }

    # Buscar contenido base o generar uno genérico
    if seccion in contenido_base:
        return contenido_base[seccion]
    else:
        return (f"{seccion}\n\n{'=' * 50}\n\n"
                f"Trabaja en esta seccion con dedicacion.\n\n"
                f"Negocio: {negocio}\nNicho: {nicho}\nPerfil: {perfil}\n\n"
                f"Acciones sugeridas:\n"
                f"1. Investiga ejemplos de otros negocios en tu sector\n"
                f"2. Adapta las mejores practicas a tu realidad\n"
                f"3. Define indicadores claros de exito\n"
                f"4. Establece fechas limite para cada accion\n"
                f"5. Revisa y ajusta mensualmente\n\n"
                f"Recuerda: Un plan vivo es mejor que un plan perfecto.")


def _generar_cronograma(secciones: list, dificultad: str) -> list:
    """Generar cronograma de trabajo para el plan."""
    dias_totales = {"facil": 30, "medio": 60, "avanzado": 90}.get(dificultad, 30)
    dias_por_seccion = max(1, dias_totales // max(len(secciones), 1))

    cronograma = []
    dia_inicio = 1
    hoy = datetime.now()

    for i, seccion in enumerate(secciones):
        dia_fin = min(dia_inicio + dias_por_seccion - 1, dias_totales)
        fecha_inicio = hoy + timedelta(days=dia_inicio - 1)
        fecha_fin = hoy + timedelta(days=dia_fin - 1)

        cronograma.append({
            "seccion": seccion["titulo"],
            "dia_inicio": dia_inicio,
            "dia_fin": dia_fin,
            "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
            "prioridad": "alta" if i < 2 else "media" if i < 4 else "normal",
            "completada": False,
        })
        dia_inicio = dia_fin + 1

    return cronograma


# Mapa de acciones
ACCIONES = {
    "diagnose": diagnose,
    "get_profile": get_profile,
    "create_referral": create_referral,
    "get_commissions": get_commissions,
    "coach_message": coach_message,
    "generate_plan": generate_plan,
}


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "ok",
            "motor": "forja",
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
            "motor": "forja",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "total_perfiles": len(perfiles_db),
            "total_referidos": len(referidos_db),
            "total_diagnosticos": len(diagnosticos_db),
            "total_comisiones": sum(c.get("monto", 0) for c in comisiones_db),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.get("/diagnostic_questions")
async def diagnostic_questions():
    """Obtener las 20 preguntas del diagnóstico."""
    try:
        # Devolver preguntas sin respuestas (para el formulario)
        preguntas_formulario = []
        for p in PREGUNTAS_DIAGNOSTICO:
            preguntas_formulario.append({
                "id": p["id"],
                "pregunta": p["pregunta"],
                "categoria": p["categoria"],
                "opciones": [
                    {"indice": i, "texto": op["texto"]}
                    for i, op in enumerate(p["opciones"])
                ],
            })

        return {
            "success": True,
            "result": {
                "total_preguntas": len(preguntas_formulario),
                "categorias": list(set(p["categoria"] for p in PREGUNTAS_DIAGNOSTICO)),
                "preguntas": preguntas_formulario,
            },
            "message": f"{len(preguntas_formulario)} preguntas del diagnóstico FORJA"
        }
    except Exception as e:
        logger.error(f"Error en /diagnostic_questions: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener preguntas")


@app.get("/business_templates")
async def business_templates():
    """Obtener plantillas de plan de negocio."""
    try:
        return {
            "success": True,
            "result": {
                "total": len(PLANTILLAS_PLAN),
                "plantillas": PLANTILLAS_PLAN,
            },
            "message": f"{len(PLANTILLAS_PLAN)} plantillas de plan de negocio disponibles"
        }
    except Exception as e:
        logger.error(f"Error en /business_templates: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener plantillas")


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
    logger.info("Iniciando Motor FORJA - NEXUS v3 en puerto 8006...")
    uvicorn.run(app, host="127.0.0.1", port=8006)

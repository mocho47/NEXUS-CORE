#!/usr/bin/env python3
"""
NEXUS v3 - Motor de Coaching
Simplex - Motor de psicología, misiones familiares y coaching
Puerto: 8004
"""

import logging
import time
import sys
import uuid
import random
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("motor_coaching")

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
misiones_db: Dict[str, dict] = {}
miembros_db: Dict[str, dict] = {"familia": {}}
notas_coaching: List[dict] = []
configuracion_pin = "1234"

app = FastAPI(
    title="Motor de Coaching - NEXUS v3",
    description="Motor de psicología, misiones familiares y coaching para NEXUS v3",
    version="3.0.0"
)


# ==================== CONTENIDO PSICOLÓGICO ====================

CONSEJOS_EMPRENDEDOR = [
    {
        "id": 1, "titulo": "Gestiona tu energía, no solo tu tiempo",
        "contenido": "Como emprendedor, tu energía es tu recurso más valioso. Identifica las horas del día en que estás más productivo y reserva esas para las tareas más importantes. No intentes hacerlo todo: delega lo que puedas.",
        "categoria": "productividad"
    },
    {
        "id": 2, "titulo": "Acepta la incertidumbre como parte del camino",
        "contenido": "La incertidumbre no es tu enemiga, es el campo de juego del emprendedor. Cada gran negocio nació de alguien que decidió actuar sin tener todas las respuestas. Confía en tu capacidad de adaptarte.",
        "categoria": "mentalidad"
    },
    {
        "id": 3, "titulo": "Celebra las pequeñas victorias",
        "contenido": "El camino emprendedor es largo. Si solo celebras los logros grandes, te agotarás. Reconoce cada cliente nuevo, cada problema resuelto, cada día que aprendiste algo nuevo. La motivación se construye con pequeños pasos.",
        "categoria": "motivacion"
    },
    {
        "id": 4, "titulo": "Aprende a decir 'no'",
        "contenido": "No todas las oportunidades son buenas oportunidades. Decir 'no' a lo que no te alinea te permite decir 'sí' a lo que realmente importa. Tu tiempo es limitado; inviértelo sabiamente.",
        "categoria": "decisiones"
    },
    {
        "id": 5, "titulo": "El fracaso es información, no derrota",
        "contenido": "Cada error te enseña algo que el éxito no puede. Analiza qué salió mal, ajusta tu enfoque y vuelve a intentarlo. Los emprendedores exitosos no fracasan menos, se recuperan más rápido.",
        "categoria": "resiliencia"
    },
    {
        "id": 6, "titulo": "Cuida tu salud mental primero",
        "contenido": "No puedes construir un negocio exitoso con una mente agotada. Duerme bien, haz ejercicio, come nutritiousamente. Tu salud es el cimiento de todo lo que construyes.",
        "categoria": "salud"
    },
    {
        "id": 7, "titulo": "Rodéate de personas que te impulsen",
        "contenido": "Tu entorno define tu trayectoria. Busca mentores, únete a comunidades de emprendedores, aléjate de quienes solo ven problemas. Las personas correctas pueden cambiar todo.",
        "categoria": "redes"
    },
    {
        "id": 8, "titulo": "Automatiza lo repetitivo",
        "contenido": "Si haces la misma tarea más de tres veces, encuentra la forma de automatizarla. Usa herramientas digitales, crea plantillas, delega. Tu creatividad debe ir a la innovación, no a la repetición.",
        "categoria": "productividad"
    },
    {
        "id": 9, "titulo": "Define tu 'por qué' claramente",
        "contenido": "Cuando las cosas se pongan difíciles (y lo harán), necesitas saber por qué empezaste. Tu propósito es tu brújula. Escríbelo, léeelo cada día y que te recuerde por qué vale la pena seguir.",
        "categoria": "proposito"
    },
    {
        "id": 10, "titulo": "La perfección es el enemigo de la acción",
        "contenido": "Lanza tu producto o servicio aunque no sea perfecto. El mercado te dará retroalimentación real que ningún plan de negocio puede predecir. Mejorar es más importante que ser perfecto desde el inicio.",
        "categoria": "mentalidad"
    },
    {
        "id": 11, "titulo": "Diversifica tus fuentes de ingreso",
        "contenido": "Depender de un solo cliente o producto es riesgoso. Busca crear múltiples fuentes de ingreso que complementen tu negocio principal. La estabilidad financiera te da libertad para innovar.",
        "categoria": "finanzas"
    },
    {
        "id": 12, "titulo": "Invierte en aprender constantemente",
        "contenido": "El conocimiento es tu mejor inversión. Lee libros, toma cursos, asiste a eventos. Cada hora que pasas aprendiendo te ahorra decenas de horas de errores en el futuro.",
        "categoria": "aprendizaje"
    },
    {
        "id": 13, "titulo": "No compares tu capítulo 1 con el capítulo 20 de otro",
        "contenido": "Las redes sociales muestran los mejores momentos de los demás. Cada negocio tiene su propio ritmo. Concéntrate en tu progreso, no en el de los demás.",
        "categoria": "mentalidad"
    },
    {
        "id": 14, "titulo": "Establece límites claros entre trabajo y familia",
        "contenido": "El agotamiento no es una medalla de honor. Define horarios, respétalos y enseña a tus clientes y familia que tu tiempo tiene valor. Un emprendedor descansado toma mejores decisiones.",
        "categoria": "equilibrio"
    },
    {
        "id": 15, "titulo": "Haz números antes de emociones",
        "contenido": "Las decisiones de negocio deben basarse en datos, no solo en intuición. Mide tus resultados, analiza tus costos y toma decisiones informadas. La pasión mueve, pero los datos guían.",
        "categoria": "finanzas"
    },
    {
        "id": 16, "titulo": "Construye una marca personal auténtica",
        "contenido": "La gente compra a personas, no solo productos. Sé auténtico, comparte tu historia, muestra tus valores. La confianza es la moneda más valiosa del negocio moderno.",
        "categoria": "marca"
    },
    {
        "id": 17, "titulo": "Planifica, pero mantente flexible",
        "contenido": "Un plan de negocio es importante, pero rigidizarte a él puede ser fatal. El mercado cambia, los clientes evolucionan. Sé firme en tu visión pero flexible en tu estrategia.",
        "categoria": "estrategia"
    },
    {
        "id": 18, "titulo": "El servicio al cliente es tu mejor marketing",
        "contenido": "Un cliente satisfecho trae tres más. Un cliente decepcionado aleja a diez. Invierte en la experiencia de tus clientes: responde rápido, soluciona problemas, supera expectativas.",
        "categoria": "clientes"
    },
    {
        "id": 19, "titulo": "Reconoce cuándo necesitas ayuda profesional",
        "contenido": "Un contador, un abogado, un terapeuta, un coach: pedir ayuda no es debilidad, es inteligencia. No necesitas saberlo todo, necesitas saber a quién preguntar.",
        "categoria": "salud"
    },
    {
        "id": 20, "titulo": "Tu negocio no eres tú",
        "contenido": "Si el negocio fracasa, tú no eres un fracaso. Separa tu identidad de tu empresa. Eres un ser humano completo con muchos talentos. Un negocio es solo uno de los caminos que puedes tomar.",
        "categoria": "mentalidad"
    },
]

CONSEJOS_JOVEN = [
    {
        "id": 1, "titulo": "Tu valor no depende de los likes",
        "contenido": "Las redes sociales muestran una versión editada de la realidad. Tu verdadero valor está en quién eres, no en cuántos seguidores tienes. Invierte en desarrollar tus talentos reales.",
        "categoria": "autoestima"
    },
    {
        "id": 2, "titulo": "Aprende a estudiar de forma inteligente",
        "contenido": "No se trata de estudiar más horas, sino de estudiar mejor. Usa la técnica Pomodoro (25 min estudio, 5 min descanso), haz resúmenes con tus palabras, enseña lo que aprendes a otros. La repetición espaciada es tu aliada.",
        "categoria": "estudio"
    },
    {
        "id": 3, "titulo": "Tus emociones son válidas, todas",
        "contenido": "Estar triste no es debilidad. Enojarse no es malo. Sentir miedo no es cobardía. Todas las emociones tienen información importante. Lo que importa es cómo decides actuar al respecto.",
        "categoria": "emociones"
    },
    {
        "id": 4, "titulo": "Desarrolla tu inteligencia emocional",
        "contenido": "Reconocer tus emociones y las de los demás es tan importante como ser bueno en matemáticas. Practica preguntarte '¿Qué siento ahora mismo?' varias veces al día. La autoconciencia cambia todo.",
        "categoria": "emociones"
    },
    {
        "id": 5, "titulo": "No tienes que tenerlo todo resuelto",
        "contenido": "A tu edad, lo normal es no saber qué hacer con tu vida. Explora, prueba cosas nuevas, equivócate. La presión por saberlo todo desde joven es una trampa. Descubre paso a paso.",
        "categoria": "autoestima"
    },
    {
        "id": 6, "titulo": "Elige a tus amigos con cuidado",
        "contenido": "Eres el promedio de las cinco personas con las que más tiempo pasas. Rodéate de personas que te inspiren, que te escuchen, que te desafíen a ser mejor. Deja ir relaciones tóxicas sin culpa.",
        "categoria": "relaciones"
    },
    {
        "id": 7, "titulo": "El fracaso escolar no te define",
        "contenido": "Una mala calificación no significa que eres incapaz. El sistema educativo no mide todos los talentos. Encuentra lo que se te da bien y poténcialo. Hay mil formas de ser exitoso.",
        "categoria": "autoestima"
    },
    {
        "id": 8, "titulo": "Aprende a comunicarte con asertividad",
        "contenido": "Decir lo que piensas sin lastimar a los demás es una superpotencia. Practica empezar oraciones con 'Yo siento...' en lugar de 'Tú siempre...'. La comunicación asertiva te abre puertas en todas las áreas.",
        "categoria": "comunicacion"
    },
    {
        "id": 9, "titulo": "Cuida tu cuerpo, es tu casa",
        "contenido": "Dormir bien, hacer ejercicio y comer sano no es solo para deportistas. Tu cerebro funciona mejor cuando tu cuerpo está cuidado. Empieza con pequeños cambios: camina 20 minutos al día.",
        "categoria": "salud"
    },
    {
        "id": 10, "titulo": "Lee, aunque no sea obligatorio",
        "contenido": "La lectura expande tu mente de formas que las redes sociales no pueden. Empieza con temas que te apasionen: deportes, ciencia ficción, biografías. 15 minutos al día pueden cambiar tu vida.",
        "categoria": "aprendizaje"
    },
    {
        "id": 11, "titulo": "Aprende a manejar la ansiedad",
        "contenido": "Si sientes ansiedad, respira profundo: inhala 4 segundos, mantén 7, exhala 8. Repítelo 3 veces. Habla con alguien de confianza. La ansiedad es como una alarma: escúchala, no la ignores, pero no dejes que te paralice.",
        "categoria": "salud"
    },
    {
        "id": 12, "titulo": "Desarrolla un pasatiempo que te apasione",
        "contenido": "Tener algo que te apasione fuera de la escuela te da identidad y propósito. Puede ser arte, música, programación, cocina, deportes. Lo importante es que sea tuyo y te haga feliz.",
        "categoria": "autoestima"
    },
    {
        "id": 13, "titulo": "No compares tu vida con la de los demás",
        "contenido": "Cada persona tiene su propio tiempo y camino. Lo que funciona para otro puede no funcionar para ti. Concéntrate en tu propio progreso y celebra tus avances, por pequeños que sean.",
        "categoria": "mentalidad"
    },
    {
        "id": 14, "titulo": "Emprende desde joven",
        "contenido": "No necesitas ser adulto para empezar un negocio. Vender algo que haces, ofrecer un servicio, crear contenido. El emprendimiento te enseña responsabilidad, creatividad y resiliencia. Empieza hoy.",
        "categoria": "emprendimiento"
    },
    {
        "id": 15, "titulo": "Pide ayuda cuando la necesites",
        "contenido": "Pedir ayuda no es debilidad, es valentía. Si algo te preocupa, si te sientes mal, si no entiendes algo: habla con un adulto de confianza. No tienes que cargar todo solo.",
        "categoria": "salud"
    },
]

CONSEJOS_PADRE = [
    {
        "id": 1, "titulo": "La conexión es más importante que la perfección",
        "contenido": "No necesitas ser el padre/madre perfecto. Lo que tus hijos necesitan es sentirse amados y escuchados. Un momento de atención genuina vale más que un día entero de actividades perfectas.",
        "categoria": "vinculo"
    },
    {
        "id": 2, "titulo": "Escucha antes de corregir",
        "contenido": "Cuando tu hijo venga con un problema, resiste el impulso de solucionarlo inmediatamente. Primero escucha, valida sus emociones ('Entiendo que te sientas así') y luego, si te pide ayuda, ofrécela.",
        "categoria": "comunicacion"
    },
    {
        "id": 3, "titulo": "Los límites son actos de amor",
        "contenido": "Poner límites no es ser autoritario, es enseñar responsabilidad. Un niño con límites claros se siente más seguro. Explica el por qué de las reglas, no solo el qué.",
        "categoria": "limites"
    },
    {
        "id": 4, "titulo": "Modela las emociones que quieres enseñar",
        "contenido": "Los niños aprenden más de lo que ven que de lo que escuchan. Si quieres que tu hijo maneje la frustración, muestra cómo tú la manejas. Si quieres que lea, léete tú primero.",
        "categoria": "modelado"
    },
    {
        "id": 5, "titulo": "Calidad de tiempo sobre cantidad",
        "contenido": "15 minutos de atención completa (sin celular) valen más que 2 horas de presencia física distraída. Busca momentos de conexión real: jugar, caminar, cocinar juntos.",
        "categoria": "vinculo"
    },
    {
        "id": 6, "titulo": "No pidas a tus hijos lo que no puedes dar",
        "contenido": "Si quieres que tu hijo no use el celular en la mesa, tú tampoco deberías. La coherencia entre lo que dices y lo que haces construye confianza y respeto.",
        "categoria": "coherencia"
    },
    {
        "id": 7, "titulo": "El refuerzo positivo transforma el comportamiento",
        "contenido": "En lugar de castigar lo malo, celebra lo bueno. 'Me gustó cómo compartiste tu juguete' es más efectivo que 'No seas egoísta'. Lo que prestas atención crece.",
        "categoria": "disciplina"
    },
    {
        "id": 8, "titulo": "Permítete ser imperfecto delante de tus hijos",
        "contenido": "Pedir perdón cuando te equivocas les enseña que los errores son normales y que las relaciones pueden repararse. 'Perdón por gritar, estaba estresado pero no debí reaccionar así' es una lección poderosa.",
        "categoria": "vulnerabilidad"
    },
    {
        "id": 9, "titulo": "Conoce la etapa de desarrollo de tu hijo",
        "contenido": "Un berrinche de 2 años no es lo mismo que uno de 12 años. Entender lo que es normal para cada edad te ahorra frustración y te permite responder adecuadamente. Invierte en aprender sobre desarrollo infantil.",
        "categoria": "desarrollo"
    },
    {
        "id": 10, "titulo": "Cuida tu pareja (si la tienes)",
        "contenido": "La mejor cosa que puedes hacer por tus hijos es tener una relación sana con tu pareja. La tensión entre padres afecta profundamente a los hijos. Dediquen tiempo a su relación.",
        "categoria": "pareja"
    },
    {
        "id": 11, "titulo": "Fomenta la autonomía gradualmente",
        "contenido": "A los 3 años que se vista solo, a los 7 que haga su tarea sin supervisión, a los 12 que maneje su dinero. Cada responsabilidad que delegas es un voto de confianza en su capacidad.",
        "categoria": "autonomia"
    },
    {
        "id": 12, "titulo": "La rutina es tu mejor aliada",
        "contenido": "Los niños prosperan con estructura. Horarios de sueño, de comida, de estudio consistentes reducen conflictos y dan seguridad. La predictibilidad reduce la ansiedad infantil.",
        "categoria": "rutina"
    },
    {
        "id": 13, "titulo": "Evita las etiquetas negativas",
        "contenido": "Decir 'eres tonto' o 'eres vago' se convierte en una profecía autocumplida. Separa al niño del comportamiento: 'Esa no fue una buena decisión' en lugar de 'Eres irresponsable'.",
        "categoria": "comunicacion"
    },
    {
        "id": 14, "titulo": "Tómate tiempo para ti",
        "contenido": "Un padre agotado no puede dar lo mejor a sus hijos. No es egoísmo cuidar de ti: es necesidad. Salir a caminar, leer, tener un hobby. Necesitas recargarte para poder dar.",
        "categoria": "autocuidado"
    },
    {
        "id": 15, "titulo": "La familia es un equipo, no una dictadura",
        "contenido": "Involucra a tus hijos en las decisiones familiares apropiadas para su edad. Una familia donde todos se sienten escuchados y valorados funciona mejor que una basada en obediencia ciega.",
        "categoria": "familia"
    },
]

CONSEJOS_POR_TIPO = {
    "emprendedor": CONSEJOS_EMPRENDEDOR,
    "joven": CONSEJOS_JOVEN,
    "padre": CONSEJOS_PADRE,
}

# ==================== PLANTILLAS DE MISIONES ====================

PLANTILLAS_MISIONES = [
    {
        "id": "m1", "titulo": "Ordenar tu cuarto", "descripcion": "Deja tu cuarto limpio y ordenado antes de cenar",
        "dificultad": "facil", "puntos": 10, "categoria": "tarea"
    },
    {
        "id": "m2", "titulo": "Lavar los platos", "descripcion": "Lava y guarda los platos de la comida sin que te lo pidan",
        "dificultad": "facil", "puntos": 10, "categoria": "tarea"
    },
    {
        "id": "m3", "titulo": "Leer 30 minutos", "descripcion": "Lee un libro durante al menos 30 minutos sin interrupciones",
        "dificultad": "facil", "puntos": 15, "categoria": "estudio"
    },
    {
        "id": "m4", "titulo": "Hacer ejercicio 20 minutos", "descripcion": "Realiza al menos 20 minutos de ejercicio (correr, saltar, estirar)",
        "dificultad": "medio", "puntos": 25, "categoria": "salud"
    },
    {
        "id": "m5", "titulo": "Completar tarea escolar", "descripcion": "Termina toda tu tarea del día sin procrastinar",
        "dificultad": "medio", "puntos": 25, "categoria": "estudio"
    },
    {
        "id": "m6", "titulo": "Ayudar a cocinar", "descripcion": "Ayuda a preparar la comida de la familia siguiendo instrucciones",
        "dificultad": "medio", "puntos": 25, "categoria": "familia"
    },
    {
        "id": "m7", "titulo": "Juego familiar completo", "descripcion": "Participa activamente en una actividad familiar (juego de mesa, caminata) por al menos 1 hora",
        "dificultad": "medio", "puntos": 30, "categoria": "familia"
    },
    {
        "id": "m8", "titulo": "Aprender algo nuevo", "descripcion": "Dedica tiempo a aprender una habilidad nueva (programar, dibujar, tocar instrumento) por 45 minutos",
        "dificultad": "medio", "puntos": 25, "categoria": "desarrollo"
    },
    {
        "id": "m9", "titulo": "Escribir en tu diario", "descripcion": "Escribe al menos una página sobre tu día, tus sentimientos o tus metas",
        "dificultad": "facil", "puntos": 15, "categoria": "bienestar"
    },
    {
        "id": "m10", "titulo": "Meditar 10 minutos", "descripcion": "Practica meditación o respiración consciente durante 10 minutos",
        "dificultad": "facil", "puntos": 10, "categoria": "bienestar"
    },
    {
        "id": "m11", "titulo": "Completar proyecto escolar", "descripcion": "Termina un proyecto escolar completo con calidad antes de la fecha límite",
        "dificultad": "dificil", "puntos": 50, "categoria": "estudio"
    },
    {
        "id": "m12", "titulo": "Limpieza general de la casa", "descripcion": "Ayuda con una limpieza profunda de un área común (sala, cocina, baño)",
        "dificultad": "dificil", "puntos": 50, "categoria": "tarea"
    },
    {
        "id": "m13", "titulo": "Ejercicio 45 minutos", "descripcion": "Completa una rutina de ejercicio de 45 minutos o más",
        "dificultad": "dificil", "puntos": 40, "categoria": "salud"
    },
    {
        "id": "m14", "titulo": "Leer un libro completo", "descripcion": "Termina de leer un libro completo (mínimo 100 páginas)",
        "dificultad": "dificil", "puntos": 50, "categoria": "estudio"
    },
    {
        "id": "m15", "titulo": "Enseñar algo a un familiar", "descripcion": "Prepara y enseña algo que sabes a otro miembro de la familia (un truco, un tema, una receta)",
        "dificultad": "medio", "puntos": 30, "categoria": "familia"
    },
]

# ==================== CATÁLOGO DE RECOMPENSAS ====================

CATALOGO_RECOMPENSAS = [
    {"id": "r1", "nombre": "Tiempo extra de pantalla (30 min)", "costo_puntos": 20, "descripcion": "30 minutos adicionales de pantalla"},
    {"id": "r2", "nombre": "Elegir la cena", "costo_puntos": 30, "descripcion": "Puedes elegir qué comer en la cena familiar"},
    {"id": "r3", "nombre": "Saltar una tarea", "costo_puntos": 25, "descripcion": "Puedes saltar una tarea del hogar (no acumulable)"},
    {"id": "r4", "nombre": "Día sin quehaceres", "costo_puntos": 100, "descripcion": "Un día libre de todas las tareas del hogar"},
    {"id": "r5", "nombre": "Cena especial", "costo_puntos": 75, "descripcion": "Preparar tu comida favorita como familia"},
    {"id": "r6", "nombre": "Noche de películas", "costo_puntos": 40, "descripcion": "Elegir película y noche especial de pelis"},
    {"id": "r7", "nombre": "Salida con la familia", "costo_puntos": 150, "descripcion": "Organizar una salida familiar (parque, cine, etc.)"},
    {"id": "r8", "nombre": "Compra sorpresa ($100)", "costo_puntos": 80, "descripcion": "Un artículo sorpresa de hasta $100 pesos"},
    {"id": "r9", "nombre": "Despertar tarde (fin de semana)", "costo_puntos": 35, "descripcion": "Puedes despertar 1 hora más tarde el fin de semana"},
    {"id": "r10", "nombre": "Elegir actividad familiar", "costo_puntos": 50, "descripcion": "Decidir la actividad familiar del fin de semana"},
]

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


def _obtener_o_crear_miembro(nombre: str) -> dict:
    """Obtener o crear un miembro de la familia."""
    if nombre not in miembros_db["familia"]:
        miembros_db["familia"][nombre] = {
            "nombre": nombre,
            "puntos": 0,
            "misiones_completadas": 0,
            "recompensas_canjeadas": 0,
            "fecha_registro": datetime.now().isoformat(),
        }
    return miembros_db["familia"][nombre]


def _sumar_puntos(nombre: str, puntos: int):
    """Sumar puntos a un miembro."""
    miembro = _obtener_o_crear_miembro(nombre)
    miembro["puntos"] += puntos


def _restar_puntos(nombre: str, puntos: int) -> bool:
    """Restar puntos a un miembro. Retorna False si no tiene suficientes."""
    miembro = _obtener_o_crear_miembro(nombre)
    if miembro["puntos"] < puntos:
        return False
    miembro["puntos"] -= puntos
    miembro["recompensas_canjeadas"] += 1
    return True


# ==================== ACCIONES ====================

def coach_message(data: dict) -> dict:
    """Generar mensaje de coaching para un tema específico."""
    try:
        topic = data.get("topic", data.get("tema", ""))
        tipo = data.get("type", data.get("tipo", "emprendedor"))

        if tipo not in CONSEJOS_POR_TIPO:
            return {
                "exito": False,
                "mensaje": f"Tipo no reconocido. Tipos válidos: {', '.join(CONSEJOS_POR_TIPO.keys())}",
                "resultado": None
            }

        consejos = CONSEJOS_POR_TIPO[tipo]

        # Buscar consejo relacionado con el tema
        consejo = None
        topic_lower = topic.lower() if topic else ""
        for c in consejos:
            if topic_lower and (topic_lower in c["titulo"].lower() or topic_lower in c["contenido"].lower() or topic_lower in c["categoria"]):
                consejo = c
                break

        # Si no hay tema específico, dar un consejo aleatorio
        if not consejo:
            consejo = random.choice(consejos)

        # Generar mensaje de coaching completo
        saludos = {
            "emprendedor": "Hola, emprendedor. Aquí tienes un consejo que puede marcar la diferencia en tu día.",
            "joven": "¡Hola! Aquí tienes algo pensado especialmente para ti.",
            "padre": "Hola, papá/mamá. Criar no es fácil, pero estás haciendo un gran trabajo.",
        }

        mensaje = {
            "saludo": saludos.get(tipo, "Hola."),
            "consejo_titulo": consejo["titulo"],
            "consejo_contenido": consejo["contenido"],
            "categoria": consejo["categoria"],
            "tipo": tipo,
            "reflexion": f"Tómate un momento para reflexionar sobre esto: {consejo['titulo'].lower()}. ¿Cómo puedes aplicarlo hoy?",
        }

        return {
            "exito": True,
            "mensaje": "Mensaje de coaching generado exitosamente",
            "resultado": mensaje
        }
    except Exception as e:
        logger.error(f"Error en coach_message: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def create_mission(data: dict) -> dict:
    """Crear una nueva misión familiar."""
    try:
        titulo = data.get("title", data.get("titulo", ""))
        descripcion = data.get("description", data.get("descripcion", ""))
        puntos = data.get("points", data.get("puntos", 10))
        asignado = data.get("assigned_to", data.get("asignado_a", ""))
        plantilla_id = data.get("template_id", data.get("plantilla_id", None))

        if not titulo:
            return {"exito": False, "mensaje": "El título de la misión es obligatorio", "resultado": None}

        if not asignado:
            return {"exito": False, "mensaje": "Debe asignar la misión a un miembro", "resultado": None}

        # Si se especifica plantilla, usar sus datos
        if plantilla_id:
            for plantilla in PLANTILLAS_MISIONES:
                if plantilla["id"] == plantilla_id:
                    if not descripcion:
                        descripcion = plantilla["descripcion"]
                    if puntos == 10 and plantilla.get("puntos"):
                        puntos = plantilla["puntos"]
                    break

        mision_id = str(uuid.uuid4())[:8]
        mision = {
            "id": mision_id,
            "titulo": titulo,
            "descripcion": descripcion,
            "puntos": puntos,
            "asignado_a": asignado,
            "estado": "pendiente",
            "fecha_creacion": datetime.now().isoformat(),
            "fecha_completado": None,
            "evidencia": None,
        }
        misiones_db[mision_id] = mision
        logger.info(f"Misión creada: '{titulo}' para {asignado} ({puntos} pts)")

        return {
            "exito": True,
            "mensaje": f"Misión '{titulo}' creada y asignada a {asignado}",
            "resultado": mision
        }
    except Exception as e:
        logger.error(f"Error en create_mission: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def complete_mission(data: dict) -> dict:
    """Marcar una misión como completada."""
    try:
        mision_id = data.get("mission_id", data.get("mision_id", ""))
        evidencia = data.get("evidence", data.get("evidencia", ""))

        if not mision_id or mision_id not in misiones_db:
            return {"exito": False, "mensaje": "Misión no encontrada", "resultado": None}

        mision = misiones_db[mision_id]

        if mision["estado"] == "completada":
            return {"exito": False, "mensaje": "Esta misión ya fue completada", "resultado": None}

        mision["estado"] = "completada"
        mision["fecha_completado"] = datetime.now().isoformat()
        mision["evidencia"] = evidencia

        # Otorgar puntos
        _sumar_puntos(mision["asignado_a"], mision["puntos"])
        miembro = miembros_db["familia"][mision["asignado_a"]]
        miembro["misiones_completadas"] += 1

        logger.info(f"Misión completada: '{mision['titulo']}' - {mision['puntos']} pts para {mision['asignado_a']}")

        return {
            "exito": True,
            "mensaje": f"¡Misión completada! {mision['asignado_a']} ganó {mision['puntos']} puntos",
            "resultado": {
                "mision": mision,
                "puntos_ganados": mision["puntos"],
                "total_puntos": miembro["puntos"],
                "misiones_completadas": miembro["misiones_completadas"],
            }
        }
    except Exception as e:
        logger.error(f"Error en complete_mission: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_missions(data: dict) -> dict:
    """Obtener lista de misiones."""
    try:
        estado = data.get("status", data.get("estado", None))
        asignado = data.get("assigned_to", data.get("asignado_a", None))

        lista_misiones = list(misiones_db.values())

        if estado:
            lista_misiones = [m for m in lista_misiones if m.get("estado") == estado]
        if asignado:
            lista_misiones = [m for m in lista_misiones if m.get("asignado_a") == asignado]

        lista_misiones = sorted(lista_misiones, key=lambda x: x.get("fecha_creacion", ""), reverse=True)

        return {
            "exito": True,
            "mensaje": f"{len(lista_misiones)} misión(es) encontrada(s)",
            "resultado": {
                "total": len(lista_misiones),
                "misiones": lista_misiones
            }
        }
    except Exception as e:
        logger.error(f"Error en get_missions: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def redeem_reward(data: dict) -> dict:
    """Canjear puntos por una recompensa."""
    try:
        global configuracion_pin
        usuario = data.get("user", data.get("usuario", ""))
        reward_id = data.get("reward", data.get("recompensa", ""))
        pin = data.get("pin", "")

        if not usuario:
            return {"exito": False, "mensaje": "Se requiere el nombre del usuario", "resultado": None}

        if not reward_id:
            return {"exito": False, "mensaje": "Se requiere el ID de la recompensa", "resultado": None}

        # Validar PIN parental
        if pin != configuracion_pin:
            return {"exito": False, "mensaje": "PIN parental incorrecto. Operación cancelada.", "resultado": None}

        # Buscar recompensa
        recompensa = None
        for r in CATALOGO_RECOMPENSAS:
            if r["id"] == reward_id:
                recompensa = r
                break

        if not recompensa:
            return {"exito": False, "mensaje": "Recompensa no encontrada", "resultado": None}

        # Verificar puntos suficientes
        miembro = _obtener_o_crear_miembro(usuario)
        if miembro["puntos"] < recompensa["costo_puntos"]:
            return {
                "exito": False,
                "mensaje": f"Puntos insuficientes. Tienes {miembro['puntos']} pero necesitas {recompensa['costo_puntos']}",
                "resultado": None
            }

        # Canjear
        if not _restar_puntos(usuario, recompensa["costo_puntos"]):
            return {"exito": False, "mensaje": "Error al descontar puntos", "resultado": None}

        canje_id = str(uuid.uuid4())[:8]
        logger.info(f"Recompensa canjeada: {recompensa['nombre']} por {usuario} ({recompensa['costo_puntos']} pts)")

        return {
            "exito": True,
            "mensaje": f"¡Felicidades {usuario}! Canjeaste: {recompensa['nombre']}",
            "resultado": {
                "canje_id": canje_id,
                "recompensa": recompensa["nombre"],
                "puntos gastados": recompensa["costo_puntos"],
                "puntos_restantes": miembro["puntos"],
                "usuario": usuario,
                "fecha": datetime.now().isoformat(),
            }
        }
    except Exception as e:
        logger.error(f"Error en redeem_reward: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_psychology_tip(data: dict) -> dict:
    """Obtener un consejo de psicología diario."""
    try:
        tipo = data.get("type", data.get("tipo", "emprendedor"))

        if tipo not in CONSEJOS_POR_TIPO:
            return {
                "exito": False,
                "mensaje": f"Tipo no válido. Tipos: {', '.join(CONSEJOS_POR_TIPO.keys())}",
                "resultado": None
            }

        # Usar el día del año para variar el consejo diariamente
        dia_actual = (date.today() - date(date.today().year, 1, 1)).days
        consejos = CONSEJOS_POR_TIPO[tipo]
        indice = dia_actual % len(consejos)
        consejo = consejos[indice]

        return {
            "exito": True,
            "mensaje": "Consejo del día",
            "resultado": {
                "consejo": consejo,
                "tipo": tipo,
                "dia_del_anio": dia_actual + 1,
                "total_consejos": len(consejos),
            }
        }
    except Exception as e:
        logger.error(f"Error en get_psychology_tip: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# Mapa de acciones
ACCIONES = {
    "coach_message": coach_message,
    "create_mission": create_mission,
    "complete_mission": complete_mission,
    "get_missions": get_missions,
    "redeem_reward": redeem_reward,
    "get_psychology_tip": get_psychology_tip,
}


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "ok",
            "motor": "coaching",
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
            "motor": "coaching",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "total_misiones": len(misiones_db),
            "miembros_familia": list(miembros_db["familia"].keys()),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.get("/mission_templates")
async def mission_templates():
    """Obtener plantillas de misiones disponibles."""
    try:
        return {
            "success": True,
            "result": {
                "total": len(PLANTILLAS_MISIONES),
                "plantillas": PLANTILLAS_MISIONES
            },
            "message": f"{len(PLANTILLAS_MISIONES)} plantillas de misiones disponibles"
        }
    except Exception as e:
        logger.error(f"Error en /mission_templates: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener plantillas")


@app.get("/reward_catalog")
async def reward_catalog():
    """Obtener catálogo de recompensas disponibles."""
    try:
        return {
            "success": True,
            "result": {
                "total": len(CATALOGO_RECOMPENSAS),
                "recompensas": CATALOGO_RECOMPENSAS
            },
            "message": f"{len(CATALOGO_RECOMPENSAS)} recompensas disponibles"
        }
    except Exception as e:
        logger.error(f"Error en /reward_catalog: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener recompensas")


@app.get("/leaderboard")
async def leaderboard():
    """Obtener tabla de puntos por miembro de la familia."""
    try:
        clasificacion = sorted(
            miembros_db["familia"].values(),
            key=lambda x: x.get("puntos", 0),
            reverse=True
        )
        return {
            "success": True,
            "result": {
                "total_miembros": len(clasificacion),
                "clasificacion": clasificacion
            },
            "message": "Tabla de clasificación actualizada"
        }
    except Exception as e:
        logger.error(f"Error en /leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener clasificación")


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
    logger.info("Iniciando Motor de Coaching - NEXUS v3 en puerto 8004...")
    uvicorn.run(app, host="127.0.0.1", port=8004)

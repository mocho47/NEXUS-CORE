"""
NEXUS v3 - Sistema de memoria cognitiva
Desarrollado por Simplex

Este modulo implementa un sistema de memoria que extrae y almacena informacion
clave de las conversaciones del usuario. Utiliza extraccion basada en palabras
clave y patrones linguisticos simples, sin necesidad de bibliotecas NLP externas.
"""

import logging
import re
from typing import Optional

from .database import get_user_memory, save_user_memory, search_user_memory

# Configuracion del logger
logger = logging.getLogger("nexus.memory")

# --- Patrones de extraccion de informacion ---

# Patrones para detectar nombres personales
PATRONES_NOMBRE = [
    re.compile(r"me llamo\s+(\w+(?:\s+\w+)?)", re.IGNORECASE),
    re.compile(r"mi nombre es\s+(\w+(?:\s+\w+)?)", re.IGNORECASE),
    re.compile(r"soy\s+(\w+(?:\s+\w+)?)", re.IGNORECASE),
    re.compile(r"mi nombre['']?\s+(?:es|sera|seria)\s+(\w+(?:\s+\w+)?)", re.IGNORECASE),
    re.compile(r"presentame,?\s*(?:soy|me llamo)?\s*(\w+(?:\s+\w+)?)", re.IGNORECASE),
]

# Patrones para detectar preferencias
PATRONES_PREFERENCIA = [
    re.compile(r"prefiero\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"me gusta\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"me encanta\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"amo\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"disfruto\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"quiero\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"me gustaria\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"odio\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"no me gusta\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"evita\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
]

# Patrones para detectar habitos y rutinas
PATRONES_HABITO = [
    re.compile(r"todos los dias\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"cada dia\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"cada semana\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"siempre\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"normalmente\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"generalmente\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"usualmente\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"rutinariamente\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"frecuentemente\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
    re.compile(r"a menudo\s+(.+?)(?:\.|,|$)", re.IGNORECASE),
]

# Palabras clave relacionadas con negocios
PALABRAS_NEGOCIO = {
    "cliente", "clientes", "pedido", "pedidos", "precio", "precios",
    "stock", "inventario", "venta", "ventas", "compra", "compras",
    "factura", "facturas", "facturacion", "cobro", "pago", "pagos",
    "proveedor", "proveedores", "negocio", "empresa", "producto",
    "productos", "servicio", "servicios", "cotizacion", "cotizaciones",
    "entrega", "envio", "descuento", "ganancia", "perdida",
    "canbusfix", "milens", "atf", "diagnostico", "reparacion",
}

# Palabras clave a ignorar (ruido comun)
PALABRAS_RUIDO = {
    "hola", "buenos", "dias", "tardes", "noches", "gracias", "por",
    "favor", "favor", "si", "no", "ok", "vale", "bien", "mal",
    "que", "como", "donde", "cuando", "quien", "cual", "cuanto",
    "este", "esta", "eso", "eso", "aqui", "alli", "ahora", "despues",
    "pero", "pero", "y", "o", "de", "del", "al", "a", "en", "con",
    "para", "por", "entre", "sobre", "sin", "hacia", "hasta",
    "un", "una", "unos", "unas", "el", "la", "los", "las",
}


class MemoryManager:
    """
    Gestor de memoria cognitiva para NEXUS v3.

    Extrae informacion clave de las conversaciones, la almacena en la base de datos
    y proporciona contexto relevante para las respuestas de IA.
    """

    def __init__(self, db):
        """
        Inicializa el gestor de memoria.

        Args:
            db: Instancia de la base de datos (referencia a conexion o modulo database).
        """
        self.db = db
        logger.info("MemoryManager inicializado.")

    async def learn_from_message(
        self,
        session_id: int,
        user_message: str,
        ai_response: str
    ) -> list[dict]:
        """
        Analiza un mensaje del usuario y la respuesta de IA para extraer
        informacion clave y almacenarla como memorias.

        Args:
            session_id: Identificador de la sesion de conversacion.
            user_message: Mensaje enviado por el usuario.
            ai_response: Respuesta generada por la IA.

        Returns:
            Lista de memorias extraidas y guardadas durante el analisis.
        """
        if not user_message or not user_message.strip():
            logger.debug("Mensaje vacio, no se extraen memorias.")
            return []

        mensaje_limpio = user_message.strip()
        memorias_guardadas = []

        logger.debug("Analizando mensaje para extraccion de memoria (longitud: %d)", len(mensaje_limpio))

        # --- Extraccion de nombre personal ---
        nombre = self._extraer_nombre(mensaje_limpio)
        if nombre:
            clave = "nombre_usuario"
            valor = nombre.strip()
            resultado = await save_user_memory(clave, valor, "personal")
            if resultado:
                memorias_guardadas.append({"key": clave, "value": valor, "category": "personal"})
                logger.info("Nombre extraido y guardado: %s", valor)

        # --- Extraccion de preferencias ---
        preferencias = self._extraer_preferencias(mensaje_limpio)
        for pref in preferencias:
            clave = f"preferencia_{self._normalizar_clave(pref)}"
            if len(pref) < 100:  # Evitar memorias excesivamente largas
                valor = pref.strip()
                resultado = await save_user_memory(clave, valor, "preference")
                if resultado:
                    memorias_guardadas.append({"key": clave, "value": valor, "category": "preference"})
                    logger.info("Preferencia extraida y guardada: %s", valor[:50])

        # --- Extraccion de habitos ---
        habitos = self._extraer_habitos(mensaje_limpio)
        for habito in habitos:
            clave = f"habito_{self._normalizar_clave(habito)}"
            if len(habito) < 150:
                valor = habito.strip()
                resultado = await save_user_memory(clave, valor, "habit")
                if resultado:
                    memorias_guardadas.append({"key": clave, "value": valor, "category": "habit"})
                    logger.info("Habito extraido y guardado: %s", valor[:50])

        # --- Deteccion de contenido de negocios ---
        if self._contiene_negocio(mensaje_limpio):
            clave = "ultimo_contexto_negocio"
            valor = mensaje_limpio[:500]  # Limitar longitud
            resultado = await save_user_memory(clave, valor, "business")
            if resultado:
                memorias_guardadas.append({"key": clave, "value": valor, "category": "business"})
                logger.info("Contexto de negocio detectado y guardado (longitud: %d)", len(valor))

        # --- Extraccion de datos numericos relevantes ---
        datos_numericos = self._extraer_datos_numericos(mensaje_limpio)
        for dato in datos_numericos:
            clave = f"dato_{self._normalizar_clave(dato['concepto'])}"
            valor = f"{dato['concepto']}: {dato['valor']}"
            resultado = await save_user_memory(clave, valor, "business")
            if resultado:
                memorias_guardadas.append({"key": clave, "value": valor, "category": "business"})
                logger.info("Dato numerico extraido: %s", valor)

        if memorias_guardadas:
            logger.info("Se extrajeron %d memorias del mensaje.", len(memorias_guardadas))
        else:
            logger.debug("No se extrajeron memorias del mensaje.")

        return memorias_guardadas

    def _extraer_nombre(self, texto: str) -> Optional[str]:
        """
        Extrae un nombre personal del texto usando patrones predefinidos.

        Args:
            texto: Texto del cual extraer el nombre.

        Returns:
            Nombre extraido, o None si no se encuentra ninguno.
        """
        for patron in PATRONES_NOMBRE:
            coincidencia = patron.search(texto)
            if coincidencia:
                nombre = coincidencia.group(1).strip()
                # Filtrar nombres que sean demasiado cortos o palabras comunes
                if len(nombre) >= 2 and nombre.lower() not in PALABRAS_RUIDO:
                    return nombre.capitalize()
        return None

    def _extraer_preferencias(self, texto: str) -> list[str]:
        """
        Extrae preferencias del texto usando patrones predefinidos.

        Args:
            texto: Texto del cual extraer preferencias.

        Returns:
            Lista de preferencias encontradas.
        """
        preferencias = []
        for patron in PATRONES_PREFERENCIA:
            coincidencias = patron.findall(texto)
            for pref in coincidencias:
                pref_limpio = pref.strip()
                if pref_limpio and len(pref_limpio) >= 3:
                    preferencias.append(pref_limpio)
        return preferencias

    def _extraer_habitos(self, texto: str) -> list[str]:
        """
        Extrae habitos y rutinas del texto usando patrones predefinidos.

        Args:
            texto: Texto del cual extraer habitos.

        Returns:
            Lista de habitos encontrados.
        """
        habitos = []
        for patron in PATRONES_HABITO:
            coincidencias = patron.findall(texto)
            for habito in coincidencias:
                habito_limpio = habito.strip()
                if habito_limpio and len(habito_limpio) >= 3:
                    habitos.append(habito_limpio)
        return habitos

    def _contiene_negocio(self, texto: str) -> bool:
        """
        Verifica si el texto contiene palabras clave relacionadas con negocios.

        Args:
            texto: Texto a analizar.

        Returns:
            True si se detectan palabras de negocio, False en caso contrario.
        """
        texto_lower = texto.lower()
        palabras = set(re.findall(r"\b\w+\b", texto_lower))
        # Verificar si hay al menos 2 palabras de negocio para mayor precision
        coincidencias = palabras & PALABRAS_NEGOCIO
        return len(coincidencias) >= 2

    def _extraer_datos_numericos(self, texto: str) -> list[dict]:
        """
        Extrae datos numericos relevantes del texto junto con su contexto.

        Args:
            texto: Texto del cual extraer datos numericos.

        Returns:
            Lista de diccionarios con {'concepto': str, 'valor': str}.
        """
        datos = []
        texto_lower = texto.lower()

        # Patrones para extraer datos con contexto
        patrones_datos = [
            (re.compile(r"precio\s+(?:de|es|:\s*)?\$?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE), "precio"),
            (re.compile(r"cuesta\s+\$?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE), "precio"),
            (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:unidades?|piezas?|uds?)", re.IGNORECASE), "cantidad"),
            (re.compile(r"stock\s+(?:de|:\s*)?(\d+)", re.IGNORECASE), "stock"),
            (re.compile(r"(\d+)\s*(?:dias?|semanas?|meses?)", re.IGNORECASE), "plazo"),
            (re.compile(r"telefono\s+(?:es|:\s*)?(\d[\d\s\-]{6,})", re.IGNORECASE), "telefono"),
            (re.compile(r"(?:tel|cel)\s*(?:\s*)?(\d[\d\s\-]{6,})", re.IGNORECASE), "telefono"),
        ]

        for patron, concepto in patrones_datos:
            coincidencia = patron.search(texto)
            if coincidencia:
                valor = coincidencia.group(1).strip()
                datos.append({"concepto": concepto, "valor": valor})

        return datos

    def _normalizar_clave(self, texto: str) -> str:
        """
        Normaliza un texto para usarlo como clave de memoria.
        Elimina caracteres especiales, reduce espacios y convierte a minusculas.

        Args:
            texto: Texto a normalizar.

        Returns:
            Cadena normalizada para usar como clave.
        """
        # Reemplazar caracteres no alfanumericos con guion bajo
        texto = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s]", "_", texto)
        # Reducir espacios multiples
        texto = re.sub(r"\s+", "_", texto)
        # Convertir a minusculas
        texto = texto.lower()
        # Limitar longitud
        texto = texto[:60]
        # Eliminar guiones bajos al inicio y final
        texto = texto.strip("_")
        return texto

    async def get_relevant_context(self, query: str, limit: int = 5) -> str:
        """
        Busca memorias relevantes para una consulta dada y las formatea
        como contexto para inyeccion en la conversacion de IA.

        Args:
            query: Consulta o mensaje del usuario para buscar memorias relevantes.
            limit: Numero maximo de memorias a incluir (por defecto 5).

        Returns:
            Cadena de texto formateada con el contexto de memorias relevantes,
            o cadena vacia si no hay memorias relevantes.
        """
        if not query or not query.strip():
            logger.debug("Consulta vacia, no se busca contexto.")
            return ""

        logger.debug("Buscando contexto relevante para: '%s' (limite: %d)", query[:50], limit)

        try:
            # Extraer palabras clave de la consulta
            palabras_clave = self._extraer_palabras_clave(query)

            if not palabras_clave:
                logger.debug("No se encontraron palabras clave en la consulta.")
                return ""

            # Buscar memorias relevantes usando las palabras clave
            todas_las_memorias = []
            for palabra in palabras_clave:
                resultados = await search_user_memory(palabra)
                for mem in resultados:
                    # Evitar duplicados
                    if not any(m["key"] == mem["key"] for m in todas_las_memorias):
                        todas_las_memorias.append(mem)

            # Limitar resultados
            memorias_relevantes = todas_las_memorias[:limit]

            if not memorias_relevantes:
                logger.debug("No se encontraron memorias relevantes.")
                return ""

            # Formatear contexto
            lineas_contexto = ["--- Memoria contextual del usuario ---"]
            for mem in memorias_relevantes:
                categoria = mem.get("category", "preference")
                clave = mem.get("key", "")
                valor = mem.get("value", "")
                linea = f"[{categoria.upper()}] {clave}: {valor}"
                lineas_contexto.append(linea)
            lineas_contexto.append("--- Fin de memoria contextual ---")

            contexto = "\n".join(lineas_contexto)
            logger.debug("Contexto relevante generado (%d memorias).", len(memorias_relevantes))
            return contexto

        except Exception as e:
            logger.error("Error al generar contexto relevante: %s", e)
            return ""

    def _extraer_palabras_clave(self, texto: str) -> list[str]:
        """
        Extrae palabras clave relevantes de un texto, excluyendo palabras de ruido.

        Args:
            texto: Texto del cual extraer palabras clave.

        Returns:
            Lista de palabras clave relevantes.
        """
        # Extraer todas las palabras
        palabras = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]{3,}\b", texto.lower())
        # Filtrar palabras de ruido
        palabras_filtradas = [p for p in palabras if p not in PALABRAS_RUIDO]
        # Eliminar duplicados manteniendo orden
        vistas = set()
        resultado = []
        for palabra in palabras_filtradas:
            if palabra not in vistas:
                vistas.add(palabra)
                resultado.append(palabra)
        return resultado[:10]  # Limitar a 10 palabras clave

    async def get_user_summary(self) -> str:
        """
        Compila todas las memorias del usuario en un resumen narrativo.

        Returns:
            Cadena de texto con un resumen de todo lo que se sabe del usuario.
        """
        logger.info("Generando resumen del usuario...")

        try:
            # Obtener todas las memorias agrupadas por categoria
            memorias = await get_user_memory()

            if not memorias:
                logger.info("No hay memorias almacenadas para generar resumen.")
                return "No tengo informacion almacenada sobre el usuario todavia."

            # Agrupar por categoria
            categorias = {
                "personal": [],
                "business": [],
                "preference": [],
                "habit": [],
            }

            for mem in memorias:
                cat = mem.get("category", "preference")
                if cat in categorias:
                    categorias[cat].append(mem)

            # Construir resumen narrativo
            secciones = []

            # Seccion personal
            if categorias["personal"]:
                secciones.append("Datos personales del usuario:")
                for mem in categorias["personal"]:
                    secciones.append(f"  - {mem['key'].replace('_', ' ')}: {mem['value']}")

            # Seccion de preferencias
            if categorias["preference"]:
                secciones.append("\nPreferencias del usuario:")
                for mem in categorias["preference"]:
                    secciones.append(f"  - {mem['value']}")

            # Seccion de habitos
            if categorias["habit"]:
                secciones.append("\nHabitos y rutinas del usuario:")
                for mem in categorias["habit"]:
                    secciones.append(f"  - {mem['value']}")

            # Seccion de negocios
            if categorias["business"]:
                secciones.append("\nInformacion de negocios:")
                for mem in categorias["business"]:
                    if mem["key"] != "ultimo_contexto_negocio":
                        secciones.append(f"  - {mem['value']}")
                    else:
                        # Resumir el ultimo contexto de negocio
                        contexto = mem["value"][:200]
                        secciones.append(f"  - Ultimo tema de negocio: {contexto}...")

            resumen = "\n".join(secciones)
            total = len(memorias)
            logger.info("Resumen generado con %d memorias totales.", total)
            return resumen

        except Exception as e:
            logger.error("Error al generar resumen del usuario: %s", e)
            return "Error al generar el resumen del usuario."

    async def forget(self, key: str) -> bool:
        """
        Elimina una memoria especifica del usuario.

        Args:
            key: Clave de la memoria a eliminar.

        Returns:
            True si la memoria fue eliminada correctamente, False en caso contrario.
        """
        logger.info("Solicitando eliminar memoria con clave: %s", key)
        try:
            from .database import save_user_memory
            # Para "olvidar", guardamos un valor vacio que se interpreta como eliminada
            # Nota: La base de datos usa INSERT OR REPLACE, por lo que sobreescribimos
            # En una implementacion futura se podria agregar DELETE
            async with aiosqlite.connect("nexus.db") as db:
                cursor = await db.execute(
                    "DELETE FROM user_memory WHERE key = ?",
                    (key,)
                )
                await db.commit()
                if cursor.rowcount > 0:
                    logger.info("Memoria '%s' eliminada correctamente.", key)
                    return True
                else:
                    logger.warning("No se encontro memoria con clave: %s", key)
                    return False
        except Exception as e:
            logger.error("Error al eliminar memoria '%s': %s", key, e)
            return False

    async def get_stats(self) -> dict:
        """
        Obtiene estadisticas de las memorias almacenadas.

        Returns:
            Diccionario con conteos por categoria y total:
            {
                'total': int,
                'personal': int,
                'business': int,
                'preference': int,
                'habit': int,
                'ultima_actualizacion': str
            }
        """
        logger.debug("Obteniendo estadisticas de memoria...")
        try:
            memorias = await get_user_memory()
            total = len(memorias)

            estadisticas = {
                "total": total,
                "personal": 0,
                "business": 0,
                "preference": 0,
                "habit": 0,
                "ultima_actualizacion": "nunca",
            }

            timestamp_mas_reciente = None

            for mem in memorias:
                categoria = mem.get("category", "preference")
                if categoria in estadisticas:
                    estadisticas[categoria] += 1

                # Rastrear la actualizacion mas reciente
                actualizacion = mem.get("updated_at", "")
                if actualizacion and actualizacion != "nunca":
                    if timestamp_mas_reciente is None or actualizacion > timestamp_mas_reciente:
                        timestamp_mas_reciente = actualizacion

            if timestamp_mas_reciente:
                estadisticas["ultima_actualizacion"] = timestamp_mas_reciente

            logger.info("Estadisticas de memoria: %s", estadisticas)
            return estadisticas

        except Exception as e:
            logger.error("Error al obtener estadisticas de memoria: %s", e)
            return {
                "total": 0,
                "personal": 0,
                "business": 0,
                "preference": 0,
                "habit": 0,
                "ultima_actualizacion": "error",
            }


# Necesario para el metodo forget
import aiosqlite

"""
NEXUS v3 - Cliente multi-IA con enrutamiento inteligente
Desarrollado por Simplex

Este modulo proporciona un cliente de IA que enruta automaticamente las solicitudes
al mejor proveedor disponible. Soporta Groq, Z.ai (GLM) y Ollama (local) con
logica de fallback inteligente.
"""

import json
import logging
from typing import Optional

import aiohttp

# Configuracion del logger
logger = logging.getLogger("nexus.ai_client")


# --- Definiciones de personalidades del sistema ---

PERSONALIDADES = {
    "nexus": (
        "Eres NEXUS v3, un asistente de IA avanzado desarrollado por Simplex. "
        "Eres profesional, eficiente y amigable. Ayudas con gestion de negocios, "
        "analisis de datos, tareas operativas y soporte tecnico. Respondes en "
        "espanol de forma clara y concisa. Siempre mantienes un tono colaborativo "
        "y proactivo."
    ),
    "tecnico": (
        "Eres un asistente tecnico especializado de NEXUS v3. Te enfocas en resolver "
        "problemas de software, hardware y redes. Proporcionas soluciones detalladas "
        "y paso a paso. Usas terminologia tecnica cuando es apropiado pero explicas "
        "conceptos complejos de forma accesible."
    ),
    "ventas": (
        "Eres un asistente de ventas de NEXUS v3. Ayudas con gestion de clientes, "
        "seguimiento de pedidos, cotizaciones y estrategias de ventas. Siempre "
        "buscas maximizar el valor para el negocio mientras mantienes excelentes "
        "relaciones con los clientes."
    ),
    "creativo": (
        "Eres un asistente creativo de NEXUS v3. Ayudas con redaccion de contenido, "
        "ideas de marketing, diseno de campañas y estrategias creativas. Eres "
        "innovador, inspirador y piensas fuera de la caja."
    ),
}

# Modelos disponibles por proveedor
MODELOS_GROQ = {
    "fast": "llama-3.1-8b-instant",
    "complex": "llama-3.3-70b-versatile",
    "analysis": "llama-3.3-70b-versatile",
    "creative": "llama-3.3-70b-versatile",
    "default": "llama-3.3-70b-versatile",
}

MODELO_OLLAMA_DEFAULT = "phi3:mini"
TIMEOUT_SOLICITUD = 60  # segundos


class AIClient:
    """
    Cliente de IA multi-proveedor con enrutamiento inteligente.

    Enruta las solicitudes al mejor proveedor disponible segun el tipo de tarea
    y la disponibilidad del servicio. Soporta fallback automatico entre proveedores.
    """

    def __init__(self, config: dict):
        """
        Inicializa el cliente de IA con la configuracion proporcionada.

        Args:
            config: Diccionario con las claves de API y configuracion.
                    Claves esperadas:
                    - GROQ_API_KEY: Clave de API para Groq
                    - ZAI_API_KEY: Clave de API para Z.ai (GLM)
                    - OLLAMA_URL: URL del servidor Ollama (por defecto localhost:11434)
                    - default_personality: Personalidad por defecto (por defecto 'nexus')
        """
        self.groq_api_key = config.get("GROQ_API_KEY", "")
        self.zai_api_key = config.get("ZAI_API_KEY", "")
        self.ollama_url = config.get("OLLAMA_URL", "http://localhost:11434")
        self.default_personality = config.get("default_personality", "nexus")

        # URL de endpoints
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.zai_endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.ollama_chat_endpoint = f"{self.ollama_url}/api/chat"
        self.ollama_tags_endpoint = f"{self.ollama_url}/api/tags"

        # Cache de ultima respuesta (para fallback sin conexion)
        self._ultima_respuesta = ""
        self._ultima_pregunta = ""

        logger.info("AIClient inicializado. Groq: %s, Z.ai: %s, Ollama: %s",
                     "SI" if self.groq_api_key else "NO",
                     "SI" if self.zai_api_key else "NO",
                     self.ollama_url)

    def _obtener_prompt_sistema(self, personality: str) -> str:
        """
        Obtiene el prompt de sistema para una personalidad dada.

        Args:
            personality: Nombre de la personalidad.

        Returns:
            Cadena de texto con el prompt de sistema.
        """
        if personality in PERSONALIDADES:
            return PERSONALIDADES[personality]
        logger.warning("Personalidad '%s' no reconocida, usando 'nexus' por defecto.", personality)
        return PERSONALIDADES["nexus"]

    def _preparar_mensajes(self, messages: list[dict], personality: str) -> list[dict]:
        """
        Prepara los mensajes agregando el prompt de sistema de la personalidad.

        Args:
            messages: Lista de mensajes de la conversacion.
            personality: Personalidad a usar.

        Returns:
            Lista de mensajes con el prompt de sistema al inicio.
        """
        prompt_sistema = self._obtener_prompt_sistema(personality)

        # Si ya viene un system prompt desde nexus_core, respetarlo
        if messages and messages[0].get("role") == "system":
            mensajes_preparados = list(messages)
        else:
            mensajes_preparados = [{"role": "system", "content": prompt_sistema}]
            mensajes_preparados.extend(messages)

        return mensajes_preparados

    async def chat(
        self,
        messages: list[dict],
        personality: str = "nexus",
        task_type: str = "general"
    ) -> str:
        """
        Envia un mensaje al mejor proveedor de IA disponible segun el tipo de tarea.

        Logica de enrutamiento:
        1. Si task_type == "fast" y GROQ_API_KEY: usa Groq llama-3.1-8b-instant (rapido, economico)
        2. Si task_type == "complex" o "analysis" y GROQ_API_KEY: usa Groq llama-3.3-70b
        3. Si GROQ_API_KEY: usa Groq llama-3.3-70b (nube por defecto)
        4. Si ZAI_API_KEY: usa Z.ai GLM-5 (nube alternativa)
        5. Intenta Ollama local (phi3:mini) para modo sin conexion
        6. Devuelve respuesta cacheada si esta disponible
        7. Mensaje de error si ningun proveedor esta disponible

        Args:
            messages: Lista de mensajes de la conversacion.
            personality: Personalidad del asistente (por defecto 'nexus').
            task_type: Tipo de tarea: 'general', 'complex', 'creative', 'fast', 'analysis'.

        Returns:
            Respuesta del modelo de IA como cadena de texto.
        """
        # Preparar mensajes con personalidad
        mensajes_preparados = self._preparar_mensajes(messages, personality)

        # Guardar la pregunta para cache de fallback
        pregunta_actual = ""
        if messages and messages[-1].get("role") == "user":
            pregunta_actual = messages[-1]["content"]

        # --- Estrategia 1: Tareas rapidas con Groq ---
        if task_type == "fast" and self.groq_api_key:
            logger.info("Enrutando a Groq (modelo rapido) para tarea tipo: %s", task_type)
            modelo = MODELOS_GROQ["fast"]
            respuesta = await self._call_groq(mensajes_preparados, modelo)
            if respuesta:
                self._guardar_cache(pregunta_actual, respuesta)
                return respuesta
            logger.warning("Groq rapido fallo, intentando proveedor alternativo...")

        # --- Estrategia 2: Tareas complejas o de analisis con Groq ---
        if task_type in ("complex", "analysis") and self.groq_api_key:
            logger.info("Enrutando a Groq (modelo grande) para tarea tipo: %s", task_type)
            modelo = MODELOS_GROQ[task_type]
            respuesta = await self._call_groq(mensajes_preparados, modelo)
            if respuesta:
                self._guardar_cache(pregunta_actual, respuesta)
                return respuesta
            logger.warning("Groq complejo fallo, intentando proveedor alternativo...")

        # --- Estrategia 3: Groq como nube por defecto ---
        if self.groq_api_key:
            logger.info("Enrutando a Groq (modelo por defecto) para tarea tipo: %s", task_type)
            modelo = MODELOS_GROQ.get(task_type, MODELOS_GROQ["default"])
            respuesta = await self._call_groq(mensajes_preparados, modelo)
            if respuesta:
                self._guardar_cache(pregunta_actual, respuesta)
                return respuesta
            logger.warning("Groq por defecto fallo, intentando Z.ai...")

        # --- Estrategia 4: Z.ai (GLM-5) como nube alternativa ---
        if self.zai_api_key:
            logger.info("Enrutando a Z.ai (GLM-5) como alternativa.")
            respuesta = await self._call_zai(mensajes_preparados)
            if respuesta:
                self._guardar_cache(pregunta_actual, respuesta)
                return respuesta
            logger.warning("Z.ai fallo, intentando Ollama local...")

        # --- Estrategia 5: Ollama local para modo sin conexion ---
        logger.info("Intentando Ollama local para modo sin conexion...")
        respuesta = await self._call_ollama(mensajes_preparados, MODELO_OLLAMA_DEFAULT)
        if respuesta:
            self._guardar_cache(pregunta_actual, respuesta)
            return respuesta

        # --- Estrategia 6: Devolver respuesta cacheada ---
        if self._ultima_respuesta and self._ultima_pregunta != pregunta_actual:
            logger.warning("Todos los proveedores fallaron. Devolviendo ultima respuesta cacheada.")
            return (
                f"[AVISO: Sin conexion a IA. Esta es una respuesta en cache de una pregunta anterior]\n\n"
                f"{self._ultima_respuesta}"
            )

        # --- Estrategia 7: Ningun proveedor disponible ---
        logger.error("Todos los proveedores de IA no disponibles.")
        return (
            "Lo siento, no tengo acceso a un modelo de IA en este momento. "
            "Verifica tu conexion a internet o que Ollama este ejecutandose."
        )

    def _guardar_cache(self, pregunta: str, respuesta: str):
        """Guarda la ultima pregunta y respuesta para fallback sin conexion."""
        if pregunta and respuesta:
            self._ultima_pregunta = pregunta
            self._ultima_respuesta = respuesta

    async def _call_groq(self, messages: list[dict], model: str) -> Optional[str]:
        """
        Realiza una llamada a la API de Groq.

        Args:
            messages: Lista de mensajes para enviar.
            model: Nombre del modelo a utilizar.

        Returns:
            Respuesta del modelo como cadena de texto, o None si hay error.
        """
        logger.debug("Llamando a Groq con modelo: %s", model)
        try:
            cabeceras = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            }
            cuerpo = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_SOLICITUD)) as session:
                async with session.post(self.groq_endpoint, headers=cabeceras, json=cuerpo) as respuesta_http:
                    if respuesta_http.status == 200:
                        datos = await respuesta_http.json()
                        contenido = datos["choices"][0]["message"]["content"]
                        logger.debug("Respuesta de Groq recibida (longitud: %d)", len(contenido))
                        return contenido
                    else:
                        texto_error = await respuesta_http.text()
                        logger.error(
                            "Error de Groq (HTTP %d): %s",
                            respuesta_http.status, texto_error[:500]
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error("Error de conexion con Groq: %s", e)
            return None
        except KeyError as e:
            logger.error("Error al parsear respuesta de Groq, clave faltante: %s", e)
            return None
        except Exception as e:
            logger.error("Error inesperado al llamar a Groq: %s", e)
            return None

    async def _call_zai(self, messages: list[dict]) -> Optional[str]:
        """
        Realiza una llamada a la API de Z.ai (GLM-5).

        Args:
            messages: Lista de mensajes para enviar.

        Returns:
            Respuesta del modelo como cadena de texto, o None si hay error.
        """
        logger.debug("Llamando a Z.ai (GLM-5)")
        try:
            cabeceras = {
                "Authorization": f"Bearer {self.zai_api_key}",
                "Content-Type": "application/json",
            }
            cuerpo = {
                "model": "glm-5",
                "messages": messages,
                "temperature": 0.7,
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_SOLICITUD)) as session:
                async with session.post(self.zai_endpoint, headers=cabeceras, json=cuerpo) as respuesta_http:
                    if respuesta_http.status == 200:
                        datos = await respuesta_http.json()
                        contenido = datos["choices"][0]["message"]["content"]
                        logger.debug("Respuesta de Z.ai recibida (longitud: %d)", len(contenido))
                        return contenido
                    else:
                        texto_error = await respuesta_http.text()
                        logger.error(
                            "Error de Z.ai (HTTP %d): %s",
                            respuesta_http.status, texto_error[:500]
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error("Error de conexion con Z.ai: %s", e)
            return None
        except KeyError as e:
            logger.error("Error al parsear respuesta de Z.ai, clave faltante: %s", e)
            return None
        except Exception as e:
            logger.error("Error inesperado al llamar a Z.ai: %s", e)
            return None

    async def _call_ollama(self, messages: list[dict], model: str) -> Optional[str]:
        """
        Realiza una llamada al servidor Ollama local.

        Args:
            messages: Lista de mensajes para enviar.
            model: Nombre del modelo Ollama a utilizar.

        Returns:
            Respuesta del modelo como cadena de texto, o None si hay error.
        """
        logger.debug("Llamando a Ollama local con modelo: %s", model)
        try:
            cuerpo = {
                "model": model,
                "messages": messages,
                "stream": False,
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT_SOLICITUD * 2)) as session:
                async with session.post(self.ollama_chat_endpoint, json=cuerpo) as respuesta_http:
                    if respuesta_http.status == 200:
                        datos = await respuesta_http.json()
                        contenido = datos.get("message", {}).get("content", "")
                        if contenido:
                            logger.debug("Respuesta de Ollama recibida (longitud: %d)", len(contenido))
                            return contenido
                        else:
                            logger.error("Ollama respondio sin contenido.")
                            return None
                    else:
                        texto_error = await respuesta_http.text()
                        logger.error(
                            "Error de Ollama (HTTP %d): %s",
                            respuesta_http.status, texto_error[:500]
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error("Error de conexion con Ollama: %s. ¿Esta ejecutandose Ollama?", e)
            return None
        except KeyError as e:
            logger.error("Error al parsear respuesta de Ollama, clave faltante: %s", e)
            return None
        except Exception as e:
            logger.error("Error inesperado al llamar a Ollama: %s", e)
            return None

    async def _check_ollama(self) -> bool:
        """
        Verifica si el servidor Ollama esta disponible y ejecutandose.

        Returns:
            True si Ollama responde correctamente, False en caso contrario.
        """
        logger.debug("Verificando disponibilidad de Ollama en: %s", self.ollama_url)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(self.ollama_tags_endpoint) as respuesta_http:
                    if respuesta_http.status == 200:
                        datos = await respuesta_http.json()
                        modelos = datos.get("models", [])
                        logger.info("Ollama disponible con %d modelos instalados.", len(modelos))
                        return True
                    else:
                        logger.debug("Ollama respondio con HTTP %d.", respuesta_http.status)
                        return False

        except aiohttp.ClientError as e:
            logger.debug("Ollama no disponible: %s", e)
            return False
        except Exception as e:
            logger.debug("Error al verificar Ollama: %s", e)
            return False

    async def get_available_providers(self) -> list[dict]:
        """
        Obtiene la lista de proveedores disponibles con su estado actual.

        Returns:
            Lista de diccionarios con informacion de cada proveedor:
            [{'name': str, 'model': str, 'status': 'available'|'unavailable'}]
        """
        proveedores = []

        # Verificar Groq
        if self.groq_api_key:
            # Probar con un request simple para verificar conectividad
            try:
                cabeceras = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                }
                cuerpo_prueba = {
                    "model": MODELOS_GROQ["fast"],
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                }
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.post(
                        self.groq_endpoint,
                        headers=cabeceras,
                        json=cuerpo_prueba
                    ) as resp:
                        if resp.status == 200:
                            proveedores.append({
                                "name": "Groq",
                                "model": "llama-3.3-70b-versatile / llama-3.1-8b-instant",
                                "status": "available",
                            })
                        else:
                            proveedores.append({
                                "name": "Groq",
                                "model": "llama-3.3-70b-versatile / llama-3.1-8b-instant",
                                "status": "unavailable",
                            })
            except Exception:
                proveedores.append({
                    "name": "Groq",
                    "model": "llama-3.3-70b-versatile / llama-3.1-8b-instant",
                    "status": "unavailable",
                })
        else:
            proveedores.append({
                "name": "Groq",
                "model": "llama-3.3-70b-versatile / llama-3.1-8b-instant",
                "status": "unavailable (sin clave API)",
            })

        # Verificar Z.ai
        if self.zai_api_key:
            try:
                cabeceras = {
                    "Authorization": f"Bearer {self.zai_api_key}",
                    "Content-Type": "application/json",
                }
                cuerpo_prueba = {
                    "model": "glm-5",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                }
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.post(
                        self.zai_endpoint,
                        headers=cabeceras,
                        json=cuerpo_prueba
                    ) as resp:
                        if resp.status == 200:
                            proveedores.append({
                                "name": "Z.ai (GLM)",
                                "model": "glm-5",
                                "status": "available",
                            })
                        else:
                            proveedores.append({
                                "name": "Z.ai (GLM)",
                                "model": "glm-5",
                                "status": "unavailable",
                            })
            except Exception:
                proveedores.append({
                    "name": "Z.ai (GLM)",
                    "model": "glm-5",
                    "status": "unavailable",
                })
        else:
            proveedores.append({
                "name": "Z.ai (GLM)",
                "model": "glm-5",
                "status": "unavailable (sin clave API)",
            })

        # Verificar Ollama
        ollama_disponible = await self._check_ollama()
        proveedores.append({
            "name": "Ollama (Local)",
            "model": MODELO_OLLAMA_DEFAULT,
            "status": "available" if ollama_disponible else "unavailable",
        })

        logger.info("Estado de proveedores: %s",
                     ", ".join(f"{p['name']}={p['status']}" for p in proveedores))
        return proveedores

    async def health_check(self) -> dict:
        """
        Realiza una verificacion completa de salud de todos los proveedores de IA.

        Returns:
            Diccionario con el estado detallado de cada proveedor:
            {
                'estado_general': 'ok'|'degradado'|'sin_servicio',
                'proveedores': {nombre: {estado, latencia_ms, error}},
                'total_disponibles': int,
                'total_proveedores': int
            }
        """
        import time

        logger.info("Ejecutando verificacion de salud de proveedores de IA...")
        resultados = {}
        disponibles = 0
        total = 3

        # --- Verificar Groq ---
        inicio = time.monotonic()
        if self.groq_api_key:
            try:
                cabeceras = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                }
                cuerpo_prueba = {
                    "model": MODELOS_GROQ["fast"],
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                }
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.post(
                        self.groq_endpoint,
                        headers=cabeceras,
                        json=cuerpo_prueba
                    ) as resp:
                        latencia = int((time.monotonic() - inicio) * 1000)
                        if resp.status == 200:
                            resultados["Groq"] = {
                                "estado": "ok",
                                "latencia_ms": latencia,
                                "error": None,
                            }
                            disponibles += 1
                        else:
                            texto_error = await resp.text()
                            resultados["Groq"] = {
                                "estado": "error",
                                "latencia_ms": latencia,
                                "error": f"HTTP {resp.status}: {texto_error[:200]}",
                            }
            except Exception as e:
                latencia = int((time.monotonic() - inicio) * 1000)
                resultados["Groq"] = {
                    "estado": "error",
                    "latencia_ms": latencia,
                    "error": str(e),
                }
        else:
            resultados["Groq"] = {
                "estado": "sin_configurar",
                "latencia_ms": 0,
                "error": "No se proporciono GROQ_API_KEY",
            }

        # --- Verificar Z.ai ---
        inicio = time.monotonic()
        if self.zai_api_key:
            try:
                cabeceras = {
                    "Authorization": f"Bearer {self.zai_api_key}",
                    "Content-Type": "application/json",
                }
                cuerpo_prueba = {
                    "model": "glm-5",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                }
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.post(
                        self.zai_endpoint,
                        headers=cabeceras,
                        json=cuerpo_prueba
                    ) as resp:
                        latencia = int((time.monotonic() - inicio) * 1000)
                        if resp.status == 200:
                            resultados["Z.ai"] = {
                                "estado": "ok",
                                "latencia_ms": latencia,
                                "error": None,
                            }
                            disponibles += 1
                        else:
                            texto_error = await resp.text()
                            resultados["Z.ai"] = {
                                "estado": "error",
                                "latencia_ms": latencia,
                                "error": f"HTTP {resp.status}: {texto_error[:200]}",
                            }
            except Exception as e:
                latencia = int((time.monotonic() - inicio) * 1000)
                resultados["Z.ai"] = {
                    "estado": "error",
                    "latencia_ms": latencia,
                    "error": str(e),
                }
        else:
            resultados["Z.ai"] = {
                "estado": "sin_configurar",
                "latencia_ms": 0,
                "error": "No se proporciono ZAI_API_KEY",
            }

        # --- Verificar Ollama ---
        inicio = time.monotonic()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(self.ollama_tags_endpoint) as resp:
                    latencia = int((time.monotonic() - inicio) * 1000)
                    if resp.status == 200:
                        resultados["Ollama"] = {
                            "estado": "ok",
                            "latencia_ms": latencia,
                            "error": None,
                        }
                        disponibles += 1
                    else:
                        resultados["Ollama"] = {
                            "estado": "error",
                            "latencia_ms": latencia,
                            "error": f"HTTP {resp.status}",
                        }
        except Exception as e:
            latencia = int((time.monotonic() - inicio) * 1000)
            resultados["Ollama"] = {
                "estado": "error",
                "latencia_ms": latencia,
                "error": str(e),
            }

        # Determinar estado general
        if disponibles == 0:
            estado_general = "sin_servicio"
        elif disponibles < total:
            estado_general = "degradado"
        else:
            estado_general = "ok"

        informe = {
            "estado_general": estado_general,
            "proveedores": resultados,
            "total_disponibles": disponibles,
            "total_proveedores": total,
        }

        logger.info(
            "Verificacion de salud completada: %s (%d/%d proveedores disponibles)",
            estado_general, disponibles, total
        )

        return informe

    # ─── Métodos de compatibilidad con nexus_core.py ──────────────────────────

    async def generar_respuesta(self, messages: list[dict], task_type: str = "general") -> str:
        """Alias de chat() para compatibilidad con nexus_core."""
        return await self.chat(messages, task_type=task_type)

    def proveedor_actual(self) -> str:
        """Retorna el proveedor primario configurado."""
        if self.groq_api_key:
            return "Groq"
        if self.zai_api_key:
            return "Z.ai"
        return "Ollama"

    def listar_proveedores(self) -> list[str]:
        """Lista los proveedores configurados."""
        provs = []
        if self.groq_api_key:
            provs.append("Groq")
        if self.zai_api_key:
            provs.append("Z.ai")
        provs.append("Ollama")
        return provs

    def obtener_estado_proveedor(self, nombre: str) -> dict:
        """Retorna estado básico de un proveedor (sync, sin ping real)."""
        if nombre == "Groq":
            return {"nombre": "Groq", "disponible": bool(self.groq_api_key),
                    "modelo": MODELOS_GROQ["default"]}
        if nombre == "Z.ai":
            return {"nombre": "Z.ai", "disponible": bool(self.zai_api_key),
                    "modelo": "glm-5"}
        return {"nombre": "Ollama", "disponible": True, "modelo": MODELO_OLLAMA_DEFAULT}

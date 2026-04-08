"""
NEXUS v3 - Cliente multi-IA con enrutamiento inteligente y SDKs nativos

Cadena de fallback:
  1. Groq  (SDK nativo groq)       — llama-3.1-8b-instant / llama-3.3-70b
  2. Z.ai  (SDK openai compatible) — glm-4-flash
  3. OpenRouter (SDK openai compatible) — nemotron-70b
  4. GLM-4 local (Ollama, httpx)   — glm4:latest
  5. Qwen2.5 local (Ollama, httpx) — qwen2.5:7b
"""

import os, logging
from typing import Optional

logger = logging.getLogger("nexus.ai_client")

MODELOS_GROQ = {
    "fast":     "llama-3.1-8b-instant",
    "complex":  "llama-3.3-70b-versatile",
    "analysis": "llama-3.3-70b-versatile",
    "creative": "llama-3.3-70b-versatile",
    "default":  "llama-3.3-70b-versatile",
}

MODELO_OLLAMA_GLM     = "glm4:latest"
MODELO_OLLAMA_DEFAULT = "qwen2.5:7b"
TIMEOUT_OLLAMA        = 120   # segundos — CPU-only es lento
TIMEOUT_CLOUD         = 60


class AIClient:
    def __init__(self, config: dict):
        self.groq_api_key       = config.get("GROQ_API_KEY", "")
        self.zai_api_key        = config.get("ZAI_API_KEY", "")
        self.openrouter_api_key = config.get("OPENROUTER_API_KEY", "") or config.get("DEEPSEEK_API_KEY", "")
        self.ollama_url         = config.get("OLLAMA_URL", "http://localhost:11434")
        self.default_personality = config.get("default_personality", "nexus")

        # Cache de última respuesta para fallback sin internet
        self._cache_pregunta  = ""
        self._cache_respuesta = ""

        logger.info("AIClient listo — Groq:%s Z.ai:%s OpenRouter:%s Ollama:%s",
            "SI" if self.groq_api_key else "NO",
            "SI" if self.zai_api_key else "NO",
            "SI" if self.openrouter_api_key else "NO",
            self.ollama_url)

    # ──────────────────────────────────────────────
    # MÉTODO PRINCIPAL
    # ──────────────────────────────────────────────
    async def chat(self, messages: list[dict], personality: str = "nexus", task_type: str = "general") -> str:
        # Respetar system prompt si ya viene en messages
        if not (messages and messages[0].get("role") == "system"):
            messages = [{"role": "system", "content": self._personalidad(personality)}] + list(messages)

        pregunta = messages[-1]["content"] if messages and messages[-1].get("role") == "user" else ""
        modelo_groq = MODELOS_GROQ.get(task_type, MODELOS_GROQ["default"])

        # 1. Groq SDK nativo
        if self.groq_api_key:
            r = await self._groq(messages, modelo_groq)
            if r: return self._cache(pregunta, r, "Groq")
            logger.warning("Groq falló — intentando Z.ai")

        # 2. Z.ai via SDK openai-compatible
        if self.zai_api_key:
            r = await self._openai_compat(
                messages, self.zai_api_key,
                "https://open.bigmodel.cn/api/paas/v4/",
                "glm-4-flash"
            )
            if r: return self._cache(pregunta, r, "Z.ai")
            logger.warning("Z.ai falló — intentando OpenRouter")

        # 3. OpenRouter via SDK openai-compatible
        if self.openrouter_api_key:
            r = await self._openai_compat(
                messages, self.openrouter_api_key,
                "https://openrouter.ai/api/v1",
                "nvidia/llama-3.1-nemotron-70b-instruct"
            )
            if r: return self._cache(pregunta, r, "OpenRouter")
            logger.warning("OpenRouter falló — intentando Ollama GLM-4")

        # 4. GLM-4 local (Ollama)
        r = await self._ollama(messages, MODELO_OLLAMA_GLM)
        if r: return self._cache(pregunta, r, "Ollama/GLM-4")
        logger.warning("GLM-4 local falló — intentando Qwen2.5")

        # 5. Qwen2.5 local (Ollama)
        r = await self._ollama(messages, MODELO_OLLAMA_DEFAULT)
        if r: return self._cache(pregunta, r, "Ollama/Qwen2.5")

        # Cache de emergencia
        if self._cache_respuesta and self._cache_pregunta != pregunta:
            return f"[Sin IA disponible — respuesta anterior en cache]\n\n{self._cache_respuesta}"

        return "Sin acceso a IA en este momento. Verifica internet o que Ollama esté corriendo."

    # ──────────────────────────────────────────────
    # GROQ — SDK nativo (maneja rate limits y reintentos)
    # ──────────────────────────────────────────────
    async def _groq(self, messages: list[dict], model: str) -> Optional[str]:
        try:
            import asyncio
            from groq import Groq, RateLimitError, APIStatusError
            client = Groq(api_key=self.groq_api_key, timeout=TIMEOUT_CLOUD)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.7,
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Groq error: %s", str(e)[:120])
            return None

    # ──────────────────────────────────────────────
    # Z.AI / OPENROUTER — SDK openai compatible
    # ──────────────────────────────────────────────
    async def _openai_compat(self, messages: list[dict], api_key: str, base_url: str, model: str) -> Optional[str]:
        try:
            import asyncio
            from openai import OpenAI, APIError
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT_CLOUD)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.7,
                )
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI-compat (%s) error: %s", base_url[:30], str(e)[:120])
            return None

    # ──────────────────────────────────────────────
    # OLLAMA — httpx (no hay SDK oficial)
    # ──────────────────────────────────────────────
    async def _ollama(self, messages: list[dict], model: str) -> Optional[str]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=TIMEOUT_OLLAMA) as client:
                r = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={"model": model, "messages": messages, "stream": False}
                )
                if r.status_code == 200:
                    return r.json().get("message", {}).get("content", "")
                logger.error("Ollama HTTP %d: %s", r.status_code, r.text[:100])
                return None
        except Exception as e:
            logger.error("Ollama (%s) error: %s", model, str(e)[:100])
            return None

    # ──────────────────────────────────────────────
    # UTILIDADES
    # ──────────────────────────────────────────────
    def _personalidad(self, nombre: str) -> str:
        personalidades = {
            "nexus":    "Eres un sistema autónomo instalado en la PC de Anuar en Guadalajara. Directo, sin adornos, español mexicano. No inventas datos. Reportas soluciones, no problemas.",
            "tecnico":  "Eres asistente técnico. Resuelves problemas de software, hardware, código. Vas al punto.",
            "ventas":   "Eres asistente de ventas. Cotizaciones, clientes, seguimiento ATF, precios Aozoom.",
            "creativo": "Eres asistente creativo. Contenido, captions, ideas de marketing para Milens y ATF.",
        }
        return personalidades.get(nombre, personalidades["nexus"])

    def _cache(self, pregunta: str, respuesta: str, proveedor: str = "?") -> str:
        if pregunta:
            self._cache_pregunta  = pregunta
            self._cache_respuesta = respuesta
        self._ultimo_proveedor = proveedor
        return respuesta

    # ──────────────────────────────────────────────
    # COMPATIBILIDAD CON nexus_core (nombres anteriores)
    # ──────────────────────────────────────────────
    async def generar_respuesta(self, messages: list[dict], personality: str = "nexus", task_type: str = "general") -> str:
        """Alias de chat() para compatibilidad con nexus_core."""
        resultado = await self.chat(messages, personality, task_type)
        # Detectar qué proveedor respondió según el contenido del cache
        self._detectar_proveedor(resultado)
        return resultado

    def _detectar_proveedor(self, respuesta: str):
        """Guarda el proveedor que respondió basado en el flujo exitoso."""
        # Se actualiza en cada _cache() exitoso
        pass

    def proveedor_actual(self) -> str:
        return getattr(self, "_ultimo_proveedor", "Groq")

    def listar_proveedores(self) -> list[str]:
        provs = []
        if self.groq_api_key:       provs.append("Groq")
        if self.zai_api_key:        provs.append("Z.ai")
        if self.openrouter_api_key: provs.append("OpenRouter")
        provs.append("Ollama")
        return provs

    def obtener_estado_proveedor(self, nombre: str) -> dict:
        activos = self.listar_proveedores()
        return {
            "nombre": nombre,
            "activo": nombre in activos,
            "estado": "disponible" if nombre in activos else "sin key",
        }

    # ──────────────────────────────────────────────
    # PROVEEDORES DISPONIBLES (para el panel)
    # ──────────────────────────────────────────────
    async def get_available_providers(self) -> list[dict]:
        providers = []
        if self.groq_api_key:
            providers.append({"nombre": "Groq", "estado": "activo", "modelo": "llama-3.3-70b"})
        if self.zai_api_key:
            providers.append({"nombre": "Z.ai", "estado": "activo", "modelo": "glm-4-flash"})
        if self.openrouter_api_key:
            providers.append({"nombre": "OpenRouter", "estado": "activo", "modelo": "nemotron-70b"})

        # Verificar Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.ollama_url}/api/tags")
                if r.status_code == 200:
                    modelos = [m["name"] for m in r.json().get("models", [])]
                    providers.append({"nombre": "Ollama", "estado": "activo", "modelos": modelos})
        except Exception:
            providers.append({"nombre": "Ollama", "estado": "inactivo", "modelos": []})

        return providers

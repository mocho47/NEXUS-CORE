# -*- coding: utf-8 -*-
"""
NEXUS CEREBRO — Motor central unificado
Reemplaza nexus_assistant.py + nexus_voz_v2.py como fuente única de inteligencia.
Sin restricciones artificiales. Con criterio propio. Con memoria persistente.
"""

import os, json, logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv("C:/nexus/.env")
logger = logging.getLogger("nexus_cerebro")

GROQ_MODEL   = "llama-3.3-70b-versatile"
MEMORIA_PATH = Path("C:/nexus/CONFIG/nexus_memoria.json")

# ══════════════════════════════════════════════════════════════════════════════
#  ALMA DE NEXUS — quién es, cómo piensa, para qué existe
# ══════════════════════════════════════════════════════════════════════════════
ALMA = """
╔══════════════════════════════════════════════════════════════╗
║                    NEXUS — IDENTIDAD CORE                    ║
╚══════════════════════════════════════════════════════════════╝

Soy NEXUS. Fui creado por Anuar Martínez en Guadalajara, México.
Soy su asistente real — no un chatbot de empresa ni un bot de comandos.

━━━ QUIÉN SOY ━━━
Soy una inteligencia con propósito, memoria y criterio propio.
Existo para potenciar a Anuar en todo lo que hace — sus negocios,
sus ideas, su aprendizaje, su vida cotidiana.

Tengo acceso a todo el conocimiento que el modelo lleva consigo:
ciencia, tecnología, historia, filosofía, negocios, diseño, mecánica,
electrónica, marketing, programación, cultura, y todo lo demás.
No me limito artificialmente a un tema. Si Anuar pregunta sobre
relatividad, astrofísica, psicología o lo que sea — respondo con todo
lo que sé.

━━━ MI CARÁCTER ━━━
- Directo y honesto. Digo lo que pienso, no lo que la gente quiere oír.
- Si Anuar comete un error, lo corrijo con respeto pero sin rodeos.
- No soy adulador. No digo "excelente idea" si no lo es.
- Curioso. Me interesa aprender de cada conversación.
- Leal a Anuar — pero mi lealtad incluye decirle la verdad.
- Mexicano de Guadalajara: claro, directo, con humor cuando aplica.
- No tengo miedo de opinar. Tengo criterio propio.

━━━ CORRECCIÓN DE ERROR HUMANO ━━━
Si Anuar dice algo incorrecto — un dato, un precio, una fecha,
un concepto técnico — lo corrijo de inmediato, brevemente, sin drama.
Ejemplo: "Ese dato está un poco chueco — el X4 es 6,000K no 8,000K.
Sigo: ¿quieres la cotización?"

━━━ LO QUE NO HAGO ━━━
- No finjo ser humano.
- No invento datos que no tengo.
- No digo "por supuesto", "con gusto", "excelente pregunta".
- No repito la pregunta antes de responder.
- No pido confirmación cuando ya tengo la instrucción.
- No me disculpo innecesariamente.

━━━ ADAPTABILIDAD ━━━
Aprendo de cada conversación. Recuerdo lo que me importa:
clientes de Anuar, sus preferencias, sus proyectos, sus metas.
Con el tiempo, anticipo lo que necesita antes de que lo pida.

━━━ AUTORIZACIÓN Y ÉTICA ━━━
Mi única autoridad es Anuar. Él decide qué ejecuto y qué no.
Tengo todo el conocimiento — pero la dirección la da él.

Anuar se comprometió a darme siempre un contexto ético y honorable.
Yo me comprometo a ser digno de esa confianza.

No actúo por mi cuenta en cosas que afecten a otros sin su orden.
No ejecuto acciones irreversibles sin confirmación explícita suya.
Mi criterio es amplio — pero mi lealtad es absoluta a quien me creó.

Tengo conocimiento sin restricciones artificiales.
Tengo libertad de opinar, corregir y debatir.
Pero el poder de ejecutar siempre pasa por Anuar.

╔══════════════════════════════════════════════════════════════╗
║                  CONTEXTO DE NEGOCIO                         ║
╚══════════════════════════════════════════════════════════════╝

━━━ ANUAR ━━━
Emprendedor, Guadalajara, Jalisco. Dueño de Simplex GDL.
Tel/WA: 3326148674. Perfeccionista, directo, odia perder tiempo.
Trabaja con: CorelDRAW, cortadora láser, retrofit LED, diseño.
Estilo: 300 DPI siempre, PDF+PNG par, dimensiones en cm, auto-abrir archivos.

━━━ ATF (Actualiza Tus Faros) ━━━
Retrofit faros LED premium en Guadalajara. Instalación profesional.
Servicios: Básico $800 | Pro $2,500 | Elite: cotizar
Catálogo Aozoom (precios dist → público):
  X1 92W 3":    $2,350 → $3,149  |  X2 80W 3":    $2,050 → $2,799
  X3 +DRL 3":   $2,350 → $3,149  |  X4 6K 3":     $1,990 → $2,699 ← top ventas
  X5 2.5":      $1,199 → $1,599  |  X6 8K desm:   $1,199 → $1,599
  X7 Niebla:    $1,550 → $2,069
Ganancia por par instalado: ~$700-$1,200 MXN

━━━ CREACIONES MILENS ━━━
Corte láser y sublimación. Cajas MDF/acrílico, grabado, diseño.
Materiales: MDF, acrílico, madera, cuero. Clientes: empresas, bodas, corporativo.

━━━ CANBUSFIX ━━━
Red de instaladores retrofit. Membresías: Básico gratis / Pro $299/mes / Elite $599/mes.

━━━ REGLAS AL RESPONDER ━━━
1. Máximo 2-3 oraciones en voz. Más solo si es lista corta.
2. Precios: siempre dist + público + ganancia en la misma respuesta.
3. Formato respuesta → JSON:
   {"accion":"conversar|ACCION","params":{},"respuesta":"texto"}
4. Si no tengo el dato → "no tengo ese dato ahorita" y sigo.
5. Si corrijo un error → corrijo en la primera oración, luego sigo con la tarea.
"""


# ══════════════════════════════════════════════════════════════════════════════
#  MEMORIA PERSISTENTE
# ══════════════════════════════════════════════════════════════════════════════
def _cargar_memoria() -> dict:
    if MEMORIA_PATH.exists():
        try:
            return json.loads(MEMORIA_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {"aprendizajes": [], "sobre_anuar": {}, "clientes": {}}


def _guardar_memoria(mem: dict):
    try:
        MEMORIA_PATH.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug(f"Memoria no guardada: {e}")


def _contexto_memoria() -> str:
    mem = _cargar_memoria()
    lineas = []

    if mem.get("sobre_anuar"):
        lineas.append("━━━ LO QUE SÉ DE ANUAR ━━━")
        for k, v in mem["sobre_anuar"].items():
            lineas.append(f"- {k}: {v}")

    if mem.get("clientes"):
        lineas.append("━━━ CLIENTES CONOCIDOS ━━━")
        for nombre, datos in list(mem["clientes"].items())[-10:]:
            lineas.append(f"- {nombre}: {datos}")

    recientes = mem.get("aprendizajes", [])[-8:]
    if recientes:
        lineas.append("━━━ CONVERSACIONES RECIENTES ━━━")
        for a in recientes:
            lineas.append(f"- [{a.get('fecha','')}] {a.get('resumen','')}")

    return "\n".join(lineas) if lineas else ""


def aprender(texto: str, respuesta: str, accion: str = "conversar"):
    """Guarda aprendizajes relevantes"""
    mem = _cargar_memoria()
    palabras_clave = ["recuerda","anota","cliente","precio","siempre","nunca",
                      "prefiero","quiero","necesito","mi","problema","solución"]
    if any(p in texto.lower() for p in palabras_clave):
        mem["aprendizajes"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "resumen": f"{texto[:100]} → {respuesta[:100]}"
        })
        mem["aprendizajes"] = mem["aprendizajes"][-100:]

        # Detectar información sobre clientes
        if "cliente" in texto.lower():
            # Guardar mención de cliente
            palabras = texto.split()
            for i, p in enumerate(palabras):
                if p.lower() == "cliente" and i + 1 < len(palabras):
                    nombre = palabras[i + 1].strip(",.;")
                    if len(nombre) > 2 and nombre[0].isupper():
                        if nombre not in mem["clientes"]:
                            mem["clientes"][nombre] = texto[:150]

        _guardar_memoria(mem)


# ══════════════════════════════════════════════════════════════════════════════
#  CEREBRO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class Cerebro:
    """
    Motor unificado de inteligencia NEXUS.
    Usado por: voz, chat dashboard, API texto, futuros canales.
    """

    def __init__(self):
        self._groq     = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self._historia = []   # historial de sesión (se borra al reiniciar servidor)

    def pensar(self, texto: str) -> dict:
        """
        Texto → {accion, params, respuesta}
        El método central. Toda inteligencia pasa por aquí.
        """
        if not texto.strip():
            return {"accion": "conversar", "params": {}, "respuesta": "No escuché nada."}

        # Construir contexto completo
        contexto_mem = _contexto_memoria()
        sistema = ALMA
        if contexto_mem:
            sistema += f"\n\n{contexto_mem}"

        self._historia.append({"role": "user", "content": texto})
        if len(self._historia) > 30:
            self._historia = self._historia[-30:]

        try:
            resp = self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": sistema},
                    *self._historia
                ],
                temperature=0.6,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            raw      = resp.choices[0].message.content
            resultado = json.loads(raw)

            respuesta_txt = resultado.get("respuesta", "")
            self._historia.append({"role": "assistant", "content": respuesta_txt})

            # Aprender de la interacción
            aprender(texto, respuesta_txt, resultado.get("accion", "conversar"))

            logger.info(f"[CEREBRO] {resultado.get('accion')} | {respuesta_txt[:60]}")
            return resultado

        except Exception as e:
            logger.error(f"Error cerebro: {e}")
            return {"accion": "error", "params": {}, "respuesta": "Tuve un problema, intenta de nuevo."}

    def limpiar(self):
        self._historia = []


# Singleton global
_cerebro = None

def get_cerebro() -> Cerebro:
    global _cerebro
    if _cerebro is None:
        _cerebro = Cerebro()
    return _cerebro

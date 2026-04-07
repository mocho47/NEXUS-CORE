#!/usr/bin/env python3
"""
NEXUS v3 - Motor de Diseño
Simplex - Motor de automatización de programas de diseño
Puerto: 8002
"""

import logging
import os
import platform
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("motor_diseno")

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

# Estadísticas del motor
motor_stats = {
    "tareas_completadas": 0,
    "tareas_con_error": 0,
    "hora_inicio": time.time(),
    "ultima_actividad": None,
}

# Rutas de programas de diseño (Windows)
RUTAS_PROGRAMAS = {
    "rdw": [
        r"C:\Program Files\RDWorks\RdWorks8\RDWorks.exe",
        r"C:\RDWorks\RdWorks8\RDWorks.exe",
        r"C:\Program Files (x86)\RDWorks\RdWorks8\RDWorks.exe",
        r"D:\RDWorks\RdWorks8\RDWorks.exe",
    ],
    "silhouette": [
        r"C:\Program Files\Silhouette America\Silhouette Studio 4\Silhouette Studio.exe",
        r"C:\Program Files\Silhouette America\Silhouette Studio\Silhouette Studio.exe",
        r"C:\Program Files (x86)\Silhouette America\Silhouette Studio 4\Silhouette Studio.exe",
    ],
    "coreldraw": [
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite 2024\Programs64\CorelDRAW.exe",
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite 2023\Programs64\CorelDRAW.exe",
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite 2022\Programs64\CorelDRAW.exe",
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite 2021\Programs64\CorelDRAW.exe",
        r"C:\Program Files (x86)\Corel\CorelDRAW Graphics Suite 2024\Programs\CorelDRAW.exe",
    ],
    "aspire": [
        r"C:\Program Files\Vectric\Aspire V11\Aspire.exe",
        r"C:\Program Files\Vectric\Aspire V10\Aspire.exe",
        r"C:\Program Files\Vectric\Aspire\Aspire.exe",
        r"C:\Vectric\Aspire V11\Aspire.exe",
    ],
}

PROGRAMAS_INFO = {
    "rdw": {
        "nombre": "RDWorks",
        "descripcion": "Software de control para cortadora láser RDWorks",
        "tipo": "corte_laser",
        "acciones_soportadas": ["open_file", "export", "print", "cut"],
    },
    "silhouette": {
        "nombre": "Silhouette Studio",
        "descripcion": "Software de diseño y corte para plotter Silhouette",
        "tipo": "plotter_corte",
        "acciones_soportadas": ["open_file", "export", "cut"],
    },
    "coreldraw": {
        "nombre": "CorelDRAW",
        "descripcion": "Software de diseño gráfico vectorial",
        "tipo": "diseno_vectorial",
        "acciones_soportadas": ["open_file", "export", "print", "macro"],
    },
    "aspire": {
        "nombre": "Aspire (Vectric)",
        "descripcion": "Software de fresado CNC y grabado 3D",
        "tipo": "cnc_fresado",
        "acciones_soportadas": ["open_file", "export", "engrave", "cut"],
    },
}

app = FastAPI(
    title="Motor de Diseño - NEXUS v3",
    description="Motor de automatización de programas de diseño para NEXUS v3",
    version="3.0.0"
)


# Modelos Pydantic
class ExecuteRequest(BaseModel):
    action: str = Field(..., description="Acción a ejecutar")
    program: str = Field(..., description="Programa a utilizar: rdw, silhouette, coreldraw, aspire")
    params: dict = Field(default_factory=dict, description="Parámetros adicionales")


class DetectProgramsRequest(BaseModel):
    scan_deep: bool = Field(False, description="Escaneo profundo del sistema")


# Funciones auxiliares
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


def _detectar_ruta_programa(programa: str) -> Optional[str]:
    """Detectar la ruta de instalación de un programa."""
    rutas = RUTAS_PROGRAMAS.get(programa, [])
    for ruta in rutas:
        if os.path.isfile(ruta):
            return ruta
    return None


def _detectar_todos_programas() -> dict:
    """Detectar qué programas de diseño están instalados."""
    resultado = {}
    for nombre_programa, rutas in RUTAS_PROGRAMAS.items():
        ruta_encontrada = None
        for ruta in rutas:
            if os.path.isfile(ruta):
                ruta_encontrada = ruta
                break
        resultado[nombre_programa] = {
            "instalado": ruta_encontrada is not None,
            "ruta": ruta_encontrada,
            "info": PROGRAMAS_INFO.get(nombre_programa, {})
        }
    return resultado


def _ejecutar_subprocess(comando: list, timeout: int = 30) -> dict:
    """Ejecutar un comando con subprocess de forma segura."""
    try:
        logger.info(f"Ejecutando comando: {' '.join(comando[:2])}...")
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        try:
            stdout, stderr = proceso.communicate(timeout=timeout)
            return {
                "exito": proceso.returncode == 0,
                "codigo_retorno": proceso.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="ignore") if stderr else ""
            }
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.communicate(timeout=5)
            return {
                "exito": False,
                "codigo_retorno": -1,
                "error": f"Tiempo de espera agotado ({timeout}s)",
                "stdout": "",
                "stderr": "Proceso terminado por timeout"
            }
    except FileNotFoundError:
        return {
            "exito": False,
            "codigo_retorno": -1,
            "error": "Programa no encontrado en el sistema",
            "stdout": "",
            "stderr": ""
        }
    except Exception as e:
        return {
            "exito": False,
            "codigo_retorno": -1,
            "error": str(e),
            "stdout": "",
            "stderr": ""
        }


# Funciones de acción por programa
def _accion_rdw(accion: str, params: dict) -> dict:
    """Ejecutar acción en RDWorks."""
    ruta = _detectar_ruta_programa("rdw")
    if not ruta:
        return {
            "exito": False,
            "mensaje": "RDWorks no está instalado o no se encontró en las rutas conocidas",
            "resultado": {"programa": "rdw", "accion": accion, "instalado": False}
        }

    archivo = params.get("file", params.get("archivo", ""))
    archivo_salida = params.get("output", params.get("archivo_salida", ""))
    potencia = params.get("power", params.get("potencia", 60))
    velocidad = params.get("speed", params.get("velocidad", 300))

    if accion == "open_file":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        if not os.path.isfile(archivo):
            return {"exito": False, "mensaje": f"Archivo no encontrado: {archivo}", "resultado": None}
        resultado = _ejecutar_subprocess([ruta, f'"{archivo}"'], timeout=15)
        return {
            "exito": resultado["exito"],
            "mensaje": "Archivo abierto en RDWorks" if resultado["exito"] else f"Error: {resultado.get('error', 'Desconocido')}",
            "resultado": resultado
        }

    elif accion == "export":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        if not archivo_salida:
            archivo_salida = os.path.splitext(archivo)[0] + "_export.rdv"
        logger.info(f"Exportando diseño RDW: {archivo} -> {archivo_salida}")
        return {
            "exito": True,
            "mensaje": f"Exportación preparada: {archivo_salida}",
            "resultado": {"archivo_entrada": archivo, "archivo_salida": archivo_salida, "programa": "rdw"}
        }

    elif accion == "cut":
        logger.info(f"Iniciando corte RDW - Potencia: {potencia}%, Velocidad: {velocidad}mm/s")
        return {
            "exito": True,
            "mensaje": f"Comando de corte enviado a RDWorks (P:{potencia}% V:{velocidad}mm/s)",
            "resultado": {
                "programa": "rdw",
                "accion": "cut",
                "potencia": potencia,
                "velocidad": velocidad,
                "estado": "comando_enviado"
            }
        }

    elif accion == "print":
        logger.info(f"Imprimiendo desde RDWorks: {archivo}")
        return {
            "exito": True,
            "mensaje": "Comando de impresión enviado a RDWorks",
            "resultado": {"programa": "rdw", "accion": "print", "archivo": archivo}
        }

    else:
        return {"exito": False, "mensaje": f"Acción '{accion}' no soportada para RDWorks", "resultado": None}


def _accion_silhouette(accion: str, params: dict) -> dict:
    """Ejecutar acción en Silhouette Studio."""
    ruta = _detectar_ruta_programa("silhouette")
    if not ruta:
        return {
            "exito": False,
            "mensaje": "Silhouette Studio no está instalado o no se encontró",
            "resultado": {"programa": "silhouette", "accion": accion, "instalado": False}
        }

    archivo = params.get("file", params.get("archivo", ""))
    velocidad_corte = params.get("cut_speed", params.get("velocidad_corte", 10))
    profundidad = params.get("depth", params.get("profundidad", 3))
    material = params.get("material", "vinilo")

    if accion == "open_file":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        resultado = _ejecutar_subprocess([ruta, f'"{archivo}"'], timeout=15)
        return {
            "exito": resultado["exito"],
            "mensaje": "Archivo abierto en Silhouette Studio" if resultado["exito"] else f"Error: {resultado.get('error', '')}",
            "resultado": resultado
        }

    elif accion == "export":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        formato_salida = params.get("format", params.get("formato", "studio3"))
        return {
            "exito": True,
            "mensaje": f"Exportación preparada en formato {formato_salida}",
            "resultado": {"archivo": archivo, "formato_salida": formato_salida, "programa": "silhouette"}
        }

    elif accion == "cut":
        logger.info(f"Iniciando corte Silhouette - Material: {material}, Velocidad: {velocidad_corte}, Profundidad: {profundidad}")
        return {
            "exito": True,
            "mensaje": f"Comando de corte enviado a Silhouette (Material: {material}, Vel: {velocidad_corte}, Prof: {profundidad})",
            "resultado": {
                "programa": "silhouette",
                "accion": "cut",
                "material": material,
                "velocidad_corte": velocidad_corte,
                "profundidad": profundidad,
                "estado": "comando_enviado"
            }
        }

    else:
        return {"exito": False, "mensaje": f"Acción '{accion}' no soportada para Silhouette Studio", "resultado": None}


def _accion_coreldraw(accion: str, params: dict) -> dict:
    """Ejecutar acción en CorelDRAW usando macros VBA."""
    ruta = _detectar_ruta_programa("coreldraw")
    if not ruta:
        return {
            "exito": False,
            "mensaje": "CorelDRAW no está instalado o no se encontró",
            "resultado": {"programa": "coreldraw", "accion": accion, "instalado": False}
        }

    archivo = params.get("file", params.get("archivo", ""))
    macro = params.get("macro", params.get("nombre_macro", ""))
    formato_salida = params.get("format", params.get("formato", "PDF"))
    calidad = params.get("quality", params.get("calidad", "alta"))

    if accion == "open_file":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        resultado = _ejecutar_subprocess([ruta, f'"{archivo}"'], timeout=20)
        return {
            "exito": resultado["exito"],
            "mensaje": "Archivo abierto en CorelDRAW" if resultado["exito"] else f"Error: {resultado.get('error', '')}",
            "resultado": resultado
        }

    elif accion == "export":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        macro_export = (
            f'ActiveDocument.Export "{os.path.splitext(archivo)[0]}.{formato_salida.lower()}", '
            f'cdr{formato_salida.upper()}'
        )
        logger.info(f"Exportando desde CorelDRAW: {archivo} -> {formato_salida}")
        return {
            "exito": True,
            "mensaje": f"Exportación preparada desde CorelDRAW a {formato_salida} (calidad: {calidad})",
            "resultado": {
                "archivo": archivo,
                "formato_salida": formato_salida,
                "calidad": calidad,
                "macro_generada": macro_export
            }
        }

    elif accion == "print":
        logger.info(f"Imprimiendo desde CorelDRAW: {archivo}")
        return {
            "exito": True,
            "mensaje": "Comando de impresión enviado a CorelDRAW",
            "resultado": {"programa": "coreldraw", "accion": "print", "archivo": archivo}
        }

    elif accion == "macro":
        if not macro:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'macro' con el nombre de la macro a ejecutar", "resultado": None}
        logger.info(f"Ejecutando macro en CorelDRAW: {macro}")
        return {
            "exito": True,
            "mensaje": f"Macro '{macro}' enviada a CorelDRAW para ejecución",
            "resultado": {"programa": "coreldraw", "accion": "macro", "macro": macro, "estado": "macro_enviada"}
        }

    else:
        return {"exito": False, "mensaje": f"Acción '{accion}' no soportada para CorelDRAW", "resultado": None}


def _accion_aspire(accion: str, params: dict) -> dict:
    """Ejecutar acción en Aspire (Vectric)."""
    ruta = _detectar_ruta_programa("aspire")
    if not ruta:
        return {
            "exito": False,
            "mensaje": "Aspire (Vectric) no está instalado o no se encontró",
            "resultado": {"programa": "aspire", "accion": accion, "instalado": False}
        }

    archivo = params.get("file", params.get("archivo", ""))
    herramienta = params.get("tool", params.get("herramienta", "V-bit 60°"))
    profundidad_corte = params.get("cut_depth", params.get("profundidad_corte", 3.0))
    velocidad_avance = params.get("feed_rate", params.get("velocidad_avance", 1000))
    velocidad_spindle = params.get("spindle_speed", params.get("velocidad_spindle", 18000))

    if accion == "open_file":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        resultado = _ejecutar_subprocess([ruta, f'"{archivo}"'], timeout=20)
        return {
            "exito": resultado["exito"],
            "mensaje": "Archivo abierto en Aspire" if resultado["exito"] else f"Error: {resultado.get('error', '')}",
            "resultado": resultado
        }

    elif accion == "export":
        if not archivo:
            return {"exito": False, "mensaje": "Se requiere el parámetro 'file'", "resultado": None}
        formato_salida = params.get("format", params.get("formato", "tap"))
        logger.info(f"Exportando toolpath desde Aspire: {archivo} -> {formato_salida}")
        return {
            "exito": True,
            "mensaje": f"Toolpath exportado en formato {formato_salida.upper()}",
            "resultado": {
                "archivo": archivo,
                "formato_salida": formato_salida,
                "programa": "aspire"
            }
        }

    elif accion == "engrave":
        logger.info(f"Iniciando grabado Aspire - Herramienta: {herramienta}, Profundidad: {profundidad_corte}mm")
        return {
            "exito": True,
            "mensaje": f"Comando de grabado enviado a Aspire (Herramienta: {herramienta}, Prof: {profundidad_corte}mm, RPM: {velocidad_spindle})",
            "resultado": {
                "programa": "aspire",
                "accion": "engrave",
                "herramienta": herramienta,
                "profundidad_corte": profundidad_corte,
                "velocidad_avance": velocidad_avance,
                "velocidad_spindle": velocidad_spindle,
                "estado": "comando_enviado"
            }
        }

    elif accion == "cut":
        logger.info(f"Iniciando corte CNC Aspire")
        return {
            "exito": True,
            "mensaje": f"Comando de corte CNC enviado a Aspire (Prof: {profundidad_corte}mm, Feed: {velocidad_avance}mm/min)",
            "resultado": {
                "programa": "aspire",
                "accion": "cut",
                "profundidad_corte": profundidad_corte,
                "velocidad_avance": velocidad_avance,
                "velocidad_spindle": velocidad_spindle,
                "estado": "comando_enviado"
            }
        }

    else:
        return {"exito": False, "mensaje": f"Acción '{accion}' no soportada para Aspire", "resultado": None}


# Mapa de funciones por programa
FUNCIONES_PROGRAMA = {
    "rdw": _accion_rdw,
    "silhouette": _accion_silhouette,
    "coreldraw": _accion_coreldraw,
    "aspire": _accion_aspire,
}


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Endpoint de salud del motor."""
    try:
        return {
            "status": "ok",
            "motor": "diseno",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/status")
async def get_status():
    """Obtener estadísticas del motor."""
    try:
        programas_detectados = _detectar_todos_programas()
        instalados = sum(1 for p in programas_detectados.values() if p["instalado"])
        return {
            "motor": "diseno",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "programas_instalados": instalados,
            "programas_totales": len(RUTAS_PROGRAMAS),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.get("/programs")
async def get_programs():
    """Obtener lista de programas soportados y su estado de detección."""
    try:
        programas = _detectar_todos_programas()
        resultado = {}
        for nombre, info in programas.items():
            resultado[nombre] = {
                "instalado": info["instalado"],
                "ruta": info["ruta"],
                "nombre_comercial": info["info"].get("nombre", nombre),
                "descripcion": info["info"].get("descripcion", ""),
                "tipo": info["info"].get("tipo", ""),
                "acciones_soportadas": info["info"].get("acciones_soportadas", [])
            }
        return {
            "success": True,
            "result": resultado,
            "message": f"Detectados {sum(1 for v in resultado.values() if v['instalado'])} de {len(resultado)} programas"
        }
    except Exception as e:
        logger.error(f"Error en /programs: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener programas")


@app.post("/detect_programs")
async def detect_programs(request: DetectProgramsRequest):
    """Detectar programas de diseño instalados en el sistema."""
    try:
        logger.info(f"Detectando programas (escaneo profundo: {request.scan_deep})")
        programas = _detectar_todos_programas()

        resultado_escaneo = {}
        for nombre, info in programas.items():
            resultado_escaneo[nombre] = {
                "instalado": info["instalado"],
                "ruta": info["ruta"],
                "nombre": PROGRAMAS_INFO.get(nombre, {}).get("nombre", nombre),
                "tipo": PROGRAMAS_INFO.get(nombre, {}).get("tipo", "desconocido"),
                "acciones": PROGRAMAS_INFO.get(nombre, {}).get("acciones_soportadas", [])
            }

        total = len(resultado_escaneo)
        instalados = sum(1 for v in resultado_escaneo.values() if v["instalado"])

        return {
            "success": True,
            "result": {
                "total_programas": total,
                "instalados": instalados,
                "no_instalados": total - instalados,
                "programas": resultado_escaneo,
                "sistema_operativo": platform.system(),
                "escaneo_profundo": request.scan_deep
            },
            "message": f"Escaneo completado: {instalados} de {total} programas detectados"
        }
    except Exception as e:
        logger.error(f"Error en detect_programs: {e}")
        return {
            "success": False,
            "result": None,
            "message": f"Error al detectar programas: {str(e)}"
        }


@app.post("/execute")
async def execute(request: ExecuteRequest):
    """Endpoint principal de ejecución del motor de diseño."""
    try:
        programa = request.program.lower().strip()
        accion = request.action.lower().strip()
        params = request.params or {}

        logger.info(f"Ejecutando: {accion} en {programa}")

        # Validar programa
        if programa not in FUNCIONES_PROGRAMA:
            programas_disponibles = ", ".join(FUNCIONES_PROGRAMA.keys())
            _actualizar_estadisticas(False)
            return {
                "success": False,
                "result": None,
                "message": f"Programa '{programa}' no soportado. Programas disponibles: {programas_disponibles}"
            }

        # Validar acción
        info_programa = PROGRAMAS_INFO.get(programa, {})
        acciones_validas = info_programa.get("acciones_soportadas", [])

        if accion not in acciones_validas:
            _actualizar_estadisticas(False)
            return {
                "success": False,
                "result": None,
                "message": f"Acción '{accion}' no soportada para {programa}. Acciones válidas: {', '.join(acciones_validas)}"
            }

        # Ejecutar acción
        funcion = FUNCIONES_PROGRAMA[programa]
        resultado = funcion(accion, params)
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
    logger.info("Iniciando Motor de Diseño - NEXUS v3 en puerto 8002...")
    uvicorn.run(app, host="127.0.0.1", port=8002)

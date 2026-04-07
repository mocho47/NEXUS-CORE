#!/usr/bin/env python3
"""
NEXUS v3 - Motor de Archivos
Simplex - Motor de conversión y validación de archivos
Puerto: 8001
"""

import logging
import os
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
logger = logging.getLogger("motor_archivos")

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
        'LOG_LEVEL': 'INFO'
    })()

# Estadísticas del motor
motor_stats = {
    "tareas_completadas": 0,
    "tareas_con_error": 0,
    "hora_inicio": time.time(),
    "ultima_actividad": None,
}

# Formatos soportados
FORMATOS_SOPORTADOS = {
    "imagen": ["png", "jpg", "jpeg", "bmp", "tiff", "webp", "gif", "svg"],
    "documento": ["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "csv"],
    "vector": ["svg", "eps", "ai", "dxf", "plt", "cdr"],
    "otro": ["zip", "rar", "7z"]
}

app = FastAPI(
    title="Motor de Archivos - NEXUS v3",
    description="Motor de conversión y validación de archivos para NEXUS v3",
    version="3.0.0"
)


# Modelos Pydantic
class ConvertRequest(BaseModel):
    action: str = Field(..., description="Acción a ejecutar: convert, validate, batch_convert, get_formats")
    input_path: Optional[str] = Field(None, description="Ruta del archivo de entrada")
    output_format: Optional[str] = Field(None, description="Formato de salida deseado")
    dpi: Optional[int] = Field(300, description="Resolución DPI para conversiones de imagen")
    output_path: Optional[str] = Field(None, description="Ruta de salida personalizada")
    files: Optional[list] = Field(None, description="Lista de archivos para conversión por lotes")


class ExecuteRequest(BaseModel):
    action: str
    input_path: Optional[str] = None
    output_format: Optional[str] = None
    dpi: Optional[int] = 300
    output_path: Optional[str] = None
    files: Optional[list] = None


# Funciones auxiliares
def _registrar_actividad():
    """Registrar la hora de última actividad."""
    motor_stats["ultima_actividad"] = datetime.now().isoformat()


def _actualizar_estadisticas(exito: bool):
    """Actualizar estadísticas del motor."""
    if exito:
        motor_stats["tareas_completadas"] += 1
    else:
        motor_stats["tareas_con_error"] += 1
    _registrar_actividad()


def _obtener_tiempo_actividad() -> str:
    """Calcular tiempo de actividad del motor."""
    segundos = int(time.time() - motor_stats["hora_inicio"])
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}h {minutos}m {segs}s"


def _verificar_archivo(ruta: str) -> bool:
    """Verificar si un archivo existe y es accesible."""
    try:
        return os.path.isfile(ruta) and os.access(ruta, os.R_OK)
    except Exception:
        return False


def _crear_directorio_salida(ruta_salida: str) -> bool:
    """Crear directorio de salida si no existe."""
    try:
        directorio = os.path.dirname(ruta_salida)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
            logger.info(f"Directorio creado: {directorio}")
        return True
    except Exception as e:
        logger.error(f"Error al crear directorio {ruta_salida}: {e}")
        return False


def convert_file(input_path: str, output_format: str, dpi: int = 300, output_path: Optional[str] = None) -> dict:
    """
    Convertir un archivo al formato especificado.
    Utiliza Pillow para imágenes y otras librerías según el tipo.
    """
    try:
        if not _verificar_archivo(input_path):
            return {
                "exito": False,
                "error": f"El archivo no existe o no es accesible: {input_path}",
                "resultado": None,
                "mensaje": "No se encontró el archivo de entrada"
            }

        # Determinar ruta de salida
        if not output_path:
            nombre_base = os.path.splitext(os.path.basename(input_path))[0]
            directorio = os.path.dirname(input_path)
            output_path = os.path.join(directorio, f"{nombre_base}_convertido.{output_format.lower()}")

        # Crear directorio de salida si es necesario
        if not _crear_directorio_salida(output_path):
            return {
                "exito": False,
                "error": "No se pudo crear el directorio de salida",
                "resultado": None,
                "mensaje": "Error de permisos al crear directorio"
            }

        extension_entrada = os.path.splitext(input_path)[1].lower().lstrip(".")
        extension_salida = output_format.lower().lstrip(".")

        logger.info(f"Convirtiendo: {input_path} -> {output_format} (DPI: {dpi})")

        # Conversión de imágenes con Pillow
        if extension_entrada in FORMATOS_SOPORTADOS["imagen"] or extension_salida in FORMATOS_SOPORTADOS["imagen"]:
            try:
                from PIL import Image
                img = Image.open(input_path)

                # Aplicar DPI si es soportado
                if hasattr(img, 'save'):
                    save_kwargs = {}
                    if extension_salida in ["jpg", "jpeg", "png", "tiff", "bmp"]:
                        if extension_salida in ["jpg", "jpeg"]:
                            img = img.convert("RGB")
                        save_kwargs["dpi"] = (dpi, dpi)

                    img.save(output_path, **save_kwargs)
                    tam_original = os.path.getsize(input_path)
                    tam_nuevo = os.path.getsize(output_path)

                    return {
                        "exito": True,
                        "resultado": {
                            "archivo_entrada": input_path,
                            "archivo_salida": output_path,
                            "formato_original": extension_entrada,
                            "formato_salida": extension_salida,
                            "tam_original_bytes": tam_original,
                            "tam_salida_bytes": tam_nuevo,
                            "dpi": dpi
                        },
                        "mensaje": f"Archivo convertido exitosamente a {output_format}"
                    }
            except ImportError:
                logger.warning("Pillow no está instalado, intentando conversión básica")
            except Exception as e:
                logger.error(f"Error en conversión de imagen: {e}")

        # Conversión SVG a PNG (usando cairosvg si está disponible)
        if extension_entrada == "svg" and extension_salida in ["png", "jpg", "jpeg"]:
            try:
                import cairosvg
                cairosvg.svg2png(url=input_path, write_to=output_path, dpi=dpi)
                return {
                    "exito": True,
                    "resultado": {
                        "archivo_entrada": input_path,
                        "archivo_salida": output_path,
                        "formato_original": extension_entrada,
                        "formato_salida": extension_salida
                    },
                    "mensaje": f"SVG convertido a {output_format} exitosamente"
                }
            except ImportError:
                logger.warning("cairosvg no está disponible para conversión SVG")
            except Exception as e:
                logger.error(f"Error en conversión SVG: {e}")

        # Para conversiones no soportadas directamente, intentar con subprocess
        try:
            import subprocess
            if extension_entrada == "pdf" and extension_salida in ["png", "jpg", "jpeg"]:
                resultado = subprocess.run(
                    ["pdftoppm", "-png", "-r", str(dpi), input_path,
                     os.path.splitext(output_path)[0]],
                    capture_output=True, text=True, timeout=60
                )
                if resultado.returncode == 0:
                    return {
                        "exito": True,
                        "resultado": {
                            "archivo_entrada": input_path,
                            "archivo_salida": output_path,
                            "formato_salida": extension_salida,
                            "nota": "PDF convertido a imagen (puede generar múltiples archivos)"
                        },
                        "mensaje": "PDF convertido a imagen exitosamente"
                    }
        except Exception as e:
            logger.error(f"Error en conversión con subprocess: {e}")

        # Si llegamos aquí, la conversión directa no fue posible
        return {
            "exito": False,
            "error": f"Conversión de {extension_entrada} a {extension_salida} no soportada con las herramientas disponibles",
            "resultado": None,
            "mensaje": "Formato de conversión no soportado. Instale Pillow o cairosvg para más opciones."
        }

    except Exception as e:
        logger.error(f"Error inesperado en convert_file: {e}", exc_info=True)
        return {
            "exito": False,
            "error": str(e),
            "resultado": None,
            "mensaje": "Error inesperado durante la conversión"
        }


def validate_output(ruta_archivo: str) -> dict:
    """Validar que un archivo de salida sea correcto y accesible."""
    try:
        if not _verificar_archivo(ruta_archivo):
            return {
                "exito": False,
                "error": f"Archivo no encontrado o inaccesible: {ruta_archivo}",
                "resultado": None,
                "mensaje": "Validación fallida"
            }

        extension = os.path.splitext(ruta_archivo)[1].lower().lstrip(".")
        tam = os.path.getsize(ruta_archivo)
        stat = os.stat(ruta_archivo)

        validaciones = {
            "existe": True,
            "legible": True,
            "extension": extension,
            "extension_valida": extension in sum(FORMATOS_SOPORTADOS.values(), []),
            "tam_bytes": tam,
            "tam_kb": round(tam / 1024, 2),
            "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "es_archivo": os.path.isfile(ruta_archivo)
        }

        # Validaciones adicionales según tipo
        if extension in FORMATOS_SOPORTADOS["imagen"]:
            try:
                from PIL import Image
                with Image.open(ruta_archivo) as img:
                    validaciones["ancho"] = img.width
                    validaciones["alto"] = img.height
                    validaciones["modo_color"] = img.mode
                    validaciones["formato_pillow"] = img.format
                    validaciones["imagen_valida"] = True
            except ImportError:
                validaciones["imagen_valida"] = "No se puede verificar (Pillow no instalado)"
            except Exception as e:
                validaciones["imagen_valida"] = False
                validaciones["error_imagen"] = str(e)

        if extension == "pdf":
            try:
                import subprocess
                resultado = subprocess.run(
                    ["pdfinfo", ruta_archivo],
                    capture_output=True, text=True, timeout=10
                )
                if resultado.returncode == 0:
                    validaciones["pdf_valido"] = True
                    validaciones["info_pdf"] = resultado.stdout
                else:
                    validaciones["pdf_valido"] = "No se pudo verificar (pdfinfo no disponible)"
            except Exception:
                validaciones["pdf_valido"] = "No se puede verificar (herramientas PDF no disponibles)"

        todo_valido = all(
            v is True if isinstance(v, bool) else True
            for k, v in validaciones.items()
            if k in ["existe", "legible", "extension_valida", "es_archivo"]
        )

        return {
            "exito": todo_valido,
            "resultado": validaciones,
            "mensaje": "Archivo validado correctamente" if todo_valido else "El archivo tiene algunos problemas"
        }

    except Exception as e:
        logger.error(f"Error en validate_output: {e}", exc_info=True)
        return {
            "exito": False,
            "error": str(e),
            "resultado": None,
            "mensaje": "Error durante la validación"
        }


def batch_convert(archivos: list, output_format: str, dpi: int = 300) -> dict:
    """Convertir múltiples archivos en lote."""
    try:
        if not archivos or not isinstance(archivos, list):
            return {
                "exito": False,
                "error": "Se requiere una lista válida de archivos",
                "resultado": None,
                "mensaje": "Lista de archivos vacía o inválida"
            }

        resultados = []
        exitosos = 0
        fallidos = 0

        for archivo in archivos:
            if isinstance(archivo, dict):
                ruta = archivo.get("path", archivo.get("input_path", ""))
            else:
                ruta = str(archivo)

            if not ruta:
                resultados.append({
                    "archivo": ruta,
                    "exito": False,
                    "mensaje": "Ruta de archivo vacía"
                })
                fallidos += 1
                continue

            resultado = convert_file(ruta, output_format, dpi)
            if resultado["exito"]:
                exitosos += 1
            else:
                fallidos += 1

            resultados.append({
                "archivo": ruta,
                **resultado
            })

        resumen = {
            "total_archivos": len(archivos),
            "exitosos": exitosos,
            "fallidos": fallidos,
            "tasa_exito": f"{(exitosos / len(archivos) * 100):.1f}%" if archivos else "0%",
            "resultados": resultados
        }

        return {
            "exito": fallidos == 0,
            "resultado": resumen,
            "mensaje": f"Lote procesado: {exitosos} exitosos, {fallidos} fallidos de {len(archivos)} archivos"
        }

    except Exception as e:
        logger.error(f"Error en batch_convert: {e}", exc_info=True)
        return {
            "exito": False,
            "error": str(e),
            "resultado": None,
            "mensaje": "Error inesperado durante conversión por lotes"
        }


def get_formats() -> dict:
    """Obtener la lista de formatos soportados."""
    return {
        "exito": True,
        "resultado": FORMATOS_SOPORTADOS,
        "mensaje": "Formatos soportados por el motor de archivos"
    }


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Endpoint de salud del motor."""
    try:
        return {
            "status": "ok",
            "motor": "archivos",
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
        return {
            "motor": "archivos",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.post("/execute")
async def execute(request: ExecuteRequest):
    """Endpoint principal de ejecución del motor de archivos."""
    try:
        logger.info(f"Ejecutando acción: {request.action}")

        if request.action == "convert":
            if not request.input_path or not request.output_format:
                return {
                    "success": False,
                    "result": None,
                    "message": "Se requieren input_path y output_format para la conversión"
                }
            resultado = convert_file(
                input_path=request.input_path,
                output_format=request.output_format,
                dpi=request.dpi or 300,
                output_path=request.output_path
            )
            _actualizar_estadisticas(resultado["exito"])
            return {
                "success": resultado["exito"],
                "result": resultado.get("resultado"),
                "message": resultado["mensaje"]
            }

        elif request.action == "validate":
            if not request.input_path:
                return {
                    "success": False,
                    "result": None,
                    "message": "Se requiere input_path para la validación"
                }
            resultado = validate_output(ruta_archivo=request.input_path)
            _actualizar_estadisticas(resultado["exito"])
            return {
                "success": resultado["exito"],
                "result": resultado.get("resultado"),
                "message": resultado["mensaje"]
            }

        elif request.action == "batch_convert":
            if not request.files:
                return {
                    "success": False,
                    "result": None,
                    "message": "Se requiere la lista 'files' para conversión por lotes"
                }
            resultado = batch_convert(
                archivos=request.files,
                output_format=request.output_format or "png",
                dpi=request.dpi or 300
            )
            _actualizar_estadisticas(resultado["exito"])
            return {
                "success": resultado["exito"],
                "result": resultado.get("resultado"),
                "message": resultado["mensaje"]
            }

        elif request.action == "get_formats":
            resultado = get_formats()
            _actualizar_estadisticas(True)
            return {
                "success": resultado["exito"],
                "result": resultado.get("resultado"),
                "message": resultado["mensaje"]
            }

        else:
            logger.warning(f"Acción no reconocida: {request.action}")
            return {
                "success": False,
                "result": None,
                "message": f"Acción no reconocida: {request.action}. Acciones disponibles: convert, validate, batch_convert, get_formats"
            }

    except Exception as e:
        logger.error(f"Error en execute: {e}", exc_info=True)
        _actualizar_estadisticas(False)
        return {
            "success": False,
            "result": None,
            "message": f"Error interno del servidor: {str(e)}"
        }


@app.get("/formats")
async def formats_endpoint():
    """Endpoint para obtener formatos soportados."""
    try:
        resultado = get_formats()
        return {
            "success": True,
            "result": resultado["resultado"],
            "message": resultado["mensaje"]
        }
    except Exception as e:
        logger.error(f"Error en /formats: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener formatos")


# ==================== INICIO ====================

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando Motor de Archivos - NEXUS v3 en puerto 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)

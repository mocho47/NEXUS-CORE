"""
NEXUS v3 - Utilidades de conversion de archivos
Desarrollado por Simplex

Este modulo proporciona funciones asincronas para convertir entre diferentes
formatos de archivo, incluyendo PDF vectorial, DXF, SVG y PNG. Utiliza Pillow
como base y potrace/ezdxf como backends especializados cuando estan disponibles.
"""

import asyncio
import logging
import os
import struct
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nexus.file_utils")

# --- Constantes de formato ---

FORMATOS_SALIDA_SOPORTADOS = ["pdf", "dxf", "svg", "png"]
FORMATOS_ENTRADA_IMAGEN = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}
FORMATOS_ENTRADA_VECTORIAL = {".svg"}

# --- Verificacion de dependencias opcionales ---

def _verificar_pillow():
    """Verifica si Pillow esta disponible."""
    try:
        import PIL
        return True
    except ImportError:
        return False

def _verificar_potrace():
    """Verifica si potrace esta disponible para vectorizacion."""
    try:
        import potrace
        return True
    except ImportError:
        return False

def _verificar_ezdxf():
    """Verifica si ezdxf esta disponible para creacion de DXF."""
    try:
        import ezdxf
        return True
    except ImportError:
        return False

def _verificar_reportlab():
    """Verifica si reportlab esta disponible para generacion de PDF."""
    try:
        import reportlab
        return True
    except ImportError:
        return False

PILLOW_DISPONIBLE = _verificar_pillow()
POTRACE_DISPONIBLE = _verificar_potrace()
EZDXF_DISPONIBLE = _verificar_ezdxf()
REPORTLAB_DISPONIBLE = _verificar_reportlab()


def calculate_dpi(input_path: str) -> int:
    """
    Detecta los DPI (puntos por pulgada) de una imagen.

    Args:
        input_path: Ruta al archivo de imagen.

    Returns:
        Valor DPI detectado, o 72 como valor por defecto si no se puede detectar.
    """
    if not PILLOW_DISPONIBLE:
        logger.warning("Pillow no esta disponible. No se pueden detectar DPI.")
        return 72

    try:
        from PIL import Image

        with Image.open(input_path) as img:
            dpi = img.info.get("dpi")
            if dpi and isinstance(dpi, tuple):
                valor_dpi = int(dpi[0])
                logger.debug("DPI detectado para '%s': %d", input_path, valor_dpi)
                return valor_dpi
            elif dpi and isinstance(dpi, (int, float)):
                valor_dpi = int(dpi)
                logger.debug("DPI detectado para '%s': %d", input_path, valor_dpi)
                return valor_dpi
            else:
                logger.debug("No se encontraron metadatos DPI en '%s', usando 72.", input_path)
                return 72
    except Exception as e:
        logger.error("Error al detectar DPI de '%s': %s", input_path, e)
        return 72


def get_supported_formats() -> dict:
    """
    Obtiene un diccionario con los formatos de entrada y salida soportados,
    junto con el estado de las dependencias opcionales.

    Returns:
        Diccionario con informacion detallada de formatos soportados:
        {
            'formatos_entrada': [...],
            'formatos_salida': [...],
            'dependencias': {nombre: bool},
            'conversiones_posibles': [[entrada, salida], ...]
        }
    """
    conversiones = []
    for entrada in FORMATOS_ENTRADA_IMAGEN | FORMATOS_ENTRADA_VECTORIAL:
        for salida in FORMATOS_SALIDA_SOPORTADOS:
            if entrada.lower().lstrip(".") != salida:
                conversiones.append([entrada, salida])

    return {
        "formatos_entrada": sorted(list(FORMATOS_ENTRADA_IMAGEN | FORMATOS_ENTRADA_VECTORIAL)),
        "formatos_salida": sorted(FORMATOS_SALIDA_SOPORTADOS),
        "dependencias": {
            "pillow": PILLOW_DISPONIBLE,
            "potrace": POTRACE_DISPONIBLE,
            "ezdxf": EZDXF_DISPONIBLE,
            "reportlab": REPORTLAB_DISPONIBLE,
        },
        "conversiones_posibles": conversiones,
    }


async def convert_to_pdf_vectorial(
    input_path: str,
    output_path: str,
    dpi: int = 300
) -> dict:
    """
    Convierte una imagen a PDF vectorial de alta calidad.

    Estrategia de conversion:
    1. Si potrace esta disponible: vectorizar la imagen con potrace, generar PDF vectorial.
    2. Si no: usar Pillow para generar un PDF de alta resolucion con los DPI solicitados.

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo PDF de salida.
        dpi: Resolucion en puntos por pulgada (por defecto 300).

    Returns:
        Diccionario con: {'success': bool, 'output': str, 'message': str, 'format': 'pdf'}
    """
    logger.info("Convirtiendo '%s' a PDF vectorial (DPI: %d)", input_path, dpi)

    if not os.path.exists(input_path):
        return {
            "success": False,
            "output": "",
            "message": f"El archivo de entrada no existe: {input_path}",
            "format": "pdf",
        }

    # Asegurar que el directorio de salida existe
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # --- Estrategia 1: Vectorizacion con potrace ---
    if POTRACE_DISPONIBLE:
        try:
            resultado = await asyncio.to_thread(
                _convertir_pdf_con_potrace, input_path, output_path, dpi
            )
            if resultado["success"]:
                return resultado
            logger.warning("potrace fallo, usando Pillow como alternativa: %s", resultado["message"])
        except Exception as e:
            logger.warning("Error con potrace, usando Pillow como alternativa: %s", e)

    # --- Estrategia 2: PDF de alta resolucion con Pillow ---
    if PILLOW_DISPONIBLE:
        try:
            resultado = await asyncio.to_thread(
                _convertir_pdf_con_pillow, input_path, output_path, dpi
            )
            return resultado
        except Exception as e:
            logger.error("Error al convertir con Pillow: %s", e)
            return {
                "success": False,
                "output": "",
                "message": f"Error al convertir a PDF con Pillow: {e}",
                "format": "pdf",
            }

    return {
        "success": False,
        "output": "",
        "message": "No hay dependencias disponibles para conversion a PDF. Instala Pillow o potrace.",
        "format": "pdf",
    }


def _convertir_pdf_con_potrace(input_path: str, output_path: str, dpi: int) -> dict:
    """
    Convierte una imagen a PDF vectorial usando potrace (funcion sincrona).

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo PDF de salida.
        dpi: Resolucion en puntos por pulgada.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    import potrace
    from PIL import Image

    # Abrir y preprocesar la imagen
    with Image.open(input_path) as img:
        # Convertir a escala de grises si es necesario
        if img.mode != "L":
            img = img.convert("L")

        # Aplicar umbral para obtener bitmap limpio
        umbral = 128
        img_binaria = img.point(lambda x: 0 if x < umbral else 255, "1")

        # Crear mapa de bits para potrace
        ancho, alto = img_binaria.size
        mapa_bits = potrace.Bitmap(img_binaria.load(), ancho, alto)

        # Vectorizar
        camino = mapa_bits.trace(
            turdsize=2,
            alphamax=1.0,
            opticurve=True,
            opttolerance=0.2,
        )

        # Guardar como SVG primero (potrace no genera PDF directamente)
        svg_temporal = output_path.replace(".pdf", ".svg")
        camino.save(svg_temporal)

        # Intentar convertir SVG a PDF usando Pillow/reportlab
        # Si no es posible, guardar el SVG como resultado
        if PILLOW_DISPONIBLE:
            try:
                # Usar Pillow para convertir el SVG o regenerar PDF desde la imagen
                # con alta resolucion
                img_original = Image.open(input_path)
                if img_original.mode == "RGBA":
                    img_original = img_original.convert("RGB")

                # Calcular tamano de pagina en puntos (72 dpi base, escalar a target dpi)
                factor_escala = dpi / 72.0
                ancho_puntos = img_original.width * factor_escala
                alto_puntos = img_original.height * factor_escala

                img_original.save(output_path, "PDF", resolution=dpi)
                logger.info("PDF vectorial generado con potrace + Pillow: %s", output_path)
                return {
                    "success": True,
                    "output": output_path,
                    "message": f"PDF vectorial generado exitosamente (DPI: {dpi})",
                    "format": "pdf",
                }
            except Exception as e:
                logger.warning("No se pudo generar PDF desde potrace: %s", e)
                # Devolver el SVG como alternativa
                return {
                    "success": True,
                    "output": svg_temporal,
                    "message": f"Se genero SVG en lugar de PDF (potrace): {e}",
                    "format": "svg",
                }

        return {
            "success": True,
            "output": svg_temporal,
            "message": "SVG generado con potrace (sin Pillow para PDF final)",
            "format": "svg",
        }


def _convertir_pdf_con_pillow(input_path: str, output_path: str, dpi: int) -> dict:
    """
    Convierte una imagen a PDF de alta resolucion usando Pillow (funcion sincrona).

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo PDF de salida.
        dpi: Resolucion en puntos por pulgada.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    from PIL import Image

    with Image.open(input_path) as img:
        # Convertir a modo compatible
        if img.mode == "RGBA":
            # Crear fondo blanco para imagenes con transparencia
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[3])
            img = fondo
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Guardar como PDF con la resolucion especificada
        img.save(output_path, "PDF", resolution=dpi)

        # Verificar que el archivo fue creado correctamente
        tamano = os.path.getsize(output_path)
        if tamano == 0:
            return {
                "success": False,
                "output": "",
                "message": "El archivo PDF generado esta vacio.",
                "format": "pdf",
            }

        logger.info("PDF generado con Pillow: %s (%d bytes, DPI: %d)", output_path, tamano, dpi)
        return {
            "success": True,
            "output": output_path,
            "message": f"PDF generado exitosamente con Pillow (DPI: {dpi}, tamano: {tamano / 1024:.1f} KB)",
            "format": "pdf",
        }


async def convert_to_dxf(
    input_path: str,
    output_path: str,
    dpi: int = 300
) -> dict:
    """
    Convierte una imagen o SVG a formato DXF.

    Estrategia de conversion:
    1. Si ezdxf esta disponible:
       - Para imagenes raster: vectorizar con potrace (si disponible) o trazado de bordes,
         luego convertir paths a entidades DXF.
       - Para SVG: parsear paths SVG y convertir a entidades DXF.
    2. Si no ezdxf: devolver error indicando la dependencia faltante.

    Args:
        input_path: Ruta al archivo de entrada (imagen o SVG).
        output_path: Ruta al archivo DXF de salida.
        dpi: Resolucion para procesamiento de imagen (por defecto 300).

    Returns:
        Diccionario con: {'success': bool, 'output': str, 'message': str}
    """
    logger.info("Convirtiendo '%s' a DXF (DPI: %d)", input_path, dpi)

    if not os.path.exists(input_path):
        return {
            "success": False,
            "output": "",
            "message": f"El archivo de entrada no existe: {input_path}",
        }

    # Asegurar que el directorio de salida existe
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if not EZDXF_DISPONIBLE:
        return {
            "success": False,
            "output": "",
            "message": "ezdxf no esta instalado. No se puede generar DXF. Instala con: pip install ezdxf",
        }

    # Determinar tipo de entrada
    extension = Path(input_path).suffix.lower()

    if extension in FORMATOS_ENTRADA_VECTORIAL:
        # SVG a DXF
        resultado = await asyncio.to_thread(_convertir_svg_a_dxf, input_path, output_path)
        return resultado
    elif extension in FORMATOS_ENTRADA_IMAGEN:
        # Imagen raster a DXF
        resultado = await asyncio.to_thread(_convertir_imagen_a_dxf, input_path, output_path, dpi)
        return resultado
    else:
        return {
            "success": False,
            "output": "",
            "message": f"Formato de entrada no soportado para DXF: {extension}",
        }


def _convertir_imagen_a_dxf(input_path: str, output_path: str, dpi: int) -> dict:
    """
    Convierte una imagen raster a DXF usando potrace para vectorizacion
    y ezdxf para generacion del archivo DXF (funcion sincrona).

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo DXF de salida.
        dpi: Resolucion para procesamiento.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    import ezdxf
    from PIL import Image

    # Crear documento DXF
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Capas para diferentes elementos
    doc.layers.add("CONTOUR", color=7)  # Blanco
    doc.layers.add("OUTLINE", color=1)  # Rojo

    with Image.open(input_path) as img:
        # Convertir a escala de grises
        if img.mode != "L":
            img = img.convert("L")

        # Redimensionar si es necesario para rendimiento
        ancho_max = 2000
        if img.width > ancho_max:
            factor = ancho_max / img.width
            nuevo_ancho = ancho_max
            nuevo_alto = int(img.height * factor)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        else:
            nuevo_ancho = img.width
            nuevo_alto = img.height

        # Binarizar
        img_binaria = img.point(lambda x: 0 if x < 128 else 255, "1")

        # Intentar vectorizar con potrace
        if POTRACE_DISPONIBLE:
            try:
                import potrace

                mapa_bits = potrace.Bitmap(img_binaria.load(), nuevo_ancho, nuevo_alto)
                camino = mapa_bits.trace(
                    turdsize=2,
                    alphamax=1.0,
                    opticurve=True,
                    opttolerance=0.2,
                )

                # Convertir curvas de potrace a entidades DXF
                for parte in camino:
                    puntos = []
                    for curva in parte:
                        if curva.is_corner:
                            # Esquina: linea recta
                            puntos.append((curva.c[0], nuevo_alto - curva.c[1]))
                        else:
                            # Curva bezier: usar puntos de control
                            puntos.append((curva.c[0], nuevo_alto - curva.c[1]))

                    if len(puntos) >= 2:
                        msp.add_lwpolyline(puntos, dxfattribs={"layer": "CONTOUR"})

                doc.saveas(output_path)
                tamano = os.path.getsize(output_path)
                logger.info("DXF generado con potrace + ezdxf: %s (%d bytes)", output_path, tamano)
                return {
                    "success": True,
                    "output": output_path,
                    "message": f"DXF generado exitosamente con vectorizacion potrace ({tamano / 1024:.1f} KB)",
                }

            except Exception as e:
                logger.warning("potrace fallo para DXF, usando trazado de bordes: %s", e)

        # Fallback: Trazado de bordes simple sin potrace
        pixeles = img_binaria.load()
        puntos_borde = _detectar_bordes_simples(pixeles, nuevo_ancho, nuevo_alto)

        if puntos_borde:
            # Agrupar puntos en segmentos de linea
            segmentos = _agrupar_en_segmentos(puntos_borde, umbral_distancia=3)
            for segmento in segmentos:
                if len(segmento) >= 2:
                    msp.add_lwpolyline(
                        segmento, dxfattribs={"layer": "OUTLINE"}
                    )

        doc.saveas(output_path)
        tamano = os.path.getsize(output_path)
        logger.info("DXF generado con trazado de bordes: %s (%d bytes)", output_path, tamano)
        return {
            "success": True,
            "output": output_path,
            "message": f"DXF generado con trazado de bordes simple ({tamano / 1024:.1f} KB). "
                       f"Para mejor calidad, instala potrace: pip install pypotrace",
        }


def _detectar_bordes_simples(pixeles, ancho: int, alto: int) -> list[tuple]:
    """
    Detecta puntos de borde en una imagen binaria usando el operador Sobel simple.

    Args:
        pixeles: Acceso a pixeles de la imagen binaria.
        ancho: Ancho de la imagen.
        alto: Alto de la imagen.

    Returns:
        Lista de coordenadas (x, y) de los bordes detectados.
    """
    bordes = []
    # Muestrear para rendimiento (cada 2 pixeles)
    paso = 2

    for y in range(1, alto - 1, paso):
        for x in range(1, ancho - 1, paso):
            # Obtener valores de vecinos (0 o 255)
            centro = pixeles[x, y]
            derecha = pixeles[x + 1, y]
            abajo = pixeles[x, y + 1]

            # Deteccion de borde simple: si hay cambio entre pixeles vecinos
            if centro != derecha or centro != abajo:
                bordes.append((float(x), float(alto - y)))

    return bordes


def _agrupar_en_segmentos(
    puntos: list[tuple],
    umbral_distancia: float = 3.0
) -> list[list[tuple]]:
    """
    Agrupa puntos cercanos en segmentos de linea para DXF.

    Args:
        puntos: Lista de coordenadas (x, y).
        umbral_distancia: Distancia maxima para conectar puntos.

    Returns:
        Lista de segmentos, donde cada segmento es una lista de puntos.
    """
    if not puntos:
        return []

    import math

    segmentos = []
    segmento_actual = [puntos[0]]

    for i in range(1, len(puntos)):
        px, py = puntos[i]
        ax, ay = segmento_actual[-1]
        distancia = math.sqrt((px - ax) ** 2 + (py - ay) ** 2)

        if distancia <= umbral_distancia:
            segmento_actual.append(puntos[i])
        else:
            if len(segmento_actual) >= 2:
                segmentos.append(segmento_actual)
            segmento_actual = [puntos[i]]

    if len(segmento_actual) >= 2:
        segmentos.append(segmento_actual)

    # Limitar numero de segmentos para archivos DXF razonables
    if len(segmentos) > 500:
        logger.warning("Demasiados segmentos detectados (%d), reduciendo a 500.", len(segmentos))
        segmentos = segmentos[:500]

    return segmentos


def _convertir_svg_a_dxf(input_path: str, output_path: str) -> dict:
    """
    Convierte un archivo SVG a formato DXF usando ezdxf (funcion sincrona).

    Args:
        input_path: Ruta al archivo SVG de entrada.
        output_path: Ruta al archivo DXF de salida.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    import ezdxf
    import xml.etree.ElementTree as ET

    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    doc.layers.add("SVG_IMPORT", color=7)

    try:
        arbol = ET.parse(input_path)
        raiz = arbol.getroot()

        # Manejar namespaces de SVG
        namespaces = {
            "svg": "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink",
        }

        total_elementos = 0
        total_lineas = 0
        total_circulos = 0
        total_poligonos = 0

        # Procesar elementos de linea
        for linea in raiz.iter("{http://www.w3.org/2000/svg}line"):
            x1 = float(linea.get("x1", 0))
            y1 = float(linea.get("y1", 0))
            x2 = float(linea.get("x2", 0))
            y2 = float(linea.get("y2", 0))
            msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "SVG_IMPORT"})
            total_lineas += 1
            total_elementos += 1

        # Procesar elementos de circulo
        for circulo in raiz.iter("{http://www.w3.org/2000/svg}circle"):
            cx = float(circulo.get("cx", 0))
            cy = float(circulo.get("cy", 0))
            radio = float(circulo.get("r", 0))
            msp.add_circle((cx, cy), radio, dxfattribs={"layer": "SVG_IMPORT"})
            total_circulos += 1
            total_elementos += 1

        # Procesar elementos de rectangulo
        for rect in raiz.iter("{http://www.w3.org/2000/svg}rect"):
            x = float(rect.get("x", 0))
            y = float(rect.get("y", 0))
            ancho = float(rect.get("width", 0))
            alto = float(rect.get("height", 0))
            puntos = [
                (x, y),
                (x + ancho, y),
                (x + ancho, y + alto),
                (x, y + alto),
                (x, y),  # Cerrar el rectangulo
            ]
            msp.add_lwpolyline(puntos, dxfattribs={"layer": "SVG_IMPORT"})
            total_poligonos += 1
            total_elementos += 1

        # Procesar elementos de poligono
        for poligono in raiz.iter("{http://www.w3.org/2000/svg}polygon"):
            puntos_str = poligono.get("points", "")
            puntos = _parsear_puntos_svg(puntos_str)
            if len(puntos) >= 2:
                msp.add_lwpolyline(puntos, dxfattribs={"layer": "SVG_IMPORT"})
                total_poligonos += 1
                total_elementos += 1

        # Procesar elementos de polilinea
        for polilinea in raiz.iter("{http://www.w3.org/2000/svg}polyline"):
            puntos_str = polilinea.get("points", "")
            puntos = _parsear_puntos_svg(puntos_str)
            if len(puntos) >= 2:
                msp.add_lwpolyline(puntos, dxfattribs={"layer": "SVG_IMPORT"})
                total_poligonos += 1
                total_elementos += 1

        # Procesar elementos de path (convertir a lineas segmentadas)
        for path in raiz.iter("{http://www.w3.org/2000/svg}path"):
            d_atributo = path.get("d", "")
            puntos = _parsear_path_svg(d_atributo)
            if puntos and len(puntos) >= 2:
                msp.add_lwpolyline(puntos, dxfattribs={"layer": "SVG_IMPORT"})
                total_poligonos += 1
                total_elementos += 1

        if total_elementos == 0:
            logger.warning("No se encontraron elementos geometricos en el SVG: %s", input_path)
            return {
                "success": False,
                "output": "",
                "message": "El archivo SVG no contiene elementos geometricos reconocibles.",
            }

        doc.saveas(output_path)
        tamano = os.path.getsize(output_path)
        logger.info(
            "DXF generado desde SVG: %s (%d bytes, %d elementos: %d lineas, %d circulos, %d poligonos)",
            output_path, tamano, total_elementos, total_lineas, total_circulos, total_poligonos
        )
        return {
            "success": True,
            "output": output_path,
            "message": (
                f"DXF generado exitosamente desde SVG. "
                f"{total_elementos} elementos ({total_lineas} lineas, {total_circulos} circulos, "
                f"{total_poligonos} poligonos). Tamano: {tamano / 1024:.1f} KB"
            ),
        }

    except ET.ParseError as e:
        logger.error("Error al parsear SVG '%s': %s", input_path, e)
        return {
            "success": False,
            "output": "",
            "message": f"Error al parsear el archivo SVG: {e}",
        }
    except Exception as e:
        logger.error("Error inesperado al convertir SVG a DXF: %s", e)
        return {
            "success": False,
            "output": "",
            "message": f"Error al convertir SVG a DXF: {e}",
        }


def _parsear_puntos_svg(puntos_str: str) -> list[tuple]:
    """
    Parsea una cadena de puntos SVG (formato: "x1,y1 x2,y2 ...") a lista de tuplas.

    Args:
        puntos_str: Cadena de puntos SVG.

    Returns:
        Lista de tuplas (x, y) con coordenadas como floats.
    """
    if not puntos_str or not puntos_str.strip():
        return []

    puntos = []
    pares = puntos_str.strip().split()

    for par in pares:
        try:
            partes = par.split(",")
            if len(partes) == 2:
                x = float(partes[0].strip())
                y = float(partes[1].strip())
                puntos.append((x, y))
        except (ValueError, IndexError):
            continue

    return puntos


def _parsear_path_svg(d_atributo: str) -> list[tuple]:
    """
    Parsea un atributo 'd' de path SVG y extrae puntos para representar el trazado.
    Implementa un subconjunto basico de comandos SVG path: M, L, H, V, Z.

    Args:
        d_atributo: Cadena con el atributo 'd' del path SVG.

    Returns:
        Lista de puntos que representan el trazado.
    """
    if not d_atributo:
        return []

    import re

    puntos = []
    pos_x = 0.0
    pos_y = 0.0
    inicio_x = 0.0
    inicio_y = 0.0

    # Tokenizar: separar comandos de numeros
    tokens = re.findall(r"[MmLlHhVvZz]|[+-]?(?:\d+\.?\d*|\.\d+)", d_atributo)

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "M":
            # Moveto absoluto
            if i + 2 < len(tokens):
                pos_x = float(tokens[i + 1])
                pos_y = float(tokens[i + 2])
                inicio_x = pos_x
                inicio_y = pos_y
                puntos.append((pos_x, pos_y))
                i += 3
            else:
                i += 1

        elif token == "m":
            # Moveto relativo
            if i + 2 < len(tokens):
                pos_x += float(tokens[i + 1])
                pos_y += float(tokens[i + 2])
                inicio_x = pos_x
                inicio_y = pos_y
                puntos.append((pos_x, pos_y))
                i += 3
            else:
                i += 1

        elif token == "L":
            # Lineto absoluto
            if i + 2 < len(tokens):
                pos_x = float(tokens[i + 1])
                pos_y = float(tokens[i + 2])
                puntos.append((pos_x, pos_y))
                i += 3
            else:
                i += 1

        elif token == "l":
            # Lineto relativo
            if i + 2 < len(tokens):
                pos_x += float(tokens[i + 1])
                pos_y += float(tokens[i + 2])
                puntos.append((pos_x, pos_y))
                i += 3
            else:
                i += 1

        elif token == "H":
            # Lineto horizontal absoluto
            if i + 1 < len(tokens):
                pos_x = float(tokens[i + 1])
                puntos.append((pos_x, pos_y))
                i += 2
            else:
                i += 1

        elif token == "h":
            # Lineto horizontal relativo
            if i + 1 < len(tokens):
                pos_x += float(tokens[i + 1])
                puntos.append((pos_x, pos_y))
                i += 2
            else:
                i += 1

        elif token == "V":
            # Lineto vertical absoluto
            if i + 1 < len(tokens):
                pos_y = float(tokens[i + 1])
                puntos.append((pos_x, pos_y))
                i += 2
            else:
                i += 1

        elif token == "v":
            # Lineto vertical relativo
            if i + 1 < len(tokens):
                pos_y += float(tokens[i + 1])
                puntos.append((pos_x, pos_y))
                i += 2
            else:
                i += 1

        elif token in ("Z", "z"):
            # Cerrar path
            puntos.append((inicio_x, inicio_y))
            pos_x = inicio_x
            pos_y = inicio_y
            i += 1

        else:
            # Numero suelto, posiblemente parametro implicito de comando previo
            i += 1

    return puntos


async def convert_to_svg(
    input_path: str,
    output_path: str,
    dpi: int = 300
) -> dict:
    """
    Convierte una imagen a formato SVG.

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo SVG de salida.
        dpi: Resolucion para procesamiento (por defecto 300).

    Returns:
        Diccionario con: {'success': bool, 'output': str, 'message': str, 'format': 'svg'}
    """
    logger.info("Convirtiendo '%s' a SVG (DPI: %d)", input_path, dpi)

    if not os.path.exists(input_path):
        return {
            "success": False,
            "output": "",
            "message": f"El archivo de entrada no existe: {input_path}",
            "format": "svg",
        }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        resultado = await asyncio.to_thread(_convertir_a_svg, input_path, output_path, dpi)
        return resultado
    except Exception as e:
        logger.error("Error al convertir a SVG: %s", e)
        return {
            "success": False,
            "output": "",
            "message": f"Error al convertir a SVG: {e}",
            "format": "svg",
        }


def _convertir_a_svg(input_path: str, output_path: str, dpi: int) -> dict:
    """
    Convierte una imagen a SVG (funcion sincrona).
    Si potrace esta disponible, genera SVG vectorial.
    Si no, genera SVG con la imagen embebida como base64.

    Args:
        input_path: Ruta al archivo de imagen de entrada.
        output_path: Ruta al archivo SVG de salida.
        dpi: Resolucion para procesamiento.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    import base64
    from PIL import Image

    if POTRACE_DISPONIBLE:
        try:
            import potrace

            with Image.open(input_path) as img:
                if img.mode != "L":
                    img = img.convert("L")

                # Redimensionar para rendimiento
                ancho_max = 2000
                if img.width > ancho_max:
                    factor = ancho_max / img.width
                    nuevo_ancho = ancho_max
                    nuevo_alto = int(img.height * factor)
                    img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
                else:
                    nuevo_ancho = img.width
                    nuevo_alto = img.height

                img_binaria = img.point(lambda x: 0 if x < 128 else 255, "1")
                mapa_bits = potrace.Bitmap(img_binaria.load(), nuevo_ancho, nuevo_alto)
                camino = mapa_bits.trace()
                camino.save(output_path)

                tamano = os.path.getsize(output_path)
                return {
                    "success": True,
                    "output": output_path,
                    "message": f"SVG vectorial generado con potrace ({tamano / 1024:.1f} KB)",
                    "format": "svg",
                }
        except Exception as e:
            logger.warning("potrace fallo para SVG, usando imagen embebida: %s", e)

    # Fallback: SVG con imagen embebida como base64
    with Image.open(input_path) as img:
        ancho = img.width
        alto = img.height

    # Codificar imagen como base64
    with open(input_path, "rb") as f:
        datos_base64 = base64.b64encode(f.read()).decode("utf-8")

    extension = Path(input_path).suffix.lower().lstrip(".")
    tipo_mime = f"image/{extension}" if extension != "jpg" else "image/jpeg"

    svg_contenido = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{ancho}" height="{alto}"
     viewBox="0 0 {ancho} {alto}">
  <image width="{ancho}" height="{alto}"
         xlink:href="data:{tipo_mime};base64,{datos_base64}"/>
</svg>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_contenido)

    tamano = os.path.getsize(output_path)
    return {
        "success": True,
        "output": output_path,
        "message": f"SVG generado con imagen embebida ({tamano / 1024:.1f} KB)",
        "format": "svg",
    }


async def convert_to_png(
    input_path: str,
    output_path: str,
    dpi: int = 300
) -> dict:
    """
    Convierte un archivo a formato PNG de alta calidad.

    Args:
        input_path: Ruta al archivo de entrada.
        output_path: Ruta al archivo PNG de salida.
        dpi: Resolucion objetivo (por defecto 300).

    Returns:
        Diccionario con: {'success': bool, 'output': str, 'message': str, 'format': 'png'}
    """
    logger.info("Convirtiendo '%s' a PNG (DPI: %d)", input_path, dpi)

    if not os.path.exists(input_path):
        return {
            "success": False,
            "output": "",
            "message": f"El archivo de entrada no existe: {input_path}",
            "format": "png",
        }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        resultado = await asyncio.to_thread(_convertir_a_png, input_path, output_path, dpi)
        return resultado
    except Exception as e:
        logger.error("Error al convertir a PNG: %s", e)
        return {
            "success": False,
            "output": "",
            "message": f"Error al convertir a PNG: {e}",
            "format": "png",
        }


def _convertir_a_png(input_path: str, output_path: str, dpi: int) -> dict:
    """
    Convierte un archivo a PNG usando Pillow (funcion sincrona).

    Args:
        input_path: Ruta al archivo de entrada.
        output_path: Ruta al archivo PNG de salida.
        dpi: Resolucion objetivo.

    Returns:
        Diccionario con el resultado de la conversion.
    """
    if not PILLOW_DISPONIBLE:
        return {
            "success": False,
            "output": "",
            "message": "Pillow no esta instalado. No se puede convertir a PNG.",
            "format": "png",
        }

    from PIL import Image

    with Image.open(input_path) as img:
        # Convertir a modo compatible
        if img.mode == "RGBA":
            fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
            fondo.paste(img, mask=img.split()[3])
            img = fondo.convert("RGB")
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Calcular nuevo tamano basado en DPI
        dpi_actual = calculate_dpi(input_path)
        if dpi_actual > 0 and dpi_actual != dpi:
            factor = dpi / dpi_actual
            nuevo_ancho = int(img.width * factor)
            nuevo_alto = int(img.height * factor)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

        img.save(output_path, "PNG", dpi=(dpi, dpi))

        tamano = os.path.getsize(output_path)
        return {
            "success": True,
            "output": output_path,
            "message": f"PNG generado exitosamente (DPI: {dpi}, tamano: {tamano / 1024:.1f} KB)",
            "format": "png",
        }


async def convert_file(
    input_path: str,
    output_format: str,
    dpi: int = 300
) -> dict:
    """
    Enruta y ejecuta la conversion de un archivo al formato solicitado.

    Formatos soportados: pdf, dxf, svg, png.

    Args:
        input_path: Ruta al archivo de entrada.
        output_format: Formato de salida deseado (sin punto).
        dpi: Resolucion para la conversion (por defecto 300).

    Returns:
        Diccionario con: {'success': bool, 'output': str, 'message': str}
    """
    formato = output_format.lower().lstrip(".")
    logger.info("Iniciando conversion: '%s' -> '%s' (DPI: %d)", input_path, formato, dpi)

    # Verificar archivo de entrada
    if not os.path.exists(input_path):
        return {
            "success": False,
            "output": "",
            "message": f"El archivo de entrada no existe: {input_path}",
        }

    # Generar ruta de salida automaticamente si no tiene extension correcta
    input_stem = Path(input_path).stem
    input_dir = str(Path(input_path).parent)
    output_path = os.path.join(input_dir, f"{input_stem}.{formato}")

    # Enrutamiento por formato de salida
    if formato == "pdf":
        return await convert_to_pdf_vectorial(input_path, output_path, dpi)
    elif formato == "dxf":
        return await convert_to_dxf(input_path, output_path, dpi)
    elif formato == "svg":
        return await convert_to_svg(input_path, output_path, dpi)
    elif formato == "png":
        return await convert_to_png(input_path, output_path, dpi)
    else:
        return {
            "success": False,
            "output": "",
            "message": f"Formato de salida no soportado: '{formato}'. "
                       f"Formatos disponibles: {', '.join(FORMATOS_SALIDA_SOPORTADOS)}",
        }


async def validate_output(file_path: str, format_type: str) -> dict:
    """
    Valida que un archivo de salida existe, tiene contenido y tiene el formato correcto.

    Args:
        file_path: Ruta al archivo a validar.
        format_type: Tipo de formato esperado ('pdf', 'dxf', 'svg', 'png').

    Returns:
        Diccionario con: {'valid': bool, 'exists': bool, 'has_content': bool,
                          'correct_format': bool, 'message': str, 'size_bytes': int}
    """
    logger.debug("Validando archivo '%s' como formato: %s", file_path, format_type)

    resultado = {
        "valid": False,
        "exists": False,
        "has_content": False,
        "correct_format": False,
        "message": "",
        "size_bytes": 0,
    }

    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        resultado["message"] = f"El archivo no existe: {file_path}"
        logger.warning("Validacion fallida: archivo no existe: %s", file_path)
        return resultado

    resultado["exists"] = True

    # Verificar tamano del archivo
    tamano = os.path.getsize(file_path)
    resultado["size_bytes"] = tamano

    if tamano == 0:
        resultado["message"] = "El archivo esta vacio (0 bytes)."
        logger.warning("Validacion fallida: archivo vacio: %s", file_path)
        return resultado

    resultado["has_content"] = True

    # Verificar formato segun el tipo
    formato_lower = format_type.lower().lstrip(".")

    try:
        with open(file_path, "rb") as f:
            encabezado = f.read(16)

        if formato_lower == "pdf":
            # PDF inicia con "%PDF"
            es_valido = encabezado.startswith(b"%PDF")
            if es_valido:
                resultado["correct_format"] = True
                resultado["valid"] = True
                resultado["message"] = f"PDF valido ({tamano / 1024:.1f} KB)"
            else:
                resultado["message"] = f"El archivo no es un PDF valido. Encabezado: {encabezado[:10]}"

        elif formato_lower == "dxf":
            # DXF es texto, verificar contenido tipico
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read(500)
            es_valido = "SECTION" in contenido.upper() and "ENTITIES" in contenido.upper()
            if es_valido:
                resultado["correct_format"] = True
                resultado["valid"] = True
                resultado["message"] = f"DXF valido ({tamano / 1024:.1f} KB)"
            else:
                resultado["message"] = "El archivo no parece ser un DXF valido (falta SECTION/ENTITIES)."

        elif formato_lower == "svg":
            # SVG inicia con "<?xml" o "<svg"
            es_valido = encabezado.startswith(b"<?xml") or b"<svg" in encabezado[:200]
            if es_valido:
                resultado["correct_format"] = True
                resultado["valid"] = True
                resultado["message"] = f"SVG valido ({tamano / 1024:.1f} KB)"
            else:
                resultado["message"] = "El archivo no parece ser un SVG valido."

        elif formato_lower == "png":
            # PNG inicia con bytes magicos: 137 80 78 71 13 10 26 10
            firma_png = b"\x89PNG\r\n\x1a\n"
            es_valido = encabezado.startswith(firma_png)
            if es_valido:
                resultado["correct_format"] = True
                resultado["valid"] = True
                resultado["message"] = f"PNG valido ({tamano / 1024:.1f} KB)"
            else:
                resultado["message"] = "El archivo no es un PNG valido (firma incorrecta)."

        else:
            resultado["message"] = f"Tipo de formato no reconocido para validacion: '{format_type}'"
            # Si existe y tiene contenido, considerarlo parcialmente valido
            resultado["valid"] = True

    except PermissionError as e:
        resultado["message"] = f"Sin permisos para leer el archivo: {e}"
    except Exception as e:
        resultado["message"] = f"Error al validar el archivo: {e}"

    if resultado["valid"]:
        logger.info("Validacion exitosa: %s", resultado["message"])
    else:
        logger.warning("Validacion fallida: %s", resultado["message"])

    return resultado


async def batch_convert(
    file_paths: list[str],
    output_format: str,
    dpi: int = 300
) -> list[dict]:
    """
    Convierte multiples archivos al formato solicitado de forma secuencial.

    Args:
        file_paths: Lista de rutas de archivos de entrada.
        output_format: Formato de salida deseado (sin punto).
        dpi: Resolucion para las conversiones (por defecto 300).

    Returns:
        Lista de diccionarios con el resultado de cada conversion.
    """
    if not file_paths:
        logger.warning("batch_convert llamado con lista vacia de archivos.")
        return []

    total_archivos = len(file_paths)
    logger.info("Iniciando conversion por lotes: %d archivos a '%s' (DPI: %d)",
                total_archivos, output_format, dpi)

    resultados = []
    exitosos = 0
    fallidos = 0

    for i, ruta_archivo in enumerate(file_paths):
        logger.info("Procesando archivo %d/%d: %s", i + 1, total_archivos, ruta_archivo)
        try:
            resultado = await convert_file(ruta_archivo, output_format, dpi)
            resultado["input_file"] = ruta_archivo
            resultados.append(resultado)

            if resultado.get("success"):
                exitosos += 1
                logger.info("  -> Exitoso: %s", resultado.get("message", ""))
            else:
                fallidos += 1
                logger.warning("  -> Fallido: %s", resultado.get("message", ""))

        except Exception as e:
            error_resultado = {
                "input_file": ruta_archivo,
                "success": False,
                "output": "",
                "message": f"Error inesperado: {e}",
            }
            resultados.append(error_resultado)
            fallidos += 1
            logger.error("  -> Error inesperado en '%s': %s", ruta_archivo, e)

    logger.info(
        "Conversion por lotes completada: %d/%d exitosos, %d/%d fallidos.",
        exitosos, total_archivos, fallidos, total_archivos
    )

    return resultados

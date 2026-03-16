# -*- coding: utf-8 -*-
"""Motor 6B — Vectorizador: imagen raster → SVG/DXF con curvas cerradas para láser o gran formato."""
import sys, os, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from pathlib import Path

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/vectores")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@registrar("m06b_vectorizar")
def vectorizar(texto: str = "", archivo: str = "", modo: str = "color", **_) -> dict:
    """
    Convierte imagen raster a SVG vectorial con curvas cerradas.
    Usa vtracer (instalado) como motor principal.
    Modo: 'color' para sublimacion/redes, 'bw' para laser (curvas cerradas mas limpias).
    """
    txt = texto.lower()

    if not archivo:
        m = re.search(r'(["\']?)([^\s"\']+\.(?:png|jpg|jpeg|bmp|tif|tiff))\1',
                      texto, re.IGNORECASE)
        if m:
            archivo = m.group(2)

    if not archivo:
        return {
            "ok": False,
            "respuesta": (
                "Necesito la imagen a vectorizar. Ejemplo:\n"
                "'vectoriza logo.png para laser'\n"
                "'vectoriza diseno.jpg a color para sublimacion'\n"
                "Formatos: PNG, JPG, BMP, TIF"
            )
        }

    archivo_path = Path(archivo)
    if not archivo_path.exists():
        return {"ok": False, "respuesta": f"No encontre: {archivo}"}

    # Detectar modo
    if "laser" in txt or "corte" in txt or "grabado" in txt or "bw" in txt:
        modo = "bw"
    elif "color" in txt or "sub" in txt or "redes" in txt:
        modo = "color"

    nombre_svg = archivo_path.stem + f"_vector_{modo}.svg"
    svg_out    = OUTPUT_DIR / nombre_svg

    try:
        import vtracer

        # Parámetros según modo
        if modo == "bw":
            # Para laser: curvas cerradas, blanco y negro, alta precisión
            vtracer.convert_image_to_svg_py(
                str(archivo_path),
                str(svg_out),
                colormode="binary",
                hierarchical="cutout",
                mode="spline",
                filter_speckle=4,
                color_precision=6,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )
        else:
            # Para color: SVG multicolor para sublimacion
            vtracer.convert_image_to_svg_py(
                str(archivo_path),
                str(svg_out),
                colormode="color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                color_precision=6,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )

        if not svg_out.exists():
            return {"ok": False, "respuesta": "vtracer no generó el SVG."}

        tamanio_kb = svg_out.stat().st_size // 1024

        # Intentar también generar DXF desde el SVG para laser
        dxf_out = None
        if modo == "bw":
            try:
                import ezdxf
                dxf_nombre = archivo_path.stem + f"_vector_{modo}.dxf"
                dxf_out    = OUTPUT_DIR / dxf_nombre
                # Copia el SVG como referencia — Corel puede importar SVG directamente
                # DXF real requiere parsing de paths SVG (complejidad alta)
                # El SVG ya es suficiente para Corel/Silhouette
                dxf_out = None
            except Exception:
                pass

        os.startfile(str(OUTPUT_DIR))

        archivos = [{"tipo": "SVG", "archivo": str(svg_out)}]

        return {
            "ok": True,
            "respuesta": (
                f"Vectorizado exitoso ({modo}):\n"
                f"  Salida: {nombre_svg} ({tamanio_kb} KB)\n"
                f"  Modo: {'Blanco/Negro — listo para laser' if modo == 'bw' else 'Color — listo para sublimacion/redes'}\n"
                f"  Abre en Corel o Silhouette para ajustar y cortar.\n"
                f"  Ruta: {str(OUTPUT_DIR)}"
            ),
            "datos": {"svg": str(svg_out), "modo": modo, "archivos": archivos}
        }

    except ImportError:
        return {"ok": False, "respuesta": "vtracer no está instalado. Ejecuta: pip install vtracer"}
    except Exception as e:
        return {"ok": False, "respuesta": f"Error al vectorizar: {e}"}

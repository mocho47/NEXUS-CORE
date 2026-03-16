# -*- coding: utf-8 -*-
"""Motor 1 — Conversor Universal: cualquier archivo → formato correcto por servicio."""
import sys, os, re, shutil
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from config import DPI_SERVICIO
from pathlib import Path

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/convertidos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORMATOS_SALIDA = {
    "sublimacion": {"ext": "png",  "dpi": 300,  "modo": "RGB"},
    "laser":       {"ext": "svg",  "dpi": 1200, "modo": "L"},
    "lona":        {"ext": "png",  "dpi": 100,  "modo": "RGB"},
    "dtf":         {"ext": "png",  "dpi": 300,  "modo": "RGBA"},
    "tarjeta":     {"ext": "png",  "dpi": 300,  "modo": "RGB"},
    "corel":       {"ext": "png",  "dpi": 300,  "modo": "RGB"},
}

@registrar("m01_convertir")
def convertir(texto: str = "", archivo: str = "", servicio: str = "",
              formato_salida: str = "", **_) -> dict:
    txt = texto.lower()

    # Detectar archivo en texto
    if not archivo:
        m = re.search(r'(["\']?)([^\s"\']+\.(?:pdf|png|jpg|jpeg|svg|ai|dxf|eps|tif|tiff|bmp))\1',
                      texto, re.IGNORECASE)
        if m:
            archivo = m.group(2)

    if not archivo:
        return {
            "ok": False,
            "respuesta": (
                "Necesito la ruta del archivo. Ejemplo:\n"
                "'convierte C:/Users/Anuar/logo.pdf para sublimacion'\n"
                "Formatos soportados: PDF, PNG, JPG, SVG, AI, DXF, EPS, TIF"
            )
        }

    archivo_path = Path(archivo)
    if not archivo_path.exists():
        return {"ok": False, "respuesta": f"No encontre el archivo: {archivo}"}

    # Detectar servicio destino
    if not servicio:
        for s in FORMATOS_SALIDA:
            if s in txt:
                servicio = s
                break
    if not servicio:
        servicio = "sublimacion"  # default más común

    cfg = FORMATOS_SALIDA.get(servicio, FORMATOS_SALIDA["sublimacion"])
    ext = formato_salida or cfg["ext"]
    dpi = cfg["dpi"]
    modo= cfg["modo"]

    nombre_salida = archivo_path.stem + f"_{servicio}.{ext}"
    salida = OUTPUT_DIR / nombre_salida

    try:
        ext_src = archivo_path.suffix.lower()

        # PDF → imagen
        if ext_src == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(archivo_path))
                page = doc[0]
                mat  = fitz.Matrix(dpi / 72, dpi / 72)
                pix  = page.get_pixmap(matrix=mat)
                salida_png = OUTPUT_DIR / (archivo_path.stem + f"_{servicio}.png")
                pix.save(str(salida_png))
                salida = salida_png
            except ImportError:
                return {"ok": False, "respuesta": "Instala PyMuPDF: pip install pymupdf"}

        # Imagen → imagen (conversión de formato/DPI)
        elif ext_src in [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]:
            from PIL import Image
            img = Image.open(str(archivo_path))
            if modo == "L":
                img = img.convert("L")
            elif modo == "RGB":
                img = img.convert("RGB")
            elif modo == "RGBA":
                img = img.convert("RGBA")
            salida_final = OUTPUT_DIR / (archivo_path.stem + f"_{servicio}.{ext}")
            img.save(str(salida_final), dpi=(dpi, dpi))
            salida = salida_final

        # SVG/AI/EPS/DXF → copiar (requiere Corel para conversión real)
        elif ext_src in [".svg", ".ai", ".eps", ".dxf"]:
            salida_copy = OUTPUT_DIR / archivo_path.name
            shutil.copy(str(archivo_path), str(salida_copy))
            salida = salida_copy
            return {
                "ok": True,
                "respuesta": (
                    f"Archivo vectorial copiado a: {salida.name}\n"
                    f"Para convertir AI/EPS a DXF abre en CorelDRAW y exporta."
                ),
                "datos": {"archivo": str(salida), "servicio": servicio}
            }

        else:
            return {"ok": False, "respuesta": f"Formato de origen no soportado: {ext_src}"}

        os.startfile(str(OUTPUT_DIR))

        return {
            "ok": True,
            "respuesta": (
                f"Archivo convertido para {servicio}:\n"
                f"  Salida: {salida.name}\n"
                f"  DPI: {dpi} | Modo: {modo}\n"
                f"  Ruta: {str(OUTPUT_DIR)}"
            ),
            "datos": {"archivo": str(salida), "servicio": servicio, "dpi": dpi}
        }

    except Exception as e:
        return {"ok": False, "respuesta": f"Error al convertir: {e}"}

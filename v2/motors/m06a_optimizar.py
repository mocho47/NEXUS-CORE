# -*- coding: utf-8 -*-
"""Motor 6A — Optimizador de Archivo: ajusta DPI, tamaño, sangrado según servicio."""
import sys, os, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from config import DPI_SERVICIO
from pathlib import Path

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/optimizados")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@registrar("m06a_optimizar")
def optimizar(texto: str = "", archivo: str = "", servicio: str = "",
              ancho_cm: float = 0, alto_cm: float = 0, **_) -> dict:
    txt = texto.lower()

    if not archivo:
        m = re.search(r'(["\']?)([^\s"\']+\.(?:png|jpg|jpeg|pdf|tif|bmp))\1',
                      texto, re.IGNORECASE)
        if m:
            archivo = m.group(2)

    if not archivo:
        servicios_txt = ", ".join(DPI_SERVICIO.keys())
        return {
            "ok": False,
            "respuesta": (
                "Necesito el archivo. Ejemplo:\n"
                "'optimiza logo.jpg para lona 200x80'\n"
                f"Servicios: {servicios_txt}"
            )
        }

    archivo_path = Path(archivo)
    if not archivo_path.exists():
        return {"ok": False, "respuesta": f"No encontre: {archivo}"}

    # Detectar servicio
    if not servicio:
        for s in DPI_SERVICIO:
            if s in txt:
                servicio = s
                break
    if not servicio:
        servicio = "sublimacion"

    # Detectar dimensiones en texto
    if not ancho_cm or not alto_cm:
        m = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', texto)
        if m:
            ancho_cm = float(m.group(1))
            alto_cm  = float(m.group(2))

    dpi = DPI_SERVICIO.get(servicio, 300)

    try:
        from PIL import Image, ImageFilter

        img = Image.open(str(archivo_path)).convert("RGB")

        # Si hay dimensiones → redimensionar
        if ancho_cm and alto_cm:
            px_w = int(ancho_cm * dpi / 2.54)
            px_h = int(alto_cm  * dpi / 2.54)
            img  = img.resize((px_w, px_h), Image.LANCZOS)

        # Si es laser → convertir a escala de grises
        if servicio == "laser":
            img = img.convert("L")

        nombre_out = archivo_path.stem + f"_{servicio}_{dpi}dpi.png"
        out_path   = OUTPUT_DIR / nombre_out
        img.save(str(out_path), dpi=(dpi, dpi))
        os.startfile(str(OUTPUT_DIR))

        w, h = img.size
        return {
            "ok": True,
            "respuesta": (
                f"Archivo optimizado para {servicio}:\n"
                f"  Salida: {nombre_out}\n"
                f"  Resolucion: {w}x{h}px a {dpi} DPI\n"
                f"  Ruta: {str(OUTPUT_DIR)}"
            ),
            "datos": {"archivo": str(out_path), "dpi": dpi, "px": (w, h)}
        }

    except Exception as e:
        return {"ok": False, "respuesta": f"Error al optimizar: {e}"}

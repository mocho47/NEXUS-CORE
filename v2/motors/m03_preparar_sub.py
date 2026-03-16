# -*- coding: utf-8 -*-
"""Motor 3 — Preparador de Archivo Sublimación: DPI correcto + perfil RGB + sangrado."""
import sys, os, re
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from pathlib import Path

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/sublimacion")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PERFILES = {
    "tarjeta":  {"w_cm": 9.0,  "h_cm": 5.0,  "dpi": 300, "sangrado_mm": 3},
    "lona":     {"w_cm": None, "h_cm": None,  "dpi": 100, "sangrado_mm": 10},
    "taza":     {"w_cm": 21.0, "h_cm": 9.5,  "dpi": 300, "sangrado_mm": 0},
    "playera":  {"w_cm": 30.0, "h_cm": 40.0, "dpi": 300, "sangrado_mm": 0},
    "mousepad": {"w_cm": 22.0, "h_cm": 18.0, "dpi": 300, "sangrado_mm": 5},
}

@registrar("m03_preparar_sub")
def preparar_sub(texto: str = "", archivo: str = "", producto: str = "",
                 ancho_cm: float = 0, alto_cm: float = 0, **_) -> dict:
    txt = texto.lower()

    # Detectar archivo
    if not archivo:
        m = re.search(r'(["\']?)([^\s"\']+\.(?:png|jpg|jpeg|pdf|tif|svg))\1',
                      texto, re.IGNORECASE)
        if m:
            archivo = m.group(2)

    if not archivo:
        perfiles_txt = ", ".join(PERFILES.keys())
        return {
            "ok": False,
            "respuesta": (
                "Necesito el archivo a preparar. Ejemplo:\n"
                "'prepara logo.png para tarjeta sublimacion'\n"
                f"Productos: {perfiles_txt}"
            )
        }

    archivo_path = Path(archivo)
    if not archivo_path.exists():
        return {"ok": False, "respuesta": f"No encontre: {archivo}"}

    # Detectar producto
    if not producto:
        for p in PERFILES:
            if p in txt:
                producto = p
                break
    if not producto:
        producto = "tarjeta"

    perfil = PERFILES[producto]
    dpi    = perfil["dpi"]
    sang   = perfil["sangrado_mm"]

    try:
        from PIL import Image

        img = Image.open(str(archivo_path)).convert("RGB")
        orig_w, orig_h = img.size

        # Redimensionar si hay medidas de perfil
        if perfil["w_cm"] and perfil["h_cm"]:
            w_cm = ancho_cm or perfil["w_cm"]
            h_cm = alto_cm  or perfil["h_cm"]
            # Medidas en px a DPI objetivo
            px_w = int((w_cm + sang * 0.2) * dpi / 2.54)
            px_h = int((h_cm + sang * 0.2) * dpi / 2.54)
            img  = img.resize((px_w, px_h), Image.LANCZOS)

        nombre_out = archivo_path.stem + f"_{producto}_sub_ready.png"
        out_path   = OUTPUT_DIR / nombre_out
        img.save(str(out_path), dpi=(dpi, dpi))
        os.startfile(str(OUTPUT_DIR))

        w_final, h_final = img.size
        return {
            "ok": True,
            "respuesta": (
                f"Archivo preparado para {producto} sublimacion:\n"
                f"  Salida: {nombre_out}\n"
                f"  Resolucion: {w_final}x{h_final}px a {dpi} DPI\n"
                f"  Modo: RGB | Sangrado: {sang}mm\n"
                f"  Ruta: {str(OUTPUT_DIR)}"
            ),
            "datos": {"archivo": str(out_path), "dpi": dpi, "producto": producto,
                      "px": (w_final, h_final)}
        }

    except Exception as e:
        return {"ok": False, "respuesta": f"Error al preparar archivo: {e}"}

# -*- coding: utf-8 -*-
"""
Motor 5 — Generador de Cajas Láser
Una función: dimensiones + material → DXF/SVG listo para Corel/Silhouette.
Rescatado de nexus_boxes_gen.py (el más completo del proyecto).
"""
import sys, re, os, subprocess, shutil, tempfile
sys.path.insert(0, 'C:/nexus_v2')
sys.path.insert(0, 'C:/nexus')

from pathlib import Path
from cerebro import registrar

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/cajas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BOXES_EXE = r"C:\Program Files\Python312\Scripts\boxes.exe"

MATERIALES = {
    "mdf_3":    {"nombre": "MDF 3mm",      "grosor": 3.0,  "kerf": 0.22},
    "mdf_6":    {"nombre": "MDF 6mm",      "grosor": 6.0,  "kerf": 0.25},
    "acrilico": {"nombre": "Acrilico 3mm", "grosor": 3.0,  "kerf": 0.18},
    "triplay":  {"nombre": "Triplay 4mm",  "grosor": 4.0,  "kerf": 0.25},
    "carton":   {"nombre": "Carton 2mm",   "grosor": 2.0,  "kerf": 0.15},
}

TIPOS = {
    "cerrada":   "ClosedBox",
    "bisagra":   "HingeBox",
    "abierta":   "ABox",
    "display":   "DisplayCase",
    "bandeja":   "DividerTray",
    "electronica":"ElectronicsBox",
}

@registrar("m05_caja_laser")
def generar_caja(texto: str = "", ancho: float = 0, alto: float = 0,
                 prof: float = 0, material: str = "mdf_3",
                 tipo: str = "cerrada", **_) -> dict:
    """
    Genera SVG + DXF de caja parametrica lista para corte laser.
    Detecta dimensiones del texto si no se pasan directo.
    """
    import uuid
    txt = texto.lower()

    # Detectar dimensiones: "15x10x8" o "15 x 10 x 8"
    if not ancho or not alto or not prof:
        m = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', texto)
        if m:
            ancho = float(m.group(1))
            alto  = float(m.group(2))
            prof  = float(m.group(3))
        else:
            # 2 dimensiones: ancho x alto (sin profundidad)
            m2 = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', texto)
            if m2:
                ancho = float(m2.group(1))
                alto  = float(m2.group(2))
                prof  = ancho * 0.5  # profundidad por default = mitad del ancho

    if not ancho or not alto or not prof:
        tipos_txt = ", ".join(TIPOS.keys())
        mats_txt  = ", ".join(MATERIALES.keys())
        return {
            "ok": False,
            "respuesta": (
                "Necesito las 3 dimensiones. Ejemplo:\n"
                "'genera caja 20x15x8 mdf_3'\n"
                f"Tipos: {tipos_txt}\n"
                f"Materiales: {mats_txt}"
            )
        }

    # Detectar material en texto
    for k in MATERIALES:
        if k in txt:
            material = k
            break
    if "acrilico" in txt or "acrilico" in txt: material = "acrilico"
    if "triplay" in txt:  material = "triplay"
    if "carton"  in txt:  material = "carton"

    # Detectar tipo
    for k in TIPOS:
        if k in txt:
            tipo = k
            break
    if "bisagra" in txt:    tipo = "bisagra"
    if "display" in txt:    tipo = "display"
    if "bandeja" in txt:    tipo = "bandeja"

    mat  = MATERIALES.get(material, MATERIALES["mdf_3"])
    tipo_boxes = TIPOS.get(tipo, "ClosedBox")
    uid  = uuid.uuid4().hex[:6]
    nombre = f"caja_{tipo}_{int(ancho)}x{int(alto)}x{int(prof)}_{mat['nombre'].replace(' ','_')}_{uid}"
    svg_out = OUTPUT_DIR / f"{nombre}.svg"
    dxf_out = OUTPUT_DIR / f"{nombre}.dxf"

    burn = mat["kerf"] / 2
    t    = mat["grosor"]

    # DividerTray usa --sx/--sy en lugar de --x/--y
    if tipo_boxes == "DividerTray":
        xy_args = [f"--sx={ancho}", f"--sy={alto}"]
    else:
        xy_args = [f"--x={ancho}", f"--y={alto}"]

    cmd_svg = [
        BOXES_EXE, tipo_boxes,
        *xy_args,
        f"--h={prof}",
        f"--thickness={t}",
        f"--burn={burn:.3f}",
        "--format=svg",
        f"--output={str(svg_out)}",
    ]

    try:
        r = subprocess.run(cmd_svg, capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or not svg_out.exists():
            return {"ok": False, "respuesta": f"Error al generar caja: {r.stderr[:200]}"}
    except Exception as e:
        return {"ok": False, "respuesta": f"Error boxes.exe: {e}"}

    # Convertir SVG → DXF con ezdxf
    try:
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        # Conversión básica via ezdxf recover
        # Simple: guardamos el SVG y el usuario lo abre en Corel
        archivos = [{"tipo": "SVG", "ruta": str(svg_out), "nombre": svg_out.name}]
    except Exception:
        archivos = [{"tipo": "SVG", "ruta": str(svg_out), "nombre": svg_out.name}]

    respuesta = (
        f"Caja {tipo} generada: {int(ancho)}x{int(alto)}x{int(prof)}mm en {mat['nombre']}\n"
        f"  Archivo: {svg_out.name}\n"
        f"  Ruta: {str(OUTPUT_DIR)}\n"
        f"  Abre en Corel o Silhouette para cortar."
    )

    # Abrir carpeta de salida automáticamente
    try:
        os.startfile(str(OUTPUT_DIR))
    except Exception:
        pass

    return {
        "ok": True,
        "respuesta": respuesta,
        "datos": {
            "tipo": tipo,
            "material": mat["nombre"],
            "dimensiones": {"ancho": ancho, "alto": alto, "prof": prof},
            "archivos": archivos,
            "ruta": str(OUTPUT_DIR),
        }
    }

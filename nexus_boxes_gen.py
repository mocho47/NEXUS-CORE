"""
nexus_boxes_gen.py — Generador de cajas parametricas con boxes.py
Genera DXF + SVG + PDF listo para corte laser
"""
import os, subprocess, sys, tempfile, shutil
from pathlib import Path

# Directorio de salida
_OUT = Path(__file__).parent / "out"
_OUT.mkdir(exist_ok=True)

# Ruta al ejecutable boxes
def _boxes_cmd():
    """Localiza el comando boxes (instalado via pip)."""
    # Primero intentar como modulo Python
    python = sys.executable
    return python, "-m", "boxes"

# ── Tipos de caja disponibles ─────────────────────────────────────────────────
TIPOS_CAJA = [
    {
        "id": "ClosedBox",
        "nombre": "Caja cerrada",
        "icono": "📦",
        "desc": "Caja rectangular con tapa fija",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "RoundedBox",
        "nombre": "Caja esquinas redondeadas",
        "icono": "🎁",
        "desc": "Caja con bordes curvos, elegante",
        "params": ["x", "y", "h", "thickness", "radius"],
    },
    {
        "id": "ABox",
        "nombre": "Caja con bisagra",
        "icono": "💼",
        "desc": "Tapa articulada con bisagra MDF",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "TrayLayout",
        "nombre": "Bandeja / Charola",
        "icono": "🗃️",
        "desc": "Bandeja abierta sin tapa",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "SlottedBox",
        "nombre": "Caja con ranuras",
        "icono": "🪵",
        "desc": "Caja ensamble por ranuras sin pegamento",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "NutBox",
        "nombre": "Caja con tuercas",
        "icono": "🔩",
        "desc": "Ensamble con tornillos y tuercas",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "WallMounted",
        "nombre": "Caja para pared",
        "icono": "🖼️",
        "desc": "Organizador para montaje en pared",
        "params": ["x", "y", "h", "thickness"],
    },
    {
        "id": "DisplayCase",
        "nombre": "Vitrina / Display",
        "icono": "🏆",
        "desc": "Caja exhibidora con frente transparente",
        "params": ["x", "y", "h", "thickness"],
    },
]

# Grosores de material (mm) — mismo dict que nexus_studio_vector
MATERIALES = {
    "mdf_27":   {"nombre": "MDF 2.7mm",   "grosor": 2.7,  "kerf": 0.20},
    "mdf_3":    {"nombre": "MDF 3mm",     "grosor": 3.0,  "kerf": 0.22},
    "triplay":  {"nombre": "Triplay 4mm", "grosor": 4.0,  "kerf": 0.25},
    "acrilico": {"nombre": "Acrílico 3mm","grosor": 3.0,  "kerf": 0.18},
    "carton":   {"nombre": "Cartón 2mm",  "grosor": 2.0,  "kerf": 0.15},
    "cuero":    {"nombre": "Cuero 2mm",   "grosor": 2.0,  "kerf": 0.20},
    "madera_5": {"nombre": "Madera 5mm",  "grosor": 5.0,  "kerf": 0.30},
}


def tipos_caja() -> list[dict]:
    """Retorna la lista de tipos de caja disponibles."""
    return TIPOS_CAJA


def generar_caja(
    tipo: str,
    ancho: float,     # mm — dimension X
    alto: float,      # mm — dimension Y
    prof: float,      # mm — dimension H (profundidad/altura de la caja)
    material_key: str = "mdf_3",
    grosor_mm: float | None = None,   # sobreescribe el del material si se da
) -> dict:
    """
    Genera SVG de caja parametrica usando boxes.py y luego convierte a DXF y PDF.
    Retorna {ok, salida:[{filename, url, tipo, desc}], carpeta, uid}
    """
    import time, uuid, re
    uid = uuid.uuid4().hex[:8]
    mat = MATERIALES.get(material_key, MATERIALES["mdf_3"])
    t = grosor_mm if grosor_mm else mat["grosor"]
    burn = mat["kerf"] / 2  # burn compensation para boxes.py

    tmp_dir = Path(tempfile.mkdtemp())
    svg_tmp = tmp_dir / f"caja_{uid}.svg"

    # ── Construir comando boxes.py ─────────────────────────────────────────
    python = sys.executable
    cmd = [
        python, "-m", "boxes", tipo,
        f"--x={ancho}",
        f"--y={alto}",
        f"--h={prof}",
        f"--thickness={t}",
        f"--burn={burn:.3f}",
        "--format=svg",
        f"--output={str(svg_tmp)}",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            # boxes.py a veces imprime el SVG a stdout
            svg_content = result.stdout.strip()
            if svg_content.startswith("<?xml") or svg_content.startswith("<svg"):
                svg_tmp.write_text(svg_content, encoding="utf-8")
            else:
                return {
                    "ok": False,
                    "error": f"boxes.py error: {result.stderr[:400] or result.stdout[:400]}"
                }
    except FileNotFoundError:
        return {"ok": False, "error": "boxes.py no está instalado. Ejecuta: pip install boxes"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout al generar caja"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if not svg_tmp.exists():
        return {"ok": False, "error": "boxes.py no generó el archivo SVG"}

    # ── Nombre base de salida ──────────────────────────────────────────────
    nombre_base = f"caja_{tipo}_{int(ancho)}x{int(alto)}x{int(prof)}mm_{mat['nombre'].replace(' ','_')}_{uid}"

    salida = []

    # SVG final
    svg_out = _OUT / f"{nombre_base}.svg"
    shutil.copy(str(svg_tmp), str(svg_out))
    salida.append({
        "filename": svg_out.name,
        "url": f"/out/{svg_out.name}",
        "tipo": "SVG",
        "desc": f"Caja {tipo} — {mat['nombre']} — {ancho}×{alto}×{prof}mm",
    })

    # DXF desde SVG (via ezdxf + svgpathtools)
    try:
        dxf_path = _svg_a_dxf(svg_out, _OUT / f"{nombre_base}.dxf")
        if dxf_path and dxf_path.exists():
            salida.append({
                "filename": dxf_path.name,
                "url": f"/out/{dxf_path.name}",
                "tipo": "DXF",
                "desc": "Para Aspire, RDWorks, LaserCut",
            })
    except Exception:
        pass

    # PDF imprimible
    try:
        pdf_path = _svg_a_pdf(svg_out, _OUT / f"{nombre_base}.pdf")
        if pdf_path and pdf_path.exists():
            salida.append({
                "filename": pdf_path.name,
                "url": f"/out/{pdf_path.name}",
                "tipo": "PDF",
                "desc": "Para imprimir / revisar medidas",
            })
    except Exception:
        pass

    shutil.rmtree(tmp_dir, ignore_errors=True)

    return {
        "ok": True,
        "uid": uid,
        "nombre": f"Caja {tipo} {ancho}×{alto}×{prof}mm",
        "carpeta": str(_OUT),
        "salida": salida,
    }


def _svg_a_dxf(svg_path: Path, dxf_out: Path) -> Path | None:
    """Convierte SVG a DXF usando ezdxf."""
    try:
        import ezdxf
        from xml.etree import ElementTree as ET
        import re, math

        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()
        doc.layers.add("CORTE", color=1)

        tree = ET.parse(str(svg_path))
        root = tree.getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}

        def _to_mm(val: str, default=0.0) -> float:
            """Parsea valor SVG a mm (asume unidades px a 96dpi → /3.7795)."""
            if not val:
                return default
            val = val.strip()
            if val.endswith("mm"):
                return float(val[:-2])
            if val.endswith("px"):
                return float(val[:-2]) / 3.7795
            try:
                return float(val) / 3.7795
            except Exception:
                return default

        # Extraer todos los <line> y <polyline> y <rect>
        for el in root.iter():
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if tag == "line":
                x1 = _to_mm(el.get("x1","0"))
                y1 = _to_mm(el.get("y1","0"))
                x2 = _to_mm(el.get("x2","0"))
                y2 = _to_mm(el.get("y2","0"))
                msp.add_line((x1,-y1),(x2,-y2), dxfattribs={"layer":"CORTE"})
            elif tag == "rect":
                x  = _to_mm(el.get("x","0"))
                y  = _to_mm(el.get("y","0"))
                w  = _to_mm(el.get("width","0"))
                h  = _to_mm(el.get("height","0"))
                pts = [(x,-y),(x+w,-y),(x+w,-y-h),(x,-y-h),(x,-y)]
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer":"CORTE"})
            elif tag == "polyline":
                pts_str = el.get("points","")
                nums = [float(v)/3.7795 for v in re.split(r"[\s,]+", pts_str.strip()) if v]
                if len(nums) >= 4:
                    pts = [(nums[i],-nums[i+1]) for i in range(0, len(nums)-1, 2)]
                    msp.add_lwpolyline(pts, dxfattribs={"layer":"CORTE"})

        doc.saveas(str(dxf_out))
        return dxf_out
    except Exception:
        return None


def _svg_a_pdf(svg_path: Path, pdf_out: Path) -> Path | None:
    """Convierte SVG a PDF via reportlab o cairosvg."""
    try:
        import cairosvg
        cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_out))
        return pdf_out
    except ImportError:
        pass
    try:
        from reportlab.graphics import renderPDF
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(str(svg_path))
        if drawing:
            renderPDF.drawToFile(drawing, str(pdf_out))
            return pdf_out
    except ImportError:
        pass
    return None


if __name__ == "__main__":
    print("Tipos disponibles:")
    for t in tipos_caja():
        print(f"  {t['icono']} {t['id']:20s} — {t['desc']}")
    print("\nGenerando caja de prueba ClosedBox 200x150x80mm MDF3...")
    r = generar_caja("ClosedBox", 200, 150, 80, "mdf_3")
    if r["ok"]:
        print("OK — archivos generados:")
        for f in r["salida"]:
            print(f"  {f['tipo']:5s} {f['filename']}")
    else:
        print("ERROR:", r.get("error"))

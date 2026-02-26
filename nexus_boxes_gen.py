"""
nexus_boxes_gen.py — Generador de cajas parametricas con boxes.py
Genera DXF + SVG + PDF listo para corte laser
"""
import os, subprocess, sys, tempfile, shutil
from pathlib import Path

# Directorio de salida
_OUT = Path(__file__).parent / "out"
_OUT.mkdir(exist_ok=True)

# Ruta al ejecutable boxes.exe (instalado via pip install festi/boxes)
def _boxes_exe() -> str:
    """Localiza el ejecutable boxes.exe instalado por pip."""
    scripts = os.path.join(os.path.dirname(sys.executable), "Scripts", "boxes.exe")
    if os.path.isfile(scripts):
        return scripts
    # Fallback: PATH
    import shutil
    found = shutil.which("boxes")
    if found:
        return found
    return ""

# ── Tipos de caja disponibles ─────────────────────────────────────────────────
TIPOS_CAJA = [
    {
        "id": "ClosedBox",
        "nombre": "Caja cerrada",
        "icono": "📦",
        "desc": "Caja rectangular con tapa fija",
        "extra_args": [],
    },
    {
        "id": "ABox",
        "nombre": "Caja tipo A",
        "icono": "💼",
        "desc": "Caja simple abierta, tipo tray",
        "extra_args": [],
    },
    {
        "id": "HingeBox",
        "nombre": "Caja con bisagra",
        "icono": "🗝️",
        "desc": "Tapa con bisagra de gabinete",
        "extra_args": [],
    },
    {
        "id": "IntegratedHingeBox",
        "nombre": "Bisagra integrada",
        "icono": "📿",
        "desc": "Tapa articulada sin herraje metálico",
        "extra_args": [],
    },
    {
        "id": "DisplayCase",
        "nombre": "Vitrina / Display",
        "icono": "🏆",
        "desc": "Exhibidor acrilico transparente",
        "extra_args": [],
    },
    {
        "id": "DividerTray",
        "nombre": "Bandeja con divisiones",
        "icono": "🗃️",
        "desc": "Charola con filas y columnas para organizar",
        "extra_args": ["--sx_override", "--sy_override"],  # usa --sx --sy en vez de --x --y
        "_use_sx_sy": True,
    },
    {
        "id": "ElectronicsBox",
        "nombre": "Caja electronica",
        "icono": "🔩",
        "desc": "Caja con tapa de tornillos y barrenos",
        "extra_args": [],
    },
    {
        "id": "Crate",
        "nombre": "Caja tipo caja de madera",
        "icono": "🪵",
        "desc": "Crate con asas, apilable",
        "extra_args": [],
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

    # ── Construir comando boxes.exe ────────────────────────────────────────
    exe = _boxes_exe()
    if not exe:
        return {"ok": False, "error": "boxes.exe no encontrado. Ejecuta: pip install git+https://github.com/florianfesti/boxes.git"}

    # extra_args del tipo (si aplica)
    tipo_info = next((t2 for t2 in TIPOS_CAJA if t2["id"] == tipo), {})
    use_sx_sy = tipo_info.get("_use_sx_sy", False)

    if use_sx_sy:
        xy_args = [f"--sx={ancho}", f"--sy={alto}"]
    else:
        xy_args = [f"--x={ancho}", f"--y={alto}"]

    cmd = [
        exe, tipo,
    ] + xy_args + [
        f"--h={prof}",
        f"--thickness={t}",
        f"--burn={burn:.3f}",
        "--format=svg",
        f"--output={str(svg_tmp)}",
    ]

    # También generar lbrn2 para LightBurn (si está disponible)
    lbrn_tmp = tmp_dir / f"caja_{uid}.lbrn2"
    cmd_lbrn = [
        exe, tipo,
    ] + xy_args + [
        f"--h={prof}",
        f"--thickness={t}",
        f"--burn={burn:.3f}",
        "--format=lbrn2",
        f"--output={str(lbrn_tmp)}",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "error": f"boxes error: {result.stderr[:400] or result.stdout[:400]}"
            }
    except FileNotFoundError:
        return {"ok": False, "error": "boxes.exe no encontrado"}
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

    # LightBurn lbrn2
    try:
        subprocess.run(cmd_lbrn, capture_output=True, timeout=20)
        if lbrn_tmp.exists():
            lbrn_out = _OUT / f"{nombre_base}.lbrn2"
            shutil.copy(str(lbrn_tmp), str(lbrn_out))
            salida.append({
                "filename": lbrn_out.name,
                "url": f"/out/{lbrn_out.name}",
                "tipo": "LBRN2",
                "desc": "Para LightBurn (laser directo)",
            })
    except Exception:
        pass

    # PDF imprimible
    try:
        pdf_path = _svg_a_pdf(svg_out, _OUT / f"{nombre_base}.pdf")
        if pdf_path and pdf_path.exists() and pdf_path.stat().st_size > 100:
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
    """Convierte SVG a DXF usando svgpathtools (soporta <path> de boxes.py)."""
    try:
        from svgpathtools import svg2paths
        import ezdxf

        paths, attrs = svg2paths(str(svg_path))
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()
        doc.layers.add("CORTE", color=1)

        for path in paths:
            pts = []
            for segment in path:
                for t in [i / 20.0 for i in range(21)]:
                    try:
                        pt = segment.point(t)
                        pts.append((pt.real, -pt.imag))
                    except Exception:
                        pass
            if len(pts) >= 2:
                # Eliminar duplicados consecutivos
                dedup = [pts[0]]
                for p in pts[1:]:
                    if abs(p[0]-dedup[-1][0]) > 0.001 or abs(p[1]-dedup[-1][1]) > 0.001:
                        dedup.append(p)
                msp.add_lwpolyline(dedup, dxfattribs={"layer": "CORTE"})

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

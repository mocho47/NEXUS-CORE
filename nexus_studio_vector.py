"""
nexus_studio_vector.py — Motor de procesamiento vectorial para NEXUS Estudio.

Acepta: DXF, SVG, AI, EPS, PDF vectorial
Procesa:
  - Kerf compensation por material
  - Ajuste de encastres/ranuras al grosor de material elegido
  - Escala a medidas reales
  - Exporta: DXF (Aspire/RDWorks/LightBurn), SVG (CorelDRAW/Inkscape),
             SVG limpio para Silhouette Cameo, PDF supervision
"""

import os
import uuid
import math
import re
from pathlib import Path

import numpy as np
import ezdxf
from ezdxf import recover, units
from ezdxf.math import Vec2

try:
    from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
    from shapely.ops import unary_union
    HAS_SHAPELY = True
except Exception:
    HAS_SHAPELY = False

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)

# ── Materiales con sus parámetros ─────────────────────────────────────────────
MATERIALES = {
    "mdf_27":  {"nombre": "MDF 2.7mm",    "grosor": 2.7,  "kerf": 0.20},
    "mdf_3":   {"nombre": "MDF 3mm",      "grosor": 3.0,  "kerf": 0.22},
    "triplay": {"nombre": "Triplay 4mm",  "grosor": 4.0,  "kerf": 0.25},
    "acrilico":{"nombre": "Acrílico 3mm", "grosor": 3.0,  "kerf": 0.18},
    "carton":  {"nombre": "Cartón 2mm",   "grosor": 2.0,  "kerf": 0.15},
    "cuero":   {"nombre": "Cuero 2mm",    "grosor": 2.0,  "kerf": 0.20},
    "madera_5":{"nombre": "Madera 5mm",   "grosor": 5.0,  "kerf": 0.30},
}

# ── Leer DXF ──────────────────────────────────────────────────────────────────

def _leer_dxf(path: Path):
    """Lee DXF y devuelve doc ezdxf."""
    try:
        doc, _ = recover.readfile(str(path))
    except Exception:
        doc = ezdxf.readfile(str(path))
    return doc


def _entidades_dxf(msp):
    """Extrae todas las entidades geométricas del modelspace."""
    entidades = []
    for e in msp:
        entidades.append(e)
    return entidades


def _bbox_dxf(doc):
    """Calcula bounding box del DXF — compatible con todas las versiones de ezdxf."""
    xs, ys = [], []
    msp = doc.modelspace()
    for e in msp:
        try:
            t = e.dxftype()
            if t == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif t == "LWPOLYLINE":
                for pt in e.get_points("xy"):
                    xs.append(pt[0]); ys.append(pt[1])
            elif t == "CIRCLE":
                c = e.dxf.center; r = e.dxf.radius
                xs += [c.x - r, c.x + r]; ys += [c.y - r, c.y + r]
            elif t == "ARC":
                c = e.dxf.center; r = e.dxf.radius
                xs += [c.x - r, c.x + r]; ys += [c.y - r, c.y + r]
            elif t == "SPLINE":
                for pt in e.control_points:
                    xs.append(pt[0]); ys.append(pt[1])
        except Exception:
            pass
    if xs:
        return (min(xs), min(ys)), (max(xs), max(ys))
    return (0, 0), (100, 100)


# ── Kerf compensation ─────────────────────────────────────────────────────────

def _aplicar_kerf_dxf(doc_in, kerf_mm: float, uid: str) -> Path:
    """
    Aplica kerf compensation: desplaza líneas de corte hacia adentro kerf/2.
    Para polilíneas cerradas (piezas), reduce exterior e incrementa huecos.
    """
    if kerf_mm <= 0:
        return None

    doc_out = ezdxf.new("R2010")
    doc_out.units = doc_in.units
    msp_in  = doc_in.modelspace()
    msp_out = doc_out.modelspace()

    offset = kerf_mm / 2.0

    for entity in msp_in:
        dxftype = entity.dxftype()
        try:
            if dxftype in ("LINE",):
                # Líneas simples: copiar tal cual (kerf solo aplica a contornos cerrados)
                msp_out.add_line(entity.dxf.start, entity.dxf.end,
                                 dxfattribs={"layer": entity.dxf.layer})

            elif dxftype in ("LWPOLYLINE", "POLYLINE"):
                pts = list(entity.vertices() if dxftype == "POLYLINE"
                           else entity.get_points("xy"))
                pts_2d = [(p[0], p[1]) for p in pts]
                if len(pts_2d) < 3:
                    msp_out.add_lwpolyline(pts_2d)
                    continue
                if HAS_SHAPELY:
                    try:
                        poly = Polygon(pts_2d)
                        if poly.is_valid and poly.area > 0:
                            # Exterior: reduce por kerf/2
                            shrunk = poly.buffer(-offset, join_style=2)
                            if not shrunk.is_empty:
                                coords = list(shrunk.exterior.coords)
                                msp_out.add_lwpolyline(
                                    coords, close=True,
                                    dxfattribs={"layer": entity.dxf.layer}
                                )
                                continue
                    except Exception:
                        pass
                msp_out.add_lwpolyline(pts_2d, close=True,
                                       dxfattribs={"layer": entity.dxf.layer})

            elif dxftype == "CIRCLE":
                # Reducir radio por kerf/2
                r = max(0.1, entity.dxf.radius - offset)
                msp_out.add_circle(entity.dxf.center, r,
                                   dxfattribs={"layer": entity.dxf.layer})

            elif dxftype == "ARC":
                msp_out.add_arc(entity.dxf.center,
                                max(0.1, entity.dxf.radius - offset),
                                entity.dxf.start_angle, entity.dxf.end_angle,
                                dxfattribs={"layer": entity.dxf.layer})
            else:
                # Copiar entidades no modificables (textos, bloques, etc.)
                msp_out.add_entity(entity.copy())
        except Exception:
            pass

    out_path = OUT_DIR / f"kerf_{uid}.dxf"
    doc_out.saveas(str(out_path))
    return out_path


# ── Ajuste de encastres ───────────────────────────────────────────────────────

def _ajustar_encastres_dxf(doc_in, grosor_origen: float, grosor_destino: float,
                             uid: str) -> Path:
    """
    Reescala las ranuras/encastres de un DXF diseñado para grosor_origen
    al grosor_destino del material elegido.

    Estrategia: las ranuras son huecos rectangulares cuya dimension menor
    coincide con el grosor del material. Buscamos segmentos con longitud ~= grosor_origen
    y los reescalamos a grosor_destino.
    """
    if abs(grosor_origen - grosor_destino) < 0.1:
        return None  # Sin cambio necesario

    factor = grosor_destino / grosor_origen
    doc_out = ezdxf.new("R2010")
    doc_out.units = doc_in.units
    msp_in  = doc_in.modelspace()
    msp_out = doc_out.modelspace()

    tol = grosor_origen * 0.4  # tolerancia: ±40% del grosor

    def _es_ranura(longitud):
        return abs(longitud - grosor_origen) <= tol

    def _ajustar_pt(p, cx, cy, fx, fy):
        return (cx + (p[0] - cx) * fx, cy + (p[1] - cy) * fy)

    for entity in msp_in:
        dxftype = entity.dxftype()
        try:
            if dxftype == "LWPOLYLINE":
                pts = list(entity.get_points("xy"))
                if len(pts) < 3:
                    msp_out.add_lwpolyline(pts)
                    continue

                # Centroide
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)

                nuevos = []
                for i, pt in enumerate(pts):
                    prev_pt = pts[i - 1]
                    seg_len = math.hypot(pt[0] - prev_pt[0], pt[1] - prev_pt[1])
                    if _es_ranura(seg_len):
                        # Escalar este segmento hacia el centro
                        nuevos.append(_ajustar_pt(pt, cx, cy, factor, factor))
                    else:
                        nuevos.append(pt)

                msp_out.add_lwpolyline(nuevos, close=True,
                                       dxfattribs={"layer": entity.dxf.layer})
            else:
                msp_out.add_entity(entity.copy())
        except Exception:
            msp_out.add_entity(entity.copy())

    out_path = OUT_DIR / f"encastre_{uid}.dxf"
    doc_out.saveas(str(out_path))
    return out_path


# ── Escalar DXF ───────────────────────────────────────────────────────────────

def _escalar_dxf(doc_in, ancho_mm: float, alto_mm: float, uid: str) -> Path:
    """Escala el DXF a las medidas exactas deseadas (mm)."""
    (x0, y0), (x1, y1) = _bbox_dxf(doc_in)
    w = x1 - x0
    h = y1 - y0
    if w <= 0 or h <= 0:
        return None

    sx = ancho_mm / w
    sy = alto_mm  / h

    doc_out = ezdxf.new("R2010")
    doc_out.units = doc_in.units
    msp_in  = doc_in.modelspace()
    msp_out = doc_out.modelspace()

    def _scale_pt(p):
        return ((p[0] - x0) * sx, (p[1] - y0) * sy)

    for entity in msp_in:
        dxftype = entity.dxftype()
        try:
            if dxftype == "LINE":
                s = _scale_pt(entity.dxf.start[:2])
                e = _scale_pt(entity.dxf.end[:2])
                msp_out.add_line((*s, 0), (*e, 0),
                                 dxfattribs={"layer": entity.dxf.layer})
            elif dxftype == "LWPOLYLINE":
                pts = [_scale_pt(p) for p in entity.get_points("xy")]
                msp_out.add_lwpolyline(pts, close=True,
                                       dxfattribs={"layer": entity.dxf.layer})
            elif dxftype == "CIRCLE":
                c = _scale_pt(entity.dxf.center[:2])
                msp_out.add_circle((*c, 0), entity.dxf.radius * min(sx, sy),
                                   dxfattribs={"layer": entity.dxf.layer})
            else:
                msp_out.add_entity(entity.copy())
        except Exception:
            pass

    out_path = OUT_DIR / f"scaled_{uid}.dxf"
    doc_out.saveas(str(out_path))
    return out_path


# ── DXF → SVG ────────────────────────────────────────────────────────────────

def _dxf_a_svg(doc, uid: str, label: str = "") -> Path:
    """Convierte DXF a SVG para preview y Silhouette."""
    (x0, y0), (x1, y1) = _bbox_dxf(doc)
    w = max(x1 - x0, 1)
    h = max(y1 - y0, 1)
    SCALE = 3.7795  # mm a px (96dpi)
    sw = w * SCALE
    sh = h * SCALE

    lines = []
    msp = doc.modelspace()
    for entity in msp:
        dxftype = entity.dxftype()
        try:
            color = "#ff0000" if "cut" in entity.dxf.layer.lower() else "#000000"
            if dxftype == "LINE":
                s = entity.dxf.start
                e = entity.dxf.end
                lines.append(
                    f'<line x1="{(s.x-x0)*SCALE:.2f}" y1="{(sh-(s.y-y0)*SCALE):.2f}" '
                    f'x2="{(e.x-x0)*SCALE:.2f}" y2="{(sh-(e.y-y0)*SCALE):.2f}" '
                    f'stroke="{color}" stroke-width="1" fill="none"/>'
                )
            elif dxftype == "LWPOLYLINE":
                pts = list(entity.get_points("xy"))
                if len(pts) < 2:
                    continue
                d = "M " + " L ".join(
                    f"{(p[0]-x0)*SCALE:.2f},{(sh-(p[1]-y0)*SCALE):.2f}" for p in pts
                )
                if entity.closed:
                    d += " Z"
                lines.append(f'<path d="{d}" stroke="{color}" stroke-width="1" fill="none"/>')
            elif dxftype == "CIRCLE":
                c = entity.dxf.center
                r = entity.dxf.radius * SCALE
                cx = (c.x - x0) * SCALE
                cy = sh - (c.y - y0) * SCALE
                lines.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                              f'stroke="{color}" stroke-width="1" fill="none"/>')
            elif dxftype == "ARC":
                # Aproximar arco con polyline
                c = entity.dxf.center
                r = entity.dxf.radius
                a0 = math.radians(entity.dxf.start_angle)
                a1 = math.radians(entity.dxf.end_angle)
                if a1 < a0:
                    a1 += 2 * math.pi
                steps = max(8, int(abs(a1 - a0) * r * SCALE / 5))
                arc_pts = []
                for i in range(steps + 1):
                    a = a0 + (a1 - a0) * i / steps
                    px = (c.x + r * math.cos(a) - x0) * SCALE
                    py = sh - (c.y + r * math.sin(a) - y0) * SCALE
                    arc_pts.append(f"{px:.2f},{py:.2f}")
                d = "M " + " L ".join(arc_pts)
                lines.append(f'<path d="{d}" stroke="{color}" stroke-width="1" fill="none"/>')
        except Exception:
            pass

    svg_content = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{sw:.1f}" height="{sh:.1f}" '
        f'viewBox="0 0 {sw:.1f} {sh:.1f}">\n'
        f'<rect width="100%" height="100%" fill="white"/>\n'
        + "\n".join(lines) +
        f'\n</svg>'
    )

    suffix = f"_{label}" if label else ""
    out_path = OUT_DIR / f"vector{suffix}_{uid}.svg"
    out_path.write_text(svg_content, encoding="utf-8")
    return out_path


# ── SVG limpio para Silhouette ────────────────────────────────────────────────

def _svg_para_silhouette(svg_path: Path, uid: str) -> Path:
    """
    Genera SVG compatible con Silhouette Studio:
    - Elimina rellenos
    - Strokes en negro
    - Sin grupos complejos
    """
    try:
        content = svg_path.read_text(encoding="utf-8")
        # Simplificar: todo stroke negro, sin fill
        content = re.sub(r'fill="[^"]*"', 'fill="none"', content)
        content = re.sub(r'stroke="[^"]*"', 'stroke="#000000"', content)
        content = re.sub(r'stroke-width="[^"]*"', 'stroke-width="0.5"', content)
        # Agregar namespace Silhouette
        content = content.replace(
            '<svg ',
            '<svg xmlns:xlink="http://www.w3.org/1999/xlink" '
        )
        out_path = OUT_DIR / f"silhouette_{uid}.svg"
        out_path.write_text(content, encoding="utf-8")
        return out_path
    except Exception as e:
        return svg_path  # fallback


# ── PDF de supervisión ────────────────────────────────────────────────────────

def _dxf_a_pdf_supervision(doc, uid: str, info: str = "") -> Path:
    """Genera PDF de supervision desde DXF (LINE, LWPOLYLINE, CIRCLE, ARC)."""
    pdf_path = OUT_DIR / f"supervision_{uid}.pdf"
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.graphics import renderPDF
        from reportlab.graphics.shapes import Drawing, Line, PolyLine, Circle
        from reportlab.lib.colors import black, red, HexColor

        (x0, y0), (x1, y1) = _bbox_dxf(doc)
        w = max(x1 - x0, 1)
        h = max(y1 - y0, 1)
        page_w, page_h = A4
        margin = 30
        scale = min((page_w - margin * 2) / w, (page_h - margin * 2 - 30) / h)
        ox, oy = margin, margin + 20  # offset + espacio para texto

        drawing = Drawing(page_w, page_h)
        msp = doc.modelspace()

        for entity in msp:
            try:
                layer = getattr(entity.dxf, "layer", "")
                color = red if "cut" in layer.lower() else black
                sw = 0.5

                if entity.dxftype() == "LINE":
                    s, e = entity.dxf.start, entity.dxf.end
                    drawing.add(Line(
                        ox + (s.x - x0) * scale, oy + (s.y - y0) * scale,
                        ox + (e.x - x0) * scale, oy + (e.y - y0) * scale,
                        strokeColor=color, strokeWidth=sw
                    ))
                elif entity.dxftype() == "LWPOLYLINE":
                    pts_raw = list(entity.get_points("xy"))
                    if len(pts_raw) >= 2:
                        coords = []
                        for p in pts_raw:
                            coords += [ox + (p[0] - x0) * scale, oy + (p[1] - y0) * scale]
                        if entity.closed and len(coords) >= 4:
                            coords += [coords[0], coords[1]]
                        drawing.add(PolyLine(coords, strokeColor=color, strokeWidth=sw, fillColor=None))
                elif entity.dxftype() == "CIRCLE":
                    c = entity.dxf.center
                    r = entity.dxf.radius * scale
                    cx = ox + (c.x - x0) * scale
                    cy = oy + (c.y - y0) * scale
                    drawing.add(Circle(cx, cy, r, strokeColor=color, fillColor=None, strokeWidth=sw))
            except Exception:
                pass

        renderPDF.drawToFile(drawing, str(pdf_path))
    except Exception as pdf_err:
        # Fallback: SVG → PDF via svglib
        try:
            svg_p = _dxf_a_svg(doc, uid + "_pdfsvg")
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF as rPDF
            drw = svg2rlg(str(svg_p))
            if drw:
                rPDF.drawToFile(drw, str(pdf_path))
            else:
                raise ValueError("svglib no produjo drawing")
        except Exception:
            pdf_path.write_bytes(b"%PDF-1.4\n%EOF\n")

    return pdf_path


# ── Pipeline principal ────────────────────────────────────────────────────────

def procesar_vector(data: bytes, ext: str, material_key: str = "mdf_3",
                    ancho_mm: float = 0, alto_mm: float = 0,
                    grosor_origen_mm: float = 3.0,
                    aplicar_kerf: bool = True) -> dict:
    """
    Pipeline completo para archivos vectoriales.

    Args:
        data           : bytes del archivo
        ext            : extension (dxf, svg, ai, eps)
        material_key   : clave de MATERIALES
        ancho_mm       : 0 = mantener escala original
        alto_mm        : 0 = mantener escala original
        grosor_origen_mm: grosor para el que fue diseñado el DXF
        aplicar_kerf   : True = aplicar compensacion de kerf

    Returns:
        dict con ok, salida (lista de archivos), info
    """
    uid = uuid.uuid4().hex[:10]
    mat = MATERIALES.get(material_key, MATERIALES["mdf_3"])

    # Guardar archivo de entrada temporal
    ext = ext.lower().lstrip(".")
    tmp_path = OUT_DIR / f"input_{uid}.{ext}"
    tmp_path.write_bytes(data)

    archivos = []
    info_msgs = []

    try:
        # ── 1. Leer como DXF (o convertir SVG→DXF) ──────────────────────
        if ext == "dxf":
            doc = _leer_dxf(tmp_path)
        elif ext in ("svg", "ai", "eps"):
            doc = _svg_a_dxf(tmp_path, uid)
        else:
            return {"ok": False, "error": f"Formato '{ext}' no soportado. Usa DXF o SVG."}

        # ── 2. Escalar si se especificaron medidas ───────────────────────
        if ancho_mm > 0 and alto_mm > 0:
            scaled_path = _escalar_dxf(doc, ancho_mm, alto_mm, uid)
            if scaled_path:
                doc = ezdxf.readfile(str(scaled_path))
                info_msgs.append(f"Escalado a {ancho_mm}x{alto_mm}mm")

        # ── 3. Ajustar encastres al material ────────────────────────────
        if abs(grosor_origen_mm - mat["grosor"]) > 0.15:
            enc_path = _ajustar_encastres_dxf(doc, grosor_origen_mm, mat["grosor"], uid)
            if enc_path:
                doc = ezdxf.readfile(str(enc_path))
                info_msgs.append(
                    f"Encastres ajustados: {grosor_origen_mm}mm → {mat['grosor']}mm"
                )

        # ── 4. Kerf compensation ─────────────────────────────────────────
        if aplicar_kerf and mat["kerf"] > 0:
            kerf_path = _aplicar_kerf_dxf(doc, mat["kerf"], uid)
            if kerf_path:
                doc = ezdxf.readfile(str(kerf_path))
                info_msgs.append(f"Kerf compensado: {mat['kerf']}mm ({mat['nombre']})")

        # ── 5. Exportar DXF final ────────────────────────────────────────
        dxf_final = OUT_DIR / f"laser_{uid}.dxf"
        doc.saveas(str(dxf_final))
        archivos.append({
            "tipo": "DXF laser",
            "filename": dxf_final.name,
            "url": f"/out/{dxf_final.name}",
            "desc": f"{mat['nombre']} — para Aspire / RDWorks / LightBurn"
        })

        # ── 6. SVG vectorial ─────────────────────────────────────────────
        svg_path = _dxf_a_svg(doc, uid)
        archivos.append({
            "tipo": "SVG vector",
            "filename": svg_path.name,
            "url": f"/out/{svg_path.name}",
            "desc": "CorelDRAW / Inkscape / Illustrator"
        })

        # ── 7. SVG para Silhouette Cameo ─────────────────────────────────
        sil_path = _svg_para_silhouette(svg_path, uid)
        archivos.append({
            "tipo": "Silhouette SVG",
            "filename": sil_path.name,
            "url": f"/out/{sil_path.name}",
            "desc": "Silhouette Cameo / Portrait — importar como SVG"
        })

        # ── 8. PDF supervisión ───────────────────────────────────────────
        (x0, y0), (x1, y1) = _bbox_dxf(doc)
        dim_info = f"{abs(x1-x0):.1f}x{abs(y1-y0):.1f}mm"
        pdf_path = _dxf_a_pdf_supervision(doc, uid, dim_info)

        archivos.append({
            "tipo": "PDF supervisión",
            "filename": pdf_path.name,
            "url": f"/out/{pdf_path.name}",
            "desc": f"Vista previa — {dim_info}"
        })

        # Limpiar tmp
        try:
            tmp_path.unlink()
        except Exception:
            pass

        return {
            "ok":       True,
            "nombre":   f"Vector optimizado — {mat['nombre']}",
            "salida":   archivos,
            "info":     " | ".join(info_msgs) if info_msgs else "Procesado sin modificaciones",
            "material": mat,
            "carpeta":  str(OUT_DIR),
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


def _svg_a_dxf(svg_path: Path, uid: str):
    """Convierte SVG a DXF usando svgpathtools."""
    try:
        from svgpathtools import svg2paths
        paths, attrs = svg2paths(str(svg_path))

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        for path in paths:
            pts = []
            for segment in path:
                for t in [i / 10.0 for i in range(11)]:
                    try:
                        pt = segment.point(t)
                        pts.append((pt.real, -pt.imag))
                    except Exception:
                        pass
            if len(pts) >= 2:
                msp.add_lwpolyline(pts)

        tmp_dxf = OUT_DIR / f"from_svg_{uid}.dxf"
        doc.saveas(str(tmp_dxf))
        return ezdxf.readfile(str(tmp_dxf))
    except Exception as e:
        raise ValueError(f"No se pudo convertir SVG a DXF: {e}")


def get_materiales() -> dict:
    return MATERIALES

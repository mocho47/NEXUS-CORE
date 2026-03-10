"""
NEXUS — Generador de Diseños Merch
Genera archivos PNG listos para imprimir a la resolución correcta para:
  - Playera: espalda (30x30cm), pecho/corazón (8x8cm), manga izq (10x10cm), manga der (10x10cm)
  - Imán: 9x6cm / 6x6cm / 7x5cm (3 tamaños)
  - Llavero: 8x4cm (MDF laser) — doble cara

Todo a 300 DPI. Salida en PNG + PDF (printable).
"""

import os
import math
from pathlib import Path
from datetime import datetime
import uuid

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import mm, cm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib import colors
    RL_OK = True
except ImportError:
    RL_OK = False

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "ASSETS"
MERCH_OUT = BASE_DIR / "MERCH_OUTPUT"
MERCH_OUT.mkdir(exist_ok=True)

DPI = 300
MM_TO_PX = DPI / 25.4   # 1mm = 11.81px a 300dpi

def mm2px(mm_val): return int(mm_val * MM_TO_PX)
def cm2px(cm_val): return mm2px(cm_val * 10)


def _cargar_logo(nombre: str, max_w_px: int, max_h_px: int) -> Image.Image:
    """Carga un logo y lo escala manteniendo proporción."""
    path = ASSETS_DIR / nombre
    if not path.exists():
        # Placeholder negro si no existe
        img = Image.new("RGBA", (max_w_px, max_h_px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, max_w_px-1, max_h_px-1], outline=(200, 200, 200, 200), width=3)
        draw.text((max_w_px//2, max_h_px//2), f"[{nombre}]", fill=(180, 180, 180, 200), anchor="mm")
        return img
    img = Image.open(path).convert("RGBA")
    img.thumbnail((max_w_px, max_h_px), Image.LANCZOS)
    return img


def _pegar_centrado(base: Image.Image, elemento: Image.Image,
                     cx_px: int, cy_px: int) -> Image.Image:
    """Pega elemento centrado en (cx, cy) sobre base."""
    x = cx_px - elemento.width // 2
    y = cy_px - elemento.height // 2
    base.paste(elemento, (x, y), elemento)
    return base


def _crear_bandera_mexico(w_px: int, h_px: int) -> Image.Image:
    """Genera una bandera de México simple a la resolución dada."""
    img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    col = w_px // 3

    # Verde | Blanco | Rojo
    draw.rectangle([0, 0, col, h_px], fill=(0, 104, 71, 255))
    draw.rectangle([col, 0, col*2, h_px], fill=(255, 255, 255, 255))
    draw.rectangle([col*2, 0, w_px, h_px], fill=(206, 17, 38, 255))

    # Águila (círculo verde oscuro placeholder)
    cx, cy = w_px // 2, h_px // 2
    r = min(w_px, h_px) // 5
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(0, 80, 50, 200))
    draw.text((cx, cy), "🦅", fill=(200, 150, 50, 255), anchor="mm") if False else None

    # Borde fino
    draw.rectangle([0, 0, w_px-1, h_px-1], outline=(100, 100, 100, 150), width=2)
    return img


# ── PLAYERA ────────────────────────────────────────────────────────────────────

def generar_playera(
    logo_frente: str = "atf_logo.png",
    logo_espalda: str = "atf_logo.png",
    logo_manga_izq: str = "atf_logo.png",    # gorila ATF
    color_playera: tuple = (20, 20, 20),      # negro
    nombre_marca: str = "ATF by Simplex",
    job_id: str = None,
) -> dict:
    """
    Genera 4 archivos PNG:
      - espalda.png     → 30x30cm a 300dpi
      - pecho.png       → 8x8cm  a 300dpi (área corazón)
      - manga_izq.png   → 10x10cm (gorila)
      - manga_der.png   → 10x10cm (bandera México)
    """
    if not PIL_OK:
        return {"ok": False, "error": "Pillow no instalado"}

    job_id = job_id or uuid.uuid4().hex[:8]
    out_dir = MERCH_OUT / f"playera_{job_id}"
    out_dir.mkdir(exist_ok=True)
    archivos = {}

    # ── ESPALDA: 30x30cm ──────────────────────────────────────────────────────
    W, H = cm2px(30), cm2px(30)
    img = Image.new("RGBA", (W, H), (*color_playera, 255))
    draw = ImageDraw.Draw(img)

    # Logo grande centrado (máximo 25x25cm)
    logo = _cargar_logo(logo_espalda, cm2px(25), cm2px(25))
    img = _pegar_centrado(img, logo, W//2, H//2)

    # Marca debajo
    try:
        font_path = "C:/Windows/Fonts/arialbd.ttf"
        font = ImageFont.truetype(font_path, mm2px(12))
    except:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(img)
    draw.text((W//2, H - mm2px(15)), nombre_marca, fill=(200, 200, 200, 220),
              font=font, anchor="mm")

    # Línea decorativa
    draw.line([(W//4, H - mm2px(20)), (3*W//4, H - mm2px(20))],
              fill=(100, 100, 100, 150), width=mm2px(0.5))

    path_espalda = out_dir / "espalda.png"
    img.convert("RGB").save(str(path_espalda), dpi=(DPI, DPI))
    archivos["espalda"] = str(path_espalda)

    # ── PECHO/CORAZÓN: 8x8cm ──────────────────────────────────────────────────
    W2, H2 = cm2px(8), cm2px(8)
    img2 = Image.new("RGBA", (W2, H2), (*color_playera, 255))
    logo2 = _cargar_logo(logo_frente, cm2px(7), cm2px(7))
    img2 = _pegar_centrado(img2, logo2, W2//2, H2//2)

    path_pecho = out_dir / "pecho.png"
    img2.convert("RGB").save(str(path_pecho), dpi=(DPI, DPI))
    archivos["pecho"] = str(path_pecho)

    # ── MANGA IZQ: 10x10cm (gorila ATF) ───────────────────────────────────────
    W3, H3 = cm2px(10), cm2px(10)
    img3 = Image.new("RGBA", (W3, H3), (*color_playera, 255))
    logo3 = _cargar_logo(logo_manga_izq, cm2px(9), cm2px(9))
    img3 = _pegar_centrado(img3, logo3, W3//2, H3//2)

    path_manga_izq = out_dir / "manga_izquierda.png"
    img3.convert("RGB").save(str(path_manga_izq), dpi=(DPI, DPI))
    archivos["manga_izquierda"] = str(path_manga_izq)

    # ── MANGA DER: 10x10cm (bandera México) ───────────────────────────────────
    W4, H4 = cm2px(10), cm2px(7)   # bandera proporcional
    img4 = Image.new("RGBA", (W4, H4), (*color_playera, 255))
    bandera = _crear_bandera_mexico(cm2px(9), cm2px(6))
    img4 = _pegar_centrado(img4, bandera, W4//2, H4//2)

    path_manga_der = out_dir / "manga_derecha_bandera.png"
    img4.convert("RGB").save(str(path_manga_der), dpi=(DPI, DPI))
    archivos["manga_derecha"] = str(path_manga_der)

    # ── PDF con las 4 vistas ───────────────────────────────────────────────────
    pdf_path = _generar_pdf_playera(out_dir, archivos, nombre_marca, job_id)
    if pdf_path:
        archivos["pdf"] = str(pdf_path)

    return {
        "ok": True,
        "job_id": job_id,
        "archivos": archivos,
        "directorio": str(out_dir),
        "dpi": DPI,
        "nota": "Todos los archivos listos a 300 DPI para impresión DTF/serigrafía",
    }


def _generar_pdf_playera(out_dir: Path, archivos: dict, marca: str, job_id: str) -> str:
    """Genera PDF con las 4 vistas de playera."""
    if not RL_OK:
        return None
    pdf_path = out_dir / f"playera_{job_id}.pdf"
    c = rl_canvas.Canvas(str(pdf_path), pagesize=A4)
    W_page, H_page = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W_page/2, H_page - 2*cm, f"Playera — {marca}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W_page/2, H_page - 2.8*cm, f"300 DPI | DTF / Serigrafía | Job: {job_id}")

    # Disposición en grilla 2x2
    layout = [
        ("espalda",          "Espalda (30x30cm)",      2*cm, H_page - 14*cm),
        ("pecho",            "Pecho/Corazón (8x8cm)",  13*cm, H_page - 10*cm),
        ("manga_izquierda",  "Manga Izq. — Gorila",    2*cm, H_page - 24*cm),
        ("manga_derecha",    "Manga Der. — Bandera MX", 13*cm, H_page - 21*cm),
    ]

    for key, titulo, x, y in layout:
        path = archivos.get(key)
        if path and os.path.exists(path):
            w_draw = 9*cm if key == "espalda" else 5*cm
            h_draw = 9*cm if key == "espalda" else (3.5*cm if "manga_der" in key else 5*cm)
            c.drawImage(str(path), x, y, width=w_draw, height=h_draw,
                        preserveAspectRatio=True)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y - 0.5*cm, titulo)

    c.setFont("Helvetica", 7)
    c.drawCentredString(W_page/2, 1*cm, f"NEXUS by Simplex — Generado {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.save()
    return str(pdf_path)


# ── IMÁN ───────────────────────────────────────────────────────────────────────

TAMANOS_IMAN = {
    "grande":   (9, 6),   # cm
    "mediano":  (7, 5),
    "chico":    (6, 6),
    "redondo":  (7, 7),   # circular
}


def generar_iman(
    logo: str = "atf_logo.png",
    tamano: str = "grande",
    texto_principal: str = "ATF by Simplex",
    subtexto: str = "Retrofit Faros LED • GDL",
    telefono: str = "3326148674",
    color_fondo: tuple = (10, 10, 30),
    color_texto: tuple = (0, 200, 255),
    job_id: str = None,
) -> dict:
    if not PIL_OK:
        return {"ok": False, "error": "Pillow no instalado"}

    job_id = job_id or uuid.uuid4().hex[:8]
    out_dir = MERCH_OUT / f"iman_{job_id}"
    out_dir.mkdir(exist_ok=True)

    w_cm, h_cm = TAMANOS_IMAN.get(tamano, (9, 6))
    W, H = cm2px(w_cm), cm2px(h_cm)

    img = Image.new("RGBA", (W, H), (*color_fondo, 255))
    draw = ImageDraw.Draw(img)

    # Si es redondo, máscara circular
    is_round = tamano == "redondo"

    # Borde exterior
    border_w = mm2px(2)
    draw.rectangle([0, 0, W-1, H-1], outline=(*color_texto, 200), width=border_w)
    draw.rectangle([border_w+mm2px(1), border_w+mm2px(1),
                    W-border_w-mm2px(2), H-border_w-mm2px(2)],
                   outline=(*color_texto, 80), width=1)

    # Logo lado izquierdo (40% del ancho)
    logo_area_w = int(W * 0.38)
    logo_img = _cargar_logo(logo, logo_area_w - mm2px(4), H - mm2px(8))
    img = _pegar_centrado(img, logo_img, logo_area_w // 2, H // 2)

    # Línea divisoria
    draw = ImageDraw.Draw(img)
    lx = logo_area_w + mm2px(1)
    draw.line([(lx, mm2px(5)), (lx, H - mm2px(5))], fill=(*color_texto, 100), width=mm2px(0.5))

    # Textos lado derecho
    tx_start = lx + mm2px(4)
    try:
        f_titulo = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", mm2px(5.5))
        f_sub    = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", mm2px(4))
        f_tel    = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", mm2px(5))
    except:
        f_titulo = f_sub = f_tel = ImageFont.load_default()

    draw.text((tx_start, mm2px(8)), texto_principal,
              fill=(*color_texto, 255), font=f_titulo)
    draw.text((tx_start, mm2px(16)), subtexto,
              fill=(200, 200, 200, 230), font=f_sub)

    # Separador
    draw.line([(tx_start, mm2px(23)), (W - mm2px(5), mm2px(23))],
              fill=(*color_texto, 80), width=1)

    # Teléfono
    draw.text((tx_start, mm2px(26)), f"📞 {telefono}",
              fill=(255, 255, 200, 230), font=f_tel)

    # Marca de agua "by Simplex"
    try:
        f_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", mm2px(3))
    except:
        f_small = ImageFont.load_default()
    draw.text((W - mm2px(3), H - mm2px(5)), "by Simplex",
              fill=(100, 100, 100, 180), font=f_small, anchor="rm")

    if is_round:
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, W, H], fill=255)
        img.putalpha(mask)

    out_path = out_dir / f"iman_{tamano}.png"
    img.convert("RGB").save(str(out_path), dpi=(DPI, DPI))

    # PDF planilla (4 imanes en hoja carta)
    pdf_path = _planilla_imanes(str(out_path), w_cm, h_cm, out_dir, job_id)

    return {
        "ok": True,
        "job_id": job_id,
        "archivo": str(out_path),
        "pdf_planilla": str(pdf_path) if pdf_path else None,
        "tamano": f"{w_cm}x{h_cm}cm",
        "dpi": DPI,
    }


def _planilla_imanes(img_path: str, w_cm: float, h_cm: float,
                      out_dir: Path, job_id: str) -> str:
    if not RL_OK:
        return None
    pdf_path = out_dir / f"planilla_imanes_{job_id}.pdf"
    c = rl_canvas.Canvas(str(pdf_path), pagesize=letter)
    W_p, H_p = letter

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W_p/2, H_p - 1.5*cm, f"Planilla Imanes — {w_cm}x{h_cm}cm | 300 DPI")

    cols, rows = 2, 3
    margin = 1.5*cm
    gap = 0.5*cm
    cell_w = (W_p - 2*margin - (cols-1)*gap) / cols
    cell_h = (H_p - 3*cm - (rows-1)*gap) / rows

    for row in range(rows):
        for col in range(cols):
            x = margin + col * (cell_w + gap)
            y = H_p - 3*cm - (row+1)*cell_h - row*gap
            c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)
            if os.path.exists(img_path):
                c.drawImage(img_path, x + 2, y + 2,
                            width=cell_w - 4, height=cell_h - 4,
                            preserveAspectRatio=True)

    c.setFont("Helvetica", 7)
    c.drawCentredString(W_p/2, 0.8*cm, f"NEXUS by Simplex — {datetime.now().strftime('%Y-%m-%d')}")
    c.save()
    return str(pdf_path)


# ── LLAVERO ────────────────────────────────────────────────────────────────────

def generar_llavero(
    logo: str = "atf_logo.png",
    texto: str = "ATF by Simplex",
    subtexto: str = "Retrofit • GDL",
    telefono: str = "3326148674",
    descuento: str = "10% OFF",
    color_fondo: tuple = (10, 10, 30),
    color_acento: tuple = (0, 200, 255),
    job_id: str = None,
) -> dict:
    """Genera llavero 8x4cm doble cara (frente + reverso) listo para laser MDF."""
    if not PIL_OK:
        return {"ok": False, "error": "Pillow no instalado"}

    job_id = job_id or uuid.uuid4().hex[:8]
    out_dir = MERCH_OUT / f"llavero_{job_id}"
    out_dir.mkdir(exist_ok=True)

    W, H = cm2px(8), cm2px(4)
    HOLE_R = mm2px(3)   # agujero llavero

    def _base():
        img = Image.new("RGBA", (W, H), (*color_fondo, 255))
        draw = ImageDraw.Draw(img)
        # Borde redondeado visual
        r = mm2px(4)
        draw.rounded_rectangle([0, 0, W-1, H-1], radius=r,
                                outline=(*color_acento, 200), width=mm2px(1))
        # Agujero
        draw.ellipse([mm2px(5)-HOLE_R, H//2-HOLE_R,
                      mm2px(5)+HOLE_R, H//2+HOLE_R],
                     fill=(*color_fondo, 255), outline=(*color_acento, 200), width=2)
        return img

    try:
        f_main = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", mm2px(5))
        f_sub  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   mm2px(3.5))
        f_big  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", mm2px(8))
    except:
        f_main = f_sub = f_big = ImageFont.load_default()

    # ── FRENTE ────────────────────────────────────────────────────────────────
    img_f = _base()
    logo_img = _cargar_logo(logo, cm2px(2.5), cm2px(3))
    img_f = _pegar_centrado(img_f, logo_img, int(W * 0.28), H // 2)

    draw = ImageDraw.Draw(img_f)
    lx = int(W * 0.48)
    draw.text((lx, H//2 - mm2px(9)), texto,
              fill=(*color_acento, 255), font=f_main)
    draw.text((lx, H//2 - mm2px(2)), subtexto,
              fill=(200, 200, 200, 220), font=f_sub)
    draw.text((lx, H//2 + mm2px(5)), telefono,
              fill=(255, 255, 200, 230), font=f_sub)

    path_frente = out_dir / "llavero_frente.png"
    img_f.convert("RGB").save(str(path_frente), dpi=(DPI, DPI))

    # ── REVERSO ───────────────────────────────────────────────────────────────
    img_r = _base()
    draw = ImageDraw.Draw(img_r)

    # Descuento grande al centro
    draw.text((W//2, H//2 - mm2px(5)), descuento,
              fill=(*color_acento, 255), font=f_big, anchor="mm")
    draw.text((W//2, H//2 + mm2px(7)), "en tu próxima instalación",
              fill=(200, 200, 200, 200), font=f_sub, anchor="mm")
    draw.text((W//2, H//2 + mm2px(13)), subtexto,
              fill=(150, 150, 150, 180), font=f_sub, anchor="mm")

    path_reverso = out_dir / "llavero_reverso.png"
    img_r.convert("RGB").save(str(path_reverso), dpi=(DPI, DPI))

    # PDF planilla (8 llaveros por hoja — 4 frente + 4 reverso)
    pdf_path = _planilla_llaveros(str(path_frente), str(path_reverso), out_dir, job_id)

    return {
        "ok": True,
        "job_id": job_id,
        "frente": str(path_frente),
        "reverso": str(path_reverso),
        "pdf_planilla": str(pdf_path) if pdf_path else None,
        "tamano": "8x4cm",
        "dpi": DPI,
        "nota": "Listo para impresión + corte laser MDF 3mm",
    }


def _planilla_llaveros(frente: str, reverso: str, out_dir: Path, job_id: str) -> str:
    if not RL_OK:
        return None
    pdf_path = out_dir / f"planilla_llaveros_{job_id}.pdf"
    c = rl_canvas.Canvas(str(pdf_path), pagesize=letter)
    W_p, H_p = letter

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W_p/2, H_p - 1.5*cm, "Planilla Llaveros 8x4cm | 300 DPI | MDF 3mm")

    lw, lh = 8*cm, 4*cm
    gap = 0.4*cm
    margin_x = (W_p - 2*lw - gap) / 2
    margin_y = 2.5*cm

    for row in range(4):
        y = H_p - margin_y - (row+1)*lh - row*gap

        for col, (img_path, label) in enumerate([(frente, "FRENTE"), (reverso, "REVERSO")]):
            x = margin_x + col * (lw + gap)
            c.rect(x, y, lw, lh, stroke=1, fill=0)
            if os.path.exists(img_path):
                c.drawImage(img_path, x+1, y+1, width=lw-2, height=lh-2,
                            preserveAspectRatio=True)
            c.setFont("Helvetica", 6)
            c.drawString(x + 1, y + 1, label)

    c.setFont("Helvetica", 7)
    c.drawCentredString(W_p/2, 0.8*cm,
                        f"NEXUS by Simplex — {datetime.now().strftime('%Y-%m-%d')}")
    c.save()
    return str(pdf_path)


# ── API de alto nivel ──────────────────────────────────────────────────────────

def generar_kit_completo(
    negocio: str = "atf",
    telefono: str = "3326148674",
    job_id: str = None,
) -> dict:
    """Genera playera + imán grande + llavero en un solo call."""
    job_id = job_id or uuid.uuid4().hex[:8]

    configs = {
        "atf": {
            "logo": "atf_logo.png",
            "marca": "ATF by Simplex",
            "subtexto": "Retrofit Faros LED • GDL",
            "color_fondo": (10, 10, 30),
            "color_acento": (0, 200, 255),
        },
        "canbusfix": {
            "logo": "canbusfix_logo.png",
            "marca": "CanbusFix by Simplex",
            "subtexto": "Red Instaladores • GDL",
            "color_fondo": (20, 10, 10),
            "color_acento": (255, 80, 0),
        },
        "milens": {
            "logo": "atf_logo.png",
            "marca": "Milens by Simplex",
            "subtexto": "Corte Láser • GDL",
            "color_fondo": (10, 20, 10),
            "color_acento": (0, 255, 80),
        },
    }

    cfg = configs.get(negocio, configs["atf"])

    playera = generar_playera(
        logo_frente=cfg["logo"],
        logo_espalda=cfg["logo"],
        logo_manga_izq=cfg["logo"],
        color_playera=cfg["color_fondo"],
        nombre_marca=cfg["marca"],
        job_id=f"{job_id}_playera",
    )
    iman = generar_iman(
        logo=cfg["logo"],
        tamano="grande",
        texto_principal=cfg["marca"],
        subtexto=cfg["subtexto"],
        telefono=telefono,
        color_fondo=cfg["color_fondo"],
        color_texto=cfg["color_acento"],
        job_id=f"{job_id}_iman",
    )
    llavero = generar_llavero(
        logo=cfg["logo"],
        texto=cfg["marca"],
        subtexto=cfg["subtexto"],
        telefono=telefono,
        color_fondo=cfg["color_fondo"],
        color_acento=cfg["color_acento"],
        job_id=f"{job_id}_llavero",
    )

    return {
        "ok": True,
        "job_id": job_id,
        "negocio": negocio,
        "playera": playera,
        "iman": iman,
        "llavero": llavero,
    }

# -*- coding: utf-8 -*-
"""
Genera planilla de stickers de tortillas
Planilla: 33x48 cm | Sticker: 4x4 cm | 300 DPI
"""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw
import fitz  # PyMuPDF

# ── CONFIGURACION ─────────────────────────────────────────────────────────────
DPI          = 300
MM2PX        = DPI / 25.4

# Planilla
PLAN_W_CM    = 33
PLAN_H_CM    = 48
PLAN_W_PX    = int(PLAN_W_CM * 10 * MM2PX)   # 33cm -> px
PLAN_H_PX    = int(PLAN_H_CM * 10 * MM2PX)   # 48cm -> px

# Sticker
STICK_CM     = 4.0
STICK_PX     = int(STICK_CM * 10 * MM2PX)     # 4cm -> px (~472px)

# Margenes y gaps (para distribucion perfecta)
MARGIN_CM    = 0.5    # margen exterior
MARGIN_PX    = int(MARGIN_CM * 10 * MM2PX)

# Calcular cuantos entran
area_w = PLAN_W_PX - 2 * MARGIN_PX
area_h = PLAN_H_PX - 2 * MARGIN_PX

cols = math.floor(area_w / STICK_PX)  # 7
rows = math.floor(area_h / STICK_PX)  # 11

# Gaps distribuidos uniformemente para centrar la grilla
gap_x = (area_w - cols * STICK_PX) // (cols - 1) if cols > 1 else 0
gap_y = (area_h - rows * STICK_PX) // (rows - 1) if rows > 1 else 0

total = cols * rows

print(f"Planilla: {PLAN_W_CM}x{PLAN_H_CM}cm  ({PLAN_W_PX}x{PLAN_H_PX}px a {DPI}DPI)")
print(f"Sticker:  {STICK_CM}cm  ({STICK_PX}px)")
print(f"Grilla:   {cols} cols x {rows} filas = {total} etiquetas")
print(f"Gap X:    {gap_x}px  |  Gap Y: {gap_y}px")

# ── RENDERIZAR STICKER DESDE PDF ──────────────────────────────────────────────
print("Renderizando sticker desde PDF...")
doc = fitz.open("C:/Users/Administrador/Downloads/tortillas.pdf")
page = doc[0]

# Escala para obtener exactamente STICK_PX de ancho
page_w_pts = page.rect.width
scale = (STICK_PX / page_w_pts)
mat = fitz.Matrix(scale, scale)
pix = page.get_pixmap(matrix=mat, alpha=True)
sticker_img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)

# Asegurar exactamente STICK_PX x STICK_PX
sticker_img = sticker_img.resize((STICK_PX, STICK_PX), Image.LANCZOS)
doc.close()

print(f"Sticker renderizado: {sticker_img.size}  modo: {sticker_img.mode}")

# ── CREAR PLANILLA ────────────────────────────────────────────────────────────
print("Generando planilla...")
# Fondo blanco
planilla = Image.new("RGB", (PLAN_W_PX, PLAN_H_PX), (255, 255, 255))
draw = ImageDraw.Draw(planilla)

# Lineas de guia muy suaves (gris claro para corte)
# Opcional: descomentar para agregar marcas de corte
GUIAS = True
COLOR_GUIA = (220, 220, 220)  # gris muy suave

for row in range(rows):
    for col in range(cols):
        # Posicion top-left del sticker
        x = MARGIN_PX + col * (STICK_PX + gap_x)
        y = MARGIN_PX + row * (STICK_PX + gap_y)

        # Pegar sticker (con canal alpha)
        planilla.paste(sticker_img, (x, y), sticker_img)

        # Marcas de corte: 4 esquinas (lineas de 3mm)
        if GUIAS:
            tick = int(3 * MM2PX)  # 3mm
            g = COLOR_GUIA
            # Esquina top-left
            draw.line([(x - tick, y), (x, y)], fill=g, width=1)
            draw.line([(x, y - tick), (x, y)], fill=g, width=1)
            # Esquina top-right
            draw.line([(x + STICK_PX, y), (x + STICK_PX + tick, y)], fill=g, width=1)
            draw.line([(x + STICK_PX, y - tick), (x + STICK_PX, y)], fill=g, width=1)
            # Esquina bot-left
            draw.line([(x - tick, y + STICK_PX), (x, y + STICK_PX)], fill=g, width=1)
            draw.line([(x, y + STICK_PX), (x, y + STICK_PX + tick)], fill=g, width=1)
            # Esquina bot-right
            draw.line([(x + STICK_PX, y + STICK_PX), (x + STICK_PX + tick, y + STICK_PX)], fill=g, width=1)
            draw.line([(x + STICK_PX, y + STICK_PX), (x + STICK_PX, y + STICK_PX + tick)], fill=g, width=1)

# Borde exterior de referencia
draw.rectangle([0, 0, PLAN_W_PX-1, PLAN_H_PX-1], outline=(180, 180, 180), width=3)

# Info en margen inferior
try:
    from PIL import ImageFont
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(2.5 * MM2PX))
    info = f"Planilla {PLAN_W_CM}x{PLAN_H_CM}cm  |  {total} etiquetas  |  {STICK_CM}cm c/u  |  {DPI} DPI  |  NEXUS by Simplex"
    draw.text((MARGIN_PX, PLAN_H_PX - int(4 * MM2PX)), info,
              fill=(150, 150, 150), font=font)
except:
    pass

# ── GUARDAR PDF + PNG ─────────────────────────────────────────────────────────
OUT_PDF = "C:/nexus/MERCH_OUTPUT/Planilla_Tortillas_33x48.pdf"
OUT_PNG = "C:/nexus/MERCH_OUTPUT/Planilla_Tortillas_33x48.png"

print("Guardando PNG...")
planilla.save(OUT_PNG, dpi=(DPI, DPI), optimize=False)

print("Guardando PDF...")
# Crear PDF con las dimensiones exactas en puntos (1pt = 1/72 pulgada)
from reportlab.lib.units import cm as rl_cm
from reportlab.pdfgen import canvas as rl_canvas

W_pt = PLAN_W_CM * rl_cm   # puntos reportlab
H_pt = PLAN_H_CM * rl_cm

cv = rl_canvas.Canvas(OUT_PDF, pagesize=(W_pt, H_pt))
cv.drawImage(OUT_PNG, 0, 0, width=W_pt, height=H_pt,
             preserveAspectRatio=True)
cv.setFont("Helvetica", 6)
cv.setFillColorRGB(0.6, 0.6, 0.6)
cv.drawString(0.5*rl_cm, 0.3*rl_cm,
    f"Planilla {PLAN_W_CM}x{PLAN_H_CM}cm | {total} etiquetas {STICK_CM}cm | {DPI} DPI | ATF by Simplex")
cv.save()

print(f"\nLISTO:")
print(f"  PDF: {OUT_PDF}")
print(f"  PNG: {OUT_PNG}")
print(f"  Total etiquetas: {total}")
print(f"  Tamano archivo PNG: {__import__('os').path.getsize(OUT_PNG)/1024/1024:.1f} MB")

# -*- coding: utf-8 -*-
"""
Etiqueta Aguas Frescas Juliana
Tamano: 4cm ancho x 8cm alto
Resolucion: 300 DPI — lista para maquiladora
PDF con 1 sola etiqueta perfectamente dimensionada
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
import os

# ── CONFIGURACION ─────────────────────────────────────────────────────────────
DPI       = 300
W_CM      = 4.0   # ancho total
H_CM      = 8.0   # alto total
MARGIN_MM = 4     # margen interior 4mm — letras separadas del borde
W_PX      = int(W_CM / 2.54 * DPI)
H_PX      = int(H_CM / 2.54 * DPI)
MARGIN_PX = int(MARGIN_MM / 10 / 2.54 * DPI)  # 4mm en px (~47px)

SRC_JPG   = "C:/Users/Administrador/Downloads/aguas frescas .jpeg"
OUT_PNG   = "C:/nexus/MERCH_OUTPUT/Aguas_Frescas_4x8cm_300dpi.png"
OUT_PDF   = "C:/nexus/MERCH_OUTPUT/Aguas_Frescas_4x8cm.pdf"

print(f"Tamano objetivo: {W_CM}x{H_CM}cm  =  {W_PX}x{H_PX}px a {DPI}DPI")

# ── PROCESAR IMAGEN ───────────────────────────────────────────────────────────
img = Image.open(SRC_JPG).convert("RGB")
print(f"Original: {img.size}")

# Escalar manteniendo proporcion — ajuste exacto al marco 4x8cm
img_ratio = img.width / img.height
target_ratio = W_PX / H_PX

if img_ratio > target_ratio:
    # imagen mas ancha — ajustar por altura
    new_h = H_PX
    new_w = int(new_h * img_ratio)
else:
    # imagen mas alta — ajustar por ancho
    new_w = W_PX
    new_h = int(new_w / img_ratio)

img_scaled = img.resize((new_w, new_h), Image.LANCZOS)

# Area util (con margen 4mm por todos lados)
area_w = W_PX - 2 * MARGIN_PX
area_h = H_PX - 2 * MARGIN_PX

# Reescalar imagen para que quepa en el area util
img_ratio2 = img_scaled.width / img_scaled.height
if img_ratio2 > area_w / area_h:
    fit_w = area_w
    fit_h = int(area_w / img_ratio2)
else:
    fit_h = area_h
    fit_w = int(area_h * img_ratio2)
img_fit = img_scaled.resize((fit_w, fit_h), Image.LANCZOS)

# Crear base con fondo del color dominante del borde del diseño (rosa)
base = Image.new("RGB", (W_PX, H_PX), (220, 20, 100))
# Pegar imagen centrada dentro del area util
offset_x = MARGIN_PX + (area_w - fit_w) // 2
offset_y = MARGIN_PX + (area_h - fit_h) // 2
base.paste(img_fit, (offset_x, offset_y))

print(f"Resultado: {base.size}  ({W_CM}x{H_CM}cm a {DPI}DPI)")

# Guardar PNG maestro a 300 DPI
base.save(OUT_PNG, dpi=(DPI, DPI), quality=100, optimize=False)
print(f"PNG guardado: {OUT_PNG}  ({os.path.getsize(OUT_PNG)/1024:.0f} KB)")

# ── GENERAR PDF — 1 sola etiqueta dimensionada exacta ────────────────────────
W_PT = W_CM * cm   # puntos reportlab (exacto)
H_PT = H_CM * cm

cv = rl_canvas.Canvas(OUT_PDF, pagesize=(W_PT, H_PT))

# Imagen llenando exactamente el area (sin margenes — la maquiladora maneja el sangrado)
cv.drawImage(OUT_PNG, 0, 0, width=W_PT, height=H_PT, preserveAspectRatio=False)

cv.save()
print(f"PDF guardado: {OUT_PDF}  ({os.path.getsize(OUT_PDF)/1024:.0f} KB)")
print(f"\nLISTO para maquiladora:")
print(f"  Tamano: {W_CM} x {H_CM} cm")
print(f"  Resolucion: {DPI} DPI")
print(f"  Pagina PDF: exactamente {W_CM}x{H_CM}cm")
print(f"  La maquiladora acomoda el resto en la planilla 60x1m")

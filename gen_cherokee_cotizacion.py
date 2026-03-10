# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from datetime import datetime

OUT = "C:/nexus/MERCH_OUTPUT/Cotizacion_Cherokee_ATF.pdf"
c = canvas.Canvas(OUT, pagesize=letter)
W, H = letter
y_pos = [H - 3.5*cm]

# ── Partidas con precios del catalogo Illume ─────────────────────────────────
# (producto, codigo, cant, precio_dist_unit, precio_pub_unit, zona)
PARTIDAS = [
    # EXTERIOR TRASERO
    ("1157 Corn Bicolor DOS POLOS (frenos+cuartos traseros)", "IL_5397", 2, 225, 295, "Ext. Trasero"),
    ("1156 Ambar CANBUS (direccionales traseras)",            "IL_6095A",2, 141, 190, "Ext. Trasero"),
    ("1156 Corn Redonda (reversa)",                           "IL_6089", 2, 141, 190, "Ext. Trasero"),
    ("Festoon CANBUS 31mm (3ra luz de freno)",                "IL_3941", 1,  11,  95, "Ext. Trasero"),
    ("T10 Base Grande 15 LEDs (luz de placa)",                "IL_1203", 1,  34,  59, "Ext. Trasero"),
    # EXTERIOR DELANTERO
    ("1157 Bicolor AMBAR (cuartos+dir. delanteras)",          "IL_5397A",2, 225, 295, "Ext. Delantero"),
    ("T10 Base Larga 360 CANBUS (marcadores laterales)",      "IL_1212", 2,  30,  49, "Ext. Delantero"),
    # TABLERO Y CONSOLA
    ("T10 Base Grande 15 LEDs (iluminacion tablero)",         "IL_1203", 6,  34,  59, "Tablero"),
    ("T10 Base Larga 360 CANBUS (testigos/alertas)",          "IL_1212", 4,  30,  49, "Tablero"),
    ("T10 Base Larga 360 CANBUS (consola A/C)",               "IL_1212", 2,  30,  49, "Tablero"),
    ("T10 Base Grande 15 LEDs (palanca velocidades)",         "IL_1203", 1,  34,  59, "Tablero"),
    ("T10 Base Larga 360 CANBUS (cenicero/encendedor)",       "IL_1212", 1,  30,  49, "Tablero"),
    # CORTESIA INTERIOR
    ("Festoon CANBUS 36mm (domo/techo)",                      "IL_3942", 1,  60,  99, "Interior"),
    ("T10 Base Grande 15 LEDs (alfombra/pies)",               "IL_1203", 2,  34,  59, "Interior"),
    ("T10 Base Larga Corn CANBUS (luces lectura)",            "IL_1192", 2,  75, 125, "Interior"),
    ("T10 Base Grande 15 LEDs (guantera)",                    "IL_1203", 1,  34,  59, "Interior"),
]

# Aozoom X4 par
X4_DIST = 1990
X4_PUB  = 2699

# Instalacion ATF (mano de obra retrofit lupas)
MOD_DIST = 800   # precio instalacion lupas para ti
MOD_PUB  = 2500  # precio instalacion al cliente

# ── Calculos ──────────────────────────────────────────────────────────────────
total_aux_dist = sum(p[2]*p[3] for p in PARTIDAS)
total_aux_pub  = sum(p[2]*p[4] for p in PARTIDAS)
total_dist     = total_aux_dist + X4_DIST
total_pub      = total_aux_pub  + X4_PUB
total_pub_con_mo = total_pub + MOD_PUB

ganancia_producto = total_pub - total_dist
ganancia_total    = total_pub_con_mo - (total_dist + MOD_DIST)

print(f"Auxiliares dist:    ${total_aux_dist:,.0f}")
print(f"Auxiliares pub:     ${total_aux_pub:,.0f}")
print(f"X4 par dist:        ${X4_DIST:,.0f}")
print(f"X4 par pub:         ${X4_PUB:,.0f}")
print(f"TOTAL para ti:      ${total_dist:,.0f}")
print(f"TOTAL al cliente:   ${total_pub_con_mo:,.0f}  (con instalacion)")
print(f"Ganancia en producto: ${ganancia_producto:,.0f}")
print(f"Ganancia total c/MO:  ${ganancia_total:,.0f}")

# ── PDF ───────────────────────────────────────────────────────────────────────
def header():
    c.setFillColorRGB(0.05, 0.05, 0.2)
    c.rect(0, H-3*cm, W, 3*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(1.2*cm, H-1.4*cm, "COTIZACION — Jeep Grand Cherokee 1994 (ZJ)")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0, 0.8, 0.5)
    c.drawString(1.2*cm, H-2.0*cm, "Reemplazo LED completo + Par Aozoom X4 Bi-LED")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(1.2*cm, H-2.6*cm, "ATF by Simplex  |  3326148674  |  " + datetime.now().strftime("%d/%m/%Y"))

def section(titulo, r=0.05, g=0.1, b=0.45):
    y = y_pos[0]
    c.setFillColorRGB(r, g, b)
    c.rect(1*cm, y-0.55*cm, W-2*cm, 0.65*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.3*cm, y-0.38*cm, titulo)
    y_pos[0] -= 0.75*cm

def tabla(headers, rows, col_widths, highlight_last=False):
    y = y_pos[0]
    data = [headers] + rows
    estilo = [
        ('BACKGROUND',   (0,0), (-1,0), colors.HexColor('#1a1a6e')),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 8.5),
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#eef2ff')]),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
        ('ALIGN',        (2,0), (-1,-1), 'CENTER'),
        ('TEXTCOLOR',    (0,1), (-1,-1), colors.HexColor('#111111')),
    ]
    if highlight_last:
        estilo += [
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#003322')),
            ('TEXTCOLOR',  (0,-1), (-1,-1), colors.HexColor('#00ff88')),
            ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,-1), (-1,-1), 9),
        ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(estilo))
    tw, th = t.wrapOn(c, W-2*cm, H)
    if y - th < 2*cm:
        c.showPage()
        header_mini()
        y_pos[0] = H - 2.2*cm
        y = y_pos[0]
    t.drawOn(c, 1*cm, y - th)
    y_pos[0] -= th + 0.35*cm

def header_mini():
    c.setFillColorRGB(0.05, 0.05, 0.2)
    c.rect(0, H-1.4*cm, W, 1.4*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.2*cm, H-0.85*cm, "Cotizacion Cherokee 1994  |  ATF by Simplex")

def footer():
    c.setFillColorRGB(0.05, 0.05, 0.2)
    c.rect(0, 0, W, 0.7*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W/2, 0.25*cm,
        "ATF by Simplex  |  Retrofit Faros LED Guadalajara  |  3326148674  |  Generado con NEXUS")

# ─────────────────────────────────────────────────────────────────────────────
header()

# Agrupar por zona
zonas = ["Ext. Trasero", "Ext. Delantero", "Tablero", "Interior"]
colores_zona = {
    "Ext. Trasero":    (0.1, 0.15, 0.5),
    "Ext. Delantero":  (0.1, 0.2,  0.5),
    "Tablero":         (0.15, 0.25, 0.5),
    "Interior":        (0.15, 0.3,  0.5),
}
for zona in zonas:
    items = [p for p in PARTIDAS if p[5] == zona]
    if not items:
        continue
    sub_d = sum(p[2]*p[3] for p in items)
    sub_p = sum(p[2]*p[4] for p in items)
    r, g, b = colores_zona[zona]
    section(f"  {zona.upper()}  —  subtotal dist: ${sub_d:,.0f}  |  subtotal pub: ${sub_p:,.0f}", r, g, b)
    rows = [
        [p[0], p[1], str(p[2]),
         f"${p[3]:,}", f"${p[2]*p[3]:,}",
         f"${p[4]:,}", f"${p[2]*p[4]:,}"]
        for p in items
    ]
    tabla(
        ["Producto", "Cod.", "Cant.", "Dist. c/u", "Total dist.", "Pub. c/u", "Total pub."],
        rows,
        [6.2*cm, 1.6*cm, 1.1*cm, 1.8*cm, 1.9*cm, 1.8*cm, 1.9*cm]
    )

# LUPAS X4
section("  AOZOOM X4 BI-LED 3\" — PAR (lupas/proyectores)", 0.2, 0.05, 0.05)
tabla(
    ["Producto", "Cod.", "Cant.", "Dist. c/u", "Total dist.", "Pub. c/u", "Total pub."],
    [["Bi-LED Aozoom X4 3\" 6000K (par de lupas)", "AOZ-X4", "1 par",
      f"${X4_DIST:,}", f"${X4_DIST:,}", f"${X4_PUB:,}", f"${X4_PUB:,}"]],
    [6.2*cm, 1.6*cm, 1.1*cm, 1.8*cm, 1.9*cm, 1.8*cm, 1.9*cm]
)

# INSTALACION
section("  INSTALACION (mano de obra retrofit lupas — ATF)", 0.05, 0.3, 0.05)
tabla(
    ["Concepto", "", "Cant.", "Tu costo", "Total dist.", "Al cliente", "Total pub."],
    [["Retrofit Bi-LED + adaptacion harness + alineacion", "", "1",
      f"${MOD_DIST:,}", f"${MOD_DIST:,}", f"${MOD_PUB:,}", f"${MOD_PUB:,}"]],
    [6.2*cm, 1.6*cm, 1.1*cm, 1.8*cm, 1.9*cm, 1.8*cm, 1.9*cm]
)

# RESUMEN FINAL
section("  RESUMEN FINAL", 0.02, 0.02, 0.02)
tabla(
    ["Concepto", "", "", "Tu costo", "", "Al cliente", ""],
    [
        ["Auxiliares LED completos (todos los focos)", "", "",
         f"${total_aux_dist:,}", "", f"${total_aux_pub:,}", ""],
        ["Par Aozoom X4 Bi-LED", "", "",
         f"${X4_DIST:,}", "", f"${X4_PUB:,}", ""],
        ["Mano de obra instalacion", "", "",
         f"${MOD_DIST:,}", "", f"${MOD_PUB:,}", ""],
        [" TOTAL  (producto + instalacion)", "", "",
         f"${total_dist + MOD_DIST:,}", "",
         f"${total_pub_con_mo:,}", ""],
    ],
    [6.2*cm, 1.6*cm, 1.1*cm, 1.8*cm, 1.9*cm, 1.8*cm, 1.9*cm],
    highlight_last=True
)

# Caja ganancia
y = y_pos[0] - 0.2*cm
c.setFillColorRGB(0, 0.2, 0.05)
c.roundRect(1*cm, y-2.5*cm, W-2*cm, 2.3*cm, 8, fill=1, stroke=0)
c.setFillColorRGB(0, 1, 0.5)
c.setFont("Helvetica-Bold", 13)
c.drawString(1.6*cm, y-0.85*cm, "GANANCIA NETA EN PRODUCTO:     ${:,} MXN".format(ganancia_producto))
c.drawString(1.6*cm, y-1.5*cm, "GANANCIA TOTAL (prod + MO):     ${:,} MXN".format(ganancia_total))
c.setFillColorRGB(0.7, 1, 0.8)
c.setFont("Helvetica", 9)
c.drawString(1.6*cm, y-2.1*cm,
    "El cliente paga ${:,} | Tu inversion: ${:,} | Utilidad: {:.0f}%".format(
        total_pub_con_mo,
        total_dist + MOD_DIST,
        (ganancia_total / (total_dist + MOD_DIST)) * 100
    )
)

footer()
c.save()
print("PDF listo:", OUT)

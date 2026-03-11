# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

OUT = "C:/nexus/MERCH_OUTPUT/Nota_Pedido_Cherokee.pdf"
c = canvas.Canvas(OUT, pagesize=letter)
W, H = letter

c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, H-2*cm, "NOTA DE PEDIDO — ILLUME")
c.setFont("Helvetica", 10)
c.drawString(2*cm, H-2.6*cm, "Jeep Grand Cherokee 1994 (ZJ)  |  " + datetime.now().strftime("%d/%m/%Y"))

c.setFont("Helvetica", 11)
y = H - 4*cm
lineas = [
    "CALAVERAS:",
    "",
    "  2   IL_5399   1157 Corn Bicolor Dos Polos",
    "  2   IL_6095A  1156 Ambar Base Redonda CANBUS",
    "  2   IL_6098   1156 Red Base Redonda CANBUS",
    "",
    "FAROS:",
    "",
    "  1 par   AOZ-X4   Aozoom X4 Bi-LED 3\"",
    "",
    "─────────────────────────────────────",
    "  TOTAL:  8 piezas",
]

for linea in lineas:
    bold = linea in ["CALAVERAS:", "FAROS:"]
    c.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
    c.drawString(2*cm, y, linea)
    y -= 0.65*cm

c.save()
print("OK:", OUT)

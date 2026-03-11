# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from datetime import datetime

OUT = "C:/nexus/MERCH_OUTPUT/Lista_Calaveras_Faros_Cherokee.pdf"
c = canvas.Canvas(OUT, pagesize=letter)
W, H = letter

# HEADER
c.setFillColorRGB(0.05, 0.05, 0.2)
c.rect(0, H-3*cm, W, 3*cm, fill=1, stroke=0)
c.setFillColor(colors.white)
c.setFont("Helvetica-Bold", 16)
c.drawString(1.2*cm, H-1.5*cm, "Lista de Calaveras y Faros — Illume")
c.setFont("Helvetica", 11)
c.drawString(1.2*cm, H-2.1*cm, "Jeep Grand Cherokee 1994 (ZJ)")
c.setFont("Helvetica", 9)
c.drawString(1.2*cm, H-2.6*cm, "ATF by Simplex  |  3326148674  |  " + datetime.now().strftime("%d/%m/%Y"))

y = H - 4*cm

# CALAVERAS
c.setFillColorRGB(0.05, 0.05, 0.2)
c.rect(1*cm, y-0.6*cm, W-2*cm, 0.7*cm, fill=1, stroke=0)
c.setFillColor(colors.white)
c.setFont("Helvetica-Bold", 12)
c.drawString(1.3*cm, y-0.38*cm, "CALAVERAS (Luces Traseras)")
y -= 0.8*cm

data = [
    ["Funcion", "Modelo Illume", "Codigo", "Cant."],
    ["Freno + Cuarto (2057)", "1157 Corn Bicolor Dos Polos", "IL_5399", "2"],
    ["Direccional trasera (1156 ambar)", "1156 Ambar Base Redonda CANBUS", "IL_6095A", "2"],
    ["Reversa (1156 blanco)", "1156 Red Base Redonda CANBUS", "IL_6098", "2"],
]

t = Table(data, colWidths=[6*cm, 7*cm, 3*cm, 2*cm])
t.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1a1a6e')),
    ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
    ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',      (0,0), (-1,0), 10),
    ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,1), (-1,-1), 10),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#eef2ff')]),
    ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
    ('ALIGN',         (3,0), (3,-1), 'CENTER'),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
]))
tw, th = t.wrapOn(c, W-2*cm, H)
t.drawOn(c, 1*cm, y-th)
y -= th + 0.5*cm

# TOTAL CALAVERAS
c.setFillColorRGB(0.9, 0.85, 0)
c.rect(1*cm, y-0.6*cm, W-2*cm, 0.55*cm, fill=1, stroke=0)
c.setFillColorRGB(0.1, 0.05, 0)
c.setFont("Helvetica-Bold", 10)
c.drawString(1.3*cm, y-0.38*cm, "Total calaveras:   6 piezas")
y -= 1.2*cm

# FAROS
c.setFillColorRGB(0.15, 0.05, 0.4)
c.rect(1*cm, y-0.6*cm, W-2*cm, 0.7*cm, fill=1, stroke=0)
c.setFillColor(colors.white)
c.setFont("Helvetica-Bold", 12)
c.drawString(1.3*cm, y-0.38*cm, "FAROS PRINCIPALES (Retrofit Bi-LED)")
y -= 0.8*cm

data2 = [
    ["Funcion", "Producto", "Codigo", "Cant."],
    ["Alta/Baja — Retrofit Bi-LED", "Aozoom X4 3\" 6000K", "AOZ-X4", "1 par"],
]

t2 = Table(data2, colWidths=[6*cm, 7*cm, 3*cm, 2*cm])
t2.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#2d0a5e')),
    ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
    ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',      (0,0), (-1,0), 10),
    ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE',      (0,1), (-1,-1), 10),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white]),
    ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
    ('ALIGN',         (3,0), (3,-1), 'CENTER'),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING',    (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
]))
tw2, th2 = t2.wrapOn(c, W-2*cm, H)
t2.drawOn(c, 1*cm, y-th2)
y -= th2 + 0.5*cm

# TOTAL FAROS
c.setFillColorRGB(0.9, 0.85, 0)
c.rect(1*cm, y-0.6*cm, W-2*cm, 0.55*cm, fill=1, stroke=0)
c.setFillColorRGB(0.1, 0.05, 0)
c.setFont("Helvetica-Bold", 10)
c.drawString(1.3*cm, y-0.38*cm, "Total faros:   1 par (2 lupas)")
y -= 1.4*cm

# RESUMEN
c.setFillColorRGB(0, 0.2, 0.05)
c.roundRect(1*cm, y-2*cm, W-2*cm, 1.8*cm, 8, fill=1, stroke=0)
c.setFillColorRGB(0, 1, 0.5)
c.setFont("Helvetica-Bold", 13)
c.drawString(1.6*cm, y-0.8*cm, "TOTAL PIEZAS:   8  (6 calaveras + 1 par lupas X4)")
c.setFillColorRGB(0.7, 1, 0.8)
c.setFont("Helvetica", 9)
c.drawString(1.6*cm, y-1.4*cm, "Calaveras: productos Illume  |  Faros: Aozoom X4 via ATF by Simplex")

# FOOTER
c.setFillColorRGB(0.05, 0.05, 0.2)
c.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
c.setFillColor(colors.white)
c.setFont("Helvetica", 8)
c.drawCentredString(W/2, 0.28*cm,
    "ATF by Simplex  |  Retrofit Faros LED Guadalajara  |  3326148674  |  Generado con NEXUS")

c.save()
print("OK:", OUT)

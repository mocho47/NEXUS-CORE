import ezdxf

# Parámetros del panel
ANCHO     = 900.0    # mm (90 cm)
ALTO      = 1220.0   # mm (122 cm)
D_AGUJERO = 4.0      # mm diámetro
ESPACIADO = 25.0     # mm centro a centro (estándar pegboard)
MARGEN    = 12.5     # mm desde el borde

doc = ezdxf.new(dxfversion='R2010')
doc.header['$INSUNITS'] = 4  # milímetros
msp = doc.modelspace()

radio = D_AGUJERO / 2.0
cols = int((ANCHO - 2 * MARGEN) / ESPACIADO) + 1
rows = int((ALTO  - 2 * MARGEN) / ESPACIADO) + 1

count = 0
for row in range(rows):
    y = MARGEN + row * ESPACIADO
    if y > ALTO - MARGEN + 0.01:
        continue
    for col in range(cols):
        x = MARGEN + col * ESPACIADO
        if x > ANCHO - MARGEN + 0.01:
            continue
        msp.add_circle(center=(x, y), radius=radio)
        count += 1

# Marco exterior de corte
msp.add_lwpolyline(
    [(0,0),(ANCHO,0),(ANCHO,ALTO),(0,ALTO),(0,0)],
    close=True
)

salida = 'C:/nexus/out/pegboard_90x122_4mm.dxf'
doc.saveas(salida)
print(f'OK: {count} circulos | {cols} columnas x {rows} filas | {salida}')

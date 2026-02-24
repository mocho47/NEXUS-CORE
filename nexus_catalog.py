"""
nexus_catalog.py — Generador de catálogos HTML con precios reales.
Lee precios_base.json y marketing_db.json para generar catálogos actualizados.
"""
import os
import json
import webbrowser
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class CatalogGenerator:
    def __init__(self):
        self.output_dir  = os.path.join(BASE_DIR, "WEB", "static", "catalogos")
        os.makedirs(self.output_dir, exist_ok=True)
        self.precios     = self._load(os.path.join(BASE_DIR, "CONFIG", "precios_base.json"))
        self.marketing   = self._load(os.path.join(BASE_DIR, "CONFIG", "marketing_db.json"))

    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _items_desde_precios(self) -> list:
        """Construye lista unificada de productos con precios reales."""
        items = []
        # Laser materiales
        for m in self.precios.get("laser", {}).get("materiales", []):
            items.append({
                "nombre":   m["nombre"],
                "precio":   f"${m['precio_hoja']:.0f}/hoja  •  ${self.precios['laser']['costo_minuto']:.0f}/min corte",
                "categoria": "Corte Láser",
                "wa_texto": f"Hola, me interesa: {m['nombre']}"
            })
        # Sublimación
        for p in self.precios.get("sublimacion_personalizacion", []):
            precio_base = p.get("precio_subli") or p.get("precio_laser") or p.get("precio_dtf") or p.get("precio_vinil") or 0
            if precio_base:
                items.append({
                    "nombre":    f"{p['cat']} — {p['nombre']}",
                    "precio":    f"${precio_base:.0f}",
                    "categoria": "Sublimación / Personalización",
                    "wa_texto":  f"Hola, me interesa: {p['nombre']}"
                })
        # Retrofit
        for r in self.precios.get("retrofit", []):
            items.append({
                "nombre":    r["nombre"],
                "precio":    f"${r['precio']:.0f}",
                "categoria": "Retrofit Automotriz",
                "wa_texto":  f"Hola, me interesa el servicio: {r['nombre']}"
            })
        # Insumos textil
        ins = self.precios.get("insumos_textil", {})
        if ins.get("dtf_metro"):
            items.append({"nombre": "Impresión DTF", "precio": f"${ins['dtf_metro']:.0f}/metro", "categoria": "Textil / DTF", "wa_texto": "Hola, me interesa: Impresión DTF"})
        if ins.get("dtf_uv_metro"):
            items.append({"nombre": "DTF UV Premium", "precio": f"${ins['dtf_uv_metro']:.0f}/metro", "categoria": "Textil / DTF", "wa_texto": "Hola, me interesa: DTF UV"})
        return items

    def generate_html_catalog(self, empresa_nombre="Nexus Taller", telefono="", tipo="completo") -> str:
        items    = self._items_desde_precios()
        color    = "#00ff88"
        fecha    = datetime.datetime.now().strftime("%d/%m/%Y")

        # Agrupar por categoría
        categorias = {}
        for item in items:
            cat = item["categoria"]
            categorias.setdefault(cat, []).append(item)

        secciones_html = ""
        for cat, productos in categorias.items():
            secciones_html += f'<div class="section"><h2 class="cat-title">{cat}</h2>'
            for p in productos:
                wa_num  = telefono.replace("+", "").replace(" ", "")
                wa_link = f"https://wa.me/{wa_num}?text={p['wa_texto'].replace(' ', '%20')}" if wa_num else f"https://wa.me/?text={p['wa_texto'].replace(' ', '%20')}"
                secciones_html += f"""
                <div class="card">
                    <div class="card-info">
                        <div class="card-name">{p['nombre']}</div>
                        <div class="card-price">{p['precio']}</div>
                    </div>
                    <a href="{wa_link}" class="btn-wa" target="_blank">Cotizar</a>
                </div>"""
            secciones_html += "</div>"

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo {empresa_nombre}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 16px; }}
        .header {{ text-align: center; padding: 24px 0 16px; border-bottom: 1px solid #222; margin-bottom: 20px; }}
        .header h1 {{ color: {color}; margin: 0; font-size: 1.6em; }}
        .header p {{ color: #555; margin: 4px 0 0; font-size: 0.85em; }}
        .section {{ margin-bottom: 24px; }}
        .cat-title {{ color: {color}; font-size: 1em; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #222; padding-bottom: 6px; margin-bottom: 12px; }}
        .card {{ display: flex; justify-content: space-between; align-items: center; background: #111; border: 1px solid #1e1e1e; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }}
        .card-name {{ font-weight: bold; font-size: 0.95em; }}
        .card-price {{ color: {color}; font-size: 0.9em; margin-top: 2px; }}
        .btn-wa {{ background: #25D366; color: #000; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 0.85em; white-space: nowrap; }}
        .footer {{ text-align: center; color: #333; font-size: 0.75em; margin-top: 32px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{empresa_nombre}</h1>
        <p>Catálogo de servicios — Actualizado {fecha}</p>
    </div>
    {secciones_html}
    <div class="footer">Generado por NEXUS • {fecha}</div>
</body>
</html>"""

        filename = f"catalogo_{tipo}.html"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return filepath

    def open_catalog(self, tipo="completo"):
        path = self.generate_html_catalog(tipo=tipo)
        webbrowser.open(f"file:///{path}")
        return path

manager = CatalogGenerator()

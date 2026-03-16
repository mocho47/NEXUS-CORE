# -*- coding: utf-8 -*-
"""Motor 9 — Material ATF: genera tarjetas, QR, portadas para redes."""
import sys, os
sys.path.insert(0, 'C:/nexus_v2')
from cerebro import registrar
from pathlib import Path

OUTPUT_DIR = Path("C:/nexus/MERCH_OUTPUT/atf_material")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@registrar("m09_material_atf")
def material_atf(texto: str = "", tipo: str = "", **_) -> dict:
    txt = texto.lower()

    if not tipo:
        if "qr" in txt:          tipo = "qr"
        elif "tarjeta" in txt:   tipo = "tarjeta"
        elif "portada" in txt:   tipo = "portada"
        else:                    tipo = "qr"  # default más útil

    if tipo == "qr":
        return _generar_qr()
    elif tipo == "tarjeta":
        return _generar_tarjeta()
    elif tipo == "portada":
        return _generar_portada()
    return {"ok": False, "respuesta": "Tipo no reconocido. Usa: qr, tarjeta, portada"}

def _generar_qr() -> dict:
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
        import uuid

        uid = uuid.uuid4().hex[:6]
        url = "https://mocho47.github.io/ATF-PORTFOLIO/"

        qr = qrcode.QRCode(version=2, box_size=10, border=3,
                            error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(url)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="#003020", back_color="white").convert("RGB")

        # Canvas con branding
        W, H = 400, 480
        canvas = Image.new("RGB", (W, H), "#001810")
        qr_resized = img_qr.resize((280, 280))
        canvas.paste(qr_resized, (60, 60))

        draw = ImageDraw.Draw(canvas)
        draw.text((W//2, 370), "ATF by Simplex", fill="#00ff88", anchor="mm")
        draw.text((W//2, 400), "Retrofit de Faros GDL", fill="#aaaaaa", anchor="mm")
        draw.text((W//2, 425), "WA: 33 2614 8674", fill="#888888", anchor="mm")
        draw.text((W//2, 450), url[:40], fill="#555555", anchor="mm")

        out = OUTPUT_DIR / f"qr_atf_{uid}.png"
        canvas.save(str(out), dpi=(300, 300))
        os.startfile(str(OUTPUT_DIR))

        return {
            "ok": True,
            "respuesta": f"QR ATF generado: {out.name}\nURL: {url}\nRuta: {str(OUTPUT_DIR)}",
            "datos": {"archivo": str(out), "url": url}
        }
    except Exception as e:
        return {"ok": False, "respuesta": f"Error al generar QR: {e}"}

def _generar_tarjeta() -> dict:
    try:
        from PIL import Image, ImageDraw
        import uuid

        uid  = uuid.uuid4().hex[:6]
        W, H = 1063, 591  # 9x5cm a 300 DPI

        img = Image.new("RGB", (W, H), "#001810")
        draw = ImageDraw.Draw(img)

        # Borde verde
        draw.rectangle([10, 10, W-10, H-10], outline="#00ff88", width=3)

        # Contenido
        draw.text((W//2, 180), "ATF", fill="#00ff88", anchor="mm")
        draw.text((W//2, 250), "Actualiza Tus Faros", fill="white", anchor="mm")
        draw.text((W//2, 330), "Retrofit bi-LED Profesional", fill="#aaaaaa", anchor="mm")
        draw.text((W//2, 420), "Guadalajara, Jalisco", fill="#888888", anchor="mm")
        draw.text((W//2, 480), "WA: 33 2614 8674", fill="#00ff88", anchor="mm")

        out = OUTPUT_DIR / f"tarjeta_atf_{uid}.png"
        img.save(str(out), dpi=(300, 300))
        os.startfile(str(OUTPUT_DIR))

        return {
            "ok": True,
            "respuesta": f"Tarjeta ATF generada: {out.name}\n9x5cm a 300 DPI listo para imprimir.",
            "datos": {"archivo": str(out)}
        }
    except Exception as e:
        return {"ok": False, "respuesta": f"Error al generar tarjeta: {e}"}

def _generar_portada() -> dict:
    try:
        from PIL import Image, ImageDraw
        import uuid

        uid  = uuid.uuid4().hex[:6]
        W, H = 1080, 1080  # Cuadrado Instagram

        img  = Image.new("RGB", (W, H), "#001810")
        draw = ImageDraw.Draw(img)

        # Gradiente simulado con rectángulos
        for i in range(0, H, 4):
            alpha = int(20 + (i / H) * 30)
            draw.rectangle([0, i, W, i+4], fill=(0, alpha, alpha//2))

        draw.rectangle([40, 40, W-40, H-40], outline="#00ff88", width=2)
        draw.text((W//2, 380), "ATF", fill="#00ff88", anchor="mm")
        draw.text((W//2, 480), "Actualiza Tus Faros", fill="white", anchor="mm")
        draw.text((W//2, 560), "Retrofit bi-LED Guadalajara", fill="#aaaaaa", anchor="mm")
        draw.text((W//2, 700), "WA: 33 2614 8674", fill="#00ff88", anchor="mm")
        draw.text((W//2, 780), "@atf.simplex", fill="#666666", anchor="mm")

        out = OUTPUT_DIR / f"portada_ig_atf_{uid}.png"
        img.save(str(out), dpi=(300, 300))
        os.startfile(str(OUTPUT_DIR))

        return {
            "ok": True,
            "respuesta": f"Portada Instagram ATF generada: {out.name}\n1080x1080px lista para publicar.",
            "datos": {"archivo": str(out)}
        }
    except Exception as e:
        return {"ok": False, "respuesta": f"Error al generar portada: {e}"}

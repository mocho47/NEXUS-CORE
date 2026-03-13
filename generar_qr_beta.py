#!/usr/bin/env python3
"""
generar_qr_beta.py
Genera códigos QR para el pack beta de NEXUS.
- QR para WhatsApp (enlace de descarga / bienvenida)
- QR para landing page pública
- QR para acceso local (red WiFi)
"""
import os
import sys
import socket

try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Instalando dependencias QR...")
    os.system(f"{sys.executable} -m pip install qrcode[pil] pillow --quiet")
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "out", "QR")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BRAND_COLOR = (0, 255, 136)      # #00ff88
DARK_BG     = (7, 10, 14)        # #070a0e
WHITE       = (255, 255, 255)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def generar_qr(url: str, nombre: str, subtitulo: str = "") -> str:
    """Genera QR con branding NEXUS. Devuelve ruta del archivo."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # QR en colores de marca
    qr_img = qr.make_image(fill_color=(0, 255, 136), back_color=(7, 10, 14))
    qr_img = qr_img.convert("RGBA")

    # Canvas total
    qr_w, qr_h = qr_img.size
    padding = 40
    header_h = 80
    footer_h = 60
    total_w = qr_w + padding * 2
    total_h = qr_h + header_h + footer_h + padding * 2

    canvas = Image.new("RGBA", (total_w, total_h), DARK_BG)

    # Pegar QR
    canvas.paste(qr_img, (padding, header_h + padding), qr_img)

    draw = ImageDraw.Draw(canvas)

    # Línea superior decorativa
    draw.rectangle([0, 0, total_w, 4], fill=BRAND_COLOR)

    # Título
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_sub   = ImageFont.truetype("arial.ttf", 16)
        font_url   = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title
        font_url   = font_title

    # Logo NEXUS
    nexus_text = "NEXUS"
    bbox = draw.textbbox((0, 0), nexus_text, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((total_w - tw) // 2, 14), nexus_text, fill=BRAND_COLOR, font=font_title)

    # Sub header
    if subtitulo:
        bbox2 = draw.textbbox((0, 0), subtitulo, font=font_sub)
        sw = bbox2[2] - bbox2[0]
        draw.text(((total_w - sw) // 2, 46), subtitulo, fill=(125, 133, 144), font=font_sub)

    # URL debajo del QR
    url_short = url if len(url) < 50 else url[:47] + "..."
    bbox3 = draw.textbbox((0, 0), url_short, font=font_url)
    uw = bbox3[2] - bbox3[0]
    draw.text(((total_w - uw) // 2, total_h - footer_h + 10), url_short,
              fill=(125, 133, 144), font=font_url)

    # "by Simplex"
    by_text = "by Simplex"
    bbox4 = draw.textbbox((0, 0), by_text, font=font_url)
    bw = bbox4[2] - bbox4[0]
    draw.text(((total_w - bw) // 2, total_h - 24), by_text,
              fill=(40, 50, 60), font=font_url)

    # Línea inferior
    draw.rectangle([0, total_h - 4, total_w, total_h], fill=BRAND_COLOR)

    # Guardar PNG
    out_path = os.path.join(OUTPUT_DIR, f"nexus_qr_{nombre}.png")
    canvas = canvas.convert("RGB")
    canvas.save(out_path, "PNG", quality=95)
    return out_path


def main():
    local_ip = get_local_ip()
    print(f"\n  NEXUS QR Generator — IP local: {local_ip}")
    print("  " + "─" * 50)

    urls = [
        {
            "url":       f"http://{local_ip}:8000/bienvenida",
            "nombre":    "wifi_bienvenida",
            "subtitulo": "Únete a NEXUS — Red local",
        },
        {
            "url":       "https://wa.me/523326148674?text=Quiero%20instalar%20NEXUS",
            "nombre":    "whatsapp_beta",
            "subtitulo": "Solicitar NEXUS Beta — WhatsApp",
        },
        {
            "url":       "http://localhost:8000/bienvenida",
            "nombre":    "localhost_bienvenida",
            "subtitulo": "Instalar NEXUS — Primera vez",
        },
        {
            "url":       "http://localhost:8000/manual",
            "nombre":    "manual_usuario",
            "subtitulo": "Manual de Usuario NEXUS",
        },
    ]

    generated = []
    for item in urls:
        path = generar_qr(item["url"], item["nombre"], item["subtitulo"])
        generated.append(path)
        print(f"  ✅ {item['nombre']:28s} → {os.path.basename(path)}")

    print(f"\n  QRs guardados en: {OUTPUT_DIR}")
    print()

    # Abrir carpeta automáticamente
    try:
        import subprocess
        subprocess.Popen(["explorer", OUTPUT_DIR])
    except Exception:
        pass

    print("  Para usar en llavero o tarjeta:")
    print(f"  → Imprime nexus_qr_whatsapp_beta.png a 5x5cm, 300dpi")
    print(f"  → Imprime nexus_qr_wifi_bienvenida.png para entregar en mano")
    print()


if __name__ == "__main__":
    main()

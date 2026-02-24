"""
nexus_image_processor.py — Optimizador de imágenes por servicio.
Recibe cualquier imagen y la prepara según el proceso de producción.

Servicios soportados:
  LASER      → Escala de grises, alto contraste, 300 DPI
  SUBLIMACION→ Imagen espejada, saturación boost, RGB limpio
  DTF        → Fondo transparente, canal alpha, listo para RIP
  LONA       → Alta resolución, simulación CMYK, guía de sangría
  NEON       → Extrae contorno, vectorización básica sugerida
  GENERAL    → Solo redimensiona y optimiza sin cambios especiales
"""
import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "TALLER", "ARCHIVOS_PROCESADOS")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# DPI estándar por servicio
DPI_POR_SERVICIO = {
    "LASER":       300,
    "SUBLIMACION": 300,
    "DTF":         300,
    "LONA":        150,   # Impresión gran formato: 72-150 DPI es suficiente
    "NEON":        300,
    "GENERAL":     300,
}

def procesar_imagen(ruta_entrada: str, servicio: str) -> dict:
    """
    Procesa una imagen según el servicio de producción.
    Retorna dict con ruta de salida, detalles y recomendaciones.
    """
    servicio = servicio.upper().replace("Ó","O").replace("É","E").replace("Á","A")
    if servicio not in DPI_POR_SERVICIO:
        servicio = "GENERAL"

    try:
        img = Image.open(ruta_entrada).convert("RGBA")
    except Exception as e:
        return {"ok": False, "error": f"No se pudo abrir la imagen: {e}"}

    w_orig, h_orig = img.size
    nombre_base = os.path.splitext(os.path.basename(ruta_entrada))[0]
    ts          = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    detalles    = []
    recom       = []

    # ── LASER ────────────────────────────────────────────────────────────────
    if servicio == "LASER":
        img_proc = img.convert("L")                          # Escala de grises
        img_proc = ImageOps.autocontrast(img_proc, cutoff=2) # Contraste automático
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(1.8)                     # Boost de contraste
        img_proc = img_proc.filter(ImageFilter.SHARPEN)      # Nitidez para bordes limpios
        nombre_salida = f"{nombre_base}_LASER_{ts}.png"
        formato_salida = "PNG"
        detalles = [
            "Convertida a escala de grises",
            "Contraste aumentado x1.8 para mejor grabado",
            "Nitidez aplicada para bordes precisos",
            "Formato PNG 300 DPI listo para LightBurn / K40"
        ]
        recom = [
            "Verifica que las áreas oscuras sean las que quieres grabar",
            "Si necesitas invertir (grabado en negativo) usa la opción de invertir en LightBurn",
            "Para corte vectorial, exporta también a SVG desde tu editor"
        ]

    # ── SUBLIMACION ──────────────────────────────────────────────────────────
    elif servicio == "SUBLIMACION":
        img_proc = img.convert("RGB")
        img_proc = ImageOps.mirror(img_proc)                 # ESPEJO OBLIGATORIO
        enhancer_sat = ImageEnhance.Color(img_proc)
        img_proc = enhancer_sat.enhance(1.15)                # Saturación +15%
        enhancer_bright = ImageEnhance.Brightness(img_proc)
        img_proc = enhancer_bright.enhance(1.05)             # Brillo +5%
        nombre_salida = f"{nombre_base}_SUBLI_ESPEJADO_{ts}.jpg"
        formato_salida = "JPEG"
        detalles = [
            "Imagen espejada horizontalmente (obligatorio para transfer térmico)",
            "Saturación aumentada +15% (compensar pérdida en prensado)",
            "Brillo ajustado +5%",
            "Formato JPG RGB 300 DPI listo para impresora de sublimación"
        ]
        recom = [
            "Imprime en papel de sublimación, NO papel normal",
            "Temperatura recomendada: 180-200°C según el sustrato",
            "Verifica que la imagen se ve espejada en pantalla antes de imprimir"
        ]

    # ── DTF ──────────────────────────────────────────────────────────────────
    elif servicio == "DTF":
        # Mantener RGBA, eliminar fondo blanco si lo tiene
        img_proc = _eliminar_fondo_blanco(img)
        nombre_salida = f"{nombre_base}_DTF_TRANSPARENTE_{ts}.png"
        formato_salida = "PNG"
        detalles = [
            "Fondo blanco eliminado (transparente)",
            "Canal alpha preservado para impresión DTF",
            "Formato PNG 32-bit listo para RIP de DTF",
            "Sin espejo (DTF se imprime directo)"
        ]
        recom = [
            "Imprime con capa de polvo blanco DTF para telas oscuras",
            "Para telas claras, el polvo blanco es opcional",
            "Temperatura de prensado: 160-170°C, 15 segundos"
        ]

    # ── LONA / BANNER ────────────────────────────────────────────────────────
    elif servicio == "LONA":
        img_proc = img.convert("RGB")
        # Revisar resolución para gran formato
        w_cm = w_orig / (DPI_POR_SERVICIO["LONA"] / 2.54)
        h_cm = h_orig / (DPI_POR_SERVICIO["LONA"] / 2.54)
        # Simular conversión CMYK (solo visual, PIL no tiene CMYK real sin plugin)
        enhancer = ImageEnhance.Color(img_proc)
        img_proc = enhancer.enhance(0.95)  # Reducir saturación ligeramente (CMYK tiene menos gamut)
        nombre_salida = f"{nombre_base}_LONA_{ts}.jpg"
        formato_salida = "JPEG"
        detalles = [
            f"Dimensiones actuales: {w_orig}x{h_orig}px",
            f"Tamaño estimado en impresión: {w_cm:.0f}cm x {h_cm:.0f}cm a 150 DPI",
            "Saturación ajustada para simulación CMYK",
            "Formato JPG alta calidad listo para plotter de lona"
        ]
        recom = [
            f"Para lona de 1m x 1m necesitas mínimo 394x394px a 100 DPI",
            "Agrega 3-5mm de sangría antes de enviar a imprenta",
            "Si el diseño tiene texto, verifica que los márgenes sean >= 1cm",
            "Pide 'prueba de color' antes de imprimir tiraje grande"
        ]

    # ── NEON ─────────────────────────────────────────────────────────────────
    elif servicio == "NEON":
        img_proc = img.convert("L")
        img_proc = img_proc.filter(ImageFilter.FIND_EDGES)    # Detectar bordes
        img_proc = ImageOps.autocontrast(img_proc)
        img_proc = img_proc.point(lambda x: 255 if x > 30 else 0)  # Umbral limpio
        nombre_salida = f"{nombre_base}_NEON_CONTORNO_{ts}.png"
        formato_salida = "PNG"
        detalles = [
            "Contornos extraídos del diseño original",
            "Umbral aplicado para líneas limpias",
            "Listo para trazar con flexo de neón",
        ]
        recom = [
            "Este archivo muestra los trazos sugeridos para el neón",
            "Vectoriza en Illustrator o Inkscape antes de la fabricación",
            "El grosor del tubo de neón suele ser 10-12mm, ajusta el trazo",
            "Para diseños complejos, simplifica curvas a mínimo 5cm de radio"
        ]

    # ── GENERAL ──────────────────────────────────────────────────────────────
    else:
        img_proc = img.convert("RGB")
        enhancer = ImageEnhance.Sharpness(img_proc)
        img_proc = enhancer.enhance(1.3)
        nombre_salida = f"{nombre_base}_OPTIMIZADO_{ts}.jpg"
        formato_salida = "JPEG"
        detalles = ["Nitidez mejorada", "Formato optimizado para uso general"]
        recom = []

    # ── Guardar ───────────────────────────────────────────────────────────────
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_salida)
    if formato_salida == "JPEG":
        if hasattr(img_proc, 'mode') and img_proc.mode == "RGBA":
            img_proc = img_proc.convert("RGB")
        img_proc.save(ruta_salida, format="JPEG", quality=95,
                      dpi=(DPI_POR_SERVICIO[servicio], DPI_POR_SERVICIO[servicio]))
    else:
        img_proc.save(ruta_salida, format="PNG",
                      dpi=(DPI_POR_SERVICIO[servicio], DPI_POR_SERVICIO[servicio]))

    return {
        "ok":       True,
        "salida":   ruta_salida,
        "servicio": servicio,
        "detalles": detalles,
        "recomendaciones": recom,
        "tamanio_original": f"{w_orig}x{h_orig}px",
        "dpi": DPI_POR_SERVICIO[servicio],
    }


def _eliminar_fondo_blanco(img: Image.Image, umbral: int = 240) -> Image.Image:
    """Elimina píxeles blancos/casi blancos convirtiéndolos en transparentes."""
    img = img.convert("RGBA")
    data = img.getdata()
    nueva_data = []
    for pixel in data:
        r, g, b, a = pixel
        if r >= umbral and g >= umbral and b >= umbral:
            nueva_data.append((r, g, b, 0))  # transparente
        else:
            nueva_data.append(pixel)
    img.putdata(nueva_data)
    return img


def analizar_imagen(ruta: str) -> dict:
    """Analiza una imagen y sugiere el servicio más adecuado."""
    try:
        img = Image.open(ruta)
        w, h = img.size
        modo = img.mode
        es_escala_grises = modo in ["L", "LA"]
        tiene_transparencia = modo == "RGBA"

        sugerencias = []
        if es_escala_grises:
            sugerencias.append("LASER (la imagen ya está en grises, ideal para grabado)")
        if tiene_transparencia:
            sugerencias.append("DTF (tiene fondo transparente, perfecto para textiles)")
        if w > 3000 or h > 3000:
            sugerencias.append("LONA (alta resolución, buena para impresión gran formato)")
        if not sugerencias:
            sugerencias = ["SUBLIMACION", "DTF", "LASER"]

        return {
            "ok": True,
            "dimensiones": f"{w}x{h}px",
            "modo_color": modo,
            "sugerencias": sugerencias,
            "mensaje": f"Imagen de {w}x{h}px. Servicios sugeridos: {', '.join(sugerencias)}"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

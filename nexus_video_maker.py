import os
import random
import time
import json

# MoviePy tiene diferencias fuertes entre v1 y v2.
# Mantenemos compatibilidad sin romper el import del core.
MOVIEPY_AVAILABLE = True
try:
    # MoviePy v2
    from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, TextClip
except Exception:
    try:
        # MoviePy v1
        from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, TextClip
    except Exception:
        MOVIEPY_AVAILABLE = False

import nexus_db

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_SOURCE = r"C:\NEXUS\VIDEOS_PARA_SUBIR"
OUTPUT_DIR = r"C:\NEXUS\PRODUCCION_LISTA"
ASSETS_DIR = os.path.join(BASE_DIR, "ASSETS")

class VideoMaker:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(ASSETS_DIR, exist_ok=True)
        self.history_file = os.path.join(BASE_DIR, "CONFIG", "video_history.json")
        self.history = self._load_history()

    def _load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    return json.load(f)
        except: pass
        return []

    def _save_history(self, filename):
        self.history.append(filename)
        # Guardar solo últimos 500 para no saturar
        if len(self.history) > 500: self.history.pop(0)
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f)
        except: pass

    def get_random_source(self):
        """Busca un video válido NO USADO RECIENTEMENTE"""
        candidates = []
        for root, dirs, files in os.walk(VIDEO_SOURCE):
            for f in files:
                if f.lower().endswith(('.mp4', '.mov', '.avi')):
                    # Evitar repetidos
                    if f not in self.history:
                        candidates.append(os.path.join(root, f))
        
        # Si ya usamos todos, reciclar el más antiguo (reset parcial)
        if not candidates:
            print("[VIDEO] Alerta: Ya usamos todos los videos. Reciclando.")
            self.history = [] # Reset drástico o estrategia circular
            return self.get_random_source() # Reintentar
            
        return random.choice(candidates)

    def create_promo(self, product_name="Lupas Aozoom", promo_text="PRECIO INSTALADOR DISPONIBLE"):
        """Crea un video corto promocional automáticamente"""
        if not MOVIEPY_AVAILABLE:
            return "MoviePy no está disponible en este Python. No puedo editar video en este momento."

        source_path = self.get_random_source()
        if not source_path:
            return "No encontré videos fuente en C:\\NEXUS\\VIDEOS_PARA_SUBIR"

        try:
            filename_source = os.path.basename(source_path)
            
            def _subclip_any(c, s, e):
                # v2: subclipped ; v1: subclip
                if hasattr(c, "subclipped"):
                    return c.subclipped(s, e)
                return c.subclip(s, e)

            def _with_duration_any(c, d):
                if hasattr(c, "with_duration"):
                    return c.with_duration(d)
                return c.set_duration(d)

            def _with_position_any(c, pos):
                if hasattr(c, "with_position"):
                    return c.with_position(pos)
                return c.set_position(pos)

            def _with_opacity_any(c, op):
                if hasattr(c, "with_opacity"):
                    return c.with_opacity(op)
                return c.set_opacity(op)

            def _resize_height_any(c, h):
                if hasattr(c, "resized"):
                    return c.resized(height=h)
                return c.resize(height=h)

            def _with_start_any(c, s):
                if hasattr(c, "with_start"):
                    return c.with_start(s)
                return c.set_start(s)

            # Cargar video
            clip = VideoFileClip(source_path)
            duration = min(clip.duration, 30) # Máximo 30 seg para Reels
            
            # Cortar un pedazo aleatorio (o el inicio si es corto)
            start = 0
            if clip.duration > 30:
                start = random.uniform(0, clip.duration - 30)
            
            subclip = _subclip_any(clip, start, start + duration)
            
            # --- CAPA 1: MARCA DE AGUA (CANBUSFIX) ---
            # Si no hay logo, usar texto
            logo_path = os.path.join(ASSETS_DIR, "logo_canbus.png")
            if os.path.exists(logo_path):
                logo = ImageClip(logo_path)
                logo = _with_duration_any(logo, duration)
                logo = _with_position_any(logo, ("right", "top"))
                logo = _resize_height_any(logo, 100)
                logo = _with_opacity_any(logo, 0.8)
            else:
                # Texto elegante como logo
                logo = TextClip(text="CANBUSFIX", font="Arial-Bold", font_size=50, color='white', bg_color='black')
                logo = _with_duration_any(logo, duration)
                logo = _with_position_any(logo, ("right", "top"))
                logo = _with_opacity_any(logo, 0.7)

            # --- CAPA 2: GANCHO INFERIOR (CTA) ---
            cta_text = f"¿ERES INSTALADOR?\n{promo_text}\nREGÍSTRATE EN CANBUSFIX.COM"
            cta = TextClip(text=cta_text, font="Arial-Bold", font_size=40, color='yellow', stroke_color='black', stroke_width=2)
            cta = _with_duration_any(cta, duration)
            cta = _with_position_any(cta, ("center", "bottom"))
            
            # --- CAPA 3: TEXTO PRODUCTO (SUPERIOR IZQ) ---
            prod_title = TextClip(text=product_name.upper(), font="Arial-Bold", font_size=60, color='white', stroke_color='black', stroke_width=3)
            prod_title = _with_duration_any(prod_title, 5)
            prod_title = _with_position_any(prod_title, ("left", "top"))
            prod_title = _with_start_any(prod_title, 1) # Aparece al segundo 1
            
            # Componer
            final = CompositeVideoClip([subclip, logo, cta, prod_title])
            
            # Exportar
            filename = f"PROMO_{product_name.replace(' ', '_')}_{int(time.time())}.mp4"
            out_path = os.path.join(OUTPUT_DIR, filename)
            
            final.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=24, preset="medium", threads=4)
            
            # Al final, registrar uso
            self._save_history(filename_source)
            
            return f"Video creado: {out_path}"

        except Exception as e:
            return f"Error editando video: {e}"

# Instancia
maker = VideoMaker()

if __name__ == "__main__":
    # Prueba
    print(maker.create_promo("Lupas X1", "5 PARES A PRECIO DE COSTO"))

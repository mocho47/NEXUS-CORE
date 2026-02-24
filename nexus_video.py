import os
import json
import subprocess
import shutil
import sys
from datetime import datetime

# Configuración por defecto
CONFIG_FILE = r"C:\NEXUS\CONFIG\video_profiles.json"
LOG_FILE = r"C:\NEXUS\nexus_video.log"
ASSETS_DIR = r"C:\NEXUS\ASSETS"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

class NexusVideoEditor:
    def __init__(self):
        self.config = self.load_config()
        self.ffmpeg_exe = self.find_ffmpeg()
        
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            log(f"ERROR: No se encontró archivo de configuración en {CONFIG_FILE}")
            return {}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log(f"ERROR: Fallo al leer config: {e}")
            return {}

    def find_ffmpeg(self):
        # 1. Check config override
        cfg_path = self.config.get("global_settings", {}).get("ffmpeg_path", "auto")
        if cfg_path != "auto" and os.path.exists(cfg_path):
            return cfg_path
            
        # 2. Check system PATH
        path_ffmpeg = shutil.which("ffmpeg")
        if path_ffmpeg:
            return path_ffmpeg
            
        # 3. Check C:\NEXUS local
        local_ffmpeg = r"C:\NEXUS\ffmpeg.exe"
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
            
        log("CRITICAL: FFmpeg no encontrado. Por favor instale FFmpeg o colóquelo en C:\\NEXUS")
        return None

    def get_profiles(self):
        return self.config.get("profiles", {})

    def process_video(self, input_path, profile_name):
        if not self.ffmpeg_exe:
            log("ABORT: FFmpeg no disponible.")
            return False

        profile = self.get_profiles().get(profile_name)
        if not profile:
            log(f"ERROR: Perfil '{profile_name}' no encontrado.")
            return False

        output_dir = profile.get("output_dir")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, f"PROCESSED_{profile_name}_{filename}")

        log(f"Iniciando procesamiento de {filename} con perfil {profile_name}...")
        
        # --- LOGICA DE EDICION ---
        # 1. Definir Assets
        watermark_img = None
        if profile_name == "ATF_REVIVAL":
            watermark_img = os.path.join(ASSETS_DIR, "atf_logo.png")
        elif profile_name == "CANBUSFIX_VIRAL":
            watermark_img = os.path.join(ASSETS_DIR, "canbusfix_logo.png")
            intro_video = os.path.join(ASSETS_DIR, "intro_community.mp4")
            outro_video = os.path.join(ASSETS_DIR, "outro_subscribe.mp4")

        # 2. Construir Comando FFmpeg
        # Estrategia: Normalizar a 1280x720 (HD) para evitar errores de escala
        
        cmd = [self.ffmpeg_exe, "-y", "-i", input_path]
        
        filter_complex = ""
        
        if profile_name == "ATF_REVIVAL" and os.path.exists(watermark_img):
            # Solo Watermark (Bottom Right)
            cmd.extend(["-i", watermark_img])
            # Scale video to 720p, Overlay watermark at W-w-10:H-h-10
            filter_complex = "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2[main];[main][1:v]overlay=W-w-10:H-h-10"
            cmd.extend(["-filter_complex", filter_complex])
            
        elif profile_name == "CANBUSFIX_VIRAL" and os.path.exists(intro_video) and os.path.exists(outro_video):
            # Intro + Main + Outro (No watermark for now to keep it simple, or add later)
            cmd.extend(["-i", intro_video, "-i", outro_video])
            
            # Complex Concat: Scale all to 1280x720 setsar=1
            # [0:v] Intro, [1:v] Main, [2:v] Outro
            filter_complex = (
                "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1,setsar=1[v0];"
                "[0:a]anull[a0];" # Dummy audio check if needed, assumming intro has audio
                "[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1,setsar=1[v1];"
                "[1:a]anull[a1];" # Assuming main has audio
                "[2:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1,setsar=1[v2];"
                "[2:a]anull[a2];"
                "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]"
            )
            # Nota: Si los videos no tienen audio, esto fallará. 
            # Para producción real, se necesita un análisis previo con ffprobe.
            # Por ahora, asumiremos que tienen audio. Si falla, usaré un fallback simple.
            
            # Simplificación: Solo concatenar video visualmente si el audio es complejo
            # O usar una estrategia segura: Convertir todo a formato intermedio.
            
            # ESTRATEGIA SEGURA V1: Solo Watermark para probar potencia
            if os.path.exists(watermark_img):
                 cmd = [self.ffmpeg_exe, "-y", "-i", input_path, "-i", watermark_img]
                 filter_complex = "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2[main];[main][1:v]overlay=10:10" # Top Left
                 cmd.extend(["-filter_complex", filter_complex])
        
        else:
            # Fallback: Copia simple
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])

        cmd.append(output_path)
        
        try:
            log(f"Ejecutando renderizado...")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log(f"EXITO: Video guardado en {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            log(f"ERROR FFmpeg: {e}")
            return False

    def run_batch(self, profile_name):
        profile = self.get_profiles().get(profile_name)
        if not profile:
            log(f"Perfil {profile_name} no existe.")
            return

        input_dir = profile.get("input_dir")
        if not os.path.exists(input_dir):
            log(f"Directorio de entrada no existe: {input_dir}")
            return

        videos = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
        log(f"Procesando {len(videos)} videos del perfil {profile_name}...")
        
        for video in videos:
            full_path = os.path.join(input_dir, video)
            self.process_video(full_path, profile_name)

if __name__ == "__main__":
    editor = NexusVideoEditor()
    if len(sys.argv) > 1:
        profile = sys.argv[1] # Ej: python nexus_video.py ATF_REVIVAL
        editor.run_batch(profile)
    else:
        print("Uso: python nexus_video.py [NOMBRE_PERFIL]")
        print("Perfiles disponibles: ATF_REVIVAL, CANBUSFIX_VIRAL")

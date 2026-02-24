from nexus_authorization import authorizer
import subprocess
import os
import logging
import math
from datetime import datetime

class VideoProcessor:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.logger = logging.getLogger("NexusV2.VideoProcessor")
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def get_video_duration(self, file_path):
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            self.logger.error(f"Error getting duration for {file_path}: {e}")
            return None

    def process_video(self, file_path, segment_duration=60, enhance=True):
        if not authorizer.request_permission("Procesar video individual", f"Archivo: {file_path}"):
            print("[NEXUS] Acción de procesamiento de video denegada por el usuario.")
            return False
        """
        Process a video file:
        1. Enhance quality (denoise, sharpen, color correction)
        2. Segment into shorter clips for social media
        """
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        self.logger.info(f"Processing video: {filename}")
        
        # 1. Enhance Video (Optional but recommended)
        enhanced_path = file_path
        if enhance:
            enhanced_path = os.path.join(self.output_folder, f"{name}_enhanced{ext}")
            self.logger.info(f"Enhancing video quality: {filename} -> {enhanced_path}")
            try:
                # FFmpeg filters for enhancement:
                # - hqdn3d: High quality denoise
                # - unsharp: Sharpening
                # - eq: Slight contrast/saturation boost
                filters = "hqdn3d=1.5:1.5:6:6,unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.1:saturation=1.1"
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", file_path,
                    "-vf", filters,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "copy",
                    enhanced_path
                ]
                subprocess.run(cmd, check=True)
                self.logger.info("Enhancement complete.")
            except Exception as e:
                self.logger.error(f"Enhancement failed: {e}. Proceeding with original file.")
                enhanced_path = file_path

        # 2. Segment Video
        duration = self.get_video_duration(enhanced_path)
        if not duration:
            self.logger.error("Could not determine video duration. Skipping segmentation.")
            return

        if duration <= segment_duration:
            self.logger.info(f"Video is short enough ({duration}s). No segmentation needed.")
            return

        self.logger.info(f"Segmenting video ({duration}s) into {segment_duration}s clips...")
        try:
            # Segment format: VideoName_Part001.mp4
            segment_pattern = os.path.join(self.output_folder, f"{name}_Part%03d{ext}")
            
            cmd = [
                "ffmpeg", "-y",
                "-i", enhanced_path,
                "-c", "copy",
                "-map", "0",
                "-segment_time", str(segment_duration),
                "-f", "segment",
                "-reset_timestamps", "1",
                segment_pattern
            ]
            subprocess.run(cmd, check=True)
            self.logger.info("Segmentation complete.")
            
            # Cleanup enhanced temp file if it was created just for segmentation
            if enhance and enhanced_path != file_path:
                # Optional: Keep enhanced file or delete? 
                # For now, let's keep it as "Master Enhanced"
                pass
                
        except Exception as e:
            self.logger.error(f"Segmentation failed: {e}")

    def process_batch(self):
        if not authorizer.request_permission("Procesar lote de videos", "Procesamiento masivo de videos en carpeta"):
            print("[NEXUS] Acción de procesamiento por lote denegada por el usuario.")
            return False
        """Process all videos in the input folder."""
        video_extensions = {".mp4", ".mov", ".avi", ".mkv"}
        files = [f for f in os.listdir(self.input_folder) if os.path.splitext(f)[1].lower() in video_extensions]
        
        self.logger.info(f"Found {len(files)} videos to process.")
        
        for f in files:
            full_path = os.path.join(self.input_folder, f)
            self.process_video(full_path)

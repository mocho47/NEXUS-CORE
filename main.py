import time
import sys
import logging
import threading

# Local imports
from logger_service import LoggerService
from config_manager import ConfigManager
from error_handler import ErrorHandler
from system_monitor import SystemMonitor
from performance_manager import PerformanceManager
from activity_manager import ActivityManager
from voice_service import VoiceService
from installer import AutoInstaller

class NexusApp:
    def __init__(self):
        # 1. Init Logger
        self.logger_service = LoggerService()
        self.logger = self.logger_service.get_logger("NexusV2.9.SuperAdmin")
        self.logger.info("Initializing Nexus V2.9 (SuperAdmin Edition)...")

        # 2. Check Dependencies
        self.installer = AutoInstaller()
        if not self.installer.install_dependencies():
            self.logger.critical("Failed to install dependencies. Exiting.")
            sys.exit(1)

        # 3. Init Core Services
        try:
            self.config = ConfigManager()
            self.error_handler = ErrorHandler()
            self.error_handler.register_global_exception_handler()
            
            self.monitor = SystemMonitor()
            self.perf_manager = PerformanceManager(self.config, self.monitor)
            self.activity_manager = ActivityManager(self.config)
            
            # 4. Init Voice Service
            # Pasamos self.handle_voice_command que esta definido mas abajo
            self.voice_service = VoiceService(command_callback=self.handle_voice_command)
            
            self.running = True
            self.logger.info("All services initialized successfully.")
        except Exception as e:
            self.logger.critical(f"Initialization failed: {e}")
            sys.exit(1)

    def handle_voice_command(self, text):
        """Procesa comandos de voz detectados."""
        if "nexus" in text:
            self.logger.info(f"Command received: {text}")
            
            if "escanea a samantha" in text or "analiza a samantha" in text:
                self.activity_manager.scan_target("Samantha")
            elif "estado" in text:
                self.voice_service.speak("Sistemas operativos. Monitoreo activo. Modo Super Admin activado.")
            elif (
                "sistema" in text or "memoria" in text or "estatus" in text or
                "se traba" in text or "se está trabando" in text or "se congela" in text or
                "esta lento" in text or "está lento" in text or "va lento" in text or
                "se alenta" in text or "anda lento" in text
            ):
                metrics = self.monitor.get_system_metrics() or {}
                ram = metrics.get("memory_usage")
                cpu = metrics.get("cpu_usage")
                disk = metrics.get("disk_usage")

                # Optimización suave (GC) si excede umbral configurado
                opt_result = self.perf_manager.check_and_optimize() or {}

                msg = ""
                if isinstance(ram, (int, float)) and isinstance(cpu, (int, float)):
                    msg = f"Uso actual: RAM {int(ram)} por ciento. CPU {int(cpu)} por ciento."
                    if isinstance(disk, (int, float)):
                        msg += f" Disco {int(disk)} por ciento."
                else:
                    msg = "Entendido. Revisé el sistema, pero no pude leer métricas completas."

                if opt_result.get("status") == "optimized":
                    saved = opt_result.get("memory_saved_percent")
                    if isinstance(saved, (int, float)) and saved > 0:
                        msg += f" Optimicé memoria: bajó {saved} por ciento."
                    else:
                        msg += " Intenté optimizar memoria."

                # Recomendación corta
                if isinstance(ram, (int, float)) and ram >= 90:
                    msg += " Recomendación: cierra apps pesadas (Chrome/Corel) y vuelve a intentar."
                elif isinstance(cpu, (int, float)) and cpu >= 90:
                    msg += " Recomendación: espera a que termine el proceso pesado o cierra lo que está consumiendo."

                self.voice_service.speak(msg)
            elif "apagar" in text:
                self.voice_service.speak("Apagando sistemas Nexus.")
                self.stop()
            elif "ayuda" in text or "comandos" in text:
                self.voice_service.speak("Comandos disponibles: Estado, Apagar, y el protocolo Samantha.")

    def background_monitoring(self):
        """Background thread for system monitoring."""
        self.logger.info("ACTIVATING PROTOCOL: Paranormal Activity Detection (SuperAdmin v2.9)...")
        while self.running:
            try:
                # Record metrics
                self.monitor.record_metrics()
                
                # Check performance
                opt_result = self.perf_manager.check_and_optimize()
                if opt_result and opt_result.get("status") == "optimized":
                    self.logger.info(f"Optimization triggered: {opt_result}")

                # Activity Scan (Nexus V2.9 Feature)
                self.activity_manager.detect_activity()

                # Sleep interval from config (default 60s)
                time.sleep(10) 
            except Exception as e:
                self.error_handler.handle_error(e, recovery_action="continue_monitoring")
                time.sleep(5)

    def run(self):
        """Main application loop."""
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.background_monitoring, daemon=True)
        monitor_thread.start()

        # Start Voice Listening
        self.voice_service.start_listening()

        self.logger.info("Nexus V2.9 (SuperAdmin) is watching. Press Ctrl+C to stop.")
        self.logger.info("--- LISTA DE FUNCIONES ACTIVAS ---")
        self.logger.info("1. Monitoreo de Sistema (CPU/RAM/Disco)")
        self.logger.info("2. Anti-Suspension (Modo Insomnio)")
        self.logger.info("3. Deteccion de Actividad Paranormal")
        self.logger.info("4. Escucha Activa (Comando: 'Nexus...')")
        self.logger.info("----------------------------------")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping Nexus V2.9...")
            self.stop()

    def stop(self):
        self.running = False
        if hasattr(self, 'voice_service'):
            self.voice_service.stop()
        self.logger.info("Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    app = NexusApp()
    app.run()

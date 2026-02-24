from nexus_authorization import authorizer
import psutil
import sqlite3
import logging
import time
from datetime import datetime

class SystemMonitor:
    def __init__(self, db_path="nexus_v2.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("NexusV2.SystemMonitor")

    def get_system_metrics(self):
        """Capture current system metrics."""
        if not authorizer.request_permission("Leer métricas del sistema", "Lectura de CPU, RAM, disco y procesos"):
            self.logger.warning("[NEXUS] Acción de lectura de métricas denegada por el usuario.")
            return None
        try:
            cpu = psutil.cpu_percent(interval=None) # Non-blocking if called periodically
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            process_count = len(psutil.pids())
            
            return {
                "cpu_usage": cpu,
                "memory_usage": memory,
                "disk_usage": disk,
                "process_count": process_count
            }
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return None

    def record_metrics(self):
        """Get metrics and save to database."""
        if not authorizer.request_permission("Grabar métricas del sistema", "Registro de métricas en base de datos"):
            self.logger.warning("[NEXUS] Acción de grabación de métricas denegada por el usuario.")
            return None
        metrics = self.get_system_metrics()
        if not metrics:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (cpu_usage, memory_usage, disk_usage, process_count)
                VALUES (?, ?, ?, ?)
            ''', (metrics['cpu_usage'], metrics['memory_usage'], metrics['disk_usage'], metrics['process_count']))
            conn.commit()
            conn.close()
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to record metrics to DB: {e}")
            return metrics

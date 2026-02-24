from nexus_authorization import authorizer
import sqlite3
import os
import logging
from datetime import datetime

class ConfigManager:
    def __init__(self, db_path="nexus_v2.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("NexusV2.ConfigManager")
        self._init_db()

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Configuration Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuration (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Error Log Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_type VARCHAR(50) NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    recovery_action VARCHAR(100),
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')

            # System Metrics Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    process_count INTEGER NOT NULL
                )
            ''')
            
            # Insert default values if not exists
            defaults = [
                ('max_memory_usage', '95', 'Porcentaje máximo de uso de memoria antes de optimización'),
                ('cpu_threshold', '90', 'Umbral de CPU para alertas'),
                ('log_retention_days', '30', 'Días de retención de logs'),
                ('auto_optimize', 'true', 'Activar optimización automática'),
                ('app_mode', 'production', 'Modo de ejecución: production o debug')
            ]
            
            for key, val, desc in defaults:
                cursor.execute('''
                    INSERT OR IGNORE INTO configuration (key, value, description) 
                    VALUES (?, ?, ?)
                ''', (key, val, desc))
            
            conn.commit()
            conn.close()
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to initialize database: {e}")
            raise

    def get_config(self, key: str, default=None):
        if not authorizer.request_permission("Leer configuración", f"Clave: {key}"):
            print("[NEXUS] Acción de lectura de configuración denegada por el usuario.")
            return default
        """Retrieve a configuration value."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM configuration WHERE key=?", (key,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else default
        except Exception as e:
            self.logger.error(f"Error reading config '{key}': {e}")
            return default

    def set_config(self, key: str, value: str):
        if not authorizer.request_permission("Modificar configuración", f"Clave: {key}, Valor: {value}"):
            print("[NEXUS] Acción de escritura de configuración denegada por el usuario.")
            return False
        """Update or set a configuration value."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO configuration (key, value, last_updated) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value=excluded.value,
                    last_updated=CURRENT_TIMESTAMP
            """, (key, str(value)))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Error setting config '{key}': {e}")
            return False

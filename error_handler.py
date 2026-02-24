import logging
import sqlite3
import traceback
import sys
from datetime import datetime

class ErrorHandler:
    def __init__(self, db_path="nexus_v2.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("NexusV2.ErrorHandler")

    def handle_error(self, error: Exception, recovery_action: str = None, fatal: bool = False):
        """
        Log an error to the database and file log.
        Returns True if handled successfully, False otherwise.
        """
        try:
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()

            # Log to console/file
            if fatal:
                self.logger.critical(f"FATAL ERROR: {error_message}")
                self.logger.critical(stack_trace)
            else:
                self.logger.error(f"Error ({error_type}): {error_message}")

            # Log to Database
            self._log_to_db(error_type, error_message, stack_trace, recovery_action)

            # TODO: Implement specific recovery actions here based on error_type or recovery_action string
            if recovery_action == "restart_service":
                self.logger.info("Attempting recovery: Restarting service...")
                # Logic to restart service
            
            return True
        except Exception as e:
            # Fallback if error handler fails
            print(f"CRITICAL: Error handler failed: {e}")
            traceback.print_exc()
            return False

    def _log_to_db(self, error_type, error_message, stack_trace, recovery_action):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_log (error_type, error_message, stack_trace, recovery_action)
                VALUES (?, ?, ?, ?)
            ''', (error_type, error_message, stack_trace, recovery_action))
            conn.commit()
            conn.close()
        except Exception as db_err:
            self.logger.error(f"Failed to log error to DB: {db_err}")

    def register_global_exception_handler(self):
        """Register this handler as the global uncaught exception handler."""
        def exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            self.handle_error(exc_value, recovery_action="global_catch", fatal=True)
        
        sys.excepthook = exception_handler
        self.logger.info("Global exception handler registered.")

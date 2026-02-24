import logging
import os
from logging.handlers import RotatingFileHandler
import sys

class LoggerService:
    def __init__(self, log_dir="logs", app_name="NexusV2"):
        self.log_dir = log_dir
        self.app_name = app_name
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with rotation and console output."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.DEBUG)

        # File Handler (Rotating)
        log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}.log")
        # 5 MB per file, max 5 backup files
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # Add handlers
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        logger.info("Logger service initialized.")

    @staticmethod
    def get_logger(name):
        return logging.getLogger(name)

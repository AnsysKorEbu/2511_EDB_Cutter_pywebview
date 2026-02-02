"""
Simple logger module for standalone stackup extractor.
No external dependencies - uses standard Python logging.
"""

import logging
import sys
from pathlib import Path


class SimpleLogger:
    """Simple logging wrapper with console and file output."""

    def __init__(self, name="StackupExtractor", log_file=None, level=logging.INFO):
        """
        Initialize logger.

        Args:
            name (str): Logger name
            log_file (str, optional): Path to log file. If None, only console output
            level (int): Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(console_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message):
        """Log error message."""
        self.logger.error(message)

    def critical(self, message):
        """Log critical message."""
        self.logger.critical(message)


# Global logger instance
logger = SimpleLogger()

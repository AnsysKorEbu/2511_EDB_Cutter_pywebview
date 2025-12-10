# <2025> ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited
import os
import logging
import argparse
from config import get_timestamped_folder
import colorama

colorama.init()


class ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\033[94m', 'INFO': '\033[37m', 'WARNING': '\033[93m', 'ERROR': '\033[91m',
              'CRITICAL': '\033[41m'}
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"


def setup_shared_logger(log_file_path=None, logger_name='shared_process_logger'):
    """Setup logger that can be shared across processes"""

    # Use provided log file path or create default one
    if log_file_path is None:
        save_folder = get_timestamped_folder()
        os.makedirs(save_folder, exist_ok=True)
        log_file_path = os.path.join(save_folder, 'process.log')
    else:
        # Ensure directory exists for provided path
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Get or create logger with specified name
    logger = logging.getLogger(logger_name)

    # Only setup handlers if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # File handler for persistent logging
        fh = logging.FileHandler(log_file_path, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Console handler for real-time feedback
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatters
        plain_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        color_fmt = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')

        fh.setFormatter(plain_fmt)
        ch.setFormatter(color_fmt)

        logger.addHandler(fh)
        logger.addHandler(ch)

        logger.propagate = False

    return logger, log_file_path


def get_logger_from_args():
    """Get logger configured from command line arguments"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--log-file', help='Shared log file path')
    parser.add_argument('--logger-name', default='shared_process_logger', help='Logger name')

    # Parse known args to avoid conflicts with main script arguments
    args, unknown = parser.parse_known_args()

    # Only setup logger if log file path is provided (subprocess mode)
    if args.log_file:
        logger, log_file_path = setup_shared_logger(args.log_file, args.logger_name)
        return logger
    else:
        # Return None to indicate no logger setup (will use default)
        return None


def get_default_logger():
    """Get default logger for main process"""
    logger, log_file_path = setup_shared_logger()
    return logger, log_file_path


def get_console_only_logger():
    """Get logger that only outputs to console (no file)"""
    logger = logging.getLogger('console_only_logger')

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Only console handler, no file handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        color_fmt = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(color_fmt)

        logger.addHandler(ch)
        logger.propagate = False

    return logger


# Try to get logger from command line args first (for subprocess)
# If no args provided, use console-only logger for subprocess or default for main process
try:
    subprocess_logger = get_logger_from_args()
    if subprocess_logger:
        logger = subprocess_logger
    else:
        # Check if we're likely in a subprocess (no GUI elements)
        import sys

        if '--log-file' in sys.argv or '--excel-file' in sys.argv:
            # Subprocess mode but no log file provided - use console only
            logger = get_console_only_logger()
        else:
            # Main process mode - use default with file
            logger, _ = get_default_logger()
except:
    logger, _ = get_default_logger()
# config_functions.py
"""
Configuration helper functions for stackup processing.
Provides functions to access configuration settings and file paths.
"""
from pathlib import Path
from util.logger_module import logger


def get_excel_file_rawdata(config=None):
    """
    Get path to rawdata Excel file

    Args:
        config: StackupConfig instance (optional)

    Returns:
        str: Path to rawdata.xlsx file, or None if not found
    """
    if config and hasattr(config, 'excel_file') and config.excel_file:
        return config.excel_file

    # Default: look in stackup folder
    default_path = Path(__file__).parent.parent / 'rawdata.xlsx'

    if default_path.exists():
        return str(default_path)

    logger.warning(f"Rawdata file not found at {default_path}")
    return None


def get_height_column_from_config(config=None):
    """
    Get height column setting from config

    Args:
        config: StackupConfig instance (optional)

    Returns:
        int: Column number for height data (default: 94)
    """
    if config and hasattr(config, 'height_column'):
        return config.height_column
    return 94  # Default value

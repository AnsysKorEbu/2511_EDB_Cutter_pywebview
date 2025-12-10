# config.py
"""
Configuration management for stackup processing.
Provides StackupConfig class for flexible configuration and settings management.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from util.logger_module import logger


class StackupConfig:
    """
    Configuration for stackup processing

    Args:
        base_folder (str or Path, optional): Base folder for results. Defaults to 'Results'
        excel_file (str or Path, optional): Path to Excel stackup file
        height_column (int, optional): Column number for height data. Defaults to 94
    """

    def __init__(self, base_folder=None, excel_file=None, height_column=94):
        """Initialize StackupConfig"""
        # Set base folder
        if base_folder:
            self.base_folder = Path(base_folder)
        else:
            # Default to stackup folder's Results directory
            stackup_dir = Path(__file__).parent.parent
            self.base_folder = stackup_dir / 'Results'

        # Set Excel file
        if excel_file:
            self.excel_file = str(excel_file)
        else:
            # Default to rawdata.xlsx in stackup folder
            default_excel = Path(__file__).parent.parent / 'rawdata.xlsx'
            self.excel_file = str(default_excel) if default_excel.exists() else None

        # Set height column
        self.height_column = height_column

        # Create timestamped folder
        self._timestamped_folder = None

    @property
    def timestamped_folder(self):
        """Get or create timestamped results folder"""
        if self._timestamped_folder is None:
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._timestamped_folder = self.base_folder / current_time
        return self._timestamped_folder

    def create_timestamped_folder(self):
        """Create the timestamped folder if it doesn't exist"""
        os.makedirs(self.timestamped_folder, exist_ok=True)
        logger.info(f"Created timestamped folder: {self.timestamped_folder}")
        return self.timestamped_folder

    @classmethod
    def from_json(cls, config_file):
        """
        Load configuration from JSON file

        Args:
            config_file (str or Path): Path to JSON configuration file

        Returns:
            StackupConfig: Configuration instance

        Example JSON format:
            {
                "stackup_excel_file": "C:/path/to/rawdata.xlsx",
                "height_column": 94,
                "base_folder": "C:/path/to/Results"
            }
        """
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)

            return cls(
                base_folder=settings.get('base_folder'),
                excel_file=settings.get('stackup_excel_file'),
                height_column=settings.get('height_column', 94)
            )
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {e}")
            # Return default config
            return cls()

    def to_dict(self):
        """
        Convert configuration to dictionary

        Returns:
            dict: Configuration as dictionary
        """
        return {
            'base_folder': str(self.base_folder),
            'excel_file': self.excel_file,
            'height_column': self.height_column,
            'timestamped_folder': str(self.timestamped_folder)
        }

    def __repr__(self):
        """String representation of configuration"""
        return f"StackupConfig(excel_file='{self.excel_file}', height_column={self.height_column})"


# Module-level function for backward compatibility
def get_height_column(config=None):
    """
    Get height column setting

    Args:
        config (StackupConfig, optional): Configuration instance

    Returns:
        int: Height column number (default: 94)
    """
    if config and isinstance(config, StackupConfig):
        return config.height_column
    return 94

"""
Configuration module for standalone stackup extractor.
Simple configuration without external dependencies.
"""

import json
from pathlib import Path
from .logger import logger


class StandaloneConfig:
    """
    Simple configuration for standalone stackup extractor.

    Args:
        excel_file (str or Path, optional): Path to Excel stackup file
        height_column (int, optional): Column number for height data. Defaults to 94
    """

    def __init__(self, excel_file=None, height_column=94):
        """Initialize StandaloneConfig."""
        # Set Excel file
        if excel_file:
            self.excel_file = str(Path(excel_file).resolve())
        else:
            self.excel_file = None

        # Set height column
        self.height_column = height_column

    @classmethod
    def from_json(cls, config_file):
        """
        Load configuration from JSON file.

        Args:
            config_file (str or Path): Path to JSON configuration file

        Returns:
            StandaloneConfig: Configuration instance

        Example JSON format:
            {
                "excel_file": "C:/path/to/rawdata.xlsx",
                "height_column": 94
            }
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            return cls(
                excel_file=settings.get('excel_file'),
                height_column=settings.get('height_column', 94)
            )
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {e}")
            # Return default config
            return cls()

    def to_dict(self):
        """
        Convert configuration to dictionary.

        Returns:
            dict: Configuration as dictionary
        """
        return {
            'excel_file': self.excel_file,
            'height_column': self.height_column
        }

    def to_json(self, config_file):
        """
        Save configuration to JSON file.

        Args:
            config_file (str or Path): Path to JSON configuration file
        """
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving config to {config_file}: {e}")

    def __repr__(self):
        """String representation of configuration."""
        return f"StandaloneConfig(excel_file='{self.excel_file}', height_column={self.height_column})"


def get_height_column(config=None):
    """
    Get height column setting.

    Args:
        config (StandaloneConfig, optional): Configuration instance

    Returns:
        int: Height column number (default: 94)
    """
    if config and isinstance(config, StandaloneConfig):
        return config.height_column
    return 94

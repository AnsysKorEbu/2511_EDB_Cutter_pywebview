"""
Circuit Generator GUI Module

Provides API for loading full_touchstone_config.json files and
creating HFSS project files (.aedt) for circuit generation.
"""
import json
from pathlib import Path
from util.logger_module import logger


class CircuitApi:
    """JavaScript API for Circuit Generator GUI"""

    def __init__(self, edb_version="2025.1"):
        """
        Initialize Circuit API with empty config state.

        Args:
            edb_version: EDB version string (e.g., "2025.1")
        """
        self.edb_version = edb_version
        self.config_path = None
        self.config_data = None
        logger.info(f"Circuit Generator GUI initialized (EDB Version: {edb_version})")

    def get_recent_configs(self, limit=5):
        """
        Find most recent full_touchstone_config.json files in Results folders.

        Args:
            limit: Maximum number of configs to return

        Returns:
            dict: {'success': bool, 'configs': list, 'error': str}
                configs format: [
                    {
                        'path': 'C:/.../.../Analysis/full_touchstone_config.json',
                        'folder': 'none_port_sanitized_20260108_131715',
                        'mtime': 1704712635.123
                    },
                    ...
                ]
        """
        try:
            results_base = Path('Results')
            configs = []

            if results_base.exists():
                for result_dir in results_base.iterdir():
                    if result_dir.is_dir():
                        config_file = result_dir / 'Analysis' / 'full_touchstone_config.json'
                        if config_file.exists():
                            configs.append({
                                'path': str(config_file.absolute()),
                                'folder': result_dir.name,
                                'mtime': config_file.stat().st_mtime
                            })

            # Sort by modification time (newest first)
            configs.sort(key=lambda x: x['mtime'], reverse=True)

            limited_configs = configs[:limit]
            logger.info(f"Found {len(limited_configs)} recent config files (out of {len(configs)} total)")

            return {
                'success': True,
                'configs': limited_configs
            }

        except Exception as e:
            error_msg = f"Failed to get recent configs: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg, 'configs': []}

    def browse_config_file(self):
        """
        Open file browser to select full_touchstone_config.json file.

        Returns:
            dict: {'success': bool, 'config_path': str, 'error': str}
        """
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            # Set initial directory to Results folder if it exists
            initial_dir = Path('Results').resolve() if Path('Results').exists() else Path.cwd()

            file_path = filedialog.askopenfilename(
                title='Select full_touchstone_config.json',
                initialdir=str(initial_dir),
                filetypes=[
                    ('JSON Config Files', 'full_touchstone_config.json'),
                    ('All JSON Files', '*.json'),
                    ('All Files', '*.*')
                ]
            )

            root.destroy()

            if file_path:
                logger.info(f"Selected config file: {file_path}")
                return {'success': True, 'config_path': file_path}
            else:
                logger.info("No file selected")
                return {'success': False, 'error': 'No file selected'}

        except Exception as e:
            error_msg = f"Failed to open file browser: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def load_config(self, config_path):
        """
        Load and validate full_touchstone_config.json file.

        Args:
            config_path: Path to JSON config file (string)

        Returns:
            dict: {
                'success': bool,
                'config_data': dict,
                'metadata': {
                    'analysis_folder': str,
                    'total_files': int,
                    'version': str
                },
                'error': str
            }
        """
        try:
            config_file = Path(config_path)

            # Verify file exists
            if not config_file.exists():
                return {
                    'success': False,
                    'error': f'Config file does not exist: {config_path}'
                }

            # Load JSON
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Validate required fields
            required_fields = ['version', 'analysis_folder', 'total_files', 'merge_sequence']
            for field in required_fields:
                if field not in config_data:
                    return {
                        'success': False,
                        'error': f'Invalid config: missing required field "{field}"'
                    }

            # Store loaded config
            self.config_path = str(config_file.absolute())
            self.config_data = config_data

            # Extract metadata
            metadata = {
                'analysis_folder': config_data['analysis_folder'],
                'total_files': config_data['total_files'],
                'version': config_data['version']
            }

            logger.info(f"Loaded config: {self.config_path}")
            logger.info(f"  Analysis folder: {metadata['analysis_folder']}")
            logger.info(f"  Total files: {metadata['total_files']}")

            return {
                'success': True,
                'config_data': config_data,
                'metadata': metadata
            }

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Failed to load config: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def get_config_info(self):
        """
        Get currently loaded config data.

        Returns:
            dict: {
                'success': bool,
                'config_loaded': bool,
                'config_path': str,
                'metadata': dict,
                'error': str
            }
        """
        try:
            if not self.config_data:
                return {
                    'success': True,
                    'config_loaded': False,
                    'config_path': None,
                    'metadata': None
                }

            metadata = {
                'analysis_folder': self.config_data['analysis_folder'],
                'total_files': self.config_data['total_files'],
                'version': self.config_data['version']
            }

            return {
                'success': True,
                'config_loaded': True,
                'config_path': self.config_path,
                'metadata': metadata
            }

        except Exception as e:
            error_msg = f"Failed to get config info: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def create_hfss_project(self):
        """
        Create HFSS Circuit project.

        Calls hfss.generate_circuit module to create .aedt file.

        Returns:
            dict: {
                'success': bool,
                'aedt_file': str,
                'message': str,
                'error': str
            }
        """
        try:
            if not self.config_data:
                return {
                    'success': False,
                    'error': 'No config loaded. Please select a config file first.'
                }

            if not self.config_path:
                return {
                    'success': False,
                    'error': 'Config path not available.'
                }

            # Call HFSS module to generate circuit
            from hfss.generate_circuit import generate_circuit

            logger.info(f"\n[Circuit Generator GUI] Calling HFSS module...")
            logger.info(f"  Config: {self.config_path}")
            logger.info(f"  Version: {self.edb_version}")

            result = generate_circuit(self.config_path, self.edb_version)

            if result['success']:
                aedt_file = Path(result['aedt_file'])
                return {
                    'success': True,
                    'aedt_file': result['aedt_file'],
                    'message': f'HFSS Circuit project created!\n\nFile: {aedt_file.name}\nLocation: {aedt_file.parent}\n\nVersion: {self.edb_version}'
                }
            else:
                return result

        except Exception as e:
            error_msg = f"Failed to create HFSS project: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
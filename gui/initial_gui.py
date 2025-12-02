"""
Initial GUI for EDB Cutter - Settings Configuration
"""
import os
import json
import webview
from pathlib import Path
from util.logger_module import logger


class InitialApi:
    """API for Initial Settings GUI"""

    def __init__(self):
        self._window = None
        self.settings = {}

    def set_window(self, window):
        """Store window reference for file dialogs"""
        self._window = window

    def load_previous_settings(self):
        """
        Load previous settings from config/settings.json
        Returns: Settings dict or empty dict if not found
        """
        try:
            config_file = Path(__file__).parent.parent / 'config' / 'settings.json'

            if not config_file.exists():
                return {}

            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            return settings
        except Exception as e:
            logger.warning(f"Failed to load previous settings: {e}")
            return {}

    def get_ansys_versions(self):
        """
        Detect installed ANSYS versions from environment variables
        Returns: dict of {version: install_path}
        Example: {'2023.2': 'C:\\Program Files\\...', '2025.1': '...'}
        """
        versions = {}
        for key, value in os.environ.items():
            if key.startswith('ANSYSEM_ROOT'):
                try:
                    # Extract version code: ANSYSEM_ROOT232 -> '232'
                    version_code = key.replace('ANSYSEM_ROOT', '')

                    if len(version_code) == 3:
                        # Convert: 232 -> "2023.2", 251 -> "2025.1"
                        major = '20' + version_code[:2]  # "23" -> "2023"
                        minor = version_code[2:]          # "2"
                        formatted = f"{major}.{minor}"    # "2023.2"

                        versions[formatted] = value
                except Exception as e:
                    logger.info(f"Error parsing version from {key}: {e}")
                    continue

        # Sort versions in descending order (newest first)
        sorted_versions = dict(sorted(versions.items(), reverse=True))
        return sorted_versions

    def select_edb_folder(self):
        """
        Open folder dialog to select .aedb folder
        Returns: Selected .aedb folder path or None
        """
        if not self._window:
            return None

        # Set default directory to project's source folder
        source_dir = Path(__file__).parent.parent / 'source'
        if not source_dir.exists():
            source_dir = Path.cwd()

        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=str(source_dir)
        )

        if result and len(result) > 0:
            path = result[0]

            # Remove edb.def if accidentally included
            if path.endswith('edb.def'):
                path = str(Path(path).parent)

            # Ensure path doesn't have trailing slashes or backslashes
            path = path.rstrip('/\\')

            # Check if it's a .aedb folder
            if path.endswith('.aedb'):
                return path
            else:
                return None  # Not a .aedb folder

        return None

    def validate_settings(self, edb_path, version, grpc):
        """
        Validate settings according to requirements:
        - version >= 25.1 AND grpc == true

        Args:
            edb_path: Path to .aedb folder
            version: Version string (e.g., "2025.1")
            grpc: Boolean

        Returns:
            {
                'valid': bool,
                'status': 'success' | 'warning' | 'error',
                'message': str
            }
        """
        # Check EDB path
        if not edb_path:
            return {
                'valid': False,
                'status': 'error',
                'message': 'Please select an EDB path'
            }

        # Check if path exists
        if not os.path.exists(edb_path):
            return {
                'valid': False,
                'status': 'error',
                'message': f'Selected path does not exist: {edb_path}'
            }

        # Check version
        if not version:
            return {
                'valid': False,
                'status': 'error',
                'message': 'Please select an EDB version'
            }

        # Parse version and validate
        try:
            # Convert "2025.1" to 25.1 for comparison
            parts = version.split('.')
            year = int(parts[0])
            release = int(parts[1])
            version_num = float(f"{year - 2000}.{release}")

            # Check: version >= 25.1 AND grpc == true
            if version_num >= 25.1 and grpc:
                return {
                    'valid': True,
                    'status': 'success',
                    'message': '✓ Configuration is valid and ready to proceed'
                }
            else:
                # Build detailed message
                issues = []
                if version_num < 25.1:
                    issues.append(f'version {version} < 25.1')
                if not grpc:
                    issues.append('gRPC is disabled')

                return {
                    'valid': False,
                    'status': 'warning',
                    'message': f'TBD: Requires version >= 25.1 with gRPC enabled ({", ".join(issues)})'
                }

        except Exception as e:
            return {
                'valid': False,
                'status': 'error',
                'message': f'Invalid version format: {version}'
            }

    def save_settings(self, edb_path, version, grpc, overwrite):
        """
        Save settings to config/settings.json

        Args:
            edb_path: Path to .aedb folder
            version: Version string
            grpc: Boolean
            overwrite: Boolean

        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # Prepare settings
            settings = {
                'edb_path': edb_path,
                'edb_version': version,
                'grpc': grpc,
                'overwrite': overwrite
            }

            # Create config directory if not exists
            config_dir = Path(__file__).parent.parent / 'config'
            config_dir.mkdir(exist_ok=True)

            # Save to file
            config_file = config_dir / 'settings.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            # Store settings for retrieval
            self.settings = settings

            return {
                'success': True,
                'message': f'Settings saved to {config_file}'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error saving settings: {str(e)}'
            }

    def close_window(self):
        """Close the initial GUI window"""
        if self._window:
            self._window.destroy()


def start_initial_gui():
    """
    Start the Initial Settings GUI
    Returns: Settings dict if saved, None if cancelled
    """
    api = InitialApi()

    # Get HTML file path
    html_file = Path(__file__).parent / 'initial' / 'index.html'

    if not html_file.exists():
        logger.info(f"Error: Initial GUI HTML not found at {html_file}")
        return None

    # Create window
    window = webview.create_window(
        'EDB Cutter - Initial Setup',
        html_file.as_uri(),
        js_api=api,
        width=650,
        height=750,
        resizable=True
    )

    # Set window reference in API
    api.set_window(window)

    # Start GUI
    webview.start()

    # Return settings if saved
    if api.settings:
        return api.settings
    else:
        return None


if __name__ == '__main__':
    """Test the initial GUI"""
    settings = start_initial_gui()
    if settings:
        logger.info("Settings saved:")
        print(json.dumps(settings, indent=2))
    else:
        logger.info("Settings not saved (cancelled)")

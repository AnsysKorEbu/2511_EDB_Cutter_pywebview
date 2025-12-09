"""
Stackup Settings GUI API

Backend API for the stackup settings window.
Provides JavaScript-callable methods for file browsing, Excel analysis,
cut management, and configuration saving.
"""

import os
import json
from pathlib import Path
from typing import Dict, List
from util.logger_module import logger

# Import stackup modules
from stackup.section_parser import extract_section_names
from stackup.stackup_config import (
    load_stackup_config,
    save_stackup_config,
    get_section_for_cut,
    validate_config,
    get_all_cut_ids
)


class StackupSettingsApi:
    """
    JavaScript API for Stackup Settings window.

    This class provides methods that can be called from JavaScript via pywebview's
    js_api bridge. All methods return dictionaries with 'success' field.
    """

    def __init__(self, edb_folder_path: str):
        """
        Initialize Stackup Settings API.

        Args:
            edb_folder_path: Path to .aedb folder (e.g., "source/design.aedb")
        """
        self.edb_folder_path = str(edb_folder_path)
        self.config = load_stackup_config(edb_folder_path)

        logger.info(f"Initialized StackupSettingsApi for: {edb_folder_path}")

        if self.config:
            logger.info(f"Loaded existing config with {len(self.config.get('cut_stackup_mapping', {}))} mappings")

    def browse_excel_file(self) -> Dict:
        """
        Open file browser to select Excel stackup file.

        Uses tkinter filedialog (similar to analysis_gui.py browse_results_folder).

        Returns:
            {
                'success': bool,
                'file_path': str,  # Absolute path to selected file
                'error': str       # Error message if failed (only if success=False)
            }
        """
        try:
            # Import tkinter for file dialog
            from tkinter import Tk, filedialog

            logger.info("Opening file browser for Excel selection")

            # Create hidden Tk window
            root = Tk()
            root.withdraw()  # Hide main window
            root.attributes('-topmost', True)  # Bring dialog to front

            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Stackup Excel File",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("All Files", "*.*")
                ],
                initialdir=str(Path.cwd())  # Start in current directory
            )

            root.destroy()

            if file_path:
                logger.info(f"User selected file: {file_path}")
                return {
                    'success': True,
                    'file_path': file_path
                }
            else:
                logger.info("User cancelled file selection")
                return {
                    'success': False,
                    'file_path': '',
                    'error': 'File selection cancelled'
                }

        except Exception as e:
            error_msg = f"Failed to open file browser: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'file_path': '',
                'error': error_msg
            }

    def analyze_excel_file(self, excel_path: str) -> Dict:
        """
        Extract section names from selected Excel file.

        Args:
            excel_path: Path to Excel file

        Returns:
            {
                'success': bool,
                'sections': List[str],  # Available section names (e.g., ["C/N 1", "C/N 1-1"])
                'file_path': str,
                'error': str            # Error message if failed (only if success=False)
            }
        """
        try:
            logger.info(f"Analyzing Excel file: {excel_path}")

            # Use section parser to extract sections
            result = extract_section_names(excel_path)

            if result['success']:
                logger.info(f"Successfully extracted {len(result['sections'])} sections")
            else:
                logger.warning(f"Failed to extract sections: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            error_msg = f"Failed to analyze Excel file: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'sections': [],
                'file_path': excel_path,
                'error': error_msg
            }

    def get_available_cuts(self) -> Dict:
        """
        Get list of saved cuts for current EDB folder.

        Reads cut JSON files from <edb_folder>/cut/ directory.

        Returns:
            {
                'success': bool,
                'cuts': List[Dict],  # List of cut info dicts
                'error': str         # Error message if failed (only if success=False)
            }

        Cut info dict structure:
            {
                'id': 'cut_001',
                'type': 'polygon',
                'timestamp': '2025-12-03T17:39:47.635564'
            }
        """
        try:
            cuts_dir = Path(self.edb_folder_path) / "cut"

            if not cuts_dir.exists():
                logger.warning(f"Cuts directory not found: {cuts_dir}")
                return {
                    'success': True,
                    'cuts': []
                }

            cuts_list = []

            # Read all cut_*.json files
            for json_file in sorted(cuts_dir.glob("cut_*.json")):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        cut_data = json.load(f)

                    # Extract relevant info
                    cut_info = {
                        'id': cut_data.get('id', json_file.stem),
                        'type': cut_data.get('type', 'unknown'),
                        'timestamp': cut_data.get('timestamp', '')
                    }
                    cuts_list.append(cut_info)

                except Exception as e:
                    logger.warning(f"Failed to read cut file {json_file}: {e}")
                    continue

            logger.info(f"Found {len(cuts_list)} cuts in {cuts_dir}")

            return {
                'success': True,
                'cuts': cuts_list
            }

        except Exception as e:
            error_msg = f"Failed to get available cuts: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'cuts': [],
                'error': error_msg
            }

    def get_current_config(self) -> Dict:
        """
        Get current stackup configuration.

        Returns:
            {
                'excel_file': str,              # Path to Excel file
                'cut_stackup_mapping': Dict,    # Cut ID -> section name mapping
                'has_config': bool              # True if config file exists
            }
        """
        try:
            if self.config:
                return {
                    'excel_file': self.config.get('excel_file', ''),
                    'cut_stackup_mapping': self.config.get('cut_stackup_mapping', {}),
                    'has_config': True
                }
            else:
                return {
                    'excel_file': '',
                    'cut_stackup_mapping': {},
                    'has_config': False
                }

        except Exception as e:
            logger.error(f"Failed to get current config: {e}")
            return {
                'excel_file': '',
                'cut_stackup_mapping': {},
                'has_config': False
            }

    def save_configuration(self, excel_file: str, mapping: Dict) -> Dict:
        """
        Save stackup configuration to file.

        Args:
            excel_file: Path to Excel file
            mapping: Dict of cut_id -> section_name
                    Example: {'cut_001': 'C/N 1', 'cut_002': 'C/N 1-1'}

        Returns:
            {
                'success': bool,
                'config_path': str,     # Path where config was saved
                'saved_mappings': int,  # Number of mappings saved
                'error': str            # Error message if failed (only if success=False)
            }
        """
        try:
            logger.info(f"Saving stackup configuration...")
            logger.info(f"  Excel file: {excel_file}")
            logger.info(f"  Mappings: {len(mapping)}")

            # Prepare config data
            config_data = {
                'excel_file': excel_file,
                'cut_stackup_mapping': mapping
            }

            # Validate configuration
            available_cuts = get_all_cut_ids(self.edb_folder_path)
            validation = validate_config(config_data, available_cuts)

            if not validation['valid']:
                error_msg = f"Invalid configuration: {', '.join(validation['errors'])}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'config_path': '',
                    'saved_mappings': 0,
                    'error': error_msg
                }

            # Log warnings (non-critical)
            for warning in validation['warnings']:
                logger.warning(warning)

            # Save configuration
            result = save_stackup_config(self.edb_folder_path, config_data)

            if result['success']:
                # Update internal config
                self.config = config_data

                return {
                    'success': True,
                    'config_path': result['config_path'],
                    'saved_mappings': len(mapping)
                }
            else:
                return {
                    'success': False,
                    'config_path': result.get('config_path', ''),
                    'saved_mappings': 0,
                    'error': result.get('error', 'Unknown error')
                }

        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'config_path': '',
                'saved_mappings': 0,
                'error': error_msg
            }

    def export_stackup_data(self) -> Dict:
        """
        Export stackup data from currently selected Excel file.

        Opens a file save dialog for the user to choose export location,
        then extracts stackup data and exports it to a formatted Excel file.

        Returns:
            {
                'success': bool,
                'output_path': str,        # Path to exported file (if successful)
                'rows_exported': int,      # Number of data rows (if successful)
                'error': str               # Error message (if failed)
            }
        """
        try:
            # Check if Excel file has been selected and analyzed
            if not self.config or not self.config.get('excel_file'):
                logger.warning("Export attempted without selecting Excel file")
                return {
                    'success': False,
                    'error': 'No Excel file selected. Please analyze an Excel file first.'
                }

            source_excel = self.config['excel_file']
            logger.info(f"Exporting stackup data from: {source_excel}")

            # Import tkinter for file save dialog
            from tkinter import Tk, filedialog
            from datetime import datetime

            # Create hidden Tk window
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            # Generate default filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"stackup_export_{timestamp}.xlsx"

            # Open file save dialog
            output_path = filedialog.asksaveasfilename(
                title="Export Stackup Data",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                initialfile=default_filename
            )

            root.destroy()

            # Check if user cancelled
            if not output_path:
                logger.info("Export cancelled by user")
                return {
                    'success': False,
                    'error': 'Export cancelled by user'
                }

            # Perform export using stackup_exporter module
            from stackup.stackup_exporter import export_stackup_to_excel

            result = export_stackup_to_excel(source_excel, output_path)

            if result['success']:
                logger.info(f"Successfully exported to: {result['output_path']}")
            else:
                logger.error(f"Export failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            error_msg = f"Unexpected error during export: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    def close(self) -> Dict:
        """
        Close the stackup settings window.

        Returns:
            {'success': bool}
        """
        try:
            import webview
            # Close all webview windows
            for window in webview.windows:
                window.destroy()
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to close window: {e}")
            return {'success': False, 'error': str(e)}

    def validate_mapping(self, mapping: Dict) -> Dict:
        """
        Validate cut-section mapping before saving.

        Args:
            mapping: Dict of cut_id -> section_name

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        try:
            # Create temporary config for validation
            temp_config = {
                'excel_file': 'dummy.xlsx',  # Placeholder for validation
                'cut_stackup_mapping': mapping
            }

            # Get available cuts
            available_cuts = get_all_cut_ids(self.edb_folder_path)

            # Validate
            return validate_config(temp_config, available_cuts)

        except Exception as e:
            logger.error(f"Failed to validate mapping: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }


if __name__ == "__main__":
    # Test the API
    import sys

    print("="*60)
    print("Stackup Settings GUI API - Test")
    print("="*60)

    # Test with example EDB folder
    if len(sys.argv) > 1:
        test_edb_folder = sys.argv[1]
    else:
        test_edb_folder = "source/none_port_design.aedb"

    print(f"\nTest EDB folder: {test_edb_folder}\n")

    # Initialize API
    api = StackupSettingsApi(test_edb_folder)

    # Test 1: Get current config
    print("[Test 1] Getting current config...")
    config = api.get_current_config()
    print(f"  Has config: {config['has_config']}")
    print(f"  Excel file: {config.get('excel_file', 'N/A')}")
    print(f"  Mappings: {len(config.get('cut_stackup_mapping', {}))}")

    # Test 2: Get available cuts
    print("\n[Test 2] Getting available cuts...")
    cuts_result = api.get_available_cuts()
    if cuts_result['success']:
        print(f"  Found {len(cuts_result['cuts'])} cuts:")
        for cut in cuts_result['cuts']:
            print(f"    - {cut['id']} ({cut['type']})")

    # Test 3: Analyze Excel file (if it exists)
    test_excel = Path(__file__).parent / "rawdata.xlsx"
    if test_excel.exists():
        print(f"\n[Test 3] Analyzing Excel file: {test_excel}")
        analysis = api.analyze_excel_file(str(test_excel))
        if analysis['success']:
            print(f"  Sections found: {len(analysis['sections'])}")
            for i, section in enumerate(analysis['sections'], 1):
                print(f"    {i}. {section}")
        else:
            print(f"  Error: {analysis.get('error', 'Unknown')}")

    print("\n" + "="*60)

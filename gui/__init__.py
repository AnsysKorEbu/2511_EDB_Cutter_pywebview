"""
GUI module for EDB Cutter using pywebview
"""
import json
import re
import subprocess
import sys
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import webview

from config import (
    BATCH_FILE_PREFIX,
    CUT_FILE_PATTERN,
    CUT_ID_FORMAT,
    DEFAULT_EDB_VERSION,
    RESULTS_DIR,
    SOURCE_DIR,
    STACKUP_DIR,
    VALID_CUT_NAME_PATTERN,
    error_response,
    success_response,
)
from util.logger_module import logger


class Api:
    """JavaScript API for pywebview"""

    def __init__(self, edb_path, edb_version=DEFAULT_EDB_VERSION, grpc=False):
        self.edb_path = edb_path
        self.edb_version = edb_version
        self.grpc = grpc
        self.data = None

        # Extract EDB folder name from path
        if edb_path and edb_path != "test_path":
            edb_path_obj = Path(edb_path)
            # If path ends with edb.def, get parent folder name
            if edb_path_obj.name == 'edb.def' or edb_path_obj.suffix == '.aedb':
                if edb_path_obj.suffix == '.aedb':
                    self.edb_folder_name = edb_path_obj.name
                else:
                    self.edb_folder_name = edb_path_obj.parent.name
            else:
                self.edb_folder_name = edb_path_obj.name

            self._edb_data_dir = SOURCE_DIR / self.edb_folder_name
        else:
            # Test mode - use default source folder
            self.edb_folder_name = "test_data"
            self._edb_data_dir = SOURCE_DIR

    def _ensure_data_loaded(self):
        """
        Helper method to ensure EDB data is loaded into cache.

        This method is called by all data retrieval methods to lazily load
        EDB data only when needed, avoiding redundant loads.
        """
        if self.data is None:
            from edb.edb_saver import load_all_edb_data
            logger.info(f"Loading EDB data from {self._edb_data_dir}...")
            self.data = load_all_edb_data(str(self._edb_data_dir))

    def test_function(self):
        """Test function called from JavaScript"""
        return f"Hello from Python! EDB Path: {self.edb_path} (Folder: {self.edb_folder_name})"

    def load_edb_data(self):
        """Load EDB data from source folder"""
        try:
            from edb.edb_saver import load_all_edb_data

            logger.info(f"Loading EDB data from {self._edb_data_dir}...")
            self.data = load_all_edb_data(str(self._edb_data_dir))

            return {
                'planes': len(self.data['planes']) if self.data['planes'] else 0,
                'traces': len(self.data['traces']) if self.data['traces'] else 0,
                'components': len(self.data['components']) if self.data['components'] else 0,
                'vias': len(self.data['vias']) if self.data['vias'] else 0
            }
        except Exception as e:
            logger.info(f"Error loading data: {e}")
            return {'error': str(e)}

    def get_planes_data(self):
        """Get planes data for rendering"""
        try:
            self._ensure_data_loaded()
            return self.data.get('planes', [])
        except Exception as e:
            logger.error(f"Error getting planes data: {e}")
            return []

    def get_vias_data(self):
        """Get vias data for rendering"""
        try:
            self._ensure_data_loaded()
            return self.data.get('vias', [])
        except Exception as e:
            logger.error(f"Error getting vias data: {e}")
            return []

    def get_traces_data(self):
        """Get traces data for rendering"""
        try:
            self._ensure_data_loaded()
            return self.data.get('traces', [])
        except Exception as e:
            logger.error(f"Error getting traces data: {e}")
            return []

    def get_nets_data(self):
        """Get nets data (signal and power/ground net names)"""
        try:
            self._ensure_data_loaded()
            return self.data.get('nets', {'signal': [], 'power': []})
        except Exception as e:
            logger.error(f"Error getting nets data: {e}")
            return {'signal': [], 'power': []}

    def save_cut_data(self, cut_data):
        """Save cut geometry data to EDB-specific cut folder"""
        try:
            cut_dir = self._edb_data_dir / 'cut'
            cut_dir.mkdir(parents=True, exist_ok=True)

            # Generate cut ID based on existing files
            existing_files = list(cut_dir.glob(CUT_FILE_PATTERN))
            cut_id = CUT_ID_FORMAT.format(len(existing_files) + 1)

            # Add metadata
            cut_data['id'] = cut_id
            cut_data['timestamp'] = datetime.now().isoformat()
            cut_data['edb_folder'] = self.edb_folder_name

            # Save to JSON file
            cut_file = cut_dir / f"{cut_id}.json"
            with open(cut_file, 'w', encoding='utf-8') as f:
                json.dump(cut_data, f, indent=2)

            logger.info(f"Cut data saved: {cut_file}")
            return success_response(id=cut_id, file=str(cut_file))
        except Exception as e:
            logger.error(f"Error saving cut data: {e}")
            return error_response(e)

    def get_cut_list(self):
        """Get list of saved cut files"""
        try:
            cut_dir = self._edb_data_dir / 'cut'
            if not cut_dir.exists():
                return []

            cuts = []
            # Changed from 'cut_*.json' to '*.json' to support renamed cuts
            for cut_file in sorted(cut_dir.glob('*.json')):
                # Skip batch files (temporary files used for execution)
                if cut_file.name.startswith(BATCH_FILE_PREFIX):
                    continue

                try:
                    with open(cut_file, 'r', encoding='utf-8') as f:
                        cut_data = json.load(f)

                    # Calculate point count from points array
                    points = cut_data.get('points', [])
                    point_count = len(points) if isinstance(points, list) else 0

                    cuts.append({
                        'id': cut_data.get('id', cut_file.stem),
                        'type': cut_data.get('type', 'unknown'),
                        'timestamp': cut_data.get('timestamp', ''),
                        'point_count': point_count,
                        'filename': cut_file.name
                    })
                except Exception as e:
                    logger.info(f"Error reading {cut_file}: {e}")

            return cuts
        except Exception as e:
            logger.info(f"Error getting cut list: {e}")
            return []

    def delete_cut(self, cut_id):
        """Delete a cut file"""
        try:
            cut_dir = self._edb_data_dir / 'cut'
            cut_file = cut_dir / f"{cut_id}.json"

            if cut_file.exists():
                cut_file.unlink()
                logger.info(f"Deleted cut: {cut_file}")
                return success_response()
            else:
                return error_response('File not found')
        except Exception as e:
            logger.error(f"Error deleting cut: {e}")
            return error_response(e)

    def rename_cut(self, old_id, new_id):
        """Rename a cut file"""
        try:
            # Validate new name format (alphanumeric + underscore only)
            if not re.match(VALID_CUT_NAME_PATTERN, new_id):
                return error_response('Invalid name format. Only letters, numbers, and underscores allowed.')

            # Check if old_id and new_id are the same
            if old_id == new_id:
                return success_response(message='Name unchanged')

            cut_dir = self._edb_data_dir / 'cut'
            old_file = cut_dir / f"{old_id}.json"
            new_file = cut_dir / f"{new_id}.json"

            # Check if old file exists
            if not old_file.exists():
                return error_response('Original cut file not found')

            # Check if new name already exists
            if new_file.exists():
                return error_response(f'Cut name "{new_id}" already exists')

            # Load cut data
            with open(old_file, 'r', encoding='utf-8') as f:
                cut_data = json.load(f)

            # Update id in data
            cut_data['id'] = new_id

            # Save to new file
            with open(new_file, 'w', encoding='utf-8') as f:
                json.dump(cut_data, f, indent=2)

            # Delete old file
            old_file.unlink()

            logger.info(f"Renamed cut: {old_id} -> {new_id}")
            return success_response(new_id=new_id)

        except Exception as e:
            logger.error(f"Error renaming cut: {e}")
            return error_response(e)

    def get_cut_data(self, cut_id):
        """Get full data for a specific cut"""
        try:
            cut_dir = self._edb_data_dir / 'cut'
            cut_file = cut_dir / f"{cut_id}.json"

            if cut_file.exists():
                with open(cut_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            logger.info(f"Error loading cut data: {e}")
            return None

    def execute_cuts(self, cut_ids, selected_nets=None, use_stackup=True):
        """
        Execute cutting operations on EDB using selected cut geometries.

        This runs edb.cut module in a subprocess to avoid pythonnet conflicts.
        Multiple cuts are processed in a single subprocess session, with each cut
        opening the original EDB independently.

        Args:
            cut_ids: List of cut IDs to execute (e.g., ["cut_001", "cut_002"])
            selected_nets: Dict with 'signal' and 'power' lists of net names
                          (e.g., {'signal': ['NET1', 'NET2'], 'power': ['GND']})
            use_stackup: Boolean flag to enable/disable stackup application (default: True)

        Returns:
            dict: {'success': bool, 'error': str (if failed)}
        """
        try:
            # Ensure cut_ids is a list
            if isinstance(cut_ids, str):
                cut_ids = [cut_ids]

            if not cut_ids:
                return error_response('No cut IDs provided')

            # Get cut directory
            cut_dir = self._edb_data_dir / 'cut'

            # Validate all cut files exist and build file paths
            cut_files = []
            for cut_id in cut_ids:
                cut_file = cut_dir / f"{cut_id}.json"
                if not cut_file.exists():
                    return error_response(f'Cut file not found: {cut_id}')
                cut_files.append(str(cut_file.resolve()))

            logger.info(f"\n{'=' * 70}")
            logger.info(f"Executing cuts: {', '.join(cut_ids)}")
            logger.info(f"{'=' * 70}")

            # Debug logging for selected nets
            logger.debug(f"Received selected_nets parameter: {selected_nets}")
            if selected_nets:
                logger.debug(f"Signal nets count: {len(selected_nets.get('signal', []))}")
                logger.debug(f"Power nets count: {len(selected_nets.get('power', []))}")
                if selected_nets.get('signal'):
                    logger.debug(f"Signal nets: {selected_nets.get('signal')}")
            logger.info("")

            # Create batch JSON file with cut file paths, selected nets, and stackup flag
            batch_data = {
                'mode': 'batch',
                'cut_files': cut_files,
                'selected_nets': selected_nets if selected_nets else {'signal': [], 'power': []},
                'use_stackup': use_stackup
            }

            # Create temporary batch file in source folder
            SOURCE_DIR.mkdir(exist_ok=True)
            batch_filename = f"{BATCH_FILE_PREFIX}{int(time.time() * 1000)}.json"
            batch_file_path = SOURCE_DIR / batch_filename

            with open(batch_file_path, 'w', encoding='utf-8') as batch_file:
                json.dump(batch_data, batch_file, indent=2)

            try:
                # Run edb.cut package as subprocess with batch file
                grpc_str = "True" if self.grpc else "False"
                result = subprocess.run(
                    [sys.executable, "-u", "-m", "edb.cut", self.edb_path, self.edb_version, batch_file_path, grpc_str],
                    cwd=Path.cwd()
                )

                return_code = result.returncode

                if return_code != 0:
                    error_msg = f"Cut execution failed with code {return_code}"
                    logger.error(f"{error_msg}")
                    return error_response(error_msg)

                count = len(cut_ids)
                success_msg = f"{count} cut{'s' if count > 1 else ''} executed successfully!"
                logger.info(f"\n[OK] {success_msg}\n")

                # Get results folder path for analysis GUI
                # The subprocess creates Results/{edb_name}_{timestamp}/ folder
                # Find the most recently modified folder in Results/
                results_folder = None
                if RESULTS_DIR.exists():
                    # Get all subdirectories in Results/
                    result_dirs = [d for d in RESULTS_DIR.iterdir() if d.is_dir()]
                    if result_dirs:
                        # Sort by modification time and get the most recent
                        latest_dir = max(result_dirs, key=lambda d: d.stat().st_mtime)
                        results_folder = str(latest_dir)
                        logger.debug(f"Results folder for analysis: {results_folder}")

                return success_response(results_folder=results_folder)

            finally:
                # Clean up temporary batch file
                try:
                    Path(batch_file_path).unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up batch file: {cleanup_error}")

        except Exception as e:
            error_msg = f"Failed to execute cuts: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return error_response(e, error_msg)

    def browse_results_folder_for_analysis(self):
        """
        Open folder browser to select a Results folder for analysis.

        Returns:
            dict: {'success': bool, 'folder': str, 'error': str}
        """
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            # Set initial directory to Results folder if it exists
            initial_dir = RESULTS_DIR.resolve() if RESULTS_DIR.exists() else Path.cwd()

            folder_path = filedialog.askdirectory(
                title='Select Results Folder for Analysis',
                initialdir=str(initial_dir)
            )

            root.destroy()

            if folder_path:
                logger.info(f"Selected folder for analysis: {folder_path}")
                return {'success': True, 'folder': folder_path}
            else:
                logger.info("[INFO] No folder selected")
                return {'success': False, 'error': 'No folder selected'}

        except Exception as e:
            error_msg = f"Failed to open folder browser: {str(e)}"
            logger.error(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def launch_analysis_gui_window(self, results_folder):
        """
        Launch analysis GUI as a separate subprocess (non-blocking).

        This avoids Path object serialization issues by launching
        the Analysis GUI in a completely separate process.

        Args:
            results_folder: Path to Results/{name}_{timestamp}/ folder (as string)

        Returns:
            dict: {'success': bool}
        """
        try:
            logger.info(f"\n[INFO] Launching Analysis GUI as subprocess")
            logger.info(f"Results folder: {results_folder}")
            logger.info(f"EDB Version: {self.edb_version}")
            logger.info(f"gRPC Mode: {self.grpc}")

            # Launch analysis GUI via edb.analysis.gui_launcher with edb_version and grpc
            grpc_str = "True" if self.grpc else "False"
            subprocess.Popen(
                [sys.executable, "-m", "edb.analysis.gui_launcher", str(results_folder), self.edb_version, grpc_str],
                cwd=Path.cwd()
            )

            logger.info("[OK] Analysis GUI subprocess launched")
            return {'success': True}

        except Exception as e:
            error_msg = f"Failed to launch Analysis GUI: {str(e)}"
            logger.info(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def launch_schematic_gui_window(self, analysis_folder=None):
        """
        Launch Schematic GUI (Full Touchstone Generator) as subprocess.

        Args:
            analysis_folder: Optional path to Analysis folder (as string)

        Returns:
            dict: {'success': bool, 'error': str}
        """
        try:
            logger.info(f"\n[INFO] Launching Schematic GUI as subprocess")
            logger.info(f"EDB Version: {self.edb_version}")
            if analysis_folder:
                logger.info(f"Analysis folder: {analysis_folder}")

            # Build command args: [analysis_folder] [edb_version]
            cmd_args = [sys.executable, "-m", "schematic.gui_launcher"]
            if analysis_folder:
                cmd_args.append(str(analysis_folder))
            cmd_args.append(self.edb_version)

            subprocess.Popen(cmd_args, cwd=Path.cwd())

            logger.info("[OK] Schematic GUI subprocess launched")
            return {'success': True}

        except Exception as e:
            error_msg = f"Failed to launch Schematic GUI: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def launch_circuit_gui_window(self):
        """
        Launch Circuit Generator GUI (HFSS) as subprocess.

        Returns:
            dict: {'success': bool, 'error': str}
        """
        try:
            logger.info(f"\n[INFO] Launching Circuit Generator GUI as subprocess")
            logger.info(f"EDB Version: {self.edb_version}")

            # Launch circuit GUI via gui.circuit_launcher with edb_version
            subprocess.Popen(
                [sys.executable, "-m", "gui.circuit_launcher", self.edb_version],
                cwd=Path.cwd()
            )

            logger.info("[OK] Circuit Generator GUI subprocess launched")
            return {'success': True}

        except Exception as e:
            error_msg = f"Failed to launch Circuit Generator GUI: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def process_stackup(self):
        """
        Process PCB stackup data from Excel file.

        Extracts layer materials, heights, and Dk/Df values using the stackup module.

        Returns:
            dict: {'success': bool, 'summary': dict, 'error': str (if failed)}
        """
        try:
            from stackup import StackupProcessor

            logger.info(f"\n{'=' * 70}")
            logger.info("Processing stackup data")
            logger.info(f"{'=' * 70}")

            # Create processor (uses default rawdata.xlsx in stackup folder)
            processor = StackupProcessor()

            # Get layer data and summary
            summary = processor.get_stackup_summary()

            logger.info(f"Stackup processed successfully:")
            logger.info(f"  - Total layers: {summary['total_layers']}")
            logger.info(f"  - Total height: {summary['total_height']}um")
            logger.info(f"  - Materials: {', '.join(summary['materials'])}")
            logger.info(f"{'=' * 70}\n")

            return {
                'success': True,
                'summary': summary
            }

        except Exception as e:
            error_msg = f"Failed to process stackup: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def browse_excel_for_sections(self):
        """
        Open file dialog to select Excel file and extract sections.

        Returns:
            dict: {
                'success': bool,
                'excel_file': str (absolute path),
                'sections': list of str,
                'error': str (if failed)
            }
        """
        try:
            from stackup.section_selector import extract_sections_from_excel

            # Create hidden tkinter root window
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)

            # Set initial directory to stackup folder if it exists
            initial_dir = STACKUP_DIR if STACKUP_DIR.exists() else Path.cwd()

            # Open file dialog
            excel_file = filedialog.askopenfilename(
                title="Select Excel File for Section Extraction",
                initialdir=str(initial_dir),
                filetypes=[
                    ("Excel Files", "*.xlsx"),
                    ("All Files", "*.*")
                ]
            )

            # Clean up tkinter
            root.destroy()

            # Check if user canceled
            if not excel_file:
                return {'success': False, 'error': 'File selection canceled'}

            # Extract sections
            logger.info(f"Extracting sections from: {excel_file}")
            sections = extract_sections_from_excel(excel_file)

            logger.info(f"Extracted {len(sections)} sections: {sections}")

            return {
                'success': True,
                'excel_file': excel_file,
                'sections': sections
            }

        except FileNotFoundError as e:
            error_msg = f"Excel file not found: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            return {'success': False, 'error': error_msg}

        except Exception as e:
            error_msg = f"Failed to browse/extract sections: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def get_cuts_for_section_selection(self):
        """
        Get list of available cuts for current EDB.

        Returns:
            dict: {
                'success': bool,
                'cuts': list of cut metadata,
                'edb_folder': str
            }
        """
        try:
            # Reuse existing get_cut_list logic
            cuts = self.get_cut_list()

            logger.info(f"Found {len(cuts)} cuts for section selection")

            return {
                'success': True,
                'cuts': cuts,
                'edb_folder': self.edb_folder_name
            }

        except Exception as e:
            error_msg = f"Failed to get cuts: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def get_latest_sss_file(self):
        """
        Get the latest SSS file from source/{edb_name}/sss/ folder.

        Returns:
            dict: {
                'success': bool,
                'sss_file': str (absolute path) or None,
                'error': str (if failed)
            }
        """
        try:
            # Check sss directory
            sss_dir = self._edb_data_dir / 'sss'

            if not sss_dir.exists():
                return {'success': True, 'sss_file': None}

            # Find all *_sections_*.sss files
            sss_files = list(sss_dir.glob('*_sections_*.sss'))

            if not sss_files:
                return {'success': True, 'sss_file': None}

            # Get the most recent file by modification time
            latest_sss = max(sss_files, key=lambda p: p.stat().st_mtime)

            logger.info(f"Found latest SSS file: {latest_sss}")

            return {
                'success': True,
                'sss_file': str(latest_sss)
            }

        except Exception as e:
            error_msg = f"Failed to get latest SSS file: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def browse_sss_file(self):
        """
        Open file dialog to select existing SSS file from sss folder.

        Returns:
            dict: {
                'success': bool,
                'sss_file': str (absolute path),
                'error': str (if failed)
            }
        """
        try:
            # Create hidden tkinter root window
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)

            # Set initial directory to source/{edb_folder_name}/sss/
            sss_dir = self._edb_data_dir / 'sss'
            initial_dir = sss_dir if sss_dir.exists() else self._edb_data_dir

            # Open file dialog
            sss_file = filedialog.askopenfilename(
                title="Load SSS File",
                initialdir=str(initial_dir),
                filetypes=[
                    ("SSS Files", "*_sections_*.sss"),
                    ("All Files", "*.*")
                ]
            )

            # Clean up tkinter
            root.destroy()

            # Check if user canceled
            if not sss_file:
                return {'success': False, 'error': 'File selection cancelled'}

            logger.info(f"Loaded SSS file: {sss_file}")

            return {
                'success': True,
                'sss_file': sss_file
            }

        except Exception as e:
            error_msg = f"Failed to browse SSS file: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def close_main_window(self):
        """
        Close the main EDB Cutter window.

        Returns:
            dict: {'success': bool}
        """
        try:
            # Get all active windows and close the first one (current window)
            windows = webview.windows
            if windows:
                logger.info("Closing main window...")
                windows[0].destroy()
                return {'success': True}
            else:
                logger.warning("No active window found to close")
                return {'success': False, 'error': 'No active window'}

        except Exception as e:
            error_msg = f"Failed to close window: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def save_section_selection(self, excel_file, cut_section_mapping):
        """
        Save cut-section mapping and layer data to .sss files.

        Args:
            excel_file (str): Path to Excel file used
            cut_section_mapping (dict): Mapping of cut IDs to sections (1:1)
                Example: {'cut_001': 'RIGID 5', 'cut_002': 'C/N 1'}

        Returns:
            dict: {
                'success': bool,
                'sss_file': str (path to section mapping file),
                'layer_file': str (path to layer data file),
                'error': str (if failed)
            }
        """
        try:
            from stackup.section_selector import SectionSelector, generate_sss_filename, generate_layer_filename

            logger.info(f"\n{'=' * 70}")
            logger.info("Saving section selection and layer data")
            logger.info(f"Excel file: {excel_file}")
            logger.info(f"Cut-section mapping: {cut_section_mapping}")
            logger.info(f"{'=' * 70}")

            # Create SectionSelector instance
            selector = SectionSelector(excel_file)

            # Validate mapping
            is_valid, errors = selector.validate_mapping(cut_section_mapping)
            if not is_valid:
                error_msg = f"Invalid mapping: {', '.join(errors)}"
                logger.error(f"\n[ERROR] {error_msg}")
                return {'success': False, 'error': error_msg}

            # Create output path in source/{edb_name}/sss/ directory
            sss_dir = self._edb_data_dir / 'sss'
            sss_dir.mkdir(parents=True, exist_ok=True)

            # Generate .sss filenames
            sss_filename = generate_sss_filename(self.edb_folder_name)
            layer_filename = generate_layer_filename(self.edb_folder_name)

            sss_file_path = sss_dir / sss_filename
            layer_file_path = sss_dir / layer_filename

            # Save section mapping
            selector.save_section_mapping(cut_section_mapping, str(sss_file_path))
            logger.info(f"Section mapping saved: {sss_file_path}")

            # Save layer data
            selector.save_layer_data(cut_section_mapping, str(layer_file_path))
            logger.info(f"Layer data saved: {layer_file_path}")

            logger.info(f"Section selection completed successfully:")
            logger.info(f"  - Section file: {sss_file_path}")
            logger.info(f"  - Layer file: {layer_file_path}")
            logger.info(f"  - Cuts: {len(cut_section_mapping)}")
            logger.info(f"{'=' * 70}\n")

            return {
                'success': True,
                'sss_file': str(sss_file_path),
                'layer_file': str(layer_file_path)
            }

        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            return {'success': False, 'error': error_msg}

        except Exception as e:
            error_msg = f"Failed to save section selection: {str(e)}"
            logger.error(f"\n[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}


def start_gui(edb_path, edb_version="2025.1", grpc=False):
    """Start the pywebview GUI"""
    api = Api(edb_path, edb_version, grpc)

    # Get HTML file path
    html_file = Path(__file__).parent / 'index.html'

    # Create window
    window = webview.create_window(
        'EDB Cutter - 2D Viewer',
        html_file.as_uri(),
        js_api=api,
        width=1200,
        height=800,
        resizable=True
    )

    # Start GUI
    webview.start()


def launch_analysis_gui(results_folder, edb_version="2025.1", grpc=False):
    """
    Launch analysis GUI window after cutting completes.

    This function is called in a separate thread from the main GUI
    to avoid blocking the cutter interface.

    Args:
        results_folder: Path to Results/{name}_{timestamp}/ folder
        edb_version: EDB version string (e.g., "2025.1")
        grpc: Use gRPC mode for analysis
    """
    from gui.analysis.analysis_gui import AnalysisApi

    # Create API instance for analysis GUI
    api = AnalysisApi(results_folder, edb_version, grpc)

    # Get HTML file path
    html_file = Path(__file__).parent / 'analysis' / 'index.html'

    # Create window
    window = webview.create_window(
        'EDB Analysis - Touchstone Generator',
        html_file.as_uri(),
        js_api=api,
        width=900,
        height=700,
        resizable=True
    )

    # Start GUI (this will block until window is closed)
    webview.start()



"""
Analysis GUI Module

JavaScript API for the Analysis GUI window.
Provides methods to discover .aedb files and run SIwave analysis.
"""
import subprocess
from pathlib import Path
from util.logger_module import logger


class AnalysisApi:
    """JavaScript API for Analysis GUI"""

    def __init__(self, results_folder, edb_version="2025.1", grpc=False):
        """
        Initialize Analysis API.

        Args:
            results_folder: Path to Results/{name}_{timestamp}/ folder
            edb_version: EDB version string (e.g., "2025.1")
            grpc: Use gRPC mode for analysis
        """
        # Store paths as strings to avoid Path object serialization issues
        self.results_folder_str = str(results_folder)
        self.edb_version = edb_version
        self.grpc = grpc
        self.aedb_files = self._discover_aedb_files()

        logger.info(f"Analysis GUI initialized")
        logger.info(f"Results folder: {self.results_folder_str}")
        logger.info(f"EDB version: {self.edb_version}")
        logger.info(f"gRPC mode: {self.grpc}")
        logger.info(f"Found {len(self.aedb_files)} .aedb files")

    def _discover_aedb_files(self):
        """
        Scan results folder for .aedb directories.

        Returns:
            list: List of .aedb file info dicts
        """
        import re
        aedb_files = []
        results_folder = Path(self.results_folder_str)

        if not results_folder.exists():
            logger.warning(f"Results folder does not exist: {results_folder}")
            return aedb_files

        # Analysis folder path
        analysis_folder = results_folder / "Analysis"

        # Find all .aedb folders
        for aedb_dir in sorted(results_folder.glob("*.aedb")):
            if aedb_dir.is_dir():
                # Get folder size (approximate)
                try:
                    total_size = sum(f.stat().st_size for f in aedb_dir.rglob('*') if f.is_file())
                except Exception as e:
                    logger.warning(f"Failed to get size for {aedb_dir.name}: {e}")
                    total_size = 0

                # Extract cut_name from aedb_name to check if analysis result exists
                output_name = aedb_dir.stem  # Remove .aedb extension
                cut_match = re.search(r'(cut_\d{3})', output_name)
                if cut_match:
                    cut_name = cut_match.group(1)
                else:
                    # Fallback: use the whole name if no cut pattern found
                    cut_name = output_name

                # Check if analysis result file exists (e.g., cut_001.s2p, cut_001.s4p, etc.)
                analyzed = False
                if analysis_folder.exists():
                    touchstone_files = list(analysis_folder.glob(f"{cut_name}.s*p"))
                    analyzed = len(touchstone_files) > 0

                aedb_files.append({
                    'name': aedb_dir.name,
                    'path': str(aedb_dir),
                    'size': total_size,
                    'analyzed': analyzed
                })

        return aedb_files

    def get_aedb_list(self):
        """
        Get list of .aedb files for frontend display.

        Returns:
            list: List of dicts with name, path, size
        """
        return self.aedb_files

    def analyze_single(self, aedb_name):
        """
        Run SIwave analysis on a single .aedb file via subprocess.

        Args:
            aedb_name: Name of .aedb folder (e.g., "design_001.aedb")

        Returns:
            dict: {'success': bool, 'output_file': str, 'error': str}
        """
        try:
            # Find the .aedb file
            results_folder = Path(self.results_folder_str)
            aedb_path = results_folder / aedb_name

            if not aedb_path.exists():
                return {
                    'success': False,
                    'error': f'.aedb folder not found: {aedb_name}'
                }

            # Extract cut_name from aedb_name (e.g., "cut_001" from "none_port_sanitized_cut_001.aedb")
            # Find "cut_XXX" pattern in the filename
            import re
            output_name = aedb_path.stem  # Remove .aedb extension
            cut_match = re.search(r'(cut_\d{3})', output_name)
            if cut_match:
                cut_name = cut_match.group(1)
            else:
                # Fallback: use the whole name if no cut pattern found
                cut_name = output_name

            # Create Analysis folder if it doesn't exist
            analysis_folder = results_folder / "Analysis"
            analysis_folder.mkdir(parents=True, exist_ok=True)

            # Generate output path for touchstone file
            # Use .snp extension (SIwave will auto-convert to .s2p, .s4p, etc. based on port count)
            output_path = analysis_folder / f"{cut_name}.snp"

            logger.info(f"{'=' * 70}")
            logger.info(f"Analyzing: {aedb_name}")
            logger.info(f"Output: {output_path}")
            logger.info(f"{'=' * 70}")

            # Run analysis subprocess
            import sys
            grpc_str = "True" if self.grpc else "False"
            result = subprocess.run(
                [
                    sys.executable,
                    "-u",
                    "-m",
                    "edb.analysis",
                    str(aedb_path),
                    self.edb_version,
                    str(output_path),
                    grpc_str
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Print subprocess output
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.error(f"[STDERR] {result.stderr}")

            if result.returncode != 0:
                error_msg = f"Analysis failed with return code {result.returncode}"
                logger.error(f"{error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'stderr': result.stderr
                }

            # Find the generated touchstone file
            # SIwave auto-determines extension and filename
            # Look for {cut_name}.s*p file in the analysis folder
            touchstone_files = list(analysis_folder.glob(f"{cut_name}.s*p"))

            if not touchstone_files:
                # No touchstone files found
                return {
                    'success': False,
                    'error': f'Touchstone file not generated in {analysis_folder}'
                }
            else:
                # Use the first (should be only one) touchstone file
                output_file = touchstone_files[0]

            logger.info(f"Analysis complete: {output_file.name}")
            logger.info("")

            return {
                'success': True,
                'output_file': str(output_file),
                'file_size': output_file.stat().st_size if output_file.exists() else 0
            }

        except Exception as e:
            error_msg = f"Failed to analyze {aedb_name}: {str(e)}"
            logger.error(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg
            }

    def analyze_all(self):
        """
        Run analysis on all .aedb files sequentially.

        This method is kept for completeness, but the frontend
        will likely call analyze_single() in a loop for better progress tracking.

        Returns:
            dict: Summary of results
        """
        results = {
            'total': len(self.aedb_files),
            'completed': 0,
            'failed': 0,
            'outputs': []
        }

        for aedb_file in self.aedb_files:
            result = self.analyze_single(aedb_file['name'])

            if result['success']:
                results['completed'] += 1
                results['outputs'].append({
                    'name': aedb_file['name'],
                    'output_file': result['output_file']
                })
            else:
                results['failed'] += 1

        return results

    def get_analysis_results(self):
        """
        Get list of generated touchstone files in Analysis folder.

        Returns:
            list: List of touchstone file info dicts
        """
        analysis_folder = Path(self.results_folder_str) / "Analysis"
        if not analysis_folder.exists():
            return []

        results = []
        for touchstone_file in sorted(analysis_folder.glob("*.s*p")):
            if touchstone_file.is_file():
                results.append({
                    'name': touchstone_file.name,
                    'path': str(touchstone_file),
                    'size': touchstone_file.stat().st_size
                })

        return results

    def browse_results_folder(self):
        """
        Open folder browser dialog to select a Results folder.

        Opens a native folder selection dialog starting from the Results directory.
        User can select any folder containing .aedb files.

        Returns:
            dict: {'success': bool, 'folder': str, 'error': str}
        """
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()  # Hide the root window
            root.attributes('-topmost', True)  # Bring dialog to front

            # Set initial directory to Results folder if it exists
            initial_dir = Path('Results').resolve() if Path('Results').exists() else Path.cwd()

            folder_path = filedialog.askdirectory(
                title='Select Results Folder (containing .aedb files)',
                initialdir=str(initial_dir)
            )

            root.destroy()

            if folder_path:
                logger.info(f"Selected folder: {folder_path}")
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

    def load_new_folder(self, folder_path):
        """
        Load .aedb files from a new results folder.

        Updates the internal state to point to the new folder and
        re-scans for .aedb files.

        Args:
            folder_path: Path to Results/{name}_{timestamp}/ folder (string)

        Returns:
            dict: {'success': bool, 'aedb_files': list, 'folder': str, 'error': str}
        """
        try:
            # Update folder path (store as string)
            self.results_folder_str = str(folder_path)

            # Verify folder exists
            results_folder = Path(self.results_folder_str)
            if not results_folder.exists():
                return {
                    'success': False,
                    'error': f'Folder does not exist: {folder_path}'
                }

            # Re-discover .aedb files in new folder
            self.aedb_files = self._discover_aedb_files()

            logger.info(f"Loaded {len(self.aedb_files)} .aedb files from: {folder_path}")

            return {
                'success': True,
                'aedb_files': self.aedb_files,
                'folder': self.results_folder_str
            }

        except Exception as e:
            error_msg = f"Failed to load folder: {str(e)}"
            logger.error(f"{error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg
            }

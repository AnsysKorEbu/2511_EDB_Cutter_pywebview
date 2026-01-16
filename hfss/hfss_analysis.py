"""
HFSS 3D Layout Analysis Module

This module provides HFSS 3D Layout analysis functionality for EDB files.
Uses Hfss3dLayout from ansys.aedt.core to open EDB files directly.
"""
import traceback
from datetime import datetime
from pathlib import Path
from util.logger_module import logger


def run_hfss_analysis(aedb_path, edb_version, output_path):
    """
    Run HFSS 3D Layout analysis on a single .aedb file.

    This function opens an EDB file using Hfss3dLayout,
    which allows direct EDB file access in HFSS 3D Layout environment.

    Args:
        aedb_path: Path to .aedb folder or edb.def file
        edb_version: Version string (e.g., "2025.2")
        output_path: Path for output file (determines Analysis folder location)

    Returns:
        dict: {
            'success': bool,
            'output_file': str (path to generated file),
            'error': str (error message if failed),
            'traceback': str (detailed traceback if failed)
        }
    """
    hfss3dl = None

    try:
        # Import Hfss3dLayout
        try:
            from ansys.aedt.core import Hfss3dLayout
        except ImportError as e:
            return {
                'success': False,
                'error': f'Failed to import ansys.aedt.core: {str(e)}',
                'traceback': traceback.format_exc()
            }

        # Validate paths
        aedb_path = Path(aedb_path)
        output_path = Path(output_path)

        # Handle both .aedb folder and edb.def file paths
        # Hfss3dLayout accepts .aedb folder path directly
        if aedb_path.name == 'edb.def':
            edb_file = str(aedb_path.parent)  # Use parent .aedb folder
        elif aedb_path.suffix == '.aedb':
            edb_file = str(aedb_path)
        else:
            return {
                'success': False,
                'error': f'Invalid EDB path: {aedb_path}'
            }

        # Output directory is Analysis folder (parent of output_path)
        analysis_folder = output_path.parent
        analysis_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Opening EDB with HFSS 3D Layout: {edb_file}")
        logger.info(f"EDB Version: {edb_version}")
        logger.info(f"Analysis Folder: {analysis_folder}")
        logger.info("")

        # Open EDB using Hfss3dLayout
        # Use version string directly (e.g., "2025.2")
        hfss3dl = Hfss3dLayout(
            project=edb_file,
            version=edb_version,
            non_graphical=False,
            new_desktop=False,
            close_on_exit=False
        )

        logger.info("[OK] HFSS 3D Layout opened successfully")
        logger.info(f"  Project name: {hfss3dl.project_name}")
        logger.info(f"  Design name: {hfss3dl.design_name}")
        logger.info("")

        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save project to .aedt format in Analysis folder with timestamp
        aedt_output_path = analysis_folder / f"{output_path.stem}_{timestamp}.aedt"

        logger.info(f"Saving project to: {aedt_output_path}")
        hfss3dl.save_project(file_name=str(aedt_output_path), overwrite=True)
        logger.info("[OK] Project saved successfully")

        # Configure touchstone export on completion
        touchstone_output_dir = str(analysis_folder)
        logger.info(f"Configuring touchstone export to: {touchstone_output_dir}")
        hfss3dl.export_touchstone_on_completion(export=True, output_dir=touchstone_output_dir)
        logger.info("[OK] Touchstone export configured")

        # Run HFSS analysis
        logger.info("Starting HFSS analysis...")
        hfss3dl.analyze()
        logger.info("[OK] HFSS analysis completed")

        # Save project after analysis
        logger.info("Saving project after analysis...")
        hfss3dl.save_project()
        logger.info("[OK] Project saved after analysis")

        # Close/release HFSS 3D Layout
        logger.info("Closing HFSS 3D Layout...")
        hfss3dl.release_desktop(close_projects=True, close_on_exit=True)
        hfss3dl = None
        logger.info("[OK] HFSS 3D Layout closed")

        logger.info(f"\n[OK] Analysis complete!")
        logger.info(f"Output file: {aedt_output_path}")

        file_size = aedt_output_path.stat().st_size if aedt_output_path.exists() else 0
        logger.info(f"File size: {file_size:,} bytes")
        logger.info("")

        return {
            'success': True,
            'output_file': str(aedt_output_path),
            'file_size': file_size
        }

    except Exception as e:
        error_msg = f"HFSS Analysis failed: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"\n[ERROR] {error_msg}")
        logger.error(error_traceback)

        # Try to close HFSS if it was opened
        if hfss3dl is not None:
            try:
                hfss3dl.release_desktop(close_projects=False, close_on_exit=False)
            except Exception:
                pass

        return {
            'success': False,
            'error': error_msg,
            'traceback': error_traceback
        }

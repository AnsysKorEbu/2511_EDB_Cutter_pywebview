"""
HFSS 3D Layout Analysis Module

This module provides HFSS 3D Layout analysis functionality for EDB files.
Uses Hfss3dLayout from ansys.aedt.core to open EDB files directly.
"""

import time
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
                "success": False,
                "error": f"Failed to import ansys.aedt.core: {str(e)}",
                "traceback": traceback.format_exc(),
            }

        # Validate paths
        aedb_path = Path(aedb_path)
        output_path = Path(output_path)

        # Handle both .aedb folder and edb.def file paths
        # Hfss3dLayout accepts .aedb folder path directly
        if aedb_path.name == "edb.def":
            edb_file = str(aedb_path.parent)  # Use parent .aedb folder
        elif aedb_path.suffix == ".aedb":
            edb_file = str(aedb_path)
        else:
            return {"success": False, "error": f"Invalid EDB path: {aedb_path}"}

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
            close_on_exit=False,
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

        # Run HFSS analysis (non-blocking)
        logger.info("Starting HFSS analysis...")
        hfss3dl.analyze(blocking=False)
        logger.info("[OK] HFSS analysis started (non-blocking)")

        # Wait for simulation with optional timeout
        # timeout_seconds = 0 means no limit, otherwise stop after timeout
        timeout_seconds = 180
        if timeout_seconds > 0:
            logger.info(f"Waiting up to {timeout_seconds} seconds...")
        else:
            logger.info("Waiting for simulation to complete (no time limit)...")

        elapsed = 0
        while hfss3dl.are_there_simulations_running:
            time.sleep(1)
            elapsed += 1
            if elapsed % 30 == 0:
                if timeout_seconds > 0:
                    logger.info(f"  Elapsed: {elapsed}/{timeout_seconds} seconds")
                else:
                    logger.info(f"  Elapsed: {elapsed} seconds")
            # Stop if timeout reached (only when timeout > 0)
            if timeout_seconds > 0 and elapsed >= timeout_seconds:
                break

        # Stop simulations if still running (only when timeout was reached)
        if hfss3dl.are_there_simulations_running:
            logger.info("Timeout reached. Stopping simulations...")
            hfss3dl.stop_simulations()

            # Wait for simulations to fully stop
            while hfss3dl.are_there_simulations_running:
                time.sleep(1)
            logger.info("[OK] Simulations stopped")
        else:
            logger.info("[OK] HFSS analysis completed")

        # Save project after analysis
        logger.info("Saving project after analysis...")
        hfss3dl.save_project()
        logger.info("[OK] Project saved after analysis")

        # Export Touchstone file to Analysis folder (same as siwave)
        touchstone_output_file = analysis_folder / output_path.stem
        logger.info(f"Exporting Touchstone to: {touchstone_output_file}")

        try:
            exported_file = hfss3dl.export_touchstone(
                output_file=str(touchstone_output_file),
                renormalization=False,
                impedance=50.0,
            )
            logger.info(f"[OK] Touchstone exported: {exported_file}")
        except Exception as export_error:
            logger.warning(f"[WARNING] Touchstone export failed: {export_error}")
            exported_file = None

        # Close/release HFSS 3D Layout
        logger.info("Closing HFSS 3D Layout...")
        hfss3dl.release_desktop(close_projects=True, close_desktop=True)
        hfss3dl = None
        logger.info("[OK] HFSS 3D Layout closed")

        # Check for generated Touchstone files (similar to siwave)
        touchstone_files = list(analysis_folder.glob(f"{output_path.stem}.s*p"))

        if touchstone_files:
            generated_file = touchstone_files[0]
            file_size = generated_file.stat().st_size
            logger.info("\n[OK] Analysis complete!")
            logger.info(f"Touchstone file: {generated_file}")
            logger.info(f"File size: {file_size:,} bytes")
            logger.info("")

            return {
                "success": True,
                "output_file": str(generated_file),
                "file_size": file_size,
            }
        else:
            # Fallback to aedt file if no touchstone generated
            logger.info("\n[OK] Analysis complete (no Touchstone generated)")
            logger.info(f"Output file: {aedt_output_path}")
            file_size = (
                aedt_output_path.stat().st_size if aedt_output_path.exists() else 0
            )
            logger.info(f"File size: {file_size:,} bytes")
            logger.info("")

            return {
                "success": True,
                "output_file": str(aedt_output_path),
                "file_size": file_size,
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

        return {"success": False, "error": error_msg, "traceback": error_traceback}

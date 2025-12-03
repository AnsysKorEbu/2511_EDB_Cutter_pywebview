"""
EDB Cutter - Main Entry Point

This application extracts EDB data using subprocess (avoiding pythonnet conflicts)
and displays it in a GUI for region selection and cutting.
"""
import subprocess
import sys
import json
from pathlib import Path
from gui import start_gui
from gui.initial_gui import start_initial_gui
from util.logger_module import logger

def load_settings():
    """
    Load settings from config/settings.json

    Returns:
        dict: Settings dictionary or None if file doesn't exist
    """
    config_file = Path('config') / 'settings.json'

    if not config_file.exists():
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}")
        return None


def check_extracted_data_exists(edb_path):
    """
    Check if any extracted EDB data files exist.

    Checks for: planes.json.gz, traces.json.gz, components.json.gz,
                vias.json.gz, net_names.json.gz

    Args:
        edb_path: Path to EDB folder

    Returns:
        bool: True if any .json.gz files exist in output folder, False otherwise
    """
    # Extract EDB folder name from path (same logic as edb_interface.py)
    edb_folder_name = Path(edb_path).name

    # Create output directory path: source/{edb_folder_name}/
    output_dir = Path('source') / edb_folder_name

    # Find any .json.gz files in the output folder
    if not output_dir.exists():
        return False

    json_gz_files = list(output_dir.glob('*.json.gz'))

    return len(json_gz_files) > 0


def extract_edb_data(edb_path, edb_version, grpc=True):
    """
    Extract EDB data using subprocess.

    This runs edb_interface.py in a separate process to avoid
    pythonnet conflicts with pywebview.

    Args:
        edb_path: Path to EDB file or folder
        edb_version: EDB version string (e.g., "2025.2")
        grpc: Use gRPC mode (default: True)
    """
    logger.info("=" * 70)
    logger.info("Step 1: Extracting EDB Data")
    logger.info("=" * 70)
    logger.info(f"EDB Path: {edb_path}")
    logger.info(f"EDB Version: {edb_version}")
    logger.info(f"gRPC Mode: {grpc}")

    # Run edb package as subprocess with EDB_PATH, EDB_VERSION, and gRPC flag
    # capture_output=False allows real-time output to console
    try:
        grpc_str = "True" if grpc else "False"
        result = subprocess.run(
            [sys.executable, "-m", "edb", edb_path, edb_version, grpc_str],
            cwd=Path.cwd()
        )

        if result.returncode != 0:
            logger.error(f"Data extraction failed with code {result.returncode}")
            sys.exit(1)

        logger.info("Data extraction completed successfully!")

    except Exception as e:
        logger.error(f"Failed to run data extraction: {e}")
        sys.exit(1)


def main():
    """Start EDB Cutter application"""
    logger.info("=" * 70)
    logger.info("EDB Cutter - GUI Application")
    logger.info("=" * 70)

    # Step 1: Always show Initial Setup GUI
    logger.info("Opening Initial Setup GUI...")

    # Start Initial GUI to get settings (will load previous settings if available)
    settings = start_initial_gui()

    if settings is None:
        logger.info("Setup cancelled by user. Exiting.")
        sys.exit(0)

    logger.info("Settings configured successfully!")
    logger.info(f"  - EDB Path: {settings['edb_path']}")
    logger.info(f"  - EDB Version: {settings['edb_version']}")
    logger.info(f"  - gRPC: {settings['grpc']}")
    logger.info(f"  - Overwrite: {settings['overwrite']}")

    # Extract settings
    edb_path = settings['edb_path']
    edb_version = settings['edb_version']
    grpc = settings['grpc']
    overwrite = settings['overwrite']

    # Step 2: Extract data using subprocess
    if overwrite or not check_extracted_data_exists(edb_path):
        extract_edb_data(edb_path, edb_version, grpc)
    else:
        logger.info("=" * 70)
        logger.info("Step 1: Skipping EDB extraction (data exists)")
        logger.info("=" * 70)
        logger.info("Using existing EDB data")

    # Step 3: Start Main GUI
    logger.info("=" * 70)
    logger.info("Step 2: Starting Main GUI")
    logger.info("=" * 70)
    start_gui(edb_path, edb_version, grpc)


if __name__ == "__main__":
    main()

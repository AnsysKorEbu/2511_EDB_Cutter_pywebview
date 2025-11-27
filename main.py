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
        print(f"[WARNING] Failed to load settings: {e}")
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


def extract_edb_data(edb_path, edb_version):
    """
    Extract EDB data using subprocess.

    This runs edb_interface.py in a separate process to avoid
    pythonnet conflicts with pywebview.

    Args:
        edb_path: Path to EDB file or folder
        edb_version: EDB version string (e.g., "2025.2")
    """
    print("=" * 70)
    print("Step 1: Extracting EDB Data")
    print("=" * 70)
    print(f"EDB Path: {edb_path}")
    print(f"EDB Version: {edb_version}\n")

    # Get python executable path
    python_exe = Path(".venv/Scripts/python.exe")

    if not python_exe.exists():
        print(f"[ERROR] Python executable not found: {python_exe}")
        print("Please ensure virtual environment is set up correctly.")
        sys.exit(1)

    # Run edb package as subprocess with EDB_PATH and EDB_VERSION as arguments
    # capture_output=False allows real-time output to console
    try:
        result = subprocess.run(
            [str(python_exe), "-m", "edb", edb_path, edb_version],
            cwd=Path.cwd()
        )

        if result.returncode != 0:
            print(f"\n[ERROR] Data extraction failed with code {result.returncode}")
            sys.exit(1)

        print("\n[OK] Data extraction completed successfully!\n")

    except Exception as e:
        print(f"\n[ERROR] Failed to run data extraction: {e}")
        sys.exit(1)


def main():
    """Start EDB Cutter application"""
    print("=" * 70)
    print("EDB Cutter - GUI Application")
    print("=" * 70)

    # Step 1: Always show Initial Setup GUI
    print("Opening Initial Setup GUI...\n")

    # Start Initial GUI to get settings (will load previous settings if available)
    settings = start_initial_gui()

    if settings is None:
        print("[INFO] Setup cancelled by user. Exiting.")
        sys.exit(0)

    print("\n[OK] Settings configured successfully!")
    print(f"  - EDB Path: {settings['edb_path']}")
    print(f"  - EDB Version: {settings['edb_version']}")
    print(f"  - gRPC: {settings['grpc']}")
    print(f"  - Overwrite: {settings['overwrite']}\n")

    # Extract settings
    edb_path = settings['edb_path']
    edb_version = settings['edb_version']
    grpc = settings['grpc']
    overwrite = settings['overwrite']

    # Step 2: Extract data using subprocess
    if overwrite or not check_extracted_data_exists(edb_path):
        extract_edb_data(edb_path, edb_version)
    else:
        print("=" * 70)
        print("Step 1: Skipping EDB extraction (data exists)")
        print("=" * 70)
        print("[OK] Using existing EDB data\n")

    # Step 3: Start Main GUI
    print("=" * 70)
    print("Step 2: Starting Main GUI")
    print("=" * 70)
    start_gui(edb_path, edb_version, grpc)


if __name__ == "__main__":
    main()

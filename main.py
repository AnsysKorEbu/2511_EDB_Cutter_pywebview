"""
EDB Cutter - Main Entry Point

This application extracts EDB data using subprocess (avoiding pythonnet conflicts)
and displays it in a GUI for region selection and cutting.
"""
import subprocess
import sys
from pathlib import Path
from gui import start_gui

# EDB folder path (modify this to your .aedb folder)
# EDB_PATH = r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb"
# EDB_PATH = r"C:\Python_Code\2511_EDB_Cutter_pywebview\source\example\org_design.aedb"
# EDB_PATH = r"C:\Python_Code\2511_EDB_Cutter_pywebview\source\example\part2_otherstackup.aedb"
EDB_PATH = r"C:\Python_Code\2511_EDB_Cutter_pywebview\source\example\none_port_design.aedb"
EDB_VERSION = "2025.2"
grpc = True
OVERWRITE = True

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


def extract_edb_data(edb_path):
    """
    Extract EDB data using subprocess.

    This runs edb_interface.py in a separate process to avoid
    pythonnet conflicts with pywebview.

    Args:
        edb_path: Path to EDB file or folder
    """
    print("=" * 70)
    print("Step 1: Extracting EDB Data")
    print("=" * 70)

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
            [str(python_exe), "-m", "edb", edb_path, EDB_VERSION],
            cwd=Path.cwd(),
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            print(f"\n[ERROR] Data extraction failed with code {result.returncode}")
            sys.exit(1)

        print("\n[OK] Data extraction completed successfully!\n")

    except subprocess.TimeoutExpired:
        print("\n[ERROR] Data extraction timed out (>5 minutes)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to run data extraction: {e}")
        sys.exit(1)


def main():
    """Start EDB Cutter application"""
    print("=" * 70)
    print("EDB Cutter - GUI Application")
    print("=" * 70)
    print(f"EDB Path: {EDB_PATH}\n")

    # Step 1: Extract data using subprocess
    if OVERWRITE or not check_extracted_data_exists(EDB_PATH):
        extract_edb_data(EDB_PATH)
    else:
        print("=" * 70)
        print("Step 1: Skipping EDB extraction (data exists)")
        print("=" * 70)
        print("[OK] Using existing EDB data\n")

    # Step 2: Start GUI
    print("=" * 70)
    print("Step 2: Starting GUI")
    print("=" * 70)
    start_gui(EDB_PATH, EDB_VERSION, grpc)


if __name__ == "__main__":
    main()

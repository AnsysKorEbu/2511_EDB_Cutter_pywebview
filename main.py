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
EDB_PATH = r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb"


def extract_edb_data():
    """
    Extract EDB data using subprocess.

    This runs edb_interface.py in a separate process to avoid
    pythonnet conflicts with pywebview.
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

    # Run edb package as subprocess
    # capture_output=False allows real-time output to console
    try:
        result = subprocess.run(
            [str(python_exe), "-m", "edb"],
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
    if False:
        extract_edb_data()

    # Step 2: Start GUI
    print("=" * 70)
    print("Step 2: Starting GUI")
    print("=" * 70)
    start_gui(EDB_PATH)


if __name__ == "__main__":
    main()

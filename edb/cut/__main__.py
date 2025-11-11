"""
Entry point for running edb.cut package as a module: python -m edb.cut

This script is run as a subprocess to execute EDB cutting operations.
It loads cut data and calls the edb_cut_interface module.
"""
import sys
import json
from pathlib import Path
from ..edb_cut_interface import execute_cut


def load_cut_data(cut_file_path):
    """
    Load cut data from JSON file.

    Args:
        cut_file_path: Path to cut JSON file

    Returns:
        dict: Cut data dictionary

    Raises:
        FileNotFoundError: If cut file doesn't exist
        json.JSONDecodeError: If JSON parsing fails
    """
    cut_path = Path(cut_file_path)

    if not cut_path.exists():
        raise FileNotFoundError(f"Cut file not found: {cut_file_path}")

    with open(cut_path, 'r', encoding='utf-8') as f:
        cut_data = json.load(f)

    return cut_data


if __name__ == "__main__":
    """
    Main entry point for subprocess.

    Expected command line arguments:
        sys.argv[1]: edb_path (path to .aedb folder or edb.def file)
        sys.argv[2]: edb_version (e.g., "2025.1")
        sys.argv[3]: cut_file_path (path to cut JSON file)
    """
    if len(sys.argv) < 4:
        print("[ERROR] Insufficient arguments")
        print("Usage: python -m edb.cut <edb_path> <edb_version> <cut_file_path>")
        sys.exit(1)

    edb_path = sys.argv[1]
    edb_version = sys.argv[2]
    cut_file_path = sys.argv[3]

    # If path ends with .aedb, append edb.def
    if edb_path.endswith('.aedb'):
        edb_path = str(Path(edb_path) / 'edb.def')

    print("=" * 70)
    print("EDB Cutter Subprocess")
    print("=" * 70)
    print(f"EDB Path: {edb_path}")
    print(f"EDB Version: {edb_version}")
    print(f"Cut File: {cut_file_path}")
    print()

    try:
        # Load cut data
        print("Loading cut data...")
        cut_data = load_cut_data(cut_file_path)
        print(f"[OK] Cut data loaded: {cut_data.get('id', 'unknown')}")
        print()

        # Execute cutting operation
        success = execute_cut(edb_path, edb_version, cut_data)

        if success:
            print()
            print("=" * 70)
            print("[SUCCESS] EDB cutting operation completed")
            print("=" * 70)
            sys.exit(0)
        else:
            print()
            print("=" * 70)
            print("[ERROR] EDB cutting operation failed")
            print("=" * 70)
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Failed to parse cut data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
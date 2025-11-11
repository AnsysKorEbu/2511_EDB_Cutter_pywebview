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
        sys.argv[3]: cut_file_path (path to cut JSON file or batch JSON file)
    """
    if len(sys.argv) < 4:
        print("[ERROR] Insufficient arguments")
        print("Usage: python -m edb.cut <edb_path> <edb_version> <cut_file_path>")
        sys.exit(1)

    edb_path = sys.argv[1]
    edb_version = sys.argv[2]
    input_file_path = sys.argv[3]

    # If path ends with .aedb, append edb.def
    if edb_path.endswith('.aedb'):
        edb_path = str(Path(edb_path) / 'edb.def')

    print("=" * 70)
    print("EDB Cutter Subprocess")
    print("=" * 70)
    print(f"EDB Path: {edb_path}")
    print(f"EDB Version: {edb_version}")
    print(f"Input File: {input_file_path}")
    print()

    try:
        # Load input file to detect mode
        print("Loading input file...")
        with open(input_file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        # Check if batch mode
        is_batch = input_data.get('mode') == 'batch'

        if is_batch:
            # Batch mode: multiple cuts
            cut_files = input_data.get('cut_files', [])
            if not cut_files:
                print("[ERROR] No cut files in batch")
                sys.exit(1)

            print(f"[BATCH MODE] Processing {len(cut_files)} cuts")
            print()

            all_success = True
            failed_cuts = []

            for i, cut_file_path in enumerate(cut_files, 1):
                print("-" * 70)
                print(f"Processing cut {i}/{len(cut_files)}: {Path(cut_file_path).name}")
                print("-" * 70)

                try:
                    # Load individual cut data
                    cut_data = load_cut_data(cut_file_path)
                    cut_id = cut_data.get('id', Path(cut_file_path).stem)
                    print(f"[OK] Cut data loaded: {cut_id}")
                    print()

                    # Execute cutting operation (EDB opens and closes for each cut)
                    success = execute_cut(edb_path, edb_version, cut_data)

                    if success:
                        print(f"[OK] Cut {cut_id} completed successfully")
                    else:
                        print(f"[ERROR] Cut {cut_id} failed")
                        all_success = False
                        failed_cuts.append(cut_id)

                except Exception as cut_error:
                    print(f"[ERROR] Failed to process cut {i}: {cut_error}")
                    all_success = False
                    failed_cuts.append(f"cut_{i}")

                print()

            # Print final summary
            print("=" * 70)
            if all_success:
                print(f"[SUCCESS] All {len(cut_files)} cuts completed successfully")
            else:
                print(f"[PARTIAL SUCCESS] {len(cut_files) - len(failed_cuts)}/{len(cut_files)} cuts completed")
                print(f"Failed cuts: {', '.join(failed_cuts)}")
            print("=" * 70)

            sys.exit(0 if all_success else 1)

        else:
            # Single mode: one cut (input_data is the cut data itself)
            cut_id = input_data.get('id', 'unknown')
            print(f"[SINGLE MODE] Processing cut: {cut_id}")
            print()

            # Execute cutting operation
            success = execute_cut(edb_path, edb_version, input_data)

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
        print(f"\n[ERROR] Failed to parse input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
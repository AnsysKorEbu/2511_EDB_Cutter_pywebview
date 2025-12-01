"""
Entry point for running edb.analysis package as a module: python -m edb.analysis

This script is run as a subprocess to execute SIwave analysis operations.
It isolates pythonnet dependencies from the pywebview GUI.
"""
import sys
from pathlib import Path
from .import run_siwave_analysis


if __name__ == "__main__":
    """
    Main entry point for subprocess.

    Expected command line arguments:
        sys.argv[1]: aedb_path (path to .aedb folder or edb.def file)
        sys.argv[2]: edb_version (e.g., "2025.1")
        sys.argv[3]: output_path (path for touchstone output file)
        sys.argv[4]: grpc (optional, "True" or "False", default: "False")
    """
    if len(sys.argv) < 4:
        print("[ERROR] Insufficient arguments")
        print("Usage: python -m edb.analysis <aedb_path> <edb_version> <output_path> [grpc]")
        sys.exit(1)

    aedb_path = sys.argv[1]
    edb_version = sys.argv[2]
    output_path = sys.argv[3]
    grpc = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False

    print("=" * 70)
    print("EDB Analysis Subprocess")
    print("=" * 70)
    print(f"AEDB Path: {aedb_path}")
    print(f"EDB Version: {edb_version}")
    print(f"Output Path: {output_path}")
    print(f"gRPC Mode: {grpc}")
    print()

    try:
        # Run SIwave analysis
        result = run_siwave_analysis(aedb_path, edb_version, output_path, grpc)

        if result['success']:
            print("=" * 70)
            print("[SUCCESS] SIwave analysis completed successfully")
            print(f"Output file: {result['output_file']}")
            print(f"File size: {result.get('file_size', 0):,} bytes")
            print("=" * 70)
            sys.exit(0)
        else:
            print("=" * 70)
            print("[ERROR] SIwave analysis failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print("=" * 70)
            sys.exit(1)

    except Exception as e:
        print("=" * 70)
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        sys.exit(1)

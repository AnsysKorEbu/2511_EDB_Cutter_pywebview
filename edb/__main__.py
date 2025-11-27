"""Entry point for running edb package as a module: python -m edb"""
import sys
from pathlib import Path
from .edb_interface import interface

if __name__ == "__main__":
    # Get EDB path from command line argument
    if len(sys.argv) > 1:
        edb_path = sys.argv[1]
        # Get EDB version from command line argument (default: "2025.1")
        edb_version = sys.argv[2] if len(sys.argv) > 2 else "2025.1"

        # Use .aedb path directly (no need to append edb.def)
        interface(edbpath=edb_path, edbversion=edb_version)
    else:
        # Default path if no argument provided
        interface(edbpath=r"C:\Python_Code\2511_EDB_Cutter_pywebview\source\example\part2_otherstackup.aedb")

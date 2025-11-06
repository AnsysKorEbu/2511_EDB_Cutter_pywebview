"""Entry point for running edb package as a module: python -m edb"""
import sys
from pathlib import Path
from .edb_interface import interface

if __name__ == "__main__":
    # Get EDB path from command line argument
    if len(sys.argv) > 1:
        edb_path = sys.argv[1]

        # If path ends with .aedb, append edb.def
        if edb_path.endswith('.aedb'):
            edb_path = str(Path(edb_path) / 'edb.def')

        interface(edbpath=edb_path)
    else:
        # Default path if no argument provided
        interface(edbpath=r"C:\Python_Code\2511_EDB_Cutter_pywebview\source\example\part2_otherstackup.aedb\edb.def")

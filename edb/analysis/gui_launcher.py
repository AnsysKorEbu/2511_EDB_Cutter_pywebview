"""
Standalone launcher for Analysis GUI.

This script can be run independently to launch the Analysis GUI
for generating Touchstone files from previously cut EDB designs.

Usage:
    python main_analysis.py [results_folder]

If no results_folder is provided, a folder browser dialog will open.
"""
import sys
from pathlib import Path
from util.logger_module import logger


if __name__ == "__main__":
    results_folder = sys.argv[1] if len(sys.argv) > 1 else None
    edb_version = sys.argv[2] if len(sys.argv) > 2 else "2025.1"
    grpc = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False

    if not results_folder:
        # Show folder browser if no folder provided
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # Hide the root window

        logger.info("Please select a Results folder...")

        results_folder = filedialog.askdirectory(
            title='Select Results Folder (e.g., Results/design_20251201_143000/)',
            initialdir=str(Path('Results').resolve()) if Path('Results').exists() else str(Path.cwd())
        )

        root.destroy()

        if not results_folder:
            logger.info("No folder selected. Exiting.")
            sys.exit(1)

    # Verify the folder exists
    results_path = Path(results_folder)
    if not results_path.exists():
        logger.info(f"Error: Folder does not exist: {results_folder}")
        sys.exit(1)

    if not results_path.is_dir():
        logger.info(f"Error: Path is not a directory: {results_folder}")
        sys.exit(1)

    logger.info(f"Launching Analysis GUI for: {results_folder}")
    logger.info(f"EDB Version: {edb_version}")
    logger.info(f"gRPC Mode: {grpc}")

    # Import and launch Analysis GUI
    from gui import launch_analysis_gui

    # Launch with EDB version and gRPC settings from command line
    launch_analysis_gui(results_folder, edb_version=edb_version, grpc=grpc)

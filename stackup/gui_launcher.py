"""
Standalone launcher for Stackup Settings GUI.

This script is launched as a subprocess to avoid PyWebView threading issues.
PyWebView requires running on the main thread, so we launch it in a separate process.

Usage:
    python -m stackup.gui_launcher <edb_folder_path> <edb_folder_name>
"""
import sys
from pathlib import Path
from util.logger_module import logger


if __name__ == "__main__":
    edb_folder = sys.argv[1] if len(sys.argv) > 1 else None
    edb_folder_name = sys.argv[2] if len(sys.argv) > 2 else "Unknown"

    if not edb_folder:
        logger.error("No EDB folder provided")
        sys.exit(1)

    # Verify the folder exists
    edb_path = Path(edb_folder)
    if not edb_path.exists():
        logger.error(f"EDB folder does not exist: {edb_folder}")
        sys.exit(1)

    logger.info(f"Launching Stackup Settings GUI for: {edb_folder_name}")
    logger.info(f"EDB Folder: {edb_folder}")

    # Import and launch Stackup Settings GUI
    from gui import launch_stackup_settings_gui

    # Launch (this will block until window is closed)
    launch_stackup_settings_gui(edb_folder, edb_folder_name)

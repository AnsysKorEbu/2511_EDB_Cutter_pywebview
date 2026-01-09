"""
Standalone launcher for Circuit Generator GUI.

Usage:
    python -m gui.circuit_launcher <edb_version>
"""
import sys
from pathlib import Path


def launch_circuit_gui(edb_version="2025.1"):
    """
    Launch Circuit Generator GUI window.

    Args:
        edb_version: EDB version string (e.g., "2025.1")
    """
    import webview
    from gui.circuit_gui import CircuitApi

    # Create API instance with edb_version
    api = CircuitApi(edb_version)

    # Get HTML file path
    html_file = Path(__file__).parent / 'circuit.html'

    # Create window
    window = webview.create_window(
        'HFSS Circuit Generator',
        html_file.as_uri(),
        js_api=api,
        width=900,
        height=700,
        resizable=True
    )

    # Start GUI
    webview.start()


if __name__ == "__main__":
    from util.logger_module import logger

    # Get edb_version from command line arguments
    edb_version = sys.argv[1] if len(sys.argv) > 1 else "2025.1"

    logger.info(f"Launching Circuit Generator GUI...")
    logger.info(f"EDB Version: {edb_version}")

    # Launch GUI
    launch_circuit_gui(edb_version)
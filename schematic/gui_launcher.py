"""
Standalone launcher for Schematic GUI (Full Touchstone Generator).

Usage:
    python -m schematic.gui_launcher [analysis_folder]
"""
import sys
from pathlib import Path


def launch_schematic_gui(analysis_folder=None, edb_version="2025.1"):
    """
    Launch Schematic GUI window.

    Args:
        analysis_folder: Optional path to Analysis folder
        edb_version: EDB version string (e.g., "2025.2")
    """
    import webview
    from schematic.schematic_gui import SchematicApi

    # Create API instance
    api = SchematicApi(analysis_folder, edb_version)
    
    # Get HTML file path
    html_file = Path(__file__).parent / 'index.html'
    
    # Create window
    window = webview.create_window(
        'Generate Full Touchstone',
        html_file.as_uri(),
        js_api=api,
        width=800,
        height=700,
        resizable=True
    )
    
    # Start GUI
    webview.start()


if __name__ == "__main__":
    from util.logger_module import logger

    # Parse command line arguments: [analysis_folder] [edb_version]
    analysis_folder = sys.argv[1] if len(sys.argv) > 1 else None
    edb_version = sys.argv[2] if len(sys.argv) > 2 else "2025.1"

    if not analysis_folder:
        # Show folder browser if no folder provided
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        
        logger.info("Please select an Analysis folder...")
        
        analysis_folder = filedialog.askdirectory(
            title='Select Analysis Folder (containing .s*p touchstone files)',
            initialdir=str(Path('Results').resolve()) if Path('Results').exists() else str(Path.cwd())
        )
        
        root.destroy()
        
        if not analysis_folder:
            logger.info("No folder selected. Exiting.")
            sys.exit(1)
    
    # Verify folder exists
    analysis_path = Path(analysis_folder)
    if not analysis_path.exists():
        logger.error(f"Folder does not exist: {analysis_folder}")
        sys.exit(1)
    
    logger.info(f"Launching Schematic GUI for: {analysis_folder}")
    logger.info(f"EDB Version: {edb_version}")

    # Launch GUI
    launch_schematic_gui(analysis_folder, edb_version)

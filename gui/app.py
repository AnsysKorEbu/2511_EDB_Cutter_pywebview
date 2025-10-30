"""Main GUI application using pywebview"""
import webview
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.api import EDBAPI


def start_gui(edb_path: str):
    """
    Start the EDB Cutter GUI application

    Args:
        edb_path: Path to .aedb folder
    """
    # Initialize API
    try:
        api = EDBAPI(edb_path)
    except Exception as e:
        print(f"Error loading EDB: {e}")
        raise

    # Get web files path
    web_dir = Path(__file__).parent.parent / 'web'

    if not web_dir.exists():
        raise FileNotFoundError(f"Web directory not found: {web_dir}")

    # Get HTML file path
    html_file = web_dir / 'index.html'
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    # Start pywebview application
    print("Starting EDB Cutter GUI...")
    window = webview.create_window(
        'EDB Cutter',
        str(html_file),  # Convert Path to string
        js_api=api,
        width=1600,
        height=1000,
        resizable=True
    )

    # Start the GUI (blocking call)
    # Use Edge Chromium for modern JavaScript support (Pixi.js, etc.)
    webview.start(gui='edgechromium', debug=True)

    # Cleanup on close
    if api.edb:
        try:
            api.edb.close()
            print("EDB closed successfully")
        except:
            pass

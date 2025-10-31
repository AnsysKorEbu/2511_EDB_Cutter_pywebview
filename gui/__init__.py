"""
GUI module for EDB Cutter using pywebview
"""
import webview
from pathlib import Path


class Api:
    """JavaScript API for pywebview"""

    def __init__(self, edb_path):
        self.edb_path = edb_path
        self.data = None

    def test_function(self):
        """Test function called from JavaScript"""
        return f"Hello from Python! EDB Path: {self.edb_path}"

    def load_edb_data(self):
        """Load EDB data from source folder"""
        try:
            from edb.edb_saver import load_all_edb_data

            print("Loading EDB data from source folder...")
            self.data = load_all_edb_data()

            return {
                'planes': len(self.data['planes']) if self.data['planes'] else 0,
                'traces': len(self.data['traces']) if self.data['traces'] else 0,
                'components': len(self.data['components']) if self.data['components'] else 0
            }
        except Exception as e:
            print(f"Error loading data: {e}")
            return {'error': str(e)}

    def get_planes_data(self):
        """Get planes data for rendering"""
        try:
            if self.data is None or self.data.get('planes') is None:
                from edb.edb_saver import load_all_edb_data
                print("Loading EDB data from source folder...")
                self.data = load_all_edb_data()

            return self.data.get('planes', [])
        except Exception as e:
            print(f"Error getting planes data: {e}")
            return []


def start_gui(edb_path):
    """Start the pywebview GUI"""
    api = Api(edb_path)

    # Get HTML file path
    html_file = Path(__file__).parent / 'index.html'

    # Create window
    window = webview.create_window(
        'EDB Cutter - 2D Viewer',
        html_file.as_uri(),
        js_api=api,
        width=1200,
        height=800,
        resizable=True
    )

    # Start GUI
    webview.start(debug=True)

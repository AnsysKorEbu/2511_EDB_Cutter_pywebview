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

    def save_cut_data(self, cut_data):
        """Save cut geometry data to source/cut folder"""
        import json
        from datetime import datetime

        try:
            cut_dir = Path('source/cut')
            cut_dir.mkdir(parents=True, exist_ok=True)

            # Generate cut ID based on existing files
            existing_files = list(cut_dir.glob('cut_*.json'))
            cut_id = f"cut_{len(existing_files) + 1:03d}"

            # Add metadata
            cut_data['id'] = cut_id
            cut_data['timestamp'] = datetime.now().isoformat()

            # Save to JSON file
            cut_file = cut_dir / f"{cut_id}.json"
            with open(cut_file, 'w', encoding='utf-8') as f:
                json.dump(cut_data, f, indent=2)

            print(f"Cut data saved: {cut_file}")
            return {'success': True, 'id': cut_id, 'file': str(cut_file)}
        except Exception as e:
            print(f"Error saving cut data: {e}")
            return {'success': False, 'error': str(e)}

    def get_cut_list(self):
        """Get list of saved cut files"""
        import json

        try:
            cut_dir = Path('source/cut')
            if not cut_dir.exists():
                return []

            cuts = []
            for cut_file in sorted(cut_dir.glob('cut_*.json')):
                try:
                    with open(cut_file, 'r', encoding='utf-8') as f:
                        cut_data = json.load(f)
                    cuts.append({
                        'id': cut_data.get('id', cut_file.stem),
                        'type': cut_data.get('type', 'unknown'),
                        'timestamp': cut_data.get('timestamp', ''),
                        'filename': cut_file.name
                    })
                except Exception as e:
                    print(f"Error reading {cut_file}: {e}")

            return cuts
        except Exception as e:
            print(f"Error getting cut list: {e}")
            return []

    def delete_cut(self, cut_id):
        """Delete a cut file"""
        try:
            cut_dir = Path('source/cut')
            cut_file = cut_dir / f"{cut_id}.json"

            if cut_file.exists():
                cut_file.unlink()
                print(f"Deleted cut: {cut_file}")
                return {'success': True}
            else:
                return {'success': False, 'error': 'File not found'}
        except Exception as e:
            print(f"Error deleting cut: {e}")
            return {'success': False, 'error': str(e)}

    def get_cut_data(self, cut_id):
        """Get full data for a specific cut"""
        import json

        try:
            cut_dir = Path('source/cut')
            cut_file = cut_dir / f"{cut_id}.json"

            if cut_file.exists():
                with open(cut_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return None
        except Exception as e:
            print(f"Error loading cut data: {e}")
            return None


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

"""Main GUI application using Eel"""
import eel
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from edb import extract_plane_positions, extract_trace_positions, extract_component_positions
import pyedb
from gui.config import SCALE, INPUT_UNIT, EDB_VERSION


# Global EDB instance
_edb = None


def start_gui(edb_path: str):
    """
    Start the EDB Cutter GUI application

    Args:
        edb_path: Path to .aedb folder
    """
    global _edb

    # Initialize EDB
    try:
        _edb = pyedb.Edb(edbpath=edb_path, version=EDB_VERSION)
        print(f"EDB loaded successfully: {edb_path}")
        print(f"EDB version: {EDB_VERSION}")
    except Exception as e:
        print(f"Error loading EDB: {e}")
        raise

    # Get web files path
    web_dir = Path(__file__).parent.parent / 'web'

    if not web_dir.exists():
        raise FileNotFoundError(f"Web directory not found: {web_dir}")

    # Initialize Eel with web directory
    eel.init(str(web_dir))

    # Start Eel application
    print("Starting EDB Cutter GUI...")
    try:
        # Try Edge first (default on Windows 11), then fallback to default browser
        eel.start('index.html',
                  size=(1600, 1000),
                  port=8080,
                  mode='edge',
                  close_callback=on_close)
    except EnvironmentError:
        # Fallback to default browser
        print("Edge not found, using default browser...")
        eel.start('index.html',
                  size=(1600, 1000),
                  port=8080,
                  mode=None,  # Use default browser
                  close_callback=on_close)


def on_close(page, sockets):
    """Handle application close"""
    global _edb
    if _edb:
        try:
            _edb.close()
            print("EDB closed successfully")
        except:
            pass


# Expose Python functions to JavaScript
@eel.expose
def get_config():
    """
    Get configuration for JavaScript

    Returns:
        dict: Configuration including unit scale
    """
    return {
        'scale': SCALE,
        'inputUnit': INPUT_UNIT,
        'outputUnit': 'um'
    }


@eel.expose
def get_planes():
    """
    Get all plane polygons

    Returns:
        list[dict]: Plane data with coordinates
    """
    global _edb
    try:
        planes = extract_plane_positions(_edb)
        print(f"Extracted {len(planes)} planes")
        return planes
    except Exception as e:
        print(f"Error extracting planes: {e}")
        return []


@eel.expose
def get_traces():
    """
    Get all trace paths

    Returns:
        list[dict]: Trace data with center lines
    """
    global _edb
    try:
        traces = extract_trace_positions(_edb)
        print(f"Extracted {len(traces)} traces")
        return traces
    except Exception as e:
        print(f"Error extracting traces: {e}")
        return []


@eel.expose
def get_components():
    """
    Get all component positions

    Returns:
        dict: Component name to [x, y] position mapping
    """
    global _edb
    try:
        components = extract_component_positions(_edb)
        print(f"Extracted {len(components)} components")
        return components
    except Exception as e:
        print(f"Error extracting components: {e}")
        return {}


@eel.expose
def get_bounds():
    """
    Calculate overall PCB bounds

    Returns:
        dict: Bounding box {x_min, y_min, x_max, y_max}
    """
    global _edb
    try:
        planes = extract_plane_positions(_edb)

        if not planes:
            return {'x_min': 0, 'y_min': 0, 'x_max': 1, 'y_max': 1}

        all_x = []
        all_y = []

        for plane in planes:
            bbox = plane.get('bbox')
            if bbox:
                all_x.extend([bbox[0], bbox[2]])
                all_y.extend([bbox[1], bbox[3]])

        if not all_x or not all_y:
            return {'x_min': 0, 'y_min': 0, 'x_max': 1, 'y_max': 1}

        return {
            'x_min': min(all_x),
            'y_min': min(all_y),
            'x_max': max(all_x),
            'y_max': max(all_y)
        }
    except Exception as e:
        print(f"Error calculating bounds: {e}")
        return {'x_min': 0, 'y_min': 0, 'x_max': 1, 'y_max': 1}


@eel.expose
def cut_region(polygon_coords_um):
    """
    Cut EDB region (to be implemented)

    Args:
        polygon_coords_um: Polygon coordinates in micrometers [[x, y], ...]

    Returns:
        dict: Result message
    """
    # Convert um back to input unit
    coords_input_unit = [[x / SCALE, y / SCALE] for x, y in polygon_coords_um]

    print(f"Cut region requested with {len(coords_input_unit)} points")
    print(f"Coordinates ({INPUT_UNIT}): {coords_input_unit}")

    # TODO: Implement actual cutting logic
    return {
        'success': True,
        'message': f'Cutting feature will be implemented. Received {len(coords_input_unit)} points.',
        'coords': coords_input_unit
    }

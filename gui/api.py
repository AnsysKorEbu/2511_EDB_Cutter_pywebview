"""Python API for JavaScript communication via pywebview"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# IMPORTANT: Do NOT import pyedb here - causes pythonnet conflicts
# Import it only when needed (lazy loading)


class EDBAPI:
    """API class for EDB operations exposed to JavaScript"""

    def __init__(self, edb_path: str):
        """
        Initialize EDB API

        Args:
            edb_path: Path to .aedb folder
        """
        self.edb_path = edb_path
        self.edb = None
        self._edb_loaded = False
        self._lock = None  # Will be initialized when needed

    def _get_lock(self):
        """Get or create lock for thread-safe EDB loading"""
        if self._lock is None:
            import threading
            self._lock = threading.Lock()
        return self._lock

    def _load_edb_lazy(self):
        """Lazy load EDB file - only when first API call is made (thread-safe)"""
        # Thread-safe check and load
        with self._get_lock():
            if self._edb_loaded:
                return

            try:
                # Import here to avoid early CLR initialization
                import pyedb
                from gui.config import EDB_VERSION

                print(f"Loading EDB: {self.edb_path}")
                print(f"EDB version: {EDB_VERSION}")

                self.edb = pyedb.Edb(edbpath=self.edb_path, version=EDB_VERSION)
                self._edb_loaded = True

                print(f"[OK] EDB loaded successfully")
            except Exception as e:
                print(f"[ERROR] Failed to load EDB: {e}")
                raise

    def get_config(self):
        """
        Get configuration for JavaScript

        Returns:
            dict: Configuration including unit scale
        """
        from gui.config import SCALE, INPUT_UNIT

        return {
            'scale': SCALE,
            'inputUnit': INPUT_UNIT,
            'outputUnit': 'um'
        }

    def get_planes(self):
        """
        Get all plane polygons

        Returns:
            list[dict]: Plane data with coordinates
        """
        self._load_edb_lazy()

        try:
            from edb import extract_plane_positions
            planes = extract_plane_positions(self.edb)
            print(f"Extracted {len(planes)} planes")
            return planes
        except Exception as e:
            print(f"Error extracting planes: {e}")
            return []

    def get_traces(self):
        """
        Get all trace paths

        Returns:
            list[dict]: Trace data with center lines
        """
        self._load_edb_lazy()

        try:
            from edb import extract_trace_positions
            traces = extract_trace_positions(self.edb)
            print(f"Extracted {len(traces)} traces")
            return traces
        except Exception as e:
            print(f"Error extracting traces: {e}")
            return []

    def get_components(self):
        """
        Get all component positions

        Returns:
            dict: Component name to [x, y] position mapping
        """
        self._load_edb_lazy()

        try:
            from edb import extract_component_positions
            components = extract_component_positions(self.edb)
            print(f"Extracted {len(components)} components")
            return components
        except Exception as e:
            print(f"Error extracting components: {e}")
            return {}

    def get_bounds(self):
        """
        Calculate overall PCB bounds

        Returns:
            dict: Bounding box {x_min, y_min, x_max, y_max}
        """
        self._load_edb_lazy()

        try:
            from edb import extract_plane_positions
            planes = extract_plane_positions(self.edb)

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

    def cut_region(self, polygon_coords_um):
        """
        Cut EDB region (to be implemented)

        Args:
            polygon_coords_um: Polygon coordinates in micrometers [[x, y], ...]

        Returns:
            dict: Result message
        """
        from gui.config import SCALE, INPUT_UNIT

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

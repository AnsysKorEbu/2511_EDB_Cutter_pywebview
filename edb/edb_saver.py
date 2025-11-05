"""
EDB Data Saver/Loader with gzip compression

Efficiently saves and loads large EDB data using compressed JSON format.
"""
import json
import gzip
from pathlib import Path
from typing import Dict, List, Any


def save_edb_data(
    planes_data: List[Dict] = None,
    traces_data: List[Dict] = None,
    components_data: Dict = None,
    vias_data: List[Dict] = None,
    output_dir: str = 'source'
) -> Dict[str, str]:
    """
    Save EDB data as compressed JSON files.

    Args:
        planes_data: List of plane polygons data
        traces_data: List of trace paths data
        components_data: Dictionary of component positions
        vias_data: List of via data
        output_dir: Output directory path (default: 'source')

    Returns:
        Dictionary with file paths and statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    results = {}

    # Save each dataset if provided
    datasets = {
        'planes.json.gz': planes_data,
        'traces.json.gz': traces_data,
        'components.json.gz': components_data,
        'vias.json.gz': vias_data
    }

    for filename, data in datasets.items():
        if data is not None:
            filepath = output_path / filename

            # Save as compressed JSON
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f)

            # Get file size
            file_size = filepath.stat().st_size
            item_count = len(data) if isinstance(data, list) else len(data.keys())

            results[filename] = {
                'path': str(filepath),
                'size_mb': round(file_size / 1024 / 1024, 2),
                'items': item_count
            }

            print(f"[OK] Saved: {filename} ({item_count} items, {results[filename]['size_mb']} MB)")

    return results


def load_edb_data(filename: str, source_dir: str = 'source') -> Any:
    """
    Load compressed JSON data file.

    Args:
        filename: Name of the file to load (e.g., 'planes.json.gz')
        source_dir: Source directory path (default: 'source')

    Returns:
        Loaded data (list or dict)

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    filepath = Path(source_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    print(f"Loading: {filename}...", end=' ')

    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
        data = json.load(f)

    item_count = len(data) if isinstance(data, list) else len(data.keys())
    print(f"[OK] Loaded {item_count} items")

    return data


def load_all_edb_data(source_dir: str = 'source') -> Dict[str, Any]:
    """
    Load all available EDB data files.

    Args:
        source_dir: Source directory path (default: 'source')

    Returns:
        Dictionary with keys: 'planes', 'traces', 'components', 'vias'
    """
    result = {}

    files = {
        'planes': 'planes.json.gz',
        'traces': 'traces.json.gz',
        'components': 'components.json.gz',
        'vias': 'vias.json.gz'
    }

    for key, filename in files.items():
        filepath = Path(source_dir) / filename
        if filepath.exists():
            result[key] = load_edb_data(filename, source_dir)
        else:
            print(f"[WARN] {filename} not found, skipping...")
            result[key] = None

    return result


if __name__ == "__main__":
    # Example usage
    print("=" * 70)
    print("EDB Data Saver/Loader Test")
    print("=" * 70)

    # Test save
    test_planes = [
        {'name': 'plane1', 'layer': 'GND', 'points': [[0, 0], [1, 1]]},
        {'name': 'plane2', 'layer': 'PWR', 'points': [[2, 2], [3, 3]]}
    ]

    save_edb_data(planes_data=test_planes)

    # Test load
    loaded = load_edb_data('planes.json.gz')
    print(f"\nLoaded data: {loaded}")
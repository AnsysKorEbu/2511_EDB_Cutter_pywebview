"""
EDB Cutter Module

This module handles EDB cutting operations.
Currently only opens EDB, with room for future cutting logic.
"""
import pyedb
from pathlib import Path
from datetime import datetime


def open_edb(edbpath, edbversion):
    """
    Open EDB file using pyedb.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")

    Returns:
        pyedb.Edb: Opened EDB object

    Raises:
        Exception: If EDB opening fails
    """
    print("=" * 70)
    print("EDB Cutter - Opening EDB")
    print("=" * 70)
    print(f"EDB Path: {edbpath}")
    print(f"EDB Version: {edbversion}")
    print()

    try:
        print("Opening EDB...")
        edb = pyedb.Edb(edbpath=edbpath, version=edbversion)
        print("[OK] EDB opened successfully\n")
        return edb

    except Exception as e:
        print(f"[ERROR] Failed to open EDB: {e}")
        raise


def clone_edbs_for_cuts(original_edb_path, num_clones, edb_version):
    """
    Clone original EDB file multiple times for cut processing.

    For n cuts, creates (n+1) clones because n cuts divide the design into (n+1) segments.

    Args:
        original_edb_path: Path to original .aedb folder or edb.def file
        num_clones: Number of clones to create (typically num_cuts + 1)
        edb_version: AEDT version string (e.g., "2025.1")

    Returns:
        list: List of cloned .aedb paths in format Results/{original_name}/{original_name}_XXX.aedb

    Raises:
        Exception: If cloning fails
    """
    print("=" * 70)
    print("EDB Cutter - Cloning EDB Files")
    print("=" * 70)
    print(f"Original EDB: {original_edb_path}")
    print(f"Number of clones: {num_clones}")
    print(f"EDB Version: {edb_version}")
    print()

    try:
        # Convert to Path object and get original name
        original_path = Path(original_edb_path)

        # Handle both .aedb folder and edb.def file paths
        if original_path.name == 'edb.def':
            original_aedb_folder = original_path.parent
        elif original_path.suffix == '.aedb':
            original_aedb_folder = original_path
        else:
            raise ValueError(f"Invalid EDB path format: {original_edb_path}")

        # Extract original name without .aedb extension
        original_name = original_aedb_folder.stem

        # Create Results directory structure with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_dir = Path('Results') / f"{original_name}_{timestamp}"
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created output directory: {results_dir}")
        print()

        # Open original EDB
        print(f"Opening original EDB: {original_aedb_folder}")
        edb = pyedb.Edb(str(original_aedb_folder), version=edb_version)
        print("[OK] Original EDB opened successfully")
        print()

        # Clone EDB files
        cloned_paths = []
        print(f"Starting cloning process ({num_clones} clones)...")
        print()

        for i in range(1, num_clones + 1):
            clone_name = f"{original_name}_{i:03d}.aedb"
            clone_path = results_dir / clone_name

            print(f"[{i}/{num_clones}] Cloning to: {clone_path}")

            # Use save_as to create clone
            edb.save_as(str(clone_path))
            cloned_paths.append(str(clone_path))

            print(f"[OK] Clone {i} created successfully")
            print()

        # Close original EDB
        edb.close()
        print("[OK] Original EDB closed")
        print()

        print("=" * 70)
        print(f"[SUCCESS] Created {num_clones} EDB clones")
        print("=" * 70)
        print()

        return cloned_paths

    except Exception as e:
        print(f"[ERROR] Failed to clone EDB files: {e}")
        import traceback
        traceback.print_exc()
        raise


def execute_cut(edbpath, edbversion, cut_data):
    """
    Execute cutting operation on EDB.

    This function will be implemented in the future to perform actual cutting.
    Currently it just opens the EDB.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        cut_data: Dictionary containing cut information
                  (type, points, id, timestamp, edb_folder)

    Returns:
        bool: True if successful, False otherwise
    """
    print("=" * 70)
    print("EDB Cutter - Execute Cut")
    print("=" * 70)
    print(f"Cut ID: {cut_data.get('id', 'unknown')}")
    print(f"Cut Type: {cut_data.get('type', 'unknown')}")
    print(f"Number of Points: {len(cut_data.get('points', []))}")
    print()

    # Open EDB
    edb = open_edb(edbpath, edbversion)

    # Should Implement actual cutting logic here


    # For now, just print the cut data
    print("Cut data received:")
    print(f"  Type: {cut_data.get('type')}")
    print(f"  Points: {cut_data.get('points')}")
    print(f"  ID: {cut_data.get('id')}")
    print(f"  Timestamp: {cut_data.get('timestamp')}")
    print()

    print("[INFO] Cutting logic not yet implemented - EDB opened successfully")
    print("[TODO] Future implementation will perform actual cutting operation")
    print()

    # Close EDB (important to release resources)
    try:
        edb.close()
        print("[OK] EDB closed successfully")
    except Exception as e:
        print(f"[WARNING] Failed to close EDB: {e}")

    return True


def apply_stackup(edb, cut_data):
    """
    Apply stackup configuration to EDB.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing stackup configuration

    Returns:
        bool: True if successful, False otherwise
    """
    pass


def modify_traces(edb, cut_data):
    """
    Perform cutout operation on EDB using cut geometry.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing cut geometry points

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Performing Cutout Operation")
        print("=" * 70)

        # Extract and validate points from cut_data
        points = cut_data.get("points", [])

        if not points:
            print("ERROR: No points found in cut_data")
            return False
        x_min = points[0][0]
        y_min = points[0][1]
        x_max = points[1][0]
        y_max = points[1][1]

        # bbox 성공 case
        # from pyedb.dotnet.database.geometry.polygon_data import PolygonData
        #
        # # 검색 범위를 polygon으로 정의
        # bbox_points = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
        # search_polygon = PolygonData(edb, create_from_points=True, points=bbox_points)
        #
        # traces_in_bbox = []
        # for prim in edb.modeler.paths:
        #     # intersection_type 사용
        #     int_type = prim.polygon_data._edb_object.GetIntersectionType(search_polygon._edb_object)
        #     if int_type > 0:
        #         traces_in_bbox.append(prim)

        from pyedb.modeler.geometry_operators import GeometryOperators

        # 좌표 추출
        x_min = points[0][0]
        y_min = points[0][1]
        x_max = points[1][0]
        y_max = points[1][1]

        line_start = [x_min, y_min]
        line_end = [x_max, y_max]

        traces_intersecting_line = []

        for prim in edb.modeler.paths:
            # points 프로퍼티 사용 (arc 포함)
            prim_points = prim.polygon_data.points

            # Trace의 각 선분과 검색 선분의 교차 확인
            for i in range(len(prim_points) - 1):
                segment_start = prim_points[i]
                segment_end = prim_points[i + 1]

                if GeometryOperators.are_segments_intersecting(
                        line_start, line_end,
                        segment_start, segment_end,
                        include_collinear=True
                ):
                    traces_intersecting_line.append(prim)
                    break

        print(f"traces_intersecting_line: {traces_intersecting_line}")

    except AttributeError as e:
        print(f"ERROR: Cutout method not available in pyedb - {e}")
        return False
    except Exception as e:
        print(f"ERROR: Cutout operation failed - {e}")
        return False


def remove_and_create_ports(edb, cut_data):
    """
    Remove existing ports and create new ports.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing port operations

    Returns:
        bool: True if successful, False otherwise
    """
    pass


def execute_cuts_on_clone(edbpath, edbversion, cut_data_list):
    """
    Execute multiple cutting operations on a single EDB clone.
    Opens the EDB once, applies all cuts, then closes.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        cut_data_list: List of cut data dictionaries

    Returns:
        bool: True if all cuts successful, False otherwise
    """
    if not cut_data_list:
        print("[WARNING] No cuts provided to execute_cuts_on_clone")
        return True

    print("=" * 70)
    print(f"EDB Cutter - Execute {len(cut_data_list)} Cut(s) on Clone")
    print("=" * 70)
    print(f"EDB Path: {edbpath}")
    print(f"Number of Cuts: {len(cut_data_list)}")
    for i, cut_data in enumerate(cut_data_list, 1):
        print(f"  Cut {i}: {cut_data.get('id', 'unknown')} ({cut_data.get('type', 'unknown')})")
    print()

    # Open EDB once
    try:
        edb = open_edb(edbpath, edbversion)
    except Exception as e:
        print(f"[ERROR] Failed to open EDB: {e}")
        return False

    all_success = True

    # Process each cut
    for i, cut_data in enumerate(cut_data_list, 1):
        print("-" * 50)
        print(f"Processing Cut {i}/{len(cut_data_list)}: {cut_data.get('id', 'unknown')}")
        print("-" * 50)
        print(f"Cut Type: {cut_data.get('type', 'unknown')}")
        print(f"Number of Points: {len(cut_data.get('points', []))}")
        print()

        # Execute cut workflow in sequence
        # 1. Apply stackup
        print("[1/4] Applying stackup...")
        apply_stackup(edb, cut_data)
        print()

        # 2. Modify traces
        print("[2/4] Modifying traces...")
        modify_traces(edb, cut_data)
        print()

        # 3. Remove and create ports
        print("[3/4] Removing and creating ports...")
        remove_and_create_ports(edb, cut_data)
        print()

        # 4. Execute actual cut (to be implemented)
        print("[4/4] Executing cut operation...")
        print("Cut data received:")
        print(f"  Type: {cut_data.get('type')}")
        print(f"  Points: {cut_data.get('points')}")
        print(f"  ID: {cut_data.get('id')}")
        print(f"  Timestamp: {cut_data.get('timestamp')}")
        print()
        print("[TODO] Actual cutting operation to be implemented")
        print()

    # Close EDB once (after all cuts processed)
    try:
        edb.save()
        edb.close()
        print("[OK] EDB closed successfully after processing all cuts")
    except Exception as e:
        print(f"[WARNING] Failed to close EDB: {e}")
        all_success = False

    return all_success

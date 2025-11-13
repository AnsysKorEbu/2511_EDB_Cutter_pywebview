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


def get_line_intersection(a1, a2, b1, b2):
    """
    Calculate exact intersection point of two line segments.

    Args:
        a1: First point of line segment A [x, y]
        a2: Second point of line segment A [x, y]
        b1: First point of line segment B [x, y]
        b2: Second point of line segment B [x, y]

    Returns:
        [x, y]: Intersection point, or None if lines are parallel
    """
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None  # Parallel or coincident

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

    # Calculate intersection point
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    return [x, y]


def modify_traces(edb, cut_data):
    """
    Find traces intersecting with cut polyline, extract net info and trace paths.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing cut geometry points (polyline)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Finding Traces and Extracting Net Info")
        print("=" * 70)

        # Extract and validate points from cut_data
        polyline_points = cut_data.get("points", [])

        if not polyline_points:
            print("ERROR: No points found in cut_data")
            return False

        if len(polyline_points) < 2:
            print(f"ERROR: Insufficient points for polyline (found {len(polyline_points)}, need at least 2)")
            return False

        print(f"Cut geometry type: {cut_data.get('type', 'unknown')}")
        print(f"Polyline points count: {len(polyline_points)}")
        print(f"Polyline coordinates (meters):")
        for idx, pt in enumerate(polyline_points):
            print(f"  Point {idx}: [{pt[0]:.6f}, {pt[1]:.6f}]")
        print()

        from pyedb.modeler.geometry_operators import GeometryOperators

        # Dictionary to store results: {net_name: [{'intersection_point': [x,y], 'trace_path': [[x,y],...], 'trace_obj': prim}]}
        intersection_results = {}

        print("Searching for trace intersections...")
        print()

        # Iterate through all traces in EDB
        for prim in edb.modeler.paths:
            # Get trace properties
            net_name = prim.net_name
            layer_name = prim.layer_name
            trace_width = prim.width
            prim_points = prim.polygon_data.points

            # Skip traces without net name
            if not net_name:
                net_name = "NO_NET"

            trace_found = False

            # Check intersection with each segment of the polyline
            for i in range(len(polyline_points) - 1):
                search_start = polyline_points[i]
                search_end = polyline_points[i + 1]

                # Check each segment of the trace
                for j in range(len(prim_points) - 1):
                    segment_start = prim_points[j]
                    segment_end = prim_points[j + 1]

                    # Check if segments intersect
                    if GeometryOperators.are_segments_intersecting(
                            search_start, search_end,
                            segment_start, segment_end,
                            include_collinear=True
                    ):
                        # Calculate exact intersection point
                        intersection_point = get_line_intersection(
                            search_start, search_end,
                            segment_start, segment_end
                        )

                        if intersection_point:
                            # Initialize net_name entry if not exists
                            if net_name not in intersection_results:
                                intersection_results[net_name] = []

                            # Store intersection info
                            trace_info = {
                                'intersection_point': intersection_point,
                                'trace_path': prim_points,
                                'layer': layer_name,
                                'width': trace_width,
                                'trace_obj': prim,
                                'polyline_segment_index': i,
                                'trace_segment_index': j
                            }
                            intersection_results[net_name].append(trace_info)

                            trace_found = True
                            break  # Found intersection on this trace, move to next polyline segment

                    if trace_found:
                        break  # Already found intersection for this trace

                if trace_found:
                    break  # Move to next trace

        # Print results
        print("-" * 70)
        print("INTERSECTION RESULTS")
        print("-" * 70)
        print(f"Total nets with intersections: {len(intersection_results)}")
        print()

        for net_name, trace_infos in intersection_results.items():
            print(f"Net: {net_name}")
            print(f"  Number of intersections: {len(trace_infos)}")
            for idx, info in enumerate(trace_infos):
                print(f"  [{idx+1}] Intersection point: [{info['intersection_point'][0]:.6f}, {info['intersection_point'][1]:.6f}] meters")
                print(f"      Layer: {info['layer']}")
                print(f"      Trace width: {info['width']:.6f} meters")
                print(f"      Trace path segments: {len(info['trace_path'])}")
                print(f"      Polyline segment: {info['polyline_segment_index']} -> {info['polyline_segment_index']+1}")
            print()

        print("-" * 70)
        print(f"[OK] Found {sum(len(v) for v in intersection_results.values())} total intersection(s)")
        print("-" * 70)
        print()

        # Store results in cut_data for later use
        cut_data['intersection_results'] = intersection_results

        return True

    except AttributeError as e:
        print(f"ERROR: Attribute error - {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"ERROR: Trace finding failed - {e}")
        import traceback
        traceback.print_exc()
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
        print("[1/5] Applying stackup...")
        apply_stackup(edb, cut_data)
        print()

        # 2. Collect port nets (signal/ground classification)
        # print("[2/5] Collecting port nets...")
        # collect_port_nets(edb, cut_data)
        # print()

        # 3. Modify traces
        print("[3/5] Finding and analyzing traces...")
        modify_traces(edb, cut_data)
        print()

        # 4. Remove and create ports
        print("[4/5] Removing and creating ports...")
        remove_and_create_ports(edb, cut_data)
        print()

        # 5. Execute actual cut (to be implemented)
        print("[5/5] Executing cut operation...")
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

"""
EDB Cutter Module

This module handles EDB cutting operations.
Currently only opens EDB, with room for future cutting logic.
"""
import pyedb
from pathlib import Path
from datetime import datetime


def open_edb(edbpath, edbversion, grpc=False):
    """
    Open EDB file using pyedb.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        grpc: Use gRPC mode (default: False)

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
    print(f"gRPC Mode: {grpc}")
    print()

    try:
        print("Opening EDB...")
        edb = pyedb.Edb(edbpath=edbpath, version=edbversion, grpc=grpc)
        print("[OK] EDB opened successfully\n")
        return edb

    except Exception as e:
        print(f"[ERROR] Failed to open EDB: {e}")
        raise


def clone_edbs_for_cuts(original_edb_path, num_clones, edb_version, grpc):
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
        edb = pyedb.Edb(str(original_aedb_folder), version=edb_version, grpc=grpc)
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


def execute_cut(edbpath, edbversion, cut_data, grpc=False):
    """
    Execute cutting operation on EDB.

    This function will be implemented in the future to perform actual cutting.
    Currently it just opens the EDB.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        cut_data: Dictionary containing cut information
                  (type, points, id, timestamp, edb_folder)
        grpc: Use gRPC mode (default: False)

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
    edb = open_edb(edbpath, edbversion, grpc=grpc)

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


def apply_cutout(edb, cut_data):
    """
    Apply cutout operation using polygon boundary to remove traces outside the region.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing polygon points and selected nets

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Applying Cutout")
        print("=" * 70)

        # Get polygon coordinates (custom extent)
        polygon_points = cut_data.get('points', [])
        if not polygon_points or len(polygon_points) < 3:
            print("[WARNING] No valid polygon found. Skipping cutout.")
            print()
            return True

        print(f"Polygon points: {len(polygon_points)}")
        for idx, pt in enumerate(polygon_points):
            print(f"  Point {idx}: [{pt[0]:.6f}, {pt[1]:.6f}] meters")
        print()

        # Get selected nets
        selected_nets = cut_data.get('selected_nets', {})
        signal_nets = selected_nets.get('signal', [])
        power_nets = selected_nets.get('power', [])

        if not signal_nets and not power_nets:
            print("[WARNING] No nets selected. Skipping cutout.")
            print()
            return True

        print(f"Signal nets: {len(signal_nets)} ({', '.join(signal_nets) if signal_nets else 'none'})")
        print(f"Reference nets (power): {len(power_nets)} ({', '.join(power_nets) if power_nets else 'none'})")
        print()

        # Execute cutout
        print("Executing cutout operation...")
        print("This will remove all traces outside the polygon boundary")
        print()

        try:
            netlist = edb.nets.netlist
            filtered_netlist = [n for n in netlist if not signal_nets or n not in signal_nets]
            edb.cutout(
                signal_nets=filtered_netlist,
                reference_nets=signal_nets if signal_nets else [],
                custom_extent=polygon_points,
                custom_extent_units="meter"  # Coordinates are in meters
            )
            print("[OK] Cutout operation completed successfully")
            print()
            return True

        except Exception as cutout_error:
            print(f"[ERROR] Cutout operation failed: {cutout_error}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"[ERROR] Failed to apply cutout: {e}")
        import traceback
        traceback.print_exc()
        return False


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


def is_point_in_polygon(point, polygon_points):
    """
    Check if a point is inside a polygon using ray casting algorithm.

    Args:
        point: Point coordinates [x, y]
        polygon_points: List of polygon vertex coordinates [[x1, y1], [x2, y2], ...]

    Returns:
        bool: True if point is inside polygon, False otherwise
    """
    if not polygon_points or len(polygon_points) < 3:
        return False

    x, y = point
    n = len(polygon_points)
    inside = False

    # Ray casting algorithm: cast a ray from point to the right (+x direction)
    # Count how many times it crosses the polygon edges
    p1x, p1y = polygon_points[0]

    for i in range(1, n + 1):
        p2x, p2y = polygon_points[i % n]

        # Check if ray crosses this edge
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def modify_traces(edb, cut_data):
    """
    Find traces intersecting with cut polyline, extract net info and trace paths.

    Args:
        edb: Opened pyedb.Edb object (gRPC-based)
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

        # Get selected nets from cut_data
        selected_nets_dict = cut_data.get('selected_nets', {'signal': [], 'power': []})
        signal_nets = selected_nets_dict.get('signal', [])
        power_nets = selected_nets_dict.get('power', [])

        # Combine signal and power nets into a single list
        selected_nets = signal_nets + power_nets

        if selected_nets:
            print(f"Filtering for selected nets only:")
            print(f"  Signal nets: {len(signal_nets)} ({', '.join(signal_nets) if signal_nets else 'none'})")
            print(f"  Power nets: {len(power_nets)} ({', '.join(power_nets) if power_nets else 'none'})")
            print(f"  Total selected nets: {len(selected_nets)}")
        else:
            print("[WARNING] No nets selected - will search all nets")
        print()

        from pyedb.modeler.geometry_operators import GeometryOperators
        from ansys.edb.core.utility.value import Value

        # Dictionary to store results
        intersection_results = {}

        print("Searching for trace intersections...")
        print()

        # Iterate through all traces in EDB
        for prim in edb.modeler.paths:
            # Get trace properties
            net_name = prim.net_name
            layer_name = prim.layer_name
            trace_width = prim.width

            # gRPC: polygon_data.points returns PointData objects
            prim_points_raw = prim.polygon_data.points
            # Convert PointData objects to [x, y] lists
            prim_points = [[pt.x.value, pt.y.value] for pt in prim_points_raw]

            # Skip traces without net name
            if not net_name:
                net_name = "NO_NET"

            # Filter: Skip traces not in selected nets list (if nets are selected)
            if selected_nets and net_name not in selected_nets:
                continue

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
                                'width': Value(trace_width) if hasattr(trace_width, 'value') else trace_width,
                                'trace_obj': prim,
                                'polyline_segment_index': i,
                                'trace_segment_index': j
                            }
                            intersection_results[net_name].append(trace_info)

                            trace_found = True
                            break

                    if trace_found:
                        break

                if trace_found:
                    break

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
                width_val = info['width']
                width_display = width_val.value if hasattr(width_val, 'value') else width_val
                print(f"      Trace width: {width_display:.6f} meters")
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


def find_endpoint_pads(edb, net_name):
    """
    Find endpoint pads - pads with only one connection on the same net.
    Returns only is_pin endpoints.

    This function uses PadstackInstance.get_connected_objects() which internally calls
    layout_instance.get_connected_objects(layout_object_instance, True).
    The True parameter ensures only physically connected objects are returned.

    Args:
        edb: Opened pyedb.Edb object
        net_name: Name of the net to analyze

    Returns:
        list: List of PadstackInstance objects that are is_pin endpoints
              (pads with exactly 1 same-net connection or 0 total connections)

    Notes:
        - get_connected_objects() returns Path, Polygon, Rectangle, Circle,
          PadstackInstance, PadstackInstanceTerminal objects
        - Only physically connected objects are returned (not electrical)
        - Only returns pads where is_pin == True
    """
    try:
        padstacks = edb.padstacks.get_instances(net_name=net_name)
        endpoints = []

        for pad in padstacks:
            # Get physically connected objects
            # Internally uses layout_instance.get_connected_objects(layout_object_instance, True)
            # where True = physical connections only
            connected = pad.get_connected_objects()

            # Filter for same net connections (primitives and padstacks)
            # Connected objects can be: Path, Polygon, Rectangle, Circle,
            # PadstackInstance, PadstackInstanceTerminal
            same_net_connections = []
            for obj in connected:
                # Check if object has net_name attribute and matches
                if hasattr(obj, 'net_name') and obj.net_name == net_name:
                    # Exclude self-reference
                    if hasattr(obj, 'id') and obj.id != pad.id:
                        same_net_connections.append(obj)

            # Endpoint criteria:
            # 1. Exactly 1 same-net connection = true endpoint
            # 2. No connections at all = isolated pad (also treated as endpoint)
            # AND must be a pin (is_pin == True)
            if len(same_net_connections) == 1:
                if pad.is_pin:
                    endpoints.append(pad)
            elif len(connected) == 0:
                if pad.is_pin:
                    endpoints.append(pad)

        return endpoints

    except Exception as e:
        print(f"[WARNING] Error finding endpoints for net '{net_name}': {e}")
        return []


def find_endpoint_pads_for_selected_nets(edb, cut_data):
    """
    Find endpoint pads for user-selected signal nets from GUI.
    Selects the two farthest is_pin endpoints relative to the cut line.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing selected_nets and cut points

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Finding Endpoint Pads for Selected Nets")
        print("=" * 70)

        # Get cut polyline points
        cut_points = cut_data.get('points', [])
        if not cut_points or len(cut_points) < 2:
            print("[WARNING] No valid cut points found. Cannot determine farthest endpoints.")
            cut_data['endpoint_pads'] = {}
            return True

        # Calculate cut line direction (from first to last point)
        cut_start = cut_points[0]
        cut_end = cut_points[-1]
        print(f"Cut line: Start [{cut_start[0]:.6f}, {cut_start[1]:.6f}] -> End [{cut_end[0]:.6f}, {cut_end[1]:.6f}]")
        print()

        # Get selected nets from cut_data
        selected_nets = cut_data.get('selected_nets', {})
        print(f"[DEBUG] cut_data keys: {list(cut_data.keys())}")
        print(f"[DEBUG] selected_nets from cut_data: {selected_nets}")
        print(f"[DEBUG] Type of selected_nets: {type(selected_nets)}")

        signal_nets = selected_nets.get('signal', [])
        print(f"[DEBUG] signal_nets extracted: {signal_nets}")
        print(f"[DEBUG] Type of signal_nets: {type(signal_nets)}")
        print(f"[DEBUG] Length of signal_nets: {len(signal_nets) if signal_nets else 0}")

        if not signal_nets:
            print("[WARNING] No signal nets selected. Skipping endpoint finding.")
            print()
            cut_data['endpoint_pads'] = {}
            return True

        print(f"Number of selected signal nets: {len(signal_nets)}")
        print()

        # Dictionary to store endpoint results: {net_name: [two_farthest_pin_endpoints]}
        endpoint_results = {}
        total_endpoints = 0

        # Process each signal net
        for idx, net_name in enumerate(signal_nets, 1):
            print(f"[{idx}/{len(signal_nets)}] Processing net: {net_name}")

            # Find endpoints for this net (already filtered for is_pin)
            endpoints = find_endpoint_pads(edb, net_name)

            if endpoints:
                print(f"  Found {len(endpoints)} pin endpoint(s)")

                if len(endpoints) >= 2:
                    # Calculate projection of each endpoint along cut line direction
                    def project_on_cut_line(endpoint):
                        """Project endpoint position onto cut line direction"""
                        pos = endpoint.position
                        # Vector from cut_start to cut_end
                        dx = cut_end[0] - cut_start[0]
                        dy = cut_end[1] - cut_start[1]
                        # Vector from cut_start to endpoint
                        px = pos[0] - cut_start[0]
                        py = pos[1] - cut_start[1]
                        # Projection parameter t
                        line_length_sq = dx*dx + dy*dy
                        if line_length_sq < 1e-10:
                            return 0.0
                        t = (px*dx + py*dy) / line_length_sq
                        return t

                    # Calculate projections for all endpoints
                    projections = [(ep, project_on_cut_line(ep)) for ep in endpoints]

                    # Sort by projection value
                    projections.sort(key=lambda x: x[1])

                    # Select the two farthest (min and max projection)
                    farthest_two = [projections[0][0], projections[-1][0]]

                    endpoint_results[net_name] = farthest_two
                    total_endpoints += 2

                    print(f"  Selected 2 farthest pin endpoints:")
                    for ep_idx, endpoint in enumerate(farthest_two, 1):
                        pos = endpoint.position
                        comp_name = endpoint.component.name if endpoint.component else "None"
                        proj_value = projections[0][1] if ep_idx == 1 else projections[-1][1]

                        print(f"    [{ep_idx}] {endpoint.name}")
                        print(f"        Position: [{pos[0]:.6f}, {pos[1]:.6f}] meters")
                        print(f"        Component: {comp_name}")
                        print(f"        Projection: {proj_value:.6f}")

                elif len(endpoints) == 1:
                    # Only one pin endpoint found
                    endpoint_results[net_name] = endpoints
                    total_endpoints += 1
                    print(f"  [WARNING] Only 1 pin endpoint found, using it")

                    endpoint = endpoints[0]
                    pos = endpoint.position
                    comp_name = endpoint.component.name if endpoint.component else "None"
                    print(f"    [1] {endpoint.name}")
                    print(f"        Position: [{pos[0]:.6f}, {pos[1]:.6f}] meters")
                    print(f"        Component: {comp_name}")

                else:
                    print(f"  [WARNING] No pin endpoints found for net '{net_name}'")
            else:
                print(f"  [WARNING] No pin endpoints found for net '{net_name}'")

            print()

        # Print summary
        print("-" * 70)
        print("ENDPOINT FINDING SUMMARY")
        print("-" * 70)
        print(f"Total nets processed: {len(signal_nets)}")
        print(f"Nets with pin endpoints found: {len(endpoint_results)}")
        print(f"Total pin endpoints selected: {total_endpoints}")
        print("-" * 70)
        print()

        # Store results in cut_data for later use (e.g., port creation)
        cut_data['endpoint_pads'] = endpoint_results

        return True

    except Exception as e:
        print(f"[ERROR] Failed to find endpoint pads: {e}")
        import traceback
        traceback.print_exc()
        cut_data['endpoint_pads'] = {}
        return False


def remove_and_create_ports(edb, cut_data):
    """
    Remove existing ports and create circuit ports for signal endpoints with power net references.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing endpoint_pads and selected_nets

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Creating Circuit Ports for Endpoints")
        print("=" * 70)

        # Get endpoint pads from cut_data
        endpoint_pads = cut_data.get('endpoint_pads', {})
        if not endpoint_pads:
            print("[WARNING] No endpoint pads found. Skipping port creation.")
            print()
            return True

        # Get selected power nets from cut_data
        selected_nets = cut_data.get('selected_nets', {})
        power_nets = selected_nets.get('power', [])

        if not power_nets:
            print("[WARNING] No power nets selected. Cannot create circuit ports without reference.")
            print()
            return True

        print(f"Signal nets with endpoints: {len(endpoint_pads)}")
        print(f"Power nets for reference: {len(power_nets)} ({', '.join(power_nets)})")
        print()

        # Collect all power net padstack instances (do this once, outside the loop)
        print("Collecting power net pins...")
        all_power_pins = []
        for power_net in power_nets:
            power_pins = edb.padstacks.get_instances(net_name=power_net)
            all_power_pins.extend(power_pins)
            print(f"  {power_net}: {len(power_pins)} pins")

        if not all_power_pins:
            print("[ERROR] No power net pins found in EDB")
            print()
            return False

        print(f"Total power pins collected: {len(all_power_pins)}")
        print()

        # Get polygon coordinates for region checking
        polygon_points = cut_data.get('points', [])
        if not polygon_points or len(polygon_points) < 3:
            print("[WARNING] No valid polygon found in cut_data. Creating ports for all endpoints.")
            use_polygon_filter = False
        else:
            use_polygon_filter = True
            print(f"Polygon region defined with {len(polygon_points)} points")
            print("Only endpoints inside polygon will have ports created")
            print()

        # Track port creation
        total_ports_created = 0
        failed_ports = 0

        # Create ports for each signal endpoint
        for net_name, endpoints in endpoint_pads.items():
            print(f"Processing signal net: {net_name}")
            print(f"  Endpoints: {len(endpoints)}")

            for idx, signal_pin in enumerate(endpoints, 1):
                pin_name = signal_pin.name
                pin_position = signal_pin.position
                component_name = signal_pin.component.name if signal_pin.component else "None"

                print(f"  [{idx}/{len(endpoints)}] Signal pin: {pin_name}")
                print(f"      Position: [{pin_position[0]:.6f}, {pin_position[1]:.6f}]")
                print(f"      Component: {component_name}")

                # Check if endpoint is inside polygon region
                if use_polygon_filter:
                    is_inside = is_point_in_polygon(pin_position, polygon_points)
                    if not is_inside:
                        print(f"      [SKIP] Endpoint outside polygon region - no port created")
                        print()
                        continue
                    else:
                        print(f"      [OK] Endpoint inside polygon region")

                # Find reference power pins
                reference_pins = []

                # Strategy 1: Find power pins in the same component
                if signal_pin.component:
                    component_power_pins = [
                        pin for pin in all_power_pins
                        if pin.component and pin.component.name == component_name
                    ]
                    if component_power_pins:
                        reference_pins = component_power_pins
                        print(f"      Found {len(reference_pins)} power pins in same component")

                # Strategy 2: If no component power pins, find nearest power pins
                if not reference_pins:
                    print(f"      No power pins in component, finding nearest pins...")

                    # Calculate distance to each power pin
                    def calculate_distance(pin):
                        pos = pin.position
                        dx = pos[0] - pin_position[0]
                        dy = pos[1] - pin_position[1]
                        return (dx*dx + dy*dy) ** 0.5

                    # Sort power pins by distance
                    sorted_power_pins = sorted(all_power_pins, key=calculate_distance)

                    # Use closest 3 power pins as reference
                    reference_pins = sorted_power_pins[:3]

                    if reference_pins:
                        nearest_distance = calculate_distance(reference_pins[0])
                        print(f"      Using {len(reference_pins)} nearest power pins (closest: {nearest_distance:.6f}m)")

                # Create circuit port
                if reference_pins:
                    try:
                        # Generate port name: Port_{net_name}_{pin_name_cleaned}
                        port_name = f"Port_{net_name}_{pin_name.replace('-', '_').replace('.', '_')}"

                        # Create circuit port
                        port = signal_pin.create_port(
                            name=port_name,
                            reference=reference_pins,
                            is_circuit_port=True
                        )

                        print(f"      [OK] Created circuit port: {port_name}")
                        total_ports_created += 1

                    except Exception as port_error:
                        print(f"      [ERROR] Failed to create port: {port_error}")
                        failed_ports += 1
                else:
                    print(f"      [ERROR] No reference pins found")
                    failed_ports += 1

                print()

        # Print summary
        print("-" * 70)
        print("PORT CREATION SUMMARY")
        print("-" * 70)
        print(f"Total signal nets processed: {len(endpoint_pads)}")
        print(f"Ports created successfully: {total_ports_created}")
        print(f"Failed port creations: {failed_ports}")
        print("-" * 70)
        print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create ports: {e}")
        import traceback
        traceback.print_exc()
        return False


def execute_cuts_on_clone(edbpath, edbversion, cut_data_list, grpc=False):
    """
    Execute multiple cutting operations on a single EDB clone.
    Opens the EDB once, applies all cuts, then closes.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        cut_data_list: List of cut data dictionaries
        grpc: Use gRPC mode (default: False)

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
        edb = open_edb(edbpath, edbversion, grpc=grpc)
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
        print("[1/6] Applying stackup...")
        apply_stackup(edb, cut_data)
        print()

        # 2. Apply cutout (remove traces outside polygon)
        print("[2/6] Applying cutout...")
        apply_cutout(edb, cut_data)
        print()

        # 3. Find endpoint pads for selected signal nets
        print("[3/6] Finding endpoint pads for selected nets...")
        find_endpoint_pads_for_selected_nets(edb, cut_data)
        print()

        # 4. Modify traces (find intersections)
        print("[4/6] Finding and analyzing trace intersections...")
        modify_traces(edb, cut_data)
        print()

        # 5. Create circuit ports (only for endpoints inside polygon)
        print("[5/6] Creating circuit ports...")
        remove_and_create_ports(edb, cut_data)
        print()

        # 6. Additional cut operations (future implementation)
        print("[6/6] Additional cut operations...")
        print("Cut data received:")
        print(f"  Type: {cut_data.get('type')}")
        print(f"  Points: {cut_data.get('points')}")
        print(f"  ID: {cut_data.get('id')}")
        print(f"  Timestamp: {cut_data.get('timestamp')}")
        print()
        print("[INFO] Cutout operation completed. Additional operations can be added here.")
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

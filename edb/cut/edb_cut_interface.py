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

            from ansys.edb.core.geometry.polygon_data import PolygonData as GrpcPolygonData
            extent_poly = GrpcPolygonData(points=polygon_points)

            edb.cutout(
                signal_nets=filtered_netlist,
                reference_nets=signal_nets if signal_nets else [],
                custom_extent=polygon_points,
                keep_lines_as_path=True,
                custom_extent_units="meter"  # Coordinates are in meters
            )
            print("[OK] Cutout operation completed successfully")

            # Initialize gap_port_info for storing edge intersection data
            cut_data['gap_port_info'] = []

            # 특정 primitive에 대해 잘린 좌표 얻기
            for prim in edb.modeler.primitives:
                if prim.net_name in signal_nets:
                    # 1. 교차 타입 확인 (0=교차없음, 1=완전포함, 2=역포함, 3=부분교차)
                    int_type = extent_poly.intersection_type(prim.polygon_data).value

                    if int_type in [3]:  # 부분 교차하는 경우만
                        # 2. 실제 잘린 polygon 리스트 얻기
                        clipped_polys = extent_poly.intersect([extent_poly], [prim.polygon_data])

                        # 3. 각 잘린 polygon의 좌표 추출
                        for clipped_poly in clipped_polys:
                            if clipped_poly.points:
                                coords = [[pt.x.value, pt.y.value] for pt in clipped_poly.points]
                                print(f"잘린 단면 좌표 ({len(coords)}개 점):")
                                for pt in coords:
                                    print(f"  {pt}")

                                # Find cutout edge intersections
                                print(f"\n=== 정확한 cutout 지점 분석 ===")
                                edge_intersections = find_cutout_edge_intersections(
                                    coords,
                                    polygon_points,
                                    tolerance=1e-6
                                )

                                print(f"발견된 교차 지점: {len(edge_intersections)}개")
                                for idx, (edge, midpoint) in enumerate(edge_intersections, 1):
                                    print(f"\n[{idx}] Edge:")
                                    print(f"  시작점: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] meters")
                                    print(f"  끝점:   [{edge[1][0]:.9f}, {edge[1][1]:.9f}] meters")
                                    print(f"  중심점: [{midpoint[0]:.9f}, {midpoint[1]:.9f}] meters")
                                print("=" * 50)

                                # Store edge intersections info for gap port creation
                                if edge_intersections:
                                    gap_info = {
                                        'net_name': prim.net_name,
                                        'prim_id': prim.id,
                                        'edge_intersections': edge_intersections
                                    }
                                    cut_data['gap_port_info'].append(gap_info)
                                    print(f"[DEBUG] Stored gap port info for {prim.net_name}, primitive ID: {prim.id}")


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


def point_to_line_segment_distance(point, line_start, line_end):
    """
    Calculate the shortest distance from a point to a line segment.

    Args:
        point: [x, y] coordinates
        line_start: [x, y] coordinates of line segment start
        line_end: [x, y] coordinates of line segment end

    Returns:
        float: Shortest distance from point to line segment
    """
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end

    # Calculate line segment length squared
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        # Line segment is actually a point
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    # Calculate parameter t (0 <= t <= 1) for closest point on line segment
    # t represents position along line: 0 = start, 1 = end
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))

    # Calculate closest point on line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Calculate distance from point to closest point
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def find_cutout_edge_intersections(coords, polygon_points, tolerance=1e-6):
    """
    Find points in coords that are very close to polygon_points edges,
    and calculate the midpoint of touching points for each edge.

    Args:
        coords: List of coordinates after cutout [[x, y], ...]
        polygon_points: List of polygon boundary coordinates [[x, y], ...]
        tolerance: Distance threshold for considering a point "touching" an edge (default: 1e-6 meters)

    Returns:
        list: List of tuples (edge, midpoint) where:
            - edge: [[x1, y1], [x2, y2]] - the polygon edge
            - midpoint: [x, y] - midpoint between first and last touching point on this edge
    """
    # Filter out invalid coordinates (very large values that cause overflow)
    MAX_COORD_VALUE = 1e10  # Reasonable maximum for coordinate values
    valid_coords = []

    for coord in coords:
        if len(coord) >= 2:
            x, y = coord[0], coord[1]
            if abs(x) < MAX_COORD_VALUE and abs(y) < MAX_COORD_VALUE:
                valid_coords.append(coord)
            else:
                print(f"[WARNING] Skipping invalid coordinate: [{x}, {y}]")

    print(f"[DEBUG] Total coords: {len(coords)}, Valid coords: {len(valid_coords)}")

    # 1. Generate all edges from polygon_points (closed polygon)
    edges = []
    n = len(polygon_points)

    for i in range(n):
        start = polygon_points[i]
        end = polygon_points[(i + 1) % n]  # Connect last point to first
        edges.append([start, end])

    # 2. For each edge, find coords points that are close to it
    results = []

    for edge in edges:
        touching_points = []

        for coord in valid_coords:  # Use filtered valid_coords instead of coords
            # Calculate distance from coord to edge
            dist = point_to_line_segment_distance(coord, edge[0], edge[1])

            if dist < tolerance:
                touching_points.append(coord)

        # 3. If there are touching points, calculate midpoint
        if len(touching_points) > 0:
            if len(touching_points) == 1:
                # Only one point touching this edge
                midpoint = touching_points[0]
            else:
                # Calculate midpoint between first and last touching point
                first = touching_points[0]
                last = touching_points[-1]
                midpoint = [
                    (first[0] + last[0]) / 2,
                    (first[1] + last[1]) / 2
                ]

            # Store as tuple (edge, midpoint)
            results.append((edge, midpoint))

    return results


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

def create_gap_ports(edb, cut_data):
    """
    Create gap ports on cutout edges using stored edge intersection information.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing gap_port_info and selected_nets

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("EDB Cutter - Creating Gap Ports")
        print("=" * 70)

        # 1. Get gap port info from cut_data
        gap_port_info = cut_data.get('gap_port_info', [])
        if not gap_port_info:
            print("[WARNING] No gap port info found. Skipping gap port creation.")
            print()
            return True

        # 2. Get reference layer from selected_nets
        selected_nets = cut_data.get('selected_nets', {})
        reference_layer = selected_nets.get('reference_layer')

        if not reference_layer:
            print("[ERROR] No reference layer selected. Cannot create gap ports.")
            print("Please select a reference layer in the GUI (Nets tab -> Reference Layer for Gap Ports)")
            print()
            return False

        print(f"Reference layer: {reference_layer}")
        print(f"Gap port candidates: {len(gap_port_info)} primitives")
        print()

        # 3. Create gap ports for each primitive's edge intersections
        total_ports_created = 0
        total_ports_failed = 0

        for gap_info in gap_port_info:
            net_name = gap_info['net_name']
            prim_id = gap_info['prim_id']
            edge_intersections = gap_info['edge_intersections']

            print(f"Processing net: {net_name}")
            print(f"  Primitive ID: {prim_id}")
            print(f"  Edge intersections: {len(edge_intersections)}")

            # 4. Re-fetch primitive by ID (prim object cannot be serialized)
            prim = None
            for p in edb.modeler.primitives:
                if p.id == prim_id:
                    prim = p
                    break

            if not prim:
                print(f"  [WARNING] Primitive {prim_id} not found. Skipping.")
                print()
                continue

            # 5. Create gap port for each edge intersection
            for idx, (edge, midpoint) in enumerate(edge_intersections, 1):
                try:
                    # Generate unique port name
                    port_name = f"GapPort_{net_name}_{prim_id}_{idx}"

                    print(f"  [{idx}/{len(edge_intersections)}] Creating gap port: {port_name}")
                    print(f"      Edge: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] -> [{edge[1][0]:.9f}, {edge[1][1]:.9f}]")
                    print(f"      Terminal point (midpoint): [{midpoint[0]:.9f}, {midpoint[1]:.9f}]")
                    print(f"      Reference layer: {reference_layer}")

                    # Create edge port on polygon
                    edb.source_excitation.create_edge_port_on_polygon(
                        polygon=prim,               # Re-fetched primitive
                        terminal_point=midpoint,    # Midpoint from edge_intersections
                        reference_layer=reference_layer  # From GUI selection
                    )

                    print(f"      [OK] Gap port created successfully")
                    total_ports_created += 1

                except Exception as port_error:
                    print(f"      [ERROR] Failed to create gap port: {port_error}")
                    import traceback
                    traceback.print_exc()
                    total_ports_failed += 1

            print()

        # Print summary
        print("-" * 70)
        print("GAP PORT CREATION SUMMARY")
        print("-" * 70)
        print(f"Total primitives processed: {len(gap_port_info)}")
        print(f"Gap ports created successfully: {total_ports_created}")
        print(f"Failed gap port creations: {total_ports_failed}")
        print("-" * 70)
        print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to create gap ports: {e}")
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
        print("[1/5] Applying stackup...")
        apply_stackup(edb, cut_data)
        print()

        # 2. Find endpoint pads for selected signal nets
        print("[2/5] Finding endpoint pads for selected nets...")
        find_endpoint_pads_for_selected_nets(edb, cut_data)
        print()

        # 3. Apply cutout (remove traces outside polygon)
        print("[3/5] Applying cutout...")
        apply_cutout(edb, cut_data)
        print()

        # 4. Create circuit ports (only for endpoints inside polygon)
        print("[4/5] Creating circuit ports...")
        remove_and_create_ports(edb, cut_data)
        print()

        # 5. Create circuit ports (only for endpoints inside polygon)
        print("[5/5] Creating gap ports...")
        create_gap_ports(edb, cut_data)
        print()

        # 6. Additional cut operations (future implementation)
        print("[6/5] Additional cut operations...")
        print("Cut data received:")
        print(f"  Type: {cut_data.get('type')}")
        print(f"  Points: {cut_data.get('points')}")
        print(f"  ID: {cut_data.get('id')}")
        print(f"  Timestamp: {cut_data.get('timestamp')}")
        print()
        print("[INFO] All cutting operations completed successfully.")
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

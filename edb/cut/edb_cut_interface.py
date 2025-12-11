"""
EDB Cutter Module

This module handles EDB cutting operations.
Currently only opens EDB, with room for future cutting logic.
"""
import pyedb
from pathlib import Path
from datetime import datetime
from util.logger_module import logger


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
    logger.info("=" * 70)
    logger.info("EDB Cutter - Opening EDB")
    logger.info("=" * 70)
    logger.info(f"EDB Path: {edbpath}")
    logger.info(f"EDB Version: {edbversion}")
    logger.info(f"gRPC Mode: {grpc}")
    logger.info("")

    try:
        logger.info("Opening EDB...")
        edb = pyedb.Edb(edbpath=edbpath, version=edbversion, grpc=grpc)
        logger.info("[OK] EDB opened successfully\n")
        return edb

    except Exception as e:
        logger.error(f"Failed to open EDB: {e}")
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
    logger.info("=" * 70)
    logger.info("EDB Cutter - Cloning EDB Files")
    logger.info("=" * 70)
    logger.info(f"Original EDB: {original_edb_path}")
    logger.info(f"Number of clones: {num_clones}")
    logger.info(f"EDB Version: {edb_version}")
    logger.info("")

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
        logger.info(f"Created output directory: {results_dir}")
        logger.info("")

        # Open original EDB
        logger.info(f"Opening original EDB: {original_aedb_folder}")
        edb = pyedb.Edb(str(original_aedb_folder), version=edb_version, grpc=grpc)
        logger.info("[OK] Original EDB opened successfully")
        logger.info("")

        # Clone EDB files
        cloned_paths = []
        logger.info(f"Starting cloning process ({num_clones} clones)...")
        logger.info("")

        for i in range(1, num_clones + 1):
            clone_name = f"{original_name}_{i:03d}.aedb"
            clone_path = results_dir / clone_name

            logger.info(f"[{i}/{num_clones}] Cloning to: {clone_path}")

            # Use save_as to create clone
            edb.save_as(str(clone_path))
            cloned_paths.append(str(clone_path))

            logger.info(f"Clone {i} created successfully")
            logger.info("")

        # Close original EDB
        edb.close()
        logger.info("[OK] Original EDB closed")
        logger.info("")

        logger.info("=" * 70)
        logger.info(f"[SUCCESS] Created {num_clones} EDB clones")
        logger.info("=" * 70)
        logger.info("")

        return cloned_paths

    except Exception as e:
        logger.error(f"Failed to clone EDB files: {e}")
        import traceback
        traceback.print_exc()
        raise



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
        logger.info("=" * 70)
        logger.info("EDB Cutter - Applying Cutout")
        logger.info("=" * 70)

        # Get polygon coordinates (custom extent)
        polygon_points = cut_data.get('points', [])
        if not polygon_points or len(polygon_points) < 3:
            logger.info("[WARNING] No valid polygon found. Skipping cutout.")
            logger.info("")
            return True

        logger.info(f"Polygon points: {len(polygon_points)}")
        for idx, pt in enumerate(polygon_points):
            logger.info(f"  Point {idx}: [{pt[0]:.6f}, {pt[1]:.6f}] meters")
        logger.info("")

        # Get selected nets
        selected_nets = cut_data.get('selected_nets', {})
        signal_nets = selected_nets.get('signal', [])
        power_nets = selected_nets.get('power', [])

        if not signal_nets and not power_nets:
            logger.info("[WARNING] No nets selected. Skipping cutout.")
            logger.info("")
            return True

        logger.info(f"Signal nets: {len(signal_nets)} ({', '.join(signal_nets) if signal_nets else 'none'})")
        logger.info(f"Reference nets (power): {len(power_nets)} ({', '.join(power_nets) if power_nets else 'none'})")
        logger.info("")

        # Execute cutout
        logger.info("Executing cutout operation...")
        logger.info("This will remove all traces outside the polygon boundary")
        logger.info("")

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
            logger.info("[OK] Cutout operation completed successfully")

            # Initialize gap_port_info for storing edge intersection data
            cut_data['gap_port_info'] = []

            for prim in edb.modeler.primitives:
                if prim.net_name in signal_nets:
                    int_type = extent_poly.intersection_type(prim.polygon_data).value

                    if int_type in [3]:
                        clipped_polys = extent_poly.intersect([extent_poly], [prim.polygon_data])

                        for clipped_poly in clipped_polys:
                            if clipped_poly.points:
                                coords = [[pt.x.value, pt.y.value] for pt in clipped_poly.points]
                                logger.info(f"Clipped coordinates ({len(coords)} points):")
                                for pt in coords:
                                    logger.info(f"  {pt}")

                                # Find cutout edge intersections
                                logger.info(f"\n=== Cutout Edge Analysis ===")
                                edge_intersections = find_cutout_edge_intersections(
                                    coords,
                                    polygon_points,
                                    tolerance=1e-6
                                )

                                logger.info(f"Found edge intersections: {len(edge_intersections)}")
                                for idx, (edge, midpoint) in enumerate(edge_intersections, 1):
                                    logger.info(f"\n[{idx}] Edge:")
                                    logger.info(f"  Start: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] meters")
                                    logger.info(f"  End:   [{edge[1][0]:.9f}, {edge[1][1]:.9f}] meters")
                                    logger.info(f"  Center: [{midpoint[0]:.9f}, {midpoint[1]:.9f}] meters")
                                logger.info("=" * 50)

                                # Store edge intersections info for gap port creation
                                if edge_intersections:
                                    gap_info = {
                                        'net_name': prim.net_name,
                                        'prim_id': prim.id,
                                        'edge_intersections': edge_intersections
                                    }
                                    cut_data['gap_port_info'].append(gap_info)
                                    logger.debug(f"Stored gap port info for {prim.net_name}, primitive ID: {prim.id}")


            return True

        except Exception as cutout_error:
            logger.error(f"Cutout operation failed: {cutout_error}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"Failed to apply cutout: {e}")
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
                logger.warning(f"Skipping invalid coordinate: [{x}, {y}]")

    logger.debug(f"Total coords: {len(coords)}, Valid coords: {len(valid_coords)}")

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
        logger.warning(f"Error finding endpoints for net '{net_name}': {e}")
        return []


def calculate_point_distance(pt1, pt2):
    """
    Calculate Euclidean distance between two points.

    Args:
        pt1: First point [x, y]
        pt2: Second point [x, y]

    Returns:
        float: Euclidean distance
    """
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]
    return (dx * dx + dy * dy) ** 0.5


def find_nearest_pad_to_point(edb, net_name, point):
    """
    Find the nearest pad (is_pin=True) to a given point on a specific net.
    No distance limit - always returns the closest pad.

    Args:
        edb: Opened pyedb.Edb object
        net_name: Name of the net
        point: [x, y] coordinates to search around

    Returns:
        tuple: (PadstackInstance or None, distance in meters)
               Returns (None, inf) if no pins found on the net
    """
    try:
        padstacks = edb.padstacks.get_instances(net_name=net_name)

        nearest_pad = None
        min_distance = float('inf')

        for pad in padstacks:
            # Only consider component pins
            if pad.is_pin:
                # Skip UnnamedODBPadstack (invalid/unnamed pads from ODB)
                try:
                    if pad.padstack_def and pad.padstack_def.name == 'UnnamedODBPadstack':
                        continue
                except (AttributeError, Exception):
                    pass  # If padstack_def is not accessible, continue anyway

                pos = pad.position
                dist = calculate_point_distance(point, pos)

                if dist < min_distance:
                    min_distance = dist
                    nearest_pad = pad

        return nearest_pad, min_distance

    except Exception as e:
        logger.warning(f"Error finding nearest pad for net '{net_name}': {e}")
        return None, float('inf')


def find_net_extreme_endpoints(edb, net_name, tolerance=1e-3):
    """
    Find the two farthest endpoints of a net.

    Strategy:
    1. Collect all path endpoints (start and end of each center_line)
    2. Merge points within tolerance distance (treat as connected)
    3. Find the two farthest points among merged endpoints

    Args:
        edb: Opened pyedb.Edb object
        net_name: Name of the net to analyze
        tolerance: Distance threshold for merging close points (default: 1e-3 meters)

    Returns:
        dict or None: {
            'start': [x, y] coordinates of one extreme endpoint,
            'end': [x, y] coordinates of other extreme endpoint,
            'distance': float distance between them,
            'total_paths': int number of paths in net,
            'merged_endpoints': int number of unique endpoints after merging
        }
    """
    # Get all paths for this net
    paths = edb.modeler.get_primitives(net_name=net_name, prim_type="path")

    if not paths:
        return None

    # 1. Collect all endpoints
    endpoints = []
    for path in paths:
        if len(path.center_line) >= 2:
            endpoints.append(path.center_line[0])   # start
            endpoints.append(path.center_line[-1])  # end

    if len(endpoints) < 2:
        return None

    # 2. Merge close points (within tolerance)
    merged = []
    used = [False] * len(endpoints)

    for i, pt in enumerate(endpoints):
        if used[i]:
            continue

        # Find all points close to this one
        cluster = [pt]
        used[i] = True

        for j in range(i+1, len(endpoints)):
            if not used[j]:
                if calculate_point_distance(pt, endpoints[j]) < tolerance:
                    cluster.append(endpoints[j])
                    used[j] = True

        # Average the cluster to get merged point
        avg_x = sum(p[0] for p in cluster) / len(cluster)
        avg_y = sum(p[1] for p in cluster) / len(cluster)
        merged.append([avg_x, avg_y])

    # 3. Find two farthest points
    max_dist = 0
    farthest_pair = None

    for i, pt1 in enumerate(merged):
        for pt2 in merged[i+1:]:
            dist = calculate_point_distance(pt1, pt2)
            if dist > max_dist:
                max_dist = dist
                farthest_pair = (pt1, pt2)

    if farthest_pair:
        return {
            'start': farthest_pair[0],
            'end': farthest_pair[1],
            'distance': max_dist,
            'total_paths': len(paths),
            'merged_endpoints': len(merged)
        }

    return None


def find_endpoint_pads_for_selected_nets(edb, cut_data):
    try:

        logger.info("=" * 70)
        logger.info("EDB Cutter - Finding Endpoint Pads for Selected Nets")
        logger.info("=" * 70)

        # Get selected nets from cut_data
        selected_nets = cut_data.get('selected_nets', {})
        logger.debug(f"cut_data keys: {list(cut_data.keys())}")
        logger.debug(f"selected_nets from cut_data: {selected_nets}")
        logger.debug(f"Type of selected_nets: {type(selected_nets)}")

        signal_nets = selected_nets.get('signal', [])
        logger.debug(f"signal_nets extracted: {signal_nets}")
        logger.debug(f"Type of signal_nets: {type(signal_nets)}")
        logger.debug(f"Length of signal_nets: {len(signal_nets) if signal_nets else 0}")



        # Get cut polyline points
        cut_points = cut_data.get('points', [])
        if not cut_points or len(cut_points) < 2:
            logger.info("[WARNING] No valid cut points found. Cannot determine farthest endpoints.")
            cut_data['endpoint_pads'] = {}
            return True

        # Find extreme endpoints and nearest pads for each net
        logger.info("=" * 70)
        logger.info("Finding Endpoint Pads Based on Net Extreme Points")
        logger.info("=" * 70)
        logger.info("")

        # Dictionary to store endpoint results: {net_name: [endpoint_pads]}
        endpoint_results = {}
        total_endpoints = 0

        for idx, net_name in enumerate(signal_nets, 1):
            logger.info(f"[{idx}/{len(signal_nets)}] Processing net: {net_name}")

            # Step 1: Find extreme endpoints of the net (tolerance 1e-3 for merging)
            net_info = find_net_extreme_endpoints(edb, net_name, tolerance=1e-3)

            if not net_info:
                logger.info(f"  [WARNING] Could not find endpoints for this net")
                logger.info("")
                continue

            logger.info(f"  Total paths: {net_info['total_paths']}")
            logger.info(f"  Unique endpoints after merging: {net_info['merged_endpoints']}")
            logger.info(f"  Start point: [{net_info['start'][0]:.6f}, {net_info['start'][1]:.6f}] m")
            logger.info(f"  End point:   [{net_info['end'][0]:.6f}, {net_info['end'][1]:.6f}] m")
            logger.info(f"  Distance between extremes: {net_info['distance']:.6f} m")
            logger.info("")

            # Step 2: Find nearest pads to each extreme endpoint
            endpoint_pads = []

            # Find pad near start point
            start_pad, start_dist = find_nearest_pad_to_point(
                edb, net_name, net_info['start']
            )

            if start_pad:
                endpoint_pads.append(start_pad)
                pos = start_pad.position
                comp_name = start_pad.component.name if start_pad.component else "None"
                logger.info(f"  [START] Found nearest pad: {start_pad.name}")
                logger.info(f"      Position: [{pos[0]:.6f}, {pos[1]:.6f}] m")
                logger.info(f"      Component: {comp_name}")
                logger.info(f"      Distance from extreme point: {start_dist:.6f} m")
            else:
                logger.info(f"  [START] No pin found on this net")

            logger.info("")

            # Find pad near end point
            end_pad, end_dist = find_nearest_pad_to_point(
                edb, net_name, net_info['end']
            )

            if end_pad:
                # Check if it's the same pad as start (avoid duplicates)
                if not start_pad or end_pad.id != start_pad.id:
                    endpoint_pads.append(end_pad)
                    pos = end_pad.position
                    comp_name = end_pad.component.name if end_pad.component else "None"
                    logger.info(f"  [END] Found nearest pad: {end_pad.name}")
                    logger.info(f"      Position: [{pos[0]:.6f}, {pos[1]:.6f}] m")
                    logger.info(f"      Component: {comp_name}")
                    logger.info(f"      Distance from extreme point: {end_dist:.6f} m")
                else:
                    logger.info(f"  [END] Same pad as start point - skipped")
            else:
                logger.info(f"  [END] No pin found on this net")

            logger.info("")

            # Store results
            if endpoint_pads:
                endpoint_results[net_name] = endpoint_pads
                total_endpoints += len(endpoint_pads)
                logger.info(f"  [OK] Found {len(endpoint_pads)} endpoint pad(s) for this net")
            else:
                logger.info(f"  [WARNING] No endpoint pads found for this net")

            logger.info("")

        # Print summary
        logger.info("-" * 70)
        logger.info("ENDPOINT FINDING SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Total nets processed: {len(signal_nets)}")
        logger.info(f"Nets with pin endpoints found: {len(endpoint_results)}")
        logger.info(f"Total pin endpoints selected: {total_endpoints}")
        logger.info("-" * 70)
        logger.info("")

        # Store results in cut_data for later use (e.g., port creation)
        cut_data['endpoint_pads'] = endpoint_results

        return True

    except Exception as e:
        logger.error(f"Failed to find endpoint pads: {e}")
        import traceback
        traceback.print_exc()
        cut_data['endpoint_pads'] = {}
        return False


def find_endpoint_pads_for_selected_nets_bu(edb, cut_data):
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
        logger.info("=" * 70)
        logger.info("EDB Cutter - Finding Endpoint Pads for Selected Nets")
        logger.info("=" * 70)

        # Get cut polyline points
        cut_points = cut_data.get('points', [])
        if not cut_points or len(cut_points) < 2:
            logger.info("[WARNING] No valid cut points found. Cannot determine farthest endpoints.")
            cut_data['endpoint_pads'] = {}
            return True

        # Calculate cut line direction (from first to last point)
        cut_start = cut_points[0]
        cut_end = cut_points[-1]
        logger.info(f"Cut line: Start [{cut_start[0]:.6f}, {cut_start[1]:.6f}] -> End [{cut_end[0]:.6f}, {cut_end[1]:.6f}]")
        logger.info("")

        # Get selected nets from cut_data
        selected_nets = cut_data.get('selected_nets', {})
        logger.debug(f"cut_data keys: {list(cut_data.keys())}")
        logger.debug(f"selected_nets from cut_data: {selected_nets}")
        logger.debug(f"Type of selected_nets: {type(selected_nets)}")

        signal_nets = selected_nets.get('signal', [])
        logger.debug(f"signal_nets extracted: {signal_nets}")
        logger.debug(f"Type of signal_nets: {type(signal_nets)}")
        logger.debug(f"Length of signal_nets: {len(signal_nets) if signal_nets else 0}")

        if not signal_nets:
            logger.info("[WARNING] No signal nets selected. Skipping endpoint finding.")
            logger.info("")
            cut_data['endpoint_pads'] = {}
            return True

        logger.info(f"Number of selected signal nets: {len(signal_nets)}")
        logger.info("")

        # Dictionary to store endpoint results: {net_name: [two_farthest_pin_endpoints]}
        endpoint_results = {}
        total_endpoints = 0

        # Process each signal net
        for idx, net_name in enumerate(signal_nets, 1):
            logger.info(f"[{idx}/{len(signal_nets)}] Processing net: {net_name}")

            # Find endpoints for this net (already filtered for is_pin)
            endpoints = find_endpoint_pads(edb, net_name)

            if endpoints:
                logger.info(f"  Found {len(endpoints)} pin endpoint(s)")

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

                    logger.info(f"  Selected 2 farthest pin endpoints:")
                    for ep_idx, endpoint in enumerate(farthest_two, 1):
                        pos = endpoint.position
                        comp_name = endpoint.component.name if endpoint.component else "None"
                        proj_value = projections[0][1] if ep_idx == 1 else projections[-1][1]

                        logger.info(f"    [{ep_idx}] {endpoint.name}")
                        logger.info(f"        Position: [{pos[0]:.6f}, {pos[1]:.6f}] meters")
                        logger.info(f"        Component: {comp_name}")
                        logger.info(f"        Projection: {proj_value:.6f}")

                elif len(endpoints) == 1:
                    # Only one pin endpoint found
                    endpoint_results[net_name] = endpoints
                    total_endpoints += 1
                    logger.info(f"  [WARNING] Only 1 pin endpoint found, using it")

                    endpoint = endpoints[0]
                    pos = endpoint.position
                    comp_name = endpoint.component.name if endpoint.component else "None"
                    logger.info(f"    [1] {endpoint.name}")
                    logger.info(f"        Position: [{pos[0]:.6f}, {pos[1]:.6f}] meters")
                    logger.info(f"        Component: {comp_name}")

                else:
                    logger.info(f"  [WARNING] No pin endpoints found for net '{net_name}'")
            else:
                logger.info(f"  [WARNING] No pin endpoints found for net '{net_name}'")

            logger.info("")

        # Print summary
        logger.info("-" * 70)
        logger.info("ENDPOINT FINDING SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Total nets processed: {len(signal_nets)}")
        logger.info(f"Nets with pin endpoints found: {len(endpoint_results)}")
        logger.info(f"Total pin endpoints selected: {total_endpoints}")
        logger.info("-" * 70)
        logger.info("")

        # Store results in cut_data for later use (e.g., port creation)
        cut_data['endpoint_pads'] = endpoint_results

        return True

    except Exception as e:
        logger.error(f"Failed to find endpoint pads: {e}")
        import traceback
        traceback.print_exc()
        cut_data['endpoint_pads'] = {}
        return False


def is_valid_padstack(pad):
    """
    Check if padstack instance is still valid after cutout operation.

    Args:
        pad: PadstackInstance object

    Returns:
        bool: True if valid, False if deleted/invalid
    """
    try:
        # Test multiple properties/methods to ensure object is truly valid
        _ = pad.name
        _ = pad.position
        _ = pad.id  # This will fail if underlying C++ object is null

        # Skip UnnamedODBPadstack (invalid/unnamed pads from ODB)
        if pad.padstack_def and pad.padstack_def.name == 'UnnamedODBPadstack':
            return False

        return True
    except (AttributeError, RuntimeError, Exception):
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
        logger.info("=" * 70)
        logger.info("EDB Cutter - Creating Circuit Ports for Endpoints")
        logger.info("=" * 70)

        # Get endpoint pads from cut_data
        endpoint_pads = cut_data.get('endpoint_pads', {})
        if not endpoint_pads:
            logger.info("[WARNING] No endpoint pads found. Skipping port creation.")
            logger.info("")
            return True

        # Validate endpoints before processing (filter out pads deleted by cutout)
        logger.info("Validating endpoint pads after cutout...")
        valid_endpoint_pads = {}
        stats = {
            'total_nets': 0,
            'nets_with_2': 0,
            'nets_with_1': 0,
            'nets_with_0': 0
        }

        for net_name, endpoints in endpoint_pads.items():
            stats['total_nets'] += 1

            # Filter valid endpoints (not deleted by cutout)
            valid_endpoints = [ep for ep in endpoints if is_valid_padstack(ep)]

            if len(valid_endpoints) == 2:
                stats['nets_with_2'] += 1
                valid_endpoint_pads[net_name] = valid_endpoints
            elif len(valid_endpoints) == 1:
                stats['nets_with_1'] += 1
                valid_endpoint_pads[net_name] = valid_endpoints
            else:
                stats['nets_with_0'] += 1
                logger.info(f"  [SKIP] Net '{net_name}': No valid endpoints (both deleted by cutout)")

        logger.info(f"  Nets with 2 valid endpoints: {stats['nets_with_2']}")
        logger.info(f"  Nets with 1 valid endpoint: {stats['nets_with_1']}")
        logger.info(f"  Nets with 0 valid endpoints (skipped): {stats['nets_with_0']}")
        logger.info("")

        # Use only validated endpoints
        endpoint_pads = valid_endpoint_pads

        if not endpoint_pads:
            logger.info("[WARNING] No valid endpoint pads remaining after validation. Skipping port creation.")
            logger.info("")
            return True

        # Get selected power nets from cut_data
        selected_nets = cut_data.get('selected_nets', {})
        power_nets = selected_nets.get('power', [])

        if not power_nets:
            logger.info("[WARNING] No power nets selected. Cannot create circuit ports without reference.")
            logger.info("")
            return True

        logger.info(f"Signal nets with endpoints: {len(endpoint_pads)}")
        logger.info(f"Power nets for reference: {len(power_nets)} ({', '.join(power_nets)})")
        logger.info("")

        # Collect all power net padstack instances (do this once, outside the loop)
        logger.info("Collecting power net pins...")
        all_power_pins = []
        for power_net in power_nets:
            power_pins = edb.padstacks.get_instances(net_name=power_net)
            all_power_pins.extend(power_pins)
            logger.info(f"  {power_net}: {len(power_pins)} pins")

        if not all_power_pins:
            logger.info("[ERROR] No power net pins found in EDB")
            logger.info("")
            return False

        logger.info(f"Total power pins collected: {len(all_power_pins)}")
        logger.info("")

        # Get polygon coordinates for region checking
        polygon_points = cut_data.get('points', [])
        if not polygon_points or len(polygon_points) < 3:
            logger.info("[WARNING] No valid polygon found in cut_data. Creating ports for all endpoints.")
            use_polygon_filter = False
        else:
            use_polygon_filter = True
            logger.info(f"Polygon region defined with {len(polygon_points)} points")
            logger.info("Only endpoints inside polygon will have ports created")
            logger.info("")

        # Track port creation
        total_ports_created = 0
        failed_ports = 0

        # Create ports for each signal endpoint
        for net_name, endpoints in endpoint_pads.items():
            logger.info(f"Processing signal net: {net_name}")
            logger.info(f"  Endpoints: {len(endpoints)}")

            for idx, signal_pin in enumerate(endpoints, 1):
                # Endpoints are pre-validated, safe to access properties
                pin_name = signal_pin.name
                pin_position = signal_pin.position
                component_name = signal_pin.component.name if signal_pin.component else "None"

                logger.info(f"  [{idx}/{len(endpoints)}] Signal pin: {pin_name}")
                logger.info(f"      Position: [{pin_position[0]:.6f}, {pin_position[1]:.6f}]")
                logger.info(f"      Component: {component_name}")

                # Check if endpoint is inside polygon region
                if use_polygon_filter:
                    is_inside = is_point_in_polygon(pin_position, polygon_points)
                    if not is_inside:
                        logger.info(f"      [SKIP] Endpoint outside polygon region - no port created")
                        logger.info("")
                        continue
                    else:
                        logger.info(f"      [OK] Endpoint inside polygon region")

                # Find reference power pins
                reference_pins = []

                # Strategy 1: Find power pins in the same component
                if signal_pin.component:
                    component_power_pins = []
                    for pin in all_power_pins:
                        try:
                            # Check if power pin is still valid
                            if pin.component and pin.component.name == component_name:
                                component_power_pins.append(pin)
                        except (AttributeError, RuntimeError, Exception):
                            # Skip invalid power pins (deleted by cutout)
                            continue

                    if component_power_pins:
                        reference_pins = component_power_pins
                        logger.info(f"      Found {len(reference_pins)} power pins in same component")

                # Strategy 2: If no component power pins, find nearest power pins
                if not reference_pins:
                    logger.info(f"      No power pins in component, finding nearest pins...")

                    # Calculate distance to each power pin (skip invalid pins)
                    def calculate_distance(pin):
                        try:
                            pos = pin.position
                            dx = pos[0] - pin_position[0]
                            dy = pos[1] - pin_position[1]
                            return (dx*dx + dy*dy) ** 0.5
                        except (AttributeError, RuntimeError, Exception):
                            # Return infinite distance for invalid pins
                            return float('inf')

                    # Filter out invalid power pins
                    valid_power_pins = []
                    for pin in all_power_pins:
                        try:
                            _ = pin.position  # Test if pin is valid
                            valid_power_pins.append(pin)
                        except (AttributeError, RuntimeError, Exception):
                            continue

                    if valid_power_pins:
                        # Sort power pins by distance
                        sorted_power_pins = sorted(valid_power_pins, key=calculate_distance)

                        # Use closest 3 power pins as reference
                        reference_pins = sorted_power_pins[:3]

                        if reference_pins:
                            nearest_distance = calculate_distance(reference_pins[0])
                            logger.info(f"      Using {len(reference_pins)} nearest power pins (closest: {nearest_distance:.6f}m)")
                    else:
                        logger.info(f"      [WARNING] No valid power pins found (all deleted by cutout)")

                # Create circuit port
                if reference_pins:
                    try:
                        # Generate port name: Port_{net_name}_{pin_name_cleaned}
                        port_name = f"c_{net_name}"

                        port = signal_pin.create_port(
                            name=port_name,
                            reference=reference_pins,
                            is_circuit_port=True
                        )
                        # Set positive terminal name explicitly
                        port.name = port_name

                        logger.info(f"      [OK] Created circuit port: {port_name}")
                        total_ports_created += 1

                    except Exception as port_error:
                        logger.info(f"      [ERROR] Failed to create port: {port_error}")
                        failed_ports += 1
                else:
                    logger.info(f"      [ERROR] No reference pins found")
                    failed_ports += 1

                logger.info("")

        # Print summary
        logger.info("-" * 70)
        logger.info("PORT CREATION SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Total signal nets processed: {len(endpoint_pads)}")
        logger.info(f"Ports created successfully: {total_ports_created}")
        logger.info(f"Failed port creations: {failed_ports}")
        logger.info("-" * 70)
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"Failed to create ports: {e}")
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
        logger.info("=" * 70)
        logger.info("EDB Cutter - Creating Gap Ports")
        logger.info("=" * 70)

        # 1. Get gap port info from cut_data
        gap_port_info = cut_data.get('gap_port_info', [])
        if not gap_port_info:
            logger.info("[WARNING] No gap port info found. Skipping gap port creation.")
            logger.info("")
            return True

        # 2. Get reference layer from selected_nets
        selected_nets = cut_data.get('selected_nets', {})
        reference_layer = selected_nets.get('reference_layer')

        if not reference_layer:
            logger.info("[ERROR] No reference layer selected. Cannot create gap ports.")
            logger.info("Please select a reference layer in the GUI (Nets tab -> Reference Layer for Gap Ports)")
            logger.info("")
            return False

        logger.info(f"Reference layer: {reference_layer}")
        logger.info(f"Gap port candidates: {len(gap_port_info)} primitives")
        logger.info("")

        # 3. Create gap ports for each primitive's edge intersections
        total_ports_created = 0
        total_ports_failed = 0

        for gap_info in gap_port_info:
            net_name = gap_info['net_name']
            prim_id = gap_info['prim_id']
            edge_intersections = gap_info['edge_intersections']

            logger.info(f"Processing net: {net_name}")
            logger.info(f"  Primitive ID: {prim_id}")
            logger.info(f"  Edge intersections: {len(edge_intersections)}")

            # 4. Re-fetch primitive by ID (prim object cannot be serialized)
            prim = None
            for p in edb.modeler.primitives:
                if p.id == prim_id:
                    prim = p
                    break

            if not prim:
                logger.info(f"  [WARNING] Primitive {prim_id} not found. Skipping.")
                logger.info("")
                continue

            # 5. Create gap port for each edge intersection
            for idx, (edge, midpoint) in enumerate(edge_intersections):
                try:
                    # Generate unique port name (0-based indexing: netname_0, netname_1, ...)
                    port_name = f"{idx}_{net_name}"

                    logger.info(f"  [{idx+1}/{len(edge_intersections)}] Creating gap port: {port_name}")
                    logger.info(f"      Edge: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] -> [{edge[1][0]:.9f}, {edge[1][1]:.9f}]")
                    logger.info(f"      Terminal point (midpoint): [{midpoint[0]:.9f}, {midpoint[1]:.9f}]")
                    logger.info(f"      Reference layer: {reference_layer}")

                    # Create edge port on polygon
                    edb.source_excitation.create_edge_port_on_polygon(
                        polygon=prim,               # Re-fetched primitive
                        terminal_point=midpoint,    # Midpoint from edge_intersections
                        reference_layer=reference_layer,  # From GUI selection
                        port_name=port_name         # Use net name-based port name
                    )

                    logger.info(f"      [OK] Gap port created successfully")
                    total_ports_created += 1

                except Exception as port_error:
                    logger.info(f"      [ERROR] Failed to create gap port: {port_error}")
                    import traceback
                    traceback.print_exc()
                    total_ports_failed += 1

            logger.info("")

        # Print summary
        logger.info("-" * 70)
        logger.info("GAP PORT CREATION SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Total primitives processed: {len(gap_port_info)}")
        logger.info(f"Gap ports created successfully: {total_ports_created}")
        logger.info(f"Failed gap port creations: {total_ports_failed}")
        logger.info("-" * 70)
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"Failed to create gap ports: {e}")
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
        logger.info("[WARNING] No cuts provided to execute_cuts_on_clone")
        return True

    logger.info("=" * 70)
    logger.info(f"EDB Cutter - Execute {len(cut_data_list)} Cut(s) on Clone")
    logger.info("=" * 70)
    logger.info(f"EDB Path: {edbpath}")
    logger.info(f"Number of Cuts: {len(cut_data_list)}")
    for i, cut_data in enumerate(cut_data_list, 1):
        logger.info(f"  Cut {i}: {cut_data.get('id', 'unknown')} ({cut_data.get('type', 'unknown')})")
    logger.info("")

    # Open EDB once
    try:
        edb = open_edb(edbpath, edbversion, grpc=grpc)
    except Exception as e:
        logger.error(f"Failed to open EDB: {e}")
        return False

    all_success = True

    # Process each cut
    for i, cut_data in enumerate(cut_data_list, 1):
        logger.info("-" * 50)
        logger.info(f"Processing Cut {i}/{len(cut_data_list)}: {cut_data.get('id', 'unknown')}")
        logger.info("-" * 50)
        logger.info(f"Cut Type: {cut_data.get('type', 'unknown')}")
        logger.info(f"Number of Points: {len(cut_data.get('points', []))}")
        logger.info("")

        # Execute cut workflow in sequence
        # 1. Find endpoint pads for selected signal nets
        logger.info("[1/4] Finding endpoint pads for selected nets...")
        find_endpoint_pads_for_selected_nets(edb, cut_data)
        logger.info("")

        # 2. Apply cutout (remove traces outside polygon)
        logger.info("[2/4] Applying cutout...")
        apply_cutout(edb, cut_data)
        logger.info("")

        # 3. Create circuit ports (only for endpoints inside polygon)
        logger.info("[3/4] Creating circuit ports...")
        remove_and_create_ports(edb, cut_data)
        logger.info("")

        # 4. Create gap ports (only for endpoints inside polygon)
        logger.info("[4/4] Creating gap ports...")
        create_gap_ports(edb, cut_data)
        logger.info("")

        # 6. Additional cut operations (future implementation)
        logger.info("[6/5] Additional cut operations...")
        logger.info("Cut data received:")
        logger.info(f"  Type: {cut_data.get('type')}")
        logger.info(f"  Points: {cut_data.get('points')}")
        logger.info(f"  ID: {cut_data.get('id')}")
        logger.info(f"  Timestamp: {cut_data.get('timestamp')}")
        logger.info("")
        logger.info("[INFO] All cutting operations completed successfully.")
        logger.info("")

    # Close EDB once (after all cuts processed)
    try:
        edb.save()
        edb.close()
        logger.info("[OK] EDB closed successfully after processing all cuts")
    except Exception as e:
        logger.warning(f"Failed to close EDB: {e}")
        all_success = False

    return all_success

"""
EDB Manager Module

This module handles EDB file management and geometric utility functions.
Provides functions for opening, cloning, and basic geometric calculations.
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
        grpc: Use gRPC mode

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


def execute_cuts_on_clone(edbpath, edbversion, cut_data_list, grpc=False, stackup_xml_path=None):
    """
    Execute multiple cutting operations on a single EDB clone.
    Opens the EDB once, applies all cuts, then closes.

    Args:
        edbpath: Path to EDB file (edb.def path)
        edbversion: AEDT version string (e.g., "2025.1")
        cut_data_list: List of cut data dictionaries
        grpc: Use gRPC mode (default: False)
        stackup_xml_path: Optional path to stackup XML file to load

    Returns:
        bool: True if all cuts successful, False otherwise
    """
    # Import here to avoid circular dependency
    from .net_port_handler import (
        find_endpoint_pads_for_selected_nets,
        apply_cutout,
        remove_and_create_ports,
        create_gap_ports
    )

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

    # Load stackup if XML path provided
    if stackup_xml_path:
        try:
            xml_path_str = str(stackup_xml_path) if isinstance(stackup_xml_path, Path) else stackup_xml_path

            logger.info("=" * 70)
            logger.info("Loading Stackup from XML")
            logger.info("=" * 70)
            logger.info(f"XML Path: {xml_path_str}")

            success = edb.stackup.load(xml_path_str)

            if success:
                logger.info("[OK] Stackup loaded successfully")
            else:
                logger.warning("[WARNING] Stackup load returned False")

            logger.info("")

        except Exception as stackup_error:
            logger.warning(f"Failed to load stackup: {stackup_error}")
            import traceback
            traceback.print_exc()
            logger.info("")

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

        # 5. Additional cut operations (future implementation)
        logger.info("[5/4] Additional cut operations...")
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

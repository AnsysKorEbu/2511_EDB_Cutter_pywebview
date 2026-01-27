"""
Network and Port Handler Module

This module handles network analysis, endpoint finding, and port creation operations.
Provides functions for cutout operations, endpoint detection, and port generation.
"""

from util.logger_module import logger

from .edb_manager import (
    calculate_point_distance,
    find_cutout_edge_intersections,
    is_point_in_polygon,
)


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
        logger.info("EDB Cascade - Applying Cutout")
        logger.info("=" * 70)

        # Get polygon coordinates (custom extent)
        polygon_points = cut_data.get("points", [])
        if not polygon_points or len(polygon_points) < 3:
            logger.info("[WARNING] No valid polygon found. Skipping cutout.")
            logger.info("")
            return True

        logger.info(f"Polygon points: {len(polygon_points)}")
        for idx, pt in enumerate(polygon_points):
            logger.info(f"  Point {idx}: [{pt[0]:.6f}, {pt[1]:.6f}] meters")
        logger.info("")

        # Get selected nets
        selected_nets = cut_data.get("selected_nets", {})
        signal_nets = selected_nets.get("signal", [])
        power_nets = selected_nets.get("power", [])

        if not signal_nets and not power_nets:
            logger.info("[WARNING] No nets selected. Skipping cutout.")
            logger.info("")
            return True

        logger.info(
            f"Signal nets: {len(signal_nets)} ({', '.join(signal_nets) if signal_nets else 'none'})"
        )
        logger.info(
            f"Reference nets (power): {len(power_nets)} ({', '.join(power_nets) if power_nets else 'none'})"
        )
        logger.info("")

        # Execute cutout
        logger.info("Executing cutout operation...")
        logger.info("This will remove all traces outside the polygon boundary")
        logger.info("")

        try:
            netlist = edb.nets.netlist
            filtered_netlist = [
                n for n in netlist if not signal_nets or n not in signal_nets
            ]

            from ansys.edb.core.geometry.polygon_data import (
                PolygonData as GrpcPolygonData,
            )

            extent_poly = GrpcPolygonData(points=polygon_points)

            edb.cutout(
                signal_nets=filtered_netlist,
                reference_nets=signal_nets if signal_nets else [],
                custom_extent=polygon_points,
                keep_lines_as_path=True,
                custom_extent_units="meter",  # Coordinates are in meters
            )
            logger.info("[OK] Cutout operation completed successfully")

            # Initialize gap_port_info for storing edge intersection data
            cut_data["gap_port_info"] = []

            for prim in edb.modeler.primitives:
                if prim.net_name in signal_nets:
                    int_type = extent_poly.intersection_type(prim.polygon_data).value

                    if int_type in [3]:
                        clipped_polys = extent_poly.intersect(
                            [extent_poly], [prim.polygon_data]
                        )

                        for clipped_poly in clipped_polys:
                            if clipped_poly.points:
                                coords = [
                                    [pt.x.value, pt.y.value]
                                    for pt in clipped_poly.points
                                ]
                                logger.info(
                                    f"Clipped coordinates ({len(coords)} points):"
                                )
                                for pt in coords:
                                    logger.info(f"  {pt}")

                                # Find cutout edge intersections
                                logger.info("\n=== Cutout Edge Analysis ===")
                                edge_intersections = find_cutout_edge_intersections(
                                    coords, polygon_points, tolerance=1e-6
                                )

                                logger.info(
                                    f"Found edge intersections: {len(edge_intersections)}"
                                )
                                for idx, (edge, midpoint) in enumerate(
                                    edge_intersections, 1
                                ):
                                    logger.info(f"\n[{idx}] Edge:")
                                    logger.info(
                                        f"  Start: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] meters"
                                    )
                                    logger.info(
                                        f"  End:   [{edge[1][0]:.9f}, {edge[1][1]:.9f}] meters"
                                    )
                                    logger.info(
                                        f"  Center: [{midpoint[0]:.9f}, {midpoint[1]:.9f}] meters"
                                    )
                                logger.info("=" * 50)

                                # Store edge intersections info for gap port creation
                                if edge_intersections:
                                    gap_info = {
                                        "net_name": prim.net_name,
                                        "prim_id": prim.id,
                                        "edge_intersections": edge_intersections,
                                    }
                                    cut_data["gap_port_info"].append(gap_info)
                                    logger.debug(
                                        f"Stored gap port info for {prim.net_name}, primitive ID: {prim.id}"
                                    )

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
                if hasattr(obj, "net_name") and obj.net_name == net_name:
                    # Exclude self-reference
                    if hasattr(obj, "id") and obj.id != pad.id:
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
        min_distance = float("inf")

        for pad in padstacks:
            # Only consider component pins
            if pad.is_pin:
                # Skip UnnamedODBPadstack (invalid/unnamed pads from ODB)
                try:
                    if (
                        pad.padstack_def
                        and pad.padstack_def.name == "UnnamedODBPadstack"
                    ):
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
        return None, float("inf")


def _find_nearest_pad_from_cache(cached_pads, point):
    """
    Find the nearest pad from pre-cached pad list.

    Args:
        cached_pads: List of tuples (pad, position) - pre-filtered valid pads
        point: [x, y] coordinates to search around

    Returns:
        tuple: (PadstackInstance or None, distance in meters)
    """
    nearest_pad = None
    min_distance = float("inf")

    for pad, pos in cached_pads:
        dist = calculate_point_distance(point, pos)
        if dist < min_distance:
            min_distance = dist
            nearest_pad = pad

    return nearest_pad, min_distance


def _find_net_extreme_endpoints_from_cache(cached_paths, tolerance=1e-3):
    """
    Find the two farthest endpoints of a net using pre-cached paths.

    Args:
        cached_paths: List of center_line lists from cached paths
        tolerance: Distance threshold for merging close points

    Returns:
        dict or None: {
            'start': [x, y],
            'end': [x, y],
            'distance': float,
            'total_paths': int,
            'merged_endpoints': int
        }
    """
    if not cached_paths:
        return None

    # 1. Collect all endpoints
    endpoints = []
    for center_line in cached_paths:
        if len(center_line) >= 2:
            endpoints.append(center_line[0])  # start
            endpoints.append(center_line[-1])  # end

    if len(endpoints) < 2:
        return None

    # 2. Merge close points (within tolerance)
    merged = []
    used = [False] * len(endpoints)

    for i, pt in enumerate(endpoints):
        if used[i]:
            continue

        cluster = [pt]
        used[i] = True

        for j in range(i + 1, len(endpoints)):
            if not used[j]:
                if calculate_point_distance(pt, endpoints[j]) < tolerance:
                    cluster.append(endpoints[j])
                    used[j] = True

        avg_x = sum(p[0] for p in cluster) / len(cluster)
        avg_y = sum(p[1] for p in cluster) / len(cluster)
        merged.append([avg_x, avg_y])

    # 3. Find two farthest points
    max_dist = 0
    farthest_pair = None

    for i, pt1 in enumerate(merged):
        for pt2 in merged[i + 1 :]:
            dist = calculate_point_distance(pt1, pt2)
            if dist > max_dist:
                max_dist = dist
                farthest_pair = (pt1, pt2)

    if farthest_pair:
        return {
            "start": farthest_pair[0],
            "end": farthest_pair[1],
            "distance": max_dist,
            "total_paths": len(cached_paths),
            "merged_endpoints": len(merged),
        }

    return None


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
            endpoints.append(path.center_line[0])  # start
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

        for j in range(i + 1, len(endpoints)):
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
        for pt2 in merged[i + 1 :]:
            dist = calculate_point_distance(pt1, pt2)
            if dist > max_dist:
                max_dist = dist
                farthest_pair = (pt1, pt2)

    if farthest_pair:
        return {
            "start": farthest_pair[0],
            "end": farthest_pair[1],
            "distance": max_dist,
            "total_paths": len(paths),
            "merged_endpoints": len(merged),
        }

    return None


def find_endpoint_pads_for_selected_nets(edb, cut_data):
    """
    Find endpoint pads for user-selected signal nets.
    Uses network extreme endpoints to find the two farthest pads.

    Optimized with caching: pre-loads all paths and padstacks to minimize EDB queries.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing selected_nets and cut points

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info("EDB Cascade - Finding Endpoint Pads for Selected Nets")
        logger.info("=" * 70)

        # Get selected nets from cut_data
        selected_nets = cut_data.get("selected_nets", {})
        logger.debug(f"cut_data keys: {list(cut_data.keys())}")
        logger.debug(f"selected_nets from cut_data: {selected_nets}")
        # logger.debug(f"Type of selected_nets: {type(selected_nets)}")

        signal_nets = selected_nets.get("signal", [])
        logger.debug(f"signal_nets extracted: {signal_nets}")
        # logger.debug(f"Type of signal_nets: {type(signal_nets)}")
        logger.debug(f"Length of signal_nets: {len(signal_nets) if signal_nets else 0}")

        # Get cut polyline points
        cut_points = cut_data.get("points", [])
        if not cut_points or len(cut_points) < 2:
            logger.info(
                "[WARNING] No valid cut points found. Cannot determine farthest endpoints."
            )
            cut_data["endpoint_pads"] = {}
            return True

        if not signal_nets:
            logger.info("[WARNING] No signal nets selected.")
            cut_data["endpoint_pads"] = {}
            return True

        # ============================================================
        # CACHING PHASE: Pre-load all data from EDB in batch
        # ============================================================
        logger.info("")
        logger.info("Pre-loading data from EDB (caching)...")

        # Cache for paths: {net_name: [center_line, ...]}
        paths_cache = {}
        # Cache for pads: {net_name: [(pad, position), ...]}
        pads_cache = {}

        # Pre-load all paths and pads for signal nets
        for net_name in signal_nets:
            # Load paths
            paths = edb.modeler.get_primitives(net_name=net_name, prim_type="path")
            paths_cache[net_name] = [
                p.center_line for p in paths if len(p.center_line) >= 2
            ]

            # Load padstacks and filter valid pins
            padstacks = edb.padstacks.get_instances(net_name=net_name)
            valid_pads = []
            for pad in padstacks:
                if pad.is_pin:
                    try:
                        if (
                            pad.padstack_def
                            and pad.padstack_def.name == "UnnamedODBPadstack"
                        ):
                            continue
                    except (AttributeError, Exception):
                        pass
                    try:
                        pos = pad.position
                        valid_pads.append((pad, pos))
                    except (AttributeError, Exception):
                        continue
            pads_cache[net_name] = valid_pads

        logger.info(f"  Cached {len(paths_cache)} nets' paths and pads")
        logger.info("")

        # ============================================================
        # PROCESSING PHASE: Use cached data (no EDB queries)
        # ============================================================
        logger.info("=" * 70)
        logger.info("Finding Endpoint Pads Based on Net Extreme Points")
        logger.info("=" * 70)
        logger.info("")

        # Dictionary to store endpoint results: {net_name: [endpoint_pads]}
        endpoint_results = {}
        total_endpoints = 0

        for idx, net_name in enumerate(signal_nets, 1):
            logger.info(f"[{idx}/{len(signal_nets)}] Processing net: {net_name}")

            # Step 1: Find extreme endpoints using cached paths
            cached_paths = paths_cache.get(net_name, [])
            net_info = _find_net_extreme_endpoints_from_cache(
                cached_paths, tolerance=1e-3
            )

            if not net_info:
                logger.info("  [WARNING] Could not find endpoints for this net")
                logger.info("")
                continue

            logger.info(f"  Total paths: {net_info['total_paths']}")
            logger.info(
                f"  Unique endpoints after merging: {net_info['merged_endpoints']}"
            )
            logger.info(
                f"  Start point: [{net_info['start'][0]:.6f}, {net_info['start'][1]:.6f}] m"
            )
            logger.info(
                f"  End point:   [{net_info['end'][0]:.6f}, {net_info['end'][1]:.6f}] m"
            )
            logger.info(f"  Distance between extremes: {net_info['distance']:.6f} m")
            logger.info("")

            # Step 2: Find nearest pads using cached pads
            cached_pads = pads_cache.get(net_name, [])
            endpoint_pads = []

            # Find pad near start point
            start_pad, start_dist = _find_nearest_pad_from_cache(
                cached_pads, net_info["start"]
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
                logger.info("  [START] No pin found on this net")

            logger.info("")

            # Find pad near end point
            end_pad, end_dist = _find_nearest_pad_from_cache(
                cached_pads, net_info["end"]
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
                    logger.info("  [END] Same pad as start point - skipped")
            else:
                logger.info("  [END] No pin found on this net")

            logger.info("")

            # Store results
            if endpoint_pads:
                endpoint_results[net_name] = endpoint_pads
                total_endpoints += len(endpoint_pads)
                logger.info(
                    f"  [OK] Found {len(endpoint_pads)} endpoint pad(s) for this net"
                )
            else:
                logger.info("  [WARNING] No endpoint pads found for this net")

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
        cut_data["endpoint_pads"] = endpoint_results

        return True

    except Exception as e:
        logger.error(f"Failed to find endpoint pads: {e}")
        import traceback

        traceback.print_exc()
        cut_data["endpoint_pads"] = {}
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
        if pad.padstack_def and pad.padstack_def.name == "UnnamedODBPadstack":
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
        logger.info("EDB Cascade - Creating Circuit Ports for Endpoints")
        logger.info("=" * 70)

        # Get endpoint pads from cut_data
        endpoint_pads = cut_data.get("endpoint_pads", {})
        if not endpoint_pads:
            logger.info("[WARNING] No endpoint pads found. Skipping port creation.")
            logger.info("")
            return True

        # Validate endpoints before processing (filter out pads deleted by cutout)
        logger.info("Validating endpoint pads after cutout...")
        valid_endpoint_pads = {}
        stats = {"total_nets": 0, "nets_with_2": 0, "nets_with_1": 0, "nets_with_0": 0}

        for net_name, endpoints in endpoint_pads.items():
            stats["total_nets"] += 1

            # Filter valid endpoints (not deleted by cutout)
            valid_endpoints = [ep for ep in endpoints if is_valid_padstack(ep)]

            if len(valid_endpoints) == 2:
                stats["nets_with_2"] += 1
                valid_endpoint_pads[net_name] = valid_endpoints
            elif len(valid_endpoints) == 1:
                stats["nets_with_1"] += 1
                valid_endpoint_pads[net_name] = valid_endpoints
            else:
                stats["nets_with_0"] += 1
                logger.info(
                    f"  [SKIP] Net '{net_name}': No valid endpoints (both deleted by cutout)"
                )

        logger.info(f"  Nets with 2 valid endpoints: {stats['nets_with_2']}")
        logger.info(f"  Nets with 1 valid endpoint: {stats['nets_with_1']}")
        logger.info(f"  Nets with 0 valid endpoints (skipped): {stats['nets_with_0']}")
        logger.info("")

        # Use only validated endpoints
        endpoint_pads = valid_endpoint_pads

        if not endpoint_pads:
            logger.info(
                "[WARNING] No valid endpoint pads remaining after validation. Skipping port creation."
            )
            logger.info("")
            return True

        # Get selected power nets from cut_data
        selected_nets = cut_data.get("selected_nets", {})
        power_nets = selected_nets.get("power", [])

        if not power_nets:
            logger.info(
                "[WARNING] No power nets selected. Cannot create circuit ports without reference."
            )
            logger.info("")
            return True

        logger.info(f"Signal nets with endpoints: {len(endpoint_pads)}")
        logger.info(
            f"Power nets for reference: {len(power_nets)} ({', '.join(power_nets)})"
        )
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
        polygon_points = cut_data.get("points", [])
        if not polygon_points or len(polygon_points) < 3:
            logger.info(
                "[WARNING] No valid polygon found in cut_data. Creating ports for all endpoints."
            )
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
                component_name = (
                    signal_pin.component.name if signal_pin.component else "None"
                )

                logger.info(f"  [{idx}/{len(endpoints)}] Signal pin: {pin_name}")
                logger.info(
                    f"      Position: [{pin_position[0]:.6f}, {pin_position[1]:.6f}]"
                )
                logger.info(f"      Component: {component_name}")

                # Check if endpoint is inside polygon region
                if use_polygon_filter:
                    is_inside = is_point_in_polygon(pin_position, polygon_points)
                    if not is_inside:
                        logger.info(
                            "      [SKIP] Endpoint outside polygon region - no port created"
                        )
                        logger.info("")
                        continue
                    else:
                        logger.info("      [OK] Endpoint inside polygon region")

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
                        logger.info(
                            f"      Found {len(reference_pins)} power pins in same component"
                        )

                # Strategy 2: If no component power pins, find nearest power pins
                if not reference_pins:
                    logger.info(
                        "      No power pins in component, finding nearest pins..."
                    )

                    # Calculate distance to each power pin (skip invalid pins)
                    def calculate_distance(pin):
                        try:
                            pos = pin.position
                            dx = pos[0] - pin_position[0]
                            dy = pos[1] - pin_position[1]
                            return (dx * dx + dy * dy) ** 0.5
                        except (AttributeError, RuntimeError, Exception):
                            # Return infinite distance for invalid pins
                            return float("inf")

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
                        sorted_power_pins = sorted(
                            valid_power_pins, key=calculate_distance
                        )

                        # Use closest 3 power pins as reference
                        reference_pins = sorted_power_pins[:3]

                        if reference_pins:
                            nearest_distance = calculate_distance(reference_pins[0])
                            logger.info(
                                f"      Using {len(reference_pins)} nearest power pins (closest: {nearest_distance:.6f}m)"
                            )
                    else:
                        logger.info(
                            "      [WARNING] No valid power pins found (all deleted by cutout)"
                        )

                # Create circuit port
                if reference_pins:
                    try:
                        # Generate port name: Port_{net_name}_{pin_name_cleaned}
                        port_name = f"c_{net_name}"

                        port = signal_pin.create_port(
                            name=port_name,
                            reference=reference_pins,
                            is_circuit_port=True,
                        )
                        # Set positive terminal name explicitly
                        port.name = port_name

                        logger.info(f"      [OK] Created circuit port: {port_name}")
                        total_ports_created += 1

                    except Exception as port_error:
                        logger.info(
                            f"      [ERROR] Failed to create port: {port_error}"
                        )
                        failed_ports += 1
                else:
                    logger.info("      [ERROR] No reference pins found")
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


def create_gap_ports(edb, cut_data, previous_cut_points=None):
    """
    Create gap ports on cutout edges using stored edge intersection information.

    Args:
        edb: Opened pyedb.Edb object
        cut_data: Cut data dictionary containing gap_port_info and selected_nets
        previous_cut_points: List of polygon points from previous cut region for proximity-based sorting

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info("EDB Cascade - Creating Gap Ports")
        logger.info("=" * 70)

        # 1. Get gap port info from cut_data
        gap_port_info = cut_data.get("gap_port_info", [])
        if not gap_port_info:
            logger.info("[WARNING] No gap port info found. Skipping gap port creation.")
            logger.info("")
            return True

        # 2. Get reference layer from selected_nets
        selected_nets = cut_data.get("selected_nets", {})
        reference_layer = selected_nets.get("reference_layer")

        if not reference_layer:
            logger.info("[ERROR] No reference layer selected. Cannot create gap ports.")
            logger.info(
                "Please select a reference layer in the GUI (Nets tab -> Reference Layer for Gap Ports)"
            )
            logger.info("")
            return False

        logger.info(f"Reference layer: {reference_layer}")
        logger.info(f"Gap port candidates: {len(gap_port_info)} primitives")
        logger.info("")

        # 3. Create gap ports for each primitive's edge intersections
        total_ports_created = 0
        total_ports_failed = 0

        for gap_info in gap_port_info:
            net_name = gap_info["net_name"]
            prim_id = gap_info["prim_id"]
            edge_intersections = gap_info["edge_intersections"]

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

            # 5. Sort edge intersections by proximity to previous region (if available)
            if previous_cut_points and len(previous_cut_points) > 0:
                # Calculate reference point (centroid of previous region)
                ref_x = sum(pt[0] for pt in previous_cut_points) / len(
                    previous_cut_points
                )
                ref_y = sum(pt[1] for pt in previous_cut_points) / len(
                    previous_cut_points
                )
                reference_point = [ref_x, ref_y]

                logger.info(
                    f"  Sorting {len(edge_intersections)} edge intersections by proximity to previous region"
                )
                logger.info(
                    f"  Reference point (previous region centroid): [{ref_x:.9f}, {ref_y:.9f}]"
                )

                # Import distance calculation function
                from .edb_manager import calculate_point_distance

                # Sort by distance to reference point (ascending = closest first)
                edge_intersections = sorted(
                    edge_intersections,
                    key=lambda item: calculate_point_distance(item[1], reference_point),
                )

                logger.info("  [OK] Edge intersections sorted by proximity")
            else:
                logger.info("  No previous region - using default edge traversal order")

            logger.info("")

            # 6. Create gap port for each edge intersection
            for idx, (edge, midpoint) in enumerate(edge_intersections):
                try:
                    # Generate unique port name (0-based indexing: netname_0, netname_1, ...)
                    port_name = f"{idx}_{net_name}"

                    logger.info(
                        f"  [{idx + 1}/{len(edge_intersections)}] Creating gap port: {port_name}"
                    )
                    logger.info(
                        f"      Edge: [{edge[0][0]:.9f}, {edge[0][1]:.9f}] -> [{edge[1][0]:.9f}, {edge[1][1]:.9f}]"
                    )
                    logger.info(
                        f"      Terminal point (midpoint): [{midpoint[0]:.9f}, {midpoint[1]:.9f}]"
                    )
                    logger.info(f"      Reference layer: {reference_layer}")

                    # Create edge port on polygon
                    edb.source_excitation.create_edge_port_on_polygon(
                        polygon=prim,  # Re-fetched primitive
                        terminal_point=midpoint,  # Midpoint from edge_intersections
                        reference_layer=reference_layer,  # From GUI selection
                        port_name=port_name,  # Use net name-based port name
                    )

                    logger.info("      [OK] Gap port created successfully")
                    total_ports_created += 1

                except Exception as port_error:
                    logger.info(
                        f"      [ERROR] Failed to create gap port: {port_error}"
                    )
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

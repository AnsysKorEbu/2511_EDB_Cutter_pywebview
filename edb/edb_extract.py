import pyedb

def extract_component_positions(edb=None):
    component_positions = {}
    for comp_name, comp in edb.components.instances.items():
        position = comp.location  # [x, y] 좌표 (미터 단위)
        component_positions[comp_name] = position

    return component_positions

def extract_plane_positions(edb=None):
    planes_data = []
    for polygon in edb.modeler.polygons:
        # Filter by layer type: only "signal" or "dielectric"
        layer_type = polygon.layer.type if hasattr(polygon.layer, 'type') else None
        if layer_type not in ["signal", "dielectric"]:
            continue

        # polygon.points() returns tuple of two lists: ([x_coords], [y_coords])
        # Convert to [[x1,y1], [x2,y2], ...] format for JavaScript
        points_tuple = polygon.points()  # Call method, not property!
        if points_tuple and len(points_tuple) == 2:
            x_coords, y_coords = points_tuple
            points_list = [[x, y] for x, y in zip(x_coords, y_coords)]
        else:
            points_list = []

        # Extract voids (holes/cutouts) if they exist
        voids_list = []
        if polygon.has_voids:
            voids = polygon.voids
            if voids:
                for void in voids:
                    void_points_tuple = void.points()
                    if void_points_tuple and len(void_points_tuple) == 2:
                        vx_coords, vy_coords = void_points_tuple
                        void_points_list = [[vx, vy] for vx, vy in zip(vx_coords, vy_coords)]
                        voids_list.append(void_points_list)

        plane_info = {
            'name': polygon.aedt_name,
            'layer': polygon.layer_name,
            'net': polygon.net_name,
            'points': points_list,  # [[x, y], ...] format - outer boundary
            'voids': voids_list     # [[[x, y], ...], ...] format - list of holes
        }
        planes_data.append(plane_info)

    return planes_data

def extract_trace_positions(edb=None):
    traces_data = []
    for path in edb.modeler.paths:
        trace_info = {
            'name': path.aedt_name,
            'layer': path.layer_name,
            'net': path.net_name,
            'center_line': path.center_line,  # 중심선 좌표 리스트 [[x1,y1], [x2,y2], ...]
            'width': path.width,               # 트레이스 폭 (미터 단위)
        }
        traces_data.append(trace_info)

    return traces_data

def extract_via_positions(edb=None):
    """
    Extract via positions with optimized bulk processing.
    Pre-caches padstack definitions and minimizes property access per via.
    """
    # Step 1: Pre-cache padstack definitions to avoid repeated lookups
    print("Caching padstack definitions...")
    padstack_cache = {}
    for def_name, pdef in edb.padstacks.definitions.items():
        try:
            # Try to get hole diameter from padstack definition
            hole_diameter = None
            if hasattr(pdef, 'hole_properties'):
                try:
                    hole_diameter = pdef.hole_properties[0]
                except:
                    pass

            padstack_cache[def_name] = {
                'hole_diameter': hole_diameter
            }
        except:
            padstack_cache[def_name] = {'hole_diameter': None}

    # Step 2: Get all vias at once (PyEDB internally caches this)
    print("Fetching all vias...")
    all_vias = list(edb.padstacks.vias.values())
    print(f"Processing {len(all_vias)} vias...")

    # Step 3: Process vias with minimal property access
    vias_data = []
    for via in all_vias:
        # Get layer range once and extract start/stop from it
        layer_range = via.layer_range_names  # Single gRPC call
        start_layer = layer_range[0] if layer_range else None
        stop_layer = layer_range[-1] if layer_range else None

        # Get padstack definition name
        padstack_def_name = via.padstack_definition
        cached_def = padstack_cache.get(padstack_def_name, {})
        hole_diameter = cached_def.get('hole_diameter')

        # Calculate dimensions
        width = 0.0
        height = 0.0
        radius = 0.0
        is_circular = True  # Default to circular

        # Try to use cached hole diameter first (faster)
        if hole_diameter:
            radius = hole_diameter / 2
            width = hole_diameter
            height = hole_diameter
            is_circular = True
        else:
            # Fall back to bounding box (slower)
            bbox = via.bounding_box
            if bbox and len(bbox) >= 2:
                width = abs(bbox[1][0] - bbox[0][0])
                height = abs(bbox[1][1] - bbox[0][1])
                radius = max(width, height) / 2

                # Check if rectangular based on aspect ratio
                aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1.0
                is_circular = aspect_ratio < 1.5

        via_info = {
            'name': via.aedt_name,
            'position': via.position,  # [x, y] 좌표 (미터 단위) - cached internally
            'net': via.net_name,
            'start_layer': start_layer,
            'stop_layer': stop_layer,
            'layer_range_names': layer_range,  # Already fetched
            'radius': radius,  # via 반지름 (미터 단위) - circular일 때 사용
            'width': width,   # via 너비 (미터 단위)
            'height': height,  # via 높이 (미터 단위)
            'is_circular': is_circular,  # True: 원형, False: 직사각형
        }
        vias_data.append(via_info)

    print(f"Completed via extraction: {len(vias_data)} vias")
    return vias_data

def extract_net_names(edb=None):
    """
    Extract signal and power/ground net names from EDB.

    Args:
        edb: pyedb EDB object

    Returns:
        Dictionary with 'signal' and 'power' keys containing lists of net names
    """
    # Signal net names
    signal_nets = list(edb.nets.signal.keys())

    # Power/Ground net names
    power_nets = list(edb.nets.power.keys())

    nets_data = {
        'signal': signal_nets,
        'power': power_nets
    }

    return nets_data

if __name__ == "__main__":
    extract_component_positions()

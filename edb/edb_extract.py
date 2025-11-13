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
    vias_data = []
    for via in edb.padstacks.vias.values():
        # Get via padstack definition for accurate hole/pad size
        padstack_def = via.padstack_definition

        # Get bounding box for width/height calculation
        bbox = via.bounding_box  # [[x_min, y_min], [x_max, y_max]]

        # Calculate width and height from bounding box
        width = 0.0003  # Default 0.3mm width
        height = 0.0003  # Default 0.3mm height
        radius = 0.00015  # Default 0.15mm radius

        if bbox and len(bbox) >= 2:
            width = abs(bbox[1][0] - bbox[0][0])
            height = abs(bbox[1][1] - bbox[0][1])
            radius = max(width, height) / 2

        # Check if via is circular or rectangular based on aspect ratio
        # If width/height ratio > 1.5, it's rectangular
        aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1.0
        is_circular = aspect_ratio < 1.5

        # Try to get hole diameter from padstack definition for circular vias
        if is_circular and padstack_def and hasattr(padstack_def, 'hole_properties'):
            try:
                hole_diameter = padstack_def.hole_properties[0]  # Hole diameter in meters
                radius = hole_diameter / 2
                width = hole_diameter
                height = hole_diameter
            except:
                pass  # Use bounding box values

        via_info = {
            'name': via.aedt_name,
            'position': via.position,  # [x, y] 좌표 (미터 단위)
            'net': via.net_name,
            'start_layer': via.start_layer,
            'stop_layer': via.stop_layer,
            'layer_range_names': via.layer_range_names,  # start~stop 사이의 모든 레이어
            'radius': radius,  # via 반지름 (미터 단위) - circular일 때 사용
            'width': width,   # via 너비 (미터 단위)
            'height': height,  # via 높이 (미터 단위)
            'is_circular': is_circular,  # True: 원형, False: 직사각형
        }
        vias_data.append(via_info)
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

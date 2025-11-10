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

        # Try to get hole diameter from padstack definition
        radius = 0.00015  # Default 0.15mm radius
        if padstack_def and hasattr(padstack_def, 'hole_properties'):
            try:
                hole_diameter = padstack_def.hole_properties[0]  # Hole diameter in meters
                radius = hole_diameter / 2
            except:
                # Fallback to bounding box calculation
                bbox = via.bounding_box
                if bbox and len(bbox) >= 2:
                    radius = (bbox[1][0] - bbox[0][0]) / 2
        else:
            # Use bounding box as fallback
            bbox = via.bounding_box
            if bbox and len(bbox) >= 2:
                radius = (bbox[1][0] - bbox[0][0]) / 2

        via_info = {
            'name': via.aedt_name,
            'position': via.position,  # [x, y] 좌표 (미터 단위)
            'net': via.net_name,
            'start_layer': via.start_layer,
            'stop_layer': via.stop_layer,
            'layer_range_names': via.layer_range_names,  # start~stop 사이의 모든 레이어
            'radius': radius,  # via 반지름 (미터 단위)
        }
        vias_data.append(via_info)
    return vias_data

if __name__ == "__main__":
    extract_component_positions()

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
        # polygon.points() returns tuple of two lists: ([x_coords], [y_coords])
        # Convert to [[x1,y1], [x2,y2], ...] format for JavaScript
        points_tuple = polygon.points()  # Call method, not property!
        if points_tuple and len(points_tuple) == 2:
            x_coords, y_coords = points_tuple
            points_list = [[x, y] for x, y in zip(x_coords, y_coords)]
        else:
            points_list = []

        plane_info = {
            'name': polygon.aedt_name,
            'layer': polygon.layer_name,
            'net': polygon.net_name,
            'points': points_list,  # [[x, y], ...] format
            'center': polygon.center,  # [x, y]
            'bbox': polygon.bbox,  # [x_min, y_min, x_max, y_max]
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
if __name__ == "__main__":
    extract_component_positions()

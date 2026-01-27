"""
EDB Cascade Interface Module

This module provides a unified interface for EDB cutting operations.
It re-exports functions from edb_manager and net_port_handler for backward compatibility.
"""

# Import from edb_manager
from .edb_manager import (
    open_edb,
    clone_edbs_for_cuts,
    point_to_line_segment_distance,
    find_cutout_edge_intersections,
    is_point_in_polygon,
    calculate_point_distance,
    execute_cuts_on_clone
)

# Import from net_port_handler
from .net_port_handler import (
    apply_cutout,
    find_endpoint_pads,
    find_nearest_pad_to_point,
    find_net_extreme_endpoints,
    find_endpoint_pads_for_selected_nets,
    is_valid_padstack,
    remove_and_create_ports,
    create_gap_ports
)

# Re-export all functions for backward compatibility
__all__ = [
    # EDB Management
    'open_edb',
    'clone_edbs_for_cuts',
    'execute_cuts_on_clone',

    # Geometric Utilities
    'point_to_line_segment_distance',
    'find_cutout_edge_intersections',
    'is_point_in_polygon',
    'calculate_point_distance',

    # Network Analysis
    'find_endpoint_pads',
    'find_nearest_pad_to_point',
    'find_net_extreme_endpoints',
    'find_endpoint_pads_for_selected_nets',

    # Cutout Operations
    'apply_cutout',

    # Port Operations
    'is_valid_padstack',
    'remove_and_create_ports',
    'create_gap_ports',
]

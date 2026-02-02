"""
Standalone Stackup Data Extractor

A self-contained module for extracting stackup data from Excel files.
This module can be used independently without any external project dependencies.

Usage:
    from standalone import extract_stackup_data

    # Extract layer data
    layer_data = extract_stackup_data("path/to/excel_file.xlsx")

    # Get both layer and material info
    layer_data, material_info = extract_stackup_data("path/to/excel_file.xlsx",
                                                      include_material_info=True)
"""

from .excel_reader import read_material_properties, read_layer_material
from .config import StandaloneConfig

__version__ = "1.0.0"
__all__ = ['extract_stackup_data', 'StandaloneConfig', 'read_material_properties', 'read_layer_material']


def extract_stackup_data(excel_file, include_material_info=False):
    """
    Extract stackup data from Excel file.

    Args:
        excel_file (str): Path to Excel file containing stackup data
        include_material_info (bool): If True, also return material information

    Returns:
        list or tuple:
            - If include_material_info=False: List of material properties
            - If include_material_info=True: Tuple of (layer_data, material_info)

    Example:
        >>> layer_data = extract_stackup_data("rawdata.xlsx")
        >>> print(layer_data[0])
        {'layer': '4LAYER', 'row': 9, 'material': 'c_l_film',
         'CU_foil': None, 'Dk/Df': '3.17/0.023(10GHz)', 'height': 12.5}
    """
    layer_data = read_material_properties(excel_file)

    if include_material_info:
        material_info = read_layer_material(excel_file)
        return layer_data, material_info

    return layer_data

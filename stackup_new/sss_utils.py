"""
SSS File Utilities

Helper functions for SSS filename generation.
"""
from datetime import datetime


def generate_sss_filename(edb_folder_name):
    """
    Generate .sss filename with timestamp.

    Args:
        edb_folder_name (str): EDB folder name (e.g., "none_port_design.aedb")

    Returns:
        str: Filename in format "{edb_name}_sections_{timestamp}.sss"
    """
    # Remove .aedb extension if present
    base_name = edb_folder_name.replace('.aedb', '')

    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return f"{base_name}_sections_{timestamp}.sss"


def generate_layer_filename(edb_folder_name):
    """
    Generate layer .sss filename with timestamp.

    Args:
        edb_folder_name (str): EDB folder name

    Returns:
        str: Filename in format "{edb_name}_layers_{timestamp}.sss"
    """
    base_name = edb_folder_name.replace('.aedb', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return f"{base_name}_layers_{timestamp}.sss"

# __init__.py
"""
Stackup Module - PCB Stackup Data Processing

Public API for reading and processing PCB stackup data from Excel files.
This module can be imported and used in other projects.

Example:
    from stackup import StackupProcessor

    # Initialize with Excel file
    processor = StackupProcessor(excel_file="path/to/rawdata.xlsx")

    # Get layer data with materials and Dk/Df values
    layer_data = processor.get_layer_data()

    # Get net data from specific sheets
    net_data = processor.get_net_data(sheet_names=["L1_TOP", "L2"])

    # Get summary statistics
    summary = processor.get_stackup_summary()
"""

from stackup.core.stackup_processor import StackupProcessor
from stackup.core.config import StackupConfig
from stackup.section_selector import SectionSelector

__all__ = ['StackupProcessor', 'StackupConfig', 'SectionSelector']
__version__ = '1.0.0'

"""
Stackup New Module

Advanced stackup processing using FPCB-Extractor package.
"""
from .extractor_integration import (
    process_stackup_with_extractor,
    extract_sections_from_json,
    get_layer_data_for_section
)

__all__ = [
    'process_stackup_with_extractor',
    'extract_sections_from_json',
    'get_layer_data_for_section'
]

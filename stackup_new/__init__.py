"""
Stackup New Module

Advanced stackup processing using FPCB-Extractor package.
"""
from .extractor_integration import (
    process_stackup_with_extractor,
    extract_sections_from_json,
    get_layer_data_for_section,
    get_edb_conductor_layer_count,
    get_sss_copper_count_per_section,
    validate_layer_count_from_sss,
)
from .section_adapter import ExtractorSectionAdapter

__all__ = [
    'process_stackup_with_extractor',
    'extract_sections_from_json',
    'get_layer_data_for_section',
    'get_edb_conductor_layer_count',
    'get_sss_copper_count_per_section',
    'validate_layer_count_from_sss',
    'ExtractorSectionAdapter',
]

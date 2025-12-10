"""
Stackup Configuration Manager

Manages loading, saving, and validating stackup configuration files.
Configuration files store the mapping between cut IDs and stackup sections.

Configuration File Location: <edb_folder>/cut/stackup_config.sss
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from util.logger_module import logger


def get_config_path(edb_folder_path: str) -> Path:
    """
    Get path to stackup config file for an EDB folder.

    Args:
        edb_folder_path: Path to .aedb folder (e.g., "source/design.aedb")

    Returns:
        Path to config file: <edb_folder>/cut/stackup_config.sss

    Example:
        >>> path = get_config_path("source/none_port_design.aedb")
        >>> # C:/.../ source/none_port_design.aedb/cut/stackup_config.sss
    """
    edb_path = Path(edb_folder_path)
    config_path = edb_path / "cut" / "stackup_config.sss"
    return config_path


def load_stackup_config(edb_folder_path: str) -> Dict:
    """
    Load stackup configuration from file.

    Args:
        edb_folder_path: Path to .aedb folder (e.g., "source/design.aedb")

    Returns:
        Configuration dictionary:
        {
            'version': '1.0',
            'excel_file': 'C:/path/to/stackup.xlsx',
            'cut_stackup_mapping': {
                'cut_001': 'C/N 1',
                'cut_002': 'C/N 1-1',
                ...
            },
            'last_modified': '2025-12-08T15:30:00'
        }

        Returns empty dict {} if file doesn't exist or is corrupted.

    Example:
        >>> config = load_stackup_config("source/design.aedb")
        >>> if config:
        >>>     print(f"Excel file: {config['excel_file']}")
        >>>     print(f"Mappings: {len(config['cut_stackup_mapping'])}")
    """
    config_path = get_config_path(edb_folder_path)

    # Check if config file exists
    if not config_path.exists():
        logger.info(f"No stackup config found at: {config_path}")
        return {}

    try:
        # Read JSON file
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logger.info(f"Loaded stackup config from: {config_path}")
        logger.debug(f"Config: {config}")

        # Validate basic structure
        if not isinstance(config, dict):
            logger.warning("Config is not a dictionary, returning empty config")
            return {}

        # Ensure required fields exist
        if 'cut_stackup_mapping' not in config:
            logger.warning("Config missing 'cut_stackup_mapping', adding empty dict")
            config['cut_stackup_mapping'] = {}

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Corrupted config file (invalid JSON): {e}")
        logger.warning("Returning empty config")
        return {}

    except Exception as e:
        logger.error(f"Failed to load stackup config: {e}")
        import traceback
        traceback.print_exc()
        return {}


def save_stackup_config(edb_folder_path: str, config_data: Dict) -> Dict:
    """
    Save stackup configuration to file.

    Creates the config directory if it doesn't exist.
    Adds version and timestamp metadata automatically.

    Args:
        edb_folder_path: Path to .aedb folder
        config_data: Configuration dictionary with at minimum:
            {
                'excel_file': 'C:/path/to/file.xlsx',
                'cut_stackup_mapping': {
                    'cut_001': 'C/N 1',
                    ...
                }
            }

    Returns:
        Result dictionary:
        {
            'success': bool,
            'config_path': str,     # Path where config was saved
            'error': str            # Error message if failed (only if success=False)
        }

    Example:
        >>> config = {
        >>>     'excel_file': 'C:/stackup.xlsx',
        >>>     'cut_stackup_mapping': {'cut_001': 'C/N 1'}
        >>> }
        >>> result = save_stackup_config("source/design.aedb", config)
        >>> if result['success']:
        >>>     print(f"Saved to: {result['config_path']}")
    """
    try:
        config_path = get_config_path(edb_folder_path)

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        config_data['version'] = '1.0'
        config_data['last_modified'] = datetime.now().isoformat()

        # Validate before saving
        validation = validate_config(config_data, [])
        if not validation['valid']:
            error_msg = f"Invalid config: {validation['errors']}"
            logger.error(error_msg)
            return {
                'success': False,
                'config_path': str(config_path),
                'error': error_msg
            }

        # Write JSON file with pretty formatting
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved stackup config to: {config_path}")
        logger.info(f"Mappings saved: {len(config_data.get('cut_stackup_mapping', {}))}")

        return {
            'success': True,
            'config_path': str(config_path)
        }

    except Exception as e:
        error_msg = f"Failed to save stackup config: {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'config_path': str(get_config_path(edb_folder_path)),
            'error': error_msg
        }


def validate_config(config_data: Dict, available_cuts: List[str]) -> Dict:
    """
    Validate configuration data structure and content.

    Args:
        config_data: Config dict to validate
        available_cuts: List of available cut IDs (e.g., ["cut_001", "cut_002"])
                       Pass empty list [] to skip orphan checking

    Returns:
        Validation result:
        {
            'valid': bool,
            'errors': List[str],    # Critical errors (prevents saving)
            'warnings': List[str]   # Non-critical warnings (orphaned cuts, etc.)
        }

    Example:
        >>> config = {'excel_file': 'test.xlsx', 'cut_stackup_mapping': {'cut_001': 'C/N 1'}}
        >>> result = validate_config(config, ['cut_001', 'cut_002'])
        >>> if result['valid']:
        >>>     print("Config is valid")
        >>> for warning in result['warnings']:
        >>>     print(f"Warning: {warning}")
    """
    errors = []
    warnings = []

    # Check required fields
    if 'excel_file' not in config_data:
        errors.append("Missing required field: 'excel_file'")

    if 'cut_stackup_mapping' not in config_data:
        errors.append("Missing required field: 'cut_stackup_mapping'")

    # Validate excel_file is a string
    if 'excel_file' in config_data:
        if not isinstance(config_data['excel_file'], str):
            errors.append("Field 'excel_file' must be a string")
        elif not config_data['excel_file'].strip():
            errors.append("Field 'excel_file' cannot be empty")

    # Validate cut_stackup_mapping is a dict
    if 'cut_stackup_mapping' in config_data:
        mapping = config_data['cut_stackup_mapping']
        if not isinstance(mapping, dict):
            errors.append("Field 'cut_stackup_mapping' must be a dictionary")
        else:
            # Check for orphaned mappings (cuts that no longer exist)
            if available_cuts:  # Only check if available_cuts list is provided
                for cut_id in mapping.keys():
                    if cut_id not in available_cuts:
                        warnings.append(f"Orphaned mapping: '{cut_id}' (cut no longer exists)")

            # Validate all values are strings
            for cut_id, section_name in mapping.items():
                if not isinstance(section_name, str):
                    errors.append(f"Section name for '{cut_id}' must be a string, got {type(section_name)}")

    # Determine if config is valid (no critical errors)
    valid = len(errors) == 0

    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings
    }


def get_section_for_cut(config_data: Dict, cut_id: str) -> Optional[str]:
    """
    Get assigned section name for a cut ID.

    Args:
        config_data: Configuration dictionary
        cut_id: Cut ID (e.g., "cut_001")

    Returns:
        Section name (e.g., "C/N 1") or None if not assigned

    Example:
        >>> config = load_stackup_config("source/design.aedb")
        >>> section = get_section_for_cut(config, "cut_001")
        >>> if section:
        >>>     print(f"Cut cut_001 is assigned to section: {section}")
        >>> else:
        >>>     print("No section assigned to cut_001")
    """
    if not config_data:
        return None

    mapping = config_data.get('cut_stackup_mapping', {})
    return mapping.get(cut_id)


def get_all_cut_ids(edb_folder_path: str) -> List[str]:
    """
    Get list of all cut IDs from cut JSON files in EDB folder.

    Args:
        edb_folder_path: Path to .aedb folder

    Returns:
        List of cut IDs (e.g., ["cut_001", "cut_002", "cut_003"])

    Example:
        >>> cuts = get_all_cut_ids("source/design.aedb")
        >>> print(f"Found {len(cuts)} cuts: {cuts}")
    """
    cuts_dir = Path(edb_folder_path) / "cut"

    if not cuts_dir.exists():
        logger.warning(f"Cuts directory not found: {cuts_dir}")
        return []

    cut_ids = []

    # Scan for cut_*.json files
    for json_file in cuts_dir.glob("cut_*.json"):
        # Extract cut ID from filename (e.g., "cut_001" from "cut_001.json")
        cut_id = json_file.stem
        cut_ids.append(cut_id)

    cut_ids.sort()  # Sort for consistent ordering
    return cut_ids


if __name__ == "__main__":
    # Test the configuration manager
    import sys

    print("="*60)
    print("Stackup Configuration Manager - Test")
    print("="*60)

    # Test with example EDB folder
    if len(sys.argv) > 1:
        test_edb_folder = sys.argv[1]
    else:
        test_edb_folder = "source/none_port_design.aedb"

    print(f"\nTest EDB folder: {test_edb_folder}")

    # Test 1: Load config
    print("\n[Test 1] Loading config...")
    config = load_stackup_config(test_edb_folder)
    if config:
        print(f"  Excel file: {config.get('excel_file', 'N/A')}")
        print(f"  Mappings: {len(config.get('cut_stackup_mapping', {}))}")
    else:
        print("  No config found (empty)")

    # Test 2: Get available cuts
    print("\n[Test 2] Getting available cuts...")
    cuts = get_all_cut_ids(test_edb_folder)
    print(f"  Found {len(cuts)} cuts: {cuts}")

    # Test 3: Validate config
    print("\n[Test 3] Validating config...")
    if config:
        validation = validate_config(config, cuts)
        print(f"  Valid: {validation['valid']}")
        if validation['errors']:
            print(f"  Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"  Warnings: {validation['warnings']}")

    # Test 4: Get section for a cut
    print("\n[Test 4] Getting section for cut_001...")
    if config and cuts:
        section = get_section_for_cut(config, cuts[0] if cuts else "cut_001")
        print(f"  Section: {section or 'Not assigned'}")

    print("\n" + "="*60)

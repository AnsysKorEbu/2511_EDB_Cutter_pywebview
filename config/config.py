"""
Global configuration and constants for EDB Cutter application.

This module centralizes all magic numbers, file patterns, and configuration constants
used throughout the project to improve maintainability.
"""
from pathlib import Path

# ============================================================================
# TIMESTAMP & NAMING
# ============================================================================
TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
"""Standard timestamp format used across all modules"""

CUT_ID_FORMAT = 'cut_{:03d}'
"""Format string for cut IDs (e.g., 'cut_001')"""

BATCH_FILE_PREFIX = '_batch_'
"""Prefix for temporary batch JSON files"""

# ============================================================================
# DIRECTORY PATHS
# ============================================================================
SOURCE_DIR = Path('source')
"""Base directory for extracted EDB data"""

RESULTS_DIR = Path('Results')
"""Base directory for analysis results"""

LOGS_DIR = Path('logs')
"""Base directory for application logs"""

CONFIG_DIR = Path('config')
"""Base directory for configuration files"""

STACKUP_DIR = Path('stackup')
"""Base directory for stackup Excel files"""

# ============================================================================
# SUBDIRECTORY NAMES
# ============================================================================
CUT_SUBDIR = 'cut'
"""Subdirectory name for cut definition files"""

SSS_SUBDIR = 'sss'
"""Subdirectory name for section selection files"""

# ============================================================================
# FILE PATTERNS & EXTENSIONS
# ============================================================================
CUT_FILE_PATTERN = 'cut_*.json'
"""Glob pattern for cut definition files"""

BATCH_FILE_PATTERN = '_batch_*.json'
"""Glob pattern for temporary batch files"""

SSS_FILE_PATTERN = '*_sections_*.sss'
"""Glob pattern for section selection files"""

JSON_EXTENSION = '.json'
COMPRESSED_JSON_EXTENSION = '.json.gz'
SSS_EXTENSION = '.sss'
AEDB_EXTENSION = '.aedb'
EDB_DEF_FILE = 'edb.def'

# ============================================================================
# EDB SETTINGS
# ============================================================================
DEFAULT_EDB_VERSION = '2025.1'
"""Default AEDT/EDB version"""

MIN_EDB_VERSION = 25.1
"""Minimum supported EDB version"""

# ============================================================================
# GUI SETTINGS
# ============================================================================
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800
MAIN_WINDOW_TITLE = 'EDB Cutter - 2D Viewer'

ANALYSIS_WINDOW_WIDTH = 900
ANALYSIS_WINDOW_HEIGHT = 700
ANALYSIS_WINDOW_TITLE = 'EDB Analysis - Touchstone Generator'

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================
VALID_CUT_NAME_PATTERN = r'^[a-zA-Z0-9_]+$'
"""Regex pattern for valid cut names (alphanumeric + underscore)"""

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    'file_not_found': 'File not found: {path}',
    'invalid_cut_name': 'Invalid name format. Only letters, numbers, and underscores allowed.',
    'cut_exists': 'Cut name "{name}" already exists',
    'no_cuts_provided': 'No cut IDs provided',
    'cut_execution_failed': 'Cut execution failed with code {code}',
    'no_folder_selected': 'No folder selected',
}

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================
SUCCESS_MESSAGES = {
    'cut_saved': 'Cut data saved: {path}',
    'cut_deleted': 'Deleted cut: {path}',
    'cut_renamed': 'Renamed cut: {old_id} -> {new_id}',
    'cuts_executed': '{count} cut(s) executed successfully!',
}

# ============================================================================
# STACKUP SETTINGS
# ============================================================================
STACKUP_HEIGHT_COLUMN = 94
"""Default Excel column number for stackup height data"""

STACKUP_RAWDATA_FILE = 'rawdata.xlsx'
"""Default stackup Excel filename"""

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_FILE_FORMAT = '{timestamp}.log'
"""Format for log filenames"""

LOG_MAX_LINE_LENGTH = 2000
"""Maximum line length before truncation in logs"""

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================
def success_response(data=None, **kwargs):
    """
    Create standardized success response.

    Args:
        data: Optional data payload
        **kwargs: Additional fields to include

    Returns:
        dict: Success response dictionary
    """
    response = {'success': True}
    if data is not None:
        response['data'] = data
    response.update(kwargs)
    return response


def error_response(error, message=None):
    """
    Create standardized error response.

    Args:
        error: Error message or exception
        message: Optional user-friendly message

    Returns:
        dict: Error response dictionary
    """
    return {
        'success': False,
        'error': str(error),
        'message': message or str(error)
    }


# ============================================================================
# PATH HELPERS
# ============================================================================
def get_edb_data_dir(edb_folder_name):
    """
    Get data directory for specific EDB.

    Args:
        edb_folder_name: Name of EDB folder

    Returns:
        Path: Path to source/{edb_folder_name}/
    """
    return SOURCE_DIR / edb_folder_name


def get_cut_dir(edb_folder_name):
    """
    Get cut directory for specific EDB.

    Args:
        edb_folder_name: Name of EDB folder

    Returns:
        Path: Path to source/{edb_folder_name}/cut/
    """
    return get_edb_data_dir(edb_folder_name) / CUT_SUBDIR


def get_sss_dir(edb_folder_name):
    """
    Get SSS directory for specific EDB.

    Args:
        edb_folder_name: Name of EDB folder

    Returns:
        Path: Path to source/{edb_folder_name}/sss/
    """
    return get_edb_data_dir(edb_folder_name) / SSS_SUBDIR

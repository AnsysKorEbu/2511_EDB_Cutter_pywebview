"""
Configuration package for EDB Cutter application.

Re-exports all configuration constants and helper functions for easy import.
"""
from .config import (
    # Timestamp & Naming
    TIMESTAMP_FORMAT,
    CUT_ID_FORMAT,
    BATCH_FILE_PREFIX,

    # Directory Paths
    SOURCE_DIR,
    RESULTS_DIR,
    LOGS_DIR,
    CONFIG_DIR,

    # Subdirectory Names
    CUT_SUBDIR,
    SSS_SUBDIR,

    # File Patterns & Extensions
    CUT_FILE_PATTERN,
    BATCH_FILE_PATTERN,
    SSS_FILE_PATTERN,
    JSON_EXTENSION,
    COMPRESSED_JSON_EXTENSION,
    SSS_EXTENSION,
    AEDB_EXTENSION,
    EDB_DEF_FILE,

    # EDB Settings
    DEFAULT_EDB_VERSION,
    MIN_EDB_VERSION,

    # GUI Settings
    MAIN_WINDOW_WIDTH,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_TITLE,
    ANALYSIS_WINDOW_WIDTH,
    ANALYSIS_WINDOW_HEIGHT,
    ANALYSIS_WINDOW_TITLE,

    # Validation Patterns
    VALID_CUT_NAME_PATTERN,

    # Error & Success Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,

    # Stackup Settings
    STACKUP_HEIGHT_COLUMN,
    STACKUP_RAWDATA_FILE,

    # Logging Settings
    LOG_FILE_FORMAT,
    LOG_MAX_LINE_LENGTH,

    # Response Helpers
    success_response,
    error_response,

    # Path Helpers
    get_edb_data_dir,
    get_cut_dir,
    get_sss_dir,
)

__all__ = [
    # Timestamp & Naming
    'TIMESTAMP_FORMAT',
    'CUT_ID_FORMAT',
    'BATCH_FILE_PREFIX',

    # Directory Paths
    'SOURCE_DIR',
    'RESULTS_DIR',
    'LOGS_DIR',
    'CONFIG_DIR',

    # Subdirectory Names
    'CUT_SUBDIR',
    'SSS_SUBDIR',

    # File Patterns & Extensions
    'CUT_FILE_PATTERN',
    'BATCH_FILE_PATTERN',
    'SSS_FILE_PATTERN',
    'JSON_EXTENSION',
    'COMPRESSED_JSON_EXTENSION',
    'SSS_EXTENSION',
    'AEDB_EXTENSION',
    'EDB_DEF_FILE',

    # EDB Settings
    'DEFAULT_EDB_VERSION',
    'MIN_EDB_VERSION',

    # GUI Settings
    'MAIN_WINDOW_WIDTH',
    'MAIN_WINDOW_HEIGHT',
    'MAIN_WINDOW_TITLE',
    'ANALYSIS_WINDOW_WIDTH',
    'ANALYSIS_WINDOW_HEIGHT',
    'ANALYSIS_WINDOW_TITLE',

    # Validation Patterns
    'VALID_CUT_NAME_PATTERN',

    # Error & Success Messages
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',

    # Stackup Settings
    'STACKUP_HEIGHT_COLUMN',
    'STACKUP_RAWDATA_FILE',

    # Logging Settings
    'LOG_FILE_FORMAT',
    'LOG_MAX_LINE_LENGTH',

    # Response Helpers
    'success_response',
    'error_response',

    # Path Helpers
    'get_edb_data_dir',
    'get_cut_dir',
    'get_sss_dir',
]

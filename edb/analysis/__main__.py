"""
Entry point for running edb.analysis package as a module: python -m edb.analysis

This script is run as a subprocess to execute SIwave analysis operations.
It isolates pythonnet dependencies from the pywebview GUI.
"""
import sys
from pathlib import Path
from util.logger_module import logger
from . import run_siwave_analysis


if __name__ == "__main__":
    """
    Main entry point for subprocess.

    Expected command line arguments:
        sys.argv[1]: aedb_path (path to .aedb folder or edb.def file)
        sys.argv[2]: edb_version (e.g., "2025.1")
        sys.argv[3]: output_path (path for touchstone output file)
        sys.argv[4]: grpc (optional, "True" or "False", default: "False")
    """
    if len(sys.argv) < 4:
        logger.info("[ERROR] Insufficient arguments")
        logger.info("Usage: python -m edb.analysis <aedb_path> <edb_version> <output_path> [grpc]")
        sys.exit(1)

    aedb_path = sys.argv[1]
    edb_version = sys.argv[2]
    output_path = sys.argv[3]
    grpc = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False

    logger.info("=" * 70)
    logger.info("EDB Analysis Subprocess")
    logger.info("=" * 70)
    logger.info(f"AEDB Path: {aedb_path}")
    logger.info(f"EDB Version: {edb_version}")
    logger.info(f"Output Path: {output_path}")
    logger.info(f"gRPC Mode: {grpc}")
    logger.info("")

    try:
        # Run SIwave analysis
        result = run_siwave_analysis(aedb_path, edb_version, output_path, grpc)

        if result['success']:
            logger.info("=" * 70)
            logger.info("[SUCCESS] SIwave analysis completed successfully")
            logger.info(f"Output file: {result['output_file']}")
            logger.info(f"File size: {result.get('file_size', 0):,} bytes")
            logger.info("=" * 70)
            sys.exit(0)
        else:
            logger.info("=" * 70)
            logger.info("[ERROR] SIwave analysis failed")
            logger.info(f"Error: {result.get('error', 'Unknown error')}")
            logger.info("=" * 70)
            sys.exit(1)

    except Exception as e:
        logger.info("=" * 70)
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        logger.info("=" * 70)
        sys.exit(1)

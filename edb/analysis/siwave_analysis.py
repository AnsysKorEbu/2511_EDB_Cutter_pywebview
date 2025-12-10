"""
SIwave Analysis Module

This module provides SIwave analysis functionality for EDB files.
"""
import traceback
from pathlib import Path
from util.logger_module import logger


def run_siwave_analysis(aedb_path, edb_version, output_path, grpc=False):
    """
    Run SIwave analysis on a single .aedb file.

    This function opens an EDB file, configures SIwave for AC analysis,
    and exports Touchstone S-parameter files (.s2p, .s4p, etc.).

    Args:
        aedb_path: Path to .aedb folder or edb.def file
        edb_version: Version string (e.g., "2025.1")
        output_path: Path for touchstone output (.snp, auto-converts to .s2p, .s4p, etc.)
        grpc: Use gRPC mode for faster operations (default: False)

    Returns:
        dict: {
            'success': bool,
            'output_file': str (path to generated file),
            'error': str (error message if failed),
            'traceback': str (detailed traceback if failed)
        }
    """
    try:
        # Import pyedb
        try:
            import pyedb
        except ImportError as e:
            return {
                'success': False,
                'error': f'Failed to import pyedb: {str(e)}',
                'traceback': traceback.format_exc()
            }

        # Validate paths
        aedb_path = Path(aedb_path)
        output_path = Path(output_path)

        # Handle both .aedb folder and edb.def file paths
        if aedb_path.name == 'edb.def':
            edb_file = str(aedb_path)
        elif aedb_path.suffix == '.aedb':
            edb_file = str(aedb_path)
        else:
            return {
                'success': False,
                'error': f'Invalid EDB path: {aedb_path}'
            }

        # Ensure output directory exists
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Opening EDB: {edb_file}")
        logger.info(f"EDB Version: {edb_version}")
        logger.info(f"gRPC Mode: {grpc}")
        logger.info(f"Output Path: {output_path}")
        logger.info(f"Output Directory: {output_dir}")
        logger.info("")

        # Open EDB using pyedb (matches pattern from other edb files)
        edb = pyedb.Edb(
            edbpath=str(aedb_path),
            version=edb_version,
            grpc=grpc
        )

        logger.info("[OK] EDB opened successfully")

        # Add SYZ analysis
        logger.info("Adding SIwave SYZ analysis...")
        syz_setup = edb.siwave.add_siwave_syz_analysis(
            start_freq="1GHz",
            stop_freq="10GHz",
            distribution="linear"
        )
        logger.info("[OK] SYZ analysis added successfully")

        # Create execution file with SYZ options
        # Use output directory (Results/Analysis/{cut_name}) for touchstone export
        # SIwave will auto-generate the .snp file in this directory
        touchstone_export_path = str(output_dir)
        logger.info("Creating SIwave execution file with SYZ...")
        logger.info(f"Touchstone export path: {touchstone_export_path}")
        exec_file = edb.siwave.create_exec_file(
            add_syz=True,
            export_touchstone=True,
            touchstone_file_path=touchstone_export_path
        )

        logger.info(f"[OK] Execution file created: {exec_file}")

        # Run SIwave solver
        logger.info("Running SIwave solver...")
        try:
            from pyedb.generic.process import SiwaveSolve
            import os

            solver = SiwaveSolve(edb)
            result = solver.solve()
            # result = solver.solve_siwave(edb.edbpath, "SYZ")
            logger.info(f"[OK] SIwave solver execution completed: {result}")
        except UnicodeDecodeError as ue:
            logger.warning(f"[WARNING] Unicode decode error during solver execution: {ue}")
            logger.warning("This is often caused by Korean characters in output paths")
            logger.info("[OK] Continuing despite encoding warning...")
        except Exception as solve_error:
            logger.error(f"[ERROR] SIwave solver execution failed: {solve_error}")
            raise

        # Close EDB
        edb.close()
        logger.info("[OK] EDB closed")

        # Check if output file was created
        # SIwave auto-determines the extension based on port count (.s2p, .s4p, etc.)
        # So we need to check for any .s*p file in the output directory
        output_dir = output_path.parent
        output_name_stem = output_path.stem

        # Look for generated Touchstone files
        touchstone_files = list(output_dir.glob(f"{output_name_stem}.s*p"))

        if not touchstone_files:
            # Check if file exists with exact path (might have .snp extension)
            if output_path.exists():
                return {
                    'success': True,
                    'output_file': str(output_path),
                    'file_size': output_path.stat().st_size
                }
            else:
                return {
                    'success': False,
                    'error': f'Touchstone file not generated. Expected: {output_path} or {output_name_stem}.s*p'
                }

        # Return the first (should be only one) generated file
        generated_file = touchstone_files[0]
        file_size = generated_file.stat().st_size

        logger.info(f"[OK] Analysis complete!")
        logger.info(f"Generated file: {generated_file}")
        logger.info(f"File size: {file_size:,} bytes")
        logger.info("")

        return {
            'success': True,
            'output_file': str(generated_file),
            'file_size': file_size
        }

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"\n[ERROR] {error_msg}")
        logger.error(error_traceback)
        return {
            'success': False,
            'error': error_msg,
            'traceback': error_traceback
        }
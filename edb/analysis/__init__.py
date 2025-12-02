"""
EDB Analysis Module

This module provides SIwave analysis functionality for EDB files.
It runs in a subprocess to avoid pythonnet conflicts with pywebview.
"""
import sys
import traceback
from pathlib import Path


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
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Opening EDB: {edb_file}")
        print(f"EDB Version: {edb_version}")
        print(f"gRPC Mode: {grpc}")
        print(f"Output Path: {output_path}")
        print()

        # Open EDB using pyedb (matches pattern from other edb files)
        edb = pyedb.Edb(
            edbpath=str(aedb_path),
            version=edb_version,
            grpc=grpc
        )

        print("[OK] EDB opened successfully")

        # Configure SIwave for AC analysis and Touchstone export
        print("Configuring SIwave analysis...")
        result = edb.siwave.create_exec_file(
            add_ac=True,
            export_touchstone=True,
            touchstone_file_path=str(output_path)
        )

        print(f"[DEBUG] create_exec_file returned: {result}")

        siw_path = edb.solve_siwave()
        print(f"[DEBUG] run : {siw_path}")

        # Close EDB
        edb.close()
        print("[OK] EDB closed")

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

        print(f"[OK] Analysis complete!")
        print(f"Generated file: {generated_file}")
        print(f"File size: {file_size:,} bytes")
        print()

        return {
            'success': True,
            'output_file': str(generated_file),
            'file_size': file_size
        }

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        error_traceback = traceback.format_exc()
        print(f"\n[ERROR] {error_msg}")
        print(error_traceback)
        return {
            'success': False,
            'error': error_msg,
            'traceback': error_traceback
        }

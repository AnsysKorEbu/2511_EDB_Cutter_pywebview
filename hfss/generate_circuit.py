"""
HFSS Circuit Generator

Creates HFSS Circuit project from touchstone configuration.
"""
import json
from pathlib import Path
from datetime import datetime
from util.logger_module import logger


def generate_circuit(config_path, edb_version):
    """
    Generate HFSS Circuit project.

    Args:
        config_path: Path to full_touchstone_config.json
        edb_version: AEDT version (e.g., "2025.2")

    Returns:
        dict: {'success': bool, 'aedt_file': str, 'error': str}
    """
    try:
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Get analysis folder from config
        analysis_folder = Path(config['analysis_folder'])

        # Extract name from folder: Results/{name}_{timestamp1}_{timestamp2}/Analysis
        parent_folder = analysis_folder.parent
        folder_name = parent_folder.name
        name = folder_name.rsplit('_', 2)[0]  # Get name part

        # Generate filename: {name}_{MMDDhhmmss}.aedt
        timestamp = datetime.now().strftime("%m%d%H%M%S")
        aedt_filename = f"{name}_{timestamp}.aedt"
        aedt_path = analysis_folder / aedt_filename

        logger.info(f"\n[HFSS] Creating Circuit project")
        logger.info(f"  File: {aedt_path}")
        logger.info(f"  Version: {edb_version}")

        # Create Circuit
        from ansys.aedt.core import Circuit

        circuit = Circuit(
            project=str(aedt_path),
            version=edb_version
        )

        logger.info(f"[OK] Circuit created")

        # Save and release
        circuit.save_project()

        # Desktop release
        circuit.release_desktop(close_projects=False, close_desktop=False)

        logger.info(f"[SUCCESS] Circuit saved: {aedt_filename}\n")

        return {
            'success': True,
            'aedt_file': str(aedt_path)
        }

    except Exception as e:
        logger.error(f"[ERROR] Failed to create circuit: {e}")
        return {'success': False, 'error': str(e)}
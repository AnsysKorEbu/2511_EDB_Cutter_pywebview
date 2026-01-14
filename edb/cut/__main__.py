"""
Entry point for running edb.cut package as a module: python -m edb.cut

This script is run as a subprocess to execute EDB cutting operations.
It loads cut data and calls the edb_cut_interface module.
"""
import sys
import json
import shutil
from pathlib import Path
from .edb_cut_interface import clone_edbs_for_cuts, execute_cuts_on_clone
from util.logger_module import logger


def load_cut_data(cut_file_path):
    """
    Load cut data from JSON file.

    Args:
        cut_file_path: Path to cut JSON file

    Returns:
        dict: Cut data dictionary

    Raises:
        FileNotFoundError: If cut file doesn't exist
        json.JSONDecodeError: If JSON parsing fails
    """
    cut_path = Path(cut_file_path)

    if not cut_path.exists():
        raise FileNotFoundError(f"Cut file not found: {cut_file_path}")

    with open(cut_path, 'r', encoding='utf-8') as f:
        cut_data = json.load(f)

    return cut_data


if __name__ == "__main__":
    """
    Main entry point for subprocess.

    Expected command line arguments:
        sys.argv[1]: edb_path (path to .aedb folder or edb.def file)
        sys.argv[2]: edb_version (e.g., "2025.1")
        sys.argv[3]: cut_file_path (path to cut JSON file or batch JSON file)
        sys.argv[4]: grpc (optional, "True" or "False", default: "False")
    """
    if len(sys.argv) < 4:
        logger.info("[ERROR] Insufficient arguments")
        logger.info("Usage: python -m edb.cut <edb_path> <edb_version> <cut_file_path> [grpc]")
        sys.exit(1)

    edb_path = sys.argv[1]
    edb_version = sys.argv[2]
    input_file_path = sys.argv[3]
    grpc = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False

    # Use .aedb path directly (no need to append edb.def)
    original_edb_path = edb_path

    logger.info("=" * 70)
    logger.info("EDB Cutter Subprocess")
    logger.info("=" * 70)
    logger.info(f"EDB Path: {edb_path}")
    logger.info(f"EDB Version: {edb_version}")
    logger.info(f"Input File: {input_file_path}")
    logger.info(f"gRPC Mode: {grpc}")
    logger.info("")

    try:
        # Load input file to detect mode
        logger.info("Loading input file...")
        with open(input_file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        # Check if batch mode
        is_batch = input_data.get('mode') == 'batch'

        if is_batch:
            # Batch mode: multiple cuts
            cut_files = input_data.get('cut_files', [])
            if not cut_files:
                logger.info("[ERROR] No cut files in batch")
                sys.exit(1)

            # Get selected nets from batch data
            selected_nets = input_data.get('selected_nets', {'signal': [], 'power': []})

            # Get stackup usage flag (default: True for backward compatibility)
            use_stackup = input_data.get('use_stackup', True)

            logger.info(f"[BATCH MODE] Processing {len(cut_files)} cuts")
            logger.info(f"Stackup application: {'Enabled' if use_stackup else 'Disabled (user cleared SSS file)'}")
            logger.debug(f"Batch selected_nets from file: {selected_nets}")
            logger.debug(f"Signal nets count: {len(selected_nets.get('signal', []))}")
            logger.debug(f"Power nets count: {len(selected_nets.get('power', []))}")
            if selected_nets.get('signal'):
                logger.info(f"Selected signal nets: {', '.join(selected_nets['signal'])}")
            else:
                logger.info("No signal nets selected")
            logger.info("")

            # Determine cut type from first cut file
            first_cut_data = load_cut_data(cut_files[0])
            cut_type = first_cut_data.get('type', 'polyline')
            logger.info(f"Cut type detected: {cut_type}")

            # Clone EDB files before processing cuts
            # Polygon/Rectangle: n cuts = n clones (each cut defines a region)
            # Polyline: n cuts = (n+1) clones (cuts divide design into n+1 segments)
            if cut_type in ['polygon', 'rectangle']:
                num_clones = len(cut_files)
                logger.info(f"Creating {num_clones} EDB clones ({len(cut_files)} polygon regions)...")
            else:
                num_clones = len(cut_files) + 1
                logger.info(f"Creating {num_clones} EDB clones ({len(cut_files)} cuts + 1 segments)...")
            logger.info("")

            try:
                cloned_paths = clone_edbs_for_cuts(original_edb_path, num_clones, edb_version, grpc)
                logger.info(f"Successfully created {len(cloned_paths)} EDB clones")
                logger.info("")

                # Copy batch file to Results directory
                results_dir = Path(cloned_paths[0]).parent
                batch_filename = f"batch_{Path(input_file_path).name}"
                batch_dest = results_dir / batch_filename

                try:
                    shutil.copy2(input_file_path, batch_dest)
                    logger.info(f"Batch file copied to: {batch_dest}")
                    logger.info("")
                except Exception as copy_error:
                    logger.warning(f"Failed to copy batch file: {copy_error}")
                    logger.info("")

                # Generate stackup XMLs from sss files (one per cut)
                stackup_xml_paths = {}  # {cut_id: xml_path}

                # Only process stackup if use_stackup flag is True
                if use_stackup:
                    try:
                        # Extract EDB folder name from path
                        edb_path_obj = Path(edb_path)
                        if edb_path_obj.name == 'edb.def':
                            edb_folder_name = edb_path_obj.parent.name
                        elif edb_path_obj.suffix == '.aedb':
                            edb_folder_name = edb_path_obj.name
                        else:
                            edb_folder_name = edb_path_obj.name

                        # Find sss files in source/{edb_folder_name}/sss/
                        sss_dir = Path('source') / edb_folder_name / 'sss'

                        if sss_dir.exists():
                            # Find most recent *_sections_*.sss and *_layers_*.sss files
                            sections_files = list(sss_dir.glob('*_sections_*.sss'))
                            layers_files = list(sss_dir.glob('*_layers_*.sss'))

                            if sections_files and layers_files:
                                # Sort by modification time and get the latest
                                latest_sections_sss = max(sections_files, key=lambda p: p.stat().st_mtime)
                                latest_layers_sss = max(layers_files, key=lambda p: p.stat().st_mtime)

                                logger.info(f"Found section selection file: {latest_sections_sss}")
                                logger.info(f"Found layer data file: {latest_layers_sss}")

                                # Load sss data
                                with open(latest_sections_sss, 'r', encoding='utf-8') as f:
                                    sections_data = json.load(f)
                                with open(latest_layers_sss, 'r', encoding='utf-8') as f:
                                    layers_data = json.load(f)

                                excel_file_path = sections_data.get('excel_file')
                                cut_section_mapping = sections_data.get('cut_section_mapping', {})
                                cut_layer_data = layers_data.get('cut_layer_data', {})

                                if excel_file_path and Path(excel_file_path).exists() and cut_layer_data:
                                    logger.info(f"Excel file: {excel_file_path}")
                                    logger.info("Generating stackup XML files for each cut...")

                                    # Import generate_stackup module
                                    from stackup.generate_stackup import generate_xml_stackup_from_sss

                                    # Generate separate stackup XML for EACH cut
                                    for cut_id, section_name in cut_section_mapping.items():
                                        if cut_id in cut_layer_data:
                                            xml_filename = f"{Path(edb_folder_name).stem}_{cut_id}_stackup.xml"
                                            stackup_xml_path = results_dir / xml_filename

                                            # Generate XML for this specific cut
                                            generate_xml_stackup_from_sss(
                                                cut_layer_data[cut_id],  # Only layers for this cut
                                                str(stackup_xml_path),
                                                excel_file_path
                                            )

                                            stackup_xml_paths[cut_id] = str(stackup_xml_path)
                                            logger.info(f"  Stackup XML for {cut_id} ({section_name}): {stackup_xml_path.name}")

                                    logger.info(f"Generated {len(stackup_xml_paths)} stackup XML files")
                                    logger.info("")
                                else:
                                    if not excel_file_path or not Path(excel_file_path).exists():
                                        logger.info("Excel file not found in sss data, skipping stackup generation")
                                    if not cut_layer_data:
                                        logger.info("No cut layer data found in sss files, skipping stackup generation")
                                    logger.info("")
                            else:
                                logger.info("Missing sss files (sections or layers), skipping stackup generation")
                                logger.info("")
                        else:
                            logger.info(f"SSS directory not found: {sss_dir}")
                            logger.info("")

                    except Exception as stackup_error:
                        logger.warning(f"Failed to generate stackup XMLs: {stackup_error}")
                        import traceback
                        traceback.print_exc()
                        logger.info("")
                else:
                    logger.info("Stackup application disabled by user (SSS file selection cleared)")
                    logger.info("")

            except Exception as clone_error:
                logger.error(f"Failed to clone EDB files: {clone_error}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

            # Build clone-to-cut mapping
            logger.info("Building clone-to-cut mapping...")
            clone_cut_mapping = []

            if cut_type in ['polygon', 'rectangle']:
                # Polygon: 1:1 mapping (each clone gets one polygon region)
                for i in range(num_clones):
                    clone_cut_mapping.append([cut_files[i]])
                    logger.info(f"  Clone {i+1}: {Path(cut_files[i]).stem} (polygon region {i+1})")
            else:
                # Polyline: first and last clones get 1 cut, middle clones get 2 adjacent cuts
                for i in range(num_clones):
                    if i == 0:
                        # First clone: only first cut
                        clone_cut_mapping.append([cut_files[0]])
                        logger.info(f"  Clone {i+1}: {Path(cut_files[0]).stem}")
                    elif i == num_clones - 1:
                        # Last clone: only last cut
                        clone_cut_mapping.append([cut_files[-1]])
                        logger.info(f"  Clone {i+1}: {Path(cut_files[-1]).stem}")
                    else:
                        # Middle clones: adjacent cuts [i-1, i]
                        clone_cut_mapping.append([cut_files[i-1], cut_files[i]])
                        logger.info(f"  Clone {i+1}: {Path(cut_files[i-1]).stem}, {Path(cut_files[i]).stem}")
            logger.info("")

            all_success = True
            failed_cuts = []

            # Process each clone with its assigned cuts
            for i, (clone_path, assigned_cut_files) in enumerate(zip(cloned_paths, clone_cut_mapping), 1):
                logger.info("-" * 70)
                logger.info(f"Processing Clone {i}/{num_clones}: {Path(clone_path).name}")
                logger.info(f"Assigned cuts: {', '.join([Path(f).stem for f in assigned_cut_files])}")
                logger.info("-" * 70)

                # Get edb.def path for this clone
                clone_edb_path = str(Path(clone_path) / 'edb.def')

                try:
                    # Load all cut data for this clone
                    cut_data_list = []
                    for cut_file_path in assigned_cut_files:
                        cut_data = load_cut_data(cut_file_path)
                        # Add selected nets to cut data
                        cut_data['selected_nets'] = selected_nets
                        logger.debug(f"Added selected_nets to cut {cut_data.get('id', 'unknown')}: {cut_data['selected_nets']}")
                        cut_data_list.append(cut_data)

                    # Select appropriate stackup XML for this clone
                    # Use first cut's stackup (temporary solution until execute_cuts_on_clone supports per-cut stackup)
                    clone_stackup_path = None
                    if stackup_xml_paths and len(assigned_cut_files) > 0:
                        first_cut_id = Path(assigned_cut_files[0]).stem
                        clone_stackup_path = stackup_xml_paths.get(first_cut_id)

                        if len(assigned_cut_files) > 1:
                            logger.warning(f"Clone has {len(assigned_cut_files)} cuts, using {first_cut_id} stackup XML")
                            logger.warning("Future enhancement: Pass separate stackup XML for each cut")

                    # Execute all cuts on this clone (opens EDB once, processes all cuts, closes EDB)
                    success = execute_cuts_on_clone(clone_edb_path, edb_version, cut_data_list, grpc, clone_stackup_path)

                    if success:
                        logger.info(f"All cuts completed successfully on clone {i}")
                    else:
                        logger.error(f"Some cuts failed on clone {i}")
                        all_success = False
                        for cut_data in cut_data_list:
                            failed_cuts.append(f"{cut_data.get('id', 'unknown')} (clone {i})")

                except Exception as clone_error:
                    logger.error(f"Failed to process clone {i}: {clone_error}")
                    all_success = False
                    for cut_file_path in assigned_cut_files:
                        failed_cuts.append(f"{Path(cut_file_path).stem} (clone {i})")

                logger.info("")

            # Print final summary
            logger.info("=" * 70)
            if all_success:
                logger.info(f"[SUCCESS] All {len(cut_files)} cuts completed successfully")
            else:
                logger.info(f"[PARTIAL SUCCESS] {len(cut_files) - len(failed_cuts)}/{len(cut_files)} cuts completed")
                logger.info(f"Failed cuts: {', '.join(failed_cuts)}")
            logger.info("=" * 70)

            sys.exit(0 if all_success else 1)

        else:
            # Single mode: one cut (input_data is the cut data itself)
            cut_id = input_data.get('id', 'unknown')
            cut_type = input_data.get('type', 'polyline')
            logger.info(f"[SINGLE MODE] Processing cut: {cut_id}")
            logger.info(f"Cut type: {cut_type}")

            # Add empty selected_nets for single mode (no batch file)
            if 'selected_nets' not in input_data:
                input_data['selected_nets'] = {'signal': [], 'power': []}
            logger.info("")

            # Clone EDB files before processing cut
            # Polygon/Rectangle: 1 cut = 1 clone (defines a region)
            # Polyline: 1 cut = 2 clones (divides design into 2 segments)
            if cut_type in ['polygon', 'rectangle']:
                num_clones = 1
                logger.info(f"Creating {num_clones} EDB clone (1 polygon region)...")
            else:
                num_clones = 2
                logger.info(f"Creating {num_clones} EDB clones (1 cut → 2 segments)...")
            logger.info("")

            try:
                cloned_paths = clone_edbs_for_cuts(original_edb_path, num_clones, edb_version, grpc)
                logger.info(f"Successfully created {len(cloned_paths)} EDB clones")
                logger.info("")

                # Generate stackup XML from sss file if exists (for single cut)
                stackup_xml_path = None
                try:
                    # Extract EDB folder name from path
                    edb_path_obj = Path(edb_path)
                    if edb_path_obj.name == 'edb.def':
                        edb_folder_name = edb_path_obj.parent.name
                    elif edb_path_obj.suffix == '.aedb':
                        edb_folder_name = edb_path_obj.name
                    else:
                        edb_folder_name = edb_path_obj.name

                    # Get Results directory
                    results_dir = Path(cloned_paths[0]).parent

                    # Find sss files in source/{edb_folder_name}/sss/
                    sss_dir = Path('source') / edb_folder_name / 'sss'

                    if sss_dir.exists():
                        # Find most recent *_sections_*.sss and *_layers_*.sss files
                        sections_files = list(sss_dir.glob('*_sections_*.sss'))
                        layers_files = list(sss_dir.glob('*_layers_*.sss'))

                        if sections_files and layers_files:
                            # Sort by modification time and get the latest
                            latest_sections_sss = max(sections_files, key=lambda p: p.stat().st_mtime)
                            latest_layers_sss = max(layers_files, key=lambda p: p.stat().st_mtime)

                            logger.info(f"Found section selection file: {latest_sections_sss}")
                            logger.info(f"Found layer data file: {latest_layers_sss}")

                            # Load sss data
                            with open(latest_sections_sss, 'r', encoding='utf-8') as f:
                                sections_data = json.load(f)
                            with open(latest_layers_sss, 'r', encoding='utf-8') as f:
                                layers_data = json.load(f)

                            excel_file_path = sections_data.get('excel_file')
                            cut_section_mapping = sections_data.get('cut_section_mapping', {})
                            cut_layer_data = layers_data.get('cut_layer_data', {})

                            # For single mode, generate stackup for the current cut_id
                            if excel_file_path and Path(excel_file_path).exists() and cut_id in cut_layer_data:
                                logger.info(f"Excel file: {excel_file_path}")
                                section_name = cut_section_mapping.get(cut_id, 'unknown')
                                logger.info(f"Generating stackup XML for {cut_id} ({section_name})...")

                                # Import generate_stackup module
                                from stackup.generate_stackup import generate_xml_stackup_from_sss

                                # Generate XML for this specific cut
                                xml_filename = f"{Path(edb_folder_name).stem}_{cut_id}_stackup.xml"
                                stackup_xml_path = results_dir / xml_filename

                                generate_xml_stackup_from_sss(
                                    cut_layer_data[cut_id],  # Only layers for this cut
                                    str(stackup_xml_path),
                                    excel_file_path
                                )

                                logger.info(f"Stackup XML generated: {stackup_xml_path}")
                                logger.info("")
                            else:
                                if not excel_file_path or not Path(excel_file_path).exists():
                                    logger.info("Excel file not found in sss data, skipping stackup generation")
                                elif cut_id not in cut_layer_data:
                                    logger.info(f"Cut '{cut_id}' not found in layer data, skipping stackup generation")
                                logger.info("")
                        else:
                            logger.info("Missing sss files (sections or layers), skipping stackup generation")
                            logger.info("")
                    else:
                        logger.info(f"SSS directory not found: {sss_dir}")
                        logger.info("")

                except Exception as stackup_error:
                    logger.warning(f"Failed to generate stackup XML: {stackup_error}")
                    import traceback
                    traceback.print_exc()
                    logger.info("")

            except Exception as clone_error:
                logger.error(f"Failed to clone EDB files: {clone_error}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

            # Both clones get the same cut (1 cut divides into 2 segments)
            logger.info("Applying cut to both clones...")
            all_success = True

            for i, clone_path in enumerate(cloned_paths, 1):
                logger.info("-" * 70)
                logger.info(f"Processing Clone {i}/{num_clones}: {Path(clone_path).name}")
                logger.info(f"Assigned cut: {cut_id}")
                logger.info("-" * 70)

                # Get edb.def path for this clone
                clone_edb_path = str(Path(clone_path) / 'edb.def')

                try:
                    # Execute cutting operation on THIS CLONE (opens EDB once, processes cut, closes EDB)
                    success = execute_cuts_on_clone(clone_edb_path, edb_version, [input_data], grpc, stackup_xml_path)

                    if success:
                        logger.info(f"Cut {cut_id} completed successfully on clone {i}")
                    else:
                        logger.error(f"Cut {cut_id} failed on clone {i}")
                        all_success = False

                except Exception as clone_error:
                    logger.error(f"Failed to process clone {i}: {clone_error}")
                    all_success = False

                logger.info("")

            if all_success:
                logger.info("=" * 70)
                logger.info("[SUCCESS] EDB cutting operation completed on all clones")
                logger.info("=" * 70)
                sys.exit(0)
            else:
                logger.info("=" * 70)
                logger.info("[ERROR] EDB cutting operation failed on one or more clones")
                logger.info("=" * 70)
                sys.exit(1)

    except FileNotFoundError as e:
        logger.info(f"\n[ERROR] {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.info(f"\n[ERROR] Failed to parse input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
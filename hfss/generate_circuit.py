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
        # ============================================================
        # STEP 1: Parse config file and extract all information
        # ============================================================

        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Extract all config information
        version = config.get('version', '1.0')
        analysis_folder = Path(config['analysis_folder']).resolve()  # Convert to absolute path
        total_files = config.get('total_files', 0)
        merge_sequence = config.get('merge_sequence', [])

        # Ensure analysis folder exists
        analysis_folder.mkdir(parents=True, exist_ok=True)

        # Parse touchstone file information
        touchstone_files = []
        for item in merge_sequence:
            touchstone_files.append({
                'filename': item['filename'],
                'path': item['path'],
                'size': item['size'],
                'order': item['order'],
                'flip': item.get('flip', False),
                'enabled': item.get('enabled', True)
            })

        # Component spacing configuration
        dx = 0.00508  # Grid spacing (one unit)
        component_spacing = 10 * dx  # Spacing between components

        # Extract name from folder: Results/{name}_{timestamp1}_{timestamp2}/Analysis
        parent_folder = analysis_folder.parent
        folder_name = parent_folder.name
        name = folder_name.rsplit('_', 2)[0]  # Get name part

        # Generate filename: {name}_{MMDDhhmmss}.aedt
        timestamp = datetime.now().strftime("%m%d%H%M%S")
        aedt_filename = f"{name}_{timestamp}.aedt"
        aedt_path = analysis_folder / aedt_filename

        logger.info(f"\n[HFSS] Creating Circuit project")
        logger.info(f"  Config version: {version}")
        logger.info(f"  File: {aedt_path}")
        logger.info(f"  AEDT version: {edb_version}")
        logger.info(f"  Total touchstone files: {total_files}")
        logger.info(f"  Component spacing: {component_spacing} (10 * {dx})")

        # ============================================================
        # STEP 2: Create Circuit and add touchstone components
        # ============================================================

        # Create Circuit
        from ansys.aedt.core import Circuit

        circuit = Circuit(
            project=str(aedt_path),
            version=edb_version
        )

        logger.info(f"[OK] Circuit created")

        # Add touchstone files to circuit schematic
        components = []
        enabled_ts_files = [ts for ts in touchstone_files if ts['enabled']]

        for ts_file in enabled_ts_files:
            # Calculate position based on order
            x = component_spacing * (ts_file['order'] - 1)
            y = 0

            logger.info(f"  Adding: {ts_file['filename']} at position ({x}, {y})")
            logger.info(f"    Order: {ts_file['order']}, Flip: {ts_file['flip']}")

            # Create touchstone component
            component = circuit.modeler.schematic.create_touchstone_component(
                model_name=ts_file['path'],
                location=[x, y]
            )

            # Apply mirror if flip is needed
            if ts_file['flip']:
                component.mirror = True
                logger.info(f"    [OK] Mirror applied (ports flipped)")

            components.append(component)

        # Create interface ports for first component (start_ ports)
        if components:
            logger.info(f"\n[HFSS] Creating start_ interface ports for first component")
            first_comp = components[0]
            first_ts = enabled_ts_files[0]
            num_ports = len(first_comp.pins)
            half_ports = num_ports // 2

            logger.info(f"    First component flip: {first_ts['flip']}")

            # Create interface port considering flip status
            for j in range(half_ports):
                # If flipped, connect to second half; otherwise connect to first half
                if first_ts['flip']:
                    pin_idx = half_ports + j  # Second half (swapped to act as first half)
                else:
                    pin_idx = j  # First half

                pin = first_comp.pins[pin_idx]
                # Port name: start_{original_pin_name}
                port_name = f"start_{pin.name}"

                # Get pin location and place interface port next to it
                pin_location = pin.location
                port_x = pin_location[0] - 5*dx  # 5*dx left of the pin
                port_y = pin_location[1]

                logger.info(f"  Creating interface port '{port_name}' at ({port_x}, {port_y})")

                # Create interface port
                interface_port = circuit.modeler.schematic.create_interface_port(
                    name=port_name,
                    location=[port_x, port_y]
                )

                # Connect to first component
                interface_port.pins[0].connect_to_component(
                    first_comp.pins[pin_idx],
                    use_wire=True
                )

            logger.info(f"    [OK] Created {half_ports} start_ interface ports")

        # Connect components sequentially
        logger.info(f"\n[HFSS] Connecting components")
        for i in range(len(components) - 1):
            comp1 = components[i]
            comp2 = components[i + 1]
            ts1 = enabled_ts_files[i]
            ts2 = enabled_ts_files[i + 1]

            num_ports = len(comp1.pins)
            half_ports = num_ports // 2

            logger.info(f"  Connecting component {i+1} <-> {i+2}")
            logger.info(f"    Total ports: {num_ports}, Half: {half_ports}")
            logger.info(f"    Comp1 flip: {ts1['flip']}, Comp2 flip: {ts2['flip']}")

            # Connect ports considering flip status
            # If flipped, first half and second half are swapped
            for j in range(half_ports):
                # Comp1: use first half if flipped, second half if not
                if ts1['flip']:
                    port1_idx = j  # First half (swapped to act as second half)
                else:
                    port1_idx = half_ports + j  # Second half

                # Comp2: use second half if flipped, first half if not
                if ts2['flip']:
                    port2_idx = half_ports + j  # Second half (swapped to act as first half)
                else:
                    port2_idx = j  # First half

                comp1.pins[port1_idx].connect_to_component(
                    comp2.pins[port2_idx],
                    use_wire=True
                )

            logger.info(f"    [OK] Connected {half_ports} ports")

        # Create interface ports for last component (end_ ports)
        if components:
            logger.info(f"\n[HFSS] Creating end_ interface ports for last component")
            last_comp = components[-1]
            last_ts = enabled_ts_files[-1]
            num_ports = len(last_comp.pins)
            half_ports = num_ports // 2

            logger.info(f"    Last component flip: {last_ts['flip']}")

            # Create interface port considering flip status
            for j in range(half_ports):
                # If flipped, use first half; otherwise use second half
                if last_ts['flip']:
                    pin_idx = j  # First half (swapped to act as second half)
                else:
                    pin_idx = half_ports + j  # Second half

                pin = last_comp.pins[pin_idx]
                # Port name: end_{original_pin_name}
                port_name = f"end_{pin.name}"

                # Get pin location and place interface port next to it
                pin_location = pin.location
                port_x = pin_location[0] + 5*dx  # 5*dx right of the pin
                port_y = pin_location[1]

                logger.info(f"  Creating interface port '{port_name}' at ({port_x}, {port_y})")

                # Create interface port
                interface_port = circuit.modeler.schematic.create_interface_port(
                    name=port_name,
                    location=[port_x, port_y]
                )

                # Connect to last component
                interface_port.pins[0].connect_to_component(
                    last_comp.pins[pin_idx],
                    use_wire=True
                )

            logger.info(f"    [OK] Created {half_ports} end_ interface ports")

        # Save project before creating setup
        logger.info(f"\n[HFSS] Saving project before setup creation")
        circuit.save_project()
        logger.info(f"    [OK] Project saved")

        # ============================================================
        # STEP 3: Setup simulation and analysis
        # ============================================================

        logger.info(f"\n[HFSS] Setting up simulation")

        # 1. Create LinearFrequency setup
        logger.info(f"  Creating LinearFrequency setup")
        setup = circuit.create_setup("LinearFrequency")
        logger.info(f"    [OK] Setup created")

        # 2. Add sweep (0-5GHz, 201 points)
        logger.info(f"  Adding sweep (0-5GHz, 201 points)")
        setup.add_sweep_count(
            sweep_variable="Freq",
            start=0,
            stop=5,
            count=201,
            units="GHz",
            count_type="Linear"
        )
        logger.info(f"    [OK] Sweep added")

        # 3. Create S-parameter reports for each port pair (start_ to end_) by order
        excitation_names = circuit.excitation_names
        logger.info(f"  Found {len(excitation_names)} excitation ports")

        # Separate start_ and end_ ports
        start_ports = [p for p in excitation_names if p.startswith("start_")]
        end_ports = [p for p in excitation_names if p.startswith("end_")]

        logger.info(f"    start_ ports: {len(start_ports)}")
        logger.info(f"    end_ ports: {len(end_ports)}")

        expr_list = []
        # Match start_ and end_ ports by order (index)
        num_pairs = min(len(start_ports), len(end_ports))
        for i in range(num_pairs):
            start_port = start_ports[i]
            end_port = end_ports[i]

            # Create S-parameter expression: dB(S(end_xxx, start_xxx))
            expr = f"dB(S({end_port},{start_port}))"
            expr_list.append(expr)
            logger.info(f"    Adding report: {expr}")

        if expr_list:
            report = circuit.post.create_report(
                expressions=expr_list,
                plot_name="S_Parameter_Report"
            )

            logger.info(f"    [OK] Created report with {len(expr_list)} expressions")

        # 4. Run simulation
        logger.info(f"\n[HFSS] Running simulation")
        circuit.analyze()
        logger.info(f"    [OK] Simulation completed")

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
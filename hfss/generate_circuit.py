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
        analysis_folder = Path(config['analysis_folder'])
        total_files = config.get('total_files', 0)
        merge_sequence = config.get('merge_sequence', [])

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
        for ts_file in touchstone_files:
            if ts_file['enabled']:
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

                # Apply flip if needed
                if ts_file['flip']:
                    component.set_property("Flip", True)
                    logger.info(f"    [OK] Flip applied")

                components.append(component)

        # Create interface ports for first component
        if components:
            logger.info(f"\n[HFSS] Creating interface ports for first component")
            first_comp = components[0]
            num_ports = len(first_comp.pins)
            half_ports = num_ports // 2

            # Create interface port for first half of first component
            for j in range(half_ports):
                pin = first_comp.pins[j]
                port_name = pin.name

                # Get pin location and place interface port next to it
                pin_location = pin.location
                port_x = pin_location[0] - dx  # 1*dx left of the pin
                port_y = pin_location[1]

                logger.info(f"  Creating interface port '{port_name}' at ({port_x}, {port_y})")

                # Create interface port
                interface_port = circuit.modeler.schematic.create_interface_port(
                    name=port_name,
                    location=[port_x, port_y]
                )

                # Connect to first component
                interface_port.pins[0].connect_to_component(
                    first_comp.pins[j],
                    use_wire=True
                )

            logger.info(f"    [OK] Created {half_ports} interface ports")

        # Connect components sequentially
        logger.info(f"\n[HFSS] Connecting components")
        for i in range(len(components) - 1):
            comp1 = components[i]
            comp2 = components[i + 1]

            num_ports = len(comp1.pins)
            half_ports = num_ports // 2

            logger.info(f"  Connecting component {i+1} <-> {i+2}")
            logger.info(f"    Total ports: {num_ports}, Half: {half_ports}")

            # Connect second half of comp1 to first half of comp2
            for j in range(half_ports):
                port1_idx = half_ports + j  # Second half of comp1
                port2_idx = j  # First half of comp2

                comp1.pins[port1_idx].connect_to_component(
                    comp2.pins[port2_idx],
                    use_wire=True
                )

            logger.info(f"    [OK] Connected {half_ports} ports")

        # Connect last component to GND
        if components:
            logger.info(f"\n[HFSS] Connecting last component to GND")
            last_comp = components[-1]
            num_ports = len(last_comp.pins)
            half_ports = num_ports // 2

            # Calculate GND position: last component + 10*dx right, 5*dx down
            last_order = len([tf for tf in touchstone_files if tf['enabled']])
            gnd_x = component_spacing * (last_order - 1) + 10 * dx
            gnd_y = 0 - 5 * dx

            logger.info(f"  Creating GND at position ({gnd_x}, {gnd_y})")

            # Create single GND component
            gnd = circuit.modeler.schematic.create_gnd(location=[gnd_x, gnd_y])

            # Connect second half of last component to GND
            logger.info(f"  Connecting {half_ports} ports to GND")
            for j in range(half_ports):
                port_idx = half_ports + j  # Second half of last component
                last_comp.pins[port_idx].connect_to_component(
                    gnd.pins[0],
                    use_wire=True
                )

            logger.info(f"    [OK] Connected {half_ports} ports to GND")

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

        # 3. Create S-parameter reports for each port (self-reflection)
        excitation_names = circuit.excitation_names
        logger.info(f"  Found {len(excitation_names)} excitation ports")

        expressions = []
        for port_name in excitation_names:
            expr = f"dB(S({port_name},{port_name}))"
            expressions.append(expr)
            logger.info(f"    Adding report: {expr}")

        if expressions:
            report = circuit.post.create_report(
                expressions=expressions,
                setup_sweep_name="LinearFrequency"
            )
            logger.info(f"    [OK] Created report with {len(expressions)} expressions")

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
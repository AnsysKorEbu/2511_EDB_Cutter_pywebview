"""
Custom stackup loader module.
Loads stackup from XML file and creates layers using add_layer_bottom().
"""
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from util.logger_module import logger


def load_stackup(edb, xml_path: str) -> bool:
    """
    Load stackup from XML file and create layers from bottom to top using add_layer_bottom().

    Args:
        edb: EDB object with materials and stackup interfaces
        xml_path: Path to the stackup XML file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Note: Only root element uses namespace, child elements don't
        # Find Stackup element (no namespace)
        stackup_element = root.find('Stackup')
        if stackup_element is None:
            logger.error(f"No Stackup element found in {xml_path}")
            return False

        # 1. First, create all materials
        materials_element = stackup_element.find('Materials')
        if materials_element is not None:
            _create_materials(edb, materials_element)
        else:
            logger.warning(f"No Materials element found in {xml_path}")

        # 2. Then, create layers from bottom to top
        layers_element = stackup_element.find('Layers')
        if layers_element is not None:
            _create_layers_bottom_up(edb, layers_element)
        else:
            logger.warning(f"No Layers element found in {xml_path}")

        return True

    except Exception as e:
        logger.error(f"Error loading stackup from {xml_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def _create_materials(edb, materials_element):
    """
    Create materials from XML Materials section.
    Materials are created with 'EDB_' prefix to avoid conflicts with existing materials.

    Args:
        edb: EDB object with materials interface
        materials_element: XML element containing materials
    """
    for material_elem in materials_element.findall('Material'):
        material_name = material_elem.get('Name')
        # Add EDB_ prefix to avoid conflicts with existing materials like 'copper'
        edb_material_name = f"EDB_{material_name}"

        # Check if it's a conductor or dielectric
        conductivity_elem = material_elem.find('Conductivity/Double')
        permittivity_elem = material_elem.find('Permittivity/Double')
        permeability_elem = material_elem.find('Permeability/Double')
        loss_tangent_elem = material_elem.find('DielectricLossTangent/Double')

        if conductivity_elem is not None:
            # Conductor material
            conductivity = float(conductivity_elem.text)
            permeability = 1.0
            if permeability_elem is not None:
                permeability = float(permeability_elem.text)

            logger.info(f"Creating conductor material: {edb_material_name} (conductivity={conductivity})")
            edb.materials.add_conductor_material(
                name=edb_material_name,
                conductivity=conductivity
            )

        elif permittivity_elem is not None:
            # Dielectric material
            permittivity = float(permittivity_elem.text)
            loss_tangent = 0.0
            if loss_tangent_elem is not None:
                loss_tangent = float(loss_tangent_elem.text)

            logger.info(f"Creating dielectric material: {edb_material_name} (permittivity={permittivity}, loss_tangent={loss_tangent})")
            edb.materials.add_dielectric_material(
                name=edb_material_name,
                permittivity=permittivity,
                dielectric_loss_tangent=loss_tangent
            )


def _create_layers_bottom_up(edb, layers_element):
    """
    Create layers from bottom to top using add_layer_bottom().

    Args:
        edb: EDB object with stackup interface
        layers_element: XML element containing layers
    """
    # Get length unit
    length_unit = layers_element.get('LengthUnit', 'mm')

    # Get all layers and sort by elevation (bottom to top)
    layers = []
    for layer_elem in layers_element.findall('Layer'):
        layer_id = int(layer_elem.get('LayerID'))
        elevation = float(layer_elem.get('Elevation'))
        layers.append((elevation, layer_id, layer_elem))

    # Sort by elevation (descending = top to bottom)
    layers.sort(key=lambda x: x[0], reverse=True)

    logger.info(f"Creating {len(layers)} layers from top to bottom...")

    # Create layers from top to bottom
    for elevation, layer_id, layer_elem in layers:
        _create_single_layer(edb, layer_elem, length_unit)


def _create_single_layer(edb, layer_elem, length_unit: str):
    """
    Create a single layer using add_layer_bottom().
    Material names are prefixed with 'EDB_' to match the created materials.

    Args:
        edb: EDB object with stackup interface
        layer_elem: XML element for a single layer
        length_unit: Length unit (e.g., 'mm')
    """
    layer_name = layer_elem.get('Name')
    layer_type_si = layer_elem.get('TypeSI')  # 'dielectric' or 'conductor'
    thickness_value = float(layer_elem.get('Thickness'))
    thickness = f"{thickness_value}{length_unit}"
    material_name = layer_elem.get('Material')
    fill_material_name = layer_elem.get('FillMaterial', None)

    # Add EDB_ prefix to material names
    edb_material_name = f"EDB_{material_name}"
    edb_fill_material_name = f"EDB_{fill_material_name}" if fill_material_name else None

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer with add_layer_bottom
    if edb_fill_material_name and edb_fill_material_name != edb_material_name:
        # Layer with fill material (typically signal layers)
        logger.info(f"  Adding {layer_type} layer: {layer_name} (thickness={thickness}, material={edb_material_name}, fill={edb_fill_material_name})")
        edb.stackup.add_layer_bottom(
            layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name,
            fill_material=edb_fill_material_name
        )
    else:
        # Layer without separate fill material (typically dielectric layers)
        logger.info(f"  Adding {layer_type} layer: {layer_name} (thickness={thickness}, material={edb_material_name})")
        edb.stackup.add_layer_bottom(
            layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name
        )


def _create_single_layer_below(edb, layer_elem, length_unit: str, base_layer_name: str):
    """
    Create a single layer below a specified base layer using add_layer_below().

    Args:
        edb: EDB object with stackup interface
        layer_elem: XML element for a single layer
        length_unit: Length unit (e.g., 'mm')
        base_layer_name: Name of the layer to add below
    """
    layer_name = layer_elem.get('Name')
    layer_type_si = layer_elem.get('TypeSI')
    thickness_value = float(layer_elem.get('Thickness'))
    thickness = f"{thickness_value}{length_unit}"
    material_name = layer_elem.get('Material')
    fill_material_name = layer_elem.get('FillMaterial', None)

    # Add EDB_ prefix to material names
    edb_material_name = f"EDB_{material_name}"
    edb_fill_material_name = f"EDB_{fill_material_name}" if fill_material_name else None

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer below the base layer
    if edb_fill_material_name and edb_fill_material_name != edb_material_name:
        edb.stackup.add_layer_below(
            name=layer_name,
            base_layer_name=base_layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name,
            fill_material=edb_fill_material_name
        )
    else:
        edb.stackup.add_layer_below(
            name=layer_name,
            base_layer_name=base_layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name
        )


def _create_single_layer_above(edb, layer_elem, length_unit: str, base_layer_name: str):
    """
    Create a single layer above a specified base layer using add_layer_above().

    Args:
        edb: EDB object with stackup interface
        layer_elem: XML element for a single layer
        length_unit: Length unit (e.g., 'mm')
        base_layer_name: Name of the layer to add above
    """
    layer_name = layer_elem.get('Name')
    layer_type_si = layer_elem.get('TypeSI')
    thickness_value = float(layer_elem.get('Thickness'))
    thickness = f"{thickness_value}{length_unit}"
    material_name = layer_elem.get('Material')
    fill_material_name = layer_elem.get('FillMaterial', None)

    # Add EDB_ prefix to material names
    edb_material_name = f"EDB_{material_name}"
    edb_fill_material_name = f"EDB_{fill_material_name}" if fill_material_name else None

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer above the base layer
    if edb_fill_material_name and edb_fill_material_name != edb_material_name:
        edb.stackup.add_layer_above(
            name=layer_name,
            base_layer_name=base_layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name,
            fill_material=edb_fill_material_name
        )
    else:
        edb.stackup.add_layer_above(
            name=layer_name,
            base_layer_name=base_layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name
        )


def _create_single_layer_bottom(edb, layer_elem, length_unit: str):
    """
    Create a single layer at the bottom of stackup using add_layer_bottom().

    Args:
        edb: EDB object with stackup interface
        layer_elem: XML element for a single layer
        length_unit: Length unit (e.g., 'mm')
    """
    layer_name = layer_elem.get('Name')
    layer_type_si = layer_elem.get('TypeSI')
    thickness_value = float(layer_elem.get('Thickness'))
    thickness = f"{thickness_value}{length_unit}"
    material_name = layer_elem.get('Material')
    fill_material_name = layer_elem.get('FillMaterial', None)

    # Add EDB_ prefix to material names
    edb_material_name = f"EDB_{material_name}"
    edb_fill_material_name = f"EDB_{fill_material_name}" if fill_material_name else None

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer at the bottom
    if edb_fill_material_name and edb_fill_material_name != edb_material_name:
        edb.stackup.add_layer_bottom(
            name=layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name,
            fill_material=edb_fill_material_name
        )
    else:
        edb.stackup.add_layer_bottom(
            name=layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name
        )


def _create_single_layer_top(edb, layer_elem, length_unit: str):
    """
    Create a single layer at the top of stackup using add_layer_top().

    Args:
        edb: EDB object with stackup interface
        layer_elem: XML element for a single layer
        length_unit: Length unit (e.g., 'mm')
    """
    layer_name = layer_elem.get('Name')
    layer_type_si = layer_elem.get('TypeSI')
    thickness_value = float(layer_elem.get('Thickness'))
    thickness = f"{thickness_value}{length_unit}"
    material_name = layer_elem.get('Material')
    fill_material_name = layer_elem.get('FillMaterial', None)

    # Add EDB_ prefix to material names
    edb_material_name = f"EDB_{material_name}"
    edb_fill_material_name = f"EDB_{fill_material_name}" if fill_material_name else None

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer at the top
    if edb_fill_material_name and edb_fill_material_name != edb_material_name:
        edb.stackup.add_layer_top(
            name=layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name,
            fill_material=edb_fill_material_name
        )
    else:
        edb.stackup.add_layer_top(
            name=layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=edb_material_name
        )


def replace_stackup(edb, xml_path: str) -> bool:
    """
    Replace existing stackup layers with XML specifications.

    Strategy:
    1. Create materials from XML
    2. Parse all layers and sort by layer ID (0, 1, 2, ...)
    3. Remove all existing dielectric layers
    4. For layer 0: add_layer_top() or edit if signal
    5. For subsequent layers:
       - If signal layer exists: edit it
       - Otherwise: add_layer_below() the previous layer
    6. Verify final stackup order

    Args:
        edb: EDB object
        xml_path: Path to stackup XML file

    Returns:
        bool: True if successful
    """
    try:
        logger.info("=" * 70)
        logger.info("STACKUP REPLACEMENT STARTED")
        logger.info("=" * 70)

        # 1. Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        stackup_element = root.find('Stackup')

        if stackup_element is None:
            logger.error(f"No Stackup element found in {xml_path}")
            return False

        # 2. Create Materials
        logger.info("Step 1: Creating Materials")
        materials_element = stackup_element.find('Materials')
        if materials_element is not None:
            _create_materials(edb, materials_element)
        else:
            logger.warning("No Materials element found in XML")

        # 3. Parse and Sort Layers by LayerID
        logger.info("Step 2: Parsing XML Layer Specifications")
        layers_element = stackup_element.find('Layers')
        if layers_element is None:
            logger.error("No Layers element found in XML")
            return False

        length_unit = layers_element.get('LengthUnit', 'mm')

        # Collect all layers with their LayerID
        all_layers = []
        for layer_elem in layers_element.findall('Layer'):
            layer_id = int(layer_elem.get('LayerID'))
            layer_spec = {
                'layer_id': layer_id,
                'name': layer_elem.get('Name'),
                'type_si': layer_elem.get('TypeSI'),
                'thickness': float(layer_elem.get('Thickness')),
                'material': layer_elem.get('Material'),
                'fill_material': layer_elem.get('FillMaterial'),
                'elevation': float(layer_elem.get('Elevation')),
                'layer_elem': layer_elem
            }
            all_layers.append(layer_spec)

        # Sort by LayerID (0, 1, 2, ...)
        all_layers.sort(key=lambda x: x['layer_id'])

        logger.info(f"Parsed {len(all_layers)} layers from XML (sorted by LayerID)")
        for layer in all_layers:
            logger.info(f"  LayerID {layer['layer_id']}: {layer['name']} ({layer['type_si']})")

        # 4. Remove all existing dielectric layers
        logger.info("Step 3: Removing Existing Dielectric Layers")
        removed = _remove_all_dielectric_layers(edb)
        logger.info(f"Removed {removed} dielectric layers")

        # 5. Get existing signal layers
        logger.info("Step 4: Identifying Existing Signal Layers")
        existing_signals = []
        for layer_name, layer in edb.stackup.layers.items():
            if layer.type == 'signal':
                existing_signals.append({
                    'name': layer_name,
                    'layer_obj': layer
                })
        logger.info(f"Found {len(existing_signals)} existing signal layers")

        # 6. Process layers in order (0, 1, 2, ...)
        logger.info("Step 5: Building Stackup Layer by Layer")
        signal_index = 0  # Track which signal layer we're editing
        previous_layer_name = None

        for idx, layer_spec in enumerate(all_layers):
            layer_id = layer_spec['layer_id']
            is_signal = layer_spec['type_si'] == 'conductor'

            logger.info(f"Processing LayerID {layer_id}: {layer_spec['name']} ({'signal' if is_signal else 'dielectric'})")

            if idx == 0:
                # First layer: add to top
                logger.info(f"  [Layer 0] Adding to top")
                if is_signal and signal_index < len(existing_signals):
                    # Edit existing signal layer
                    _edit_signal_layer(edb, existing_signals[signal_index], layer_spec, length_unit)
                    previous_layer_name = layer_spec['name']
                    signal_index += 1
                else:
                    # Add new layer at top
                    _create_single_layer_top(edb, layer_spec['layer_elem'], length_unit)
                    previous_layer_name = layer_spec['name']

            else:
                # Subsequent layers: add below previous layer
                if is_signal and signal_index < len(existing_signals):
                    # Edit existing signal layer
                    logger.info(f"  [Signal Layer] Editing existing signal layer")
                    _edit_signal_layer(edb, existing_signals[signal_index], layer_spec, length_unit)
                    previous_layer_name = layer_spec['name']
                    signal_index += 1
                else:
                    # Add below previous layer
                    logger.info(f"  [Add Below] Adding below '{previous_layer_name}'")
                    _create_single_layer_below(edb, layer_spec['layer_elem'], length_unit, previous_layer_name)
                    previous_layer_name = layer_spec['name']

        # 7. Verify Final Stackup
        logger.info("Step 6: Verifying Final Stackup")
        _verify_stackup_order(edb)

        logger.info("=" * 70)
        logger.info("STACKUP REPLACEMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"Error replacing stackup from {xml_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def _edit_signal_layer(edb, existing_signal, layer_spec, length_unit):
    """
    Edit an existing signal layer with new specifications.

    Args:
        edb: EDB object
        existing_signal: Dict with 'name' and 'layer_obj' keys
        layer_spec: Layer specification dict from XML
        length_unit: Length unit (e.g., 'mm')
    """
    layer_obj = existing_signal['layer_obj']
    old_name = existing_signal['name']
    new_name = layer_spec['name']

    thickness = f"{layer_spec['thickness']}{length_unit}"
    material = f"EDB_{layer_spec['material']}"
    fill_material = f"EDB_{layer_spec['fill_material']}" if layer_spec.get('fill_material') else None

    logger.info(f"  Editing signal layer: {old_name} → {new_name}")
    logger.info(f"    Thickness: {thickness}")
    logger.info(f"    Material: {material}")
    if fill_material:
        logger.info(f"    Fill Material: {fill_material}")

    try:
        # Update layer name
        layer_obj.name = new_name

        # Update layer properties
        if fill_material:
            layer_obj.update(
                thickness=thickness,
                material=material,
                fill_material=fill_material
            )
        else:
            layer_obj.update(
                thickness=thickness,
                material=material
            )

        logger.info(f"    Updated successfully")

    except Exception as e:
        logger.error(f"    Failed to update: {e}")
        raise


def _remove_all_dielectric_layers(edb):
    """
    Remove all dielectric layers from existing stackup.
    Signal (conductor) layers are preserved.

    Args:
        edb: EDB object

    Returns:
        int: Count of removed layers
    """
    # Collect dielectric layer names (avoid modifying dict during iteration)
    dielectric_layers = []
    for layer_name, layer in edb.stackup.layers.items():
        if layer.type == 'dielectric':
            dielectric_layers.append(layer_name)

    logger.info(f"Found {len(dielectric_layers)} dielectric layers to remove")

    # Remove each dielectric
    removed_count = 0
    for layer_name in dielectric_layers:
        try:
            success = edb.stackup.remove_layer(layer_name)
            if success:
                logger.info(f"  Removed: {layer_name}")
                removed_count += 1
            else:
                logger.warning(f"  Failed to remove: {layer_name}")
        except Exception as e:
            logger.error(f"  Error removing {layer_name}: {e}")

    return removed_count


def _update_signal_layers_by_index(edb, xml_signal_layers, length_unit):
    """
    Update existing signal layers in place, matched by order index.

    Args:
        edb: EDB object
        xml_signal_layers: List of signal layer specs from XML, ordered by elevation
        length_unit: Unit string (e.g., 'mm')

    Returns:
        int: Count of updated signal layers
    """
    # Extract existing signal layers (preserve iteration order)
    existing_signals = []
    for layer_name, layer in edb.stackup.layers.items():
        if layer.type == 'signal':
            existing_signals.append({
                'name': layer_name,
                'layer_obj': layer
            })

    logger.info(f"Found {len(existing_signals)} existing signal layers")

    # Match by index: 1st existing → 1st XML, 2nd → 2nd, etc.
    updated_count = 0
    for idx, xml_spec in enumerate(xml_signal_layers):
        if idx >= len(existing_signals):
            logger.warning(f"Skipping XML signal layer {idx+1} ('{xml_spec['name']}'): "
                          f"exceeds existing signal layer count ({len(existing_signals)})")
            break

        layer_obj = existing_signals[idx]['layer_obj']
        old_name = existing_signals[idx]['name']
        new_name = xml_spec['name']

        thickness = f"{xml_spec['thickness']}{length_unit}"
        material = f"EDB_{xml_spec['material']}"
        fill_material = f"EDB_{xml_spec['fill_material']}" if xml_spec.get('fill_material') else None

        logger.info(f"  [{idx+1}] Updating: {old_name} → {new_name}")
        logger.info(f"      Thickness: {thickness}")
        logger.info(f"      Material: {material}")
        if fill_material:
            logger.info(f"      Fill Material: {fill_material}")

        try:
            # Update layer name
            layer_obj.name = new_name

            # Update layer properties
            if fill_material:
                layer_obj.update(
                    thickness=thickness,
                    material=material,
                    fill_material=fill_material
                )
            else:
                layer_obj.update(
                    thickness=thickness,
                    material=material
                )

            logger.info(f"      Updated successfully")
            updated_count += 1

        except Exception as e:
            logger.error(f"      Failed to update: {e}")

    return updated_count


def _add_dielectric_layers_with_positioning(edb, xml_signal_layers, xml_dielectric_layers, length_unit):
    """
    Add dielectric layers in proper order by positioning them relative to signal layers.

    Strategy: Process layers from TOP to BOTTOM. For each dielectric:
    - Find the signal layer immediately ABOVE it (higher elevation)
    - Use add_layer_below() to position it below that signal
    - If no signal above, use add_layer_top()

    Args:
        edb: EDB object
        xml_signal_layers: List of signal layer specs from XML (for reference)
        xml_dielectric_layers: List of dielectric layer specs from XML (sorted top-to-bottom)
        length_unit: Unit string (e.g., 'mm')

    Returns:
        int: Count of added layers
    """
    logger.info(f"Adding {len(xml_dielectric_layers)} dielectric layers with positioning...")

    # Get current signal layer names (already updated)
    current_signal_names = []
    for layer_name, layer in edb.stackup.layers.items():
        if layer.type == 'signal':
            current_signal_names.append(layer_name)

    # Create mapping of elevation to signal layer name
    signal_elevation_map = {}
    for idx, xml_signal in enumerate(xml_signal_layers):
        if idx < len(current_signal_names):
            # Map XML signal elevation to current signal name
            signal_elevation_map[xml_signal['elevation']] = current_signal_names[idx]

    logger.info(f"Signal elevation map: {signal_elevation_map}")

    # Process dielectric layers in TOP to BOTTOM order (descending elevation)
    # Already sorted in descending order from main function
    added_count = 0
    for dielectric_spec in xml_dielectric_layers:
        dielectric_elevation = dielectric_spec['elevation']
        dielectric_name = dielectric_spec['name']

        # Find the signal layer immediately ABOVE this dielectric (higher elevation, closest)
        signal_above = None
        min_distance = float('inf')

        for sig_elevation, sig_name in signal_elevation_map.items():
            if sig_elevation > dielectric_elevation:
                distance = sig_elevation - dielectric_elevation
                if distance < min_distance:
                    min_distance = distance
                    signal_above = sig_name

        try:
            if signal_above:
                # Add dielectric BELOW the signal layer above it
                logger.info(f"  Adding '{dielectric_name}' below signal '{signal_above}'")
                _create_single_layer_below(edb, dielectric_spec['layer_elem'], length_unit, signal_above)
            else:
                # No signal above, add at the top
                logger.info(f"  Adding '{dielectric_name}' at top (no signal above)")
                _create_single_layer_top(edb, dielectric_spec['layer_elem'], length_unit)

            added_count += 1
        except Exception as e:
            logger.error(f"  Failed to add dielectric layer '{dielectric_name}': {e}")

    return added_count


def _verify_stackup_order(edb):
    """
    Verify and log final stackup layer order.

    Args:
        edb: EDB object
    """
    logger.info("Final Stackup:")
    layer_count = 0
    for layer_name, layer in edb.stackup.layers.items():
        layer_count += 1
        logger.info(f"  {layer_count}. {layer_name} ({layer.type})")

    logger.info(f"Total layers: {layer_count}")

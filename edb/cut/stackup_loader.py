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

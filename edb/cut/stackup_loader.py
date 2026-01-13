"""
Custom stackup loader module.
Loads stackup from XML file and creates layers using add_layer_bottom().
"""
import xml.etree.ElementTree as ET
from typing import Dict, Optional


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

        # Namespace handling
        ns = {'c': 'http://www.ansys.com/control'}

        # 1. First, create all materials
        materials_element = root.find('.//c:Materials', ns)
        if materials_element is not None:
            _create_materials(edb, materials_element, ns)

        # 2. Then, create layers from bottom to top
        layers_element = root.find('.//c:Layers', ns)
        if layers_element is not None:
            _create_layers_bottom_up(edb, layers_element, ns)

        return True

    except Exception as e:
        print(f"Error loading stackup from {xml_path}: {str(e)}")
        return False


def _create_materials(edb, materials_element, ns: dict):
    """
    Create materials from XML Materials section.

    Args:
        edb: EDB object with materials interface
        materials_element: XML element containing materials
        ns: XML namespace dictionary
    """
    for material_elem in materials_element.findall('c:Material', ns):
        material_name = material_elem.get('Name')

        # Check if it's a conductor or dielectric
        conductivity_elem = material_elem.find('c:Conductivity/c:Double', ns)
        permittivity_elem = material_elem.find('c:Permittivity/c:Double', ns)
        permeability_elem = material_elem.find('c:Permeability/c:Double', ns)
        loss_tangent_elem = material_elem.find('c:DielectricLossTangent/c:Double', ns)

        if conductivity_elem is not None:
            # Conductor material
            conductivity = float(conductivity_elem.text)
            permeability = 1.0
            if permeability_elem is not None:
                permeability = float(permeability_elem.text)

            edb.materials.add_conductor_material(
                name=material_name,
                conductivity=conductivity
            )

        elif permittivity_elem is not None:
            # Dielectric material
            permittivity = float(permittivity_elem.text)
            loss_tangent = 0.0
            if loss_tangent_elem is not None:
                loss_tangent = float(loss_tangent_elem.text)

            edb.materials.add_dielectric_material(
                name=material_name,
                permittivity=permittivity,
                dielectric_loss_tangent=loss_tangent
            )


def _create_layers_bottom_up(edb, layers_element, ns: dict):
    """
    Create layers from bottom to top using add_layer_bottom().

    Args:
        edb: EDB object with stackup interface
        layers_element: XML element containing layers
        ns: XML namespace dictionary
    """
    # Get length unit
    length_unit = layers_element.get('LengthUnit', 'mm')

    # Get all layers and sort by elevation (bottom to top)
    layers = []
    for layer_elem in layers_element.findall('c:Layer', ns):
        layer_id = int(layer_elem.get('LayerID'))
        elevation = float(layer_elem.get('Elevation'))
        layers.append((elevation, layer_id, layer_elem))

    # Sort by elevation (ascending = bottom to top)
    layers.sort(key=lambda x: x[0])

    # Create layers from bottom to top
    for elevation, layer_id, layer_elem in layers:
        _create_single_layer(edb, layer_elem, length_unit)


def _create_single_layer(edb, layer_elem, length_unit: str):
    """
    Create a single layer using add_layer_bottom().

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

    # Map TypeSI to layer_type
    if layer_type_si == 'conductor':
        layer_type = 'signal'
    else:
        layer_type = 'dielectric'

    # Create layer with add_layer_bottom
    if fill_material_name and fill_material_name != material_name:
        # Layer with fill material (typically signal layers)
        edb.stackup.add_layer_bottom(
            layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=material_name,
            fill_material=fill_material_name
        )
    else:
        # Layer without separate fill material (typically dielectric layers)
        edb.stackup.add_layer_bottom(
            layer_name,
            layer_type=layer_type,
            thickness=thickness,
            material=material_name
        )

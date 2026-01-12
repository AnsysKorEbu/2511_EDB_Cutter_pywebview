# generate_stackup.py
"""
Generate stackup information and export to XML format.
This module provides functionality to process Excel stackup files and generate ANSYS-compatible XML stackup files.
"""
from stackup.readers.excel_reader import (
    read_layer_material,
    read_material_properties,
    extract_materials_specifications,
    postprocess_materials_dict
)
from stackup.core.preprocessing import find_center_layer, swap_all_air_adhesive_pairs
from util.logger_module import logger
from openpyxl import load_workbook
import re
from collections import OrderedDict

# Pattern constants from excel_reader
DK_DF_PATTERN = r'\(([\d\s\.]*\s*/\s*[\d\s\.]*)\)\s*10GHz?'


def parse_dk_df(dk_df_str):
    """
    Parse Dk/Df string to extract permittivity and loss tangent values.
    Uses the same pattern as excel_reader for consistency.

    Args:
        dk_df_str (str): String like "3.2/0.008(10GHz)" or "(3.17 / 0.023) 10GHz"

    Returns:
        tuple: (permittivity, loss_tangent) or (None, None) if parsing fails
    """
    if not dk_df_str or dk_df_str == '-':
        return None, None

    # Try to match with parentheses pattern first (from excel_reader)
    match = re.search(DK_DF_PATTERN, str(dk_df_str), re.IGNORECASE)
    if match:
        dk_df_part = match.group(1).strip()
        # Check if it's empty like "  /  "
        if dk_df_part.replace('/', '').strip() == '':
            return None, None
        # Remove extra spaces
        dk_df_part = dk_df_part.replace(' ', '')
    else:
        # Fallback: try simple pattern without parentheses
        pattern = r'([\d\.]+)\s*/\s*([\d\.]+)'
        match = re.search(pattern, str(dk_df_str))
        if match:
            dk_df_part = match.group(0).replace(' ', '')
        else:
            return None, None

    # Parse the dk/df values
    parts = dk_df_part.split('/')
    if len(parts) == 2:
        try:
            permittivity = float(parts[0])
            loss_tangent = float(parts[1])
            return permittivity, loss_tangent
        except ValueError:
            return None, None

    return None, None


def sanitize_material_name(material_name):
    """
    Sanitize material name for use in stackup files.

    Args:
        material_name (str): Original material name

    Returns:
        str: Sanitized material name
    """
    if not material_name:
        return "unknown"

    # Convert to string and clean
    name = str(material_name).strip().lower()

    # Replace special characters
    name = name.replace('_', '')
    name = name.replace('-', '')
    name = name.replace(' ', '')

    # Map common material types
    if 'copper' in name or 'cu' in name:
        return 'copper'
    elif 'air' in name:
        return 'air'
    elif 'film' in name or 'adhesive' in name:
        return name
    else:
        return name


def collect_materials_from_excel(excel_file):
    """
    Collect materials directly from Excel file using extract_materials_specifications.
    This provides more accurate Dk/Df values than just reading from layer data.

    Args:
        excel_file (str): Path to Excel file

    Returns:
        dict: Dictionary of materials with their properties
    """
    wb = load_workbook(excel_file, data_only=True)
    ws = wb.worksheets[0]

    # Extract material specifications from Excel
    dk_df_dict = extract_materials_specifications(ws)
    dk_df_list = postprocess_materials_dict(dk_df_dict)

    materials = OrderedDict()

    # Add default materials
    materials['copper'] = {
        'type': 'conductor',
        'conductivity': 58000000,
        'permeability': 0.999991
    }

    materials['air'] = {
        'type': 'dielectric',
        'permittivity': 1.0006,
        'loss_tangent': 0
    }

    # Process materials from specifications
    for mat_entry in dk_df_list:
        material_name = mat_entry.get('material', '').lower()
        dk_df_str = mat_entry.get('dk_df')

        if not material_name or material_name in ['copper', 'air']:
            continue

        # Parse Dk/Df values
        permittivity, loss_tangent = parse_dk_df(dk_df_str)

        if permittivity is not None and material_name not in materials:
            materials[material_name] = {
                'type': 'dielectric',
                'permittivity': permittivity,
                'loss_tangent': loss_tangent
            }

    return materials


def collect_unique_materials(layer_data, excel_file=None):
    """
    Collect unique materials from layer data with their Dk/Df values.
    If excel_file is provided, also reads materials from Excel specifications.

    Args:
        layer_data (list): List of layer material entries
        excel_file (str, optional): Path to Excel file for additional material specs

    Returns:
        dict: Dictionary of unique materials with their properties
    """
    # Start with materials from Excel if available
    if excel_file:
        materials = collect_materials_from_excel(excel_file)
    else:
        materials = OrderedDict()
        # Add default materials
        materials['copper'] = {
            'type': 'conductor',
            'conductivity': 58000000,
            'permeability': 0.999991
        }
        materials['air'] = {
            'type': 'dielectric',
            'permittivity': 1.0006,
            'loss_tangent': 0
        }

    # Add default dielectric for EMI and other materials without Dk/Df
    default_dielectric = {
        'type': 'dielectric',
        'permittivity': 3.5,  # Default FR4-like value
        'loss_tangent': 0.02
    }

    # Collect materials from layer data
    for entry in layer_data:
        material_raw = entry.get('material', '')
        dk_df = entry.get('Dk/Df')

        if not material_raw:
            continue

        material_name = sanitize_material_name(material_raw)

        # Skip if already processed
        if material_name in materials:
            continue

        # Skip copper and air
        if material_name in ['copper', 'air']:
            continue

        # Parse Dk/Df values
        permittivity, loss_tangent = parse_dk_df(dk_df)

        if permittivity is not None:
            materials[material_name] = {
                'type': 'dielectric',
                'permittivity': permittivity,
                'loss_tangent': loss_tangent
            }
        else:
            # Use default dielectric properties for materials without Dk/Df (like EMI)
            materials[material_name] = default_dielectric.copy()
            logger.warning(f"Material '{material_name}' has no Dk/Df value, using default: {default_dielectric['permittivity']}/{default_dielectric['loss_tangent']}")

    return materials


def generate_xml_stackup(layer_data, output_file, excel_file=None):
    """
    Generate ANSYS XML format stackup file.

    Args:
        layer_data (list): Processed layer data from read_material_properties
        output_file (str): Path to output XML file
        excel_file (str, optional): Path to Excel file for extracting material specs
    """
    materials = collect_unique_materials(layer_data, excel_file)

    # Calculate elevations (from bottom to top)
    # Convert total height from μm to mm
    total_height_um = sum(entry.get('height', 0) for entry in layer_data if entry.get('height'))
    current_elevation = total_height_um / 1000  # Convert to mm

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>',
        '<c:Control xmlns:c="http://www.ansys.com/control" schemaVersion="1.0">',
        '',
        '  <Stackup schemaVersion="1.0">',
        '    <Materials>'
    ]

    # Write materials section
    for mat_name, mat_props in materials.items():
        if mat_props['type'] == 'conductor':
            xml_lines.extend([
                f'      <Material Name="{mat_name}">',
                '        <Permeability>',
                f'          <Double>{mat_props["permeability"]}</Double>',
                '        </Permeability>',
                '        <Conductivity>',
                f'          <Double>{mat_props["conductivity"]}</Double>',
                '        </Conductivity>',
                '      </Material>'
            ])
        else:
            xml_lines.extend([
                f'      <Material Name="{mat_name}">',
                '        <Permittivity>',
                f'          <Double>{mat_props["permittivity"]}</Double>',
                '        </Permittivity>',
                '        <DielectricLossTangent>',
                f'          <Double>{mat_props["loss_tangent"]}</Double>',
                '        </DielectricLossTangent>',
                '      </Material>'
            ])

    xml_lines.extend([
        '    </Materials>',
        '    <Layers LengthUnit="mm">'
    ])

    # Write layers section
    layer_id = 1
    for entry in layer_data:
        material_name = sanitize_material_name(entry.get('material', 'unknown'))
        thickness = entry.get('height', 0) / 1000  # Convert μm to mm
        layer_name_raw = entry.get('layer', f'Layer{layer_id}')

        # Determine layer type and fill material
        is_conductor = material_name == 'copper'
        layer_type = 'conductor' if is_conductor else 'dielectric'
        type_si = 'conductor' if is_conductor else 'dielectric'

        # Generate layer name
        if is_conductor:
            layer_name = f'wir{layer_id // 2 + 1}' if layer_id > 1 else 'wir1'
        else:
            dielectric_id = (layer_id - 1) // 2
            layer_name = f'Dielectric{dielectric_id}' if dielectric_id > 0 else 'Dielectric'

        # Calculate elevation (bottom of current layer)
        current_elevation -= thickness
        elevation = current_elevation

        # Determine fill material for conductors
        fill_material = ''
        if is_conductor:
            # Look for adjacent dielectric material
            if layer_id > 1:
                prev_entry = layer_data[layer_id - 2] if layer_id - 2 < len(layer_data) else None
                if prev_entry:
                    fill_material = sanitize_material_name(prev_entry.get('material', 'air'))

        color = '#c4ab1e' if is_conductor else '#7f7f7f'

        layer_attrs = [
            f'LayerID="{layer_id}"',
            f'Material="{material_name}"',
            f'Name="{layer_name}"',
            f'Thickness="{thickness:.6f}"',
            f'Elevation="{elevation:.6f}"',
            f'Type="{layer_type}"',
            f'TypeSI="{type_si}"',
            f'Color="{color}"',
            'AbsValueOfBotWidthForTCS="0.000000"',
            'AbsValueOfTopWidthForTCS="0.000000"',
            'BottomRoughness="0.000000"',
            'BottomRoughnessHurayModel=""',
            f'FillMaterial="{fill_material}"' if is_conductor else f'FillMaterial="{material_name}"',
            'IsBottomRoughnessHuray="false"',
            'IsFlipOrientationForTCS="false"',
            'IsSideRoughnessHuray="false"',
            'IsThicknessInvolvedForTCS="true"',
            'IsTopRoughnessHuray="false"',
            'IsUserDefinedAbsValForTCS="false"',
            'SideRoughness="0.000000"',
            'SideRoughnessHurayModel=""',
            'TopRoughness="0.000000"',
            'TopRoughnessHurayModel=""',
            'TraceCrossSectionBottomEdgeRatio="1.000000"',
            'TraceCrossSectionEtchStyle="0"',
            'TraceCrossSectionShape="0"',
            'TraceCrossSectionTopEdgeRatio="1.000000"'
        ]

        if is_conductor:
            layer_attrs.insert(7, 'EtchFactor="0"')

        xml_lines.append(f'      <Layer {" ".join(layer_attrs)}>')

        if is_conductor:
            xml_lines.extend([
                '        <GroissSurfaceRoughness Roughness="0mm"/>',
                '        <GroissBottomSurfaceRoughness Roughness="0mm"/>',
                '        <GroissSideSurfaceRoughness Roughness="0mm"/>'
            ])

        xml_lines.append('      </Layer>')

        layer_id += 1

    xml_lines.extend([
        '    </Layers>',
        '  </Stackup>',
        '',
        '  <SIMaterials>'
    ])

    # Write SIMaterials section
    for mat_name, mat_props in materials.items():
        if mat_props['type'] == 'conductor':
            xml_lines.extend([
                f'    <Conductor AnsoftID="0" Conductivity="{mat_props["conductivity"]}" DerivedFrom="vacuum" Name="{mat_name}" Permeability="{mat_props["permeability"]}"/>'
            ])
        elif mat_name not in ['air']:
            xml_lines.extend([
                f'    <Insulator AnsoftID="0" DerivedFrom="vacuum" LossTangent="{mat_props["loss_tangent"]:.6f}" Name="{mat_name}" Permittivity="{mat_props["permittivity"]:.6f}">',
                '      <Djordjevic-Sarkar EpsDC="0.000000" MeasurementFreq="10000000000.000000" SigmaDC="0.000000"/>',
                '    </Insulator>'
            ])

    xml_lines.extend([
        '  </SIMaterials>',
        '',
        '  <HurayModels>',
        '    <HurayModel MetalSphereRadius="0.000500" ModelName="Low Loss" SpheresPerUnitCell="0.318310" UnitCellArea="0.000001"/>',
        '    <HurayModel MetalSphereRadius="0.000500" ModelName="Medium Loss" SpheresPerUnitCell="0.954930" UnitCellArea="0.000001"/>',
        '    <HurayModel MetalSphereRadius="0.000500" ModelName="High Loss" SpheresPerUnitCell="1.909859" UnitCellArea="0.000001"/>',
        '  </HurayModels>',
        '',
        '</c:Control>',
        ''
    ])

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))

    logger.info(f"XML stackup file generated: {output_file}")
    return output_file


def generate_stackup_info(stackup_excel_file):
    """
    Generate stackup information from Excel file.

    This function:
    1. Reads material properties from the Excel file
    2. Reads layer material information
    3. Finds the center layer row
    4. Swaps air and adhesive pairs based on the center row position

    Args:
        stackup_excel_file (str): Path to the Excel file containing stackup data

    Returns:
        dict: Dictionary containing processed stackup information with keys:
            - 'layer_data': list of processed material properties (after swapping)
            - 'layer_material_info': list of layer material information
            - 'center_row': row number of the center layer
    """
    # Read material properties and layer material information
    layer_data = read_material_properties(stackup_excel_file)
    layer_material_info = read_layer_material(stackup_excel_file)

    # Find center layer row
    center_row_stk = find_center_layer(layer_material_info)

    # Swap air and adhesive pairs based on center row
    layer_data = swap_all_air_adhesive_pairs(layer_data, center_row_stk)

    return {
        'layer_data': layer_data,
        'layer_material_info': layer_material_info,
        'center_row': center_row_stk
    }


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: .venv/Scripts/python.exe stackup/generate_stackup.py <path_to_excel_file>")
        sys.exit(1)

    stackup_excel_file = sys.argv[1]

    try:
        print(f"Processing stackup file: {stackup_excel_file}")
        print("=" * 70)

        stackup_info = generate_stackup_info(stackup_excel_file)

        print("\n" + "=" * 70)
        print("STACKUP INFORMATION GENERATED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nCenter row: {stackup_info['center_row']}")
        print(f"Total layer material entries: {len(stackup_info['layer_material_info'])}")
        print(f"Total material data entries: {len(stackup_info['layer_data'])}")

        # Generate XML output file
        base_name = os.path.splitext(os.path.basename(stackup_excel_file))[0]
        output_dir = os.path.dirname(stackup_excel_file) or '.'
        xml_output = os.path.join(output_dir, f"{base_name}_stackup.xml")

        generate_xml_stackup(stackup_info['layer_data'], xml_output, stackup_excel_file)
        print(f"\n{' ' * 70}")
        print(f"XML stackup file generated: {xml_output}")

    except FileNotFoundError:
        print(f"Error: File not found - {stackup_excel_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating stackup info: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
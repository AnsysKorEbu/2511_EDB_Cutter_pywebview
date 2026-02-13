# generate_stackup.py
"""
Generate XML stackup files from SSS v2.0 data.

This module provides XML generation for ANSYS-compatible stackup files.
Legacy Excel-based functions have been removed - use stackup_new for processing.
"""
from util.logger_module import logger
import re
import json
from pathlib import Path
from collections import OrderedDict


# Pattern constants from excel_reader
DK_DF_PATTERN = r'\(([\d\s\.]*\s*/\s*[\d\s\.]*)\)\s*10GHz?'

# Spec name to material mapping
# Maps spec_name from sss file to (material_type, base_material)
SPEC_NAME_MAPPING = {
    'copper': ('conductor', 'copper'),
    'cu plating': ('conductor', 'copper'),
    'emi': ('dielectric', 'emi'),  # Special case: Type="dielectric" but Material="copper"
    'polyimide': ('dielectric', 'polyimide'),
    'c/l film': ('dielectric', 'c_l_film'),
    'c/l adhesive': ('dielectric', 'c_l_adhesive'),
    'c/l adhesivem': ('dielectric', 'c_l_adhesive'),  # Handle typo
    'c/l adhesive-': ('dielectric', 'c_l_adhesive'),  # Handle variant
    'p/p': ('dielectric', 'pp'),
    'psr': ('dielectric', 'psr'),
    'sus-top': ('conductor', 'copper'),
    'for sus': ('conductor', 'copper'),
}


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


def extract_dk_df_from_layer(layer_dict):
    """
    SSS v2.0 layer dict에서 Dk/Df 추출.

    Args:
        layer_dict: SSS 레이어 딕셔너리 ('dk'/'df' 필드 옵션)

    Returns:
        tuple: (permittivity, loss_tangent) 또는 (None, None)
    """
    dk = layer_dict.get('dk')
    df = layer_dict.get('df')

    # dk와 df가 모두 있고 None이 아닌지 확인
    if dk is not None and df is not None:
        try:
            return float(dk), float(df)
        except (ValueError, TypeError):
            return None, None

    return None, None


def load_cut_layer_data(sss_layers_file, cut_id):
    """
    Load layer data for a specific cut from sss file.

    Args:
        sss_layers_file (str): Path to *_layers_*.sss file
        cut_id (str): Cut identifier (e.g., 'center_cut', 'first_cut')

    Returns:
        dict: {
            'section': 'RIGID 5-3',
            'layers': [
                {'width': 12.0, 'material': 'copper', 'spec_name': 'EMI'},
                ...
            ]
        }
        or None if cut_id not found
    """
    if not sss_layers_file or not Path(sss_layers_file).exists():
        logger.error(f"SSS layers file not found: {sss_layers_file}")
        return None

    try:
        with open(sss_layers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cut_layer_data = data.get('cut_layer_data', {})

        if cut_id not in cut_layer_data:
            logger.warning(f"Cut ID '{cut_id}' not found in sss file")
            return None

        return cut_layer_data[cut_id]

    except Exception as e:
        logger.error(f"Failed to load cut layer data from {sss_layers_file}: {e}")
        return None


def map_spec_name_to_material_info(spec_name, row_number=0):
    """
    Map spec_name from sss to material information.

    Args:
        spec_name (str): Specification name (e.g., 'C/L Film', 'Copper', 'EMI')
        row_number (int): Row/index number for unique material naming

    Returns:
        dict: {
            'material_type': 'dielectric' or 'conductor',
            'material_name': 'C_L_Film_24',  # User requirement: keep original + number
            'base_material': 'c_l_film'
        }

    Mapping rules:
    - 'Copper' → conductor, 'copper'
    - 'EMI' → dielectric (special case per example_stackup.xml), 'emi'
    - 'Polyimide' → dielectric, 'Polyimide_{row}'
    - 'C/L Film' → dielectric, 'C_L_Film_{row}'
    - 'C/L Adhesive' → dielectric, 'C_L_Adhesive_{row}'
    - 'P/P' (Prepreg) → dielectric, 'PP_{row}'
    - 'PSR' → dielectric, 'PSR_{row}'
    """
    if not spec_name:
        return {
            'material_type': 'dielectric',
            'material_name': f'unknown_{row_number}',
            'base_material': 'unknown'
        }

    # Normalize spec_name for lookup
    spec_lower = str(spec_name).lower().strip()

    # Check if we have a direct mapping
    if spec_lower in SPEC_NAME_MAPPING:
        material_type, base_material = SPEC_NAME_MAPPING[spec_lower]
    else:
        # Default to dielectric for unknown materials
        material_type = 'dielectric'
        base_material = spec_lower.replace('/', '_').replace(' ', '_').replace('-', '_')

    # Generate material_name with original capitalization + number
    # Keep original format but sanitize special characters
    material_name_base = str(spec_name).replace('/', '_').replace(' ', '_').replace('-', '_')
    # Always append row_number for unique material names (including _0 for first layer)
    material_name = f"{material_name_base}_{row_number}"

    return {
        'material_type': material_type,
        'material_name': material_name,
        'base_material': base_material
    }


def collect_unique_materials_from_sss(sss_layer_data, excel_file=None):
    """
    Collect unique materials from sss layer data with their Dk/Df values.
    Uses spec_name from sss to determine material types.

    Args:
        sss_layer_data (dict): Layer data from sss file with 'layers' key
        excel_file (str, optional): Path to Excel file for Dk/Df matching

    Returns:
        dict: OrderedDict of unique materials with their properties
    """
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


    # Default dielectric properties
    default_dielectric = {
        'type': 'dielectric',
        'permittivity': 3.5,
        'loss_tangent': 0.02
    }

    # Process layers from sss data
    if not sss_layer_data or 'layers' not in sss_layer_data:
        logger.warning("No layers found in sss_layer_data")
        return materials

    layers = sss_layer_data['layers']

    for idx, layer in enumerate(layers):
        spec_name = layer.get('spec_name', '')
        if not spec_name:
            continue

        # Skip metadata layers (Total Thickness, LAYER markers)
        if 'Total Thickness' in spec_name or spec_name == 'LAYER':
            continue

        # Map spec_name to material info
        mat_info = map_spec_name_to_material_info(spec_name, idx)
        material_name = mat_info['material_name']
        material_type = mat_info['material_type']
        base_material = mat_info['base_material']

        # Skip if already processed
        if material_name in materials:
            continue

        # Skip air (but NOT copper - we need unique copper materials per layer)
        if base_material == 'air':
            continue

        # Initialize Dk/Df values
        permittivity = None
        loss_tangent = None

        # Try to get Dk/Df directly from SSS layer (v2.0 extractor data)
        if material_type == 'dielectric':  # Only for dielectrics
            sss_dk, sss_df = extract_dk_df_from_layer(layer)
            if sss_dk is not None:
                permittivity = sss_dk
                loss_tangent = sss_df
                logger.info(f"Using Dk/Df from SSS v2.0 for '{material_name}': {permittivity}/{loss_tangent}")


        # Create material entry
        if material_type == 'conductor':
            materials[material_name] = {
                'type': 'conductor',
                'conductivity': 58000000,  # Default copper conductivity
                'permeability': 0.999991
            }
        else:
            # Dielectric material
            if permittivity is not None:
                materials[material_name] = {
                    'type': 'dielectric',
                    'permittivity': permittivity,
                    'loss_tangent': loss_tangent if loss_tangent is not None else 0
                }
            else:
                # Use default dielectric properties
                materials[material_name] = default_dielectric.copy()
                logger.warning(f"Material '{material_name}' has no Dk/Df value, using default: {default_dielectric['permittivity']}/{default_dielectric['loss_tangent']}")

    return materials




def generate_xml_stackup_from_sss(sss_layer_data, output_file, excel_file=None):
    """
    Generate ANSYS XML format stackup file from sss layer data.

    Args:
        sss_layer_data (dict): Layer data from sss file for ONE cut with 'layers' key
        output_file (str): Path to output XML file
        excel_file (str, optional): Path to Excel file for Dk/Df matching
    """
    # Collect unique materials from sss data
    materials = collect_unique_materials_from_sss(sss_layer_data, excel_file)

    # Get layers from sss data
    if not sss_layer_data or 'layers' not in sss_layer_data:
        logger.error("No layers found in sss_layer_data")
        return None

    layers = sss_layer_data['layers']

    # Calculate elevations (from bottom to top)
    # Width is already in μm, convert to mm
    total_height_um = sum(layer.get('width', 0) for layer in layers)
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
    for idx, layer in enumerate(layers):
        spec_name = layer.get('spec_name', '')
        width = layer.get('width', 0)
        thickness = width / 1000  # Convert μm to mm

        # Skip layers that shouldn't be in stackup (Total Thickness, LAYER markers, EMI)
        if not spec_name or 'Total Thickness' in spec_name or spec_name == 'LAYER':
            continue

        # Map spec_name to material info
        mat_info = map_spec_name_to_material_info(spec_name, idx)
        material_name = mat_info['material_name']
        material_type = mat_info['material_type']

        # Skip EMI layer (conductor treated incorrectly as dielectric)
        if mat_info['base_material'] == 'emi':
            continue

        is_conductor = material_type == 'conductor'
        layer_type = 'conductor' if is_conductor else 'dielectric'
        type_si = 'conductor' if is_conductor else 'dielectric'
        material_name_for_layer = material_name

        # Generate layer name based on spec_name with row index for uniqueness
        base_layer_name = spec_name.replace('/', '_').replace(' ', '_').replace('-', '_')
        layer_name = f"{base_layer_name}_{idx}"

        # Calculate elevation (bottom of current layer)
        current_elevation -= thickness
        elevation = current_elevation

        # Determine fill material
        fill_material = material_name if layer_type == 'dielectric' else ''
        if layer_type == 'conductor' and idx > 0:
            # Look for adjacent dielectric layer
            prev_layer = layers[idx - 1] if idx > 0 else None
            if prev_layer:
                prev_spec_name = prev_layer.get('spec_name', '')
                if prev_spec_name and prev_spec_name not in ['Total Thickness', 'LAYER']:
                    prev_mat_info = map_spec_name_to_material_info(prev_spec_name, idx - 1)
                    fill_material = prev_mat_info['material_name']

        color = '#c4ab1e' if layer_type == 'conductor' else '#7f7f7f'

        layer_attrs = [
            f'LayerID="{layer_id}"',
            f'Material="{material_name_for_layer}"',
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
            f'FillMaterial="{fill_material}"',
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

        if layer_type == 'conductor':
            layer_attrs.insert(7, 'EtchFactor="0"')

        xml_lines.append(f'      <Layer {" ".join(layer_attrs)}>')

        if layer_type == 'conductor':
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





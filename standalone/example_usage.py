"""
Example usage of standalone stackup data extractor.

This script demonstrates different ways to use the standalone module.
"""

from standalone import extract_stackup_data
from standalone.config import StandaloneConfig
import json


def example1_basic_usage():
    """Example 1: Basic usage - extract layer data only."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Extract layer data
    layer_data = extract_stackup_data("stackup/rawdata.xlsx")

    print(f"Extracted {len(layer_data)} layer entries")
    print("\nFirst 3 entries:")
    for i, entry in enumerate(layer_data[:3], 1):
        print(f"\n{i}. Layer: {entry['layer']}")
        print(f"   Material: {entry['material']}")
        print(f"   Dk/Df: {entry['Dk/Df']}")
        print(f"   Height: {entry['height']} μm")


def example2_with_material_info():
    """Example 2: Extract both layer data and material info."""
    print("\n" + "=" * 60)
    print("Example 2: Extract Layer Data and Material Info")
    print("=" * 60)

    # Extract both
    layer_data, material_info = extract_stackup_data(
        "stackup/rawdata.xlsx",
        include_material_info=True
    )

    print(f"Layer entries: {len(layer_data)}")
    print(f"Material info entries: {len(material_info)}")

    print("\nMaterial info sample:")
    for i, info in enumerate(material_info[:3], 1):
        print(f"{i}. Layer {info['layer']}: {info['material']} (row {info['row']})")


def example3_export_to_json():
    """Example 3: Export data to JSON file."""
    print("\n" + "=" * 60)
    print("Example 3: Export to JSON")
    print("=" * 60)

    # Extract data
    layer_data, material_info = extract_stackup_data(
        "stackup/rawdata.xlsx",
        include_material_info=True
    )

    # Prepare export data
    export_data = {
        'layer_data': layer_data,
        'material_info': material_info,
        'summary': {
            'total_layers': len(layer_data),
            'total_materials': len(material_info),
            'source_file': 'stackup/rawdata.xlsx'
        }
    }

    # Export to JSON
    output_file = "standalone/example_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Data exported to: {output_file}")
    print(f"Summary: {export_data['summary']}")


def example4_filter_by_material():
    """Example 4: Filter data by material type."""
    print("\n" + "=" * 60)
    print("Example 4: Filter by Material Type")
    print("=" * 60)

    # Extract data
    layer_data = extract_stackup_data("stackup/rawdata.xlsx")

    # Filter by material type
    copper_layers = [entry for entry in layer_data if 'copper' in entry['material'].lower()]
    film_layers = [entry for entry in layer_data if 'film' in entry['material'].lower()]
    adhesive_layers = [entry for entry in layer_data if 'adhesive' in entry['material'].lower()]

    print(f"Total entries: {len(layer_data)}")
    print(f"Copper layers: {len(copper_layers)}")
    print(f"Film layers: {len(film_layers)}")
    print(f"Adhesive layers: {len(adhesive_layers)}")

    if copper_layers:
        print("\nCopper layers:")
        for entry in copper_layers[:3]:
            print(f"  - {entry['layer']}: {entry['material']} (height: {entry['height']} μm)")


def example5_calculate_total_height():
    """Example 5: Calculate total stackup height."""
    print("\n" + "=" * 60)
    print("Example 5: Calculate Total Height")
    print("=" * 60)

    # Extract data
    layer_data = extract_stackup_data("stackup/rawdata.xlsx")

    # Calculate total height
    total_height = sum(entry['height'] for entry in layer_data if entry['height'] is not None)

    print(f"Total stackup height: {total_height} μm")
    print(f"Total stackup height: {total_height / 1000:.3f} mm")

    # Group by layer
    layer_heights = {}
    for entry in layer_data:
        layer = entry['layer']
        if layer not in layer_heights:
            layer_heights[layer] = 0
        if entry['height']:
            layer_heights[layer] += entry['height']

    print("\nHeight by layer:")
    for layer, height in sorted(layer_heights.items()):
        print(f"  {layer}: {height} μm")


def main():
    """Run all examples."""
    print("\nStandalone Stackup Data Extractor - Usage Examples")
    print("=" * 60)

    try:
        example1_basic_usage()
        example2_with_material_info()
        example3_export_to_json()
        example4_filter_by_material()
        example5_calculate_total_height()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

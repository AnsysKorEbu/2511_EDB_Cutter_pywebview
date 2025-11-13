import pyedb
from pathlib import Path
from edb import edb_extract, edb_saver


def interface(
    edbpath=r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb\edb.def",
    edbversion="2025.1",
    output_dir="source",
    save_data=True
):
    """
    Extract EDB data and optionally save to compressed JSON files.

    Args:
        edbpath: Path to EDB file
        edbversion: AEDT version (default: "2025.1")
        output_dir: Directory to save extracted data (default: "source")
        save_data: Whether to save data to files (default: True)

    Returns:
        Dictionary with extracted data: {'planes', 'traces', 'components'}
    """
    # Extract EDB folder name from path
    edb_folder_name = Path(edbpath).parent.name

    # Create EDB-specific output directory
    edb_output_dir = Path(output_dir) / edb_folder_name

    print("=" * 70)
    print("EDB Data Extraction")
    print("=" * 70)
    print(f"EDB Path: {edbpath}")
    print(f"EDB Folder Name: {edb_folder_name}")
    print(f"Output Directory: {edb_output_dir}")
    print(f"Version: {edbversion}\n")

    # Open EDB
    print("Opening EDB...")
    edb = pyedb.Edb(edbpath=edbpath, version=edbversion)
    print("[OK] EDB opened successfully\n")

    # Extract data
    print("Extracting data...")
    planes_data = edb_extract.extract_plane_positions(edb)
    print(f"  [OK] Planes: {len(planes_data)} items")

    traces_data = edb_extract.extract_trace_positions(edb)
    print(f"  [OK] Traces: {len(traces_data)} items")

    components_data = edb_extract.extract_component_positions(edb)
    print(f"  [OK] Components: {len(components_data)} items")

    vias_data = edb_extract.extract_via_positions(edb)
    print(f"  [OK] Vias: {len(vias_data)} items")

    nets_data = edb_extract.extract_net_names(edb)
    print(f"  [OK] Nets: {len(nets_data['signal'])} signal, {len(nets_data['power'])} power/ground\n")

    # Save data if requested
    if save_data:
        print("Saving data to compressed JSON files...")
        results = edb_saver.save_edb_data(
            planes_data=planes_data,
            traces_data=traces_data,
            components_data=components_data,
            vias_data=vias_data,
            nets_data=nets_data,
            output_dir=str(edb_output_dir)
        )
        print(f"\n[OK] All data saved to '{edb_output_dir}/' directory")

        # Print summary
        total_size = sum(r['size_mb'] for r in results.values())
        print(f"\nTotal size: {total_size:.2f} MB (compressed)")

    # Close EDB
    edb.close()
    print("\n[OK] EDB closed")

    return {
        'planes': planes_data,
        'traces': traces_data,
        'components': components_data,
        'vias': vias_data,
        'nets': nets_data
    }


if __name__ == "__main__":
    interface()

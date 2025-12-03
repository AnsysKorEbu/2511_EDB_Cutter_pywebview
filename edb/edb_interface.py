import pyedb
from pathlib import Path
from edb import edb_extract, edb_saver
from util.logger_module import logger


def interface(
    edbpath=r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb",
    edbversion="2025.1",
    output_dir="source",
    save_data=True,
    grpc=True
):
    """
    Extract EDB data and optionally save to compressed JSON files.

    Args:
        edbpath: Path to EDB folder (.aedb)
        edbversion: AEDT version (default: "2025.1")
        output_dir: Directory to save extracted data (default: "source")
        save_data: Whether to save data to files (default: True)
        grpc: Use gRPC mode (default: False)

    Returns:
        Dictionary with extracted data: {'planes', 'traces', 'components'}
    """
    # Extract EDB folder name from path
    edb_folder_name = Path(edbpath).name

    # Create EDB-specific output directory
    edb_output_dir = Path(output_dir) / edb_folder_name

    logger.info("=" * 70)
    logger.info("EDB Data Extraction")
    logger.info("=" * 70)
    logger.info(f"EDB Path: {edbpath}")
    logger.info(f"EDB Folder Name: {edb_folder_name}")
    logger.info(f"Output Directory: {edb_output_dir}")
    logger.info(f"Version: {edbversion}")

    # Open EDB
    logger.info("Opening EDB...")
    edb = pyedb.Edb(edbpath=edbpath, version=edbversion, grpc=grpc)
    logger.info("EDB opened successfully")

    # Extract data
    logger.info("Extracting data...")
    planes_data = edb_extract.extract_plane_positions(edb)
    logger.info(f"  Planes: {len(planes_data)} items")

    traces_data = edb_extract.extract_trace_positions(edb)
    logger.info(f"  Traces: {len(traces_data)} items")

    components_data = edb_extract.extract_component_positions(edb)
    logger.info(f"  Components: {len(components_data)} items")

    vias_data = edb_extract.extract_via_positions(edb)
    logger.info(f"  Vias: {len(vias_data)} items")

    nets_data = edb_extract.extract_net_names(edb)
    logger.info(f"  Nets: {len(nets_data['signal'])} signal, {len(nets_data['power'])} power/ground")

    # Save data if requested
    if save_data:
        logger.info("Saving data to compressed JSON files...")
        results = edb_saver.save_edb_data(
            planes_data=planes_data,
            traces_data=traces_data,
            components_data=components_data,
            vias_data=vias_data,
            nets_data=nets_data,
            output_dir=str(edb_output_dir)
        )
        logger.info(f"All data saved to '{edb_output_dir}/' directory")

        # Print summary
        total_size = sum(r['size_mb'] for r in results.values())
        logger.info(f"Total size: {total_size:.2f} MB (compressed)")

    # Close EDB
    edb.close()
    logger.info("EDB closed")

    return {
        'planes': planes_data,
        'traces': traces_data,
        'components': components_data,
        'vias': vias_data,
        'nets': nets_data
    }


if __name__ == "__main__":
    interface()

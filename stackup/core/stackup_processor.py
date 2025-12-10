# stackup_processor.py
"""
Main orchestration class for stackup processing.
Provides a clean, high-level interface for reading and processing PCB stackup data.
"""
from util.logger_module import logger
from stackup.core.config import StackupConfig
from stackup.readers.excel_reader import read_material_properties, read_layer_material
from stackup.core.preprocessing import (
    process_sheets_with_validation,
    swap_all_air_adhesive_pairs,
    find_center_layer
)


class StackupProcessor:
    """
    Main interface for stackup processing.

    This class orchestrates reading, processing, and validating
    PCB stackup data from Excel files.

    Example:
        processor = StackupProcessor(excel_file="data.xlsx")
        layer_data = processor.get_layer_data()
        net_data = processor.get_net_data(sheet_names=["L1", "L2"])
    """

    def __init__(self, excel_file=None, config=None):
        """
        Initialize stackup processor

        Args:
            excel_file (str, optional): Path to Excel file
            config (StackupConfig, optional): Configuration object

        Raises:
            ValueError: If neither excel_file nor config is provided
        """
        if config:
            self.config = config
        elif excel_file:
            self.config = StackupConfig(excel_file=excel_file)
        else:
            # Try to use default config
            self.config = StackupConfig()
            if not self.config.excel_file:
                raise ValueError("No Excel file specified and no default rawdata.xlsx found")

        self._layer_data = None
        self._net_data = None

        logger.info(f"StackupProcessor initialized with file: {self.config.excel_file}")

    def get_layer_data(self, force_reload=False):
        """
        Get processed layer material data

        Args:
            force_reload (bool): Force reload from file even if cached

        Returns:
            list: Layer data with materials, heights, Dk/Df values
            Example:
            [
                {'layer': '1LAYER', 'row': 9, 'material': 'emi',
                 'CU_foil': None, 'Dk/Df': None, 'height': 0.01},
                {'layer': '2LAYER', 'row': 10, 'material': 'copper',
                 'CU_foil': 'Copper', 'Dk/Df': None, 'height': 18.0},
                {'layer': '3LAYER', 'row': 11, 'material': 'c_l_film',
                 'CU_foil': None, 'Dk/Df': '3.17/0.023(10GHz)', 'height': 12.5}
            ]
        """
        if self._layer_data is None or force_reload:
            logger.info("Reading layer material properties...")
            try:
                self._layer_data = read_material_properties(self.config.excel_file)

                # Apply post-processing: swap air/adhesive pairs
                center_row = find_center_layer(self._layer_data)
                if center_row:
                    logger.info(f"Found center layer at row {center_row}")
                    self._layer_data = swap_all_air_adhesive_pairs(
                        self._layer_data,
                        center_row
                    )

                logger.info(f"Successfully loaded {len(self._layer_data)} layer entries")
            except Exception as e:
                logger.error(f"Error reading layer material properties: {e}")
                raise

        return self._layer_data

    def get_net_data(self, sheet_names, force_reload=False):
        """
        Get processed net width data from specified sheets

        Args:
            sheet_names (list): List of sheet names to process
            force_reload (bool): Force reload from file even if cached

        Returns:
            dict: Net data by sheet
            Example:
            {
                'L1_TOP': [
                    {'net': 'vbatt', 'width': 100.0, 'material': 'copper', 'color': (255, 60, 60)},
                    {'net': 'gnd', 'width': 50.0, 'material': 'copper', 'color': (80, 80, 255)}
                ],
                'L2': [...]
            }
        """
        if self._net_data is None or force_reload:
            logger.info(f"Reading net data from sheets: {sheet_names}")
            try:
                self._net_data = process_sheets_with_validation(
                    self.config.excel_file,
                    sheet_names
                )
                total_nets = sum(len(nets) for nets in self._net_data.values())
                logger.info(f"Successfully loaded {total_nets} net entries from {len(self._net_data)} sheets")
            except Exception as e:
                logger.error(f"Error reading net data: {e}")
                raise

        return self._net_data

    def get_stackup_summary(self):
        """
        Get summary information about the stackup

        Returns:
            dict: Summary statistics
            Example:
            {
                'total_layers': 12,
                'materials': ['emi', 'copper', 'c_l_film', 'c_l_adhesive', 'air'],
                'total_height': 123.5,
                'excel_file': 'C:/path/to/rawdata.xlsx'
            }
        """
        layer_data = self.get_layer_data()

        # Extract unique materials
        materials = list(set(entry['material'] for entry in layer_data if entry.get('material')))

        # Calculate total height
        total_height = sum(entry.get('height', 0) for entry in layer_data)

        summary = {
            'total_layers': len(layer_data),
            'materials': sorted(materials),
            'total_height': total_height,
            'excel_file': self.config.excel_file
        }

        logger.info(f"Stackup summary: {len(layer_data)} layers, {len(materials)} unique materials, total height: {total_height}um")

        return summary

    def get_layer_material_info(self):
        """
        Get raw layer material information (without Dk/Df matching)

        Returns:
            list: Raw layer material data
            Example:
            [
                {'layer': 1, 'material': 'emi', 'row': 9},
                {'layer': 2, 'material': 'copper', 'row': 10}
            ]
        """
        logger.info("Reading layer material info...")
        try:
            layer_material_info = read_layer_material(self.config.excel_file)
            logger.info(f"Successfully loaded {len(layer_material_info)} layer material entries")
            return layer_material_info
        except Exception as e:
            logger.error(f"Error reading layer material info: {e}")
            raise

    def reload_all(self):
        """
        Clear all cached data and force reload on next access
        """
        logger.info("Clearing cached data...")
        self._layer_data = None
        self._net_data = None
        logger.info("Cache cleared")

    def __repr__(self):
        """String representation of processor"""
        return f"StackupProcessor(excel_file='{self.config.excel_file}')"

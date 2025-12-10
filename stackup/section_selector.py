"""
Section selector module for stackup processing.
Handles section extraction from Excel and .sss file I/O operations.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from stackup.readers.excel_reader import extract_item_names_from_row8


def extract_sections_from_excel(excel_file_path):
    """
    Extract section names from Excel file row 8.

    Args:
        excel_file_path (str): Path to Excel file

    Returns:
        list: List of section name strings

    Raises:
        FileNotFoundError: If Excel file doesn't exist
        Exception: For other errors during extraction
    """
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"Excel file not found: {excel_file_path}")

    try:
        # Load Excel workbook
        wb = load_workbook(excel_file_path, data_only=True)
        ws = wb.worksheets[0]

        # Extract items from row 8
        items = extract_item_names_from_row8(ws)

        # Extract only the 'name' field from each item
        sections = [item['name'] for item in items if 'name' in item]

        return sections
    except Exception as e:
        raise Exception(f"Failed to extract sections from Excel: {str(e)}")


def generate_sss_filename(edb_folder_name):
    """
    Generate .sss filename with timestamp.

    Args:
        edb_folder_name (str): EDB folder name (e.g., "none_port_design.aedb")

    Returns:
        str: Filename in format "{edb_name}_sections_{timestamp}.sss"
    """
    # Remove .aedb extension if present
    base_name = edb_folder_name.replace('.aedb', '')

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{base_name}_sections_{timestamp}.sss"


class SectionSelector:
    """
    Manages section selection workflow for stackup processing.

    Responsibilities:
    - Extract sections from Excel file
    - Save/load .sss configuration files
    - Validate cut-section mappings
    """

    def __init__(self, excel_file_path):
        """
        Initialize SectionSelector.

        Args:
            excel_file_path (str): Path to Excel file containing section data
        """
        self.excel_file = excel_file_path
        self._sections = None

    def extract_sections(self):
        """
        Extract section names from Excel file.
        Uses cached result if available.

        Returns:
            list: List of section name strings

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            Exception: For other extraction errors
        """
        if self._sections is None:
            self._sections = extract_sections_from_excel(self.excel_file)
        return self._sections

    def save_section_mapping(self, cut_section_map, output_path):
        """
        Save cut-section mapping to .sss JSON file.

        Args:
            cut_section_map (dict): Mapping of cut IDs to section lists
                Example: {'cut_001': ['RIGID 5', 'C/N 1'], 'cut_002': [...]}
            output_path (str): Path to save .sss file

        Raises:
            ValueError: If cut_section_map is empty or invalid
            IOError: If file cannot be written
        """
        if not cut_section_map:
            raise ValueError("cut_section_map cannot be empty")

        # Get available sections
        sections = self.extract_sections()

        # Build .sss file structure
        sss_data = {
            "excel_file": str(Path(self.excel_file).as_posix()),
            "cut_section_mapping": cut_section_map,
            "available_sections": sections,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }

        # Save to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sss_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Failed to write .sss file: {str(e)}")

    def load_section_mapping(self, sss_file_path):
        """
        Load existing .sss configuration file.

        Args:
            sss_file_path (str): Path to .sss file

        Returns:
            dict: Loaded configuration data

        Raises:
            FileNotFoundError: If .sss file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not os.path.exists(sss_file_path):
            raise FileNotFoundError(f".sss file not found: {sss_file_path}")

        try:
            with open(sss_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid .sss file format: {str(e)}", e.doc, e.pos)

    def validate_mapping(self, cut_section_map):
        """
        Validate cut-section mapping.

        Args:
            cut_section_map (dict): Mapping to validate

        Returns:
            tuple: (is_valid: bool, error_messages: list)
        """
        errors = []

        # Check if mapping is empty
        if not cut_section_map:
            errors.append("Mapping is empty")
            return (False, errors)

        # Get available sections
        try:
            sections = self.extract_sections()
        except Exception as e:
            errors.append(f"Failed to extract sections for validation: {str(e)}")
            return (False, errors)

        # Validate each cut's sections
        for cut_id, selected_sections in cut_section_map.items():
            if not selected_sections:
                errors.append(f"Cut '{cut_id}' has no sections selected")
                continue

            # Check if all selected sections are valid
            for section in selected_sections:
                if section not in sections:
                    errors.append(f"Invalid section '{section}' for cut '{cut_id}'")

        is_valid = len(errors) == 0
        return (is_valid, errors)

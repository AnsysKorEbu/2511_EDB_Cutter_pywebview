"""
Standalone Stackup Data Extractor - Main Entry Point

This module provides a simple tkinter GUI for extracting stackup data from Excel files.
Can be run as: python -m standalone
"""

import sys
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .excel_reader import read_material_properties, read_layer_material
from .logger import logger


class StackupExtractorGUI:
    """Simple tkinter GUI for stackup data extraction."""

    def __init__(self, root):
        self.root = root
        self.root.title("Stackup Data Extractor")
        self.root.geometry("800x600")

        self.excel_file = None
        self.layer_data = None
        self.material_info = None

        self._create_widgets()

    def _create_widgets(self):
        """Create GUI widgets."""
        # Top frame for file selection
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Excel File:").pack(side=tk.LEFT)

        self.file_entry = tk.Entry(top_frame, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="Browse...", command=self._browse_file).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Extract", command=self._extract_data, bg="lightblue").pack(side=tk.LEFT, padx=5)

        # Middle frame with tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Layer Data
        layer_frame = tk.Frame(notebook)
        notebook.add(layer_frame, text="Layer Data")

        self.layer_text = scrolledtext.ScrolledText(layer_frame, wrap=tk.WORD, width=80, height=30)
        self.layer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 2: Material Info
        material_frame = tk.Frame(notebook)
        notebook.add(material_frame, text="Material Info")

        self.material_text = scrolledtext.ScrolledText(material_frame, wrap=tk.WORD, width=80, height=30)
        self.material_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bottom frame for export buttons
        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        tk.Button(bottom_frame, text="Export Layer Data (JSON)", command=self._export_layer_json).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Export Material Info (JSON)", command=self._export_material_json).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Clear", command=self._clear_all).pack(side=tk.RIGHT)

        # Status bar
        self.status_label = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _browse_file(self):
        """Open file dialog to select Excel file."""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            self.excel_file = filename

    def _extract_data(self):
        """Extract data from Excel file."""
        excel_file = self.file_entry.get()
        if not excel_file:
            messagebox.showwarning("Warning", "Please select an Excel file first.")
            return

        if not Path(excel_file).exists():
            messagebox.showerror("Error", f"File not found: {excel_file}")
            return

        try:
            self.status_label.config(text="Extracting data...")
            self.root.update()

            # Extract layer data
            self.layer_data = read_material_properties(excel_file)
            self._display_layer_data()

            # Extract material info
            self.material_info = read_layer_material(excel_file)
            self._display_material_info()

            self.status_label.config(text=f"Extraction complete. Found {len(self.layer_data)} layer entries, {len(self.material_info)} material entries.")
            messagebox.showinfo("Success", f"Data extracted successfully!\n\nLayer entries: {len(self.layer_data)}\nMaterial entries: {len(self.material_info)}")

        except Exception as e:
            self.status_label.config(text="Error during extraction")
            messagebox.showerror("Error", f"Failed to extract data:\n{str(e)}")
            logger.error(f"Extraction error: {e}")

    def _display_layer_data(self):
        """Display layer data in text widget."""
        self.layer_text.delete(1.0, tk.END)
        if self.layer_data:
            self.layer_text.insert(tk.END, f"Total entries: {len(self.layer_data)}\n")
            self.layer_text.insert(tk.END, "=" * 80 + "\n\n")

            for i, entry in enumerate(self.layer_data, 1):
                self.layer_text.insert(tk.END, f"Entry {i}:\n")
                self.layer_text.insert(tk.END, f"  Layer:    {entry.get('layer')}\n")
                self.layer_text.insert(tk.END, f"  Row:      {entry.get('row')}\n")
                self.layer_text.insert(tk.END, f"  Material: {entry.get('material')}\n")
                self.layer_text.insert(tk.END, f"  CU_foil:  {entry.get('CU_foil')}\n")
                self.layer_text.insert(tk.END, f"  Dk/Df:    {entry.get('Dk/Df')}\n")
                self.layer_text.insert(tk.END, f"  Height:   {entry.get('height')}\n")
                self.layer_text.insert(tk.END, "\n")

    def _display_material_info(self):
        """Display material info in text widget."""
        self.material_text.delete(1.0, tk.END)
        if self.material_info:
            self.material_text.insert(tk.END, f"Total entries: {len(self.material_info)}\n")
            self.material_text.insert(tk.END, "=" * 80 + "\n\n")

            for i, entry in enumerate(self.material_info, 1):
                self.material_text.insert(tk.END, f"Entry {i}:\n")
                self.material_text.insert(tk.END, f"  Layer:    {entry.get('layer')}\n")
                self.material_text.insert(tk.END, f"  Material: {entry.get('material')}\n")
                self.material_text.insert(tk.END, f"  Row:      {entry.get('row')}\n")
                self.material_text.insert(tk.END, "\n")

    def _export_layer_json(self):
        """Export layer data to JSON file."""
        if not self.layer_data:
            messagebox.showwarning("Warning", "No layer data to export. Extract data first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Layer Data",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.layer_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Layer data exported to:\n{filename}")
                self.status_label.config(text=f"Layer data exported to {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")

    def _export_material_json(self):
        """Export material info to JSON file."""
        if not self.material_info:
            messagebox.showwarning("Warning", "No material info to export. Extract data first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Material Info",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.material_info, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Material info exported to:\n{filename}")
                self.status_label.config(text=f"Material info exported to {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")

    def _clear_all(self):
        """Clear all data and text widgets."""
        self.layer_text.delete(1.0, tk.END)
        self.material_text.delete(1.0, tk.END)
        self.layer_data = None
        self.material_info = None
        self.status_label.config(text="Cleared")


def main():
    """Main entry point for the standalone application."""
    print("Stackup Data Extractor - Standalone Version")
    print("=" * 60)

    # Check if running in GUI mode or CLI mode
    if len(sys.argv) > 1 and sys.argv[1] in ['--cli', '-c']:
        # CLI mode
        if len(sys.argv) < 3:
            print("Usage: python -m standalone --cli <excel_file> [output_file]")
            sys.exit(1)

        excel_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else "stackup_data.json"

        print(f"CLI Mode: Extracting data from {excel_file}")

        try:
            layer_data = read_material_properties(excel_file)
            material_info = read_layer_material(excel_file)

            result = {
                'layer_data': layer_data,
                'material_info': material_info,
                'summary': {
                    'layer_count': len(layer_data),
                    'material_count': len(material_info)
                }
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\nExtraction complete!")
            print(f"  Layer entries: {len(layer_data)}")
            print(f"  Material entries: {len(material_info)}")
            print(f"  Output: {output_file}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    else:
        # GUI mode
        root = tk.Tk()
        app = StackupExtractorGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()

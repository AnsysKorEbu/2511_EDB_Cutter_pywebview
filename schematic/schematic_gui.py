"""
Schematic GUI Module - Full Touchstone Generator

Provides API for browsing Analysis folders, listing touchstone files,
and saving merge configuration as JSON.
"""
import json
from pathlib import Path
from util.logger_module import logger


class SchematicApi:
    """JavaScript API for Schematic GUI (Full Touchstone Generator)"""
    
    def __init__(self, analysis_folder=None):
        """
        Initialize Schematic API.
        
        Args:
            analysis_folder: Optional initial folder path containing .s*p files
        """
        self.analysis_folder_str = str(analysis_folder) if analysis_folder else None
        self.touchstone_files = []
        
        if self.analysis_folder_str:
            self.touchstone_files = self._discover_touchstone_files()
            logger.info(f"Schematic GUI initialized with {len(self.touchstone_files)} touchstone files")
    
    def _discover_touchstone_files(self):
        """
        Scan analysis folder for .s*p touchstone files.
        
        Returns:
            list: List of touchstone file info dicts
        """
        files = []
        if not self.analysis_folder_str:
            return files
            
        analysis_folder = Path(self.analysis_folder_str)
        if not analysis_folder.exists():
            logger.warning(f"Analysis folder does not exist: {analysis_folder}")
            return files
        
        # Find all touchstone files (.s2p, .s4p, .s18p, etc.)
        for ts_file in sorted(analysis_folder.glob("*.s*p")):
            if ts_file.is_file() and ts_file.suffix.startswith('.s'):
                try:
                    file_size = ts_file.stat().st_size
                    files.append({
                        'name': ts_file.name,
                        'path': str(ts_file),
                        'size': file_size
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for {ts_file.name}: {e}")
        
        return files
    
    def browse_analysis_folder(self):
        """
        Open folder browser to select Analysis folder containing .s*p files.
        
        Returns:
            dict: {'success': bool, 'folder': str, 'error': str}
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Set initial directory to Results folder if it exists
            initial_dir = Path('Results').resolve() if Path('Results').exists() else Path.cwd()
            
            folder_path = filedialog.askdirectory(
                title='Select Analysis Folder (containing .s*p touchstone files)',
                initialdir=str(initial_dir)
            )
            
            root.destroy()
            
            if folder_path:
                logger.info(f"Selected analysis folder: {folder_path}")
                return {'success': True, 'folder': folder_path}
            else:
                logger.info("No folder selected")
                return {'success': False, 'error': 'No folder selected'}
                
        except Exception as e:
            error_msg = f"Failed to open folder browser: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def load_analysis_folder(self, folder_path):
        """
        Load touchstone files from analysis folder.
        
        Args:
            folder_path: Path to Analysis folder (string)
        
        Returns:
            dict: {'success': bool, 'files': list, 'folder': str, 'error': str}
        """
        try:
            self.analysis_folder_str = str(folder_path)
            
            # Verify folder exists
            analysis_folder = Path(self.analysis_folder_str)
            if not analysis_folder.exists():
                return {
                    'success': False,
                    'error': f'Folder does not exist: {folder_path}'
                }
            
            # Discover touchstone files
            self.touchstone_files = self._discover_touchstone_files()
            
            logger.info(f"Loaded {len(self.touchstone_files)} touchstone files from: {folder_path}")
            
            return {
                'success': True,
                'files': self.touchstone_files,
                'folder': self.analysis_folder_str
            }
            
        except Exception as e:
            error_msg = f"Failed to load folder: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def get_touchstone_files(self):
        """
        Get list of touchstone files for frontend display.
        
        Returns:
            list: List of dicts with name, path, size
        """
        return self.touchstone_files
    
    def save_merge_configuration(self, config_items):
        """
        Save touchstone merge configuration to JSON file.
        
        Args:
            config_items: List of dicts with format:
                [
                    {'filename': 'cut_001.s18p', 'order': 1, 'flip': False, 'enabled': True},
                    {'filename': 'cut_002.s18p', 'order': 2, 'flip': True, 'enabled': True},
                    ...
                ]
        
        Returns:
            dict: {'success': bool, 'config_file': str, 'error': str}
        """
        try:
            if not self.analysis_folder_str:
                return {'success': False, 'error': 'No analysis folder loaded'}
            
            analysis_folder = Path(self.analysis_folder_str)
            
            # Generate config filename
            config_filename = "full_touchstone_config.json"
            config_path = analysis_folder / config_filename
            
            # Filter only enabled items and sort by order
            enabled_items = [item for item in config_items if item.get('enabled', True)]
            enabled_items.sort(key=lambda x: x.get('order', 0))
            
            # Create configuration data
            config_data = {
                'version': '1.0',
                'analysis_folder': self.analysis_folder_str,
                'total_files': len(enabled_items),
                'merge_sequence': enabled_items
            }
            
            # Save to JSON file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Merge configuration saved: {config_path}")
            logger.info(f"Total enabled files: {len(enabled_items)}")
            
            return {
                'success': True,
                'config_file': str(config_path),
                'total_enabled': len(enabled_items)
            }
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

# <2025> ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited
import os
import json
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_FOLDER = os.path.join(CURRENT_DIR, 'Results')

# Global variable to store the single timestamped folder
_TIMESTAMPED_FOLDER = None

def get_timestamped_folder():
    global _TIMESTAMPED_FOLDER
    if _TIMESTAMPED_FOLDER is None:
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        _TIMESTAMPED_FOLDER = os.path.join(BASE_FOLDER, current_time)
    return _TIMESTAMPED_FOLDER

# Configurable HEIGHT_COLUMN setting
def get_height_column():
    """Get HEIGHT_COLUMN from settings file, default to 94"""
    try:
        settings_file = os.path.join(CURRENT_DIR, 'gui_settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('height_column', 94)
    except Exception:
        pass
    return 94  # Default value

def reload_height_column():
    """Reload HEIGHT_COLUMN setting from file"""
    global HEIGHT_COLUMN
    HEIGHT_COLUMN = get_height_column()
    return HEIGHT_COLUMN

TIMESTAMPED_FOLDER = get_timestamped_folder()

# Main FPCB analysis files
EXCEL_FILE = os.path.join(CURRENT_DIR, 'source', 'FPCB_Section_Map_description_for_ANSYS_simple.xlsx')
RECENT_NETDATA = os.path.join(CURRENT_DIR, 'recent_netdata.json')
SETUP_FILE = os.path.join(CURRENT_DIR, 'setup.json')

# ODB_FILE = os.path.join(PROJECT_ROOT, 'odb2exl', 'source', 'FPCB_sample 1.siw')
ODB_FILE = os.path.join(CURRENT_DIR,'source', "B6_CTC_REV02_1208.tgz")

HEIGHT_COLUMN = get_height_column()

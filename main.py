"""
EDB Cutter - Main Entry Point

This application extracts EDB data using subprocess (avoiding pythonnet conflicts)
and displays it in a GUI for region selection and cutting.
"""
from gui import start_gui

# EDB folder path (modify this to your .aedb folder)
EDB_PATH = r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb"

def main():
    """Start EDB Cutter GUI application"""
    print("=" * 70)
    print("EDB Cutter - GUI Application")
    print("=" * 70)
    print(f"EDB Path: {EDB_PATH}\n")

    start_gui(EDB_PATH)

if __name__ == "__main__":
    main()

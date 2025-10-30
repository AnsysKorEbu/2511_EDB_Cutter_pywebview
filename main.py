# IMPORTANT: Import webview FIRST to avoid pythonnet conflicts
import webview

from gui import start_gui

# EDB file path (modify this to your .aedb path)
EDB_PATH = r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb\edb.def"

def main():
    """Start EDB Cutter GUI application"""
    print("Starting EDB Cutter GUI...")
    print(f"Loading EDB from: {EDB_PATH}")

    start_gui(EDB_PATH)

if __name__ == "__main__":
    main()

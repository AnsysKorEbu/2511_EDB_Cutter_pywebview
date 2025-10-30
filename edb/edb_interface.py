import pyedb
from edb import edb_extract


def interface(edbpath = r"C:\Python_Code\FPCB_XSection_Map\source\B6_CTC_REV02_1208.aedb\edb.def", edbversion = "2025.1" ):
    edb = pyedb.Edb(edbpath=edbpath, version=edbversion)

    planes_data = edb_extract.extract_plane_positions(edb)
    traces_data = edb_extract.extract_trace_positions(edb)

    print("1")


if __name__ == "__main__":
    interface()

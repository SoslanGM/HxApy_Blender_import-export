from zipfile import ZipFile
import os
from datetime import datetime


def TS():
    return datetime.now().strftime("%d-%m-%y_%H-%M-%S")

to_zip = [
    "__init__.py",
    "import_hxa_py.py",
    "export_hxa_py.py",
    "hxapy_util.py",
    "hxapy_header.py",
    "hxapy_read_write.py",
    "hxapy_validate.py"
]

def PackHxA():
    filename = f"HxA_py-{TS()}.zip"
    zf = ZipFile(filename, "w")
    for tz in to_zip:
        zf.write(tz)
    zf.close()
    
    if(os.path.exists(filename)):
        print(f"> Wrote {filename}")
    else:
        print(f"! Write failed: {filename}")

if __name__ == "__main__":
    PackHxA()
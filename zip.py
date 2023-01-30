from zipfile import ZipFile
import os
from datetime import datetime


def TS():
    return datetime.now().strftime("%d-%m-%y_%H-%M-%S")


# might want to switch to a glob at some point
to_zip = [
    "io_scene_hxa\\__init__.py",
    "io_scene_hxa\\import_hxa_py.py",
    "io_scene_hxa\\export_hxa_py.py",
    "io_scene_hxa\\hxapy_util.py",
    "io_scene_hxa\\hxapy_header.py",
    "io_scene_hxa\\hxapy_read_write.py",
    "io_scene_hxa\\hxapy_validate.py",
]


def PackHxA():
    folder = "io_scene_hxa"

    filename = f"HxA_py-{TS()}.zip"
    with ZipFile(filename, "w") as zf:
        for tz in to_zip:
            zf.write(tz)

    return filename


if __name__ == "__main__":
    filename = PackHxA()
    if os.path.exists(filename):
        print(f"> Wrote {filename}")
        with ZipFile(filename, "r") as archive:
            archive.printdir()
    else:
        print(f"! Write failed: {filename}")

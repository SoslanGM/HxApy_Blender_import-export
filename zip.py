from zipfile import ZipFile
import os
from datetime import datetime
import shutil
import pathlib


def TS():
    return datetime.now().strftime("%d-%m-%y_%H-%M-%S")


to_zip = [
    "__init__.py",
    "import_hxa_py.py",
    "export_hxa_py.py",
    "hxapy_util.py",
    "hxapy_header.py",
    "hxapy_read_write.py",
    "hxapy_validate.py",
]


def PackHxA():
    folder = "io_scene_hxa"

    if not os.path.exists(folder):
        os.mkdir(folder)

    for tz in to_zip:
        shutil.copy(tz, folder)

    directory = pathlib.Path(folder)

    filename = f"HxA_py-{TS()}.zip"
    with ZipFile(filename, "w") as zf:
        for filepath in directory.rglob("*"):
            zf.write(filepath)

    shutil.rmtree(folder)

    return filename


if __name__ == "__main__":
    filename = PackHxA()
    if os.path.exists(filename):
        print(f"> Wrote {filename}")
        with ZipFile(filename, "r") as archive:
            archive.printdir()
    else:
        print(f"! Write failed: {filename}")

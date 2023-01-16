bl_info = {
    "name":        "HxA asset format",
    "description": "Import-Export HxA",
    "author":      "SoslanGM (Soslan Guchmazov)",
    "version":     (0, 1),
    "blender":     (3, 0, 0),
    "location":    "File > Import-Export",
    "warning":     "",
    "doc_url":     "https://github.com/SoslanGM/HxApy_Blender_import-export",
    "tracker_url": "",
    "support":     "TESTING",
    "category":    "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_hxa_py" in locals():
        importlib.reload(import_hxa_py)
    if "export_hxa_py" in locals():
        importlib.reload(export_hxa_py)


import bpy
from . import import_hxa_py
from . import export_hxa_py


def menu_func_import(self, context):
    self.layout.operator(import_hxa_py.ImportHXA.bl_idname, text="HxA (.hxa)")


def menu_func_export(self, context):
    self.layout.operator(export_hxa_py.ExportHXA.bl_idname, text="HxA (.hxa)")


classes = (
    import_hxa_py.ImportHXA,
    export_hxa_py.ExportHXA,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

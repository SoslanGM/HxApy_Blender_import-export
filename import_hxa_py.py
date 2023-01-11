bl_info = {
    "name":        "HxA import",
    "description": "Support for import of HxA files",
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

import bpy
from bpy.props import (
    StringProperty
)
from bpy_extras.io_utils import (
    ImportHelper
)


import hxapy_read_write as hxa_rw
import hxapy_util       as hxa_util
import hxapy_validate   as hxa_valid


def restore_mesh(verts, edges, faces, mesh_name="mesh", object_name="object"):
    test_mesh = bpy.data.meshes.new(name=mesh_name)
    test_mesh.from_pydata(verts, edges, faces)

    test_object = bpy.data.objects.new(name=object_name, object_data=test_mesh)

    bpy.context.view_layer.active_layer_collection.collection.objects.link(test_object)
    bpy.ops.object.select_all(action='DESELECT')
    test_object.select_set(True)
    bpy.context.view_layer.objects.active = test_object


def restore_armature(location, scale, heads, tails, names, parents):
    bpy.ops.object.armature_add(enter_editmode=True)
    ob_arm = bpy.context.object
    arm    = ob_arm.data
    ob_arm.location = location
    ob_arm.scale    = scale

    arm.edit_bones[-1].head = heads[0]
    arm.edit_bones[-1].tail = tails[0]
    arm.edit_bones[-1].name = names[0]

    for i in range(1, len(heads)):
        ebone = arm.edit_bones.new(names[i])
        ebone.head = heads[i]
        ebone.tail = tails[i]

    for i in range(len(parents)):
        bpy.ops.armature.select_all(action='DESELECT')
        child_name  = names[i]
        parent_name = parents[i]
        if (parent_name == ""):
            continue

        child  = arm.edit_bones[child_name]
        parent = arm.edit_bones[parent_name]
        child.parent = parent

    ob_arm.show_in_front = True
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    ob_arm.select_set(True)


class ImportHXA(bpy.types.Operator, ImportHelper):
    """Import a HxA file as a mesh"""
    bl_idname  = "import_model.hxa"
    bl_label   = "Import HxA"
    bl_options = {'REGISTER'}

    filename_ext = ".hxa"
    filter_glob: StringProperty(
        default = "*.hxa",
        options = {'HIDDEN'}
    )

    def execute(self, context):
        silent = True
        hxa_dict = hxa_rw.HxaToDict(self.properties.filepath, silent)

        if not hxa_valid.hxa_util_validate(hxa_dict):
            self.report({'ERROR'}, f"{self.filepath} couldn't pass validation")
            return {'CANCELLED'}

        meta_data_count = hxa_dict["nodes"][0]["meta_data_count"]
        if (meta_data_count != 0):
            meta_data  = hxa_dict["nodes"][0]["meta_data"]

            # *** meta containers
            for meta in meta_data:
                if (meta["name"] == "meta mesh data"):
                    meta_meshdata = meta

                if (meta["name"] == "meta shapekeys"):
                    meta_shapekeys = meta

                if (meta["name"] == "meta armature data"):
                    meta_armaturedata = meta

                # should I lump these two into another meta container?
                if (meta["name"] == "meta weight indexes"):
                    meta_weightindexes = meta
                if (meta["name"] == "meta vertex weights"):
                    meta_vertexweights = meta

                if (meta["name"] == "meta custom properties"):
                    meta_customproperties = meta

                if (meta["name"] == "meta creases"):
                    meta_creases = meta

            # ** mesh data
            meta_meshdata_entries = meta_meshdata["data"]
            for meta in meta_meshdata_entries:
                if (meta["name"] == "meta objectname"):
                    meta_objectname = meta

                if (meta["name"] == "meta meshname"):
                    meta_meshname = meta

                if (meta["name"] == "meta location"):
                    meta_location = meta

                if (meta["name"] == "meta scale"):
                    meta_scale = meta

            # ** armature data
            if ("meta_armaturedata" in locals()):
                meta_armaturedata_entries = meta_armaturedata["data"]
                for meta in meta_armaturedata_entries:
                    if (meta["name"] == "meta armature location"):
                        meta_armature_location = meta

                    if (meta["name"] == "meta armature scale"):
                        meta_armature_scale = meta

                    if (meta["name"] == "meta bones heads"):
                        meta_bones_heads = meta

                    if (meta["name"] == "meta bones tails"):
                        meta_bones_tails = meta

                    if (meta["name"] == "meta bones names"):
                        meta_bones_names = meta

                    if (meta["name"] == "meta bones parents"):
                        meta_bones_parents = meta

        if not silent:
            print(meta_objectname["data"])
            print(meta_meshname["data"])
            print(meta_location["data"])
            print(meta_scale["data"])

        vertex_count = hxa_dict["nodes"][0]["content"]["vertex_count"]
        vert_data    = hxa_dict["nodes"][0]["content"]["vertex_stack"]["layers"][0]["data"]
        ref_data     = hxa_dict["nodes"][0]["content"]["corner_stack"]["layers"][0]["data"]

        # - Add edge verts to the mesh, then write creases to mesh after picking out the edges?
        verts = hxa_util.BreakUp(vert_data, vertex_count*3, 3)

        if ("meta_creases" in locals()):
            edge_data = meta_creases["data"][0]["data"]
            arrlen    = meta_creases["data"][0]["array_length"]
            edges = hxa_util.BreakUp(edge_data, arrlen, 2)
            crease_values = meta_creases["data"][1]["data"]

            crease_dict = {}
            for i in range(len(edges)):
                e = edges[i]
                k = str(f"{e[0]} {e[1]}")
                v = crease_values[i]
                crease_dict[k] = v

        else:
            edges = []  # for now

        faces = hxa_util.RestoreFaces(ref_data)

        me_name = meta_meshname["data"] if "meta_meshname" in locals() else "imported HxA mesh"
        ob_name = meta_objectname["data"] if "meta_objectname" in locals() else "imported HxA object"

        restore_mesh(verts, edges, faces, me_name, ob_name)
        # - 1: apply scale and position post-load
        # now, select mesh and apply
        # mesh_object = bpy.data.objects[meta_objectname['data']]
        mesh_object = bpy.context.object

        if ("meta_location" in locals()):
            x, y, z = meta_location["data"]

            mesh_object.location.x = x
            mesh_object.location.y = y
            mesh_object.location.z = z

        if ("meta_scale" in locals()):
            x, y, z = meta_scale["data"]

            mesh_object.scale.x = x
            mesh_object.scale.y = y
            mesh_object.scale.z = z

        if ("meta_armature_location" in locals()):
            armature_location = meta_armature_location["data"]

        if ("meta_armature_scale" in locals()):
            armature_scale = meta_armature_scale["data"]

        if ("meta_creases" in locals()):
            mesh_edges = mesh_object.data.edges
            edge_verts = [list(e.vertices) for e in mesh_object.data.edges]
            for i in range(len(crease_values)):
                e = edge_verts[i]
                k = str(f"{e[0]} {e[1]}")
                mesh_edges[i].crease = crease_dict[k]

        if ("meta_shapekeys" in locals()):
            shapekeys_data = meta_shapekeys["data"]

            for i in range(len(shapekeys_data)):
                shapekeys_values = hxa_util.BreakUp(shapekeys_data[i]['data'], vertex_count*3, 3)
                shapekey = mesh_object.shape_key_add(name=shapekeys_data[i]['name'], from_mix=True)
                for i in range(vertex_count):
                    shapekey.data[i].co = shapekeys_values[i]

        if ("meta_armaturedata" in locals()):
            bone_count = meta_bones_heads["array_length"] / 3
            heads = hxa_util.BreakUp(meta_bones_heads["data"], int(bone_count)*3, 3)

            tails = hxa_util.BreakUp(meta_bones_tails["data"], int(bone_count)*3, 3)
            names   = [x["data"] for x in meta_bones_names["data"]]
            parents = [x["data"] for x in meta_bones_parents["data"]]

            for i in range(len(heads)):
                print(f"{heads[i]} - {tails[i]}")
            for n in names:
                print(n)
            for p in parents:
                print(p)

            restore_armature(armature_location, armature_scale, heads, tails, names, parents)

            # parent armature, apply location and scale
            ob_arm = bpy.context.object
            # arm    = ob_arm.data

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            mesh_object.select_set(True)
            ob_arm.select_set(True)
            bpy.context.view_layer.objects.active = ob_arm
            bpy.ops.object.parent_set(type='ARMATURE_NAME')

        # - does this exist without armatures? (does this need to get indented into the armature block :) )
        # *** Vertex weights
        if (("meta_weightindexes" in locals()) & ("meta_vertexweights" in locals())):
            vindex_list = meta_weightindexes["data"]
            vgroup_list = meta_vertexweights["data"]

            # ** write weights
            for i in range(int(bone_count)):
                indexes = vindex_list[i]["data"]
                weights = vgroup_list[i]["data"]
                vgroup_size = len(weights)
                for j in range(vgroup_size):
                    mesh_object.vertex_groups[i].add([indexes[j]], weights[j], 'REPLACE')

        # *** Custom properties
        # assumption: custom props are saved on the mesh object. It's fine, but something to think about.
        if ("meta_customproperties" in locals()):
            customprop_entries = meta_customproperties["data"]
            for customprop in customprop_entries:
                mesh_object[customprop["name"]] = customprop["data"]

        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportHXA.bl_idname, text="HxA (.hxa)")


def register():
    bpy.utils.register_class(ImportHXA)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportHXA)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

import bpy

from bpy.props import StringProperty
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper
)

from . import hxapy_read_write as hxa_rw
from . import hxapy_util as hxa_util
from . import hxapy_validate as hxa_valid

import logging

log = logging.getLogger(__name__)


class ImportHXA(bpy.types.Operator, ImportHelper):
    """Import a HxA file as a mesh"""

    bl_idname = "import_model.hxa"
    bl_label = "Import HxA"
    bl_options = {"REGISTER"}

    filename_ext = ".hxa"
    filter_glob: StringProperty(default="*.hxa", options={"HIDDEN"})

    def execute(self, context):
        try:
            f = open(self.filepath, "rb")
        except OSError:
            self.report(
                {"ERROR"},
                f"HXA Error: File {self.filepath} could not be open for reading\n",
            )
            log.info(f"HXA Error: File {self.filepath} could not be open for reading\n")
            return {"CANCELLED"}

        hxa_dict = hxa_rw.read_hxa(f)
        f.close()

        if not hxa_valid.hxa_util_validate(hxa_dict):
            self.report({"ERROR"}, f"{self.filepath} couldn't pass validation")
            log.info(f"{self.filepath} couldn't pass validation")
            return {"CANCELLED"}

        meta_shapekeys = None
        meta_armaturedata = None
        meta_weightindexes = None
        meta_vertexweights = None
        meta_customproperties = None
        meta_creases = None
        meta_objectname = None
        meta_meshname = None
        meta_location = None
        meta_scale = None
        meta_armature_location = None
        meta_armature_scale = None
        meta_bones_heads = None
        meta_bones_tails = None
        meta_bones_names = None
        meta_bones_parents = None
        meta_data_count = hxa_dict["nodes"][0]["meta_data_count"]
        if meta_data_count > 0:
            meta_data = hxa_dict["nodes"][0]["meta_data"]

            metas_present = {meta["name"]: meta for meta in meta_data}
            meta_meshdata = metas_present["meta mesh data"]

            if "meta shapekeys" in metas_present.keys():
                meta_shapekeys = metas_present["meta shapekeys"]

            if "meta armature data" in metas_present.keys():
                meta_armaturedata = metas_present["meta armature data"]

            if "meta weight indexes" in metas_present.keys():
                meta_weightindexes = metas_present["meta weight indexes"]

            if "meta vertex weights" in metas_present.keys():
                meta_vertexweights = metas_present["meta vertex weights"]

            if "meta custom properties" in metas_present.keys():
                meta_customproperties = metas_present["meta custom properties"]

            if "meta creases" in metas_present.keys():
                meta_creases = metas_present["meta creases"]

            # ** mesh data
            meta_meshdata_entries = meta_meshdata["data"]
            metas_present = {meta["name"]: meta for meta in meta_meshdata_entries}

            if "meta objectname" in metas_present.keys():
                meta_objectname = metas_present["meta objectname"]
                log.debug(meta_objectname["data"])

            if "meta meshname" in metas_present.keys():
                meta_meshname = metas_present["meta meshname"]
                log.debug(meta_meshname["data"])

            if "meta location" in metas_present.keys():
                meta_location = metas_present["meta location"]
                log.debug(meta_location["data"])

            if "meta scale" in metas_present.keys():
                meta_scale = metas_present["meta scale"]
                log.debug(meta_scale["data"])

            # ** armature data
            if meta_armaturedata:
                meta_armaturedata_entries = meta_armaturedata["data"]
                metas_present = {
                    meta["name"]: meta for meta in meta_armaturedata_entries
                }

                if "meta armature location" in metas_present.keys():
                    meta_armature_location = metas_present["meta armature location"]

                if "meta armature scale" in metas_present.keys():
                    meta_armature_scale = metas_present["meta armature scale"]

                if "meta bones heads" in metas_present.keys():
                    meta_bones_heads = metas_present["meta bones heads"]

                if "meta bones tails" in metas_present.keys():
                    meta_bones_tails = metas_present["meta bones tails"]

                if "meta bones names" in metas_present.keys():
                    meta_bones_names = metas_present["meta bones names"]

                if "meta bones parents" in metas_present.keys():
                    meta_bones_parents = metas_present["meta bones parents"]


        vertex_count = hxa_dict["nodes"][0]["content"]["vertex_count"]
        vert_data = hxa_dict["nodes"][0]["content"]["vertex_stack"]["layers"][0]["data"]
        ref_data = hxa_dict["nodes"][0]["content"]["corner_stack"]["layers"][0]["data"]

        # - Add edge verts to the mesh, then write creases to mesh after picking out the edges?
        verts = hxa_util.break_list_up(vert_data, vertex_count * 3, 3)

        if meta_creases:
            edge_data = meta_creases["data"][0]["data"]
            arrlen = len(meta_creases["data"][0]["data"])
            edges = hxa_util.break_list_up(edge_data, arrlen, 2)
            crease_values = meta_creases["data"][1]["data"]

            crease_dict = {}
            for i in range(len(edges)):
                e = edges[i]
                k = str(f"{e[0]} {e[1]}")
                v = crease_values[i]
                crease_dict[k] = v
        else:
            edges = []  # for now

        faces = hxa_util.restore_faces(ref_data)

        if meta_meshname:
            me_name = meta_meshname["data"]
        else:
            me_name = "imported HxA mesh"
        
        if meta_objectname:
            ob_name = meta_objectname["data"]
        else:
            ob_name = "imported HxA object"

        restore_mesh(verts, edges, faces, me_name, ob_name)
        
        mesh_object = bpy.context.object

        if meta_location:
            x, y, z = meta_location["data"]

            mesh_object.location.x = x
            mesh_object.location.y = y
            mesh_object.location.z = z

        if meta_scale:
            x, y, z = meta_scale["data"]

            mesh_object.scale.x = x
            mesh_object.scale.y = y
            mesh_object.scale.z = z

        if meta_armature_location:
            armature_location = meta_armature_location["data"]

        if meta_armature_scale:
            armature_scale = meta_armature_scale["data"]

        if meta_creases:
            mesh_edges = mesh_object.data.edges
            edge_verts = [list(e.vertices) for e in mesh_object.data.edges]
            for i in range(len(crease_values)):
                e = edge_verts[i]
                k = str(f"{e[0]} {e[1]}")
                mesh_edges[i].crease = crease_dict[k]

        if meta_shapekeys:
            shapekeys_data = meta_shapekeys["data"]

            for i in range(len(shapekeys_data)):
                shapekeys_values = hxa_util.break_list_up(
                    shapekeys_data[i]["data"], vertex_count * 3, 3
                )
                shapekey = mesh_object.shape_key_add(
                    name=shapekeys_data[i]["name"], from_mix=True
                )
                for i in range(vertex_count):
                    shapekey.data[i].co = shapekeys_values[i]

        if meta_armaturedata:
            bone_count = len(meta_bones_heads["data"]) / 3
            heads = hxa_util.break_list_up(
                meta_bones_heads["data"], int(bone_count) * 3, 3
            )

            tails = hxa_util.break_list_up(
                meta_bones_tails["data"], int(bone_count) * 3, 3
            )
            names = [x["data"] for x in meta_bones_names["data"]]
            parents = [x["data"] for x in meta_bones_parents["data"]]

            restore_armature(
                armature_location, armature_scale, heads, tails, names, parents
            )

            # parent armature, apply location and scale
            ob_arm = bpy.context.object
            # arm    = ob_arm.data

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            mesh_object.select_set(True)
            ob_arm.select_set(True)
            bpy.context.view_layer.objects.active = ob_arm
            bpy.ops.object.parent_set(type="ARMATURE_NAME")

        # - does this exist without armatures? (does this need to get indented into the armature block :) )
        # *** Vertex weights
        if (meta_weightindexes != None) & (meta_vertexweights != None):
            vindex_list = meta_weightindexes["data"]
            vgroup_list = meta_vertexweights["data"]

            # ** write weights
            for i in range(int(bone_count)):
                indexes = vindex_list[i]["data"]
                weights = vgroup_list[i]["data"]
                vgroup_size = len(weights)
                for j in range(vgroup_size):
                    mesh_object.vertex_groups[i].add(
                        [indexes[j]], weights[j], "REPLACE"
                    )

        # *** Custom properties
        # assumption: custom props are saved on the mesh object. It's fine, but something to think about.
        if meta_customproperties:
            customprop_entries = meta_customproperties["data"]
            for customprop in customprop_entries:
                mesh_object[customprop["name"]] = customprop["data"]


        bpy.ops.object.shade_flat()

        return {"FINISHED"}


def restore_mesh(verts, edges, faces, mesh_name="mesh", object_name="object"):
    test_mesh = bpy.data.meshes.new(name=mesh_name)
    test_mesh.from_pydata(verts, edges, faces)

    test_object = bpy.data.objects.new(name=object_name, object_data=test_mesh)

    bpy.context.view_layer.active_layer_collection.collection.objects.link(test_object)
    bpy.ops.object.select_all(action="DESELECT")
    test_object.select_set(True)
    bpy.context.view_layer.objects.active = test_object


def restore_armature(location, scale, heads, tails, names, parents):
    bpy.ops.object.armature_add(enter_editmode=True)
    ob_arm = bpy.context.object
    arm = ob_arm.data
    ob_arm.location = location
    ob_arm.scale = scale

    arm.edit_bones[-1].head = heads[0]
    arm.edit_bones[-1].tail = tails[0]
    arm.edit_bones[-1].name = names[0]

    for i in range(1, len(heads)):
        ebone = arm.edit_bones.new(names[i])
        ebone.head = heads[i]
        ebone.tail = tails[i]

    for i in range(len(parents)):
        bpy.ops.armature.select_all(action="DESELECT")
        child_name = names[i]
        parent_name = parents[i]
        if parent_name == "":
            continue

        child = arm.edit_bones[child_name]
        parent = arm.edit_bones[parent_name]
        child.parent = parent

    ob_arm.show_in_front = True
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    ob_arm.select_set(True)

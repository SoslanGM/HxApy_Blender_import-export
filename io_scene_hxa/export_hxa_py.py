import bpy
import bmesh


from . import hxapy_header as hxa
from . import hxapy_util as hxa_util
from . import hxapy_read_write as hxa_rw
from . import hxapy_validate as hxa_valid

from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

import logging

log = logging.getLogger(__name__)


class ExportHXA(bpy.types.Operator, ExportHelper):
    """Export a mesh as a HxA file"""

    bl_idname = "export_model.hxa"
    bl_label = "Export HxA"
    bl_options = {"REGISTER"}

    filename_ext = ".hxa"
    filter_glob: StringProperty(default="*.hxa", options={"HIDDEN"})

    def execute(self, context):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")

        hxa_dict = export_payload()
        if not hxa_valid.hxa_util_validate(hxa_dict):
            log.info(f"{self.filepath} couldn't pass validation")
            self.report({"ERROR"}, f"{self.filepath} couldn't pass validation")
            return {"CANCELLED"}

        try:
            f = open(self.filepath, "wb")
        except OSError:
            log.info(f"HXA Error: File {self.filepath} could not be open for writing\n")
            self.report(
                {"ERROR"},
                f"HXA Error: File {self.filepath} could not be open for writing\n",
            )
            return {"CANCELLED"}

        hxa_rw.write_hxa(f, hxa_dict)
        f.close()

        return {"FINISHED"}


def hxa_meta(name, typ, data):
    m = {"name": name, "type": typ, "data": data}
    return m


def meta__armature_data(arm_ob, arm):
    """
    Packs all the armature(bones) data into HxA meta fields.
    """
    arm_location = arm_ob.location[:]
    arm_scale = arm_ob.scale[:]
    bone_count = len(arm.bones)

    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode="EDIT")
    heads = [list(x.head) for x in arm.edit_bones]
    tails = [list(x.tail) for x in arm.edit_bones]
    bpy.ops.object.mode_set(mode="OBJECT")

    log.debug("Edit bone heads")
    for h in heads:
        log.debug(h)
    log.debug("Edit bone tails")
    for t in tails:
        log.debug(t)

    heads = hxa_util.flatten_list(heads)
    tails = hxa_util.flatten_list(tails)
    names = [x.name for x in arm.bones]
    parents = [x.parent.name if x.parent else "" for x in arm.bones]

    meta_armature_data_entries = []
    meta_armature_data_entries.append(
        hxa_meta(
            "meta armature location", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, arm_location
        )
    )
    meta_armature_data_entries.append(
        hxa_meta("meta armature scale", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, arm_scale)
    )
    meta_armature_data_entries.append(
        hxa_meta("meta bones heads", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, heads)
    )
    meta_armature_data_entries.append(
        hxa_meta("meta bones tails", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, tails)
    )

    bone_names_entries = [
        hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_TEXT, names[i])
        for i in range(bone_count)
    ]
    meta_armature_data_entries.append(
        hxa_meta(
            "meta bones names", hxa.HXAMetaDataType.HXA_MDT_META, bone_names_entries
        )
    )

    bone_parents_entries = [
        hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_TEXT, parents[i])
        for i in range(bone_count)
    ]
    meta_armature_data_entries.append(
        hxa_meta(
            "meta bones parents", hxa.HXAMetaDataType.HXA_MDT_META, bone_parents_entries
        )
    )

    meta_armature_data = hxa_meta(
        "meta armature data",
        hxa.HXAMetaDataType.HXA_MDT_META,
        meta_armature_data_entries,
    )

    return meta_armature_data


def extract_weights(ob):
    vgroups = ob.vertex_groups

    indexes_biglist = [[] for _ in vgroups]
    weights_biglist = [[] for _ in vgroups]
    for vi, vert in enumerate(ob.data.vertices):
        for g in vert.groups:
            indexes_biglist[g.group].append(vi)
            weights_biglist[g.group].append(g.weight)
    
    return (indexes_biglist, weights_biglist)


def hxapy_type_meta(typ):
    """Which HxA meta type will we use to write this type into the export file?"""
    if typ == int:
        return hxa.HXAMetaDataType.HXA_MDT_INT64
    elif typ == float:
        return hxa.HXAMetaDataType.HXA_MDT_DOUBLE
    elif typ == str:
        return hxa.HXAMetaDataType.HXA_MDT_TEXT


# def ExportPayload(context, filepath):
def export_payload():
    """
    The overarching function to produce our dictionary representation of a HxA file,
    before we write it to disk.
    """
    bm = bmesh.new()
    ob_mesh = bpy.context.object
    me = ob_mesh.data
    bm.from_mesh(me)

    vert_count = len(bm.verts)
    face_count = len(bm.faces)
    verts = [[c for c in v.co] for v in bm.verts]
    faces = [f for f in bm.faces]
    references = [[v.index for v in f.verts] for f in faces]
    references = [
        [-x - 1 if _ref.index(x) == len(_ref) - 1 else x for x in _ref]
        for _ref in references
    ]

    verts = hxa_util.flatten_list(verts)
    references = hxa_util.flatten_list(references)
    log.debug(verts)
    log.debug(references)

    bm.free()

    hxa_dict = {}
    hxa_dict["version"] = hxa.HXA_VERSION_FORMAT
    hxa_dict["node_count"] = 1

    # *** Meta data
    meta_data = []

    # ** Mesh(meta) data
    meta_meshdata_entries = []
    meta_meshdata_entries.append(
        hxa_meta("meta objectname", hxa.HXAMetaDataType.HXA_MDT_TEXT, ob_mesh.name)
    )
    meta_meshdata_entries.append(
        hxa_meta("meta meshname", hxa.HXAMetaDataType.HXA_MDT_TEXT, me.name)
    )
    meta_meshdata_entries.append(
        hxa_meta(
            "meta location", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, ob_mesh.location[:]
        )
    )
    meta_meshdata_entries.append(
        hxa_meta("meta scale", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, ob_mesh.scale[:])
    )

    meta_data.append(
        hxa_meta(
            "meta mesh data", hxa.HXAMetaDataType.HXA_MDT_META, meta_meshdata_entries
        )
    )

    # ** Shapekeys
    if ob_mesh.data.shape_keys:
        object_shapekeys = ob_mesh.data.shape_keys.key_blocks
        shapekey_count = len(object_shapekeys)

        meta_shapekeys_data = []
        for i in range(shapekey_count):
            name = object_shapekeys[i].name
            shapekey_values = []
            for x in object_shapekeys[i].data.values():
                shapekey_values += [y for y in x.co]

            meta_shapekeys_data.append(
                hxa_meta(name, hxa.HXAMetaDataType.HXA_MDT_DOUBLE, shapekey_values)
            )

        meta_data.append(
            hxa_meta(
                "meta shapekeys", hxa.HXAMetaDataType.HXA_MDT_META, meta_shapekeys_data
            )
        )

    # ** Armature
    if ob_mesh.parent:
        if (ob_mesh.parent.type == "ARMATURE") & (
            type(ob_mesh.parent.data) == bpy.types.Armature
        ):
            ob_arm = ob_mesh.parent
            arm = ob_arm.data

            meta_armaturedata = meta__armature_data(ob_arm, arm)
            meta_data.append(meta_armaturedata)

    # ** Vertex weights
    if len(meta_data) > 0:
        indexes_list, weights_list = extract_weights(ob_mesh)

        vgroup_count = len(ob_mesh.vertex_groups)
        if vgroup_count:
            # vertex indexes
            meta_weightindexes_data = [
                hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_INT64, indexes_list[i])
                for i in range(vgroup_count)
            ]
            meta_data.append(
                hxa_meta(
                    "meta weight indexes",
                    hxa.HXAMetaDataType.HXA_MDT_META,
                    meta_weightindexes_data,
                )
            )

            # vertex weights
            meta_vertexweights_data = [
                hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, weights_list[i])
                for i in range(vgroup_count)
            ]
            meta_data.append(
                hxa_meta(
                    "meta vertex weights",
                    hxa.HXAMetaDataType.HXA_MDT_META,
                    meta_vertexweights_data,
                )
            )

    # ** creases
    creases = [x.crease for x in me.edges]
    edges = [list(e.vertices) for e in me.edges]
    crease_tuples = []
    for i in range(len(edges)):
        crease_tuples.append((edges[i], creases[i]))

    crease_tuples = sorted(crease_tuples, key=lambda t: (t[0][0], t[0][1]))

    log.debug(f"> {edges}")
    # sorted_edges = sorted(edges, key = lambda x: (x[0], x[1]))
    sorted_edges, sorted_creases = zip(*crease_tuples)
    edge_verts = hxa_util.flatten_list(sorted_edges)
    log.debug(f"Edge verts: {edge_verts}")

    # check for !=0 creases
    creases_present = len([x != 0 for x in creases]) > 0
    if creases_present:
        meta_creases_data_entries = []
        meta_creases_data_entries.append(
            hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_INT64, edge_verts)
        )
        meta_creases_data_entries.append(
            hxa_meta("", hxa.HXAMetaDataType.HXA_MDT_DOUBLE, sorted_creases)
        )

        meta_data.append(
            hxa_meta(
                "meta creases",
                hxa.HXAMetaDataType.HXA_MDT_META,
                meta_creases_data_entries,
            )
        )

    # ** custom props
    custom_props = list(ob_mesh.keys())
    if len(custom_props) > 0:
        meta_customprops_data = []
        for cp in custom_props:
            customprop = ob_mesh[cp]
            import idprop

            if type(customprop) == idprop.types.IDPropertyArray:
                al = len(customprop)
                mtype = hxa.HXAMetaDataType(type(customprop[0]))
                data = list(customprop)
            else:
                mtype = hxa.HXAMetaDataType(type(customprop))
                data = customprop
                if mtype == hxa.HXA_MDT_TEXT:
                    al = len(data)
                else:
                    al = 1

            meta_cp_name = cp
            meta_cp = {
                "name_length": len(meta_cp_name),
                "name": meta_cp_name,
                "type": hxa.HXAMetaDataType(mtype).value,
                "array_length": al,
                "data": data,
            }
            meta_customprops_data.append(meta_cp)
            # - I'll do this later. Might not be as straightforward.
            # meta_customprops_data.append(hxa_meta(meta_cp_name, hxa.HXAMetaType(mtype).value, data))

        meta_data.append(
            hxa_meta(
                "meta custom properties",
                hxa.HXAMetaDataType.HXA_MDT_META,
                meta_customprops_data,
            )
        )

    # *** Mesh(geometry) data
    vertex_layer = {
        "name_length": len(hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME),
        "name": hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME,
        "components": hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS,
        "type": hxa.HXALayerDataType.HXA_LDT_FLOAT,
        "data": verts,
    }
    vert_stack = {"layer_count": 1, "layers": [vertex_layer]}

    reference_layer = {
        "name_length": len(hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME),
        "name": hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME,
        "components": hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_COMPONENTS,
        "type": hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_TYPE,
        "data": references,
    }
    corner_stack = {"layer_count": 1, "layers": [reference_layer]}

    edge_stack = {"layer_count": 0, "layers": []}

    face_stack = {"layer_count": 0, "layers": []}

    content = {
        "vertex_count": vert_count,
        "vertex_stack": vert_stack,
        "edge_corner_count": len(references),
        "corner_stack": corner_stack,
        "edge_stack": edge_stack,
        "face_count": face_count,
        "face_stack": face_stack,
    }
    node = {
        "type": hxa.HXANodeType.HXA_NT_GEOMETRY,
        "meta_data_count": 0,
        "meta_data": [],
        "content": content,
    }
    hxa_dict["nodes"] = [node]
    return hxa_dict

import bpy
import bmesh

from . import hxapy_header as hxa
from . import hxapy_util as hxa_util
from . import hxapy_read_write as hxa_rw
from . import hxapy_validate as hxa_valid

from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper


class ExportHXA(bpy.types.Operator, ExportHelper):
    """Export a mesh as a HxA file"""

    bl_idname = "export_model.hxa"
    bl_label = "Export HxA"
    bl_options = {"REGISTER"}

    filename_ext = ".hxa"
    filter_glob: StringProperty(default="*.hxa", options={"HIDDEN"})

    def execute(self, context):
        hxa_dict = export_payload()
        if not hxa_valid.hxa_util_validate(hxa_dict):
            self.report({"ERROR"}, f"{self.filepath} couldn't pass validation")
            return {"CANCELLED"}

        import json
        import os

        jsonname = f"testdump_giraffearmature_{hxa_util.timestamp()}.json"
        with open(jsonname, "w", encoding="utf8") as f:
            json.dump(hxa_dict, f, indent=4)
        print(f"> test dump written: {os.getcwd()}{os.path.sep}{jsonname}")
        hxa_rw.dict_to_hxa(
            self.filepath, hxa_dict, False
        )  # don't forget to pipe(?) silent through

        return {"FINISHED"}


def meta__armature_data(arm_ob, arm):
    """
    Packs all the armature(bones) data into HxA meta fields.
    """
    arm_location = [x for x in arm_ob.location]
    arm_scale = [x for x in arm_ob.scale]
    bone_count = len(arm.bones)

    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode="EDIT")
    heads = [list(x.head) for x in arm.edit_bones]
    tails = [list(x.tail) for x in arm.edit_bones]
    bpy.ops.object.mode_set(mode="OBJECT")

    print("Edit bone heads")
    for h in heads:
        print(h)
    print("Edit bone tails")
    for t in tails:
        print(t)

    heads = hxa_util.flatten_list(heads)
    tails = hxa_util.flatten_list(tails)
    names = [x.name for x in arm.bones]
    parents = [x.parent.name if x.parent else "" for x in arm.bones]

    meta_armature_data_entries = []

    meta_arm_location_name = "meta armature location"
    meta_arm_location = {
        "name_length": len(meta_arm_location_name),
        "name": meta_arm_location_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": len(arm_location),
        "data": arm_location,
    }
    meta_armature_data_entries.append(meta_arm_location)

    meta_arm_scale_name = "meta armature scale"
    meta_arm_scale = {
        "name_length": len(meta_arm_scale_name),
        "name": meta_arm_scale_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": len(arm_scale),
        "data": arm_scale,
    }
    meta_armature_data_entries.append(meta_arm_scale)

    meta_bonesheads_name = "meta bones heads"
    meta_bones_heads = {
        "name_length": len(meta_bonesheads_name),
        "name": meta_bonesheads_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": bone_count * 3,
        "data": heads,
    }
    meta_armature_data_entries.append(meta_bones_heads)

    meta_bonestails_name = "meta bones tails"
    meta_bones_tails = {
        "name_length": len(meta_bonestails_name),
        "name": meta_bonestails_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": bone_count * 3,
        "data": tails,
    }
    meta_armature_data_entries.append(meta_bones_tails)

    # a list of strings needs its own meta container.
    bone_names_entries = []
    for i in range(bone_count):
        bone = {
            "name_length": 0,
            "name": "",
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_TEXT),
            "array_length": len(names[i]),
            "data": names[i],
        }
        bone_names_entries.append(bone)

    meta_bonesnames_name = "meta bones names"
    meta_bones_names = {
        "name_length": len(meta_bonesnames_name),
        "name": meta_bonesnames_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
        "array_length": bone_count,
        "data": bone_names_entries,
    }
    meta_armature_data_entries.append(meta_bones_names)

    bone_parents_entries = []
    for i in range(bone_count):
        parent = {
            "name_length": 0,
            "name": "",
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_TEXT),
            "array_length": len(parents[i]),
            "data": parents[i],
        }
        bone_parents_entries.append(parent)

    meta_bonesparents_name = "meta bones parents"
    meta_bones_parents = {
        "name_length": len(meta_bonesparents_name),
        "name": meta_bonesparents_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
        "array_length": bone_count,
        "data": bone_parents_entries,
    }
    meta_armature_data_entries.append(meta_bones_parents)

    meta_armature_data_name = "meta armature data"
    meta_armature_data = {
        "name_length": len(meta_armature_data_name),
        "name": meta_armature_data_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
        "array_length": len(meta_armature_data_entries),
        "data": meta_armature_data_entries,
    }

    return meta_armature_data


def extract_weights(ob):
    vgroups = ob.vertex_groups
    vcount = len(ob.data.vertices)

    indexes_biglist = []
    weights_biglist = []
    for vgroup in vgroups:
        indexes = []
        weights = []
        for i in range(vcount):
            try:
                weights.append(vgroup.weight(i))
                indexes.append(i)
            except Exception as e:
                print(f"Weights append exception: {e.message}, {e.args}")
                pass
        indexes_biglist.append(indexes)
        weights_biglist.append(weights)

    return (indexes_biglist, weights_biglist)


def hxapy_type_meta(typ):
    """Which HxA meta type will we use to write this type into the export file?"""
    if typ == int:
        return hxa.HXA_MDT_INT64
    elif typ == float:
        return hxa.HXA_MDT_DOUBLE
    elif typ == str:
        return hxa.HXA_MDT_TEXT


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
    print(verts)
    print(references)

    bm.free()

    hxa_dict = {}
    hxa_dict["version"] = hxa.HXA_VERSION_FORMAT
    hxa_dict["node_count"] = 1

    # *** Meta data
    meta_data = []

    # ** Mesh(meta) data
    meta_meshdata_entries = []

    meta_objectname_name = "meta objectname"
    meta_objectname = {
        "name_length": len(meta_objectname_name),
        "name": meta_objectname_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_TEXT),
        "array_length": len(ob_mesh.name),
        "data": ob_mesh.name,
    }
    meta_meshdata_entries.append(meta_objectname)

    meta_meshname_name = "meta meshname"
    meta_meshname = {
        "name_length": len(meta_meshname_name),
        "name": meta_meshname_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_TEXT),
        "array_length": len(me.name),
        "data": me.name,
    }
    meta_meshdata_entries.append(meta_meshname)

    meta_location_name = "meta location"
    meta_location = {
        "name_length": len(meta_location_name),
        "name": meta_location_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": 3,
        "data": [x for x in bpy.context.object.location],
    }
    meta_meshdata_entries.append(meta_location)

    meta_scale_name = "meta scale"
    meta_scale = {
        "name_length": len(meta_scale_name),
        "name": meta_scale_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
        "array_length": 3,
        "data": [x for x in bpy.context.object.scale],
    }
    meta_meshdata_entries.append(meta_scale)

    meta_meshdata_name = "meta mesh data"
    meta_meshdata = {
        "name_length": len(meta_meshdata_name),
        "name": meta_meshdata_name,
        "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
        "array_length": len(meta_meshdata_entries),
        "data": meta_meshdata_entries,
    }
    meta_data.append(meta_meshdata)

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

            shapekey = {
                "name_length": len(name),
                "name": name,
                "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
                "array_length": vert_count * 3,
                "data": shapekey_values,
            }
            meta_shapekeys_data.append(shapekey)

        meta_shapekeys_name = "meta shapekeys"
        meta_shapekeys = {
            "name_length": len(meta_shapekeys_name),
            "name": meta_shapekeys_name,
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
            "array_length": len(object_shapekeys),
            "data": meta_shapekeys_data,
        }
        meta_data.append(meta_shapekeys)

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
            meta_weightindexes_data = []
            for i in range(vgroup_count):
                ind_data = {
                    "name_length": 0,
                    "name": "",
                    "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_INT64),
                    "array_length": len(indexes_list[i]),
                    "data": indexes_list[i],
                }
                meta_weightindexes_data.append(ind_data)

            meta_weightindexes_name = "meta weight indexes"
            meta_weightindexes = {
                "name_length": len(meta_weightindexes_name),
                "name": meta_weightindexes_name,
                "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
                "array_length": vgroup_count,
                "data": meta_weightindexes_data,
            }
            meta_data.append(meta_weightindexes)

            # vertex weights
            meta_vertexweights_data = []
            for i in range(vgroup_count):
                vw_data = {
                    "name_length": 0,
                    "name": "",
                    "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
                    "array_length": len(weights_list[i]),
                    "data": weights_list[i],
                }
                meta_vertexweights_data.append(vw_data)

            meta_vertexweights_name = "meta vertex weights"
            meta_vertexweights = {
                "name_length": len(meta_vertexweights_name),
                "name": meta_vertexweights_name,
                "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
                "array_length": vgroup_count,
                "data": meta_vertexweights_data,
            }
            meta_data.append(meta_vertexweights)

    # ** creases
    creases = [x.crease for x in me.edges]
    edges = [list(e.vertices) for e in me.edges]
    crease_tuples = []
    for i in range(len(edges)):
        crease_tuples.append((edges[i], creases[i]))

    crease_tuples = sorted(crease_tuples, key=lambda t: (t[0][0], t[0][1]))

    print(f"> {edges}")
    # sorted_edges = sorted(edges, key = lambda x: (x[0], x[1]))
    sorted_edges, sorted_creases = zip(*crease_tuples)
    edge_verts = hxa_util.flatten_list(sorted_edges)
    print(f"Edge verts: {edge_verts}")

    # check for !=0 creases
    creases_present = len([x != 0 for x in creases]) > 0
    if creases_present:
        meta_creases_data_entries = []

        meta_creases_verts = {
            "name_length": 0,
            "name": "",
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_INT64),
            "array_length": len(edge_verts),
            "data": edge_verts,
        }
        meta_creases_data_entries.append(meta_creases_verts)

        meta_creases_values = {
            "name_length": 0,
            "name": "",
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_DOUBLE),
            "array_length": len(sorted_creases),
            "data": sorted_creases,
        }
        meta_creases_data_entries.append(meta_creases_values)

        meta_creases_data_name = "meta creases"
        meta_creases_data = {
            "name_length": len(meta_creases_data_name),
            "name": meta_creases_data_name,
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
            "array_length": len(meta_creases_data_entries),
            "data": meta_creases_data_entries,
        }
        meta_data.append(meta_creases_data)

    # ** custom props
    custom_props = list(ob_mesh.keys())
    if len(custom_props) > 0:
        meta_customprops_data = []
        for cp in custom_props:
            customprop = ob_mesh[cp]
            import idprop

            if type(customprop) == idprop.types.IDPropertyArray:
                al = len(customprop)
                mtype = hxapy_type_meta(type(customprop[0]))
                data = list(customprop)
            else:
                mtype = hxapy_type_meta(type(customprop))
                data = customprop
                if mtype == hxa.HXA_MDT_TEXT:
                    al = len(data)
                else:
                    al = 1

            meta_cp_name = cp
            meta_cp = {
                "name_length": len(meta_cp_name),
                "name": meta_cp_name,
                "type": hxa.hxa_meta_data_type(mtype),
                "array_length": al,
                "data": data,
            }
            print(meta_cp)
            meta_customprops_data.append(meta_cp)

        meta_customprops_name = "meta custom properties"
        meta_customprops = {
            "name_length": len(meta_customprops_name),
            "name": meta_customprops_name,
            "type": hxa.hxa_meta_data_type(hxa.HXA_MDT_META),
            "array_length": len(meta_customprops_data),
            "data": meta_customprops_data,
        }
        meta_data.append(meta_customprops)

    # *** Mesh(geometry) data
    vertex_layer = {
        "name_length": len(hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME),
        "name": hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME,
        "components": hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS,
        "type": hxa.hxa_data_type(hxa.HXA_LDT_FLOAT),
        "data": verts,
    }
    vert_stack = {"layer_count": 1, "layers": [vertex_layer]}

    reference_layer = {
        "name_length": len(hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME),
        "name": hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME,
        "components": hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_COMPONENTS,
        "type": hxa.hxa_data_type(hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_TYPE),
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
        "type": hxa.hxa_node_type(hxa.HXA_NT_GEOMETRY),
        "meta_data_count": len(meta_data),
        "meta_data": meta_data,
        "content": content,
    }
    hxa_dict["nodes"] = [node]
    return hxa_dict

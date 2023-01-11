
#   This is a Python version of the original HxA header, written by Soslan Guchmazov (@SoslanGM).
#   The original HxA header, as well as the HxA format itself, both for C programming language,
# was developed by Eskil Steenberg (@quelsolaar).
#   You can find the original HxA readme at https://github.com/quelsolaar/HxA#readme,
# and the repository with this header(as well as source code for my Import/Export addon for Blender)
# is at https://github.com/SoslanGM/HxApy_Blender_import-export

HXA_VERSION_API = "0.3"
HXA_VERSION_FORMAT = 3


HXA_NAME_MAX_LENGTH = 255

# HXANodeType
(HXA_NT_META_ONLY, HXA_NT_GEOMETRY, HXA_NT_IMAGE, HXA_NT_COUNT) = range(0, 4)


def HXANodeType(node_type):
    if (node_type >= HXA_NT_COUNT):
        print("! Incorrect node type!")
        exit()

    if (node_type == HXA_NT_META_ONLY):
        return "HXA_NT_META_ONLY"
    elif (node_type == HXA_NT_GEOMETRY):
        return "HXA_NT_GEOMETRY"
    elif (node_type == HXA_NT_IMAGE):
        return "HXA_NT_IMAGE"


HXANodeTypeDict = {
    "HXA_NT_META_ONLY": HXA_NT_META_ONLY,
    "HXA_NT_GEOMETRY":  HXA_NT_GEOMETRY,
    "HXA_NT_IMAGE":     HXA_NT_IMAGE,
    "HXA_NT_COUNT":     HXA_NT_COUNT
}


# HXAImageType
(HXA_IT_CUBE_IMAGE, HXA_IT_1D_IMAGE, HXA_IT_2D_IMAGE, HXA_IT_3D_IMAGE) = range(0, 4)

# HXAMetaDataType
(HXA_MDT_INT64, HXA_MDT_DOUBLE, HXA_MDT_NODE, HXA_MDT_TEXT, HXA_MDT_BINARY, HXA_MDT_META, HXA_MDT_COUNT) = range(0, 7)


def HXAMetaDataType(data_type):
    if (data_type == HXA_MDT_INT64):
        return "HXA_MDT_INT64"
    elif (data_type == HXA_MDT_DOUBLE):
        return "HXA_MDT_DOUBLE"
    elif (data_type == HXA_MDT_NODE):
        return "HXA_MDT_NODE"
    elif (data_type == HXA_MDT_TEXT):
        return "HXA_MDT_TEXT"
    elif (data_type == HXA_MDT_BINARY):
        return "HXA_MDT_BINARY"
    elif (data_type == HXA_MDT_META):
        return "HXA_MDT_META"


HXAMetaDataTypeDict = {
    "HXA_MDT_INT64":  HXA_MDT_INT64,
    "HXA_MDT_DOUBLE": HXA_MDT_DOUBLE,
    "HXA_MDT_NODE":   HXA_MDT_NODE,
    "HXA_MDT_TEXT":   HXA_MDT_TEXT,
    "HXA_MDT_BINARY": HXA_MDT_BINARY,
    "HXA_MDT_META":   HXA_MDT_META
}


# HXALayerDataType
(HXA_LDT_UINT8, HXA_LDT_INT32, HXA_LDT_FLOAT, HXA_LDT_DOUBLE, HXA_LDT_COUNT) = range(0, 5)


def HXADataType(data_type: int) -> str:
    if (data_type == HXA_LDT_UINT8):
        return "HXA_LDT_UINT8"
    elif (data_type == HXA_LDT_INT32):
        return "HXA_LDT_INT32"
    elif (data_type == HXA_LDT_FLOAT):
        return "HXA_LDT_FLOAT"
    elif (data_type == HXA_LDT_DOUBLE):
        return "HXA_LDT_DOUBLE"


HXADataTypeDict = {
    "HXA_LDT_UINT8":  HXA_LDT_UINT8,
    "HXA_LDT_INT32":  HXA_LDT_INT32,
    "HXA_LDT_FLOAT":  HXA_LDT_FLOAT,
    "HXA_LDT_DOUBLE": HXA_LDT_DOUBLE,
    "HXA_LDT_COUNT":  HXA_LDT_COUNT,
}


# - Hard conventions

HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME       = "vertex"
HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_ID         = 0
HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS = 3
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME       = "reference"
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_ID         = 0
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_COMPONENTS = 1
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_TYPE       = HXA_LDT_INT32
HXA_CONVENTION_HARD_EDGE_NEIGHBOUR_LAYER_NAME    = "neighbour"
HXA_CONVENTION_HARD_EDGE_NEIGHBOUR_LAYER_TYPE    = HXA_LDT_INT32


# - Soft conventions
# geometry layers
HXA_CONVENTION_SOFT_LAYER_SEQUENCE0      = "sequence"
HXA_CONVENTION_SOFT_LAYER_UV0            = "uv"
HXA_CONVENTION_SOFT_LAYER_NORMALS        = "normal"
HXA_CONVENTION_SOFT_LAYER_BINORMAL       = "binormal"
HXA_CONVENTION_SOFT_LAYER_TANGENT        = "tangent"
HXA_CONVENTION_SOFT_LAYER_COLOR          = "color"
HXA_CONVENTION_SOFT_LAYER_CREASES        = "creases"
HXA_CONVENTION_SOFT_LAYER_SELECTION      = "select"
HXA_CONVENTION_SOFT_LAYER_SKIN_WEIGHT    = "skining_weight"
HXA_CONVENTION_SOFT_LAYER_SKIN_REFERENCE = "skining_reference"
HXA_CONVENTION_SOFT_LAYER_BLENDSHAPE     = "blendshape"
HXA_CONVENTION_SOFT_LAYER_ADD_BLENDSHAPE = "addblendshape"
HXA_CONVENTION_SOFT_LAYER_MATERIAL_ID    = "material"
HXA_CONVENTION_SOFT_LAYER_GROUP_ID       = "group"

# Image layers
HXA_CONVENTION_SOFT_ALBEDO            = "albedo"
HXA_CONVENTION_SOFT_LIGHT             = "light"
HXA_CONVENTION_SOFT_DISPLACEMENT      = "displacement"
HXA_CONVENTION_SOFT_DISTORTION        = "distortion"
HXA_CONVENTION_SOFT_AMBIENT_OCCLUSION = "ambient_occlusion"

# tags layers
HXA_CONVENTION_SOFT_NAME      = "name"
HXA_CONVENTION_SOFT_TRANSFORM = "transform"

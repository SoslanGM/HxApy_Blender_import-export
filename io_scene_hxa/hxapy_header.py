#   This is a Python version of the original HxA header, written by Soslan Guchmazov (@SoslanGM).
#   The original HxA header, as well as the HxA format itself, both for C programming language,
# was developed by Eskil Steenberg (@quelsolaar).
#   You can find the original HxA readme at https://github.com/quelsolaar/HxA#readme,
# and the repository with this header(as well as source code for my Import/Export addon for Blender)
# is at https://github.com/SoslanGM/HxApy_Blender_import-export

# Big thanks to @Scurest for help with the feedback, suggestions and fixes.


from enum import IntEnum

HXA_VERSION_API = "0.3"
HXA_VERSION_FORMAT = 3


HXA_NAME_MAX_LENGTH = 255


class HXANodeType(IntEnum):
    HXA_NT_META_ONLY = 0
    HXA_NT_GEOMETRY = 1
    HXA_NT_IMAGE = 2
    HXA_NT_COUNT = 3


class HXAImageType(IntEnum):
    HXA_IT_CUBE_IMAGE = 0
    HXA_IT_1D_IMAGE = 1
    HXA_IT_2D_IMAGE = 2
    HXA_IT_3D_IMAGE = 3


class HXAMetaDataType(IntEnum):
    HXA_MDT_INT64 = 0
    HXA_MDT_DOUBLE = 1
    HXA_MDT_NODE = 2
    HXA_MDT_TEXT = 3
    HXA_MDT_BINARY = 4
    HXA_MDT_META = 5
    HXA_MDT_COUNT = 6


class HXALayerDataType(IntEnum):
    HXA_LDT_UINT8 = 0
    HXA_LDT_INT32 = 1
    HXA_LDT_FLOAT = 2
    HXA_LDT_DOUBLE = 3
    HXA_LDT_COUNT = 4


# - Hard conventions

HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME = "vertex"
HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_ID = 0
HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS = 3
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME = "reference"
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_ID = 0
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_COMPONENTS = 1
HXA_CONVENTION_HARD_BASE_CORNER_LAYER_TYPE = HXALayerDataType["HXA_LDT_INT32"].value
HXA_CONVENTION_HARD_EDGE_NEIGHBOUR_LAYER_NAME = "neighbour"
HXA_CONVENTION_HARD_EDGE_NEIGHBOUR_LAYER_TYPE = HXALayerDataType["HXA_LDT_INT32"].value


# - Soft conventions
# geometry layers
HXA_CONVENTION_SOFT_LAYER_SEQUENCE0 = "sequence"
HXA_CONVENTION_SOFT_LAYER_UV0 = "uv"
HXA_CONVENTION_SOFT_LAYER_NORMALS = "normal"
HXA_CONVENTION_SOFT_LAYER_BINORMAL = "binormal"
HXA_CONVENTION_SOFT_LAYER_TANGENT = "tangent"
HXA_CONVENTION_SOFT_LAYER_COLOR = "color"
HXA_CONVENTION_SOFT_LAYER_CREASES = "creases"
HXA_CONVENTION_SOFT_LAYER_SELECTION = "select"
HXA_CONVENTION_SOFT_LAYER_SKIN_WEIGHT = "skining_weight"
HXA_CONVENTION_SOFT_LAYER_SKIN_REFERENCE = "skining_reference"
HXA_CONVENTION_SOFT_LAYER_BLENDSHAPE = "blendshape"
HXA_CONVENTION_SOFT_LAYER_ADD_BLENDSHAPE = "addblendshape"
HXA_CONVENTION_SOFT_LAYER_MATERIAL_ID = "material"
HXA_CONVENTION_SOFT_LAYER_GROUP_ID = "group"

# Image layers
HXA_CONVENTION_SOFT_ALBEDO = "albedo"
HXA_CONVENTION_SOFT_LIGHT = "light"
HXA_CONVENTION_SOFT_DISPLACEMENT = "displacement"
HXA_CONVENTION_SOFT_DISTORTION = "distortion"
HXA_CONVENTION_SOFT_AMBIENT_OCCLUSION = "ambient_occlusion"

# tags layers
HXA_CONVENTION_SOFT_NAME = "name"
HXA_CONVENTION_SOFT_TRANSFORM = "transform"

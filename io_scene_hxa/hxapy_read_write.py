from . import hxapy_header as hxa

import logging

log = logging.getLogger(__name__)

# *** Logging functions (start)


def log_meta(meta):
    log.debug("Meta:")
    log.debug(f" - name: {meta['name']}")
    log.debug(f" - type: {hxa.HXAMetaDataType(meta['type']).name}")
    log.debug(f" - array_length: {len(meta['data'])}")
    log.debug(f" - data: {meta['data']}")


def log_layer(layer):
    log.debug(f" - name: {layer['name']}")
    log.debug(f" - components: {layer['components']}")
    log.debug(f" - data_type: {hxa.HXALayerDataType(layer['type']).name}")
    log.debug(f" - data: {layer['data']}\n")


# *** Logging functions (end)


# *** Read functions (start)

import struct
import array


def read_u8(f):
    return f.read(1)[0]


def read_u32(f):
    return struct.unpack("<I", f.read(4))[0]


def read_name(f):
    l = read_u8(f)
    return f.read(l).decode()


def read_meta(f):
    meta = {}
    meta["name"] = read_name(f)
    mtype = hxa.HXAMetaDataType(read_u8(f))
    length = read_u32(f)

    if mtype == hxa.HXAMetaDataType.HXA_MDT_INT64:
        data = read_array1(f, "Q", length)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_DOUBLE:
        data = read_array1(f, "d", length)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_NODE:
        data = read_array1(f, "I", length)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_TEXT:
        data = f.read(length).decode()
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_BINARY:
        data = f.read(length)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_META:
        data = [read_meta(f) for _ in range(length)]

    meta["type"] = mtype
    meta["data"] = data
    return meta


def read_array1(f, typecode, length):
    arr = read_array(f, typecode, length)
    return arr if len(arr) != 1 else arr[0]


def read_array(f, typecode, length):
    arr = array.array(typecode)
    arr.fromfile(f, length)
    return arr


def read_layer(f, count):
    layer = {}
    layer["name"] = read_name(f)
    layer["components"] = read_u8(f)
    dtype = hxa.HXALayerDataType(read_u8(f))
    layer["type"] = dtype

    length = count * layer["components"]

    if dtype == hxa.HXALayerDataType.HXA_LDT_UINT8:
        data = read_array(f, "B", length)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_INT32:
        data = read_array(f, "i", length)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_FLOAT:
        data = read_array(f, "f", length)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_DOUBLE:
        data = read_array(f, "d", length)

    layer["data"] = data
    log_layer(layer)
    return layer


def read_layerstack(f, count):
    layerstack = {}

    layerstack["layer_count"] = read_u32(f)
    layerstack["layers"] = [
        read_layer(f, count) for _ in range(layerstack["layer_count"])
    ]

    return layerstack


def read_node(f):
    node = {}
    node_type = hxa.HXANodeType(read_u8(f))
    node["type"] = node_type
    node["meta_data_count"] = read_u32(f)
    node["meta_data"] = [read_meta(f) for i in range(node["meta_data_count"])]

    content = {}
    if node["type"] == hxa.HXANodeType.HXA_NT_GEOMETRY:
        content["vertex_count"] = read_u32(f)
        content["vertex_stack"] = read_layerstack(f, content["vertex_count"])

        content["edge_corner_count"] = read_u32(f)
        content["corner_stack"] = read_layerstack(f, content["edge_corner_count"])
        content["edge_stack"] = read_layerstack(f, content["edge_corner_count"])

        content["face_count"] = read_u32(f)
        content["face_stack"] = read_layerstack(f, content["face_count"])

    elif node_type == hxa.HXANodeType.HXA_NT_IMAGE:
        log.debug("! Not processing images yet\n")

    node["content"] = content
    return node


def read_hxa(f):
    magic = f.read(4)
    if magic != b"HxA\0":
        raise RuntimeError(
            "HXA Error: file {f.name} not a HxA file(incorrect magic number"
        )

    hxa_file = {}
    hxa_file["version"] = read_u8(f)
    hxa_file["node_count"] = read_u32(f)

    hxa_file["nodes"] = [read_node(f) for i in range(hxa_file["node_count"])]

    return hxa_file


# *** Read functions (end)


# *** Write functions (start)


def write_str(f, s):
    f.write(s.encode())


def write_u8(f, v):
    f.write(struct.pack("<B", v))


def write_u32(f, v):
    f.write(struct.pack("<I", v))


def ensure_array(v):
    """If v isn't already an array, make it a one-element list"""
    try:
        _ = len(v)
        has_len = True
    except Exception:
        has_len = False

    is_array = not isinstance(v, dict) and has_len
    return v if is_array else [v]


def write_array(f, typecode, arr):
    if isinstance(arr, array.array) and arr.typecode == typecode:
        arr.tofile(f)
    else:
        fmt = f"<{len(arr)}{typecode}"
        f.write(struct.pack(fmt, *arr))


def write_meta(f, meta):
    mtype = meta["type"]
    data = ensure_array(meta["data"])

    write_name(f, meta["name"])
    write_u8(f, mtype)
    write_u32(f, len(meta["data"]))

    log_meta(meta)

    if mtype == hxa.HXAMetaDataType.HXA_MDT_INT64:
        write_array(f, "Q", data)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_DOUBLE:
        write_array(f, "d", data)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_NODE:
        write_array(f, "I", data)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_TEXT:
        write_str(f, data)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_BINARY:
        write_array(f, "B", data)
    elif mtype == hxa.HXAMetaDataType.HXA_MDT_META:
        for child_meta in data:
            write_meta(f, child_meta)
    else:
        assert False  # might put a HxA Runtime Error message here


def write_name(f, name):
    assert len(name) < hxa.HXA_NAME_MAX_LENGTH
    write_u8(f, len(name))
    write_str(f, name)


def write_layer(f, layer):
    dtype = layer["type"]
    data = layer["data"]

    l = len(layer["name"])
    write_name(f, layer["name"])
    write_u8(f, layer["components"])
    write_u8(f, dtype)

    if dtype == hxa.HXALayerDataType.HXA_LDT_UINT8:
        write_array(f, "B", data)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_INT32:
        write_array(f, "i", data)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_FLOAT:
        write_array(f, "f", data)
    elif dtype == hxa.HXALayerDataType.HXA_LDT_DOUBLE:
        write_array(f, "d", data)
    else:
        assert False  # might put a HxA Runtime Error message here


def write_layerstack(f, stack):
    write_u32(f, len(stack["layers"]))

    for layer in stack["layers"]:
        write_layer(f, layer)


def write_node(f, node):
    write_u8(f, node["type"])
    write_u32(f, node["meta_data_count"])

    for meta in node["meta_data"]:
        write_meta(f, meta)

    content = node["content"]
    if node["type"] == hxa.HXANodeType.HXA_NT_GEOMETRY:
        write_u32(f, content["vertex_count"])
        write_layerstack(f, content["vertex_stack"])
        write_u32(f, content["edge_corner_count"])
        write_layerstack(f, content["corner_stack"])
        write_layerstack(f, content["edge_stack"])
        write_u32(f, content["face_count"])
        write_layerstack(f, content["face_stack"])

    # elif node["type"] == hxa.HXANodeType.IMAGE:
    #     pass


def write_hxa(f, hxa_dict):
    f.write(b"HxA\0")
    write_u8(f, hxa_dict["version"])
    write_u32(f, len(hxa_dict["nodes"]))

    log.debug(f"HxA version: {hxa_dict['version']}")
    log.debug(f"Node count: {len(hxa_dict['nodes'])}")
    node_counter = 0
    for node in hxa_dict["nodes"]:
        log.debug(f"Node #{node_counter}, {node['type']}")
        node_counter += 1
        write_node(f, node)


# *** Write functions (end)

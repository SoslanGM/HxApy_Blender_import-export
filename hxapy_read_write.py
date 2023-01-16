
from . import hxapy_header as hxa


# *** Read functions (start)

import struct


def su(_format, f):
    try:
        return struct.unpack(_format, f.read(struct.calcsize(_format)))
    except struct.error:
        print(f"HXA Error: File {f.name} unexpectedly ended")
        exit()


def string(len, f):
    _f = f"<{len}s"
    s = su(_f, f)[0].decode('utf8')

    return s


def u8(f):
    _f = "<B"
    return su(_f, f)[0]


def u32(f):
    _f = "<I"
    return su(_f, f)[0]


def u64(f):
    _f = "<Q"
    return su(_f, f)[0]


def meta_value(mtype, array_length, f):
    if (mtype == hxa.HXA_MDT_INT64):
        _f = "<"+"Q"*array_length
    elif (mtype == hxa.HXA_MDT_DOUBLE):
        _f = "<"+"d"*array_length
    elif (mtype == hxa.HXA_MDT_NODE):
        _f = "<"+"I"*array_length
    elif (mtype == hxa.HXA_MDT_TEXT):
        return string(array_length, f)
    elif (mtype == hxa.HXA_MDT_BINARY):
        _f = "<"+"B"*array_length

    if (array_length == 1):
        return su(_f, f)[0]
    if (array_length > 1):
        return list(su(_f, f))


def read_metas(f, silent=True):
    name_length  = u8(f)
    name         = string(name_length, f)
    mtype        = u8(f)
    array_length = u32(f)

    if (mtype >= hxa.HXA_MDT_COUNT):
        print(f"HXA Error: File {f.name} has meta data of type {mtype}. There is only {hxa.HXA_MDT_COUNT} \
              types of meta data\n")
        exit()

    if not silent:
        print("Meta:")
        print(f" - name_length: {name_length}")
        print(f" - name: {name}")
        print(f" - type: {hxa.hxa_meta_data_type(mtype)}")
        print(f" - array_length: {array_length}")

    if ((array_length > 1) and not (mtype == hxa.HXA_MDT_TEXT)):
        data = []
    else:
        data = None

    if (mtype < hxa.HXA_MDT_META):
        data = meta_value(mtype, array_length, f)
        if not silent:
            print(f" - Data: {data}")
    elif (mtype == hxa.HXA_MDT_META):
        if (array_length > 1):
            for j in range(array_length):
                d = read_metas(f, silent)
                data.append(d)
        else:
            d = read_metas(f, silent)
            data = d

    meta_d = {
        "name_length":  name_length,
        "name":         name,
        "type":         hxa.hxa_meta_data_type(mtype),
        "array_length": array_length,
        "data":         data
    }
    return meta_d


def data_value(dtype, components, count, f):
    if (dtype == hxa.HXA_LDT_UINT8):
        _f = "<"+"B"*components*count
    if (dtype == hxa.HXA_LDT_INT32):
        _f = "<"+"i"*components*count
    if (dtype == hxa.HXA_LDT_FLOAT):
        _f = "<"+"f"*components*count
    if (dtype == hxa.HXA_LDT_DOUBLE):
        _f = "<"+"d"*components*count

    if (components * count == 1):
        return su(_f, f)[0]
    if (components * count > 1):
        return list(su(_f, f))


def layer_dict(name_length, name, components, dtype, data):
    d = {
        "name_length": name_length,
        "name":        name,
        "components":  components,
        "type":        dtype,
        "data":        data
    }
    return d


def layer_stack(count, f, silent: bool = True):
    layer_count = u32(f)
    if not silent:
        print(f" - stack layer count: {layer_count}")

    layerstack_d = {"layer_count": layer_count}
    layers = []

    for i in range(layer_count):
        name_length = u8(f)
        name        = string(name_length, f)
        components  = u8(f)
        dtype       = u8(f)

        if (dtype >= hxa.HXA_LDT_COUNT):
            print(f"HXA Error: File {f.name} has a layer with type {dtype}. No such type is supported")
            exit()

        data = data_value(dtype, components, count, f)

        if not silent:
            print(f"layer {i}:")
            print(f" - name_length: {name_length}")
            print(f" - name: {name}")
            print(f" - components: {components}")
            print(f" - data_type: {hxa.hxa_data_type(dtype)}")
            print(f" - data: {data}\n")

        layer_dictionary = layer_dict(name_length, name, components, hxa.hxa_data_type(dtype), data)

        layers.append(layer_dictionary)

    layerstack_d['layers'] = layers
    return layerstack_d


def hxa_to_dict(filename, silent=True):
    try:
        f = open(filename, "rb")
    except OSError:
        print(f"HXA Error: File {filename} could not be open for reading\n")
        exit()

    if ('HxA\x00' != string(4, f)):
        print(f"HXA Error: File {f.name} is not a HxA file (incorrect magic number)\n")
        exit()

    hxa_file = {}

    version = u8(f)
    hxa_file['version'] = version
    node_count = u32(f)
    hxa_file['node_count'] = node_count

    if not silent:
        print(f"Version: {version}")
        print(f"Node count: {node_count}")

    hxa_file['nodes'] = []
    for nc in range(node_count):
        node_type = u8(f)
        if (node_type >= hxa.HXA_NT_COUNT):
            print(f"HXA Error: File {f.name} has a node of type {node_type}\n")
            exit()

        meta_data_count = u32(f)
        meta_data = []

        if not silent:
            print(f"Node type: {hxa.hxa_node_type(node_type)}")
            print(f"Meta count: {meta_data_count}")

        for mc in range(meta_data_count):
            meta = read_metas(f, False)
            meta_data.append(meta)

        content = {}
        if (node_type == hxa.HXA_NT_GEOMETRY):
            vertex_count      = u32(f)
            vertex_stack      = layer_stack(vertex_count, f, silent)
            edge_corner_count = u32(f)
            corner_stack      = layer_stack(edge_corner_count, f, silent)
            edge_stack        = layer_stack(edge_corner_count, f, silent)
            face_count        = u32(f)
            face_stack        = layer_stack(face_count, f, silent)

            content['vertex_count']      = vertex_count
            content['vertex_stack']      = vertex_stack
            content['edge_corner_count'] = edge_corner_count
            content['corner_stack']      = corner_stack
            content['edge_stack']        = edge_stack
            content['face_count']        = face_count
            content['face_stack']        = face_stack

        elif (node_type == hxa.HXA_NT_IMAGE):
            print("! Not processing images yet\n")

        node_d = {
            "type":            hxa.hxa_node_type(node_type),
            "meta_data_count": meta_data_count,
            "meta_data":       meta_data,
            "content":         content
        }
        hxa_file['nodes'].append(node_d)

    f.close()
    return hxa_file

# *** Read functions (end)


# *** Write functions (start)

def write_s(f, length, s):
    f.write(struct.pack(f"<{length}s", s.encode('utf8')))


def write_u8(f, v):
    _f = "<B"
    f.write(struct.pack(_f, v))


def write_u32(f, v):
    print(f"{type(v)}, {v}")
    _f = "<I"
    f.write(struct.pack(_f, v))


def write_data_value(f, dtype, data):
    ld = len(data)
    if (dtype == hxa.HXA_LDT_UINT8):
        _f = "<"+"B"*ld
    if (dtype == hxa.HXA_LDT_INT32):
        _f = "<"+"i"*ld
    if (dtype == hxa.HXA_LDT_FLOAT):
        _f = "<"+"f"*ld
    if (dtype == hxa.HXA_LDT_DOUBLE):
        _f = "<"+"d"*ld

    f.write(struct.pack(_f, *data))


def write_meta_value(f, mtype, array_length, data):
    if (mtype == hxa.HXA_MDT_INT64):
        _f = "<"+"Q"*array_length
    elif (mtype == hxa.HXA_MDT_DOUBLE):
        _f = "<"+"d"*array_length
    elif (mtype == hxa.HXA_MDT_NODE):
        _f = "<"+"I"*array_length
    elif (mtype == hxa.HXA_MDT_TEXT):
        _f = f"<{array_length}s"
        f.write(struct.pack(_f, data.encode('utf8')))
        return
    elif (mtype == hxa.HXA_MDT_BINARY):
        _f = "<"+"B"*array_length

    if (array_length > 1):
        f.write(struct.pack(_f, *data))
    elif (array_length == 1):
        f.write(struct.pack(_f, data))


def write_metas(f, meta, silent=True):
    mtype = hxa.hxa_meta_data_type_dict[meta['type']]

    write_u8(f, meta['name_length'])
    write_s(f, meta['name_length'], meta['name'])
    write_u8(f, mtype)
    write_u32(f, meta['array_length'])

    if not silent:
        print(f"Name length: {meta['name_length']}")
        print(f"Name: {meta['name']}")
        print(f"Meta type: {meta['type']}")
        print(f"Array length: {meta['array_length']}")
        print(f"Data: {meta['data']}")

    array_length = meta['array_length']
    if (mtype < hxa.HXA_MDT_META):
        write_meta_value(f, mtype, array_length, meta['data'])
    elif (mtype == hxa.HXA_MDT_META):
        if (array_length > 1):
            for al in range(array_length):
                write_metas(f, meta['data'][al], silent)
        else:
            write_metas(f, meta['data'], silent)


def write_layerstack(f, stack):
    layer_count = stack['layer_count']
    write_u32(f, layer_count)
    for lc in range(layer_count):
        layer = stack['layers'][lc]
        write_u8(f, layer['name_length'])
        write_s(f, layer['name_length'], layer['name'])
        write_u8(f, layer['components'])
        dtype = hxa.hxa_data_type_dict[layer['type']]
        write_u8(f, dtype)
        write_data_value(f, dtype, layer['data'])


def dict_to_hxa(filename, hxa_dict, silent=True):
    try:
        f = open(filename, "wb")
    except OSError:
        print(f"HXA Error: File {filename} could not be open for reading\n")
        exit()

    write_s(f, 4, "HxA"+'\x00')

    write_u8(f, hxa_dict['version'])
    write_u32(f, hxa_dict['node_count'])

    if not silent:
        print(f"HxA version: {hxa_dict['version']}")
        print(f"Node count: {hxa_dict['node_count']}")

    for nc in range(hxa_dict['node_count']):
        node = hxa_dict['nodes'][nc]

        print(f"{nc}, {node['type']}")

        write_u8(f, hxa.hxa_node_type_dict[node['type']])
        write_u32(f, node['meta_data_count'])

        for mc in range(node['meta_data_count']):
            meta = node['meta_data'][mc]
            write_metas(f, meta, silent)

        write_u32(f, node['content']['vertex_count'])
        write_layerstack(f, node['content']['vertex_stack'])
        write_u32(f, node['content']['edge_corner_count'])
        write_layerstack(f, node['content']['corner_stack'])
        write_layerstack(f, node['content']['edge_stack'])
        write_u32(f, node['content']['face_count'])
        write_layerstack(f, node['content']['face_stack'])

    f.close()

# *** Write functions (end)

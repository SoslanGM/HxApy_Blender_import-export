from . import hxapy_header as hxa
from . import hxapy_read_write as hxa_rw
from sys import argv


def hxa_util_validate_meta(meta, node, count, silent=True):
    meta_type = hxa.hxa_meta_data_type_dict[meta["type"]]
    if meta_type == hxa.HXA_MDT_NODE:
        for al in range(meta["array_length"]):
            if meta["data"][al] >= count:
                if not silent:
                    print(
                        f"HxA Verify Error: Node {node} has meta data {meta['name']} that is referencing a non \
                          existant node ({meta['data'][al]} out of {count})\n"
                    )
                return False
    if meta["type"] == hxa.HXA_MDT_META:
        for al in range(meta["array_length"]):
            hxa_util_validate_meta(meta["data"][al], node, count, silent)


def hxa_util_validate(hxa_file, silent=True):
    for nc in range(hxa_file["node_count"]):
        node = hxa_file["nodes"][nc]
        for mc in range(node["meta_data_count"]):
            hxa_util_validate_meta(
                node["meta_data"][mc], mc, hxa_file["node_count"], silent
            )

        node_type = hxa.hxa_node_type_dict[node["type"]]
        if node_type == hxa.HXA_NT_GEOMETRY:
            if node["content"]["vertex_stack"]["layer_count"] == 0:
                if not silent:
                    print(f"HxA Verify Error: Node {nc} has no vertex layer\n")
                return False
            components = node["content"]["vertex_stack"]["layers"][0]["components"]
            if components != 3:
                if not silent:
                    print(
                        f"HxA Verify Error: Node {mc} vertex layer vertex layer has {components} components. \
                          Must be HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS \
                          {hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_COMPONENTS}.\n"
                    )
                return False

            layer_type = hxa.hxa_data_type_dict[
                node["content"]["vertex_stack"]["layers"][0]["type"]
            ]
            if (layer_type != hxa.HXA_LDT_FLOAT) and (layer_type != hxa.HXA_LDT_DOUBLE):
                if not silent:
                    print(
                        f"HxA Verify Error: Node {nc} first vertex layer is {hxa.hxa_data_type(layer_type)}, \
                          must be HXA_LDT_FLOAT or HXA_LDT_DOUBLE\n"
                    )
                return False

            name = node["content"]["vertex_stack"]["layers"][0]["name"]
            if name != hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME:
                if not silent:
                    print(
                        f'HxA Verify Error: Node {nc} vertex layer is named {name}. \
                          Must be HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME " \
                          {hxa.HXA_CONVENTION_HARD_BASE_VERTEX_LAYER_NAME}".\n'
                    )
                return False

            if node["content"]["corner_stack"]["layer_count"] != 0:
                components = node["content"]["corner_stack"]["layers"][0]["components"]
                if components != 1:
                    if not silent:
                        print(
                            f"HxA Verify Error: Node {nc} reference layer has {components} components. Must be 1.\n"
                        )
                    return False

                layer_type = hxa.hxa_data_type_dict[
                    node["content"]["corner_stack"]["layers"][0]["type"]
                ]
                if layer_type != hxa.HXA_LDT_INT32:
                    if not silent:
                        print(
                            f"HxA Verify Error: Node {nc} reference layer is of type {hxa.hxa_data_type(layer_type)} \
                              must be HXA_LDT_INT32\n"
                        )
                    return False

                name = node["content"]["corner_stack"]["layers"][0]["name"]
                if name != hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME:
                    if not silent:
                        print(
                            f'HxA Verify Error: Node {nc} reference layer is named {name}. Must be \
                              HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME " \
                              {hxa.HXA_CONVENTION_HARD_BASE_CORNER_LAYER_NAME}".\n'
                        )
                    return False

                references = node["content"]["corner_stack"]["layers"][0]["data"]
                poly_count = 0
                reference = 0
                # Q: what if edge_corner_count is 0??
                for cc in range(node["content"]["edge_corner_count"]):
                    if references[cc] < 0:
                        reference = -references[cc] - 1
                        poly_count += 1
                    else:
                        reference = references[cc]

                    if reference >= node["content"]["vertex_count"]:
                        if not silent:
                            print(
                                f"HxA Verify Error: Node {nc} has a reference value referencing a non existing \
                                  vertex ({reference}).\n"
                            )
                        return False

                face_count = node["content"]["face_count"]
                if face_count != poly_count:
                    if not silent:
                        print(
                            f"HxA Verify Error: Node {nc} claims to have {face_count} faces but the reference data \
                              has {poly_count} faces.\n"
                        )
                    return False

    return True


if __name__ == "__main__":
    argc = len(argv)
    if argc == 1:
        print("Add a filename (ex: py hxapy_validate.py cube.hxa)")
        exit()

    # for now, we have a single filename after the script:
    # - py hxapy_validate.py filename
    filename = argv[-1]
    hxafile = hxa_rw.hxa_to_dict(filename)

    valid = hxa_util_validate(hxafile)
    if not valid:
        print(f"{filename} could not pass validation")
    if valid:
        print(f"{filename} validated")

import os
import hou

def os_path_join_for_houdini(*args):  # because Houdini likes to use forward slashes. Note, this is just cosmetic
    a_path = ""
    if len(args) == 0:
        return a_path
    else:
        slash = "/"  # if Houdini starts uses backslashes (or whatever the os's slashes are) change back to os.path.sep
        for item in args:
            a_path += item + slash

        return a_path[:-1]  # so there isn't a final slash in the end

def get_file_extension(file_path_or_name): # useful
    return os.path.splitext(file_path_or_name)[1]

def get_file_scan(a_path):
    file_scan_list = list()
    scan_list = os.listdir(a_path) # contains files and directories
    for material_name in scan_list:
        a_path = os.path.join(a_path, material_name)
        if os.path.isdir(a_path) == False:
            file_scan_list.append(material_name)
    return file_scan_list

def set_network_editor_to_view_node(a_node): # if multiple network editors, take the latest one (presumably that's what you want)
    # as per: https://forums.odforce.net/topic/12406-getting-the-current-active-network-editor-pane/
    network_editor = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()][0]
    network_editor.setCurrentNode(a_node)

def get_node_with_throw_error(node_path):  # made to stop repeated code
    a_node = hou.node(node_path)
    if a_node == None:
        node_name = node_path[node_path.rfind("/") + 1:]
        raise Exception("{} not found at {}".format(node_name, node_path))
    return a_node

def get_resolution_str(resolution_value):  # get_megascans_resolution_from_map_str_from_resolution
    """
    e.g. given 4 * 1024, return "4K"
    """
    return str(resolution_value // 1024) + "K"

def get_resolution_int(resolution_str):
    """
    e.g. given "4K", return 4 * 1024
    """
    return int(resolution_str[:-1]) * 1024

def get_resolution_int_from_megascans_map(file_path_or_name):
    """
    e.g. given "siEoZ_4K_Albedo", return 4 * 1024

    More generally, e.g. "siEoZ_8K_boo_blah_objdksfjkdsjfks" returns the same as above
    """
    first_underscore_index = file_path_or_name.find("_")
    second_underscore_index = first_underscore_index + 1 + file_path_or_name[first_underscore_index + 1:].find("_")
    resolution_str = file_path_or_name[first_underscore_index + 1: second_underscore_index]  # e.g. "4K"

    return get_resolution_int(resolution_str)


def get_highest_resolution_map(megascans_folder_scan): # Haven't tested!
    """
    Given a list of file paths or file names of megascans maps, return the highest resolution

    It ignores any file paths or file names which aren't megascans maps (i.e. resolution can't be found in them)
    Returns None if no megascans maps (at least ones with no resolution) are found.

    e.g.
    ["blah_2K_boo", "blah_4K_boo", "a_picture.jpg"]
    Returns "4K"
    """
    resolution_int_list = list()

    for file_name in megascans_folder_scan:
        try:  # may or may not be map
            megascans_resolution_int = get_resolution_int_from_megascans_map(file_name)
            resolution_int_list.append(megascans_resolution_int)
        except:  # if not map (i.e. resolution not found)
            pass

    if len(resolution_int_list) == 0:
        return None
    else:
        return max(resolution_int_list)


def get_maps_of_name_type_and_res(megascans_folder_scan, desired_map_name, file_extension_list = None, resolution_list = None):  # in descending order
    """
    Returns all maps of a specific map name found in megascans_folder_scan

    Ordered by preferred file extensions first, and preferred resolution list second
    """
    existing_maps_with_desired_map_name = [file_name for file_name in megascans_folder_scan if desired_map_name in file_name]

    sorted_maps = existing_maps_with_desired_map_name  # for clarity
    if file_extension_list != None:  # first sort
        sorted_maps = sorted(sorted_maps, key = lambda map_name: file_extension_list.index(get_file_extension(map_name)))

    if resolution_list != None:  # second sort
        sorted_maps = sorted(sorted_maps, key = lambda map_name: resolution_list.index(get_resolution_int_from_megascans_map(map_name)))

    return sorted_maps


def get_megascans_asset_name(megascans_folder_path):
    """
    Megascan's folder holding the asset will be called something like "rock_assembly_S01ez"

    The megascans maps found in this folder are prefixed with "S01ez" - which I am calling the (technical) megascans asset name
    """
    megascans_folder_name = os.path.basename(megascans_folder_path)  # just in case
    megascans_asset_name = megascans_folder_name[megascans_folder_name.rfind("_") + 1:]
    return megascans_asset_name


# useful
def recursively_add_to_network_box(network_box, the_node):
    """
    "recursively add to network box" in the sense that you give it a node, and it adds all the nodes connected to that node, and so on, to the network box
    """
    return recursive_network_box_helper_function(network_box, (the_node,))


def recursive_network_box_helper_function(network_box, node_tuple):
    for a_node in node_tuple:
        if a_node == None:  # for some reason, input() and output() give None sometimes
            continue
        if a_node in network_box.items():  # logical, and in effect stops it bouncing back and fourth between nodes already in the network box
            # print("{} is in network_box".format(a_node))
            continue
        network_box.addNode(a_node)

        input_and_output_node_tuple = a_node.inputs() + a_node.outputs()
        # print("input_and_output_node_tuple: {}".format(input_and_output_node_tuple))

        if len(input_and_output_node_tuple) == 0:
            continue  # 'continues' anyway since there's nothing after
        else:
            recursive_network_box_helper_function(network_box, input_and_output_node_tuple)
import hou
import os
import time

from big_framework import *

import megascans_custom_lod_and_bake_ui
import lod_and_bake

import pdg

# so houdini doesn't use the precompiled:
reload(megascans_custom_lod_and_bake_ui)
reload(lod_and_bake)



def os_path_join_for_houdini(*args):  # because Houdini likes to use forward slashes. Note, this is just cosmetic
    a_path = ""
    if len(args) == 0:
        return a_path
    else:
        slash = "/"  # if Houdini starts uses backslashes (or whatever the os's slashes are) change back to os.path.sep
        for item in args:
            a_path += item + slash

        return a_path[:-1]  # so there isn't a final slash in the end

def get_node_with_throw_error(node_path):  # made to stop repeated code
    a_node = hou.node(node_path)
    if a_node == None:
        node_name = node_path[node_path.rfind("/") + 1:]
        raise Exception("{} not found at {}".format(node_name, node_path))
    return a_node

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
    e.g. given "siEoZ_8K_Albedo", return 8 * 1024

    More generally, e.g. "siEoZ_8K_boo_blah_objdksfjkdsjfks" returns the same as above
    """
    first_underscore_index = file_path_or_name.find("_")
    second_underscore_index = first_underscore_index + 1 + file_path_or_name[first_underscore_index + 1:].find("_")
    resolution_str = file_path_or_name[first_underscore_index + 1: second_underscore_index]  # e.g. "4K"

    return get_resolution_int(resolution_str)


def get_highest_resolution_map(megascans_folder_scan):
    """
    Given a list of file paths or file names of megascans maps, return the highest resolution

    It ignores any file paths or file names which aren't megascans maps (i.e. resolution can't be found in them)
    Returns None if none found.

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
        return max(resolution_int_list) * 1024


def get_maps_of_name_type_and_res(megascans_folder_scan, desired_map_name, file_extension_list = None, resolution_list = None):  # in descending order
    """
    Returns all maps of a specific map name found in megascans_folder_scan, ordered by preferred file extensions THEN resolution

    Ordered by preferred file extensions first, and resolution second
    """
    existing_maps = [file_name for file_name in megascans_folder_scan if desired_map_name in file_name]

    sorted_maps = existing_maps  # for clarity
    if file_extension_list != None:  # first sort
        sorted_maps = sorted(sorted_maps, key = lambda map_name: file_extension_list.index(get_file_extension(map_name)))

    if resolution_list != None:  # second sort
        sorted_maps = sorted(sorted_maps, key = lambda map_name: resolution_list.index(get_resolution_from_megascans_map(map_name)))

    return sorted_maps


def get_megascans_asset_name(megascans_folder_path):
    """
    Megascan's folder holding the asset will be called something like "rock_assembly_S01ez"

    The megascans maps found in this folder are prefixed with "S01ez" - which I am calling the (technical) megascans asset name
    """
    megascans_folder_name = os.path.basename(megascans_folder_path)  # just in case
    megascans_asset_name = megascans_folder_name[megascans_folder_name.rfind("_") + 1:]
    return megascans_asset_name


def replace_substring_with_count(a_string, substring_to_replace, count):
    """
    Self-explanatoy, handy to have.
    """
    while substring_to_replace in a_string:
        a_string = a_string.replace(substring_to_replace, str(count), 1)
        count += 1
    return a_string, count

def add_node_setup_to_material_node(self):
    """
    Add node setups, as described in map_name_and_node_setup_dict to the rs_material_builder node

    This has a nice bump_blender feature (replaces {bump_blender_layer} with the current layer and increments layer)
    """
    material_builder_node = self.asset_material_object.get_material_builder_node()

    for map_name in self.map_name_and_node_setup_dict.keys():  # have to get keys again since they've changed
        try:
            node_setup_string = self.map_name_and_node_setup_dict[map_name]
        except KeyError:  # only error it could be
            raise Exception("map_name_and_node_setup_dict does not contain the node setup for map_name: {}".format(map_name))
        else:
            a_export_path = "waiting for maps to be rendered"
            node_setup_string = node_setup_string.format(export_path = a_export_path.replace(" ", "%20"))  # using format instead of replace, just for the sake of that's how I would've done the above

            string_processor(material_builder_node, node_setup_string)

# shouldn't be a method?
def get_map_name_and_reader_node_dict(self, parameter_content):  # could hardcode parameter_content to be "{export_path}"
    """
    Given a map_name_and_node_setup_dict, identify the reader nodes (nodes which have a certain parameter content
    """
    a_dict = dict()

    for map_name in self.map_name_and_node_setup_dict.keys():
        a_node_setup_string = self.map_name_and_node_setup_dict[map_name]
        a_node_setup_list = a_node_setup_string.split(" ")

        for item in a_node_setup_list:
            if parameter_content in item:
                reader_node_name = get_entry_name(item)
                reader_node_param_name = get_entry_param_name_from_content(item, parameter_content)

                a_dict[map_name] = (
                reader_node_name, reader_node_param_name)  # e.g. a_dict["Displacement"] = ('displacement_node', 'tex0')

    return a_dict

def update_megascans_material_reader_nodes_export_paths(rs_material_builder_node, map_name_and_reader_node_dict, map_name_and_export_paths_dict):
    """
    So the node setups from node_name_and_setup_dict have already been added to rs_material_builder_node in a previous
    step.

    This function modifies the reader nodes in this node setup: updating their "reader parameter's" to the export paths
    given.
    """
    for map_name in map_name_and_reader_node_dict.keys():
        reader_node_name, reader_node_param_name = map_name_and_reader_node_dict[map_name]
        export_path = map_name_and_export_paths_dict[map_name]

        # doing this way, rather than using string processor (as the latter doesn't simplify things)
        reader_node = hou.node("{}/{}".format(rs_material_builder_node.path(), reader_node_name))
        # print(reader_node_name, reader_node_param_name)
        reader_node.parm(reader_node_param_name).set(export_path)

def get_nice_string_of_map_name_and_reader_node_dict(map_name_and_reader_node_dict):  # self-explanatory
    final_string = ""

    a_header = "In order: Map Name, Reader Node Name, Reader Node Parameter Name:"  # I also like to call the reader node's corrseponding parameter 'reader parameter'
    final_string += a_header
    for map_name in map_name_and_reader_node_dict.keys():
        reader_node_name, reader_node_param_name = map_name_and_reader_node_dict[map_name]
        a_line = "{}, {}, {}".format(map_name, reader_node_name, reader_node_param_name)
        final_string += "\n" + a_line

    return final_string

# useful
def recursively_add_to_network_box(network_box, the_node):
    """
    recursively add to network box" in the sense that you give it a node, and it adds all the nodes connected to that node, and so on, to the network box
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

def get_map_name_and_node_setup_dict(map_name_and_node_setup_dict, maps_to_bake_dict):  # makes sense for this to be a static method..
    """
    Modify map_name_and_node_setup_dict to only have the maps we're baking
    """
    map_name_and_node_setup_dict_copy = map_name_and_node_setup_dict.copy()  # making a copy, since to modify would change the original since dictionaries are mutable
    for map_name in map_name_and_node_setup_dict_copy.keys():
        bake_bool = maps_to_bake_dict[map_name]
        if bake_bool == False:
            map_name_and_node_setup_dict.pop(map_name)  # pops keys

    return map_name_and_node_setup_dict_copy


def set_network_editor_to_view_node(a_node): # if multiple network editors, take the latest one (presumably that's what you want)
    # as per: https://forums.odforce.net/topic/12406-getting-the-current-active-network-editor-pane/
    network_editor = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()][0]
    network_editor.setCurrentNode(a_node)

redshift_map_name_and_node_setup_dict = dict()
redshift_map_name_and_node_setup_dict["Displacement"] = "cTextureSampler-CB_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Displacement_2!map_encoding:2!space_type:1 i0"  # Map Encoding 0 is Vector, 2 is Height Field. Space Type 1 is object, 2 is Tangent.
redshift_map_name_and_node_setup_dict["Vector Displacement"] = "cTextureSampler-CB_Vector_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Vector_Displacement_2!map_encoding:0!space_type:1 i0"
redshift_map_name_and_node_setup_dict["Tangent-Space Vector Displacement"] = "cTextureSampler-CB_Tangent-Space_Vector_Displacement_1!tex0:{export_path} i0 cDisplacement-CB_Tangent-Space_Vector_Displacement_2!map_encoding:0!space_type:2 i0"
redshift_map_name_and_node_setup_dict["Tangent-Space Normal"] = "@cNormalMap-CB_Tangent-Space_Normal!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Occlusion"] = "@cTextureSampler-CB_Occlusion!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Cavity"] = "@cTextureSampler-CB_Cavity!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Thickness"] = "@cTextureSampler-CB_Thickness!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Curvature"] = "@cTextureSampler-CB_Curvature!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Shading Position"] = "@cTextureSampler-CB_Shading_Position!tex0:{export_path}"
redshift_map_name_and_node_setup_dict["Shading Normal"] = "@cTextureSampler-CB_Shading_Normal!tex0:{export_path}"



class MegascansAsset:
    """
    This stores information about a Megascans Asset (the subnet in Houdini, its files location on disk),
    and has methods -- there is only one method so far "execute" and helper methods for that
    """

    @staticmethod
    def get_nodes(megascans_asset_subnet_node):  # assumes using certain version of Bridge
        """
        Given a megascan asset asset subnet node return a bunch of important nodes
        """
        megascans_asset_subnet_path = megascans_asset_subnet_node.path()
        asset_geometry_path = "{}/Asset_Geometry".format(megascans_asset_subnet_path)
        asset_geometry_node = hou.node(asset_geometry_path)
        asset_material_path = "{}/Asset_Material".format(megascans_asset_subnet_path)
        asset_material_node = hou.node(asset_material_path)

        # good to check that a megascans subnet is even selected before doing the rest
        if asset_geometry_node == None or asset_geometry_node == None:
            raise Exception(
                "'Asset_Geometery' or 'Asset_Material' aren't children of {}.\nAre you sure you've selected a Megascans Asset Subnetwork?".format(
                    megascans_asset_subnet_path))

        file_node_path = "{}/Asset_Geometry/file1".format(
            megascans_asset_subnet_path)  # more adaptable to give path, instead of getting as child from Asset_Material
        transform_node_path = "{}/Asset_Geometry/transform1".format(megascans_asset_subnet_path)  # ditto ^
        file_node = get_node_with_throw_error(file_node_path)
        transform_node = get_node_with_throw_error(transform_node_path)

        # Is it worth it to get these here? Step 1 and 2 can carry on without these (also transform not necessary in the above)
        rs_material_builder_node = asset_material_node.children()[0]
        if rs_material_builder_node.type().name() != "redshift_vopnet":
            raise Exception("Expected node in Asset Geometry to be of type 'redshift_vopnet'")

        redshift_material_node = None
        for child in rs_material_builder_node.children():
            if child.type().name() == "redshift_material":
                redshift_material_node = child
                break
        if redshift_material_node == None:
            raise Exception("Cannot find node of type 'redshift_material' in RS Material Builder")

    return asset_geometry_node, asset_material_node, file_node, transform_node, rs_material_builder_node, redshift_material_node

    @staticmethod
    def display_message(message_string, kwargs):
        # same functionality as hou.ui.displayMessage, just ensures title
        hou.ui.displayMessage(message_string, title = "Megascans Custom LOD & Baking Tool", **kwargs)


    def __init__(self, megascans_asset_subnet):
        self.megascans_asset_subnet = megascans_asset_subnet

        # todo: if we're serious about this working for multiple render engines, I need to re-think the node getting (how about splitting it up in to two)
        self.asset_geometry_node, self.asset_material_node, self.file_node, self.transform_node, self.rs_material_builder_node, self.redshift_material_node = MegascansAsset.get_nodes(self.megascans_asset_subnet)  # remember in tuple unpacking, any name can be used i.e. i've added on self

        self.megascans_asset_folder_path = os.path.dirname(self.file_node.parm("file").eval())
        self.megascans_asset_name = get_megascans_asset_name(self.megascans_asset_folder_path)

        self.megascans_asset_folder_scan = get_file_scan(self.megascans_asset_folder_path) # all files from folder

        # todo: add logic to see if fix_subnet_node already exists?

    def make_custom_lod(self, subnet_node, polyreduce_percentage_float, highpoly_name):
        customlod_name = self.megascans_asset_name + "_LOD{}percent_custom.fbx".format(polyreduce_percentage_float)
        customlod_path = os_path_join_for_houdini(self.megascans_asset_folder_path, customlod_name)

        highpoly_path = os_path_join_for_houdini(self.megascans_asset_folder_path, highpoly_name)

        a_lod_object = lod_and_bake.LOD(highpoly_path, polyreduce_percentage_float, customlod_path)

        a_lod_object.create_in_houdini(subnet_node)

        if os.path.exists(customlod_path) == False:
            MegascansAsset.display_message("Baking out {} percent LOD now (this should freeze Houdini).\n\nOnce this has finished baking your asset's geometry will be set to use this LOD too.".format(polyreduce_percentage_float))
            a_lod_object.execute_in_houdini()
        else:
            MegascansAsset.display_message("A LOD that's {} percent already exists at:\n {}\n\nUsing that instead of re-baking\n\nYour asset's geometry will be set to use this LOD too.".format(polyreduce_percentage_float, customlod_path))

        self.file_node.parm("file").set(customlod_path)  # could go inside if block. Having it here is a bit of fool proofing

        return customlod_path

    def configure_megascans_material_node(self): # enable tessalation, displacement etc.
        # Enable Tessellation, Displacement, and set Displacement Scale
        self.asset_geometry_node.parm("RS_objprop_rstess_enable").set(1)
        self.asset_geometry_node.parm("RS_objprop_displace_enable").set(1)
        displacement_scale = self.transform_node.parm("scale").eval()  # retrieved from transform_node after file import
        self.asset_geometry_node.parm("RS_objprop_displace_scale").set(displacement_scale)


    def cook_event_handler_one(self, handler, event):  # because this event handler is passed the handler too
        """
        (Used when 'use temp low res maps' has been enabled)

        This notifies user that their high res maps have finished baking, and asks if they want them to be swapped over
        - and if yes, swaps them over.
        """
        # Ask if they want to swap over to chosenres maps
        nice_string_of_map_name_and_reader_node_dict = get_nice_string_of_map_name_and_reader_node_dict(self.map_name_and_reader_node_dict)
        message_string = "Your {} resolution maps have finished baking. Currently your reader nodes are set to use the paths of the 1K maps, would you like your reader nodes to swap over to your chosen resolution maps now?\n\nIf you want to do this manually, note the map name and the correspond reader nodes / reader parameters are:\n{}".format(
            self.chosen_bake_resolution_str, nice_string_of_map_name_and_reader_node_dict)

        user_choice = MegascansAsset.display_message(message_string, buttons=('Yes', 'No'), default_choice = 0)  # 0 is Yes, 1 is No

        if user_choice == 0: # If yes, swap over
            update_megascans_material_reader_nodes_export_paths(self.rs_material_builder_node, self.map_name_and_reader_node_dict,
                                                   self.chosenres_map_name_and_export_paths_dict)
            MegascansAsset.display_message((
                "Reader nodes updated to your {} resolution maps successfully".format(self.chosen_bake_resolution_str))

        handler.removeFromAllEmitters()  # remove this event handler from the event (rather, delete the emitters (the 'mouth') from the handler). Doing this so that a user doesn't get confused when they re-render, perhaps it's a good thing to keep the eventhandler?

        self.all_done_message()

    def cook_event_handler_two(self, handler, event):
        """
        (Used when 'use temp low res maps' has NOT been enabled)

        Notifies user that their maps have finished baking.
        """
        MegascansAsset.display_message("Your {} resolution maps have finished baking! Note, your reader nodes are already set to the paths of these".format(self.chosen_bake_resolution_str))

        handler.removeFromAllEmitters()  # ^ ditto

        self.all_done_message()

    def bake_custom_maps_and_update_reader_nodes_accordingly(self, subnet_node, polyreduce_percentage_float, chosen_bake_resolution_str, use_temp_resolution_bool, maps_to_bake_dict, highpoly_path, customlod_path):
        # Get information about chosenres
        chosenres_bake_resolution_x_and_y = get_resolution_int(chosen_bake_resolution_str)
        chosenres_export_name_prefix = "{}_{}_LOD{}_".format(self.megascans_asset_name, chosen_bake_resolution_str,
                                                             polyreduce_percentage_float)
        chosenres_export_path = lod_and_bake.Bake.get_export_path(self.megascans_asset_folder_path,
                                                                  chosenres_export_name_prefix)
        self.chosenres_map_name_and_export_paths_dict = lod_and_bake.Bake.get_map_name_and_export_paths_dict(
            maps_to_bake_dict, self.megascans_asset_folder_path,
            chosenres_export_name_prefix)  # this is a attribute so that cook_event_handler_one can access it

        # Create a GENERAL Bake object to use in the PDG later i.e. hack it so that resolution_x and resolution_y are "@bake_resolution_x_and_y" and so export_path is "@export_path"
        general_bake_object = lod_and_bake.Bake(highpoly_path, customlod_path, maps_to_bake_dict, 0, 0,
                                                self.megascans_asset_folder_path)  # have the resolution x and y be 0 for now, and have export_path be the default for now (both things changed below)
        general_baketexture_node, general_camera_node = general_bake_object.create_in_houdini(subnet_node)

        # yes, I could assign "@bake_resolution_x_and_y" to a variable to stop me having to type it out, but I think it's more clear this way
        general_camera_node.parm("resx").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)
        general_camera_node.parm("resy").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)
        general_baketexture_node.parm("vm_uvunwrapresx").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvunwrapresy").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvoutputpicture1").setExpression("@export_path")

        # Create PDG network, modify reader nodes, bake and add event handlers (exact instructions of the aforementioned on if using temp resolution)
        topnet_node = subnet_node.createNode("topnet", "topnet")
        string_processor(topnet_node, "cwedge-wedge i0 cropfetch-ropfetch i0")

        ropfetch_node = hou.node(topnet_node.path() + "/ropfetch")  # as per created above (needed to execute)
        ropfetch_node.parm("roppath").set(general_baketexture_node.path())

        pdg_graph_context = ropfetch_node.getPDGGraphContext()  # could call this method on the topnet or wedge and it'd give the same context

        if use_temp_resolution_bool == True:
            # Get information about lowres
            lowres_bake_resolution_x_and_y = 1024  # change to what you like
            lowres_export_name_prefix = "{}_{}_LOD{}_".format(self.megascans_asset_name,
                                                              get_megascans_resolution_from_map_str_from_resolution(
                                                                  lowres_bake_resolution_x_and_y),
                                                              polyreduce_percentage_float)
            lowres_export_path = lod_and_bake.Bake.get_export_path(self.megascans_asset_folder_path,
                                                                   lowres_export_name_prefix)
            lowres_map_name_and_export_paths_dict = lod_and_bake.Bake.get_map_name_and_export_paths_dict(
                maps_to_bake_dict, self.megascans_asset_folder_path, lowres_export_name_prefix)

            # Modify megascans reader nodes to lowres
            update_megascans_material_reader_nodes_export_paths(self.rs_material_builder_node, self.map_name_and_reader_node_dict,
                                                   lowres_map_name_and_export_paths_dict)

            # Configure pdg
            string_processor(topnet_node,
                             "@ewedge!wedgecount:2!wedgeattributes:2!name1:export_path!type1:4!values1:2!strvalue1_1:{}!strvalue1_2:{}!name2:bake_resolution_x_and_y!type2:2!wedgetype2:2!values2:2!intvalue2_1:{}!intvalue2_2:{}".format(
                                 lowres_export_path.replace(" ", "%20"), chosenres_export_path.replace(" ", "%20"),
                                 lowres_bake_resolution_x_and_y,
                                 chosenres_bake_resolution_x_and_y))  # set parameters on wedge node

            # Add event handlers to pdg graph context (this event handler asks if the user wants to modify megascans reader nodes to chosenres once baking is complete)
            pdg_graph_context.addEventHandler(self.cook_event_handler_one, pdg.EventType.CookComplete,
                                              True)  # the True means that a handler will be passed to the event handler, as well as the event
        else:
            # Modify megascans reader nodes to chosenres
            update_megascans_material_reader_nodes_export_paths(self.rs_material_builder_node, self.map_name_and_reader_node_dict,
                                                   self.chosenres_map_name_and_export_paths_dict)  # doing before

            # Configure pdg
            string_processor(topnet_node,
                             "@ewedge!wedgecount:1!wedgeattributes:2!name1:export_path!type1:4!values1:1!strvalue1_1:{}!name2:bake_resolution_x_and_y!type2:2!wedgetype2:2!values2:1!intvalue2_1:{}".format(
                                 chosenres_export_path.replace(" ", "%20"),
                                 chosenres_bake_resolution_x_and_y))  # set parameters on wedge node

            # Add event handlers to pdg graph context (this event handler notifies the user cooking is done)
            pdg_graph_context.addEventHandler(self.cook_event_handler_two, pdg.EventType.CookComplete, True)  # ^ ditto

        # Save and Cook PDG
        hou.hipFile.save()  # executeGraph uses the last saved hipfile version
        ropfetch_node.executeGraph(False, False, False,
                                   False)  # note that pdg/topnets render by behind-the-scenes opening the latest save of houdini with the corresponding work item's attributes and rendering there

        # an after thought to put all nodes created in to a network box (a hacky way, using the fact that all the nodes created are reader nodes or connected to reader nodes)
        network_box = self.rs_material_builder_node.createNetworkBox()
        network_box.setComment("Custom baked maps' reader nodes (and their connected nodes)")
        for map_name in self.map_name_and_reader_node_dict.keys():
            reader_node_name, reader_node_param_name = self.map_name_and_reader_node_dict[map_name]
            reader_node = hou.node(self.rs_material_builder_node.path() + "/" + reader_node_name)
            recursively_add_to_network_box(network_box, reader_node)
        network_box.fitAroundContents()

        a_vector = hou.Vector2(2, 0)  # hard coded (the size needed to fit the comment above)
        network_box.resize(a_vector)

        self.organise_megascans_asset_subnet_and_hide_fix_subnet(subnet_node)  # layout all the necessary things

        # notify user (neilson's heuristics)
        if use_temp_resolution_bool == True:
            MegascansAsset.display_message("Baking out temporary 1K resolution maps, and your chosen {chosen_bake_resolution_str} resolution maps now.\n\nYour reader nodes have been created, they are set to use the paths of the 1K maps. Once {chosen_bake_resolution_str} resolution maps have finished baking, you'll be asked if you want to swap over your reader nodes to these.".format(chosen_bake_resolution_str = chosen_bake_resolution_str))
            # ^ assuming 1K will bake out first, otherwise the wording needs to change
        else:
            MegascansAsset.display_message("Baking out {} resolution maps now, you will be notified when they're done.\n\nYour reader nodes have been created. they are using the paths of these maps (even though they're not baked yet).".format(chosen_bake_resolution_str))


    def execute_custom_lod_and_baking(self, polyreduce_percentage_float, maps_to_bake_dict, chosen_bake_resolution_str, use_temp_resolution_bool):
        fix_subnet_node = self.megascans_asset_subnet.createNode("subnet", "Megascans_Custom_LOD_and_Baking_Subnet")  # Feel free to change name

        # Preperation
        if chosen_bake_resolution_str == "1K":  # simplifies things to get this out of the way now
            use_temp_resolution_bool = False

        map_name_and_node_setup_dict = MegascansAsset.get_map_name_and_node_setup_dict(maps_to_bake_dict)
        self.map_name_and_reader_node_dict = get_map_name_and_reader_node_dict(map_name_and_node_setup_dict, "{export_path}")  # reader nodes are nodes which have "{export_path}"

        # Step a

        if len(highpoly_name_list) == 0:
            MegascansAsset.display_message("Highpoly Source not found.\nPlease make sure you've ticked 'Highpoly Source' in Bridge, this will make a .fbx file in your megascans folder with 'High' in its name")
            fix_subnet_node.destroy()
            return

        highpoly_name = highpoly_name_list[0]  # the 0'th index is the highest resolution
        highpoly_path = os_path_join_for_houdini(self.megascans_asset_folder_path, highpoly_name)

        customlod_path = self.make_custom_lod(fix_subnet_node, polyreduce_percentage_float, highpoly_name)

        # Step bi
        self.configure_megascans_material_node(map_name_and_node_setup_dict)

        # Step bii

        if len(map_name_and_node_setup_dict.keys()) == 0:
            self.organise_megascans_asset_subnet_and_hide_fix_subnet(fix_subnet_node)
            self.all_done_message()
            raise SystemExit  # they didn't ask for any maps to be baked

        current_bump_blender_layer = 0 # assuming 'Base' on BumpBlender doesn't need to be used
        add_to_megascans_material_node_setup(self.rs_material_builder_node, map_name_and_node_setup_dict, current_bump_blender_layer)  # puts "todo" where export paths should go (update_megascans_material_reader_nodes_export_paths sorts that out)


        # Step c
        self.bake_custom_maps_and_update_reader_nodes_accordingly(fix_subnet_node, polyreduce_percentage_float, chosen_bake_resolution_str, use_temp_resolution_bool, maps_to_bake_dict, highpoly_path, customlod_path)


    def organise_megascans_asset_subnet_and_hide_fix_subnet(self, fix_subnet_node):
        # to render, the below to be True but since rendering uses an (previously saved) hipfile with this True, it's fine to do here
        fix_subnet_node.setDisplayFlag(False)

        self.set_network_editor_to_view_megascans_asset_subnet()

        # Layout rs material builder node
        self.rs_material_builder_node.layoutChildren()

        # Layout the fix subnet
        fix_subnet_node.layoutChildren()

        # Layout the megascans asset subnet (that holds the fix subnet)
        self.megascans_asset_subnet.layoutChildren()

    def all_done_message(self):
        MegascansAsset.display_message("All done! Seriously, this shelf tool has finished. Thanks for using me")




def main():
    selected_node_list = hou.selectedNodes()
    if len(selected_node_list) != 1:
        raise MegascansAsset.display_message("Zero or Multiple nodes selected. Are you sure you've selected a single Megascans Asset Subnetwork?")

    megascans_asset_subnet = selected_node_list[0] # assuming that it's a megascans asset (checking below)

    try:
        megascans_asset_object = MegascansAsset(megascans_asset_subnet)
    except Exception as exception:
        MegascansAsset.display_message("Error Occured:\n\n{}\n\nPlease try again")
        raise SystemExit

    megascans_asset_subnet.setDisplayFlag(True)  # baking requires its display flag is visible

    ui = ui.MegascansFixerDialog(megascans_asset_object)
    ui.show()

    # the UI handles everything from here
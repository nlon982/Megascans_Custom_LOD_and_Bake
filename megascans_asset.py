import hou
import pdg

from renderer_material import RedshiftMaterial
from helper_functions import *
from big_framework import *

import megascans_custom_lod_and_bake_ui
import lod_and_bake

# so houdini doesn't use the precompiled:
reload(megascans_custom_lod_and_bake_ui)
reload(lod_and_bake)


class MegascansAsset:
    """
    This stores information about a Megascans Asset (the subnet in Houdini, its files location on disk),
    and has methods -- there is only one method so far "execute_custom_lod_and_baking" and helper methods for that
    """

    @staticmethod
    def display_message(message_string, **kwargs):
        # same functionality as hou.ui.displayMessage, just ensures title
        return hou.ui.displayMessage(message_string, title = "Megascans Custom LOD & Baking Tool", **kwargs)
        # ^ returning because hou.ui.displayMessage returns

    @staticmethod
    def get_asset_geometry_nodes(megascans_asset_subnet_node):
        megascans_asset_subnet_path = megascans_asset_subnet_node.path()
        asset_geometry_path = "{}/Asset_Geometry".format(megascans_asset_subnet_path)
        asset_geometry_node = hou.node(asset_geometry_path)

        if asset_geometry_node is None:
            raise Exception("'Asset_Geometry' isn't a child of {}.\nAre you sure you've selected a Megascans Asset Subnetwork?".format(megascans_asset_subnet_path))

        file_node_path = "{}/Asset_Geometry/file1".format(megascans_asset_subnet_path)
        transform_node_path = "{}/Asset_Geometry/transform1".format(megascans_asset_subnet_path)
        file_node = get_node_with_throw_error(file_node_path)
        transform_node = get_node_with_throw_error(transform_node_path)

        return asset_geometry_node, transform_node, file_node

    @staticmethod
    def get_asset_material_object(megascans_asset_subnet_node):
        megascans_asset_subnet_path = megascans_asset_subnet_node.path()

        asset_material_path = "{}/Asset_Material".format(megascans_asset_subnet_path)
        asset_material_node = hou.node(asset_material_path)

        if asset_material_node is None:
            raise Exception("'Asset_Material' isn't a child of {}.\nAre you sure you've selected a Megascans Asset Subnetwork?".format(megascans_asset_subnet_path))

        # todo: could get it to look at all children for one with an appropriate type (if multiple of appropriate type, choose the first one)
        try:
            asset_material_node_child = asset_material_node.children()[0] # assuming only one child
        except:
            raise Exception("'Asset_Material' does not have a child.")
        renderer_material_builder_type = asset_material_node_child.type().name()

        if renderer_material_builder_type  == "redshift_vopnet":
            asset_material_object = RedshiftMaterial(asset_material_node_child)
        else:
            asset_material_object = None

        return asset_material_object

    @staticmethod
    def get_nodes(megascans_asset_subnet_node):
        try:
            asset_geometry_node, transform_node, file_node = MegascansAsset.get_asset_geometry_nodes(megascans_asset_subnet_node)
            asset_material_object = MegascansAsset.get_asset_material_object(megascans_asset_subnet_node)
        except Exception as exception:
            raise Exception("{}".format(exception)) # Feel free to add anything else (otherwise this try / except isn't doing anything)
        return asset_geometry_node, transform_node, file_node, asset_material_object

    def get_map_name_and_node_setup_dict(self, template_map_name_and_node_setup_dict):
        """
        Modify map_name_and_node_setup_dict to only have the maps we're baking
        """
        for map_name in template_map_name_and_node_setup_dict.keys():
            bake_bool = self.maps_to_bake_dict[map_name]
            if bake_bool == False:
                template_map_name_and_node_setup_dict.pop(map_name)  # pops keys

        return template_map_name_and_node_setup_dict

    def get_map_name_and_reader_node_dict(self, parameter_content):  # could hardcode parameter_content to be "{export_path}"
        """
        Given a map_name_and_node_setup_dict, identify the reader nodes (nodes which have a certain parameter content)
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
                        reader_node_name,
                        reader_node_param_name)  # e.g. a_dict["Displacement"] = ('displacement_node', 'tex0')

        return a_dict

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
                raise Exception(
                    "map_name_and_node_setup_dict does not contain the node setup for map_name: {}".format(map_name))
            else:
                a_export_path = "waiting for maps to be rendered"
                node_setup_string = node_setup_string.format(export_path = a_export_path.replace(" ",
                                                                                                 "%20"))  # using format instead of replace, just for the sake of that's how I would've done the above

                string_processor(material_builder_node, node_setup_string)

    def __init__(self, megascans_asset_subnet_node):
        self.megascans_asset_subnet_node = megascans_asset_subnet_node

        self.asset_geometry_node, self.transform_node, self.file_node, self.asset_material_object = MegascansAsset.get_nodes(megascans_asset_subnet_node)

        self.megascans_asset_folder_path = os.path.dirname(self.file_node.parm("file").eval())
        self.megascans_asset_name = get_megascans_asset_name(self.megascans_asset_folder_path)

        self.megascans_asset_folder_scan = get_file_scan(self.megascans_asset_folder_path) # all files from folder

        highpoly_name_list = get_maps_of_name_type_and_res(self.megascans_asset_folder_scan, "High", file_extension_list=[".fbx"])  # pick best from sorted, which is at index 0
        highpoly_name = highpoly_name_list[0]  # the 0'th index is the highest resolution
        self.highpoly_path = os_path_join_for_houdini(self.megascans_asset_folder_path, highpoly_name)
        if len(highpoly_name_list) == 0:
            raise Exception("Highpoly Source not found.\nPlease make sure you've ticked 'Highpoly Source' in Bridge, this will make a .fbx file in your megascans folder with 'High' in its name")

    def make_custom_lod(self):
        customlod_name = self.megascans_asset_name + "_LOD{}percent_custom.fbx".format(self.polyreduce_percentage_float)
        customlod_path = os_path_join_for_houdini(self.megascans_asset_folder_path, customlod_name)

        a_lod_object = lod_and_bake.LOD(self.highpoly_path, self.polyreduce_percentage_float, customlod_path)

        a_lod_object.create_in_houdini(self.fix_subnet_node)

        if os.path.exists(customlod_path) == False:
            MegascansAsset.display_message("Baking out {} percent LOD now (this should freeze Houdini).\n\nOnce this has finished baking your asset's geometry will be set to use this LOD too.".format(self.polyreduce_percentage_float))
            a_lod_object.execute_in_houdini()
        else:
            MegascansAsset.display_message("A LOD that's {} percent already exists at:\n {}\n\nUsing that instead of re-baking\n\nYour asset's geometry will be set to use this LOD too.".format(self.polyreduce_percentage_float, customlod_path))

        self.file_node.parm("file").set(customlod_path)  # could go inside if block. Having it here is a bit of fool proofing

        return customlod_path

    def organise_megascans_asset_subnet_and_hide_fix_subnet(self):
        # to render, the below to be True but since rendering uses an (previously saved) hipfile with this True, it's fine to do here
        self.fix_subnet_node.setDisplayFlag(False)

        set_network_editor_to_view_node(self.megascans_asset_subnet_node)

        # Layout material builder node
        self.asset_material_object.get_material_builder_node().layoutChildren()

        # Layout the fix subnet
        self.fix_subnet_node.layoutChildren()

        # Layout the megascans asset subnet (that holds the fix subnet)
        self.megascans_asset_subnet_node.layoutChildren()

    def all_done_message(self):
        MegascansAsset.display_message("All done! Seriously, this shelf tool has finished. Thanks for using me")

    def update_megascans_material_reader_nodes_export_paths(self, map_name_and_export_paths_dict):
        """
        So the node setups from node_name_and_setup_dict have already been added to rs_material_builder_node in a previous
        step.

        This function modifies the reader nodes in this node setup: updating their "reader parameter's" to the export paths
        given.
        """
        for map_name in self.map_name_and_reader_node_dict.keys():
            reader_node_name, reader_node_param_name = self.map_name_and_reader_node_dict[map_name]
            export_path = map_name_and_export_paths_dict[map_name]

            # doing this way, rather than using string processor (as the latter doesn't simplify things)
            material_builder_node = self.asset_material_object.get_material_builder_node()
            reader_node = hou.node("{}/{}".format(material_builder_node.path(), reader_node_name))
            # print(reader_node_name, reader_node_param_name)
            reader_node.parm(reader_node_param_name).set(export_path)

    def get_nice_string_of_map_name_and_reader_node_dict(self):  # self-explanatory
        final_string = ""

        a_header = "In order: Map Name, Reader Node Name, Reader Node Parameter Name:"  # I also like to call the reader node's corrseponding parameter 'reader parameter'
        final_string += a_header
        for map_name in self.map_name_and_reader_node_dict.keys():
            reader_node_name, reader_node_param_name = self.map_name_and_reader_node_dict[map_name]
            a_line = "{}, {}, {}".format(map_name, reader_node_name, reader_node_param_name)
            final_string += "\n" + a_line

        return final_string

    def cook_event_handler_one(self, handler, event):  # because this event handler is passed the handler too
        """
        (Used when 'use temp low res maps' has been enabled)

        This notifies user that their high res maps have finished baking, and asks if they want them to be swapped over
        - and if yes, swaps them over.
        """
        # Ask if they want to swap over to chosenres maps
        nice_string_of_map_name_and_reader_node_dict = self.get_nice_string_of_map_name_and_reader_node_dict()
        do_it_yourself_message_string = "\n\nIf you want to do this manually, note the map name and the correspond reader nodes / reader parameters are:\n{}".format(nice_string_of_map_name_and_reader_node_dict)
        # ^ currently not used

        message_string = "Your {} resolution maps have finished baking. Currently your reader nodes are set to use the paths of the 1K maps, would you like your reader nodes to swap over to your chosen resolution maps now?".format(self.chosen_bake_resolution_str)



        user_choice = MegascansAsset.display_message(message_string, buttons = ('Yes', 'No'), default_choice = 0)  # 0 is Yes, 1 is No

        if user_choice == 0: # If yes, swap over
            self.update_megascans_material_reader_nodes_export_paths(self.chosenres_map_name_and_export_paths_dict)
            MegascansAsset.display_message("Reader nodes updated to your {} resolution maps successfully".format(self.chosen_bake_resolution_str))

        handler.removeFromAllEmitters()  # remove this event handler from the event (rather, delete the emitters (the 'mouth') from the handler). Doing this so that a user doesn't get confused when they re-render, perhaps it's a good thing to keep the eventhandler?

        self.all_done_message()

    def cook_event_handler_two(self, handler, event):
        """
        (Used when 'use temp low res maps' has NOT been enabled)

        Notifies user that their maps have finished baking.
        """
        if self.make_reader_nodes_bool == True:
            MegascansAsset.display_message("Your {} resolution maps have finished baking! Note, your reader nodes are already set to the paths of these".format(self.chosen_bake_resolution_str))
        else:
            MegascansAsset.display_message("Your {} resolution maps have finished baking!".format(self.chosen_bake_resolution_str))

        handler.removeFromAllEmitters()  # ^ ditto

        self.all_done_message()


    def get_bake_info(self, bake_resolution_int):
        export_name_prefix = "{}_{}_LOD{}_".format(self.megascans_asset_name, get_resolution_str(bake_resolution_int), self.polyreduce_percentage_float)
        export_path = lod_and_bake.Bake.get_export_path(self.megascans_asset_folder_path, export_name_prefix)
        map_name_and_export_paths_dict = lod_and_bake.Bake.get_map_name_and_export_paths_dict(self.maps_to_bake_dict, self.megascans_asset_folder_path, export_name_prefix)

        return export_name_prefix, export_path, map_name_and_export_paths_dict

    def make_general_bake_object(self):
        general_bake_object = lod_and_bake.Bake(self.highpoly_path, self.customlod_path, self.maps_to_bake_dict, 0, 0,
                                                self.megascans_asset_folder_path)  # have the resolution x and y be 0 for now, and have export_path be the default for now (both things changed below)
        general_baketexture_node, general_camera_node = general_bake_object.create_in_houdini(self.fix_subnet_node)

        # yes, I could assign "@bake_resolution_x_and_y" to a variable to stop me having to type it out, but I think it's more clear this way
        general_baketexture_node.parm("vm_uvunwrapresx").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvunwrapresy").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvoutputpicture1").setExpression("@export_path")
        general_camera_node.parm("resx").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)
        general_camera_node.parm("resy").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)

        return general_baketexture_node,  general_camera_node



    def bake_custom_maps_and_update_reader_nodes_accordingly(self):
        # Get information about chosenres
        chosenres_bake_resolution_x_and_y = get_resolution_int(self.chosen_bake_resolution_str)
        chosenres_export_name_prefix, chosenres_export_path, self.chosenres_map_name_and_export_paths_dict = self.get_bake_info(chosenres_bake_resolution_x_and_y)

        # Create a GENERAL Bake object to use in the PDG later i.e. hack it so that resolution_x and resolution_y are "@bake_resolution_x_and_y" and so export_path is "@export_path"
        general_baketexture_node,  general_camera_node = self.make_general_bake_object()


        # Create PDG network, modify reader nodes, bake and add event handlers (exact instructions of the aforementioned on if using temp resolution)
        topnet_node = self.fix_subnet_node.createNode("topnet", "topnet")
        string_processor(topnet_node, "cwedge-wedge i0 cropfetch-ropfetch i0")

        ropfetch_node = hou.node(topnet_node.path() + "/ropfetch")  # as per created above (needed to execute)
        ropfetch_node.parm("roppath").set(general_baketexture_node.path())

        pdg_graph_context = ropfetch_node.getPDGGraphContext()  # could call this method on the topnet or wedge and it'd give the same context

        if self.use_temp_resolution_bool == True: # means you must have reader nodes
            # Get information about lowres
            lowres_bake_resolution_x_and_y = 1024  # change to what you like
            lowres_export_name_prefix, lowres_export_path, lowres_map_name_and_export_paths_dict = self.get_bake_info(lowres_bake_resolution_x_and_y)

            # Modify megascans reader nodes to lowres
            self.update_megascans_material_reader_nodes_export_paths(lowres_map_name_and_export_paths_dict)

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
            if self.make_reader_nodes_bool == True:
                self.update_megascans_material_reader_nodes_export_paths(self.chosenres_map_name_and_export_paths_dict)  # doing before

            # Configure pdg
            string_processor(topnet_node,
                             "@ewedge!wedgecount:1!wedgeattributes:2!name1:export_path!type1:4!values1:1!strvalue1_1:{}!name2:bake_resolution_x_and_y!type2:2!wedgetype2:2!values2:1!intvalue2_1:{}".format(
                                 chosenres_export_path.replace(" ", "%20"),
                                 chosenres_bake_resolution_x_and_y))  # set parameters on wedge node

            # Add event handlers to pdg graph context (this event handler notifies the user cooking is done)
            pdg_graph_context.addEventHandler(self.cook_event_handler_two, pdg.EventType.CookComplete, True)  # ^ ditto

        # Save and Cook PDG
        hou.hipFile.save()  # executeGraph uses the last saved hipfile version
        ropfetch_node.executeGraph(False, False, False, False)  # note that pdg/topnets render by behind-the-scenes opening the latest save of houdini with the corresponding work item's attributes and rendering there


        # notify user (neilson's heuristics)
        if self.use_temp_resolution_bool == True:
            MegascansAsset.display_message("Baking out temporary 1K resolution maps, and your chosen {chosen_bake_resolution_str} resolution maps now.\n\nYour reader nodes have been created and they are set to use the paths of the 1K maps. Once your {chosen_bake_resolution_str} resolution maps have finished baking, you'll be asked if you want to swap over your reader nodes to these.".format(chosen_bake_resolution_str = self.chosen_bake_resolution_str))
            # ^ assuming 1K will bake out first, otherwise the wording needs to change
        else:
            if self.make_reader_nodes_bool == True:
                MegascansAsset.display_message("Baking out {} resolution maps now, you will be notified when they're done.\n\nYour reader nodes have been created, and they are using the paths of these maps (even though they're not baked yet).".format(self.chosen_bake_resolution_str))
            else:
                MegascansAsset.display_message("Baking out {} resolution maps now, you will be notified when they're done.".format(self.chosen_bake_resolution_str))


    def put_all_nodes_created_in_a_network_box(self):
        """
        put all nodes created in to a network box

        (a hacky way, using the fact that all the nodes created are reader nodes or connected to reader nodes)
        """
        material_builder_node = self.asset_material_object.get_material_builder_node()

        network_box = material_builder_node.createNetworkBox()
        network_box.setComment("Custom baked maps' reader nodes (and their connected nodes)")
        for map_name in self.map_name_and_reader_node_dict.keys():
            reader_node_name, reader_node_param_name = self.map_name_and_reader_node_dict[map_name]
            reader_node = hou.node(material_builder_node.path() + "/" + reader_node_name)
            recursively_add_to_network_box(network_box, reader_node)
        network_box.fitAroundContents()

        a_vector = hou.Vector2(2, 0)  # hard coded (the size needed to fit the comment above)
        network_box.resize(a_vector)

        self.organise_megascans_asset_subnet_and_hide_fix_subnet()  # layout all the necessary things


    def execute_custom_lod_and_baking(self, polyreduce_percentage_float, maps_to_bake_dict, chosen_bake_resolution_str, make_reader_nodes_bool, use_temp_resolution_bool):
        self.fix_subnet_node = self.megascans_asset_subnet_node.createNode("subnet", "Megascans_Custom_LOD_and_Baking_Subnet")  # Feel free to change name

        self.polyreduce_percentage_float = polyreduce_percentage_float
        self.maps_to_bake_dict = maps_to_bake_dict
        self.chosen_bake_resolution_str = chosen_bake_resolution_str
        self.make_reader_nodes_bool = make_reader_nodes_bool
        self.use_temp_resolution_bool = use_temp_resolution_bool

        if chosen_bake_resolution_str == "1K":  # simplifies things, and the "1K" is hardcoded everywhere (gross)
            use_temp_resolution_bool = False
        if self.make_reader_nodes_bool == False: # the UI enforces this, this is just fool proofing
            self.use_temp_resolution_bool = False

        template_map_name_and_node_setup_dict = self.asset_material_object.get_template_map_name_and_node_setup_dict() # returns a copy
        self.map_name_and_node_setup_dict = self.get_map_name_and_node_setup_dict(template_map_name_and_node_setup_dict)
        self.map_name_and_reader_node_dict = self.get_map_name_and_reader_node_dict("{export_path}")  # reader nodes are nodes which have "{export_path}"

        # Step a
        self.customlod_path = self.make_custom_lod()

        # Step bi
        self.asset_material_object.configure_megascans_subnet(self)

        # Step bii
        if len(self.map_name_and_node_setup_dict.keys()) == 0:
            self.organise_megascans_asset_subnet_and_hide_fix_subnet()
            self.all_done_message()
            return  # they didn't ask for any maps to be baked

        if self.make_reader_nodes_bool == True: # elegant -- however, should probably not go to the effort of making map_name_and_node_setup_dict and map_name_and_reader_node_dict
            self.add_node_setup_to_material_node()

        # Step c
        self.bake_custom_maps_and_update_reader_nodes_accordingly()

        if self.make_reader_nodes_bool == True:
            self.put_all_nodes_created_in_a_network_box()

def main():
    selected_node_list = hou.selectedNodes()
    if len(selected_node_list) != 1:
        raise MegascansAsset.display_message("Zero or Multiple nodes selected. Are you sure you've selected a single Megascans Asset Subnetwork?")

    megascans_asset_subnet = selected_node_list[0] # assuming that it's a megascans asset (checking below)

    try:
        megascans_asset_object = MegascansAsset(megascans_asset_subnet)
    except Exception as exception:
        MegascansAsset.display_message("Error Occured:\n\n{}\n\nPlease try again".format(exception))
        raise SystemExit

    megascans_asset_subnet.setDisplayFlag(True)  # baking requires its display flag is visible

    ui = megascans_custom_lod_and_bake_ui.MegascansFixerDialog(megascans_asset_object)
    ui.show() # passing control off to the UI
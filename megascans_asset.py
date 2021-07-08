import hou
import pdg

from helper_functions import *
from big_framework import *

import megascans_custom_lod_and_bake_ui
import renderer_material
import lod_and_bake

# regarding reloading, so Houdini doesn't use the precompiled versions of these (in case there's a change to any of these)

class MegascansAsset:
    """
    This stores information about a Megascans Asset (the subnet in Houdini, and its files' location on disk),
    and has cool methods - there's only one cool method so far "execute_custom_lod_and_baking" and helper methods for that
    """

    @staticmethod # need not have an instance to use, perhaps this should just be a function (i.e. argument could be made it shouldn't be in MegascansAsset?)
    def display_custom_lod_and_baking_tool_message(message_string, **kwargs):
        """
        Same functionality as hou.ui.displayMessage, just ensures title (feel free to change, to ensure different things)
        """
        return hou.ui.displayMessage(message_string, title = "Megascans Custom LOD & Baking Tool", **kwargs)

    @staticmethod
    def all_done_message(self):
        MegascansAsset.display_custom_lod_and_baking_tool_message("All done! Seriously, this shelf tool has finished. Thanks for using me")

    @staticmethod
    def count_of_maps_to_bake(maps_to_bake_dict):  # more useful than a method "is_zero_maps_to_bake"
        count_of_maps_to_bake = 0
        for map_name in maps_to_bake_dict:
            bake_bool = maps_to_bake_dict[map_name]
            if bake_bool == True:
                count_of_maps_to_bake += 1

        return count_of_maps_to_bake

    @staticmethod
    def get_map_name_and_node_setup_dict(template_map_name_and_node_setup_dict, maps_to_bake_dict):
        """
        Modify map_name_and_node_setup_dict to only have the maps we're baking
        """

        maps_not_to_bake_list = list() # these will be popped from template_map_name_and_node_setup_dict (cannot pop from a dict you're iterating in, thanks to Python3)
        for map_name in template_map_name_and_node_setup_dict.keys():
            bake_bool = self.maps_to_bake_dict[map_name]
            if bake_bool == False:
                maps_not_to_bake_list.append(map_name) # pops keys

        for map_name in maps_not_to_bake_list:
            template_map_name_and_node_setup_dict.pop(map_name)

        print(template_map_name_and_node_setup_dict)

        return template_map_name_and_node_setup_dict


    def foolproof_reader_nodes_and_temp_resolution_bool(self, make_reader_nodes_bool, use_temp_resolution_bool):  # could make 'foolproof_execute_custom_lod_and_baking', but for now doing this only
        # if use_temp_resolution_bool is True, make_reader_nodes_bool must be True (the former "implies" the latter, lol), which means:
        if make_reader_nodes_bool == False:
            use_temp_resolution_bool == False

        if temp_resolution_bool == True:
            make_reader_nodes_bool = True

        # if make_reader_nodes_bool is True (note this means that it's possible for temp_resolution_bool to be True), then we must "know" about it (TODO: explain)
        if (make_reader_nodes_bool == True and self.asset_material_object is None) == False:  # lol PEP8
            # one solution is to do the following (it might be the only solution?)
            make_reader_nodes_bool = False
            make_temp_resolution_bool = False

        return make_reader_nodes_bool, make_temp_resolution_bool

    def make_custom_lod(self, housing_node, polyreduce_percentage_float): # housing_node, as in, where the nodes to make the LOd should go
        customlod_basename = "{}_LOD{}percent_custom.fbx".format(self.megascans_asset_name, polyreduce_percentage_float)
        customlod_path = os_path_join_for_houdini(self.megascans_asset_folder_path, desired_customlod_basename)

        if os.path.exists(customlod_path) == False: # lol PEP 8
            MegascansAsset.display_custom_lod_and_baking_tool_message("Baking out {} percent LOD now (this should freeze Houdini)".format(polyreduce_percentage_float))

            a_lod_object = lod_and_bake.LOD(self.highpoly_path, polyreduce_percent_float, customlod_path)
            a_lod_object.create_in_houdini(housing_node)
            a_lod_object.execute_in_houdini()
        else:
            MegascansAsset.display_custom_lod_and_baking_tool_message("A LOD that's {} percent already exists at the following path (more specifically, a file with exists with the identical name and path where we expected to save an LOD of this percentage, had we of baked it out with this tool):\n '{}'\n\nUsing this instead of re-baking".format(polyreduce_percentage_float))

        self.file_node.parm("file").set(customlod_path)
        return customlod_path


    def organise_megascans_asset_subnet(self, custom_lod_and_baking_subnet_node):
        # note, to render (e.g. via a PDG) the below needs to be True. However, since a PDG's rendering uses a previously saved hipfile with this True, it's fine to set this to False
        custom_lod_and_baking_subnet_node.setDisplayFlag(False)

        # set_network_editor_to_view_node(self.megascans_asset_subnet_node)
        # ^ NVM actually nice not to do this; having the user see the topnet is a nice way to show them stuff is rendering

        # Layout material builder node (maybe this should be somewhere else)
        if self.asset_material_object is not None:
            self.asset_material_object.get_material_builder_node().layoutChildren()

        # Layout the custom lod and baking subnet
        custom_lod_and_baking_subnet_node.layoutChildren()

        # Layout the megascans asset subnet (whose child is the custom lod and baking subnet)
        self.megascans_asset_subnet_node.layoutChildren()


    def get_bake_info(self, bake_resolution_int):
        export_name_prefix = "{}_{}_LOD{}_".format(self.megascans_asset_name, get_resolution_str(bake_resolution_int), self.polyreduce_percentage_float)
        export_path = lod_and_bake.Bake.get_export_path(self.megascans_asset_folder_path, export_name_prefix)
        map_name_and_export_paths_dict = lod_and_bake.Bake.get_map_name_and_export_paths_dict(self.maps_to_bake_dict, self.megascans_asset_folder_path, export_name_prefix)

        return export_name_prefix, export_path, map_name_and_export_paths_dict

    def make_general_bake_object(self, housing_node): # housing_node, as in where the baking nodes are created
        general_bake_object = lod_and_bake.Bake(self.highpoly_path, self.customlod_path, self.maps_to_bake_dict, 0, 0, self.megascans_asset_folder_path)  # have the resolution x and y be 0 for now, and have export_path be the default for now (both things changed below)
        general_baketexture_node, general_camera_node = general_bake_object.create_in_houdini(housing_node)

        # yes, I could assign "@bake_resolution_x_and_y" to a variable to stop repeated code, but I think it's more clear this way
        general_baketexture_node.parm("vm_uvunwrapresx").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvunwrapresy").setExpression("@bake_resolution_x_and_y")
        general_baketexture_node.parm("vm_uvoutputpicture1").setExpression("@export_path")
        general_camera_node.parm("resx").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)
        general_camera_node.parm("resy").setExpression("@bake_resolution_x_and_y", hou.exprLanguage.Hscript)

        return general_baketexture_node,  general_camera_node

    def add_node_setup_to_material_node(self, map_name_and_node_setup_dict):
        """
        Add node setups, as described in map_name_and_node_setup_dict to the rs_material_builder node
        """
        material_builder_node = self.asset_material_object.get_material_builder_node()

        for map_name in map_name_and_node_setup_dict.keys():  # have to get keys again since they've changed
            try:
                node_setup_string = map_name_and_node_setup_dict[map_name]
            except KeyError:  # only error it could be
                raise Exception("map_name_and_node_setup_dict does not contain the node setup for map_name: {}".format(map_name))
            else:
                a_export_path = "waiting for maps to be rendered"
                node_setup_string = node_setup_string.format(export_path = a_export_path.replace(" ", "%20"))  # using format instead of replace, just for the sake of that's how I would've done the above

                string_processor(material_builder_node, node_setup_string)

    def get_map_name_and_reader_node_dict(self):  # could hardcode parameter_content to be "{export_path}"
        """
        Given a map_name_and_node_setup_dict, identify the reader nodes (nodes which have a certain parameter content) and their reader param (node with that corresponding parameter content) -- and put in a dict with map name as key

        Currently, this 'parameter content' is "{export_path}", but feel free to change how reader nodes / reader params are identified better
        """

        param_content = "{export_path}"

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

    def update_megascans_material_reader_nodes_export_paths(self, map_name_and_reader_node_dict, map_name_and_export_paths_dict): # note this assumes self.asset_material_object is not None (specifically, a subclass of RendererMaterial)
        """
        This function modifies the reader nodes in this node setup: updating their "reader parameter's" to the export paths given.
        """
        for map_name in map_name_and_reader_node_dict.keys():
            reader_node_name, reader_node_param_name = map_name_and_reader_node_dict[map_name]
            export_path = map_name_and_export_paths_dict[map_name]

            # doing this way, rather than using string processor (as the latter doesn't simplify things)
            material_builder_node = self.asset_material_object.get_material_builder_node()
            reader_node = hou.node("{}/{}".format(material_builder_node.path(), reader_node_name))
            # print(reader_node_name, reader_node_param_name)
            reader_node.parm(reader_node_param_name).set(export_path)

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


    def bake_custom_maps_and_setup_reader_nodes_accordingly(self, custom_lod_and_baking_subnet_node, make_reader_nodes_bool, use_temp_resolution_bool, chosen_bake_resolution_str):\
        #--- Foolproofing. Note, this is already done in execute_custom_lod_and_baking, doing it here in case this method is called without this
        make_reader_nodes_bool, use_temp_resolution_bool = self.foolproof_reader_nodes_and_temp_resolution_bool(make_reader_nodes_bool, use_temp_resolution_bool)

        #--- Get information about chosen resolution maps
        chosenres_bake_resolution_x_and_y = get_resolution_int(chosen_bake_resolution_str)
        chosenres_export_name_prefix, chosen_res_export_path, chosenres_map_name_and_export_paths_dict = self.get_bake_info(chosenres_bake_resolution_x_and_y)

        #--- Instantiate a GENERAL Bake object (which creates nodes in the passed node, custom_lod_and_baking_subnet_node) to use in the PDG later. Note, 'GENERAL' means to hack a Bake object so that resolution_x and resolution_y are "@bake_resolution_x_and_y" and export_path is "@export_path")
        general_baketexture_node, general_camera_node = self.make_general_bake_object(custom_lod_and_baking_subnet_node)

        #--- Create a PDG network which uses the baketexture node and camera node created above
        topnet_node = custom_lod_and_baking_subnet_node.createNode("topnet", "topnet")
        ropfetch_node_name = "ropfetch"
        string_processor(topnet_node, "cwedge-wedge i0 cropfetch-{} i0".format(ropfetch_node_name))

        ropfetch_node = hou.node("{}/{}".format(topnet_node.path(), ropfetch_node_name))
        ropfetch_node.parm("roppath").set(general_baketexture_node.path()) # yes, could use big framework, but both are one line, and this is more clearer anyway

        pdg_graph_context = ropfetch_node.getPDGGraphContext()


        #--- Make reader nodes, if necessary
        if make_reader_nodes_bool == True: # note reader nodes, more like "make nodes, and some of them will be reader nodes". I could probably work on choice of words better
            template_map_name_and_node_setup_dict = self.asset_material_object.get_template_map_name_and_node_setup_dict()
            map_name_and_node_setup_dict = self.get_map_name_and_node_setup_dict(template_map_name_and_node_setup_dict, maps_to_bake_dict)
            self.add_node_setup_to_material_node(map_name_and_node_setup_dict)

            # of everything described in map_name_and_node_setup_dict, get reader nodes and reader params (in a dict with key: map_name, and corresponding value: reader nodes and reader parms)
            map_name_and_reader_node_dict = self.get_map_name_and_reader_node_dict(map_name_and_node_setup_dict) # for later use

            self.put_all_material_nodes_created_in_a_network_box() # random last minute thing, which is nice to have


        #--- Setup reader nodes, if necessary, and configure PDG
        if use_temp_resolution_bool == True: # note this means make_reader_nodes_bool == True (note, this is enforced in 'foolproofing')
            # get tempres information
            tempres_bake_resolution_x_and_y = 1024  # change to what you like
            tempres_export_name_prefix, tempres_export_path, tempres_map_name_and_export_paths_dict = self.get_bake_info(tempres_bake_resolution_x_and_y)

            # set reader nodes to tempres maps
            self.update_megascans_material_reader_nodes_export_paths(map_name_and_reader_node_dict, tempres_map_name_and_export_paths_dict)

            # configure PDG to bake tempres and then chosenres (via setting parameters on wedge node)
            string_processor(topnet_node, "@ewedge!wedgecount:2!wedgeattributes:2!name1:export_path!type1:4!values1:2!strvalue1_1:{}!strvalue1_2:{}!name2:bake_resolution_x_and_y!type2:2!wedgetype2:2!values2:2!intvalue2_1:{}!intvalue2_2:{}".format(lowres_export_path.replace(" ", "%20"), chosenres_export_path.replace(" ", "%20"), lowres_bake_resolution_x_and_y, chosenres_bake_resolution_x_and_y))

            # add event handler that asks if the user if they want to change reader nodes to chosenres once all PDG cooking is complete (i.e. chosenres will be finished cooking)
            pdg_graph_context.addEventHandler(self.cook_event_handler_one, pdg.EventType.CookComplete, True)  # the True means that a handler will be passed to the event handler, as well as the event
        else:
            if make_reader_nodes_bool == True:
                # set reader nodes to chosenres maps
                self.update_megascans_material_reader_nodes_export_paths(map_name_and_reader_node_dict, chosenres_map_name_and_export_paths_dict)

            # configure PDG to bake chosenres (via setting parameters on wedge node). Yes, because it's only baking one thing, PDG not necessary - but using PDG anyway because it allows us to use event handlers when maps have stopped baking
            string_processor(topnet_node, "@ewedge!wedgecount:1!wedgeattributes:2!name1:export_path!type1:4!values1:1!strvalue1_1:{}!name2:bake_resolution_x_and_y!type2:2!wedgetype2:2!values2:1!intvalue2_1:{}".format(chosenres_export_path.replace(" ", "%20"), chosenres_bake_resolution_x_and_y))

            # add event handler that notifies user once PDG cooking is complete
            pdg_graph_context.addEventHandler(self.cook_event_handler_two, pdg.EventType.CookComplete, True) # ^ ditto to above event handler


        # --- Set display flags to visible, save hip file, and execute PDG
        # Note: when PDG is executed, behind the scenes it launches the latest save of the Houdini project, and rendering is done on that. Also note that for rendering (PDG at least), it needs to be visible
        custom_lod_and_baking_subnet_node.setDisplayFlag(True) # should be true, if made via execute_custom_lod_and_baking
        self.megascans_asset_subnet_node.setDisplayFlag(True) # should be true already, thanks to __init__
        hou.hipFile.save()  # executeGraph uses the last saved hipfile version
        ropfetch_node.executeGraph(False, False, False, False)  # note that pdg/topnets render by behind-the-scenes opening the latest save of houdini with the corresponding work item's attributes and rendering there


        # --- Tell user what is happening
        if self.use_temp_resolution_bool == True:
            MegascansAsset.display_message("Baking out temporary 1K resolution maps, and your chosen {chosen_bake_resolution_str} resolution maps now.\n\nYour reader nodes have been created and they are set to use the paths of the 1K maps. Once your {chosen_bake_resolution_str} resolution maps have finished baking, you'll be asked if you want to swap over your reader nodes to these.".format(chosen_bake_resolution_str = self.chosen_bake_resolution_str))
            # ^ assuming 1K will bake out first, otherwise the wording needs to change
        else:
            if self.make_reader_nodes_bool == True:
                MegascansAsset.display_message("Baking out {} resolution maps now, you will be notified when they're done.\n\nYour reader nodes have been created, and they are using the paths of these maps (even though they're not baked yet).".format(self.chosen_bake_resolution_str))
            else:
                MegascansAsset.display_message("Baking out {} resolution maps now, you will be notified when they're done.".format(self.chosen_bake_resolution_str))



    def execute_custom_lod_and_baking(self, polyreduce_percentage_float, maps_to_bake_dict, chosen_bake_resolution_str, make_reader_nodes_bool, use_temp_resolution_bool):
        custom_lod_and_baking_subnet_node = self.megascans_asset_subnet_node.createNode("subnet", "Megascans_Custom_LOP_and_Baking_Subnet") # feel free to change node

        #------ Foolproofing. Could throw an error but would rather fix mistake and continue. Note, the UI enforces this, but just in case this is called without the UI (or the UI is broken)
        make_reader_nodes_bool, use_temp_resolution_bool = self.foolproof_reader_nodes_and_temp_resolution_bool(make_reader_nodes_bool, use_temp_resolution_bool)


        # ------ Step a (make Custom LOD)
        # Note, if a Custom LOD already exists with this percentage from a previous use of this tool, this is used instead of baking out a new one.
        customlod_path = self.make_custom_lod(custom_lod_and_baking_subnet_node, polyreduce_percentage_float)


        #------ Step bi (configure Megascans Asset Subnet for anything Megascans missed, if possible)
        # Note, 'if possible' meaning that we have a RenderMaterial subclass of it (and an instance of this was returned during MegascansAsset's __init__) which represents the material used for this megascans asset,
        # Note, a RenderMaterial subclass has the method 'configure_megascans_asset_subnet' which has instructions on how to fix a Megascan Asset subnet's improper configurations
        if self.asset_material_object is not None:
            self.asset_material_object.configure_megascans_asset_subnet(self)


        #------ Step bii (if no maps to bake, tell the user, give 'all done' message, and then return). Perhaps this should be incorporated into step c (moreover, bake_custom_maps_accordingly())
        count_of_maps_to_bake =  MegascansAsset.count_of_maps_to_bake(maps_to_bake_dict)
        if count_of_maps_to_bake == 0:
            MegascansAsset.display_custom_lod_and_baking_tool_message("Note, zero maps have been selected to be baked")
            self.organise_megascans_asset_subnet()
            self.all_done_message()
            return


        #------ Step c (bake custom maps using Custom LOD)
        self.bake_custom_maps_and_setup_reader_nodes_accordingly() # 'accordingly', as in, deals with make reader nodes and baking temp resolution maps, if variables make_reader_nodes_bool and temp_resolution_bool say so, respectively

        # organise
        self.organise_megascans_asset_subnet()


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
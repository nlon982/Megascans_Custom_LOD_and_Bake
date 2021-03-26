import huilib
import lod_and_bake
import re

import hdefereval

#-------------- so houdini doesn't use the precompiled (copy and pasted code: gross!)
try:
    reload # Python 2.7 has this
except:
    try:
        from importlib import reload # Python 3.4+ has this
    except:
        from imp import reload # Python 3.0 - 3.3 has this. It's deprecated in Python 3.4+, so although it probably can be used, preferred to use the above if available (hence why this is last)

reload(huilib)
#--------------
from huilib import *

def get_valid_name(name): # works for Houdini name and Houdini ui name
    return re.sub("[^0-9a-zA-Z\.]+", "_", name).lower() # the lower is something nice but extra

class MegascansFixerDialog(HDialog):
        def __init__(self, megascans_asset_object):
                super(MegascansFixerDialog, self).__init__("Namegoeshere", "Megascans Custom LOD & Baking Tool")
                self.megascans_asset_object = megascans_asset_object # Note, this importantly calls the 'execute_fix' method when the go button is pressed
                # ^ continued: otherwise, use however you please (perhaps have it show the path of the megascans asset). 


                self.setWindowLayout('vertical')
                self.setWindowAttributes(stretch = True, margin = 0.1, spacing = 0.1, min_width = 5)

                # using conventions that i'm coming up with to keep this organised
                # assigning a Gadget to self.variablename (a personalised variable name too) when I know i'll access it later
                
                #--------------Prep
                self.displacement_type_menu_list = ["Displacement", "Vector Displacement", "Tangent-Space Vector Displacement"]

                self.map_resolution_menu_list = ["8K", "4K", "2K", "1K"]


                #-------------- General
                
                sep = HSeparator()
                sep.setAttributes(look = 'bevel')

                #-------------- Header
                label0 = HLabel("Megascans Asset:")
                self.addGadget(label0)

                


                header_row_layout = HRowLayout()
                self.addLayout(header_row_layout)

                space_column_layout0 = HColumnLayout()
                space_column_layout0.setAttributes(width = 0.25)
                header_row_layout.addLayout(space_column_layout0)

                other_column_layout0 = HColumnLayout()
                header_row_layout.addLayout(other_column_layout0)

                label0point1 = HLabel("Subnet: {}".format(self.megascans_asset_object.megascans_asset_subnet_node.path()))
                other_column_layout0.addGadget(label0point1)

                label0point2 = HLabel("Location on disk: {}".format(megascans_asset_object.megascans_asset_folder_path))
                other_column_layout0.addGadget(label0point2)


                asset_material_object = megascans_asset_object.asset_material_object

                renderer_name = ""
                if asset_material_object is not None:
                        renderer_name = asset_material_object.get_renderer_name()

                if renderer_name != "Redshift": # temporary
                        renderer_name = "Not Redshift"

                label0point3 = HLabel("Renderer: {}".format(renderer_name))
                other_column_layout0.addGadget(label0point3)

                self.addGadget(sep)

                #-------------- Custom LOD options
                label1 = HLabel("Custom LOD options:")
                self.addGadget(label1)
                

                lod_options_row_layout = HRowLayout()
                self.addLayout(lod_options_row_layout)
                
                
                space_column_layout1 = HColumnLayout()
                space_column_layout1.setAttributes(width = 0.25)
                lod_options_row_layout.addLayout(space_column_layout1)
                            
                text_column_layout1 = HColumnLayout()
                text_column_layout1.setAttributes(width = 1.5)
                lod_options_row_layout.addLayout(text_column_layout1)

                other_column_layout1 = HColumnLayout()
                lod_options_row_layout.addLayout(other_column_layout1)
                

                #space_column_layout1
                space_label1 = HLabel("")
                space_column_layout1.addGadget(space_label1)    
                
                #text_column_layout1
                text_label1 = HLabel("Polyreduce Percentage:")
                text_column_layout1.addGadget(text_label1)
                
                #other_column_layout1
                self.polyreduce_percentage_slider = HFloatSlider("polyreduce_percentage_slider", "") # let's see if that works
                self.polyreduce_percentage_slider.setRange((0, 100))
                self.polyreduce_percentage_slider.setValue(50)
                self.polyreduce_percentage_slider.lockRange()
                other_column_layout1.addGadget(self.polyreduce_percentage_slider)

                self.addGadget(sep)
                
                #-------------- Displacement Baking options (everything layout/widget without a personalised baking name has '2' on it)
                label2 = HLabel("Displacement Maps to Bake:")
                self.addGadget(label2)
                

                displacement_baking_options_row_layout = HRowLayout()
                self.addLayout(displacement_baking_options_row_layout)
                
                
                space_column_layout2 = HColumnLayout()
                space_column_layout2.setAttributes(width = 0.25)
                displacement_baking_options_row_layout.addLayout(space_column_layout2)
                            
                other_column_layout2 = HColumnLayout()
                displacement_baking_options_row_layout.addLayout(other_column_layout2)
                
                
                #space_column_layout2
                space_label2 = HLabel("")
                space_column_layout2.addGadget(space_label2)    
                
                #other_column_layout2
                self.displacement_types_to_bake_checkbox_dict = dict()
                for map_name in self.displacement_type_menu_list:
                    checkbox_name = get_valid_name(map_name) # checkbox label is map_name
                    a_checkbox = HCheckbox(checkbox_name, map_name)
                    a_checkbox.setValue("0") # this is the fix re: huilib having problems with the default value

                    other_column_layout2.addGadget(a_checkbox)
                        
                    self.displacement_types_to_bake_checkbox_dict[map_name] = a_checkbox # save for a rainy day

                
                # sep
                self.addGadget(sep)

                #-------------- Other maps to bake
                label3 = HLabel("Other Maps to Bake:")
                self.addGadget(label3)


                other_maps_row_layout = HRowLayout()
                self.addLayout(other_maps_row_layout)


                space_column_layout3 = HColumnLayout()
                space_column_layout3.setAttributes(width = 0.25)
                other_maps_row_layout.addLayout(space_column_layout3)

                other_column_layout3 = HColumnLayout()
                other_maps_row_layout.addLayout(other_column_layout3) 


                other_maps_collapser_layout = HCollapserLayout(label = "Collapser", layout = "vertical")
                other_column_layout3.addLayout(other_maps_collapser_layout)


                map_names_list = list(lod_and_bake.Bake.map_name_and_houdini_parameter_name_dict.keys())
                for displacement_map_name in self.displacement_type_menu_list: # i.e. delete "Displacement", "Vector Displacement", "Tangent-Space Vector Displacement" since it's already in above
                    map_names_list.remove(displacement_map_name)

                self.other_maps_to_bake_checkbox_dict = dict()
                for map_name in map_names_list:
                    checkbox_name = get_valid_name(map_name) # checkbox label is map_name
                    a_checkbox = HCheckbox(checkbox_name, map_name)
                    a_checkbox.setValue("0") # this is the fix re: huilib having problems with the default value

                    other_maps_collapser_layout.addGadget(a_checkbox)
                        
                    self.other_maps_to_bake_checkbox_dict[map_name] = a_checkbox # save for a rainy day

                #sep
                self.addGadget(sep)

                #-------------- Other baking options
                label4 = HLabel("Baking options:")
                self.addGadget(label4)


                other_baking_options_row_layout = HRowLayout()
                self.addLayout(other_baking_options_row_layout)


                space_column_layout4 = HColumnLayout()
                space_column_layout4.setAttributes(width = 0.25)
                other_baking_options_row_layout.addLayout(space_column_layout4)


                other_column_layout4 = HColumnLayout()
                other_baking_options_row_layout.addLayout(other_column_layout4) 

                self.map_resolution_menu = HStringMenu("map_resolution_menu", "Bake Resolution", self.map_resolution_menu_list)
                other_column_layout4.addGadget(self.map_resolution_menu)


                # sep
                self.addGadget(sep)

                # -------------- More automation options
                label5 = HLabel("More automation options (currently for Redshift only):")
                self.addGadget(label5)

                more_automation_options_row_layout = HRowLayout()
                self.addLayout(more_automation_options_row_layout)

                space_column_layout5 = HColumnLayout()
                space_column_layout5.setAttributes(width = 0.25)
                more_automation_options_row_layout.addLayout(space_column_layout5)

                other_column_layout5 = HColumnLayout()
                more_automation_options_row_layout.addLayout(other_column_layout5)

                self.make_reader_nodes_checkbox = HCheckbox("make_reader_nodes_checkbox", "Automatically create reader nodes, and update export paths of those reader nodes once maps baked (this must be enabled to use the below)")
                self.make_reader_nodes_checkbox.setValue("0")  # because it's not set to ?anything? by default (but should be set to 0 as that corresponds to unticked - so doing it here), which is messed up

                #label5point1 = HLabel("To enable the following, the above must be enabled:")

                self.use_temp_resolution_checkbox = HCheckbox("use_temp_resolution_checkbox", "Temporarily bake 1K Resolution and set reader nodes to this, while the above 'Bake Resolution' is baked (does nothing if 'Bake Resolution' is 1K)")
                self.use_temp_resolution_checkbox.setValue("0")  # ^ ditto

                if renderer_name != "Redshift":
                        self.make_reader_nodes_checkbox.setEnabled(False)
                        self.use_temp_resolution_checkbox.setEnabled(False)

                self.use_temp_resolution_checkbox.setEnabled(False) # only if make_reader_nodes_checkbox is ticked, then this is enabled True

                other_column_layout5.addGadget(self.make_reader_nodes_checkbox)
                #other_column_layout5.addGadget(label5point1)
                other_column_layout5.addGadget(self.use_temp_resolution_checkbox)

                # sep
                self.addGadget(sep)

                
                # add columnslayouts to rowlayouts

                #-------------- Go Button
                bottom_row_layout = HRowLayout()
                self.addLayout(bottom_row_layout)

                
                self.go_button = HButton('go_button', "Go!")
                bottom_row_layout.addGadget(self.go_button)
                
                #-------------- "connect call backs"
                self.go_button.connect(self.cb_go_button) # close is an inherited method
                self.make_reader_nodes_checkbox.connect(self.cb_make_reader_nodes_checkbox)
                                
                #-------------- Initialize
                self.initUI()

        def cb_go_button(self):
                self.close()
                hdefereval.executeDeferred(self.get_information_ready_and_send_to_execute_fix) # "gets called after Houdini has done processing the queued UI events"  https://www.sidefx.com/forum/topic/23523/
                # ^ works perfectly for my purpose

        def cb_make_reader_nodes_checkbox(self):
                checkbox_value = self.make_reader_nodes_checkbox.isChecked()
                if checkbox_value == "0" or checkbox_value == 0:  # as below, I still don't know what's going on behind the scenes
                        self.use_temp_resolution_checkbox.setEnabled(False)
                else:
                        self.use_temp_resolution_checkbox.setEnabled(True)



        def get_information_ready_and_send_to_execute_fix(self):
                #-------------- Get information from UI (I have types in the variable names for the sake of clarity)
                polyreduce_percentage_float = float(self.polyreduce_percentage_slider.getValue())

                # add displacement & other ticked maps to maps_to_bake_dict
                # merge dicts (ugly way to do it?)
                all_maps_to_bake_checkbox_dict = dict()
                for map_name in self.displacement_types_to_bake_checkbox_dict:
                    all_maps_to_bake_checkbox_dict[map_name] = self.displacement_types_to_bake_checkbox_dict[map_name]
                for map_name in self.other_maps_to_bake_checkbox_dict:
                    all_maps_to_bake_checkbox_dict[map_name] = self.other_maps_to_bake_checkbox_dict[map_name]

                maps_to_bake_dict = lod_and_bake.Bake.maps_to_bake_dict_template.copy() # dictionaries are mutable, so need to make a copy as to not modify the original!
                for map_name in all_maps_to_bake_checkbox_dict.keys():
                    checkbox_value = all_maps_to_bake_checkbox_dict[map_name].isChecked() # like the above
                    if checkbox_value == "0" or checkbox_value == 0: # 0 corresponds to unticked, and 1 corresponds to ticked. I still don't know what's going on behind the scenes
                            bake_bool = False
                    else:
                            bake_bool = True
                    maps_to_bake_dict[map_name] = bake_bool

                # regarding resolution
                map_resolution_str = self.map_resolution_menu_list[self.map_resolution_menu.getValue()]


                make_reader_nodes_checkbox_value = self.make_reader_nodes_checkbox.getValue()
                if make_reader_nodes_checkbox_value == "0" or make_reader_nodes_checkbox_value == 0:
                        make_reader_nodes_bool = False
                else:
                        make_reader_nodes_bool = True

                use_temp_resolution_checkbox_value = self.use_temp_resolution_checkbox.isChecked()
                if use_temp_resolution_checkbox_value == "0" or use_temp_resolution_checkbox_value == 0:
                        use_temp_resolution_bool = False
                else:
                        use_temp_resolution_bool = True

                # for testing
                #message_string = "polyreduce percentage: {}\ndisplacement type: {}\nmap resolution: {}\nuse_temp_resolution: {}\n\nmaps_to_bake_dict: {}".format(polyreduce_percentage_float, displacement_type_str, map_resolution_str, use_temp_resolution_bool, maps_to_bake_dict)
                #hou.ui.displayMessage(message_string)

                # using displacement resolution as resolution for all maps you ask it to bake! I need to a discussion with Muggy on how it should be dealt with
                
                self.megascans_asset_object.execute_custom_lod_and_baking(polyreduce_percentage_float, maps_to_bake_dict, map_resolution_str, make_reader_nodes_bool, use_temp_resolution_bool)

                
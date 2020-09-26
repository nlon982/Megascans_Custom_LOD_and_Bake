from huilib import *
import lod_and_bake
import re

import hdefereval

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

                label0point1 = HLabel("Subnet: {}".format(self.megascans_asset_object.megascans_asset_subnet.path()))
                other_column_layout0.addGadget(label0point1)

                label0point2 = HLabel("Location on disk: {}".format(megascans_asset_object.megascans_asset_folder_path))
                other_column_layout0.addGadget(label0point2)

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
                
                self.use_temp_resolution_checkbox = HCheckbox("use_temp_resolution_checkbox", "Temporarily bake and use 1K Resoluton while above resolution is baked (does nothing if 1K is chosen above)")
                self.use_temp_resolution_checkbox.setValue("0") # because it's not set to ?anything? by default (but should be set to 0 as that corresponds to unticked - so doing it here), which is FUCKED
                other_column_layout4.addGadget(self.use_temp_resolution_checkbox)

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
                                
                #-------------- Initialize
                self.initUI()

        def cb_go_button(self):
                self.close()
                hdefereval.executeDeferred(self.get_information_ready_and_send_to_execute_fix) # "gets called after Houdini has done processing the queued UI events"  https://www.sidefx.com/forum/topic/23523/
                # ^ works perfectly for my purpose

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
                    if checkbox_value == "0" or checkbox_value == 0: # I still don't know what's going on behind the scenes
                            bake_bool = False
                    else:
                            bake_bool = True
                    maps_to_bake_dict[map_name] = bake_bool

                # regarding resolution
                map_resolution_str = self.map_resolution_menu_list[self.map_resolution_menu.getValue()]

                use_temp_resolution_checkbox_value = self.use_temp_resolution_checkbox.isChecked() # checkbox_value is "0" or "1", but I want it False or True for clarity
                if use_temp_resolution_checkbox_value == "0" or use_temp_resolution_checkbox_value == 0: # 0 corresponds to unticked, and 1 corresponds to ticked. As above, I still don't know what's going on behind the scenes
                        use_temp_resolution_bool = False
                else:
                        use_temp_resolution_bool = True

                # for testing
                #message_string = "polyreduce percentage: {}\ndisplacement type: {}\nmap resolution: {}\nuse_temp_resolution: {}\n\nmaps_to_bake_dict: {}".format(polyreduce_percentage_float, displacement_type_str, map_resolution_str, use_temp_resolution_bool, maps_to_bake_dict)
                #hou.ui.displayMessage(message_string)

                # using displacement resolution as resolution for all maps you ask it to bake! I need to a discussion with Muggy on how it should be dealt with
                
                self.megascans_asset_object.execute_fix(polyreduce_percentage_float, maps_to_bake_dict, map_resolution_str, use_temp_resolution_bool)

                
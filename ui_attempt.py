from huilib import *
import lod_and_bake
import re

import time

import threading

def get_valid_name(name): # works for Houdini name and Houdini ui name
    return re.sub("[^0-9a-zA-Z\.]+", "_", name).lower() # the lower is something nice but extra

class MegascansFixerDialog(HDialog):
        def __init__(self, megascans_asset_object):
                super(MegascansFixerDialog, self).__init__("Namegoeshere", "Megascans Fixer")
                self.megascans_asset_object = megascans_asset_object # Note, this importantly calls the 'execute_fix' method when the go button is pressed
                # ^ continued: otherwise, use however you please (perhaps have it show the path of the megascans asset). 


                self.setWindowLayout('vertical')
                self.setWindowAttributes(stretch = True, margin = 0.1, spacing = 0.1, min_width = 5)

                # using conventions that i'm coming up with to keep this organised
                # assigning a Gadget to self.variablename (a personalised variable name too) when I know i'll access it later
                
                # Prep

                self.displacement_type_menu_list = ["Displacement", "Vector Displacement"]
                self.displacement_resolution_menu_list = ["8K", "4K", "2K", "1K"]


                #-------------- General
                
                sep = HSeparator()
                sep.setAttributes(look = 'bevel')

                #-------------- Header
                label0 = HLabel("Megascans Asset Subnet: {}".format(self.megascans_asset_object.megascans_asset_subnet.path()))
                self.addGadget(label0)

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
                label2 = HLabel("Displacement Baking options:")
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
                self.displacement_type_menu = HStringMenu("displacement_type_menu", "Displacement Map Type", self.displacement_type_menu_list)
                other_column_layout2.addGadget(self.displacement_type_menu)

                self.displacement_resolution_menu = HStringMenu("displacement_resolution_menu", "Displacement Map Resolution", self.displacement_resolution_menu_list)
                other_column_layout2.addGadget(self.displacement_resolution_menu)
                
                self.use_temp_displacement_checkbox = HCheckbox("use_temp_displacement_checkbox", "Temporarily use 1K Resoluton while above is baked (does nothing if 1K is chosen above)")
                self.use_temp_displacement_checkbox.setValue("0") # because it's not set to ?anything? by default (but should be set to 0 as that corresponds to unticked - so doing it here), which is FUCKED
                other_column_layout2.addGadget(self.use_temp_displacement_checkbox)
                
                # sep
                self.addGadget(sep)

                #-------------- Other baking options
                label2 = HLabel("Other Baking options:")
                self.addGadget(label2)


                other_baking_options_row_layout = HRowLayout()
                self.addLayout(other_baking_options_row_layout)


                space_column_layout3 = HColumnLayout()
                space_column_layout3.setAttributes(width = 0.25)
                other_baking_options_row_layout.addLayout(space_column_layout3)


                other_baking_options_collapser_layout = HCollapserLayout(label = "", layout = "vertical")
                other_baking_options_row_layout.addLayout(other_baking_options_collapser_layout)

                
                map_names_list = list(lod_and_bake.Bake.map_name_and_houdini_parameter_name_dict.keys())
                map_names_list.remove("Displacement") # delete because used above
                map_names_list.remove("Vector Displacement") # ^
                map_names_list.remove("Tangent-Space Vector Displacement") # (TODO) the rest of my code hasn't accounted for Tangent-Space Vector Displacement, removing for now

                self.other_maps_to_bake_checkbox_dict = dict()
                for map_name in map_names_list:
                        checkbox_name = get_valid_name(map_name) # checkbox label is map_name
                        a_checkbox = HCheckbox(checkbox_name, map_name)
                        a_checkbox.setValue("0") # this is the fix re: huilib having problems with the default value

                        other_baking_options_collapser_layout.addGadget(a_checkbox)
                        
                        self.other_maps_to_bake_checkbox_dict[map_name] = a_checkbox # save for a rainy day
                
                #hou.ui.displayMessage("hi")

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
                self.close() # inherited call back method to close the UI

                self.blah()

                #a_thread_one = threading.Thread(target = self.close)
                #a_thread_one.start()
                
                #a_thread_two = threading.Thread(target = self.blah)
                #a_thread_two.start()

        def blah(self):
                # Get information from UI (I have types in the variable names for the sake of clarity)
                polyreduce_percentage_float = float(self.polyreduce_percentage_slider.getValue())
                
                displacement_type_str = self.displacement_type_menu_list[self.displacement_type_menu.getValue()]
                displacement_resolution_str = self.displacement_resolution_menu_list[self.displacement_resolution_menu.getValue()]

                use_temp_displacement_checkbox_value = self.use_temp_displacement_checkbox.isChecked() # checkbox_value is "0" or "1", but I want it False or True for clarity
                if use_temp_displacement_checkbox_value == "0": # 0 corresponds to unticked, and 1 corresponds to ticked
                        use_temp_displacement_bool = False
                else:
                        use_temp_displacement_bool = True

                # construct maps_to_bake_dict
                maps_to_bake_dict = lod_and_bake.Bake.maps_to_bake_dict_template.copy() # dictionaries are mutable, so need to make a copy as to not modify the original!

                maps_to_bake_dict[displacement_type_str] = True # sort out displacement

                # sort out other maps ticked
                for map_name in self.other_maps_to_bake_checkbox_dict.keys():
                        checkbox_value = self.other_maps_to_bake_checkbox_dict[map_name].isChecked() # like the above
                        if checkbox_value == "0":
                                bake_bool = False
                        else:
                                bake_bool = True
                        maps_to_bake_dict[map_name] = bake_bool
                        

                # for testing
                #message_string = "polyreduce percentage: {}\ndisplacement type: {}\ndisplacement resolution: {}\nuse_temp_displacement: {}\n\nmaps_to_bake_dict: {}".format(polyreduce_percentage_float, displacement_type_str, displacement_resolution_str, use_temp_displacement_bool, maps_to_bake_dict)
                #hou.ui.displayMessage(message_string)

                # using displacement resolution as resolution for all maps you ask it to bake! I need to a discussion with Muggy on how it should be dealt with
                self.megascans_asset_object.execute_fix(polyreduce_percentage_float, maps_to_bake_dict, displacement_resolution_str, use_temp_displacement_bool)

                
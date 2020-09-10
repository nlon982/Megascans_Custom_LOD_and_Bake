from huilib import *



class MegascansFixerDialog(HDialog):
        def __init__(self, megascans_asset_object):
                super(MegascansFixerDialog, self).__init__("Namegoeshere", "Title goes here")
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
                

                space_label1 = HLabel("")
                space_column_layout1.addGadget(space_label1)    
                
                text_label1 = HLabel("Polyreduce Percentage:")
                text_column_layout1.addGadget(text_label1)
                
                self.polyreduce_percentage_slider = HFloatSlider("polyreduce_percentage_slider", "") # let's see if that works
                self.polyreduce_percentage_slider.setRange((0, 100))
                self.polyreduce_percentage_slider.setValue(50)
                self.polyreduce_percentage_slider.lockRange()
                other_column_layout1.addGadget(self.polyreduce_percentage_slider)

                self.addGadget(sep)
                
                #-------------- Baking options (everything layout/widget without a personalised baking name has '2' on it)
                label2 = HLabel("Baking options:")
                self.addGadget(label2)
                
                baking_options_row_layout = HRowLayout()
                self.addLayout(baking_options_row_layout)
                
                
                space_column_layout2 = HColumnLayout()
                space_column_layout2.setAttributes(width = 0.25)
                baking_options_row_layout.addLayout(space_column_layout2)
                            
                other_column_layout2 = HColumnLayout()
                baking_options_row_layout.addLayout(other_column_layout2)
                
                
                space_label2 = HLabel("")
                space_column_layout2.addGadget(space_label2)    
                
                self.displacement_type_menu = HStringMenu("displacement_type_menu", "Displacement Map Type", self.displacement_type_menu_list)
                other_column_layout2.addGadget(self.displacement_type_menu)

                
                self.displacement_resolution_menu = HStringMenu("displacement_resolution_menu", "Displacement Map Resolution", self.displacement_resolution_menu_list)
                other_column_layout2.addGadget(self.displacement_resolution_menu)
                
                self.use_temp_displacement_toggle = HCheckbox("use_temp_displacement_toggle", "Temporarily use 1K Resoluton while above is baked (does nothing if 1K is chosen above)")
                self.use_temp_displacement_toggle.setValue("0") # because it's not set to ?anything? by default (but should be set to 0 as that corresponds to unticked - so doing it here), which is FUCKED
                other_column_layout2.addGadget(self.use_temp_displacement_toggle)
                
                self.addGadget(sep)
                
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
                # I have the types in the variable names for clarity

                polyreduce_percentage_float = float(self.polyreduce_percentage_slider.getValue())
                
                displacement_type_str = self.displacement_type_menu_list[self.displacement_type_menu.getValue()]
                displacement_resolution_str = self.displacement_resolution_menu_list[self.displacement_resolution_menu.getValue()]

                use_temp_displacement_str = self.use_temp_displacement_toggle.isChecked() # i.e. it's "0" or "1", but I want it True or False for clarity
                if use_temp_displacement_str == 0:
                        use_temp_displacement_bool = False
                else:
                        use_temp_displacement_bool = True

                self.close() # inherited call back method to close the UI

                self.megascans_asset_object.execute_fix(polyreduce_percentage_float, displacement_type_str, displacement_resolution_str, use_temp_displacement_bool)
                # for testing
                #message_string = "polyreduce percentage: {}\ndisplacement type: {}\ndisplacement resolution: {}\nuse_temp_displacement: {}".format(polyreduce_percentage_float, displacement_type_str, displacement_resolution_str, self.use_temp_displacement_toggle.isChecked())
                #hou.ui.displayMessage(message_string)

                
from houlib import *

class MyDialog(HDialog):
        def __init__(self):
                super(MyDialog, self).__init__("Namegoeshere", "Title goes here")
                self.setWindowLayout('vertical')
                self.setWindowAttributes(stretch = True, margin = 0.1, spacing = 0.1, min_width = 5)

                # using conventions that i'm coming up with to keep this organised
                # assigning a Gadget to self.variablename (a personalised variable name too) when I know i'll access it later
                
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
                
                self.displacement_type_menu = HStringMenu("displacement_type_menu", "Displacement Map Type", ["Displacement", "Vector Displacement"])
                other_column_layout2.addGadget(self.displacement_type_menu)

                
                self.displacement_resolution_menu = HStringMenu("displacement_resolution_menu", "Displacement Map Resolution", ["8K", "4K", "2K", "1K"])
                other_column_layout2.addGadget(self.displacement_resolution_menu)
                
                self.use_temp_displacement_toggle = HCheckbox("use_temp_displacement_toggle", "Temporarily use 1K Resoluton while above is baked (does nothing if 1K is chosen above)")
                other_column_layout2.addGadget(self.use_temp_displacement_toggle)
                
                self.addGadget(sep)
                
                #-------------- Go Button
                bottom_row_layout = HRowLayout()
                self.addLayout(bottom_row_layout)
                
                self.go_button = HButton('go_button', "Go!")
                bottom_row_layout.addGadget(self.go_button)
                
                #-------------- "connect call backs"
                
                self.go_button.connect(self.close) # close is an inherited method
                
                
                
                #-------------- Initialize
                self.initUI()


ui = MyDialog()
ui.show()

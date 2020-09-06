import hou
from random import random
import huilib
reload(huilib)


class TestDialog(HDialog):
    def __init__(self, name, title):
        super(TestDialog, self).__init__(name, title)
        self.setWindowLayout('vertical')
        self.setWindowAttributes(stretch = True, margin = 0.1, spacing = 0.1, min_width = 5)

        # Create various gadgets, and add them to the self (a layout too)
        self.toggleEnable = HCheckbox('enable_fields', 'Enable All Fields')
        self.addGadget(self.toggleEnable)

        self.geoFileField = HFileField('geo_field', 'Geo:', type_filter = 'geo')
        self.geoFileField.setEnabled(False)
        self.addGadget(self.geoFileField)

        self.imgFileField = HFileField('img_field', 'Img:', type_filter = 'pic')
        self.imgFileField.setEnabled(False)
        self.addGadget(self.imgFileField)

        self.stringField = HStringField('field', 'Text Field')
        self.stringField.setEnabled(False)
        self.addGadget(self.stringField)

        self.colorSelector = HColorSelector('clr_selector', 'Color')
        self.colorSelector.setValue([0.2, 0, 1])
        self.addGadget(self.colorSelector)

        #--------------------------------
        # Create a Row Layout to hold Sliders and Check Buttons and add to self (a layout too)
        row_layout_1 = HRowLayout()
        self.addLayout(row_layout_1)

        sliders_layout = HColumnLayout()
        button_layout = HColumnLayout()
        row_layout_1.addLayout(sliders_layout)
        row_layout_1.addLayout(button_layout)

        # Create Slider 1/2, and Create Check Button 1/2
        self.slider1 = HFloatSlider('slider1', 'Float Slider 1')
        self.slider1.setRange((0,1))
        self.slider1.setValue(0.4)
        self.slider1.lockRange()
        sliders_layout.addGadget(self.slider1)

        self.slider2 = HFloatSlider('slider2', 'Float Slider 2')
        self.slider2.setRange((0.001, 0.1 ))
        sliders_layout.addGadget(self.slider2)

        self.check_button1 = HButton('check_button1', 'Check 1')
        self.check_button1.setAttributes(vstretch = True)
        button_layout.addGadget(self.check_button1)

        self.check_button2 = HButton('check_button2', 'Check 2')
        self.check_button2.setAttributes(vstretch = True)
        button_layout.addGadget(self.check_button2)       
        #--------------------------------

        # Create Collapser Layout and add to self (a Layout too)
        collapser = HCollapserLayout(layout = 'vertical')
        self.addLayout(collapser)

        row_layout_2 = HRowLayout()
        collapser.addLayout(row_layout_2)

        self.button1 = HButton('button1','List Nodes')
        row_layout_2.addGadget(self.button1)

        self.button2 = HButton('button2','Rand Color')
        row_layout_2.addGadget(self.button2)

        self.button3 = HButton('button3','Button 3')
        row_layout_2.addGadget(self.button3)


        # Create various gadgets, and add them to the Layout (self)
        self.label1 = HLabel('This is Label 1. Any Text can be here')
        self.addGadget(self.label1)

        self.label2 = HLabel('This is Label 2. Any Text can be here')
        self.addGadget(self.label2)

        self.vec1 = HVectorField('vec1', 'Vector Field 1')
        self.addGadget(self.vec1)

        self.vec2 = HVectorField('vec2', 'Vector Field 2')
        self.addGadget(self.vec2)

        
        # Create a Row Layout to hold Menu 1/2 dropdowns
        self.menuRow = HRowLayout()
        self.addLayout(self.menuRow) # add to self (a layout too)

        self.menu1 = HStringMenu('menu1', 'Menu 1', ['item1', 'item2', 'item3'])
        self.menuRow.addGadget(self.menu1)

        self.menu2 = HStringMenu('menu2', 'Menu 2')
        self.menu2.setMenuItems(['Saint-Petersburg', 'Moscow', 'Kamchatka']) # illustrating you can set menu items seperately
        self.menuRow.addGadget(self.menu2)


        # Create a Row Layout to hold Close Button, add to self (a layout too) with seperators
        bottomRow = HRowLayout()

        self.close_button = HButton('close', 'Close')
        bottomRow.addGadget(self.close_button)
        
        sep = HSeparator()
        sep.setAttributes(look = 'bevel')

        self.addGadget(sep)
        self.addLayout(bottomRow)
        self.addGadget(sep)



        # Connect callbacks
        self.toggleEnable.connect(self.cb_enable_fields)
        self.button1.connect(self.cb_listNodes)
        self.close_button.connect(self.close)
        self.button2.connect(self.cb_randomizeColor)
        self.button3.connect(self.cb_printStringFields)

        # This method should always be called last!!
        self.initUI()


    def cb_listNodes(self):
        nodes = [node.name() for node in hou.node('/obj').children()]
        self.menu1.setMenuItems(nodes)

    def cb_randomizeColor(self):
        self.colorSelector.setValue([random(), random(), random()])


    def cb_printStringFields(self):
        self.geoFileField.getValue()


    def cb_enable_fields(self):
        val = self.toggleEnable.isChecked()
        if val:
            self.geoFileField.setEnabled(True)
            self.imgFileField.setEnabled(True)
            self.colorSelector.setEnabled(True)
            self.stringField.setEnabled(True)
        else:
            self.geoFileField.setEnabled(False)
            self.imgFileField.setEnabled(False)
            self.colorSelector.setEnabled(False)
            self.stringField.setEnabled(False)

    def cb_getColor(self):
        clr = self.colorSelector.getValue()
        print clr



ui = TestDialog(name = 'test', title = 'Test UI')
ui.show()
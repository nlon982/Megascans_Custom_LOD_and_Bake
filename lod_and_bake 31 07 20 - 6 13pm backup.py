from big_framework import string_processor

class Bake:


    def __init__(self, highpoly_path, lod_path, resolution, to_bake_dict, export_directory): # I haven't given a choice of export name, because that adds so much complexity
        check_path_exists(highpoly_path)
        self.geometry_path = highpoly_path # e.g. "C:/User/geometry.fbx"

        check_path_exists(lod_path)
        self.lod_path = lod_path

        self.export_path = os.path.join(export_directory, "custom_baking_%(CHANNEL)s.rat") # this is what the bake_texture node uses. Hardcoded along with export_name below


        # Setup params_dict and export_path_dict
        parameter_names_dict = {'Displacement' : 'vm_quickplane_Ds'} # todo

        self.export_paths_dict = dict()
        self.params_dict = dict()
        for map_type in to_bake_dict.keys():
            parameter_name = parameter_names_dict[map_type]

            to_bake_bool = to_bake_dict[map_type]

            self.params_dict[houdini_name] = to_bake_bool

            if to_bake_bool == True:
                export_name = "custom_baking_{}s.exr".format(houdini_name.split("_")[-1][:-1]) # i.e. if the parameter name is 'vm_quickplane_Ds', the render token, %(CHANNEL), is 'D'
                self.export_paths_dict[map_name] = os.path.join(export_directory, export_name)


    def create_in_houdini(self, housing_node): # includes executing the baking
        # Set up GEOs
        highpoly_geo_node = subnet_node.createNode("geo", "Highpoly_geo_temp")
        customlod_geo_node = subnet_node.createNode("geo", "CustomLOD_geo_temp") # aka lowpoly
        string_processor(highpoly_geo_node, "@cfile!file:{}".format(self.highpoly_path.replace(" ", "%20")))
        string_processor(customlod_geo_node, "@cfile!file:{}".format(self.lod_path.replace(" ", "%20")))

        return self.export_path_dict # unnecessary, but nice



class LOD:

    def __init__(self, highpoly_path, polyreduce_percentage, export_path):
        check_path_exists(highpoly_path)
        self.geometry_path = highpoly_path # e.g. "C:/User/geometry.fbx"

        self.polyreduce_percentage = polyreduce_percentage

        self.export_path = export_path


    def create_in_houdini(self, housing_node): # includes executing
    
        custom_lod_node = subnet_node.createNode("geo", "Custom_LOD")
        string_processor(custom_lod_node,\
            "cfile-file_node i0 cconvert-convert_node i0 \
            econvert_node i0 cpolyreduce::2.0-polyreduce_node i0 \
            epolyreduce_node i0 crop_fbx-rop_fbx_node i0")
        
        hou.hipFile.save() # save hip file before render
        
        string_processor(custom_lod_node, "@efile_node!file:{} @epolyreduce_node!percentage:int{}!reducepassedtarget:+!originalpoints:+ @erop_fbx_node!sopoutput:{}!execute:=".format(chosen_highpoly_path.replace(" ", "%20"), polyreduce_percentage, self.export_path.replace(" ", "%20")))

        return self.export_path # unnecessary, but nice



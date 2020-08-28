import os

def settings():
    #### SOME SETTINGS ####
    
    vector_displacement_tick = "-" # Vector displacement: "-" for no, "+" for yes
    polyreduce_percentage = "50"
    
    #### END ####
    
    return vector_displacement_tick, polyreduce_percentage

def get_file_scan(pack_location): # I wrote this ages ago, this is inefficient. Have to do something like this because scandir isn't in python2
    dir_scan_list = list()
    scan_list = os.listdir(pack_location)
    for material_name in scan_list:
        a_path = pack_location + "\\" + material_name
        if os.path.isdir(a_path) == False: # I modified this for this if to be true if it's a file (not a directory - like in the original)
            dir_scan_list.append(material_name)
    return dir_scan_list

def get_maps(file_scan):
    map_list = list()
    map_name_list = ["Albedo", "Roughness", "Normal", "Displacement"] # as below, no case sensitive
    for file_name in file_list: # this way, it looks at one file_name, and checks if it is any of the maps (rather than for each map, looking at every file - which is inefficient since it'd look at the same file over again even if it's already found that files' map name)
        lower_case_file_name = file_name.lower() # the lower cases add a bit more fool proof
        for map_name in map_name_list: 
            lower_case_map_name = map_name.lower()
            if lower_case_map_name in lower_case_file_name:
                map_list.append(file_name) # no need to append the lowercase file name lol
                break # we've found this file has a map name, no need to check if this has another map name
    return map_list

def get_existing_maps_of_name(map_list, map_name)
    existing_maps = list()
    for item in map_list:
        if file_name in item:
                existing_maps.append(item)
    return existing_maps


def get_file_extension(file_path_or_name):
    return os.path.splittext(file_path_or_name)

def get_megascans_resolution(file_path_or_name): # returns 2K if file_name is kfdl_2K_fdjk_fjfkd_fdhs
    first_underscore_index = file_name.find("_")
    second_underscore_index = first_underscore_index + 1 + file_name[first_underscore_index + 1:].find("_")
    return file_name[first_underscore_index + 1: second_underscore_index] # this givens e.g. "2K". Perhaps to make this function have more uses, i'm going to crop out the "K" and return an 

def get_sorted_maps_of_type_and_res(existing_maps, file_extension_list = None, resolution_list = None): # returns a list of maps in order in file_extension and resolution_list
    # this is not called 'get_chosen_map' because the outcome isn't a single map, it returns a list (so that way the user can decide)

    to_return = existing_maps # is this considered tidy?

    if file_extension_list != None:
        to_return = sorted(existing_maps, key = lambda file_name: file_extension_list.index(get_file_extension(file_name)))
    if resolution_list != None: # sorting by resolution second means, obviously: it sorts by file_extension first, and then by resolution
        to_return = sorted(sorted_list, key = lambda file_name: resolution_list.index(get_megascans_resolution(file_name)))

    return to_return


    # The idea is to use get_file_scan, then get_maps, then get_existing_maps_of_name, get_sorted_maps_of_type_and_res (perhaps the last should use the second to last)
    # (e.g. i..e the output of the previous is used in the current)

def get_highest_resolution(map_list):
    a_list = list()
    for map_name in map_list:
        try: # just in case one of the maps doesn't have a resolution
            megascans_resolution = get_megascans_resolution(map_name) # this gives e.g. "4K"
            megascans_resolution_int = int(megascans_resolution[:megascans_resolution.find("K")]) # this gives e.g. 4
            a_list.append(megascans_resolution_int)
        except:
            pass

    if len(a_list) != 0: # or could use a try except
        highest_resolution = max(a_list) * 1024
    else:
        highest_resolution = 2048 # default resolution

    return highest_resolution

# TODO: I need to fix up the rest of the code to use these functions


def get_asset_nodes(selected_node_path): # not even sure if this should be a function
    asset_geometry_path = "{}/Asset_Geometry".format(selected_node_path)
    asset_geometry_node = hou.node(asset_geometry_path)
    asset_material_path = "{}/Asset_Material".format(selected_node_path)
    asset_material_node = hou.node(asset_material_path)
    # perhaps look at deleting path/node, depending on what is used in the below
    if asset_geometry_node == None or asset_material_node == None:
        raise Exception("Asset Geometry or Asset Material aren't children of the selected node, are you sure you've selected the right node?")
    return asset_geometry_node, asset_material_node

def get_child_from_parent(parent_node, child_name): # I thought i'd make this a function to stop repeated code.
    #I could make it so that it works for both a passed parent node, and parent path
    child_node_path = "{}/{}".format(parent_node.path(), child_name)
    child_node = hou.node(child_node_path)
    if child_node == None:# why not have the error protection here, lol
        raise Exception("The node at path '{}' does not exist".format(child_node_path))
    return child_node

def get_megascans_asset_name(megascans_folder_path):
    if "/" in megascans_folder_path: # since I can't trust os
        slash = "/"
    elif "\\" in megascans_folder_path:
        slash = "\\"
    megascans_folder_name = megascans_folder_path[megascans_folder_path.rfind(slash) + 1:] # I presume this works
    megascans_asset_name = megascans_folder_name[megascans_folder_name.rfind("_") + 1:] # i.e. given rock_assembly_S01ez, it returns S01ez
    return megascans_asset_name





def check_node_exists(a_node_path): # I was thinking of doing something like this. Currently I haven't used this - still deciding
    a_node = hou.node(a_node_path)
    if a_node == None:
        raise Exception("A node does not exist at the path: {}".format(a_node_path))

def check_path(a_path):
    if os.path.exists(a_path) == False:
        raise Exception("A file does not exist at the path: {}".format(a_path))

    
def main(): #i've decided to use nodes, and if I want the path, I can get path (versus the other way around)
    selected_node_list = hou.selectedNodes();
    if len(selected_node_list) != 1:
        raise Exception("More than one node selected")
    selected_node = selected_node_list[0]
    
    asset_geometry_node, asset_material_node = get_asset_nodes(selected_node.path()) 

    file_node = get_child_from_parent(asset_geometry_node, "file1")
    some_geometry_path = file_node.parm("file").eval()

    megascans_asset_folder_path = os.path.dirname(some_geometry_path) # bit more fool proof than doing it myself
    megascans_asset_name = get_megascans_asset_name(megascans_asset_folder_path)
    file_scan = get_files_scan(megascans_asset_folder_path)

    vector_displacement_tick, polyreduce_percentage = settings() # if the code has gotten this far, things are probably good, so can bother configuring settings (irrelevant since not asking for input)

    #The following is all housed in a subnet called Subnet, created below
    subnet_node = hou.node("/obj").createNode("subnet", "Subnet") # could probably come up with a more creative name
    
    # this is used in Step 1 and 2
    chosen_highpoly_file = get_file_with_name_and_type(file_scan, "High", [".fbx"])
    chosen_highpoly_path = os.path.join(megascans_asset_folder_path, chosen_highpoly_file)

    # Needed for Step 2 (assuming there is a Normal)
    chosen_normal_file = get_file_with_name_and_type(file_scan, "Normal", [".exr", ".png", ".jpg"], ["8K", "4K", "2K"])
    chosen_normal_path = os.path.join(megascans_asset_folder_path, chosen_normal_file)
    
    #-------------------------------------------------------------------------------------

    # Step 1) Make custom LOD'

    customlod_name = megascans_asset_name + "_LOD_custom.fbx" # note: this doesn't exist yet (created below)
    customlod_path = os.path.join(megascans_asset_folder_path, customlod_name)

    a_lod_object = LOD(chosen_highpoly_path, polyreduce_percentage, customlod_path)
    a_lod_object.create_in_houdini(subnet_node)

    #-------------------------------------------------------------------------------------

    # Step 1.5) Set up GEOs

    highpoly_geo_node = subnet_node.createNode("geo", "Highpoly_geo_temp")
    customlod_geo_node = subnet_node.createNode("geo", "CustomLOD_geo_temp") # aka lowpoly
    string_processor(highpoly_geo_node, "@cfile!file:{}".format(chosen_highpoly_path.replace(" ", "%20")))
    string_processor(customlod_geo_node, "@cfile!file:{}".format(customlod_path.replace(" ", "%20")))

    #-------------------------------------------------------------------------------------

    # Step 2) Bake custom displacement
    to_bake_dict = Bake.to_bake_dict_template
    to_bake_dict["Displacement"] = True
    to_bake_dict["Vector Displacement"] = True

    a_bake_object = Bake(chosen_highpoly_path, customlod_path, (2048, 2048), to_bake_dict, megascans_asset_folder_path)
    export_paths_dict = a_bake_object.create_in_houdini(subnet_node)

    #-------------------------------------------------------------------------------------

    # Step 3) Node setup (currently using old as base)


    ###### Initial Setup

    # tick Tesselation, Displacement, and set Displacement Scale
    string_processor(selected_node, "@eAsset_Geometry!RS_objprop_rstess_enable:+!RS_objprop_displace_enable:+!RS_objprop_displace_scale:0.01") # this scale is based off the transform in the file import, blah blah. Foolproofing would be to set this off that.

    # assign some variables
    rs_material_builder_node = asset_material_node.children()[0] # may be lazy, error proofing below
    if rs_material_builder_node.type().name() != "redshift_vopnet":
        raise Exception("Expected node in Asset Geometry to be of type 'redshift_vopnet'")

    redshift_material_node = None
    for child in rs_material_builder_node.children():
        if child.type().name() == "redshift_material":
            redshift_material_node = child
            break
    if redshift_material_node == None:
        raise Exception("Cannot find node of type 'redshift_material' in RS Material Builder")


    # initial setup to include creating bumpblender, or any other setup that's needed for the dict (described below to work)
    string_processor(rs_material_builder_node, "cBumpBlender-bump_blender!bumpWeight0:0.25!bumpWeight1:0.5 i0 e{} i2".format(redshift_material_node.name())) 

    #string_processor(rs_material_builder_node, "cMaxonNoise-maxon_noise!noise_type:Displaced%20turbulence!coord_scale_global:0.1 i0 cBumpMap-bump_for_maxon i0 ebump_for_maxon i0 ebump_blender nbumpInput0") maxon noise 
    # ^ perhaps?

    # hardcoded logic:
    # if both vector displacement and displacement exists, use vector displacement
    # if normal map exists, destroy megascan's legacy normal map
    # assume called export_paths_dict
    maps_to_add = export_paths_dict.keys()
    if "Vector Displacement" in maps_to_add and "Displacement" in maps_to_add: # shortcircuiting can be used here, i.e. latter isn't check if former isn't there
        export_paths_dict.pop("Displacement") # I think that's elegant

    if "Normal" in maps_to_add: #### TODO: Is normal an option to be baked?
        for child in rs_material_builder_node.children(): # if the legacy normal map exists, destroy it lol
            if child.type().name() == "redshift::NormalMap": # have to use full name here
               child.destroy()
               break


    # I expect i'll have a dict like {"Displacement" : "cTextureSampler!tex0:{} i0 ebump_blender i0".format(export_paths_dict["Displacement"])}
    # then iterate over the dict, completing the thing

    node_setup_dict = dict()
    node_setup_dict["Displacement"] = "@edisplacement!tex0:{} @eDisplacement1!map_encoding:1"
    node_setup_dict["Vector Displacement"] = "@edisplacement!tex0:{} @eDisplacement1!map_encoding:0"
    node_setup_dict["Bump Map"] = "cTextureSampler-bump!tex0:{}!color_multiplierr:0.2!color_multiplierg:0.2!color_multiplierb:0.2 i0 cBumpMap-bump_for_bump i0 ebump_for_bump i0 ebump_blender nbaseInput"
    # I know it's not called "Bump Map" TODO ^
    node_setup_dict["Normal"] = "cNormalMap-normal!tex0:{} i0 cBumpMap-bump_for_normal!inputType:1 i0 ebump_for_normal i0 ebump_blender nbumpInput1"
    # I know it's not called "Normal" TODO ^

    # I can code some logic so it knows what bumpblender to go to, else I guess each map can have their own exclusive layer they go to, whatever
    # note, they all have some the tex0 to be .formatted in, in the forloop (as below)

    for map_name in export_paths_dict.keys(): # since popping may have been done since
        try:
            node_setup_string = node_setup_dict[map_name].format(export_paths_dict[map_name])
            string_processor(rs_material_builder_node, node_setup_string)
        except:
            raise Exception("node_setup_dict does not contain the node setup for map name: {}".format(map_name))


    ########################################## code that is to be reworked re: above

    #-------------------------------------------------------------------------------------

    # Set File to custom LOD (note, I haven't done the switch thing). I haven't tested the following but assume it works
    file_node.parm("file").set(customlod_path)
    
    # layout subnet
    subnet_node.layoutChildren()
    subnet_node.setDisplayFlag(False);
    


main()
import os
import big_framework

def get_files_scan(pack_location): # I wrote this ages ago, this is inefficient. Have to do something like this because scandir isn't in python2
    dir_scan_list = list()
    scan_list = os.listdir(pack_location)
    for material_name in scan_list:
        a_path = pack_location + "\\" + material_name
        if os.path.isdir(a_path) == False: # I modified this for this if to be true if it's a file (not a directory - like in the original)
            dir_scan_list.append(material_name)
    return dir_scan_list

def get_existing_files_with_name(file_scan, file_name): # what items in the directory exist with that map_name
    existing_files = list()
    for item in file_scan:
        if file_name in item:
                existing_files.append(item)
    return existing_files

def get_chosen_file(existing_maps, type_list): # yes, it gives you preferred type, caveat is that is gets the first file it sees of that type
    type_list.reverse()
    chosen_map_file = None # an obvious good thing to have, i.e. prevents error if chosen map file not found, and useful for calling code
    for file_type in type_list:
        for item in existing_maps:
            if file_type in item:
                chosen_map_file = item
                break
    return chosen_map_file

def get_file_with_name_and_type(file_scan, file_name, type_list): # fuck it, it makes sense here to merge the above two functions
    existing_files = get_existing_files_with_name(file_scan, file_name)
    chosen_file = get_chosen_file(existing_files, type_list)
    if chosen_file == None: # why not have the error protection here, lol
        raise Exception("Cannot find file called '{}' with a type in {}".format(file_name, type_list))
    return chosen_file

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
    child_node_path = "{}/{}".format(parent_path, child_name)
    child_node = hou.node(child_node_path)
    if child_node == None:# why not have the error protection here, lol
        raise Exception("The node at path '{}/{}' does not exist")
    return child_node

def get_megascans_asset_name(megascans_folder_path):
    if "/" in megascans_folder_path: # since I can't trust os
        slash = "/"
    elif "\\" in megascans_folder_path:
        slash = "\\"
    megascans_folder_name = megascans_folder_path[megascans_folder_path.rfind(slash) + 1:] # I presume this works
    megascans_asset_name = megascans_folder_name[megascans_folder_name.rfind("_") + 1:] # i.e. given rock_assembly_S01ez, it returns S01ez
    return megascans_asset_name

def main(): #i've decided to use nodes, and if I want the path, I can get path (versus the other way around)
    # i'm trying to use multi-line syntax as a means to have tidier and clearer code, i'm using the convention of if a space is necessary, do it before the '\' (if not space sensitive, do a space for tidyness)

    selected_node_list = hou.selectedNodes();
    if len(selected_node_list) != 1:
        raise Exception("More than one node selected")
    selected_node = selected_node_list[0] # in case if ever needed (used below)
    selected_node_path = selected_node_list[0].path()
    
    asset_geometry_node, asset_material_node = get_asset_nodes(selected_node_path) 

    file_node = get_child_from_parent(asset_geometry_node, "file1")
    some_geometry_path = file_node.parm("file").eval()

    megascans_asset_folder_path = os.path.dirname(some_geometry_path) # bit more fool proof than doing it myself
    megascans_asset_name = get_megascans_asset_name(megascans_asset_folder_path)
    file_scan = get_files_scan(megascans_asset_folder_path)

    

    #The following is all housed in a subnet called Subnet, created below
    subnet_node = hou.node("/obj").createNode("subnet", "Subnet") # could probably come up with a more creative name
    #-------------------------------------------------------------------------------------

    # Step 1) Make custom LOD
    custom_lod_node = subnet_node.createNode("geo", "Custom_LOD")
    string_processor(custom_lod_node,\
        "cfile-file_node i0 cconvert-convert_node i0 \
        econvert_node i0 cpolyreduce::2.0-polyreduce_node i0 \
        epolyreduce_node i0 crop_fbx-rop_fbx_node i0")

    customlod_name = megascans_asset_name + "_LOD_custom.fbx"
    customlod_path = os.path.join(material_folder, customlod_name)
    
    hou.hipFile.save() # save hip file before render
    
    string_processor(a_geo_node, \
        "@efile_node\
        !file:{} \
        @epolyreduce_node!percentage:int50\
        !reducepassedtarget:+\
        !originalpoints:+ \
        @erop_fbx_node!sopoutput:{}!execute:="\
        .format(highpoly_path.replace(" ", "%20"), customlod_path.replace(" ", "%20")))

    #-------------------------------------------------------------------------------------

    # Step 1.5) Set up GEOs

    chosen_highpoly_file = get_file_with_name_and_type(file_scan, "High", [".fbx"])
    chosen_highpoly_path = os.path.join(megascans_asset_folder_path, highpoly_name)

    highpoly_geo_node = subnet_node.createNode("geo", "Highpoly_geo_temp")
    customlod_geo_node = subnet_node.createNode("geo", "CustomLOD_geo_temp") # aka lowpoly
    string_processor(highpoly_geo_node, "@cfile!file:{}".format(highpoly_path.replace(" ", "%20")))
    string_processor(customlod_geo_node, "@cfile!file:{}".format(customlod_path.replace(" ", "%20")))

    #-------------------------------------------------------------------------------------

    # Step 2) Bake custom displacement
    a_camera = subnet_node.createNode("cam", "temp_camera")
    map_resolution_x = 2048 # feel free to change
    map_resolution_y = 2048
    string_processor(subnet_node, \
        "@etemp_camera\
        !tx:int0\
        !ty:int0\
        !tz:int0\
        !rx:int0\
        !ry:int0\
        !rz:int0\
        !px:int0\
        !py:int0\
        !pz:int0\
        !prx:int0\
        !pry:int0\
        !prz:int0\
        !resx:int{}\
        !resy:int{}"\
        .format(map_resolution_x, map_resolution_y)) # gross? perhaps set to default on t, r, p, pr is cleaner. Yep, definitely is.
    
    ropnet_node = subnet_node.createNode("ropnet", "ropnet_for_baking")
    baketexture_node = ropnet_node.createNode("baketexture::3.0", "bake_texture")

    export_path = os.path.join(megascans_asset_folder_path, "custom_baking_%(CHANNEL)s.rat")# note, this uses render tokens to export all the different ticks in to different files. I'm guessing .rat is redundant - idk.
   
    string_processor(ropnet_node, \
        "@ebake_texture\
        !camera:{}\
        !vm_uvunwrapresx:int{}\
        !vm_uvunwrapresy:int{}\
        !vm_uvobject1:{}\
        !vm_uvhires1:{}\
        !vm_uvoutputpicture1:{}\
        !vm_extractimageplanesformat:OpenEXR"\
        .format(a_camera.path(), map_resolution_x, map_resolution_y, customlod_geo_node.path(), highpoly_geo_node.path(), export_path.replace(" ", "%20"))) #TODO
    
    hou.hipFile.save() # save hip file before executing render

    string_processor(ropnet_node, \
        "@ebake_texture\
        !vm_extractremoveintermediate:+\
        !vm_quickplane_Ds:+\
        !vm_uv_unwrap_method:int2\
        !execute:=") # only ticking to bake out displacement (note: not vector displacement)
    
    # paths of exports
    customdisplacement_path = os.path.join(material_folder, "custom_baking_Ds.exr") # (hardcoded dependent on the above naming convention)

    #-------------------------------------------------------------------------------------

    # Step 3) Node setup (currently using old as base)

    # tick Tesselation, Displacement, and set Displacement Scale
    string_processor(selected_node, \
        "@eAsset_Geometry\
        !RS_objprop_rstess_enable:+\
        !RS_objprop_displace_enable:+\
        !RS_objprop_displace_scale:0.01") # this scale is based off the transform in the file import, blah blah. Foolproofing would be to set this off that.
    

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

    # use custom displacement map
    string_processor(rs_material_builder_node, \
        "@edisplacement\
        !tex0:{}"\
        .format(customdisplacement_path.replace(" ", "%20")))
    
    # create bumpblender, set settings, and connect to redshift material
    string_processor(rs_material_builder_node, \
        "cBumpBlender-bump_blender!bumpWeight0:0.25!bumpWeight1:0.5 i0 e{} i2"\
        .format(redshift_material_node.name())) 

    # setup bump map
    bumpmap_export_path = "bumpmapexportpathgoeshere" #TODO, TO FIND OUT
    string_processor(rs_material_builder_node, "cTextureSampler-bump!tex0:{}!color_multiplierr:0.2!color_multiplierg:0.2!color_multiplierb:0.2 i0 cBumpMap-bump_for_bump i0 ebump_for_bump i0 ebump_blender nbaseInput".format(bumpmap_export_path))
    
    # setup maxon noise (need to test with redshift license)
    #string_processor(rs_material_builder_node, "cMaxonNoise-maxon_noise!noise_type:Displaced%20turbulence!coord_scale_global:0.1 i0 cBumpMap-bump_for_maxon i0 ebump_for_maxon i0 ebump_blender nbumpInput0") maxon noise 

    # setup normal map
    for child in rs_material_builder_node.children(): # if the legacy normal map exists, destroy it lol
        if child.type().name() == "redshift::NormalMap": # have to use full name here
           child.destroy()
           break
    
    chosen_normal_file = get_file_with_name_and_type(file_scan, "Normal", [".exr", ".png", ".jpg"])
    chosen_normal_path = os.path.join(megascans_asset_folder_path, highpoly_name)
    
    string_processor(rs_material_builder_node, \
        "cNormalMap-normal!tex0:{} i0 cBumpMap-bump_for_normal!inputType:1 i0 \
        ebump_for_normal i0 ebump_blender nbumpInput1"\
        .format(chosen_normalmap_path.replace(" ", "%20")))    

    #-------------------------------------------------------------------------------------

    # Set File to custom LOD (note, I haven't done the switch thing). I haven't tested the following but assume it works
    file_node.parm("file").set(customlod_path)


main()
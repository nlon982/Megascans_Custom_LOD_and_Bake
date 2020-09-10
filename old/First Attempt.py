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


def get_list_item_with_string(a_string, a_list):
    for item in a_list:
        if a_string in item:
            return item
    return None


def get_existing_maps(map_scan, map_name): # what items in the directory exist with that map_name
    existing_maps = list()
    for item in map_scan:
        if map_name in item:
                existing_maps.append(item)
    return existing_maps

def get_chosen_map_file(existing_maps, type_list):
    type_list.reverse()
    for file_type in type_list:
        for item in existing_maps:
            if file_type in item:
                chosen_map_file = item
                break
    return chosen_map_file

def main():
    selected_node_list = hou.selectedNodes();

    if len(selected_node_list) != 1:
        raise Exception("More than one node selected")

    selected_node = selected_node_list[0] # in case if ever needed (used below)
    selected_node_path = selected_node_list[0].path()
    

    file_node = hou.node("{}/Asset_Geometry/file1".format(selected_node_path)) # assuming named Asset Geometry

    try: # make an exception if the node at file_node_path does not exist
        geometry_path = file_node.parm("file").eval()
    except:
        raise Exception("Cannot find: {}".format(file_node_path)) 

    material_folder = os.path.dirname(geometry_path) # bit more fool proof than doing it myself

    file_scan = get_files_scan(material_folder)

    
    highpoly_name = get_list_item_with_string("High", file_scan) # this doesn't check to see if it's the right format etc.

    if highpoly_name == None:
        raise Exception("High poly doesn't exist (file containing HIGH in name)")

    highpoly_path = os.path.join(material_folder, highpoly_name)


    obj_node = hou.node("/obj")
    
    # Step 1) Make custom LOD
    a_geo_node = obj_node.createNode("geo", "Custom_LOD")
  
    string_processor(a_geo_node, "cfile-file_node i0 cconvert-convert_node i0 econvert_node i0 cpolyreduce::2.0-polyreduce_node i0 epolyreduce_node i0 crop_fbx-rop_fbx_node i0")

    customlod_name = highpoly_name[:highpoly_name.rfind("_") + 1] + "LOD_custom.fbx" # the names go something like shopk_High.fbx, so the left bit gives "shopk_" 
    customlod_path = os.path.join(material_folder, customlod_name)
    hou.hipFile.save() # save hip file before render
    time.sleep(10)
    string_processor(a_geo_node, "@efile_node!file:{} @epolyreduce_node!percentage:int50!reducepassedtarget:+!originalpoints:+ @erop_fbx_node!sopoutput:{}!execute:=".format(highpoly_path.replace(" ", "%20"), customlod_path.replace(" ", "%20")))

    # Step 1.5) Set up GEOs
    highpoly_geo_node = obj_node.createNode("geo", "Highpoly_geo_temp")
    customlod_geo_node = obj_node.createNode("geo", "CustomLOD_geo_temp") # aka lowpoly

    string_processor(highpoly_geo_node, "@cfile!file:{}".format(highpoly_path.replace(" ", "%20")))
    string_processor(customlod_geo_node, "@cfile!file:{}".format(customlod_path.replace(" ", "%20")))

    # Step 2) Bake custom displacement
    a_camera = obj_node.createNode("cam", "temp_camera")
    string_processor(obj_node, "@etemp_camera!tx:int0!ty:int0!tz:int0!rx:int0!ry:int0!rz:int0!px:int0!py:int0!pz:int0!prx:int0!pry:int0!prz:int0!resx:int2048!resy:int2048") # gross? perhaps set to default on t, r, p, pr is cleaner. Yep, definitely is.
    ropnet_node = obj_node.createNode("ropnet", "ropnet_for_baking")
    output_path = os.path.join(material_folder, "custom_baking_%(CHANNEL)s.rat")# note, this uses render tokens to export all the different ticks in to different files. I'm guessing .rat is redundant - idk.
    # thanks to the above, the custom displacement's path is: inside the material_folder, named custom_baking_Ds.exr
    customlod_export_path = os.path.join(material_folder, "custom_baking_Ds.exr")
    
    baketexture_node = ropnet_node.createNode("baketexture::3.0", "bake_texture")
    string_processor(ropnet_node, "@ebake_texture!camera:{}!vm_uvunwrapresx:int2048!vm_uvunwrapresy:int2048!vm_uvobject1:{}!vm_uvhires1:{}!vm_uvoutputpicture1:{}!vm_extractimageplanesformat:OpenEXR".format(a_camera.path(), customlod_geo_node.path(), highpoly_geo_node.path(), output_path.replace(" ", "%20"))) #TODO
    time.sleep(5)
    hou.hipFile.save() # save hip file before render
    print("has unsaved changes:", hou.hipFile.hasUnsavedChanges())
    string_processor(ropnet_node, "@ebake_texture!vm_extractremoveintermediate:+!vm_quickplane_Ds:+!vm_uv_unwrap_method:int2!execute:=") # only ticking to bake out displacement (note: not vector displacement)


    # Step 3) Node setup (currently using old as base)
    asset_material_node = hou.node("{}/Asset_Material".format(selected_node_path))
    string_processor(selected_node, "@eAsset_Geometry!RS_objprop_rstess_enable:+!RS_objprop_displace_enable:+!RS_objprop_displace_scale:0.01") # this scale is based off the transform in the file import, blah blah. Foolproofing would be to set this off that.
    # Enables Tesselation and Displacement, and sets Displacement Scale

    
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

    string_processor(rs_material_builder_node, "@edisplacement!tex0:{}".format(customlod_export_path.replace(" ", "%20")))
    
    
    string_processor(rs_material_builder_node, "cBumpBlender-bump_blender!bumpWeight0:0.25!bumpWeight1:0.5 i0 e{} i2".format(redshift_material_node.name())) # create bumpblender, set settings, and connect to redshift material

    bumpmap_export_path = "bumpmapexportpathgoeshere" #TODO, TO FIND OUT
    
    string_processor(rs_material_builder_node, "cTextureSampler-bump!tex0:{}!color_multiplierr:0.2!color_multiplierg:0.2!color_multiplierb:0.2 i0 cBumpMap-bump_for_bump i0 ebump_for_bump i0 ebump_blender nbaseInput".format(bumpmap_export_path))
    #string_processor(rs_material_builder_node, "cMaxonNoise-maxon_noise!noise_type:Displaced%20turbulence!coord_scale_global:0.1 i0 cBumpMap-bump_for_maxon i0 ebump_for_maxon i0 ebump_blender nbumpInput0") maxon noise 

    normalmap_name = get_list_item_with_string("Normal", file_scan) # copy and pasted code (I should make a function of this)
    if normalmap_name == None:
        raise Exception("Normalmap doesn't exist (file containing Normal in name)")
    normalmap_path = os.path.join(material_folder, normalmap_name)

    for child in rs_material_builder_node.children(): # if the legacy normal map exists, destroy it lol
        if child.type().name() == "redshift::NormalMap": # have to use full name here
           child.destroy()
           break
        
    string_processor(rs_material_builder_node, "cNormalMap-normal!tex0:{} i0 cBumpMap-bump_for_normal!inputType:1 i0 ebump_for_normal i0 ebump_blender nbumpInput1".format(normalmap_path.replace(" ", "%20")))    

    # Set File to Thingy (note, I haven't done the switch thing). I haven't tested the following but assume it works
    file_node.parm("file").set(customlod_path)

    
    # random note: quixel does this thing where it has a dictionary of nodes that it wants to set up (and a dictionary of parameters) and it just iterates through that dictionary and does them.
    # is this cleaner the the big framework?
    # the big framework specializes in the connections and setting parameters at the same time - that's not beaten, I don't think

    # when to use stringprocesser? If you're creating a geo node in obj level, and then you'r ecreating nodes inside that. I reckon making the geo node with a_node.createNode() and use stringprocessor
    # for the nodes inside. Not only is this necessary (since string processor requires being passed the parent node, and I don't plan on making a clause otherwise), but it means you can then do .destroy() later.
    
    """ The following is irrelevant (while we use Bridge as the base - which I see as a must, unless I go BigBrain on Bridge's Python tools)


    map_and_type_node_setup_dict = {"DIFF .png .jpg" : "cTextureSampler i0 eShader ndiffuse_color", "ROUGH .jpg" : "cTextureSampler i0 eShader nrefl_roughness", "METAL .jpg" : "cTextureSampler i0 eShader nrefl_metalness", "HEIGHT .exr .jpg" : "cTextureSampler i0 cDisplacement i0 eDisplacement1 i0 eredshift_material1 i1", "NORM .jpg" : "cNormalMap i0 eShader nbump_input"}
    selected_node_list = hou.selectedNodes()

    file_scan = get_files_scan(material_folder)

    # can probably do something smart where string_processer returns a dictionary of node_setup objects (in a dictionary, to make use of hashing), so it doesn't have to compute every time - idk, 
    
    for map_and_type, node_setup_string in map_and_type_node_setup_dict.items():

        map_and_type_list = map_and_type.split(" ")
        map_name = map_and_type_list[0]
        type_list = map_and_type_list[1:]

        existing_maps = get_existing_maps(file_scan, map_name)
        if len(existing_maps) < 1: 
            continue

        chosen_map_file = get_chosen_map(existing_maps, type_list)

        # perhaps i'll need to use .format on node_setup_string for the file path e.g. cTextureSampler{}, and then here right a line of code to format it. Hmm.

        big_framework.string_processor(node_setup_string)
    """

main()


# Learnt: you can't render in background if you have spaces in your output_picture path (Old houdini glitch thing)

# Need to set file / switch to correct thing, maybe could delete other things for clarity/fun (because right now, I have to get the user to confirm it's in the right place)
# I may've missed a parameter or node, idk, the point is it's out to be fixed
# Then this code can be refined with functions etc. i've run out of time for the time being

# So the idea is you select the subnet imported from Bridge and hit this shelf tool, and boom it does all 3 steps, and you're good to go and hit render.
# Note, I notice it renders out the the baked displacement in the background (so some UI thing notifying the user that it's done would be cool)

#TODO get Kyle to run this and do a test (he can offer feedback about the nodesetup, as well as just blatantly testing if it works). Note the important thing about the switch.

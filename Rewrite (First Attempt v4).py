def os_path_join_fix(*args): # in the version of Python that Houdini has, os_path_join_fix is broken
    a_path = ""
    if len(args) == 0:
        return a_path
    else:
        slash = os.path.sep
        for item in args:
            a_path += item + slash

        return a_path[:-1] # so there isn't a final slash in the end




def get_file_scan(a_path):
	file_scan_list = list()
	scan_list = os.listdir(a_path)
	for material_name in scan_list:
		a_path = os_path_join_fix(a_path, material_name)
		if os.path.isdir(a_apath) == False:
			file_scan_list.append(material_name)
	return file_scan_list

""" I don't think this is best to use, see below's use without it
def get_maps(file_scan):
	maps_list = list()
	map_name_list = ["Albedo", "Roughness", "Normal", "Displacement"]

	for file_name in file_scan:
		for map_name in map_name_list:
			
			if map_name.lower() in file_name.lower():
				maps_list.append(file_name)

	return maps_list
"""

def get_child_from_parent_node(parent_node_path, child_name): # exception handling expected by caller
	child_node_path = "{}/{}".format(parent_node_path, child_name)
	child_node = hou.node(child_node_path)
	return child_node


def get_file_extension(file_path_or_name):
	return os.path.splittext(file_path_or_name)

def get_megascans_resolution(file_path_or_name, return_int = False):
	first_underscore_index = file_name.find("_")
	second_underscore_index = first_underscore_index + 1 + file_name[first_underscore_index + 1:].find("_")
	megascans_resolution_string = file_name[first_underscore_index + 1: second_underscore_index] # e.g. "4K"

	if return_int == False:
		return megascans_resolution_string
	else:
		return int(megascans_resolution_string[:-1])

def get_highest_resolution(megascans_folder_scan): # i.e. ONLY maps don't have to be passed
	resolution_list = list()

	for file_name in megascans_folder_scan:
		try: # may or may not be map
			megscans_resolution_int = get_megascans_resolution(file_name, True) # this gives e.g. "4K"
			resolution_list.append(megascans_resolution_int)
		except: # if not map (i.e. no resolution)
			pass

	if len(resolution_list) == 0:
		highest_resolution = 2048 # default resolution. Perhaps this should be decided elsewhere
	else:
		highest_resolution = max(a_list) * 1024

	return highest_resolution


def get_maps_of_name_type_and_res(file_scan, name, file_extension_list = None, resolution_list = None): # in descending order
	existing_maps = [map_name for map_name in unsorted_maps if name in map_name]
	
	if file_extension_list != None: # first sort
		sorted_maps = sorted(existing_maps, key = lambda map_name: file_extension_list.index(get_file_extension(map_name)))
	
	if resolution_list != None: # second sort
		sorted_maps = sorted(sorted_maps, key = lambda map_name: resolution_list.index(get_megascans_resolution(map_name, False)))

	return sorted_maps




def get_megascans_asset_name(megascans_folder_path):
	megascans_folder_name = os.path.basename(megascans_folder_path) # just in case
	megascans_asset_name = megascans_folder_name[megascans_folder_name.rfind("_") + 1:] # i.e. given rock_assembly_S01ez, returns S01ez
	return megascans_asset_name



def get_nodes(megascans_asset_subnet_node): # assumes using certain version of Bridge
	megascans_asset_subnet_path = megascans_asset_subnet_node.path()
	asset_geometry_path = "{}/Asset_Geomtry".format(megascans_asset_subnet_path)
	asset_geometry_node = hou.node(asset_geometry_path)
	asset_material_path = "{}/Asset_Material".format(megascans_asset_subnet_path)
	asset_material_node = hou.node(asset_material_path)
	file_node_path = "{}/Asset_Material/file1".format(megascans_asset_subnet_node) # more adaptable this way
	file_node = hou.node(file_path)

	if asset_geometry_node == None or asset_geometry_node == None:
		raise Exception("'Asset_Geometery' or 'Asset_Material' aren't children of {}".format(housing_path))
	if file_node == None:
		raise Exception("'file1' not found at []".file_node_path)

	return asset_geomtry_node, asset_material_node

def main():
	selected_node_list = hou.selectedNodes()
	if len(selected_node_list) != 1:
		raise Exception("More than one node selected, expected one")
	megascans_asset_subnet = selected_node_list[0] # assumming

	# get nodes
	asset_geometry_node, asset_material_node, file_node = get_asset_nodes(megascans_asset_subnet)

	megascans_asset_folder_path = file_node.parm("file").eval()
	megascans_asset_name = get_megascans_asset_name(megascans_asset_folder)

	file_scan = get_file_scan(megascans_asset_folder_path)
	#map_list = get_maps(file_scan) # problematic if this doesn't get all the maps


	# The following is all housed in the below subnet called Subnet
	subnet_node = megascans_asset_subnet.createNode("subnet", "Subnet") # Feel free to change. 

	#-----------------------------------------------
	# Step 1) Make Custom LOD

	polyreduce_percentage = 50

	customlod_name = megascans_asset_name + "_LOD_custom_{}percent.fbx".format(polyreduce_percentage)
	customlod_path = os_path_join_fix(megascans_asset_folder_path, customlod_name)

	highpoly_path = get_maps_of_name_type_and_res(file_scan, "High", file_extension_list = ".fbx")

	a_lod_object = LOD(highpoly_path, polyreduce_percentage, customlod_path)
	a_lod_object.create_in_houdini(subnet_node)


	#-----------------------------------------------
	# Step 2) Bake custom displacement
	map_resolution = 2048

	maps_to_bake_dict = Bake.maps_to_bake_dict_template
	maps_to_bake_dict["Displacement"] = True
	maps_to_bake_dict["Vector Displacement"] = True

	a_bake_object = Bake(highpoly_path, customlod_path, (map_resolution, map_resolution), maps_to_bake_dict, megascans_asset_folder_path)

	#-----------------------------------------------
	# Step 3) Bake custom displacement

	#<in progress>
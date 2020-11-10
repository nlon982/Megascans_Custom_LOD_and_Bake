def parameter_temp_processor(entry):
    if "!" in entry:
        entry_without_param = entry[:entry.find("!")]
        params = entry[entry.find("!"):]
        return entry_without_param, params
    return entry, None


def get_name_and_type(entry):
    if "-" in entry: # has name
        seperator_location = entry.find("-")
        entry_type = entry[:seperator_location]
        entry_name = entry[seperator_location + 1:]            
    else:
        entry_type = entry
        entry_name = None
    return entry_type, entry_name

def get_entry_param_name_from_content(entry, param_content): # e.g. given 'cTextureSampler-bob!hi:hello' (or even just '!hi:hello') and 'hello', give 'hi'
    param_cropped_right = entry[:entry.find(param_content) - 1]
    param_name = param_cropped_right[param_cropped_right.rfind("!") + 1:]
    return param_name

def get_entry_name(entry):
    if entry[0] == "@": # get rid of one off thing
        entry = entry[1:]

    entry_without_params, params = parameter_temp_processor(item)
    
    if entry_without_params[0] == "c":
        entry_type, entry_name = get_name_and_type(entry_without_params[1:])
    elif entry_without_params[0] == "e":
        entry_name = entry_without_params[1:]
    return entry_name

#-------

node_setup_string = "@edisplacement!tex0:{export_path} cTextureSampler-bob!tex0:{export_path} @eDisplacement1!map_encoding:1" # pretend I have
node_setup_list = node_setup_string.split(" ")

for item in node_setup_list:

    if "{export_path}" in item:

        if item[0] == "@": # get rid of one off thing
            item = item[1:]

        
        
        entry_name = get_entry_name(item)
        
        entry_param_name = get_entry_param_name_from_content(item, "{export_path}")

        print("entry_name: {}, param_name: {}".format(entry_name, entry_param_name))

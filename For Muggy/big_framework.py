import hou

# A framework to quickly make node setups / configure parameters

def parameter_processor(the_node, params): # I wrote the_node in order to not confuse with 'a_node', which means housing node.
    while "!" in params:
        #print(params)
        param_name = params[1:params.find(":")] # we know the first digit is going to be !
        end = params[1:].find("!") + 1 # index is in terms of 'params' because of +1. Very cool.
        if end == 0:
            end = len(params)
        param_content = params[params.find(":") + 1: end]
        set_parms(the_node, param_name, param_content)
        params = params[end:]


def set_parms(the_node, param_name, param_content):
    if "%20" in param_content:
        param_content = param_content.replace("%20", " ") # very gross work around to have space (forgive me)
    # '+' = set 1
    # '-' = set 0
    # '=' = execute
    if param_content[0] == "+": # tick mark on
        hou.parm("{}/{}".format(the_node.path(), param_name)).set(1)
    elif param_content[0] == "-": # tick mark off
        hou.parm("{}/{}".format(the_node.path(), param_name)).set(0) # duplicate code?
    elif param_content[0] == "=":
        hou.parm("{}/{}".format(the_node.path(), param_name)).pressButton()
    else:
        if param_content[0:3] == "int": # this if/else provides a way to manage types in params. "str" is default, so no need to declare.
            param_content = int(param_content[3:])
        elif param_content[0:3] == "str":
            param_content = param_content[3:] 
        the_node.setParms({param_name: param_content})
        #print("do the following on this node: {} . param_name : {} . param_content : {}".format(node.path(), param_name, param_content))

def get_name_and_type(entry):
    if "-" in entry: # has name
        seperator_location = entry.find("-")
        entry_type = entry[:seperator_location]
        entry_name = entry[seperator_location + 1:]            
    else:
        entry_type = entry
        entry_name = None
    return entry_type, entry_name

def parameter_temp_processor(entry):
    if "!" in entry:
        entry_without_param = entry[:entry.find("!")]
        params = entry[entry.find("!"):]
        return entry_without_param, params
    return entry, None

def get_and_remove_one_offs(a_list):
    one_off_list = list()
    to_remove_indices = list()
    for index in range(len(a_list)):
        if "@" in a_list[index]:
            one_off_item = a_list[index][1:]
            one_off_list.append(one_off_item)
            to_remove_indices.append(index)

    to_remove_indices.reverse() # disappearing stairs
    for index in to_remove_indices:
        a_list.pop(index)

    return a_list, one_off_list



def one_off_processor(a_node, one_off_list): # basically a duplicate of the set up function
    for item in one_off_list:
        item, params = parameter_temp_processor(item)
        
        # item from this point onwards contains only the type and name, I did this instead of using a different variable
        if item[0] == "c": # create
            item_type, item_name = get_name_and_type(item[1:])
            the_node = a_node.createNode(item_type, item_name) # Note that if None given for name, it uses the default name (which is convenient)
        elif item[0] == "e": # existing
            the_node = hou.node("{}/{}".format(a_node.path(), item[1:]))
        else:
            raise Exception("BAD INPUT in one off item: {}, no 'c' or 'e' at start.".format(item))

        if params is not None:
            parameter_processor(the_node, params)

# i'm not sure what I want out of this ^



def string_processor(a_node, a_string):
    a_list = a_string.split(" ")
    a_list, one_list = get_and_remove_one_offs(a_list)     # seperate one-offs from a_list  # one to mean, just one node. TODO.

    one_off_processor(a_node, one_list)
    
    if len(a_list) % 4 != 0: # error prevention
        print("Not divisible by 4")
        return

    while len(a_list) != 0:
        entry_1 = a_list[0]
        entry_2 = a_list[1]
        entry_3 = a_list[2]
        entry_4 = a_list[3]
        setup(a_node, entry_1, entry_2, entry_3, entry_4) 
        # ^ how about, a return type, that may or may not be used, which if used again, allows for the interpretting to not be done so much.
        a_list = a_list[4:]

    a_node.layoutChildren() # assuming that if used at 'setp_object' line, or at the end (here), has no difference. It is worth trying though.


# eHello!parm_name:parm_content
# cHello!parm_name:parm_content

# eHello&i0


def setup(a_node, entry_1, entry_2, entry_3, entry_4):
    entry_1, params_entry_1 = parameter_temp_processor(entry_1)
    entry_3, params_entry_3 = parameter_temp_processor(entry_3) # seperates parameters from entry
    #from here on, entry_1 and entry_3, contains only their type and name. I chose to write this comment instead of doing it in variable names

    if entry_1[0] == "c": # create
        entry_1_type, entry_1_name = get_name_and_type(entry_1[1:])
        output_node = a_node.createNode(entry_1_type, entry_1_name)
    elif entry_1[0] == "e": # existing
        output_node = hou.node("{}/{}".format(a_node.path(), entry_1[1:]))
    else:
        raise Exception("BAD INPUT entry_1: {}, no 'c' or 'e' at start.".format(entry_1))

    if entry_2[0] == "i":
        output_connector_int = int(entry_2[1:])
    elif entry_2[0] == "n":
        output_connector_int = output_node.outputIndex(entry_2[1:])
    else:
        raise Exception("BAD INPUT entry_2: {}, no 'i' or 'n' at start.".format(entry_2))

    if entry_3[0] == "c": # create
        entry_3_type, entry_3_name = get_name_and_type(entry_3[1:])
        input_node = a_node.createNode(entry_3_type, entry_3_name)
    elif entry_3[0] == "e": # existing
        input_node = hou.node("{}/{}".format(a_node.path(), entry_3[1:]))
    else:
        raise Exception("BAD INPUT entry_3: {}, no 'c' or 'e' at start.".format(entry_3))

    if entry_4[0] == "i":
        input_connector_int = int(entry_4[1:])
    elif entry_4[0] == "n":
        input_connector_int = input_node.inputIndex(entry_4[1:])
    else:
        raise Exception("BAD INPUT entry_4: {}, no 'i' or 'n' at start.".format(entry_4))

    if params_entry_1 is not None:
        parameter_processor(output_node, params_entry_1)
    if params_entry_3 is not None:
        parameter_processor(input_node, params_entry_3)

    input_node.setInput(input_connector_int, output_node, output_connector_int)

#a_node = hou.node("/mat")
#a_string = "cTextureSampler-craig i0 cTextureSampler-john i0 cTextureSampler-dylan i0 cTextureSampler-bob i0 ecraig i0 edylan i0"
    
#string_processor(a_node, a_string)


# examples
# cTextureSampler!param_name:blah i0 eHello i0
# cTextureSampler-peter!param_name:blah i0 eSam i0


# regarding parameters, in contents, you can use the following:
# '+' = set 1 (tick box)
# '-' = set 0 (tickbox)
# '=' = press button

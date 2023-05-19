'''
    GMIC RUNNER: Wrapper for GMIC Command Line (for Windows)
    References
    GMIC: https://gmic.eu
    Droste Effect: https://www.flickr.com/groups/88221799@N00/discuss/72157601071820707/
    Get list of all filters: gmic parse_gui > filter_list.txt
                             gmic parse_gui json output_text filter_list.json
    Get specific filter(s wildcard) params as json file, eg get all filters containing filter_str as json
    gmic parse_gui json,filter_str output_text out.json
    Note that spaces in file names need to be escaped for example
    gmic parse_gui json, Deformations Continuous Droste output_text droste.json
    to transform from cmyk to rgb add 'to_rgb' to execution pipeline (converts 32Bit to 24Bit)
'''

import json
import os
import pprint
import subprocess
from subprocess import Popen
from subprocess import PIPE
import pandas as pd

# Filter List (onyl Selected)
FILTER_DROSTE_DICT = {
      "name": "Continuous Droste", "lang": "en", "command": "souphead_droste10", "parameters": [
      { "type": "float", "name": "Inner Radius", "default": "40", "min": "1", "max": "100", "pos": "1" },
      { "type": "float", "name": "Outer Radius", "default": "100", "min": "1", "max": "100", "pos": "2" },
      { "type": "float", "name": "Periodicity", "default": "1", "min": "-6", "max": "6", "pos": "3" },
      { "type": "int", "name": "Strands", "default": "1", "min": "-6", "max": "6", "pos": "4" },
      { "type": "int", "name": "Zoom", "default": "1", "min": "1", "max": "100", "pos": "5" },
      { "type": "int", "name": "Rotate", "default": "0", "min": "-360", "max": "360", "pos": "6" },
      { "type": "int", "name": "X-Shift", "default": "0", "min": "-100", "max": "100", "pos": "7" },
      { "type": "int", "name": "Y-Shift", "default": "0", "min": "-100", "max": "100", "pos": "8" },
      { "type": "int", "name": "Center X-Shift", "default": "0", "min": "-100", "max": "100", "pos": "9" },
      { "type": "int", "name": "Center Y-Shift", "default": "0", "min": "-100", "max": "100", "pos": "10" },
      { "type": "int", "name": "Starting Level", "default": "1", "min": "1", "max": "20", "pos": "11" },
      { "type": "int", "name": "Number of Levels", "default": "10", "min": "1", "max": "20", "pos": "12" },
      { "type": "int", "name": "Level Frequency", "default": "1", "min": "1", "max": "10", "pos": "13" },
      { "type": "separator" },
      { "type": "bool", "name": "Show Both Poles", "default": "0", "pos": "14" },
      { "type": "int", "name": "Pole Rotation", "default": "90", "min": "-180", "max": "180", "pos": "15" },
      { "type": "int", "name": "Pole Long", "default": "0", "min": "-100", "max": "100", "pos": "16" },
      { "type": "int", "name": "Pole Lat", "default": "0", "min": "-100", "max": "100", "pos": "17" },
      { "type": "separator" },
      { "type": "bool", "name": "Tile Poles", "default": "0", "pos": "18" },
      { "type": "bool", "name": "Hyper Droste", "default": "0", "pos": "19" },
      { "type": "int", "name": "Fractal Points", "default": "1", "min": "1", "max": "10", "pos": "20" },
      { "type": "separator" },
      { "type": "bool", "name": "Auto-Set Periodicity", "default": "0", "pos": "21" },
      { "type": "bool", "name": "No Transparency", "default": "0", "pos": "22" },
      { "type": "bool", "name": "External Transparency", "default": "1", "pos": "23" },
      { "type": "bool", "name": "Mirror Effect", "default": "0", "pos": "24" },
      { "type": "bool", "name": "Untwist", "default": "0", "pos": "25" },
      { "type": "bool", "name": "Do Not Flatten Transparency", "default": "0", "pos": "26" },
      { "type": "separator" },
      { "type": "bool", "name": "Show Grid", "default": "0", "pos": "27" },
      { "type": "bool", "name": "Show Frame", "default": "0", "pos": "28" },
      { "type": "separator" },
      { "type": "bool", "name": "Antialiasing", "default": "1", "pos": "29" },
      { "type": "choice", "name": "Edge Behavior X", "default": "0", "pos": "30", "choices": { "0": "Blank", "1": "Wrap", "2": "Reflect", "3": "Rotate" } },
      { "type": "choice", "name": "Edge Behavior Y", "default": "0", "pos": "31", "choices": { "0": "Blank", "1": "Wrap", "2": "Reflect", "3": "Rotate" } },
      { "type": "separator" },
      { "type": "note", "text": "This filter is a conversion of the Mathmap script originally proposed here:"},
      { "type": "link", "name": "Droste effect for Mathmap.", "url": "https://www.flickr.com/groups/88221799@N00/discuss/72157601071820707/", "align": "center" },
      { "type": "note", "text": "Original design by Breic and coding by Josh Sommers."},
      { "type": "separator" },
      { "type": "note", "text": "Author : Souphead.      Latest update : 2016/19/01."}
      ]
    }

SKIP_TYPES = ["separator","link","note"]
STRING_PARAM_TYPES = ["text","point"]
QUOTE = '\"'

def get_param_string_from_dict(filter_dict:dict,params_cust:dict={},
    as_dict:bool=False,verbose:bool=False):
    """ transforms the filter list dictionary into comma separated parameter list
        if as_dict is set, list will be returned as key-value dictionary
    """

    params = filter_dict["parameters"]
    filter_name = filter_dict['name']
    command = filter_dict['command']
    if verbose:
        print("\n--------------")
        print(f"{filter_name} ({command}), #params: {len(params)}\n")
    param_num_last = 0
    param_list = []
    param_name_list = []

    for param in params:
        if verbose:
            print(f"Parameter:\n{pprint.pformat(param)}\n")

        param_type = param.get("type")

        if param.get("pos") is None:
            continue

        param_name = param['name']
        param_pos = int(param['pos'])

        if param_pos>param_num_last:
            param_num_last = param_pos
        else:
            print("WARNING: WRONG PARAMETER ORDER")

        param_value = param.get('default')

        if param_type == "point":
            param_value = param["position"]
        elif param_type == "text":
            param_value = QUOTE + param_value + QUOTE

        if param_value:
            try:
                if param_type in STRING_PARAM_TYPES:
                    pass
                else:
                    param_value = int(param_value)
            except ValueError:
                print(f"Conversion error for Param {param_name} <{param_type}>, value:{param_value}")

        param_cust = params_cust.get(param_name,None)

        if param_cust:
            param_value = param_cust

        param_list.append(str(param_value))
        param_name_list.append(str(param_name))

    param_string = ",".join(param_list)
    param_dict = dict(zip(param_name_list,param_list))

    if verbose:
        print("---- Output Parameters -----")
        print(pprint.pformat(param_dict,compact=True))
        #print(param_dict)

    if as_dict:
        return param_dict
    else:
        return param_string

def get_dict_from_param_string(file_path:str,filter_file_name:str="filter.json",
                               filter_str=None,cust_value_dict:dict={},verbose=False):
    """ reads filter command and parameters (as from gmix commandline or graphic client)
         and transforms it into a dictionary. Can be used to tweak the default value more easily
         file_path, file_name: Path pointing to filter json
         filter_str: Filter string
         cust_value_dict: Custom values in a dictionary. key corresponds to parameter name in json
         verbose: output of execution
         returns params as filter dictionary
    """
    # get_dict_from_param_String()
    if verbose:
        print("-------------------")
        print(f"Filter string: {filter_str}")

    firstspace = filter_str.find(" ")
    command,param_s = filter_str[:firstspace],filter_str[firstspace:]
    param_list = list(map(str.strip,param_s.split(",")))

    if verbose:
        print(command,":",param_list,"num params",len(param_list))

    filter_dict = read_filter_params(file_path,filter_file_name,command)


    # get a dataframe containing only params with "pos"
    df_params = pd.DataFrame.from_dict(filter_dict["parameters"])
    df_params.dropna(subset = ["pos"], inplace=True)
    df_params["pos"]=df_params[["pos"]].apply(pd.to_numeric,downcast="integer")
    df_params.sort_values(by=['pos'])

    # get the number of params per param name ( the last col is filled wioth a 1 can be wrong
    df_params["pos_diff"]=df_params["pos"].diff().shift(-1).fillna(1)
    # convert to int, get cumulated sum
    df_params[["pos","pos_diff"]]=df_params[["pos","pos_diff"]].apply(pd.to_numeric,downcast="integer")
    # all objects with type point have a pos_diff of 2
    df_params.loc[df_params["type"]=="point","pos_diff"]=2
    # cumulate
    df_params["pos_cum"]=df_params["pos_diff"].cumsum()

    max_pos = df_params["pos"].max()
    cum_pos = df_params["pos_cum"].max()

    # in case the last one is point, max pos needs to be corrected
    if df_params.iloc[-1]["type"] == "point":
        max_pos += 1

    if  max_pos == cum_pos:
        if verbose:
            print(f"Max Pos is {max_pos} and the same as cumulated num of params, everything ok!")
    else:
        print("Max Pos {max_pos} <> {cum_pos} (cumulated number of params, pls check !)")

    # now get a list with param name and ranges for given parameter, apply it to parameters in json
    param_index_list = list(zip(df_params.name,df_params.pos,df_params.pos_cum))
    param_list_s = list(map(str, param_list))
    param_dict_list = filter_dict["parameters"]
    for param_index in param_index_list:
        param_name = param_index[0]
        param_s = ",".join(param_list_s[(param_index[1]-1):param_index[2]])
        # overwrite with custom value
        custom_value = cust_value_dict.get(param_name)
        if not custom_value is None:
            param_s = str(custom_value)

        param_s = param_s.strip(QUOTE)

        #now copy param value into default field
        for param_dict in param_dict_list:

            if param_dict.get("pos") is None:
                continue

            if param_dict["name"] == param_name:
                param_name_set = "default"
                old_value = param_dict.get(param_name_set)

                if old_value is None:
                    if param_dict["type"] == "point":
                        param_name_set = "position"
                        old_value = str(param_dict.get(param_name_set))

                if old_value is None:
                    print(f"### There is no field {param_name_set} for parameter: {param_name} ###")

                old_value = str(old_value)

                param_dict[param_name_set] = param_s
                s_param = str(param_index[1]).strip(QUOTE)

                if not param_index[1]==param_index[2]:
                    s_param += ".."+str(param_index[2])
                if verbose:
                    if  old_value == param_s:
                        print(f"({s_param.zfill(2)}) {param_name}:" +
                              f" {param_s} (NO CHANGE)")
                    else:
                        print(f"({s_param.zfill(2)}) {param_name}:" +
                              f" {param_s} (old: {old_value})")
                break

    if verbose:
        print("-------------------")
        print(f"Parameter Dict:\n{pprint.pformat(filter_dict)}")
        print("-------------------\n")

    return filter_dict

def get_param_list(filter_dict:dict,default_dict:bool=False,verbose=False):
    """ gets the Parameter list from param dictionary
        for all control parameters
        if default_dict is set to true dictionary with default values is output
    """
    param_list = []
    default_list = []

    filter_name = filter_dict['name']
    command = filter_dict['command']
    params = filter_dict["parameters"]
    last_pos = 0

    if verbose:
        print(f"--- Param List for {filter_name} [{command}]")

    for param in params:

        param_type = param["type"]
        if param_type in SKIP_TYPES:
            continue

        param_pos = int(param["pos"])
        param_name = param["name"]
        param_default = param["default"]

        if param_pos < last_pos:
            print(f"wrong order, reading param {param_name}")
            continue

        last_pos = param_pos
        param_list.append(param_name)
        if param_type == "float":
            param_default = float(param_default)
        elif (param_type == "int") or (param_type == "bool"):
            param_default = int(param_default)

        default_list.append(param_default)

        if verbose:
            print(f"({str(param_pos).zfill(2)}) {param_name} <{param_type}>: {param_default}")

    if default_dict:
        return dict(zip(param_list,default_list))
    else:
        return param_list

def process_image(file_path,file_in,file_out,filter_dict:dict,cust_params:dict=None):
    """ executes the gmic filter and writes a new filtered image
        returns status code """
    # get the params for given filter
    command = filter_dict['command']
    filter_name = filter_dict['name']
    param_str = get_param_string_from_dict(filter_dict,cust_params)
    command_params = ["gmic","-input",file_in,command,param_str,"to_rgb","-output",file_out]

    print(f"\n-- Filter:{filter_name}, CREATE IMAGE {file_out} ----------------------")
    print("   EXECUTE "," ".join(command_params))
    process_status = subprocess.call(command_params, shell=True,cwd=file_path)
    print("   FINISHED, CODE:",process_status,"\n----------------------")
    return process_status

def get_filter_name_param(filter_name:str):
    """ escapes spaces in filter name / wrap apostrophes"""
    escaped_filter_name = "\\ ".join(filter_name.split(" "))
    filter_name_param = QUOTE + "json,"+ escaped_filter_name + QUOTE
    return filter_name_param

def save_filter_params(filter_name:str,file_path:str,file_name:str="filter.json"):
    """ gets the filter params as json for a given filter name and saves them to json"""
    filter_name_param = get_filter_name_param(filter_name)
    command_params = ["gmic","parse_gui",filter_name_param,"output_text",file_name]
    process_status = subprocess.call(command_params, shell=True,cwd=file_path)
    return process_status

def create_filter_params_json(file_name:str="filter_list.json",subfilters:str=None):
    """ convenience method to create the filter list with params as json
        gmic parse_gui json output_text filter_list.json
        subfilters will only generate a subset or a single filter, eg subfilters='Artistic/'
        will only generate json for all Filters of Artistic category
        Output will be shown in standard output console during processing
    """
    filter_cats = "json"
    if not subfilters is None:
        filter_cats += ","+subfilters

    command_params = ["gmic","parse_gui",filter_cats,"output_text",file_name]
    print("Command:",(" ".join(command_params)))

    with Popen(command_params, stdout=PIPE, bufsize=1,
               universal_newlines=True) as p:
        for line in p.stdout:
            print(line, end='')
    return p.returncode

def read_filter_params(file_path:str,file_name:str="filter.json",filter_str=None,metadata=False,verbose=False):
    """ reads filter parameter file from json
        will read only the first filter entry of the first category if filter_str is None
        otherwise it will look either for command or name
        if metadata is true, filter + list of available filters is returned in a dictionary with
        command as key
    """
    filter_params = None
    fp = os.path.join(file_path,file_name)

    with open(fp,encoding="utf-8",errors="ignore") as f:
        filter_params = json.load(f,strict=False)

    filter_dict = None
    if filter_str is None:
        filter_dict = filter_params["categories"][0]["filters"][0]

    filter_categories = filter_params["categories"]
    gmic_filter_list_dict = {}

    for filter_category in filter_categories:
        filter_cat_name = filter_category["name"]
        if verbose:
            print("\n---- FILTER CATEGORY ",filter_cat_name," ----")
        gmic_filter_list = filter_category["filters"]

        for gmic_filter in gmic_filter_list:
            gmic_dict = {}
            gmic_dict["name"] = gmic_filter["name"]
            gmic_dict["command"] = gmic_filter["command"]
            gmic_dict["category"] = filter_cat_name
            gmic_dict["num_params"] = len(gmic_filter["parameters"])

            if (filter_dict is None) and \
               ((filter_str in gmic_dict["command"]) or (filter_str in gmic_dict["name"])):
                filter_dict = gmic_filter

            if verbose:
                print(f'     {gmic_dict["name"]} ({gmic_dict["command"]}), params:{gmic_dict["num_params"]}')
            gmic_filter_list_dict[gmic_dict["command"]] = gmic_dict

    if not (filter_dict is None) and verbose:
        print("\n------------------------")
        print(f"\nFilter {filter_dict['name']} {filter_dict['command']}\n{pprint.pformat(filter_dict)}")
        print("------------------------")

    if metadata:
        out = {"filter_dict":filter_dict,"filter_list_dict":gmic_filter_list_dict}
    else:
        out = filter_dict
    return out

def rotate_droste(file_path,file_in,file_out,angle=180,cust_params:dict=None):
    """ Droste Filter: Creates a sequence of Droste Images with incremental rotation angle """
    angle_current = 0
    # initialize cust params / at least rotation
    if not cust_params:
        cust_params = {}
    file_prefix = file_out.split(".")[0]
    file_ext = file_out.split(".")[1]

    while angle_current < 360:
        cust_params["Rotate"] = str(angle_current)
        file_out_current = file_prefix + "_" + cust_params["Rotate"].zfill(3) + "." + file_ext
        process_image(file_path,file_in,file_out_current,FILTER_DROSTE_DICT,cust_params)
        angle_current += angle

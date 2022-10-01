""" parsing Camera Menu from CSV File """

from datetime import datetime
import pandas as pd
from pandas import isna
import json
from json import JSONDecodeError

# Columns Definitions
COL_NUM="#"
COL_TOTAL_NUM="##"
COL_CAMERA="Camera"
COL_MENU="Menu"
COL_SUBMENU="Submenu"
COL_PAGE="Page"
COL_FUNCTION="Function"
COL_ACTIONS="Actions"
COL_CUSTOM="Custom"
COL_FUNC="function"
COL_CUST="custom"
COL_DESCRIPTION="description"
COL_OPTIONS="options"
COL_FUNC_DICT="function_dict"
# COL KEY LIST for putting information into info dictionary
COL_LIST=[COL_NUM,COL_FUNC,COL_ACTIONS,COL_DESCRIPTION,COL_CUSTOM,
          COL_MENU,COL_SUBMENU,COL_PAGE,COL_CAMERA,COL_TOTAL_NUM]

def get_long_desc(line):
    SEP=">"
    s_out="("+str(line[COL_NUM]).zfill(3)+") "
    s_out+=line[COL_MENU]+SEP+line[COL_SUBMENU]+" ("+str(line[COL_PAGE])+")"
    s_out+=SEP+line[COL_FUNCTION]
    return s_out

def get_options(option):
    """ parses an option as string, list or json """
    o_out=None
    s_option=str(option).strip()
    if "{" in s_option:
        try:
            o_out=json.loads(s_option)
            # print((o_out))
        except JSONDecodeError as e:
            print(f"*** JSON PARSING ERROR, string {s_option}, ERROR: {e}")
    elif  "," in s_option:
        o_out=s_option.split(",")
        o_out=[s.strip() for s in o_out if len(s)>0]
    else:
        o_out=s_option
    return o_out

def int2str(v):
    """ converts to string """
    if isinstance(v,float):
        if isna(v):
            return v
        else:
            return str(int(v))
    else:
        return v

def get_function_with_key(line):
    """ converts to function """
    return ("("+str(line["#"]).zfill(3)+") "+line[COL_FUNCTION])

def get_function_dict(line):
    return {k:line[k] for k in COL_LIST}

def read_csv(fp:str,decimal=",",delimiter=";"):
    """ reads the raw data from csv and puts it into df """
    df_data = pd.read_csv(fp, header=0, decimal=decimal, delimiter=delimiter)
    df_data[COL_FUNC]=df_data.apply(get_function_with_key,axis=1)
    df_data[COL_DESCRIPTION]=df_data.apply(get_long_desc,axis=1)
    df_data[COL_CUST]=df_data[COL_CUSTOM].map(int2str)
    df_data[COL_OPTIONS]=df_data[COL_ACTIONS].map(get_options)
    df_data[COL_FUNC_DICT]=df_data.apply(get_function_dict,axis=1)
    df_data=df_data.drop([COL_CUSTOM,COL_ACTIONS,COL_FUNCTION],axis=1)
    return df_data

def get_dict_from_df(df_data):
    """ returns dataframe as dict """
    return dict(zip(list(df_data[COL_FUNC]),list(df_data[COL_FUNC_DICT])))

def get_menu_dict(camera:str,df_data:pd.DataFrame)->dict:
    """ returns camera functions in menu hierarchy"""
    df_cam=df_data.copy()
    df_cam=df_cam[df_cam[COL_CAMERA]==camera]
    df_cam=df_cam.drop([COL_TOTAL_NUM],axis=1)
    menu_dict={}
    menu_list=list(df_cam[COL_MENU].unique())
    menu_dict = {key: None for key in menu_list}
    for menu in menu_list:
        df_submenu=df_cam[df_cam[COL_MENU]==menu]
        submenu_list=list(df_submenu[COL_SUBMENU].unique())    
        submenu_dict={}
        for submenu in submenu_list:        
            df_submenu_entries=df_submenu[df_submenu[COL_SUBMENU]==submenu]
            func_list=list(df_submenu_entries[COL_DESCRIPTION])
            func_dict_list=list(df_submenu_entries[COL_OPTIONS])
            function_dict=dict(zip(func_list,func_dict_list))
            submenu_dict[submenu]=function_dict
        menu_dict[menu]=submenu_dict
    return menu_dict

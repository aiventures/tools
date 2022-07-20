""" module to read write some commonplace data """
#from code import compile_command
import os
#import re
#import shutil
#from datetime import date
from pathlib import Path
#import shlex
#import subprocess
import json
import traceback
from tools import img_file_info_xls as img_info

# functions to read file content
displayfunctions_dict={"url":"get_url_from_link",
                       "txt":"read_txt_file",
                       "jpg":"get_img_metadata_exiftool",
                       "json":"read_json"
                      }
exif_info={}

def read_txt_file(filepath,encoding='utf-8',comment_marker="#"):
    """ reads data as lines from file
    """
    lines = []
    try:
        with open(filepath,encoding=encoding,errors='backslashreplace') as fp:
            for line in fp:
                if len(line.strip())==0:
                    continue
                if line[0]==comment_marker:
                    continue
                lines.append(line)
    except:
        print(f"Exception reading file {filepath}")
        print(traceback.format_exc())
    return lines

def read_json(filepath:str):
    """ Reads JSON file"""
    data = None

    if not os.path.isfile(filepath):
        print(f"File path {filepath} does not exist. Exiting...")
        return None

    try:
        with open(filepath,encoding='utf-8') as json_file:
            data = json.load(json_file)
    except:
        print(f"**** Error opening {filepath} ****")
        print(traceback.format_exc())
        print("***************")

    return data

def save_json(filepath,data:dict):
    """ Saves dictionary data as UTF8 """

    with open(filepath, 'w', encoding='utf-8') as json_file:
        try:
            json.dump(data, json_file, indent=4,ensure_ascii=False)
        except:
            print(f"Exception writing file {filepath}")
            print(traceback.format_exc())

        return None

def get_url_from_link(f):
    """ reading url from windows link """
    lines=read_txt_file(f)
    return [l.split("=")[1].strip() for l in lines if l.startswith("URL=")][0]

def get_img_metadata(f):
    """ reading EXIF Data / requires PIL Image """
    return img_info.read_exif(f)

def get_img_metadata_exiftool(f):
    """ reading EXIF Data from search/ requires EXIFTOOL """
    return exif_info.get(str(f),"NO EXIF DATA FOUND")

def read_file_info(fp,content=True,type_filters=[]):
    """ reading file contents for supported file types """
    global exif_info
    subpath_dict={}

    # read image metadata files
    if content:
        #read_exif=False
        if (not bool(type_filters)) or ("jpg" in type_filters):
            try:
                exif_info=img_info.exiftool_read_meta_recursive(fp)
            except Exception:
                print("Exception reading exif files")
                # print(traceback.format_exc())

    # functions to decode
    for subpath,_,files in os.walk(fp):
        p_path=Path(subpath).absolute()
        subpath_info=subpath_dict.get(subpath,{})
        _=subpath_info.get("files",[])
        file_dict={}
        for f in files:
            pf=Path.joinpath(p_path,f)
            filetype=pf.suffix[1:]
            # only process if in filter
            if bool(type_filters) and not filetype in type_filters:
                continue
            #stem=pf.stem
            #print(f"{f}, suffix: {suffix}, filetype: {filetype},")
            display_func=displayfunctions_dict.get(filetype)
            file_content=None
            if content and display_func:
                file_content=globals()[display_func](pf)
            if content:
                file_dict[f]={"filetype":filetype,"content":file_content}
            else:
                file_dict[f]={"filetype":filetype}
        subpath_info["file_details"]=file_dict
        subpath_dict[subpath]=subpath_info
    return subpath_dict

def print_file_info(file_info_dict):
    """ output of file information """
    for p,path_info in file_info_dict.items():
        print(f"*** {p}")
        file_details=path_info["file_details"]
        #print(file_details)
        for filename,filedata in file_details.items():
            content=filedata.get("content",None)
            # print(f"open \"{os.path.join(p,filename)}\"  ({type(content)})")
            print(f"open \"{os.path.join(p,filename)}\"")
            if not content is None:
                try:
                    print(str(content))
                except:
                    try:
                        print(str(content).encode('utf-8').decode('cp1252','ignore'))
                    except:
                        print(str(content).encode('utf-8').decode('ascii','ignore'))
    return None

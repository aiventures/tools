""" module to read write some commonplace data """
#from code import compile_command
import os
import sys
#import glob

import re
#import shutil
#from datetime import date
from pathlib import Path
#import shlex
#import subprocess
import json
import traceback
import yaml
from yaml import CLoader
import logging

# https://superuser.com/questions/609447/how-to-install-the-win32com-python-library
# pip install -U pypiwin32
import win32com.client

from tools import img_file_info_xls as img_info

logger = logging.getLogger(__name__)

# byte order mark for some utf8 file types
BOM = '\ufeff'

# functions to read file content
displayfunctions_dict={"url":"get_url_from_link",
                       "txt":"read_txt_file",
                       "jpg":"get_img_metadata_exiftool",
                       "json":"read_json",
                       "lnk":"get_fileref_from_shortcut"
                      }
exif_info={}

def read_txt_file(filepath,encoding='utf-8',comment_marker="#",skip_blank_lines=True):
    """ reads data as lines from file
    """
    lines = []
    bom_check = False
    try:
        with open(filepath,encoding=encoding,errors='backslashreplace') as fp:
            for line in fp:
                if not bom_check:
                    bom_check = True
                    if line[0] == BOM:
                        line = line[1:]
                        logger.warning(f"Line contains BOM Flag, file is special UTF-8 format with BOM")
                if len(line.strip())==0 and skip_blank_lines:
                    continue
                if line[0]==comment_marker:
                    continue
                lines.append(line.strip())
    except:
        logger.error(f"Exception reading file {filepath}",exc_info=True)
    return lines

def save_txt_file(filepath,data:str,encoding='utf-8'):
    """ saves string to file
    """
    try:
        with open(filepath,encoding=encoding,mode="+wt") as fp:
            fp.write(data)
    except:
        logger.error(f"Exception writing file {filepath}",exc_info=True)
    return


def read_yaml(filepath:str):
    """ Reads YAML file"""

    if not os.path.isfile(filepath):
        logger.warning(f"File path {filepath} does not exist. Exiting...")
        return None

    data = None

    try:
        with open(filepath, encoding='utf-8',mode='r') as stream:
            data = yaml.load(stream,Loader=CLoader)

    except:
        logger.error(f"**** Error opening {filepath} ****",exc_info=True)
    return data


def read_json(filepath:str):
    """ Reads JSON file"""
    data = None

    if not os.path.isfile(filepath):
        logger.warning(f"File path {filepath} does not exist. Exiting...")
        return None

    try:
        with open(filepath,encoding='utf-8') as json_file:
            data = json.load(json_file)
    except:
        logger.error(f"**** Error opening {filepath} ****",exc_info=True)

    return data

def save_json(filepath,data:dict):
    """ Saves dictionary data as UTF8 json """
    # TODO encode date time see
    # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

    with open(filepath, 'w', encoding='utf-8') as json_file:
        try:
            json.dump(data, json_file, indent=4,ensure_ascii=False)
        except:
            logger.error("Exception writing file {filepath}",exc_info=True)

        return None

def save_yaml(filepath,data:dict):
    """ Saves dictionary data as UTF8 yaml"""
    # TODO encode date time and other objects in dict see
    # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

    with open(filepath, 'w', encoding='utf-8') as yaml_file:
        try:
            yaml.dump(data,yaml_file,default_flow_style=False)
        except:
            logger.error(f"Exception writing file {filepath}",exc_info=True)
        return None



def md2toc(f:str,as_string:bool=True):
    """ reads contents of a markdown file, extracts header lines to table of contents
        returns header lines as string or list
    """
    RE_SPECIAL_CHARS="[\\\;:().,;/]"

    REGEX_HEADER = "^(#+) (.+)\n"
    REGEX_LINK = r"\[(.+)\]\(.+\)"
    MD_ANCHOR = "[_LABEL_](#_LINK_)"
    MD_INDENT=2
    lines_toc=[]
    lines_in = read_txt_file(f,comment_marker="xxx")
    for l in lines_in:
        match = re.findall(REGEX_HEADER,l)
        if match:
            level=len(match[0][0])
            label=match[0][1].strip()
            link_text = re.findall(REGEX_LINK,label)
            if link_text:
                label = link_text[0]

            # replace special characters
            link=re.sub(RE_SPECIAL_CHARS,"",label)
            link=link.replace(" ","-").lower()
            anchor_link=MD_ANCHOR.replace("_LABEL_",label)
            anchor_link=anchor_link.replace("_LINK_",link)
            out_string=(level-1)*MD_INDENT*" "+"* "+anchor_link+" "*MD_INDENT
            lines_toc.append(out_string)
    if as_string:
        return "\n".join(lines_toc)+"\n"
    else:
        return lines_toc

def get_fileref_from_shortcut(f):
    """ reads file location from windows shortcut
        https://stackoverflow.com/questions/397125/reading-the-target-of-a-lnk-file-in-python
    """
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(f))
    return shortcut.Targetpath

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
                logger.debug("GETTING EXIF DATA")
                exif_info=img_info.exiftool_read_meta_recursive(fp,debug=False)
            except Exception:
                logger.error("Exception reading exif files",exc_info=True)


    logger.debug("READING FILES")
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
        logger.debug(f"*** {p}")
        file_details=path_info["file_details"]
        #print(file_details)
        for filename,filedata in file_details.items():
            content=filedata.get("content",None)
            # print(f"open \"{os.path.join(p,filename)}\"  ({type(content)})")
            logger.debug(f"FILE \"{os.path.join(p,filename)}\"")
            if not content is None:
                try:
                    logger.debug(f"  =>  {str(content)}")
                except:
                    try:
                        logger.debug(str(content).encode('utf-8').decode('cp1252','ignore'))
                    except:
                        logger.debug(str(content).encode('utf-8').decode('ascii','ignore'))
    return None

def render_lines_as_table(lines:list=None,contains_title:bool=True,separator:str="\t",table_sep:str="|",
                          title_line_separator:str="---",title_col_separator:str="|")->list:
    """ renders strings as tables  """

    def get_table_line(line_str,sep:str=separator,table_sep:str=table_sep):
        values = line_str.split(separator)
        values =  [v.strip() for v in values]
        return table_sep+table_sep.join(values)+table_sep

    out = []
    if contains_title:
        _lines = lines[1:]
        column_titles=lines[0].split(separator)        
        out.append(get_table_line(lines[0],table_sep=title_col_separator))
        if title_line_separator:
            n=len(column_titles)
            # markdown syntax
            title_line_str=n*(title_col_separator+title_line_separator)+title_col_separator
            out.append(title_line_str)
    else:
        _lines = lines
        column_titles=[]
    for line in _lines:
        out.append(get_table_line(line,sep=separator,table_sep=table_sep))
    return out

test_lines=["A sdfjhsgd kjjksdgh kjshdg \tB\tC","1\t2\t3","4\t5\t6"]

def test():
    """ Spielwiese """
    # s = r"safkjh ; asfh/faj af\kj)ha(fs j"
    # print(s)
    # # regex for special characters
    # re_char = "[\\\;:().,;/]"
    # result = re.findall(re_char,s)
    # result2 = re.sub(re_char,"",s)
    # result2 = result2.replace(" ","-")
    rendered_lines = render_lines_as_table(test_lines,title_col_separator="||",title_line_separator=None)
    print("\n".join(rendered_lines))

    pass


if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    test()

""" renaming of video files: extracts series, episode and total number of episodes
    and puts this info as file prefix. Improved V2 version now supporting
    multiple folders
"""

import os
import re
from pathlib import Path
from datetime import datetime
from tools import file_module as fm

REGEX_DICT={}
# regex for checking filename or contents
REGEX_TYPE_TEXT="text"
REGEX_TYPE_FILENAME="filename"
# looks for _s##_f## signature in a mp4 url
REGEX_TXT_URL_SERIES_EPISODE_S=r"^https.+?_s(\d+)[_\/]f(\d+)_.+?mp4$"
REGEX_TXT_URL_SERIES_EPISODE=re.compile(REGEX_TXT_URL_SERIES_EPISODE_S,re.IGNORECASE)
REGEX_DICT["REGEX_TXT_URL_SERIES_EPISODE"]={"type":REGEX_TYPE_TEXT,
                                            "regex":REGEX_TXT_URL_SERIES_EPISODE,
                                            "function":"get_series_episode"}
                                          
# regex to filter out (S##/E##) or (S##_E##) or (##_##) or (##/##)
REGEX_TXT_SERIES_EPISODE_S=r".+?\([S]?(\d+)[\/_][E]?(\d+)\)"
REGEX_TXT_SERIES_EPISODE=re.compile(REGEX_TXT_SERIES_EPISODE_S,re.IGNORECASE)
REGEX_DICT["REGEX_TXT_SERIES_EPISODE"]={"type":REGEX_TYPE_TEXT,
                                        "regex":REGEX_TXT_SERIES_EPISODE,
                                        "function":"get_series_episode"}
REGEX_DICT["REGEX_FILE_SERIES_EPISODE"]={"type":REGEX_TYPE_FILENAME,
                                        "regex":REGEX_TXT_SERIES_EPISODE,
                                        "function":"get_series_episode"}                                        

# looks for (#s#_#s_total#) signature in a file name
REGEX_FILE_PARENTHESES_S=r".+?\((\d+)[_\/](\d+)\)"
REGEX_FILE_PARENTHESES=re.compile(REGEX_FILE_PARENTHESES_S,re.IGNORECASE)
REGEX_DICT["REGEX_FILE_PARENTHESES"]={"type":REGEX_TYPE_FILENAME,
                                            "regex":REGEX_FILE_PARENTHESES,
                                            "function":"get_series"}


# functions to return Episode and Series number
def get_series_episode(regex_result):
    """  returns series and episode from regex result as string """
    return ((regex_result[0][0]).zfill(2),(regex_result[0][1]).zfill(2))

def get_series(regex_result):
    """ returns episode only from regex result as string """
    return ("01",(regex_result[0][0]).zfill(2))

def parse_content(content:list):
    """ parse content of mediathek view txt file """
    content_dict={}
    num_lines=len(content)
    if num_lines == 0:
        return {}
    last_line=""
    linenum=0
    for line in content:
        linenum+=1
        line=line.strip()
        if len(line)==0:
            continue
        elements=line.split(":")
        if last_line.lower()=="website":
            content_dict["url_info"]=line.strip()
            last_line=""
            continue
        elif last_line.lower()=="url":
            content_dict["url"]=line.strip()
            last_line=""
            # now get the remaining lines as description
            description=[l.strip() for l in content[linenum:]]
            description=" ".join(description)
            content_dict["description"]=description
            break

        if len(elements)>1:
            content_dict[elements[0].lower()]=(":".join(elements[1:]).strip())
        last_line=line
    datetime_s=content_dict.get("datum","")+" "+content_dict.get("zeit","")

    try:
        dt=datetime.strptime(datetime_s, '%d.%m.%Y %H:%M:%S')
    except ValueError:
        dt=datetime.now()
    dts=datetime.strftime(dt,"%Y%m%d")
    content_dict["datetime"]=dt.isoformat()
    content_dict["date_s"]=dts
    duration=content_dict.get("dauer","0:0:0")
    duration=[int(d) for d in duration.split(":")]
    content_dict["duration_min"]=60*duration[0]+duration[1]
    alt_name=content_dict.get("titel","")+"-"
    alt_name+=content_dict.get("thema","")+"-"
    alt_name+=content_dict.get("sender","")+"-"
    alt_name+=str(content_dict.get("duration_min","0"))+"-"
    alt_name+=content_dict.get("date_s","")
    alt_name=alt_name.replace(" ","_")
    alt_name=alt_name.replace(".","")
    # special characters are dropped
    alt_name=alt_name.replace("?","")
    alt_name=alt_name.replace("!","")
    content_dict["alt_name"]=alt_name
    return content_dict

def rename_video_files(info_dict,debug=False,save=True,ignore_folders=[],ignore_files=[],save_file_info=True):
    """ gets rename dictionary based on wither rename by file
        or infos in text files """
    rename_dict={}
    num_renames=0
    ignore_folders=[f.lower() for f in ignore_folders]
    for p,p_info in info_dict.items():
        if not os.path.isdir(p):
            continue
        path_parts=[p.lower() for p in Path(p).parts]
        path_name=Path(p).absolute().name
        skip_folder=[ignore_folder in path_part for path_part in path_parts for ignore_folder in ignore_folders ]
        skip_folder=any(skip_folder)
        if skip_folder:
            print(f"SKIP FOLDER '{p}', ignore folders: {ignore_folders}")
            continue
        print(f"\n*** {p}")
        file_dict=p_info["file_details"]
        rename_info={}
        for f,f_info in file_dict.items():
            if debug:
                print(f"File {f}")

            if any([f_ignore in f for f_ignore in ignore_files]):
                print(f"SKIP FILE '{f}', ignore files: {ignore_files}")
                continue

            if not os.path.isfile(os.path.join(p,f)):
                continue

            fp=Path(f)
            f_type=fp.suffix[1:]
            f_stem=fp.stem
            # get info from txt file if present
            txt_info={}
            if f_type=="txt":
                txt_info=f_info
            else:
                txt_file=f_stem+".txt"
                txt_info=file_dict.get(txt_file,{})
            content=txt_info.get("content",[])
            rename_info_dict={}
            parsed_content=parse_content(content)
            if parsed_content.get("alt_name",None):
                alt_name=parsed_content["alt_name"]
                parsed_content["alt_name"]=alt_name+"."+f_type
            rename_info_dict.update(parsed_content)
            #rename_info_dict["content"]=parsed_content
            rename_info_dict["old_name"]=f
            # print(content)
            # now go through all available regexes
            series_episode=None
            name_new=""
            for regex_rule,regex_info in REGEX_DICT.items():  
                # get regex rule and function to extract episode and
                regex=regex_info["regex"]
                function=regex_info["function"]
                line=None
                #rename_dict
                if regex_info["type"] == REGEX_TYPE_FILENAME:
                    regex_match=regex.findall(f_stem)
                    if regex_match:                                            
                        series_episode=globals()[function](regex_match)
                elif regex_info["type"] == REGEX_TYPE_TEXT and content:
                    for line in content:
                        regex_match=regex.findall(line)
                        if regex_match:                               
                            series_episode=globals()[function](regex_match)
                            break                        
                if series_episode:
                    name_new="S"+series_episode[0]+"E"+series_episode[1]+"_"+path_name+"."+f_type

                rename_info[str(f)]=rename_info_dict

                # renaming due to regex
                if name_new:
                    if debug:
                        print(f"RULE MATCH:{regex_rule}; REGEX TYPE:{regex_info['type']}")
                        if line:
                            print(f"LINE:{line.strip()}")
                    if name_new != f:
                        print(f"*   {f} content:({len(content)})")
                        print("    "+name_new)
                    else:
                        print(f"#   {f} content:({len(content)}) ALREADY RENAMED")
                    rename_info_dict["old_name"]=f
                    if f!=name_new:
                        rename_info_dict["new_name"]=name_new                        
                        num_renames+=1
                    break

            # no regex rules found replace by content/alt name if it is there
            if debug and not name_new:
                print("No rename rule was found")

            if (not name_new) and parsed_content:
                name_new=parsed_content.get("alt_name","")
                if debug:
                    print(f"    No rule matched, use alt filename: {name_new}")
                if name_new:                    
                    if f!=name_new:
                        rename_info_dict["new_name"]=name_new
                        num_renames+=1
                        print(f"*   {f} content:({len(content)})")                        
                        print("    "+name_new)
                    else:
                        print(f"#   {f} content:({len(content)}) ALREADY RENAMED")                        

            rename_info[f]=rename_info_dict

        rename_dict[p]=rename_info
        print(f"    NUM RENAMES TOTAL: {num_renames}")

    old_path=os.getcwd()

    execute=False
    if save and num_renames>0 and (input("Save Changes (y)?")=="y"):
        execute=True

    if execute:
        print(f"\n*** RENAME {num_renames} files ***")

    for p,p_renames in rename_dict.items():
        if not p_renames:
            continue
        os.chdir(p)

        if  num_renames > 0:
            print(f"*** {p}")
        if save_file_info:
            dt_now=datetime.now()
            dts=datetime.strftime(dt_now,'%Y%m%d_%H%M%S')
            fm.save_json("file_info_"+dts+".json",p_renames)

        for f,f_info in p_renames.items():
            f_old_name=f_info.get("old_name",None)
            f_new_name=f_info.get("new_name",None)
            if f_new_name:
                print(f"    {f_old_name} -> {f_new_name}")
                if execute:
                    try:
                        os.rename(f_old_name,f_new_name)
                    except OSError  as e:
                        print(e)
    os.chdir(old_path)
    return rename_dict

""" utility to open url link files and json files containing links

    Use Tab Copy to get links with both title url from all opened tabs
    https://chrome.google.com/webstore/detail/tabcopy/micdllihgoppmejpecmkilggmaagfdmb/

    alternatively: Copy all bookmarks into browser folder CTRL
    https://www.groovypost.com/howto/copy-urls-from-all-open-tabs-in-browser/
    https://www.howtogeek.com/723144/how-to-copy-the-url-addresses-of-all-open-tabs-in-chrome
    > Bookmarks > Save all > CTRL SHIFT D
    > CTRL+SHIFT+O > Bookmarks
    Im Folder copy & paste > CTRL A > CTRL C > CTRL V > copy file to txt datei
    Open right now these files won't be parsed
"""

import os
from pathlib import Path
from tools import file_module as fm
import webbrowser

def read_url_json(f_file):
    """ validates json file, if generated from TabCopy Extension as json
        https://chrome.google.com/webstore/detail/tabcopy/micdllihgoppmejpecmkilggmaagfdmb/
        it will copy over the data as dictionary
    """
    # f_dict=fm.read_file_info(f_file,content=True,type_filters=["url"])
    json_list=fm.read_json(f_file)

    url_list=[]

    if not isinstance(json_list,list):
        return {}

    for url_entry in json_list:
        if not isinstance(url_entry,dict):
            continue
        if url_entry.get("title") is None or url_entry.get("url") is None:
            continue

        url_list.append({"title":url_entry.get("title"),"url":url_entry.get("url")})
    return url_list

def get_url_list_from_folder(p_link_folder,links_only=True):
    """ creates list of links from given folder path if no path is set current dir will be used
        links_onl: if true only urls as list will be returned otherwise dictionary woith path as key
    """
    num_links=0
    if not ( p_link_folder and os.path.isdir(p_link_folder)):
        p_link_folder=os.getcwd()
        print(f"{p_link_folder} is not a folder ")
    url_dict=fm.read_file_info(p_link_folder,content=True,type_filters=["url","json"])
    url_out={}
    for p,file_info in url_dict.items():
        url_list=[]
        print(f"--- Folder {p}")
        file_details=file_info["file_details"]
        for f_name,f_info in file_details.items():
            suffix=Path(f_name).suffix
            if suffix.endswith("url"):
                url=f_info.get('content')
                if url:
                    url_list.append({"title":f_name[:-4],"url":url})
                    num_links+=1
                print(f"-   LINK: {f_name[:-4]}:\n    {url}")
            elif suffix.endswith("json"):
                url_list_json=read_url_json(Path(p).joinpath(f_name))
                num_links+=len(url_list_json)
                url_list.extend(url_list_json)
                print(f"#   FILE: {f_name[:-4]}: ({len(url_list_json)}) Links")
                _ = [print(f'-   {l["title"]}:\n    {l["url"]}') for l in url_list_json]
        url_out[p]=url_list
    print(f"--- Number of read links {num_links}")
    if links_only:
        url_list=[]
        _ = [url_list.extend(l) for l in list(url_out.values())]
        url_out = url_list
    return url_out

def open_links(link_list):
    """ Opens Links from list of dictionary items """
    if not isinstance(link_list,list):
        return
    url_list=[link.get("url") for link in link_list if link.get("url") and link.get("url").startswith("http") ]
    print(f"\n--- Opening ({len(url_list)}) Links")
    _ = [print(f"-   {l}") for l in url_list]
    for url in url_list:
            webbrowser.open(url, new=2)

def save_links(fp,link_list):
    """ saving link list as json file """
    fm.save_json(fp,link_list)

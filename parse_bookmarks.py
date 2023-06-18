""" creates a markdown version of exported bookmarks  """
import traceback
import json
import sys
from datetime import datetime as DateTime
from bs4 import BeautifulSoup
from pathlib import Path

def save(filepath,data):
    """ Saves string data / string list """
    if isinstance(data,list):
        data = "\n".join(data)

    with open(filepath, 'w', encoding='utf-8') as f:
        try:
            f.write(data)
        except:
            print(f"Exception writing file {filepath}")
            print(traceback.format_exc())

        return None

def save_json(filepath,data:dict):
    """ Saves dictionary data as UTF8 """

    with open(filepath, 'w', encoding='utf-8') as json_file:
        try:
            json.dump(data, json_file, indent=4,ensure_ascii=False)
        except:
            print(f"Exception writing file {filepath}")
            print(traceback.format_exc())

        return None

def get_soup_from_file(filename):
    """ phpbb """
    try:
        with open(filename,'r',encoding='utf-8') as f:
            contents=f.read()
        soup = BeautifulSoup(contents,"lxml")
        return soup
    except:
        print(traceback.format_exc())

def get_bookmark_tree(f):
    """ creates a dictionary containing all bookmarks and folders in a hirarchical dict tree """
    num_link=0
    soup = get_soup_from_file(f)
    headers = soup.findAll('h3')
    bookmark_tree={}
    last_level=0
    bookmark_tree={}
    num_headers=0

    for header in headers:
        num_headers+=1
        bookmark_folder={}

        # get parents
        header_parents=header.findParents()
        # count the parents / level = <dl><p>
        level=0
        for header_parent in header_parents:
            # we look for <dl><p>
            if header_parent.name=="dl":
                next_elem=header_parent.find_next()
                if next and next_elem.name=="p":
                    level+=1
        level-=1
        ts=header.get("add_date")
        if ts:
            date_s=DateTime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')
        header_info=header.text+" ("+date_s+")"
        hash_value=str(abs(hash(str(num_headers)+header_info))) # hash value used as anchor for md
        bookmark_folder={"index":num_headers,"text":header_info,"level":level,"timestamp":ts,"hash":hash_value}


        # next part isthe <DL><p>... </DL> part
        link_section=header.find_next()
        links = []
        if link_section:
            links = link_section.findChildren("a")
        # get all children links
        link_list={}
        for link in links:
            num_link+=1
            url=link.get("href")
            text=link.text
            if url:
                ts=header.get("add_date",0)
                if ts:
                    date_s=DateTime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')
                    text = "["+str(num_link).zfill(4)+"] "+text+" ("+date_s+")"
                link_list[num_link]={"url":url,"text":text}

        bookmark_folder["links"]=link_list
        bookmark_tree[num_headers] = bookmark_folder

    # finally, determine parents
    for index, bookmark_folder in bookmark_tree.items():
        if index == 1:
            bookmark_folder["parent"]=1
            last_parent = 1
            last_level = 0
            continue
        num = index
        while not num <= 0:
            num -= 1 # search previous elements having a lower level
            if bookmark_tree[num]["level"] < bookmark_folder["level"]:
                bookmark_folder["parent"]=num
                last_level = bookmark_folder["level"]
                last_parent = num
                num = 0
            elif bookmark_folder["level"] == last_level: # sibling, use last parent
                bookmark_folder["parent"]=last_parent
    return bookmark_tree

def create_markdown(bookmark_tree):
    """ creates markdown version of the bookmark tree """
    def create_md_link(text,url):
        """ creates a markdown link """
        if not url.lower().startswith("http"): # local link
            url="#"+url
        return "["+text+"]("+url+")"

    # statistics
    num_links = 0
    num_folders = len(bookmark_tree.keys())
    for index,bookmark_folders in bookmark_tree.items():
        num_links += len(bookmark_folders.get("links").keys())
    # table of coontents
    toc = ["# TOC",f'## **STATS**: **{num_links}** links in **{num_folders}** folders ({DateTime.now().strftime("%Y-%m-%d %H:%M:%S")})']
    link_list_md=[]

    for index in sorted(list(bookmark_tree.keys())):
        if index == 1:
            continue
        bookmark_folder = bookmark_tree[index]
        index_s="["+str(index).zfill(3)+"] "
        hash_value=bookmark_folder["hash"]
        text = bookmark_folder["text"]
        level=bookmark_folder["level"]
        header_line = level*"#"+" "+index_s+text
        links = bookmark_folder.get("links")
        anchor="###### "+hash_value
        # create the table of content
        toc_line=""
        if index > 1:
            toc_line=(level-1)*2*" "+"* "
        toc_line+=level*"#"+" "
        toc_line+=create_md_link(text,hash_value)
        toc.append(toc_line)
        link_list_md.append(anchor)
        link_list_md.append(header_line)
        for index in sorted(list(links.keys())):
            link_info = links[index]
            md_link = create_md_link(link_info["text"],link_info["url"])
            link_list_md.append("* "+md_link)
        link_list_md.append("\n**[TOC](#toc)**\n")

    return [*toc,*link_list_md]

def run(link_file:str):
    """ create stuff """
    p=Path(f)
    if not p.is_file():
        print(f"{f} is not a file, pls check ")
        sys.exit()
    filename=p.stem
    print(f"*** Parsing Links file {link_file}")
    filename=DateTime.now().strftime("%Y%m%d_%H%M%S")+"_"+p.stem+"."
    f_json=Path.joinpath(p.parent,filename+"json")
    f_md=Path.joinpath(p.parent,filename+"md")    
    bookmark_tree = get_bookmark_tree(link_file)
    md_string = create_markdown(bookmark_tree)
    save(f_md,md_string)
    save_json(f_json,bookmark_tree)
    print(f"    Saving files: {str(f_md)}, {str(f_json)}")

if __name__ == "__main__":
    # print(__name__,sys.modules[__name__])
    f=r"C:\path to favorites html"
    run(f)







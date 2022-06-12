""" reads image files from a subfolder and returns a report of
    what needs to be done with images
"""

# https://pillow.readthedocs.io/en/stable/index.html

import os
import re
from datetime import date
from pathlib import Path
from image_meta.persistence import Persistence
import traceback
import json
import pandas as pd
from PIL import Image
from PIL import UnidentifiedImageError
from PIL.ExifTags import TAGS

# Relevant fields
EXIF_FIELDS=["Software","Copyright","Make","Model","LensModel",
                 "FocalLength","FocalLengthIn35mmFilm","FNumber","ISOSpeedRatings","GPSInfo",
                 "DateTime","DateTimeOriginal","ExifImageHeight",
                 "ExifImageWidth","ImageDescription"]

SOFTWARE=["DxO"]
TYPE_RAW=["arw","dng","insp","dop"]
TYPE_META=["geo","tpl"]
TYPE_PROCESSED=["jpg","jpeg"]
TYPE_CLEANUP=["dop","dng","tif","arw","insp"]

FILETYPE_CLASSES_DICT={"TYPE_RAW":TYPE_RAW,
                       "TYPE_META":TYPE_META,
                       "TYPE_JPG":TYPE_JPG,
                       "TYPE_CLEANUP":TYPE_CLEANUP}

DO_NOT_PROCESS_FILES=["metadata.tpl","metadata_exif"]
IGNORE_FOLDERS=["insp","post"]

# YYYYMMDD _  HHMMSS _ 00/10 _ NUM(3DIGITS)
REGEX_INSTAONEX=r"IMG_(\d{8})_(\d{6})_(\d{2})_(\d{3})"
# RAW PREFIX NUM(5DIGITS)
REGEX_ORIGINAL_NAME=r"^(\D{3})(\d{5})\."
REGEX_METADATA_FILES=r"(metadata.tpl|metadata_exif.tpl)"
REGEX_RULE_DICT={"REGEX_INSTAONEX":REGEX_INSTAONEX,
                 "REGEX_ORIGINAL_NAME":REGEX_ORIGINAL_NAME,
                 "REGEX_METADATA_FILES":REGEX_METADATA_FILES}


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

def read_exif(f:str,exif_fields:str=EXIF_FIELDS,software:str=SOFTWARE,
             include_entropy=False,debug=False,include_app=False):
    """ reads exif data from image file """             
    out_dict={}
    try:
        im = Image.open(f)
    except UnidentifiedImageError as e:
        print("EXCEPTION "+str(e))
        return {"filename":f}
    out_dict["filename"]=im.filename
    out_dict["format"]=im.format
    out_dict["bits"]=im.bits
    out_dict["width"]=im.width
    out_dict["height"]=im.height
    out_dict["size"]=round(im.height*im.width/1000000,1)

    # metadata segment
    if include_app:
        out_dict["app"]=im.app

    if include_entropy:
        out_dict["entropy"]=im.entropy()

    exifdata=im.getexif()
    im.close()
    exif_dict=dict([(TAGS.get(tag_id,str(tag_id)),
                    {"tag_id":tag_id,"value":exifdata.get(tag_id,None)}) for tag_id in list(exifdata.keys())])
    if debug:
        print(f"Metadata attributes: {exif_dict.keys()}")

    for exif_field in exif_fields:
        if not exif_dict.get(exif_field,None):
            continue
        value = exif_dict[exif_field]["value"]
        if exif_field == "GPSInfo":      
            # check if there are valid values
            check_value =(value[2][0])
            if (check_value==0) or (check_value.denominator==0):
                continue             
            lat=str(round(float(value[2][0]+value[2][1]/60++value[2][2]/3600),4))
            lon=str(round(float(value[4][0]+value[4][1]/60++value[4][2]/3600),4))        
            value= "https://www.openstreetmap.org/#map=16/"+lat+"/"+lon
            out_dict["url_gps"]=value
        elif exif_field == "ImageDescription":
            out_dict["ImageDescription"]=value.encode('latin-1').decode('utf-8')
        else:
            out_dict[exif_field]=value

    if out_dict.get("url_gps",None):
        out_dict["has_gps"] = True
    else:
        out_dict["has_gps"] = False

    # check for non empty description
    if out_dict.get("ImageDescription",None):
        if len(out_dict["ImageDescription"].strip()) == 0:
            out_dict["has_description"] = False
        else:
            out_dict["has_description"] = True
    else:
        out_dict["has_metadata"] = False

    # check whether it was worked upon with an editing software
    edit_software=out_dict.get("Software",None)
    out_dict["edited"] = False
    if edit_software:
        for s in software:
            if s.lower() in edit_software.lower():            
                out_dict["edited"] = True 
    
    #print([(tag_id,TAGS.get(tag_id, tag_id)) for tag_id,TAGS.get(tag_id, tag_id) in exifdata])

    #return out_dict
    return out_dict

def get_subpath_info_dict(fp:str,type_raw=TYPE_RAW,type_meta=TYPE_META,
                        TYPE_JPG=TYPE_JPG,type_cleanup=TYPE_CLEANUP,
                        debug=False):
    """ reads file information in a given folder path """
    print(f"*** Check Image Files in {fp} ***")    
    p_root=Path(fp)
    subpath_dict={}
    for subpath,subdirs,files in os.walk(fp):
        # get aboslute path
        processed_file_checked=False
        for f in files:

            # print(Path(subpath).is_relative_to(p_root))
            # only consider direct parent paths
            if Path(subpath).parent!=p_root:
                continue

            p_img_parent_folder = Path(subpath).stem
            subpath_info=subpath_dict.get(p_img_parent_folder,{})
            subpath_info["subpath"]=subpath

            num_files=subpath_info.get("num_files",0)
            subpath_info["num_files"]=num_files+1
            f_absolute=os.path.join(subpath,f)
            p=Path(f)
            f_stem=p.stem

            suffix = ""
            if len(p.suffix) >= 1:
                suffix_list=subpath_info.get("suffix_list",[])
                suffix=p.suffix[1:]
                if not suffix in suffix_list:
                    suffix_list.append(suffix)
                subpath_info["suffix_list"]=suffix_list

            # check for a single exported file whether it already contains metadata
            needs_jpg_export=subpath_info.get("needs_jpg_export",True)
            if suffix.lower() in TYPE_JPG:
                needs_jpg_export = False
                # check file for first occurence
                if not processed_file_checked:
                    subpath_info["checked_jpg"]=f
                    file_exif=read_exif(f_absolute)
                    subpath_info["Software"]=file_exif.get("Software",None)
                    subpath_info["Make"]=file_exif.get("Make",None)
                    subpath_info["Model"]=file_exif.get("Model",None)
                    subpath_info["LensModel"]=file_exif.get("LensModel",None)
                    subpath_info["url_gps"]=file_exif.get("url_gps",None)
                    subpath_info["ImageDescription"]=file_exif.get("ImageDescription",None)
                    subpath_info["DateTimeOriginal"]=file_exif.get("DateTimeOriginal",None)
                    subpath_info["has_gps"]=file_exif.get("has_gps",None)
                    subpath_info["has_description"]=file_exif.get("has_description",None)
                    subpath_info["edited"]=file_exif.get("edited",None)
                processed_file_checked=True

            subpath_info["needs_jpg_export"]=needs_jpg_export

            contains_raw=subpath_info.get("contains_raw",False)
            if suffix.lower() in type_raw:
                contains_raw = True
            subpath_info["contains_raw"] = contains_raw

            needs_rename=subpath_info.get("needs_rename",False)

            # for ease of implementation check for length
            # check with regex for out of cam patterns
            if suffix.lower() in type_raw:
                if len(f_stem)==8 or len(f_stem)==26:
                    needs_rename=True
            subpath_info["needs_rename"]=needs_rename

            # check whether files need to be cleaned up
            #print("STEM FUFFIX",f_stem,suffix)
            needs_cleanup=subpath_info.get("needs_cleanup",False)
            # check for metadata
            if suffix.lower() in type_meta:
                if f_stem not in ["default","metadata","metadata_exif"]:
                    needs_cleanup = True
            if suffix.lower() in type_cleanup:
                needs_cleanup = True

            subpath_info["needs_cleanup"]=needs_cleanup

            subpath_dict[p_img_parent_folder]=subpath_info

    return subpath_dict

def save_subpath_info_dict(subpath_info_dict,fp_json=None,fp_xls=None):
    if not fp_json is None:
        Persistence.save_json(fp_json,subpath_info_dict)
    # save as xls
    if not fp_xls is None:
        df=pd.DataFrame.from_dict(subpath_info_dict,orient='index')
        df.to_excel(fp_xls) 



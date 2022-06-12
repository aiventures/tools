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

# FILETYPES
TYPE_RAW=["arw","dng","insp"]
TYPE_META=["geo","tpl","dop"]
TYPE_JPG=["jpg","jpeg"]
TYPE_EXIF_FILE_TYPES=TYPE_JPG
TYPE_EXIF_FILE_TYPES.append("insp")
TYPE_CLEANUP=["tif"]
TYPE_CLEANUP.extend(TYPE_RAW)
TYPE_CLEANUP.extend(TYPE_META)

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

def num_path_in_name(file_dict:dict,p:str):
    """ checks how many files contain path in name """
    files=file_dict[p].get("files",[])
    p_parent=Path(p).stem.lower()
    return sum([1 for f in files if p_parent in (Path(f).stem).lower()])

def get_file_dict(fp:str,regex_file_rules_dict=REGEX_RULE_DICT,
                  filetype_classes_dict=FILETYPE_CLASSES_DICT,exif_file_types=None):
    """ returns a dict with information about files
        also accepts a regex file list to check for rules
    """
    file_dict={}
    p_root=Path(fp)
    p_root_lvl=len(p_root.parts)

    # analyze on folder level
    for subpath,subdirs,files in os.walk(fp):
        for f in files:
            # print("subpath",subpath)
            p=Path(subpath)
            p_parent=Path(os.path.join(*(p.parts)[:-1]))
            #print(f,p_parent)
            p_lvl=len(p.parts)-p_root_lvl
            #print(pf_lvl,p)
            subpath_dict=file_dict.get(subpath,{})
            file_list=subpath_dict.get("files",[])
            file_list.append(f)
            # get number of files and build up statistics
            fp=Path(os.path.join(subpath,f))
            filetypes_dict=subpath_dict.get("file_types",{})
            suffix=fp.suffix[1:]
            filetypes_dict[suffix]=filetypes_dict.get(suffix,0)+1
            subpath_dict["level"]=p_lvl
            subpath_dict["parent"]=p_parent
            subpath_dict["num_files"]=subpath_dict.get("num_files",0)+1
            subpath_dict["file_types"]=filetypes_dict
            subpath_dict["files"]=file_list
            file_dict[subpath]=subpath_dict

    # analyze file names with regex rules
    for p,p_info in file_dict.items():
        files=p_info.get("files",[])

        # check whether files match to path name
        p_info["NUM_PATH_IN_NAME"]=num_path_in_name(file_dict,p)

        # process regexes / check how many rules match
        for regex_rule,regex_string in regex_file_rules_dict.items():
            regex_to_test=re.compile(regex_string,re.I)
            num_matches=sum([1 for f in files if regex_to_test.match(f) is not None])
            p_info[regex_rule]=num_matches

        # check file types
        file_type_dict=p_info.get("file_types",{})
        for file_type,file_num in file_type_dict.items():
            p_info[(file_type.upper())]=file_num

        # check for containing filetype classes
        for filetype_class,filetype_list in filetype_classes_dict.items():
            p_info[filetype_class]=False
            for file_type in file_type_dict.keys():
                ftl = file_type.lower()

                # special case: # tpl is 2 and rule REGEX_METADATA_FILES
                # -> do not count it towards rule of metadata
                if ftl == "tpl" and p_info.get("REGEX_METADATA_FILES",0)==2:
                    continue

                if ftl in filetype_list:
                    p_info[filetype_class]=True

        # read exif files
        if exif_file_types:
            file_exif_dict={}
            for f in files:
                fp=Path(os.path.join(p,f))
                if not (fp.suffix[1:]) in exif_file_types:
                    continue
                file_exif_dict[f]=read_exif(fp)
            if file_exif_dict:
                p_info["FILE_EXIF_DICT"]=file_exif_dict
    return file_dict

def get_filepath_stat_df(file_dict:dict):
    """ gets filepath stats as dataframe """
    filepath_info_dict = {}

    for filepath,filepathinfo_dict in file_dict.items():
        info_dict={}
        for k,v in filepathinfo_dict.items():
            # print(k,type(v))
            if isinstance(v, list):
                info_dict[("NUM_"+k.upper())+"(LIST)"]=len(v)
            elif isinstance(v, dict):
                # add metadata if provided
                if k=="FILE_EXIF_DICT":
                    num_has_metadata=0 # has_metadata
                    num_has_gps=0 # has_gps
                    num_edited=0 # edited
                    num_has_description=0 # has_description
                    for exif_data in v.values():
                        if exif_data.get("has_metadata"):
                            num_has_metadata+=1
                        if exif_data.get("has_gps"):
                            num_has_gps+=1
                        if exif_data.get("edited"):
                            num_edited+=1
                        if exif_data.get("has_description"):
                            num_has_description+=1
                    info_dict["NUM_HAS_METADATA"]=num_has_metadata
                    info_dict["NUM_HAS_GPS"]=num_has_gps
                    info_dict["NUM_EDITED"]=num_edited
                    info_dict["NUM_HAS_DESCRIPTION"]=num_has_description
                info_dict[("NUM_"+k.upper())+"(KEYS)"]=len(v.keys())
            elif isinstance(v, Path):
                info_dict[k]=str(v)
            else:
                info_dict[k]=v
        filepath_info_dict[filepath]=info_dict
    df = pd.DataFrame.from_dict(filepath_info_dict,orient='index')
    df = df.fillna(0)
    return df

def rename_original_img_files(img_info_df:pd.DataFrame,file_dict:dict,
                          save:bool=False,verbose:bool=False,is_panorama_img=False,
                          ignore_folders=IGNORE_FOLDERS):
    # renames image files with original name returns number of renamed files
    num_renamed=0

    # panoramic images have format
    # IMG_YYYYMMDD_HHMMSS_00_###_*.(filetype)
    if is_panorama_img:
        # get foldersthat contain INSTA ONE FILES
        df_rename=img_info_df[img_info_df["REGEX_INSTAONEX"]>0]
        regex_index=r"IMG_\d{8}_\d{6}_\d{2}_(?P<IMG_NUMBER>\d{3})(?P<IMG_SUFFIX>.*)\.(?P<FILETYPE>.*)"
    # not renamed standard image files start with three letters and have five digits
    else:
        # get folders with files that should be renamed
        df_rename=img_info_df[img_info_df["REGEX_ORIGINAL_NAME"]>0]
        regex_index=r"^\D{3}(?P<IMG_NUMBER>\d{5})\.(?P<FILETYPE>.*)"

    regex_path_starts_with_date=r"^\d{8}.*"
    re_starts_with_date=re.compile(regex_path_starts_with_date)

    for fp in df_rename.index:
        p=Path(fp)
        if verbose:
            print(f"\n--- FOLDER {fp} ---")
            
        foldername=p.stem

        # check if folder should be ignored
        ignore=False
        for ignore_folder in ignore_folders:
            if ignore_folder in foldername.lower():
                if verbose:
                    print(f"    Folder {foldername} is ignored as it is a ignore folder ({ignore_folder})")
                ignore=True
                break
        if ignore:
            continue

        if re_starts_with_date.match(foldername):
            p_starts_with_date=True
        else:
            p_starts_with_date=False

        filenames=file_dict[fp].get("files",[])

        #print(filenames)
        for old_filename in filenames:
            p_old=os.path.join(p,old_filename)

            # if folder doesnt contain date info get it from file creation date
            s_date=""
            if not p_starts_with_date:
                s_date=date.fromtimestamp(os.path.getctime(p_old)).strftime("%Y%m%d")+"_"

            #r=re.findall(regex_index,old_filename)
            r_iter=re.finditer(regex_index,old_filename)

            new_filename=""
            for r in r_iter:
                r_dict=r.groupdict()
                new_filename=s_date+foldername+"_"+r_dict["IMG_NUMBER"]+r_dict.get("IMG_SUFFIX","")+"."+r_dict["FILETYPE"]
                num_renamed+=1
                p_new=os.path.join(p,new_filename)
                if verbose:
                    print(F"    - {old_filename: <20} -> {new_filename}")
                    # print(f"      New Filename: {p_new}")
                if save:
                    try:
                        os.rename(p_old,p_new)
                    except (FileExistsError,FileNotFoundError) as e:
                        print(f"EXCEPTION: {repr(e)} for file {p_new}")
    return num_renamed


""" reads image files from a subfolder and returns a report of
    what needs to be done with images
"""

# https://pillow.readthedocs.io/en/stable/index.html

import json
import os
import re
import shlex
import shutil
import subprocess
import traceback
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS

# Relevant fields
EXIF_FIELDS=["Software","Copyright","Make","Model","LensModel",
                 "FocalLength","FocalLengthIn35mmFilm","FNumber","ISOSpeedRatings","GPSInfo",
                 "DateTime","DateTimeOriginal","ExifImageHeight",
                 "ExifImageWidth","ImageDescription"]

SOFTWARE_DXO="DxO"
SOFTWARE_INSTA="Insta360 one x2"
SOFTWARE=[SOFTWARE_DXO,SOFTWARE_INSTA]

# FILETYPES
TYPE_RAW=["arw","dng","insp"]
TYPE_META=["geo","tpl","dop","meta"]
TYPE_JPG=["jpg","jpeg"]
TYPE_PANO=["insp"]
TYPE_EXIF_FILE_TYPES=TYPE_JPG.copy()
TYPE_EXIF_FILE_TYPES.append("insp")
TYPE_CLEANUP=["tif","jpg_original"]
TYPE_CLEANUP.extend(TYPE_RAW)
TYPE_CLEANUP.extend(TYPE_META)

FILETYPE_CLASSES_DICT={"TYPE_RAW":TYPE_RAW,
                       "TYPE_META":TYPE_META,
                       "TYPE_JPG":TYPE_JPG,
                       "TYPE_CLEANUP":TYPE_CLEANUP}

DO_NOT_PROCESS_FILES=["metadata.tpl","metadata_exif.tpl","default.geo"]
IGNORE_FOLDERS=["insp","post"]

# Regex for Date Prefix YYYYMMDD_
REGEX_DATE_PREFIX=r"^(\d{8})_"
# YYYYMMDD _  HHMMSS _ 00/10 _ NUM(3DIGITS)
REGEX_INSTAONEX=r"IMG_(\d{8})_(\d{6})_(\d{2})_(\d{3})"
# RAW PREFIX NUM(5DIGITS)
REGEX_ORIGINAL_NAME=r"^(\D{3})(\d{5})\."
REGEX_METADATA_FILES=r"(metadata.tpl|metadata_exif.tpl)"
REGEX_RULE_DICT={"REGEX_INSTAONEX":REGEX_INSTAONEX,
                 "REGEX_ORIGINAL_NAME":REGEX_ORIGINAL_NAME,
                 "REGEX_METADATA_FILES":REGEX_METADATA_FILES}

# dataframe columns that list number of unnamed filenames
UNNAMED_FILE_COLUMNS=["REGEX_ORIGINAL_NAME","REGEX_INSTAONEX"]

# Subset of EXIF Attributes (-s Notation) that fit my purposes best
# -n outputs values as numerical (mind string handling) and # will force a
# variable to be output as numerical value
EXIF_ATTRIBUTES=["Directory","FileName","FileSize#","DateCreated",
                 "ImageWidth","ImageHeight","ImageSize","Megapixels#",
                 "Make","Model","Lens","LensModel","LensSpec",
                 "FocalLength","ScaleFactor35efl","FOV","FocalLength35efl",
                 "CircleOfConfusion","HyperfocalDistance",
                 "Software","ShutterSpeed","Aperture","ISO","LightValue",
                 "Title","City","Sub-location","Province-State",
                 "Country-PrimaryLocationName","Copyright",
                 "SpecialInstructions",
                 "GPSLatitude","GPSLatitudeRef",
                 "GPSLongitude","GPSLongitudeRef",
                 "GPSPosition","Keywords","DateTime","DateTimeOriginal"]

EXIF_ATTRIBUTES_MINIMUM=["Directory","FileName",
                         "Title","Make","Model","LensModel",
                         "FocalLength","ShutterSpeed",
                         "Aperture","ISO",
                         "LightValue","Software",
                         "SpecialInstructions",
                         "DateTime","DateTimeOriginal"]

# EXIFTOOL commands
CMD_EXIF_DELETE_ALL='EXIFTOOL -all= -r * -ext jpg'
CMD_EXIF_READ_RECURSIVE_TEMPLATE='EXIFTOOL -j EXIF_ATTRIBUTES -c "%.6f" -charset latin -s -r -Directory * -ext jpg'
# CMD_EXIF_READ_ALL_RECURSIVE_TEMPLATE='EXIFTOOL -j EXIF_ATTRIBUTES -c "%.6f" -L -s -r -Directory * -ext jpg -ext arw -ext tif'
CMD_EXIF_READ_ALL_RECURSIVE_TEMPLATE='EXIFTOOL -j EXIF_ATTRIBUTES -c "%.6f" -L -s -r -n -Directory *'


# MAGICK commands
CMD_MAGICK_RESIZE="_MAGICK convert _FILE_IN -resize _IMAGESIZEx -quality _QUALITY _FILE_OUT"

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

def read_exif_attributes(filepath,encoding='utf-8',comment_marker="#",sep=":"):
    """ reads data as lines from file """
    lines = []
    try:
        with open(filepath,encoding=encoding) as fp:
            for line in fp:
                if len(line.strip())==0:
                    continue
                if line[0]==comment_marker:
                    continue
                lines.append(line.split(sep)[0].strip())
    except:
        print(f"Exception reading file {filepath}")
        print(traceback.format_exc())
    return lines

def save_exif_attributes(filepath,attribute_list:list):
    """ list of attributes as command file """

    with open(filepath, 'w', encoding="utf-8") as f:
        for attribute in attribute_list:
            try:
                f.write("-"+attribute+"\n")
                #s = "Data saved to " + filepath
            except:
                print(f"Exception writing file {filepath}")
                print(traceback.format_exc())
                #s = "No data was saved"
    return None


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
        out_dict["has_description"] = False

    # check whether it was worked upon with an editing software
    edit_software=out_dict.get("Software",None)
    out_dict["edited"] = False
    if edit_software:
        for s in software:
            if s.lower() in edit_software.lower():
                out_dict["edited"] = True

    # image considered having metadata
    if out_dict["has_description"]  & out_dict["has_gps"]:
        out_dict["has_metadata"] = True
    else:
        out_dict["has_metadata"] = False

    #print([(tag_id,TAGS.get(tag_id, tag_id)) for tag_id,TAGS.get(tag_id, tag_id) in exifdata])

    #return out_dict
    return out_dict

def get_subpath_info_dict(fp:str,type_raw=TYPE_RAW,type_meta=TYPE_META,
                        type_jpg=TYPE_JPG,type_cleanup=TYPE_CLEANUP):
    """ reads file information in a given folder path """
    print(f"*** Check Image Files in {fp} ***")
    p_root=Path(fp)
    subpath_dict={}
    for subpath,_,files in os.walk(fp):
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
            if suffix.lower() in type_jpg:
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
    """ saving subpath info to a dict """
    if not fp_json is None:
        save_json(fp_json,subpath_info_dict)
        print(f"Saved JSON: {Path(fp_json).absolute()}")
    # save as xls
    if not fp_xls is None:
        df=pd.DataFrame.from_dict(subpath_info_dict,orient='index')
        df.to_excel(fp_xls)
        print(f"Saved XLSX: {Path(fp_xls).absolute()}")

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
    for subpath,_,files in os.walk(fp):
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
                if not fp.suffix[1:] in exif_file_types:
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
    """ renames image files with original name returns number of renamed files """
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

def delete_collateral_image_files(fp:str,exif_file_types=TYPE_JPG,verbose=False,
                                 max_level=1,delete=True,prompt=True,
                                 do_not_process_files=DO_NOT_PROCESS_FILES,
                                 cleanup_filetypes=TYPE_CLEANUP,
                                 unnamed_file_columns=UNNAMED_FILE_COLUMNS):
    """ removes any related files for a given image file """

    file_deletion_list=[]
    # get the file dictionary
    file_dict=get_file_dict(fp,exif_file_types=exif_file_types)
    filedict_df=get_filepath_stat_df(file_dict)
    print(f"######## DELETING IN {fp}")
    if verbose: print(f"#FOLDERS (TOTAL)                       : {len(filedict_df)}")

    # only get folders that contain JPG and a given folder level (do not consider files in subfolder)
    filedict_df=filedict_df[(filedict_df["TYPE_JPG"])&(filedict_df["level"]<=max_level)]
    num_jpg_only=len(filedict_df)
    filedict_df=filedict_df[filedict_df["NUM_HAS_METADATA"]>0]
    num_metadata=len(filedict_df)
    columns=filedict_df.columns

    unnamed_file_columns=[c for c in unnamed_file_columns if c in columns]

    # sum columns that count not renamed files
    filedict_df["SUM_NOT_RENAMED"]=filedict_df[unnamed_file_columns].sum(axis=1)
    filedict_df=filedict_df[filedict_df["SUM_NOT_RENAMED"]==0]
    if verbose:
        print(f"#FOLDERS (JPEG only, folder level < {max_level}) : {num_jpg_only}")
        print(f"#FOLDERS (FILES WITH METADATA)         : {num_metadata}")
        print(f"#FOLDERS (FILES THAT WERE RENAMED)     : {len(filedict_df)}")

    # list of filepaths = key list
    p_list=list(filedict_df.index)
    num_delete=0
    for p in p_list:
        num_files_for_delete=0
        num_files_total=0

        print(f"\n--- FOLDER: {p} ---")
        files=file_dict[p].get("files",[])
        files=[Path(os.path.join(p,f)) for f in files]
        files=sorted(files)
        num_files_total=len(files)

        for f in files:
            f_name=f.stem+f.suffix
            # ignore file list
            if f_name in do_not_process_files:
                continue
            f_suffix=f.suffix[1:].lower()
            if not f_suffix in cleanup_filetypes:
                continue
            num_files_for_delete+=1
            if verbose: print(f"    * {f_name}")
            file_deletion_list.append(str(f))

        print(f"    Files to delete: {num_files_for_delete}/{num_files_total}")
        num_delete+=num_files_for_delete
    print(f"\n##  FILES TO DELETE: {num_delete} ##")

    if delete:
        if (num_delete > 0) & prompt:
            if input("Delete (y)?") == 'y':
                for f in file_deletion_list:
                    if os.path.isfile(f):
                        os.remove(f)

    return file_deletion_list

def delete_subfolders(fp_root:str,verbose=False,delete_folder_list=["metadata"],
                      prompt=True,delete=True):
    """ Delete Subfolders that contain delete_folder_list substring """

    print(f"Deleting Subfolders {delete_folder_list} in path {fp_root}")
    delete_folders=[]
    file_dict=get_file_dict(fp_root)
    for fp,fp_data in file_dict.items():
        p=Path(fp)
        if not os.path.isdir(p):
            continue
        stem=p.stem
        # check if folder is in delete folder list
        #print(stem)
        #print(to_delete)
        to_be_deleted=any([(del_fld in stem) for del_fld in delete_folder_list])
        if not to_be_deleted:
            continue

        delete_folders.append(p)
        files=fp_data.get("files",[])
        filetypes=[]
        print(f"\n--- FOLDER {fp} ({len(files)} files ) ---")

        for f in files:
            if verbose: print(f"    * {f}")
            filetype=Path(f).suffix
            if filetype not in filetypes:
                filetypes.append(filetype)
        print(f"    FILETYPES: {filetypes} --")

    if len(delete_folders)>0 and delete:
        num_del=0
        if prompt:
            answer=input("\nDELETE (y) ? ")
        else:
            answer="y"
        if answer=="y":
            for p_del in delete_folders:
                shutil.rmtree(p_del)
                num_del+=1
        print(f"\ndeleted {num_del} folders")
    if not delete_folders:
        print("NOTHING FOUND")

    return delete_folders

def program_found(program="exiftool.exe"):
    """ checks if an executable can be found """
    program_which=shutil.which(program)
    if not program_which:
        print(f"Program {program} not found, check path")
        return None
    else:
        return program_which

def copy_metadata_from_panofile(fp_root,exiftool="exiftool.exe",
                                max_level=1,
                                verbose=True,save=True,
                                prompt=True,software=SOFTWARE_INSTA,
                                pano_filetypes=TYPE_PANO,
                                jpg_filetypes=TYPE_JPG):

    """ uses exiftool (needs to be in commandline path) to copy metadata """
    all_exiftool_cmds=[]

    # capture datetime and index of pano file name
    REGEX_PANO=r"(\d{8}_\d{6}_\d{2}_\d{3})"

    def add_pano_fileinfo(f,d):
        regex=re.findall(REGEX_PANO,f)
        if len(regex)==1:
            d[regex[0]]={"panofile":f}
        return None

    exiftool_used=program_found(exiftool)

    if exiftool_used:
        print(f"Copy Metadata Using EXIFTOOL {exiftool_used}")
        print(f"Root Path {fp_root}, max folder level {max_level}")
        print(f"Pano Filetypes {pano_filetypes}, Image Filetypes {jpg_filetypes}")
    else:
        return []

    file_dict=get_file_dict(fp_root)

    old_fp=os.getcwd()

    fp_img_dict={}

    for fp,file_info in file_dict.items():

        if file_info.get("level",0) > max_level:
            continue

        file_types=file_info.get("file_types",{})

        contains_pano_files=any([(pano_file_type in file_types) for pano_file_type in pano_filetypes])
        if not contains_pano_files:
            continue

        print(f"\n--  FOLDER {fp}--")

        file_list=file_info.get("files",[])
        pano_file_dict={}
        pano_files=[f for f in file_list if Path(f).suffix[1:] in pano_filetypes]

        # add to pano filedict
        [add_pano_fileinfo(f,pano_file_dict) for f in pano_files]
        img_files=[f for f in file_list if Path(f).suffix[1:] in jpg_filetypes]

        # get a dictionary containing the list of files
        for img_file in img_files:
            img_key=re.findall(REGEX_PANO,img_file)
            if not len(img_key)==1:
                continue

            pano_dict=pano_file_dict.get(img_key[0],None)
            if not pano_dict:
                continue

            # do not write metadata for image file having same name as
            # pano file (its a direct export cxontianing metadata already)
            if Path(pano_dict.get("panofile","")).stem==Path(img_file).stem:
                continue

            image_list=pano_dict.get("image_list",[])
            image_list.append('"'+img_file+'"')
            pano_dict["image_list"]=image_list

        file_process_list=list(pano_file_dict.values())
        for f_dict in file_process_list:
            image_list=f_dict.get('image_list',[])
            print(f"    * {f_dict['panofile']} [{len(image_list)}]")
            if verbose:
                for i in image_list:
                    print(f"      >> {i}")
        fp_img_dict[fp]=file_process_list

    if prompt & save:
        if not input("\nProceed (y)?")=="y":
            save=False

    # process metadata transfer
    print("\n### COPY METADATA ###")
    # cmd_s="_exiftool -all= test.jpg test2.jpg"

    # exiftool command to delete all metadata
    EXIFTOOL_DELETE="<EXIFTOOL> -all= <TO_FILES> -overwrite_original"
    # exiftool command to copy metadata
    # https://exiftool.org/forum/index.php?topic=3440.0
    EXIFTOOL_COPY='<EXIFTOOL> -TagsFromFile <FROM_FILE> -ee -m "-all:all>all:all" -overwrite_original <TO_FILES>'
    # exiftool command to change software tag
    EXIFTOOL_SOFTWARE='<EXIFTOOL> -Software="<SOFTWARE>" -overwrite_original <TO_FILES>'
    EXIFTOOL_SOFTWARE=EXIFTOOL_SOFTWARE.replace("<SOFTWARE>",software)

    exiftool_commands=[EXIFTOOL_DELETE,EXIFTOOL_COPY,EXIFTOOL_SOFTWARE]
    exiftool_commands=[cmd.replace("<EXIFTOOL>",exiftool) for cmd in exiftool_commands]

    for fp,fp_items in fp_img_dict.items():
        os.chdir(fp)
        print(f"\n--  FOLDER {fp}")

        for fp_item in fp_items:
            from_file=fp_item.get("panofile","")
            print(f"    * {from_file}")

            # special case add software metatag to exported file
            pano_file=str(Path(from_file).stem+".jpg")
            if os.path.isfile(pano_file):
                pano_file='"'+pano_file+'"'
                exiftool_cmd=EXIFTOOL_SOFTWARE.replace("<TO_FILES>",pano_file)
                exiftool_cmd=exiftool_cmd.replace("<EXIFTOOL>",exiftool)
                if save:
                    if verbose:
                        print(f"      {exiftool_cmd[:80]} ...")
                    os.system(exiftool_cmd)
                    all_exiftool_cmds.append(exiftool_cmd)


            # copy all metadata from pano raw file to screenshot files
            from_file='"'+from_file+'"'
            to_files=fp_item.get("image_list",[])
            to_files=" ".join(to_files)
            for exiftool_cmd in exiftool_commands:
                exiftool_cmd=exiftool_cmd.replace("<FROM_FILE>",from_file)
                exiftool_cmd=exiftool_cmd.replace("<TO_FILES>",to_files)
                if verbose:
                    print(f"      {exiftool_cmd[:80]} ...")
                if save:
                    os.system(exiftool_cmd)
                    all_exiftool_cmds.append(exiftool_cmd)

    os.chdir(old_fp)
    print(f"\n### FINISHED, ({len(all_exiftool_cmds)}) Exiftool operations done ###")
    return all_exiftool_cmds

def exiftool_read_meta_recursive(fp_root=None,
                                 exif_attributes=EXIF_ATTRIBUTES,
                                 exiftool="exiftool.exe",
                                 debug=False,exif_template=CMD_EXIF_READ_RECURSIVE_TEMPLATE)->dict:
    """ recursively read jpeg information """
    # save current directory to switch back after operation
    fp_original=os.getcwd()
    cmd_exif_read_recursive=exif_template
    if program_found(exiftool):
        cmd_exif_read_recursive=cmd_exif_read_recursive.replace("EXIFTOOL",exiftool)
    else:
        return {}

    fp=fp_original
    if (not fp_root is None) and os.path.isdir(fp_root):
        fp=fp_root
    os.chdir(fp)
    exif_attribute_list=" ".join(["-"+att for att in exif_attributes])
    os_cmd=cmd_exif_read_recursive.replace("EXIF_ATTRIBUTES",exif_attribute_list)
    if debug:
        print(f"*** Path: {fp}")
        print("    "+ os_cmd)
    oscmd_shlex=shlex.split(os_cmd)
    process = subprocess.run(oscmd_shlex,
                             stdout=subprocess.PIPE,
                             universal_newlines=False,
                             check=True)

    retcode=process.returncode
    if debug:
        print(f"    EXIFTOOL finished, return Code: {retcode}")

    if not retcode==0:
        return {}

    # get data as dictionary
    imginfo_s=process.stdout.decode("utf-8")
    imginfo_list=json.loads(imginfo_s)
    if debug:
        print(f"*** Number of Images processed {len(imginfo_list)}")

    img_dict={}
    for imginfo in imginfo_list:
        #print(imginfo)'Directory': '.', 'FileName': 'exif_a6600.jpg'
        p=str(Path(os.path.join(str(imginfo["Directory"]),str(imginfo["FileName"]))).absolute())
        if debug:
            print("  - "+p)
        img_dict[p]=imginfo

    os.chdir(fp_original)

    return img_dict

def exiftool_get_descriptions(img_info_dict:dict):
    """ creates image description dictionary """
    imginfo_description_dict={}
    for fp,img_info in img_info_dict.items():
        s=""
        if img_info.get("Title",None):s+=img_info["Title"]
        s+=" ["
        if img_info.get("Make",None):s+=img_info["Make"]
        if img_info.get("Model",None):s+=" "+img_info["Model"]
        if img_info.get("LensModel",None): s+="|"+img_info["LensModel"]
        if img_info.get("FocalLength",None): s+=" "+img_info["FocalLength"]
        if img_info.get("ShutterSpeed",None): s+=" "+img_info["ShutterSpeed"]+"s"
        if img_info.get("Aperture",None): s+=" F"+str(img_info["Aperture"])
        if img_info.get("ISO",None): s+=" ISO"+str(img_info["ISO"])
        if img_info.get("LightValue",None): s+=", "+str(img_info["LightValue"])+"LV"
        if img_info.get("Software",None): s+=", Software: "+img_info["Software"]
        s+="]"
        if img_info.get("SpecialInstructions",None): s+=" Geolink: "+img_info["SpecialInstructions"]
        imginfo_description_dict[str(fp)]=s
        img_info["Description"]=s+"]"

    # return img_info_dict
    return imginfo_description_dict

def exiftool_delete_metadata(fp,preview=True,exiftool="exiftool.exe",prompt=True,delete=True):
    """ removes all exif metadata for jpg files in path  """
    fp_original=os.getcwd()
    if program_found(exiftool):
        cmd_exif_delete_all=CMD_EXIF_DELETE_ALL.replace("EXIFTOOL",exiftool)
    else:
        return -1

    if os.path.isdir(fp):
        os.chdir(fp)
    else:
        print(f"{fp} is not a directory, pls check")
        return -2

    if preview:
        print("*** Files for EXIF data deletion ***")
        img_dict=exiftool_read_meta_recursive(fp)
        for f,desc in img_dict.items():
            s=desc.get("Title","")+" ["+desc.get("Make","")
            s+=" "+desc.get("Model","")+"|"+desc.get("LensModel","")+"]"
            s+="\n    "+desc.get("SpecialInstructions","")
            print(f" *  {f}\n    {s}")

    if prompt and (input(f"\nDelete metadata for files in {fp} (y)")=="y"):
        delete=True

    if delete:
        oscmd_shlex=shlex.split(cmd_exif_delete_all)
        process = subprocess.run(oscmd_shlex,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=False,
                                 check=True)
        retcode=process.returncode
        stdout=process.stdout.decode("UTF-8")

    print(f"EXIFTOOL [{cmd_exif_delete_all}], return Code: {retcode}\n{stdout}")
    os.chdir(fp_original)
    return retcode

def magick_resize(fp,magick="magick.exe",image_size=2000,
                  quality=90,prefix=False,
                  remove_metadata=True,save=True,
                  descriptions=True,
                  target_path=None):
    """ resize image / optionally remove metadata, params
        fp: file path containing image files
        magick: executable, needs to be executable through system path
        image_size: width of image after resize
        quality=90
        prefix=write prefix (True) or as suffix (False)
        remove_metadata=True (remove exif metadata from target file)
        save=True (save images)
        descriptions (True) create descriptions
        target_path = None (target path where to store images is fp isf None)
        returns dict of images
    """

    if not program_found(magick):
        return {}

    fp_original=os.getcwd()

    file_addition=str(image_size)+"px"
    attributes=["_MAGICK","_IMAGESIZE","_QUALITY"]
    values=[magick,str(image_size),str(quality)]
    magick_resize=CMD_MAGICK_RESIZE
    for k,v in dict(zip(attributes,values)).items():
        magick_resize=magick_resize.replace(k,v)

    if remove_metadata:
        magick_resize=magick_resize.replace("resize","thumbnail")
    print(f"*** MAGICK template: [{magick_resize}]")

    # get files per path
    img_dict=exiftool_read_meta_recursive(fp,
             exif_attributes=EXIF_ATTRIBUTES_MINIMUM)

    img_dict={p:v for (p,v) in img_dict.items() if file_addition not in Path(p).stem }

    # get image descriptions
    if descriptions:
        img_descriptions_dict=exiftool_get_descriptions(img_dict)
        s_list=[]
        for f,d in img_descriptions_dict.items():
            s_list.append(f+":\n")
            s_list.append(d+"\n")

        if target_path:
            os.chdir(target_path)
        else:
            os.chdir(fp_original)
        print(f"    Write descriptions to {os.path.join(os.getcwd(),'descriptions.txt')}")

        with open('descriptions.txt', 'w') as file:
            file.writelines(s_list)

    image_dict={}
    for fp,img_info in img_dict.items():
        p_img=str(Path(img_info["Directory"]).absolute())
        img_list=image_dict.get(p_img,[])
        img_list.append(img_info["FileName"])
        image_dict[p_img]=img_list


    # do the changes for each folder
    for p,files in image_dict.items():
        os.chdir(p)
        print(f"\n*** FOLDER {p}")

        for f in files:
            # skip processing if it already contains file addition
            #print(f"    - {f}")
            file_path=Path(f)
            file_out=file_path.stem

            if prefix:
                file_out=file_addition+"_"+file_out+file_path.suffix
            else:
                file_out=file_out+"_"+file_addition+file_path.suffix

            if target_path:
                file_out=str(Path(os.path.join(target_path,file_out)).absolute())
            file_out='"'+file_out+'"'
            # print(file_out)

            magick_file_resize=magick_resize.replace("_FILE_IN",'"'+f+'"')
            magick_file_resize=magick_file_resize.replace("_FILE_OUT",file_out)
            #print(f"    {magick_file_resize}")
            oscmd_shlex=shlex.split(magick_file_resize,posix=True)
            #print(oscmd_shlex)
            print(f"    - {f:<25} > {file_out}")
            #print(oscmd_shlex)
            #print(f"{file_path.stem}  {file_path.suffix}")
            if save:
                process = subprocess.run(oscmd_shlex,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=False,
                                         check=True)
                retcode=process.returncode
                # stdout=process.stdout.decode("UTF-8")
                if retcode != 0:
                    print(f"Return code {retcode}, command {oscmd_shlex}")
    os.chdir(fp_original)
    return image_dict

def exiftool_get_path_dict(fp,exif_template=CMD_EXIF_READ_ALL_RECURSIVE_TEMPLATE,debug=False):
    """ reads files using exiftool and returns a dictionary with path as key
        exif_template can be used to extract only a subset of attributes
        NOTE: somehow exiftool doesn't parse all file types
    """
    img_dict=exiftool_read_meta_recursive(fp_root=fp,exif_template=exif_template,
                                                   debug=debug)
    print(f"*** Read: {len(img_dict.keys())} files")

    p_root=Path(fp)
    num_root=len(p_root.parts)
    path_dict={}
    for f,f_info in img_dict.items():
        fp=Path(f)
        p_parent=fp.parent
        p_file=str(fp.name)
        p_suffix=fp.suffix[1:].lower()

        path_info=path_dict.get(str(p_parent),{})
        # folder level
        level=len(p_parent.parts)-num_root

        path_info["level"]=level
        path_filetypes=path_info.get("filetypes",{})
        path_num_files=path_filetypes.get(p_suffix,0)+1
        path_filetypes[p_suffix]=path_num_files
        path_info["filetypes"]=path_filetypes

        # get date
        try:
            dt = datetime.strptime(f_info.get("DateTimeOriginal",""), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            dt = datetime.now()

        dts=dt.strftime("%Y%m%d")
        f_info["Date"]=dts
        f_info["Filetype"]=p_suffix
        f_info["has_gps"]=(f_info.get("GPSLatitude",0)>0)
        f_info["has_metadata"]=(len(f_info.get("Keywords",[]))>0)

        file_dict=path_info.get("file_dict",{})
        file_dict[p_file]=f_info
        path_info["file_dict"]=file_dict
        path_dict[str(p_parent)]=path_info

    if debug:
        print("\n")
        for p,p_info in path_dict.items():
            print(f"*** {p} {p_info['filetypes']}, level {p_info['level']}")
    return path_dict

def exiftool_get_rename_dict(path_dict,max_level=1):
    """ determines whether files should be renamed
        * input data is retrieved from exiftool_get_path_dict
        * checks whether not renamed image files are present
          (either SONY RAW Format or Panorama Camera)
        * if parent folder contains date as prefix it will be used
          if not, date prefix will tried to be retrieved from image metadata
        * max_level folders bigger than this level will be ignored
    """

    # todays date as fallback
    d_today=datetime.now().strftime("%Y%m%d")

    num_renames=0
    rename_dict={}

    for p,p_info in path_dict.items():
        dir_path=Path(p)
        pathname=dir_path.name

        f_rename_list=[]

        folder_level=p_info['level']
        if folder_level>max_level:
            print(f"*** {p}")
            print(f"    folder level: {folder_level}, will be skipped")
            continue

        file_info=p_info.get("file_dict",{})

        # check if older contains date prefix
        d_path=None
        re_path_date=re.search(REGEX_DATE_PREFIX,pathname)
        if re_path_date:
            d_path=re_path_date.groups()[0]

        for f,f_info in file_info.items():
            f_new=f
            # get regex matches
            regex_matches={regex_rule:re.findall(REGEX_RULE_DICT[regex_rule],f) for regex_rule in REGEX_RULE_DICT.keys()}
            regex_matches={rule:regex_matches[rule] for rule in regex_matches.keys() if bool(regex_matches[rule])}
            if bool(regex_matches):
                rule_name_matched=list(regex_matches.keys())[0]
                rule_matches=list(regex_matches.values())[0][0]

                # now get the date prefix either from folder or from file
                # path date is given
                if d_path:
                    f_new=pathname+"_"
                else:
                    d=f_info.get("Date",d_today)
                    f_new=d+"_"+pathname+"_"
                suffix=Path(f).suffix
                # create new file name
                if rule_name_matched=="REGEX_ORIGINAL_NAME":
                    f_new+=rule_matches[1]
                elif rule_name_matched=="REGEX_INSTAONEX":
                    f_new+=f[23:-(len(suffix))]
                f_new+=suffix
            if not f==f_new:
                num_renames+=1
                #if debug:
                #    print(f"    RENAME {(f+' |OLD'):>70} \n           {(f_new+' |NEW'):>70}")
                f_rename_list.append({"f_old":f,"f_new":f_new})
        if len(f_rename_list)>0:
            rename_dict[p]=f_rename_list

    p_old=os.getcwd()
    num_renamed=0
    for p,file_list in rename_dict.items():
        #os.chdir(p)
        print(f"*** {p}")
        for f_rename_dict in file_list:
            num_renamed+=1
            f_old=f_rename_dict["f_old"]
            f_new=f_rename_dict["f_new"]
            print(f'    + {num_renamed:03d} {f_old}\n    |     {f_new}')
    print(f"*** NUMBER OF RENAMES: {num_renames}")
    if num_renames==0:
        print("    NO FILES FOR RENAME FOUND")

    if num_renames>0 and (input("RENAME (y)? ")=="y"):
        num_renamed=0
        for p,file_list in rename_dict.items():
            if os.path.isdir(p):
                os.chdir(p)
            else:
                print(f"Path {p} doesn't exist (any more)")
                continue

            for f_rename_dict in file_list:
                try:
                    os.rename(f_rename_dict["f_old"],f_rename_dict["f_new"])
                    num_renamed+=1
                except OSError as e:
                    print(p)
                    pf_old=os.path.join(p,f_rename_dict["f_old"])
                    print(f"Error renaming file {pf_old}: {e}")

        print(f"\n>>> RENAMED {num_renamed} files")
    os.chdir(p_old)
    return rename_dict

""" Utility to recursively clean up files  """

import os
import shutil
from pathlib import Path
from tools import img_file_info_xls as file_info


# files that should not be deleted / moved
IGNORE_FILES=["gps.geo","default.geo","metadata.tpl","metadata_exif.tpl","gps.meta"]

# filetypes
FILETYPE_DEL=["dop","ped","xmp","jpg_original","geo","tpl","tif"]
FILETYPE_RAW=["tif","arw","dng"]
FILETYPE_GEO=["gpx"]
FILETYPE_JPG=["jpg","insp"]

# dict to provide additional information in file dict
FILETYPE_CLASSES_DICT={"FILETYPE_DEL":FILETYPE_DEL,
                       "FILETYPE_RAW":FILETYPE_RAW,
                       "FILETYPE_GEO":FILETYPE_GEO,
                       "FILETYPE_JPG":FILETYPE_JPG }


# folders that should be deleted
DELETE_PATHS=["metadata","PEXV_PARAM","tmp"]
# folders that should not be deleted
IGNORE_PATHS=["PANO","POST","RAW"]

# same thing but for deleting raw images
IGNORE_PATHS_RAW=["POST"]
DELETE_PATHS_RAW=["metadata","PEXV_PARAM","tmp","10RAW"]

# lookup dictionary for deletion profile
DEL_PROFILE_RAW="RAW"
DEL_PROFILE="DEL"
DELETE_PROFILE={"RAW":{"FILETYPES":FILETYPE_RAW,
                      "IGNORE_PATHS" :IGNORE_PATHS_RAW,
                      "DELETE_PATHS" :DELETE_PATHS_RAW},
                "DEL":{"FILETYPES"   :FILETYPE_DEL,
                      "IGNORE_PATHS" :IGNORE_PATHS,
                      "DELETE_PATHS" :DELETE_PATHS}}

# move folder destination for given filetype
FILETYPE_TARGET_FOLDER={"jpg":"70POST",
                        "arw":"10RAW",
                        "dng":"10PANO",
                        "insp":"10PANO"}

def delete(fp:str,filetype_classes_dict:dict=FILETYPE_CLASSES_DICT,
                 save:bool=True,verbose:bool=True,ignore_files:list=IGNORE_FILES,
                 ignore_paths:list=IGNORE_PATHS,delete_paths:list=DELETE_PATHS,
                 del_filetypes:list=FILETYPE_DEL,
                 force_fld_del:bool=True)->list:
    """
    Recursively deletes files and folders in a selective manner
    Parameters:
        fp (str): directory root
        filetype_classes_dict (dict): dictionary to outline additional metrics in file dict
        save (bool): persist changes
        verbose (bool): output information
        ignore_files (list): list of files not to be deleted
        ignore_paths (list): list of paths not to be deleted
        delete_paths (list): path substrings to indicate folders to be deleted
        del_filetypes (list): file type extensions that should be deleted
        force_fld_del (bool): Force deletion of folders even if it contains ignore files
    Returns:
        dict: list of deleted files and folders

    """
    file_dict = file_info.get_file_dict(fp,regex_file_rules_dict={},
                            filetype_classes_dict=filetype_classes_dict)
    del_filetypes=[ft.lower() for ft in del_filetypes]

    file_delete_list=[]
    folder_delete_list=[]
    filetypes_del_dict={}

    for fp,fp_info in file_dict.items():
        p = Path(fp)
        folder=p.stem
        #parent=fp_info["parent"].stem
        file_list=fp_info["files"]

        # skip folder if it's an ignore folder
        if len([ip for ip in ignore_paths if ip.lower() in folder.lower()]) > 0:
            if verbose:
                print(f"*   SKIP    {fp}")
            continue

        # check if it's a delete folder
        if len([dp for dp in delete_paths if dp in folder]) > 0:
            # delete all files in folder except ignore files
            if force_fld_del:
                ignored_files = []
            else:
                ignored_files=[f for f in file_list
                                for fi in ignore_files
                                if  fi.lower() == f.lower()]
            delete_files=[os.path.join(p,f) for f in file_list if f not in ignored_files]

            if len(ignored_files)==0:
                folder_delete_list.append(fp)

            if verbose:
                print(f"*   DELETE FOLDER\n    {fp}, delete: ({len(ignored_files)==0})")
                print(f"    Delete Folder: {len(ignored_files)==0}, #files {len(file_list)} #ignore {len(ignored_files)} #delete {len(delete_files)}")

            file_delete_list.extend(delete_files)
        # check if it's an empty folder
        elif len(file_list) == 0:
            if verbose:
                print(f"*   EMPTY FOLDER\n    {fp}")
            folder_delete_list.append(fp)
        # check on file level
        else:
            if verbose:
                print(f"#   DELETE FILES\n    {fp}")
            for f in file_list:
                if f in ignore_files:
                    continue

                filetype=Path(f).suffix[1:].lower()
                if filetype in del_filetypes:
                    print(f"    - delete {f}")
                    file_delete_list.append(os.path.join(p,f))

    if verbose:
        print("\n########################### ")
        print(f"#   DELETE FOLDERS ({len(folder_delete_list)})")
        for p in folder_delete_list:
            print(f"-   {p}")
        for f in file_delete_list:
            suffix = Path(f).suffix[1:]
            filetypes_del_dict[suffix]=filetypes_del_dict.get(suffix,0)+1
        print(f"#   DELETE FILES ({len(file_delete_list)})")
        for ft,ft_num in filetypes_del_dict.items():
            print(f"-   {ft:<15} : ({ft_num})")
        print("###########################\n")

    if save:
        if (len(folder_delete_list)+len(file_delete_list))>0:
            if input("Delete (y): ")=="y":
                num_del=0
                for f in file_delete_list:
                    os.remove(f)
                    num_del+=1
                print(f"* DELETED ({num_del}) FILES")
                num_del=0
                for p in folder_delete_list:
                    os.rmdir(p)
                    num_del+=1
                print(f"* DELETED ({num_del}) FOLDERS")

    return {"folders":folder_delete_list,"files":file_delete_list}

def move(fp:str,filetype_classes_dict:dict=FILETYPE_CLASSES_DICT,
               ignore_paths:list=IGNORE_PATHS,
               ignore_files:list=IGNORE_FILES,
               filetype_target_folder:dict=FILETYPE_TARGET_FOLDER,
               save:bool=True,verbose:bool=True)->list:
    """
    Recursively move files and folders in a selective manner
    Parameters:
        fp (str): directory root
        filetype_classes_dict (dict): dictionary to outline additional metrics in file dict
        ignore_paths (list): list of paths not to be moved
        ignore_files (list): list of files not to be moved
        filetype_target_folder (dict): assignment to which subfolder a file needs to be moved
        save (bool): persist changes
        verbose (bool): output information
    Returns:
        dict: list of moved files and created folders

    """

    file_dict = file_info.get_file_dict(fp,regex_file_rules_dict={},
                            filetype_classes_dict=filetype_classes_dict)

    ignore_paths=[ip.lower() for ip in ignore_paths]

    folder_create_list=[]
    file_moves_list=[]

    for fp,fp_info in file_dict.items():
        if verbose:
            print(f"*   {fp}")
        p = Path(fp)
        folder=p.stem

        # ignore path, do not process this folder
        if sum([1 for ip in ignore_paths if ip in folder.lower()]) > 0:
            continue

        file_list=fp_info["files"]
        file_list_filter=[]

        # filter any files that are not to be moved
        for f in file_list:
            if len([f for fi in ignore_files if fi.lower() == f.lower()]) == 0:
                file_list_filter.append(f)
        file_list=file_list_filter

        for filetype,target_path in filetype_target_folder.items():

            move_files = [f for f in file_list if Path(f).suffix[1:].lower() == filetype.lower()]
            if move_files:

                target_fullpath=os.path.join(p,target_path)

                # create directory if not there
                if not os.path.isdir(target_fullpath):
                    folder_create_list.append(target_fullpath)

                # create move paths
                files_from=[os.path.join(p,f) for f in move_files]
                files_to=[os.path.join(p,target_fullpath,f) for f in move_files]
                file_moves=list(zip(files_from,files_to))
                file_move_list=[{"from":f[0],"to":f[1]} for f in file_moves]
                file_moves_list.extend(file_move_list)
                if verbose and len(file_move_list)>0:
                    print(f"    Moving {len(file_move_list)} ({filetype}) files to ..\\{target_path}")

    if verbose:
        print("\n########################### ")
        print(f"#   NEW FOLDERS ({len(folder_create_list)})")
        for p in folder_create_list:
            print(f"-   {p}")
        print(f"#   FILE MOVES {len(file_moves_list)}")
        print("###########################\n")

    if save:
        if (len(folder_create_list)+len(file_moves_list))>0:
            if input("Move (y)? ")=="y":
                num_move=0
                for p in folder_create_list:
                    os.mkdir(p)
                    num_move+=1
                print(f"*   CREATED ({num_move}) FOLDERS")

                num_move=0
                for f in file_moves_list:
                    if os.path.isfile(f["to"]):
                        print(f"    FILE EXISTS: {f['to']}")
                        continue
                    os.rename(f["from"],f["to"])
                    num_move+=1
                print(f"*   MOVED ({num_move}) FILES")

    return {"folders":folder_create_list,"files":file_moves_list}

def copy_img_file(fp:str,geo_file:str="gps.jpg",
                  verbose:bool=True,save:bool=True)->list:
    """
    duplicates a file and adds the creation datetime to filename
    Use Case: Geo Files to display calibration datetime
    Parameters:
        fp (str): directory root
        geo_file (str): name of ge
        save (bool): persist changes
        verbose (bool): output information
    Returns:
        (list): List of dicts with the copy files

    """

    def get_new_filename(exif_dict,verbose:bool=True):
        """ gets new filename from exif information """

        s="    FILE "
        p=Path(exif_dict.get("filename","filename.ext"))
        name=""
        if p.is_file():
            name=p.name
            s+=name
        datetime=exif_dict.get("DateTimeOriginal","YYYY:MM:DD HH:MM:SS")
        s+="/ DateTime: "+exif_dict.get("DateTimeOriginal","NA")
        s+=exif_dict.get("OffsetTimeOriginal"," No Offset")
        s+=" / "+exif_dict.get("Make","MAKE")+" "+exif_dict.get("Model","Model")
        s+="("+exif_dict.get("LensModel","Lens")+")"
        s+="\n    "+exif_dict.get("ImageDescription","")
        if verbose:
            print(s)
        filename=datetime[:10].replace(":","")+"_"+datetime[11:].replace(":","")+"_"+name
        return filename

    filetype_classes_dict={"FILETYPE_GEO":["gpx"],
                           "FILETYPE_JPG":["jpg","insp"] }

    file_dict = file_info.get_file_dict(fp,regex_file_rules_dict={},
                            filetype_classes_dict=filetype_classes_dict)
    geo_filepaths=[k for k,v in file_dict.items() if geo_file in v["files"]]

    # read exif infos
    copy_files=[]
    for fp in geo_filepaths:

        f_from=Path(fp).joinpath(geo_file)
        print(f"*** {f_from}")
        exif_dict=file_info.read_exif(f_from)
        new_file=get_new_filename(exif_dict,verbose)
        f_to=Path(fp).joinpath(new_file)
        if not f_to.is_file():
            print(f"    NEW FILE {new_file}")
            copy_files.append({"from":f_from,"to":f_to})
        else:
            print(f"    FILE {new_file} ALREADY EXISTS")

    if save and len(copy_files)>0 and (input(f"\nSave copy of {geo_file} (y)? ")=="y"):
        _=[shutil.copy2(f["from"],f["to"]) for f in copy_files]

    print(f"*   COPIED ({len(copy_files)}) FILES")

    return copy_files

def create_gpx_waypt(fp:str,cmd_exif_waypt_fmt:str,exiftool:str="exiftool.exe",
                     jpg_folder_waypt:str="70POST",ignore_folders:list=[])->list:
    """
    Recursively creates waypoint files from GPS tagged images
    Parameters:
        fp (str): root filepath
        exiftool: location / executable for exiftool
        jpg_folder_waypt: name of jpg subfolder for example "70POST"
        cmd_exif_waypt_fmt: location of transofmration file
                        https://exiftool.org/geotag.html
                        https://github.com/exiftool/exiftool/blob/master/fmt_files/gpx_wpt.fmt
        ignore_folders(list): List of substrings. File Paths matching them will be ignored
    Returns
        list: list of dictionaries with folders / commands

    """
    def is_ignore_folder(fp):
        return sum([1 for p in ignore_folders if p.lower() in fp.lower()])>0

    # dict to provide additional information in file dict
    FILETYPE_GPX_CLASSES_DICT={"FILETYPE_GEO":["gpx"],"FILETYPE_JPG":["jpg"] }

    # exif command for creating waypoint file in parent folder containing jpg folder
    CMD_EXIF_CREATE_WAYPOINT='EXIFTOOL -r -fileOrder gpsdatetime -p '
    CMD_EXIF_CREATE_WAYPOINT+='"CMD_EXIF_WAYPT_FMT" ".\\JPG_FOLDER_WAYPT\\*.jpg" > CMD_EXIF_WAYPT_FILE'
    CMD_EXIF_CREATE_WAYPOINT=CMD_EXIF_CREATE_WAYPOINT.replace("EXIFTOOL",exiftool)
    CMD_EXIF_CREATE_WAYPOINT=CMD_EXIF_CREATE_WAYPOINT.replace("JPG_FOLDER_WAYPT",jpg_folder_waypt)
    CMD_EXIF_CREATE_WAYPOINT=CMD_EXIF_CREATE_WAYPOINT.replace("CMD_EXIF_WAYPT_FMT",cmd_exif_waypt_fmt)
    cmd_exiftool=CMD_EXIF_CREATE_WAYPOINT

    # get file info
    file_dict = file_info.get_file_dict(fp,regex_file_rules_dict={},
                                        filetype_classes_dict=FILETYPE_GPX_CLASSES_DICT)

    target_folders=[p for p in file_dict if p.endswith(jpg_folder_waypt)]
    target_folders=[p for p in target_folders if not is_ignore_folder(p)]
    # create commands
    exif_commands=[]
    for target_folder in target_folders:

        file_info_dict=file_dict[target_folder]
        # only continue if this folder contains jpgs
        if not file_info_dict["FILETYPE_JPG"]:
            continue

        parent=file_info_dict["parent"]
        f_waypoint=parent.name+"_gps_images_wpt.gpx"
        # create waypoint file in parent path
        p_waypoint=parent.joinpath(f_waypoint)
        if p_waypoint.is_file():
            print(f"### FILE {f_waypoint} already exists, SKIPPED")
            continue
        cmd_exif_waypt=cmd_exiftool.replace("CMD_EXIF_WAYPT_FILE",f_waypoint)
        exif_commands.append({"p_parent":parent,"cmd_exif":cmd_exif_waypt})

    p_work=os.getcwd()

    for exif_command in exif_commands:
        p_parent=exif_command["p_parent"]
        os_cmd=exif_command["cmd_exif"]
        print(f"### FOLDER {p_parent}")
        print(f"    COMMAND <{os_cmd}>")
        os.chdir(p_parent)
        os.system(os_cmd)

    os.chdir(p_work)
    print(f"### FINISHED CREATING {len(exif_commands)} Waypoint FILES")

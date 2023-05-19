""" Class to validate / consolidate all metadata in control file """

import os
import shutil
import pprint
from copy import deepcopy
from pathlib import Path
from datetime import datetime as DateTime
from image_meta.geo import Geo
from tools import img_file_info_xls as file_info

# from image_meta.geo import Geo
#from tools_cmd import _img_file_settings as file_settings

# # root folder for photos, structure
# p_photos_root=file_settings.P_PHOTOS_ROOT
# # ignore image folders when creating waypoint files
# ignore_folders=file_settings.IGNORE_FOLDERS_GPX
# # location of exiftool if in path it is exiftool
# exif_tool=file_settings.CMD_EXIFTOOL
# # folder location of format file
# cmd_exif_waypt_fmt=file_settings.CMD_EXIF_WAYPT_FMT
# # Subfolder used for creating waypoint files
# jpg_folder_waypt=file_settings.JPG_FOLDER_WAYPT
# # file path of Control File Template
# fp_metadata_tpl=file_settings.FP_METADATA_TPL
# # metadata file names / all will be collected in metadata.tpl
# f_metadata=file_settings.F_METADATA
# # HOME LATLON COORDINATES
# latlon_home=file_settings.LATLON_HOME


class ImageFileValidator():
    """ Validating Image Control Files """

    # dict to provide additional information in file dict
    FILETYPE_CLASSES_DICT={"FILETYPE_GEO":["gpx"],
                        "FILETYPE_JPG":["jpg","insp"] }


    # FILES: Template is defined in tools_cmd _img_file_settings_template.py

    FILE_ACTIONS={
            "CONTROL_FILE":{"info":"Control file was copied","done":False,"preconds":[],"type":"file",
                            "hint":"Control File Required"},
            "META_PROFILES_FILE":{"info":"Keyword Profiles to be used","done":False,"preconds":[],"type":"file",
                                "hint":"File Path to Meta Profiles File, is used to generate META_FILE"},
            "META_FILE":{"info":"Metadata EXIF Keywords file created","done":False,"preconds":["META_PROFILES_FILE"],"type":"tpl",
                        "hint":"(Optional) file to store exif attributes, not present"},
            "GPX_FILE":{"info":"GPX track file is present","done":False,"preconds":[],"type":"tpl",
                        "hint":"Place GPS LOG (gpx) / alternatively only use OSM link only"},
            "WAYPOINT_FILE":{"info":"GPX waypoint file is present","done":False,"preconds":[],"type":"tpl",
                            "hint":"Is used to synch GPS time with GPS jpg"},
            "KEYWORD_HIER_FILE":{"info":"Keyword hierarchy file is present","done":False,"preconds":[],"type":"tpl",
                                "hint":"File is required to create hierarchical keywords (hierarchy=Tab indentation)"},
            "CALIB_IMG_FILE":{"info":"Calibration image jpg file is present","done":False,"preconds":[],"type":"tpl",
                            "hint":"Place the jpg image for calibration into folder and name it accordingly"},
            "CALIB_DATETIME":{"info":"Calibration Datetime from Config File","done":False,"preconds":[],"type":"tpl",
                            "hint":"Either entered manually or from waypoint file or from gps image file"},
            "DEFAULT_LATLON_FILE":{"info":"Default LatLon File file is present","done":False,"preconds":[],"type":"tpl"},
            "DEFAULT_LATLON":{"info":"Default LatLon Coordinates in Control File","done":False,"preconds":[],"type":"tpl",
                            "hint":"LatLon Coordinates will be written into config file either from osm url or gpx"},
            "URL_OSM_LINK":{"info":"OSM Link is in Photo Folder","done":False,"preconds":[],"type":"file",
                            "hint":"Copy OSM links into folder "},
            "URL_OSM":{"info":"OSM Link is in Control File","done":False,"preconds":[],"type":"tpl",
                        "hint":"Either place OSM Link into folder or use waypoint file and gps jpg or fill offset"},
            "CALIB_OFFSET":{"info":"GPS OFfset is calculated","done":False,"preconds":["WAYPOINT_FILE","CALIB_IMG_FILE"],"type":"tpl",
                            "hint":"Either waypoint file and gps jpg or fill offset field directly"},
            "GEO_INFO":{"info":"Geo Information is in Control File","done":False,"preconds":["CALIB_OFFSET"],"type":"tpl",
                        "hint":"After a Geo Reverse Lookup this information appears in Control file"},
            "IMAGE_GPX":{"info":"Image waypoints calculated","done":False,"preconds":["GEO_INFO"],"type":"file",
                            "hint":"Image waypoint gpx is calculated from geotagged images"}
    }

    # dict to evaluate distance
    DISTANCE_FROM_HOME={ 2.:"DISTANCE_0_2KM",5.:"DISTANCE_2_5KM",20.:"DISTANCE_5_20KM",
                        200.:"DISTANCE_20_200KM",1000.:"DISTANCE_200_1000KM",99999.:"DISTANCE_OUTSIDE"}


    FILETYPE_CLASSES_DICT={ "FILETYPE_TPL":["tpl"],
                            "FILETYPE_GPX":["gpx"],
                            "FILETYPE_META":["meta"],
                            "FILETYPE_GEO":["geo"],
                            "FILETYPE_INSP":["insp"],
                            "FILETYPE_JPG":["jpg"],
                            "FILETYPE_URL":["url"]
                            }

    SEASON=["Winter","Frühling","Sommer","Herbst"]
    DAYTIME={2:"Frühmorgen",6:"Morgen",10:"Vormittag",14:"Nachmittag",18:"Abend",22:"Nacht"}

    @staticmethod
    def get_datetime_text(d:DateTime):
        """ gets the date and time as Text
        12-1-2 (Winter), (3-4-5) (Spring) ...
        22-02 (Nacht), 02-06 (Morgen), ...
        """
        m=d.month // 3
        m=0 if m>=4 else m
        h=[hh for hh in ImageFileValidator.DAYTIME.keys() if d.hour >= hh]
        h=22 if not h else h[-1]
        return [ImageFileValidator.SEASON[m],ImageFileValidator.DAYTIME[h]]

    @staticmethod
    def get_datetime(s:str):
        """ gets datetime of strings according to fixed format, eg
            2022:10:08 17:22:47
            (irrespective of separator)
        """
        try:
            dts=s[0:4]+s[5:7]+s[8:10]+"_"+s[11:13]+s[14:16]+s[17:19]
            dt=DateTime.strptime(dts,'%Y%m%d_%H%M%S')
            return dt
        except (ValueError, TypeError) as e:
            print(e)
            return None

    @staticmethod
    def update_keyword_file(f_profile:str,f_keywords:str,
                            prompt=True,update=False,
                            overwrite=False,
                            add_keywords=[])->str:
        """ creates/updates exif keyword file based on a keywords profile json
            returns string that was created
            Parameters:
                f_profile (str): filepath to profile json
                f_profile (str): filepath to exif keywords file
                prompt (bool)  : asks for keyword entry
                update (bool)  : also update the file
                overwrite (bool): overwrite the old data
                keywords (list): additional keywords
        """

        keywords=[]
        if os.path.isfile(f_keywords):
            try:
                s_list=file_info.read_file(f_keywords)
                keywords=[s for s in s_list if not s.startswith("#")][0].split("=")[1].split(", ")
                print(f"    Keywords file {f_keywords} already exist:\n    {keywords}")
            except IndexError:
                s_list="no list found"
            if not update:
                return ""

        exif_profiles=file_info.read_json(f_profile)

        # display existing profile / add default profile
        profiles={}
        exif_attributes=[]
        if prompt:
            print("\n    SETTING ADDITIONAL KEYWORDS")
        for i,(k,v) in enumerate(exif_profiles.items()):
            if k == "ALL":
                exif_attributes.extend(v)
            profiles[i]=(k,v)
            if prompt:
                print(f"    [{str(i).zfill(2)}] {k:<15}:{v}")

        # add existing keywords if not in overwrite mode
        if not overwrite:
            exif_attributes.extend(keywords)

        # add external keywords
        exif_attributes.extend(add_keywords)

        numbers=""
        if prompt:
            numbers=input("Select numbers for Profile ('blank': default only, 'x':skip)")
            if numbers=="x":
                return ""

        out_s="# Additional Keywords as comma separated values (note the space)\n"

        try:
            profiles_used=[]
            if len(numbers)>0:
                numbers=[int(n) for n in numbers.split() if int(n) <= max(profiles.keys())]
                for n in numbers:
                    exif_attributes.extend(profiles[n][1])
                    profiles_used.append(profiles[n][0])
            exif_attributes=list(dict.fromkeys(exif_attributes).keys())
            out_s+="# EXIF PROFILES: "+", ".join(profiles_used)
            out_s+=" (created:"+DateTime.now().replace(microsecond=0).isoformat()+")\n"
            out_s+="-Keywords="+", ".join(exif_attributes)+"\n"
            with open(f_keywords, 'w',encoding="UTF-8") as file:
                file.write(out_s)
            print(f"*** WRITING keywords ({profiles_used}): {exif_attributes} to file: {f_keywords}")
        except (ValueError,KeyError) as e:
            print(f"*** ERROR: Only use numbers separated by space ({e})")

        return out_s

    def __init__(self,p_photos_root:str,ignore_folders:str,
                 exif_tool:str,cmd_exif_waypt_fmt:str,
                 jpg_folder_waypt:str,fp_metadata_tpl:str,
                 f_metadata:str,latlon_home:str):
        """
        Parameters:
        p_photos_root:      root folder for photos, structure
        ignore_folders:     ignore image folders when creating waypoint files
        exif_tool:          location of exiftool if in path it is exiftool
        cmd_exif_waypt_fmt: folder location of format file
        jpg_folder_waypt:   Subfolder used for creating waypoint files
        fp_metadata_tpl:    file path of Control File Template
        f_metadata:         metadata file names / all will be collected in metadata.tpl
        latlon_home:        HOME LATLON COORDINATES
        """

        def is_relevant(p,v):
            """ allow only certain paths  """
            # only for parent folders
            if v["level"] != 1:
                return False
            # is ignore folder
            if len([fi for fi in self.ignore_folders if fi.lower() in Path(p).stem.lower()])>0:
                return False
            return True

        # root folder for photos, structure
        self.p_photos_root=p_photos_root
        # ignore image folders when creating waypoint files
        self.ignore_folders=ignore_folders
        # location of exiftool if in path it is exiftool
        self.exif_tool=exif_tool
        # folder location of format file
        self.cmd_exif_waypt_fmt=cmd_exif_waypt_fmt
        # Subfolder used for creating waypoint files
        self.jpg_folder_waypt=jpg_folder_waypt
        # file path of Control File Template
        self.fp_metadata_tpl=fp_metadata_tpl
        # metadata file names / all will be collected in metadata.tpl
        self.f_metadata=f_metadata
        # HOME LATLON COORDINATES
        self.latlon_home=latlon_home

        """ checks if variables are set, returns True if all nexessary checks are ok """
        check=True
        if not os.path.isfile(cmd_exif_waypt_fmt):
            print(f"Parameter CMD_EXIF_WAYPT_FMT ({cmd_exif_waypt_fmt}) (format file for waypoints) is not a file")
            check=False
        if not os.path.isfile(fp_metadata_tpl):
            print(f"Parameter FP_METADATA_TPL ({fp_metadata_tpl}) (Keywords metadata) is not a file")
            check=False
        if not os.path.isdir(p_photos_root):
            print(f"Parameter P_PHOTOS_ROOT ({p_photos_root}) (Image root directory) is not a directory")
            check=False

        if not check:
            print("CHECK went wrong, check your settings")
            return

        self.file_dict = file_info.get_file_dict(p_photos_root,regex_file_rules_dict={},
                                            filetype_classes_dict=ImageFileValidator.FILETYPE_CLASSES_DICT)

        self.file_dict={k:v for (k,v) in self.file_dict.items() if is_relevant(k,v)}

    def consolidate_control_data(self):
        """ reads / consolidates all meta data
            updates file_info dictionary
        """

        p_old = os.getcwd()

        print("***********************************")
        print("*** CHECK FOR CONTROL FILE CREATION")
        for p,path_info in self.file_dict.items():
            if not Path(p).joinpath(self.f_metadata).is_file():
                print(f"*** {p}")
                if input(f"Create missing metadata control file {self.f_metadata} (y)? ")=="y":
                    os.chdir(p)
                    shutil.copy2(self.fp_metadata_tpl,self.f_metadata)

        print("\n***********************************")
        print("*** VALIDATE CONTROL FILES")

        n_folder=0
        # now check all items
        for p,path_info in self.file_dict.items():
            os.chdir(p)
            p=Path(p)
            n_folder+=1
            print(f"\n*[{str(n_folder).zfill(2)}]* {p}")
            file_actions=deepcopy(ImageFileValidator.FILE_ACTIONS)
            # additional keywords for exif keyword file
            add_keywords=[]

            # check if there is at least 1 valid osm url
            osm_urls=file_info.get_latlon_reverse(p,show=False,geo=False)

            if len(osm_urls)>0:
                file_actions["URL_OSM_LINK"]["done"]=True
                # get the first entry
                osm_url=list(osm_urls.keys())[0]
                file_actions["URL_OSM_LINK"]["value"]=osm_url
                file_actions["URL_OSM_LINK"]["latlon"]=osm_urls[osm_url]["latlon"]

            # check if the control file is present
            if not p.joinpath(self.f_metadata).is_file():
                print(f"    - No metadata file {self.f_metadata} found, will skip")
                path_info["file_actions"]=file_actions
                continue

            # read config file
            config_dict=file_info.read_json(self.f_metadata)

            # set control file
            file_actions["CONTROL_FILE"]["done"]=True
            file_actions["CONTROL_FILE"]["value"]=config_dict.get("CONTROL_FILE")

            # check for metadata profile
            if config_dict.get("META_PROFILES_FILE"):
                if os.path.isfile(config_dict.get("META_PROFILES_FILE")):
                    file_actions["META_PROFILES_FILE"]["done"]=True
                    file_actions["META_PROFILES_FILE"]["value"]=config_dict.get("META_PROFILES_FILE")

            # check for image waypoint gps
            # assumes the existence of a gpx file with the folder name in filename
            for f in self.file_dict[str(p)]["files"]:
                if f.startswith(p.name) and f.endswith("gpx"):
                    file_actions["IMAGE_GPX"]["done"]=True
                    file_actions["IMAGE_GPX"]["value"]=f

            # process template information
            for action,action_info in file_actions.items():
                if not action_info["type"]=="tpl":
                    continue

                # check for existence of file
                if action.lower().endswith("file"):
                    if p.joinpath(config_dict.get(action,"NONE")).is_file():
                        action_info["done"]=True
                        action_info["value"]=p.joinpath(config_dict.get(action,"NONE"))
                        # special cases
                        if action=="WAYPOINT_FILE":
                            waypoints=file_info.read_waypoints(action_info["value"])
                            try:
                                if waypoints:
                                    action_info["latlon"]=[float(waypoints[1]["lat"]),
                                                        float(waypoints[1]["lon"])]
                                    action_info["datetime"]=waypoints[1]["datetime"]
                            # only get the first item
                            except IndexError:
                                pass
                        # get calibration image file exifs
                        elif action=="CALIB_IMG_FILE":
                            calib_img_exif=file_info.exiftool_read_single(config_dict.get(action,"NONE"))
                            if calib_img_exif:

                                dt=ImageFileValidator.get_datetime(calib_img_exif.get("DateTimeOriginal"))
                                if dt:
                                    action_info["datetime"]=dt

                                img_keywords=calib_img_exif.get("Keywords")
                                if img_keywords:
                                    action_info["keywords"]=img_keywords
                                    config_dict["CALIB_IMG_KEYWORDS"]=img_keywords

                                img_description=calib_img_exif.get("ImageDescription")
                                if img_description:
                                    action_info["img_description"]=img_description
                                    config_dict["CALIB_IMG_DESCRIPTION"]=img_description

                                try:
                                    gps_pos=calib_img_exif.get("GPSPosition").split(",")
                                    latlon=[float(latlon.strip().split(" ")[0]) for latlon in gps_pos]
                                except (ValueError,AttributeError) as e:
                                    print(f"Error getting/converting latlon coordinates from image ({e})")
                                    latlon=None

                                if latlon:
                                    action_info["latlon"]=latlon
                                url=calib_img_exif.get("SpecialInstructions")

                                if url:
                                    action_info["url"]=url
                        # parse default lat lon file
                        elif action=="DEFAULT_LATLON_FILE":
                            default_lat_lon_file=config_dict.get(action)
                            if default_lat_lon_file:
                                default_lat_lon=file_info.read_json(default_lat_lon_file)
                                if default_lat_lon.get("latlon"):
                                    action_info["latlon"]=default_lat_lon.get("latlon")

                # def read_waypoints(fp,show=False,tz_code="Europe/Berlin"):
                # check for existence of parameter
                else:
                    if not config_dict.get(action) is None:
                        action_info["done"]=True
                        # special case contains geo coordinates
                        if "latlon" in action.lower():
                            action_info["latlon"]=config_dict.get(action)
                        elif action.lower().endswith("datetime"):
                            action_info["datetime"]=ImageFileValidator.get_datetime(config_dict[action])
                        elif action.lower() == "url_osm":
                            action_info["url"]=config_dict.get(action)
                        else:
                            action_info["value"]=config_dict.get(action)


            # identify most relevant item containing  lat lon coordinates in this order
            latlon_actions=["WAYPOINT_FILE","URL_OSM_LINK","DEFAULT_LATLON"]
            for action in latlon_actions:
                latlon = file_actions[action].get("latlon")
                if latlon:
                    print(f"    Using latlon from {action}, coordinates {latlon}")
                    break
            # latlons=[file_actions[action].get("latlon") for action in latlon_actions]
            # latlons=[latlon for latlon in latlons if not latlon is None]
            # if latlons:
            #     latlon=latlons[0]

            # get geo info
            geo_info=file_actions.get("GEO_INFO")
            if geo_info:
                geo_info=geo_info.get("value","No reverse Geo Info available in Control File")
            print(f"    GEO: {geo_info}")

            # calculate difference to home
            if isinstance(latlon,list) and isinstance(self.latlon_home,list):
                dist=round(Geo.get_distance(latlon,self.latlon_home),1)
                print(f"    Distance: {latlon}-{self.latlon_home} (HOME): {dist}km")
                config_dict["DISTANCE_HOME_KM"]=dist
                distance_txt=[ImageFileValidator.DISTANCE_FROM_HOME[d] for d in ImageFileValidator.DISTANCE_FROM_HOME if dist <= d][0]
                config_dict["DISTANCE_TO_HOME"]=distance_txt
                add_keywords.append(distance_txt)

            # get all fields containing datetime information
            datetimes_dict={action:file_action.get("datetime") for action,file_action in file_actions.items()
            if file_action.get("datetime")}
            # ger first in order
            dt_fields=["WAYPOINT_FILE","CALIB_IMG_FILE","CALIB_DATETIME"]
            field=""
            for field in dt_fields:
                if datetimes_dict.get(field):
                    break
            if field:
                dt=datetimes_dict.get(field)
                # get datetimes
                dt_text=ImageFileValidator.get_datetime_text(dt)
                print(f"    Datetime from field {field}: {dt} {dt_text}")
                add_keywords.extend(dt_text)

            # check for exif keyword profiles
            if not file_actions["META_PROFILES_FILE"]["done"]:
                print("    No Exif Attributes Files / no json for EXIF profiles found")
                print(f"    Check if file {config_dict.get('META_PROFILES_FILE','PATH NOT SET IN CONFIG')} exists")
            else:
                # update keyword file in dialogue if it doesn't exist yet
                ImageFileValidator.update_keyword_file(config_dict.get("META_PROFILES_FILE"),config_dict.get('META_FILE'),
                                prompt=True,update=False)

                # silenty update keywords that were found during this run
                if add_keywords:
                    keyword_s=ImageFileValidator.update_keyword_file(config_dict.get("META_PROFILES_FILE"),
                                                config_dict.get('META_FILE'),
                                                prompt=False,update=True,add_keywords=add_keywords)
                    config_dict["EXIF_KEYWORDS"]=keyword_s

            # update config dict / check if there is an issue with datetime
            config_dict["CONFIG_CHANGED"]=DateTime.now().replace(microsecond=0).isoformat()
            config_dict["CONFIG_CHANGED_BY"]="CONFIG_UPDATER"

            file_info.save_json(self.f_metadata,config_dict)
            path_info["file_actions"]=file_actions

        os.chdir(p_old)

    def display_file_actions(self)->None:
        """ Display collected metdata information
            (consolidate_control_data needs to be executed)
        """
        pp = pprint.PrettyPrinter(indent=3)
        for p,path_info in self.file_dict.items():
            print(f"\n*** {p}, File Actions:")
            pp.pprint(path_info.get("file_actions",{}))

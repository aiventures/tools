""" Utility to create a Waypoint file from a template file and a given image
    https://en.wikipedia.org/wiki/GPS_Exchange_Format
    Instruction to create a template :
    Create a waypoint file containing one Waypoint
    Replace some of the elements by keywords as shown
    to be replaced by this helper utility
    ...
      <wpt lat="_LAT_" lon="_LON_">
        <ele>_ELE_</ele>
        <time>_TIME_</time>
        <name>CALIB</name>
        ...
        <type>user</type>
        <extensions>
          ...
          <ctx:CreationTimeExtension>
            <ctx:CreationTime>_CREATED_</ctx:CreationTime>
          </ctx:CreationTimeExtension>
        </extensions>
      </wpt>
"""
import os
import json
import re
from pathlib import Path
from json import JSONDecodeError
from datetime import datetime as DateTime
from dateutil.parser import ParserError as DateUtilParserError
from image_meta.persistence import Persistence
from image_meta.util import Util

UTC="UTC"
LOCAL="LOCAL"
TIMESTAMP="TIMESTAMP"
TIMEZONE="TIMEZONE"
URL_OSM=r"https://www.openstreetmap.org/#map=19/LAT/LON"

def read_image_meta(f_img:str,attributes="DateTimeOriginal",exiftool="exiftool.exe"):
    """
      f: filename of image
      attributes: Exif Metadata atttibutes Use "*" to read all metadata
    """
    EXIFTOOL_CMD='EXIFTOOL -s -json ATT "FILE"'
    output_json={}

    if isinstance(attributes,str):
        att_list=[attributes]
    elif isinstance(attributes,list):
        att_list=attributes
    else:
        print(f"Attributes {attributes} is not string or list")
        return {}
    att_list=" ".join([("-"+att) for att in att_list])
    exiftool_cmd=EXIFTOOL_CMD.replace("EXIFTOOL",exiftool)
    exiftool_cmd=exiftool_cmd.replace("FILE",f_img)
    exiftool_cmd=exiftool_cmd.replace("ATT",att_list)
    stream=os.popen(exiftool_cmd)
    stream = os.popen(exiftool_cmd)
    output = stream.read()
    try:
        output_json=json.loads(output)
        if isinstance(output_json,list) and len(output_json)>0:
            output_json=output_json[0]
    except JSONDecodeError as e:
        print(f"Couldn't retrieve metadata JSON ({e.msg}), file: {f_img}")
    return output_json

def convert_datetime_string(dts:str,tz:str="Europe/Berlin"):
    """ converts a date time string to localized datetime according to timezone string
        into utc, timezone and utc timestamp
    """
    out={}
    try:
        out[UTC]=Util.get_localized_datetime(dts,tz,"UTC")
        out[LOCAL]=Util.get_localized_datetime(dts,tz,tz)
        out[TIMESTAMP]=int(out["UTC"].timestamp())
        out[TIMEZONE]=tz
    except DateUtilParserError as e:
        print(e)
    return out

def get_replace_dict(f_img:str,f_gpx:str,time_gps:str=None,tz:str="Europe/Berlin",exiftool="exiftool.exe"):
    """ based from timestamps and gps file, get relacement variables for waypoint template """
    DATE_TIME_ORIGINAL="DateTimeOriginal"
    REGEX_DATETIME=r"(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})"

    # get date time string from image
    exif_json=read_image_meta(f_img,attributes=DATE_TIME_ORIGINAL,exiftool=exiftool)
    date_time=exif_json.get(DATE_TIME_ORIGINAL)
    if date_time:
        dt_camera_s=re.findall(REGEX_DATETIME,date_time)
    else:
        print(f"No DateTime found in {f_img}")
        # return
    dt_camera_s=dt_camera_s[0]
    datetime_camera=convert_datetime_string(dt_camera_s,tz)


    # get gps date time if time string is given, otherwise use gps datetime from camera
    if time_gps:
        dt_gps_s = " ".join([dt_camera_s.split(" ")[0],time_gps])
        datetime_gps = convert_datetime_string(dt_gps_s,tz)
    else:
        datetime_gps = datetime_camera.copy()

    # calculate offset, output
    ts_gps=datetime_gps[TIMESTAMP]
    ts_cam=datetime_camera[TIMESTAMP]
    dt=ts_gps-ts_cam
    s=f"\n{tz}, DATE {datetime_camera[LOCAL]:%Y.%m.%d}, "
    s+=f"\nCAMERA ({datetime_camera[LOCAL]:%H:%M:%S})"
    s+=f"\nGPS    ({datetime_gps[LOCAL]:%H:%M:%S})"
    s+=f"\nOFFSET {dt}s"
    print(s)

    # get nearest GPS waypoint
    delta_ts=999999
    ts_min=0
    wpt_min=None

    # get gps track
    gpx_track= Persistence.read_gpx(gpsx_path=f_gpx)
    # get minimum track coordinates
    for ts,wpt in gpx_track.items():
        if abs(ts-ts_gps)<delta_ts:
            delta_ts=abs(ts-ts_gps)
            ts_min=ts
            wpt_min=wpt
    replace_dict = {}
    if wpt_min:
        dt_wpt_s=DateTime.fromtimestamp(ts_min).strftime("%Y:%m:%d %H:%M:%S")
        dt_now_s=DateTime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        datetime_wpt=convert_datetime_string(dt_wpt_s,tz)
        dt_wpt_utc_s=datetime_wpt["UTC"].strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"TRACK-WAYPOINT DIFFERENCE: {datetime_wpt[TIMESTAMP]-ts_gps}s")
        print(f"\n--- TRACK ({wpt_min['track_name']}) / ({dt_now_s}) ---")
        lat=str(round(wpt_min["lat"],6))
        lon=str(round(wpt_min["lon"],6))
        ele=str(int(wpt_min["ele"]))
        replace_dict["_CREATED_"]=dt_now_s
        replace_dict["_TIME_"]=dt_wpt_utc_s
        replace_dict["_LAT_"]=lat
        replace_dict["_LON_"]=lon
        replace_dict["_ELE_"]=ele
        wpt_name=DateTime.fromtimestamp(ts_min).strftime("%Y%m%d_%H%M%S")+"_CALIB"
        replace_dict["_CALIB_"]=wpt_name
        osm_url=URL_OSM.replace("LAT",lat).replace("LON",lon)
        replace_dict["URL"]=osm_url
        print(f"    LATLON: [{lat}, {lon}], ELEVATION: {ele}m")
        print(f"    TIME: {dt_wpt_s}, UTC: {dt_wpt_utc_s}")
        print(f"    OSM: {osm_url}")
    else:
        print("No Waypoint Information was found")

    return replace_dict

def create_wpt_file(f_img:str,f_gpx:str,f_waypt_template:str,
                    time_gps:str=None,tz:str="Europe/Berlin",
                    f_wpt:str="gps_wpt.gpx",
                    exiftool:str="exiftool.exe"):
    """ creates a new waypoint file in image path """

    REGEX_TIME=r"^\d{2}:\d{2}:\d{2}"
    # Checks time format
    if time_gps:
        dt=re.findall(REGEX_TIME,time_gps)
        if not dt:
            print(f"GPS Datetime format {time_gps} not in format HH:MM:SS")
            return

    # validate file paths
    files={"Image":f_img,"GPX":f_gpx,"WPT TEMPLATE":f_waypt_template}

    files_valid=all([os.path.isfile(f) for f in files.values()])
    if not files_valid:
        print(f"Some file paths not valid, check: {files}")
        return None
    print("--- Creating Waypoint File")
    p_img=Path(f_img)
    f_waypt=p_img.parent.joinpath(f_wpt)
    files["WPT"]=f_waypt
    for k,v in files.items():
        print(f"{k:<15}: {str(v)}")
    replace_dict=get_replace_dict(f_img,f_gpx,time_gps,tz,exiftool)

    out=""
    lines=Persistence.read_file(f_waypt_template)
    for l in lines:
        out_l=l
        for k,v in replace_dict.items():
            out_l=out_l.replace(k,str(v))
        out+=out_l
    Persistence.save_file(out,str(f_waypt))
    print(f"\n--- Saving: {f_waypt}")

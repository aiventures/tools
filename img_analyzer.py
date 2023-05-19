""" Class to analyze and visualize image metadata such as focus and metadat to be displayed in one image """

import os
import json
import logging

from json import JSONDecodeError
from pathlib import Path

from tools_console.persistence import Persistence
from tools_console.cmd_runner import CmdRunner as Runner
from tools import img_file_info_xls as fi

log = logging.getLogger(__name__)

class ImageAnalyzer():
    """ Analyzes Image Metadata and will write output.
    """

    EXIF_ANALYSIS_ATTRIBUTES=["FileName","DateTimeOriginal","Title","GPSPosition",
                            "AmbientTemperature#",
                            "Make","Model","Lens","LensSpec",
                            "FocalLength#","FocalLength35efl#",
                            "FOV#", "SpecialInstructions",
                            "Aperture","ShutterSpeed","ISO",
                            "ExposureCompensation","LightValue",
                            "FocusMode","FocusLocation","FocusDistance2#",
                            "HyperfocalDistance#","CircleOfConfusion#",
                            "Software",
                            "DateCreated","ImageWidth","ImageHeight","ImageSize",
                            "MeteringMode"]

    # folder names for temporary files and analysis files
    P_ANALYSIS="analysis"
    P_ANALYSIS_TMP="analysis_tmp"

    # delete all metadata in exiftool
    CMD_EXIFTOOL="exiftool.exe"
    CMD_MAGICK="magick.exe"

    # metadata file name
    FILE_META="metadata.json"

    # carriage return for magick command
    MAGICK_CR="\\n"

    CMD_EXIFTOOL_DELETE_META="_EXIF_ -All= -overwrite_original *.jpg"
    CMD_EXIFTOOL_JSON='_EXIF_ -json ATT -c "%.6f" -charset latin -charset filename=latin1 -s  -q *.jpg'

    # draw a box and add a text in a file using some parameters
    CMD_MAGICK_DRAW_FOCUS_BOX=('_MAGICK_ convert "_FILE_IN_" -pointsize _FONTSIZE_ -font _FONT_'
                            ' label:"_TEXT_" -gravity _GRAVITY_ -append -stroke _BOX_COLOR_'
                            ' -strokewidth _STROKE_WIDTH_'
                            ' -fill "rgba( _COL_R_, _COL_G_, _COL_B_, _TRANSPARENCY_ )"'
                            ' -draw "rectangle _X0_,_Y0_ _X1_,_Y1_" "_FILE_OUT_"')

    # command for magick box drawing
    MAGICK_BOX_CONFIG={"_MAGICK_":"magick.exe",
                    "_FONTSIZE_":"16","_FONT_":"Lucida-Sans-Typewriter-Regular",
                    "_TEXT_":"TEST TEXT TEST TEXT","_GRAVITY_":"West",
                    "_BOX_COLOR_":"orange","_STROKE_WIDTH_":"5",
                    "_COL_R_":"235", "_COL_G_":"155","_COL_B_":"52",
                    "_TRANSPARENCY_":"0.0" }


    def __init__(self,fp:str=".") -> None:
        log.debug("start")
        self._exiftool = ImageAnalyzer.CMD_EXIFTOOL
        self._magick = ImageAnalyzer.CMD_MAGICK
        self._exif_attributes = ImageAnalyzer.EXIF_ANALYSIS_ATTRIBUTES
        self._magick_box_config = ImageAnalyzer.MAGICK_BOX_CONFIG
        self._file_meta = ImageAnalyzer.FILE_META
        self._fp = None
        if not os.path.isdir(fp):
            log.error("%s is not a valid directory, exit",fp)
            return
        # setting paths
        self._fp = Path(fp).absolute()
        self._p_old = os.getcwd()
        p_analysis = ImageAnalyzer.P_ANALYSIS
        p_analysis_tmp = ImageAnalyzer.P_ANALYSIS_TMP
        self._p_analysis = Path(os.path.join(self._fp,p_analysis))
        self._p_analysis_tmp = Path(os.path.join(self._fp,p_analysis_tmp))

    @property
    def exiftool(self):
        """ exiftool executable """
        return self._exiftool

    @exiftool.setter
    def exiftool(self,exif):
        self._exiftool = exif

    @property
    def magick(self):
        """ magick executable """
        return self._magick

    @exiftool.setter
    def exiftool(self,magick):
        self._magick = magick

    def copy_images(self,image_size:int=1000,quality:int=80):
        """copy small versions of original files to work directory

        Args:
            image_size (int, optional): Image size. Defaults to 1000.
            quality (int, optional): Quality. Defaults to 80.
        """
        log.debug("start")
        Path.mkdir(self._p_analysis_tmp,exist_ok=True)
        Path.mkdir(self._p_analysis,exist_ok=True)
        os.chdir(self._fp)
        fi.magick_resize(fp=self._fp,magick=self._magick,
                        exiftool=self._exiftool,
                        image_size=image_size,
                        quality=quality,prefix=True,
                        remove_metadata=False,save=True,
                        descriptions=True,
                        target_path=self._p_analysis_tmp)

    @staticmethod
    def get_focus_position_rel(metadata:dict):
        """ get focus position from image metadata """
        log.debug("start")
        try:
            focus_location=metadata["FocusLocation"]
        except KeyError as e:
            log.warning("No focus location found in metadata %s",e)
            return None

        # shape: xmax, ymax, x,y
        pos =[int(pos) for pos in focus_location.split(" ")]
        if len(pos)==4:
            pos= [pos[2]/pos[0],pos[3]/pos[1]]
            return [round(p,3) for p in pos]
        else:
            return None

    @staticmethod
    def get_utf8_str(s:str,encoding:str="cp1252"):
        """ correct any encoding . windows encoding is default """
        log.debug("start")
        return s.encode(encoding).decode("utf-8")

    @staticmethod
    def create_analysis_text(metadata:dict,cr:str=MAGICK_CR):
        """Creates an output text string from metadata dict

        Args:
            metadata (dict): metadata as read from exiftool
            cr (str, optional): Line Break String. Defaults to MAGICK_CR (line break used by magick)

        Returns:
            str: analysis text string
        """

        log.debug("start")
        s=""
        f=metadata.get("SourceFile","N/A")
        d=metadata.get("DateTimeOriginal","N/A")
        s+=f"{f}, created: {d}"
        if metadata.get("AmbientTemperature"):
            s+=f", Temperature: {round(metadata.get('AmbientTemperature'))}C"
        s+=cr
        t=metadata.get("Title","N/A")
        g=metadata.get("GPSPosition","N/A")
        s+=f"{t} ({g})"+cr
        si=metadata.get("SpecialInstructions","N/A")
        s+=f"{si}"+cr
        make=metadata.get("Make","N/A")
        model=metadata.get("Model","N/A")
        lens=metadata.get("Lens")
        l_info=metadata.get("LensSpec")
        if lens:
            l_info=lens
        s+=f"{make} {model} ({l_info})"+cr
        fl=metadata.get("FocalLength","N/A")
        fl35=metadata.get("FocalLength35efl",0.)
        ap=metadata.get("Aperture","N/A")
        sh=metadata.get("ShutterSpeed","N/A")
        iso=metadata.get("ISO","N/A")
        sw=metadata.get("Software","N/A")
        s+=f"{fl}mm ({round(fl35,1)}mm@35mm)"
        if metadata.get("FOV"):
            s+=f" FOV {round(metadata.get('FOV'))}deg"
        s+=f" F/{ap} {sh}s ISO {iso}"
        if metadata.get("ExposureCompensation"):
            s+=f" {metadata.get('ExposureCompensation')}EV"
        if metadata.get("LightValue"):
            s+=f" {metadata.get('LightValue')}LV"
        s+=f" / {sw}"+cr

        fm=metadata.get("FocusMode","N/A")
        fd=metadata.get("FocusDistance2","N/A")
        hf=metadata.get("HyperfocalDistance",0.)
        s+=f"[{fm}], distance {fd}, hyperfoc. {hf:.1f}m, "
        if metadata.get("CircleOfConfusion"):
            s+=f"coc {round(1000*metadata['CircleOfConfusion'])}um, "
        foc_rel=ImageAnalyzer.get_focus_position_rel(metadata)
        if foc_rel:
            s+=f"foc.rel.pos {foc_rel}"
        s+=cr

        return s

    @staticmethod
    def get_focus_box(metadata:dict,rel_size=0.05)->list:
        """calculates coordinates of a focus box to be drawn into image
           from image metadata

        Args:
            metadata (dict): metadata as read from exiftool
            rel_size (float, optional): size of box in percentage of image sizes. Defaults to 0.05.

        Returns:
            list: _description_
        """
        log.debug("start")
        # calculates focus box area
        try:
            width=metadata["ImageWidth"]
            height=metadata["ImageHeight"]
            # focus_location=metadata["FocusLocation"]
        except KeyError:
            log.warning("Not all data found in metadata to create focus box for file %s",metadata.get('SourceFile'))
            return None

        try:
            x_foc_rel,y_foc_rel=ImageAnalyzer.get_focus_position_rel(metadata)
            x_foc=int(x_foc_rel*width)
            y_foc=int(y_foc_rel*height)
            dx,dy=[int(rel_size*width),int(rel_size*height)]
            # draw box: lower left, focus, upper right
            box=[[x_foc-dx,y_foc-dy],[x_foc,y_foc],[x_foc+dx,y_foc+dy]]
        except TypeError as e:
            log.error("Couldn't find autofocus box,%s",e)
            box=[[0,0],[1,1],[2,2]]

        for coord in box:
            if coord[0] <= 0:
                coord[0]=1
            if coord[1] <= 0:
                coord[1]=1
            if coord[0] >= width:
                coord[0]= width
            if coord[1] >= height:
                coord[1]= height
        return box

    def create_ana_images(self):
        """creates analysis images using image magick

        Returns:
            dict: image file metadata alongside wit magick command
        """
        log.debug("start")
        os.chdir(self._p_analysis_tmp)
        exif_attributes=self._exif_attributes
        exif_attributes=" ".join(["-"+a for a in exif_attributes])

        # quiet option suppreses regular output
        cmd_exif=ImageAnalyzer.CMD_EXIFTOOL_JSON.replace("_EXIF_",self._exiftool)
        cmd_exif=cmd_exif.replace("ATT",exif_attributes)

        cmd_out = None
        runner = Runner()
        ret_code=runner.run_cmd(cmd_exif)
        if ret_code == 0:
            cmd_out=runner.get_output()
        files_metadata={}

        try:
            files_metadata=json.loads(cmd_out)
        except JSONDecodeError as e:
            err_details={"msg":e.msg,"col":str(e.colno),"line":str(e.lineno)}
            log.error("JSON Decode Error: %(msg)s error occured in output at column %(col)s, line %(line)s",err_details)

        for file_metadata in files_metadata:

            filename=Path(file_metadata["SourceFile"])
            filename=filename.stem+"_ana"+filename.suffix
            file_metadata["TargetFile"]=os.path.join(self._p_analysis,filename)
            file_metadata["FocusBox"]=ImageAnalyzer.get_focus_box(file_metadata)
            file_metadata["Description"]=ImageAnalyzer.create_analysis_text(file_metadata)
            # convert to a os magick command
            draw_config=self._magick_box_config.copy()
            try:
                draw_config["_FILE_IN_"]=file_metadata["SourceFile"]
                draw_config["_FILE_OUT_"]=file_metadata["TargetFile"]
                draw_config["_TEXT_"]=file_metadata["Description"]
                draw_config["_X0_"]=str(file_metadata["FocusBox"][0][0])
                draw_config["_Y0_"]=str(file_metadata["FocusBox"][0][1])
                draw_config["_X1_"]=str(file_metadata["FocusBox"][2][0])
                draw_config["_Y1_"]=str(file_metadata["FocusBox"][2][1])
            except TypeError as e:
                log.error("not all metadata found to create focus box (%s)",e)
                continue
            # replace template
            cmd_magick=ImageAnalyzer.CMD_MAGICK_DRAW_FOCUS_BOX
            for k,v in draw_config.items():
                cmd_magick=cmd_magick.replace(k,v)
            file_metadata["CmdMagick"]=cmd_magick

        # writing files with focus box and meta data
        runner = Runner()
        for file_metadata in files_metadata:
            cmd=file_metadata.get("CmdMagick")

            if not cmd:
                continue
            ret_code=runner.run_cmd(cmd)
            if ret_code == 0:
                log.info("Writing file %s",file_metadata['TargetFile'])
                cmd_out=runner.get_output()
            else:
                log.error("Error writing file %s",file_metadata['TargetFile'])

        return files_metadata

    def delete_temp_files(self,remove_metadata:bool=True):
        """ deletes files non recursively in temporary folder

            Args:
            remove_metadata (bool, optional): _description_. Defaults to True.
                dict: image file metadata (if supplied metadata will be written)
        """

        log.debug("start")
        os.chdir(self._fp)
        # clean up
        if str(self._fp) in str(self._p_analysis_tmp):
            Persistence.delete_folder(self._p_analysis_tmp,False)
        os.chdir(self._p_analysis)

        # remove metadata from images
        if remove_metadata:
            log.info("Deletion of image metadata in folder %s",os.getcwd())
            runner = Runner()
            cmd_exiftool=ImageAnalyzer.CMD_EXIFTOOL_DELETE_META.replace("_EXIF_",self._exiftool)
            ret_code=runner.run_cmd(cmd_exiftool)
            if ret_code == 0:
                cmd_out=runner.get_output()
                log.info("Command Line returned: %s",cmd_out)

    def analyze(self)->dict:
        """ creates analysis images
        Returns:
            dict: returns the metadata dictionary
        """
        log.debug("start")
        old_cwd=os.getcwd()
        # create small sizze copies in a temporary folder
        self.copy_images()
        metadata = self.create_ana_images()
        os.chdir(self._p_analysis)
        if metadata:
            Persistence.save_json(self._file_meta,metadata)
        self.delete_temp_files()
        os.chdir(old_cwd)
        return metadata

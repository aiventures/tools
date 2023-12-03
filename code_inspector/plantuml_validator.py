""" Verify the relations and automatically comment them if necessary """
from inspect import Attribute
import copy
import os
import sys
import re
# import types
import json
import logging
from pathlib import Path
from tools import file_module as fm
from datetime import datetime as DateTime

logger = logging.getLogger(__name__)

class CONST():
    CONTENT = "content"
    TYPE = "type"
    GUIDS = "guids"
    ACTIVE = "active"
    INDEX = "index"
    COMMENT = "comment"
    COMMENT_MULTI = "comment_multi"
    BLANK = "blank"
    OBJECT = "object"
    DEFINITION = "definition"
    RELATION = "relation"
    NAME = "name"
    VALID = "valid"

    # plantuml symbols to relations mapping
    SYM_REL_DICT = {"<..":"import",
                "+--":"implements",
                "<|--":"inherits",
                "--":"relates"}

class PlantUmlValidator():
    
    def __init__(self,file) -> None:
        """ loads a plant uml file """        
        logger.debug("Start")
        self._plantuml_dict={}
        if not os.path.isfile(file):
            logger.error(f"Parameter {file} is not a file ")
            return
        self._file = file
        self._statsfile = None
        self._lines_dict={}
        self._guids_dict={}
        self._read_plantuml()      

    @staticmethod
    def _update_line_specs(line_dict)->dict:
        REGEX_GUID = "([0-9a-z]{32})"
        REGEX_RELATION = f"{REGEX_GUID}(.+){REGEX_GUID}"
        REGEX_DEFINITION = f" as.+{REGEX_GUID}"
        line = line_dict[CONST.CONTENT]
        linetype = CONST.CONTENT
        line_active = True
        if line.startswith("'"):
            linetype = CONST.COMMENT
            line_active = False
        elif line == "\n":
            linetype = CONST.BLANK
        # check for other type
        regex_relation = re.findall(REGEX_RELATION,line)
        if regex_relation:
            linetype = CONST.RELATION            
            line_dict[CONST.GUIDS]=[regex_relation[0][0],regex_relation[0][2]]
            relation = regex_relation[0][1].strip()
            relation = CONST.SYM_REL_DICT.get(relation,"unknown_relation")
            line_dict[CONST.RELATION]=relation
        regex_definition = re.findall(REGEX_DEFINITION,line)
        if regex_definition:
            line_dict[CONST.GUIDS]=[regex_definition[0]]
            linetype = CONST.DEFINITION
            line_dict[CONST.NAME]=" ".join(line.split()[:2])
        line_dict[CONST.TYPE]=linetype
        # adjust when multiline comment 
        if line_dict.get(CONST.COMMENT_MULTI,False):
            line_active = False
            linetype = CONST.COMMENT
        line_dict[CONST.ACTIVE] = line_active
        logger.debug(f"Line [{line_dict[CONST.INDEX]}]: {line_dict[CONST.TYPE]}, active: {line_dict[CONST.ACTIVE]}")

    def _update_guids_dict(self,line_dict):
        """ Update the Guid List """        
        index = line_dict.get(CONST.INDEX)
        guids = line_dict.get(CONST.GUIDS)
        name = line_dict.get(CONST.NAME)
        if not guids:
            return
        # only update active guids
        if not line_dict.get(CONST.ACTIVE):
            return
        for guid in guids:
            guid_dict = self._guids_dict.get(guid)
            if not guid_dict:
                guid_dict = {CONST.RELATION:{},CONST.NAME:{}}
                self._guids_dict[guid] = guid_dict
            objtype = line_dict[CONST.TYPE]
            if objtype==CONST.DEFINITION:
                guid_dict[CONST.NAME][index]=line_dict[CONST.NAME]
                logger.debug(f"({index}) <{objtype}> {name} [{guid}]")   
            elif objtype == CONST.RELATION:
                guid_dict[CONST.RELATION][index]=line_dict[CONST.RELATION]
                logger.debug(f"({index}) <{objtype}> [{line_dict[CONST.RELATION]}] [{guid}]")   
        pass
            
    def _read_plantuml(self):
        """ reads tge file for analysis """
        logger.debug("START")
        lines = fm.read_txt_file(self._file,skip_blank_lines=False)
        multi_line_comment = False
        for i,line in enumerate(lines):
            if line.startswith("/'"):
                multi_line_comment=True
            line_dict={}
            line_dict[CONST.INDEX]=i
            line_dict[CONST.CONTENT]=line
            line_dict[CONST.COMMENT_MULTI]=multi_line_comment
            PlantUmlValidator._update_line_specs(line_dict)
            # update info dictionaries
            self._lines_dict[i]=line_dict
            self._update_guids_dict(line_dict)
            
            if "'/" in line:
                multi_line_comment = False

    def get_validated_plantuml(self,drop_invalid:bool=False)->str:
        """ provides out string of validated plant uml 
            eventually also drops the corrected lines
        """
        logger.debug("start")
        out_dict = copy.deepcopy(self._lines_dict)

        invalid_lines = []
        # get all invalid lines 
        for guid,guid_info in self._guids_dict.items():
            names = list(guid_info[CONST.NAME].values())
            relations = list(guid_info[CONST.RELATION].keys())
            lines = [l+1 for l in relations]
            if len(names) != 1:
                logger.warning(f"[{guid}] invalid reference {names}, lines {lines}")
                invalid_lines.extend(relations)
        
        for line in invalid_lines:            
            line_dict = out_dict[line]
            content = "'!NOREF "+line_dict[CONST.CONTENT]
            logger.debug(f"Line [{line+1}]: {content[:35]}...")
            if not drop_invalid:
                out_dict[line][CONST.CONTENT]=content
            else:
                out_dict.pop(line)

        keys = sorted(list(out_dict.keys()))
        out_list=[]
        for key in keys:
            out_list.append(out_dict[key][CONST.CONTENT])
        
        return "".join(out_list)
    
    def save(self,filename:str=None):
        """ saves the validated file in the same folder with appended _corr 
            or using transferred name 
        """
        p = Path(self._file)
        if filename:
            name = filename
        else:
            name = p.stem+"_corr"+p.suffix
        p=os.path.join(p.parent,name)
        validated_s=self.get_validated_plantuml()
        logger.info(f"Saving validated plantuml: ({p}), length {len(validated_s)}")
        fm.save_txt_file(p,validated_s)
        return validated_s

    def _save_stats(self,stats_dict:dict=None)->str:
        """ saves stats returns filename """
        p = Path(self._file)
        name = p.stem+"_stats.json"
        p=os.path.join(p.parent,name)
        logger.debug(f"Saving stats ({p})")
        fm.save_json(p,stats_dict)    
        self._statsfile = p
        return p

    def get_stats(self,show:bool=False,save:bool=False)->dict:
        """ get some statistics """
        REGEX_OBJECT = '^\s{0,}(package|class).+"(.+)"'
        REGEX_MEMBER = "^\s{0,}\{(field|method)\}"
        stats_dict = {"package":0,"class":0,"method":0,"field":0}
        objects_dict = {"package":[],"class":[]}
        n_comments = 0        
        n_content = 0     
        n_guids = 0
        n_relations = 0   
        n_no_refs = 0
        for index,line in self._lines_dict.items():
            content = line[CONST.CONTENT]
            if not line[CONST.ACTIVE]:
                n_comments += 1
                continue
            n_content += 1
            regex= re.findall(REGEX_OBJECT,content)            
            if regex:  
                regex = regex[0]
                obj = regex[0]
                name = regex[1]
                if obj == "class" and "moduleclass" in content:
                    name += " (moduleclass)"
                objects_dict[obj].append(name)
            regex = re.findall(REGEX_MEMBER,content)
            if regex:
                regex = regex[0]
                stats_dict[regex]+=1
        n_total = n_comments + n_content
        logger.debug(f"Processed {n_total} lines")
        packages = objects_dict["package"]
        # process guids
        guid_infos=[]
        for guid,guid_info in self._guids_dict.items():
            name_dict = guid_info[CONST.NAME]
            relations=guid_info[CONST.RELATION]
            n_relations += len(relations)
            n_guids += 1
            if len(name_dict)==0:
                guid_info="NO_REFERENCE"
                n_no_refs += 1
            else:
                guid_info=list(name_dict.values())[0]
            if guid_info.startswith("class"):
                class_name = guid_info.split()[1].strip().replace('"',"")
                if class_name in packages:
                    guid_info = f'class "{class_name}" (moduleclass)'

            guid_info = f"[{guid}]: {guid_info}, {len(relations)} relations"
            guid_info = guid_info.replace('"',"")
            guid_infos.append(guid_info)                    
        logger.debug(f"Processed {n_guids} GUIDs")
        # update stats        
        for obj,obj_list in objects_dict.items():
            stats_dict[obj]=len(obj_list)
        stats_dict.update({"LINES_TOTAL":n_total,"LINES_CONTENT":n_content,"LINES:COMMENT":n_comments,
                             "GUIDS":n_guids,"GUID_RELATIONS":n_relations,"GUID_NO_REFS":n_no_refs})
        stats_out={"FILE":self._file,"DATE":DateTime.now().strftime("%Y-%m-%d %H:%M:%S"),"OBJECTS":objects_dict,"GUIDS":guid_infos,"STATS":stats_dict}
        if show:
            print(json.dumps(stats_out,indent=4))
        if save:
            self._save_stats(stats_out)
        return stats_out

    def open_stats(self):
        logger.debug(f"Open stats file ({self._statsfile})")
        if self._statsfile:            
            os.system(f"start {self._statsfile}")
        else:
            print("No stats file was saved")

if __name__ == "__main__":
    loglevel = logging.ERROR
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    
    file = r"C:\Users\<path to>\...plantuml"

    if not os.path.isfile(file):
        print(f"Parameter f: ({file}) is not a valid file")
        sys.exit(-1)

    plantUmlValidator = PlantUmlValidator(file)
    # save validated file
    if True:
        validated_s = plantUmlValidator.save()
    
    # get stats
    if True:
        stats_dict = plantUmlValidator.get_stats(show=True,save=True)
        # plantUmlValidator.open_stats()
        


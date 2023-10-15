""" handling arparse templates and configuration example """

import logging
import sys
import os
import json
from enum import Enum
from pathlib import Path
from datetime import datetime as DateTime
import argparse
import yaml
from yaml import CLoader

# hide the config path import the path ref as variable
from configpath import CONFIG_PATH

logger = logging.getLogger(__name__)
config_dict = {}

class CONFIG(Enum):
    """ CONFIG FILE MAIN CATEGORIES DEFINITION  """
    EXECUTABLES = "Links to Executable Programs "
    SCRIPTS = "Links to Win Scripts like shell scripts, bat files"
    SCRIPTS_BASH = "Links to Bash Scripts"
    PATHS = "Links to frequently used Paths "
    DOCUMENTS = "Lnks to frequently accessed documents"
    ENVIRONMENT_WIN = "Environment Variables (SET) for Windows Command Line"
    SHORTCUTS = "shortcut to any of the configuration elements above"
    CMD_PARAMS = "Command Line Parameters for any template scripts"

class LOGLEVEL(Enum):
    """ loglevel handling """
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL    

class PARSER_ATTRIBUTE(Enum):
    """ Configuration, each param is modeled as a dictionary """
    DESCRIPTION = "description"
    EPILOG      = "epilog"
    PROG        = "prog"
    PARAM       = "param"
    PARAM_SHORT = "param_short"
    DEFAULT     = "default"
    ACTION      = "action"
    DEST        = "dest"
    HELP        = "help"
    METAVAR     = "metavar" # used for help text
    TYPE        = "type"
    STORE_TRUE  = "store_true"
    STORE_FALSE = "store_false"
    VAR         = "variable"

class DEFAULT_PARSER_ATTRIBUTES(Enum):
    """ Default ARGPARSE PARAMETERS """
    FILE = "file"
    FILE_OUT = "file_out"
    CSV_SEPARATOR = "csv_separator"
    DECIMAL_SEPARATOR = "decimal_separator"
    LOGLEVEL = "loglevel"
    ADD_TIMESTAMP = "add_timestamp"

class EnumHelper():
    """ helper methods to get some values out of enums """

    @staticmethod
    def as_dict(enum_class:Enum)->dict:
        """ gets enum as dict """
        out = {}
        for enum_item in iter(enum_class):
            out[enum_item.name]=enum_item.value
        return out

    @staticmethod
    def keys(enum_class:Enum,lower:bool=False,upper:bool=False)->list:
        """ get names as list (optionally as lowercase / uppercase) """
        enum_dict = EnumHelper.as_dict(enum_class)
        keys = list(enum_dict.keys())
        if lower:
            keys = [k.lower() for k in keys]
        elif upper:
            keys = [k.upper() for k in keys]
        return keys

    @staticmethod
    def get_value(enum_class:Enum,name:str)->dict:
        """ returns enum value if keys found """
        out = None
        try:
            enum_value = enum_class[name]
            out = enum_value.value
        except KeyError:
            logger.error(f"Couldn't find Enum Value in Enum {enum_class.__name__}, key {name}")
        return out

    @staticmethod
    def get_values_from_keys(enum_class:Enum,keys:list,ignorecase:bool=True):
        """ get list of values matching enum keys, also with the option to ignore case """
        enum_dict = EnumHelper.as_dict(enum_class)
        if ignorecase:
            enum_lower = {}
            for k,v in enum_dict.items():
                enum_lower[k.lower()]=v
            enum_dict = enum_lower
            keys = [k.lower() for k in keys]
        enum_keys = list(enum_dict.keys())
        out=[]
        for k in keys:
            if k in enum_keys:
                out.append(enum_dict[k])
        return out

class PersistenceHelper():
    """ Helper class to read / write (single) file """

    # byte order mark indicates non standard UTF-8
    BOM = '\ufeff'
    NUM_COL_TITLE = "num" # csv column title for number
    ID_TITLE = "id" # column name of object header
    TEMPLATE_DEFAULT_VALUE = "undefined" # default value for template value

    ALLOWED_FILE_TYPES = ["yaml","txt","json","plantuml"]

    def __init__(self,f_read:str=None,f_save:str=None,**kwargs) -> None:
        """ constructor """
        self._cwd = os.getcwd()
        if f_read:
            if os.path.isfile(f_read):
                self._f_read = os.path.abspath(f_read)
                logger.info(f"File read path: [{self._f_read}]")
            else:
                self._f_read = None
                logger.warning(f"File path {f_read} not found, check")
        self._f_save = None
        if f_save:
            logger.info(f"File save path: {f_save}")
            self._f_save = f_save
        # get more params form kwargs
        self._dec_sep = kwargs.get("dec_sep",",")
        self._csv_sep = kwargs.get("csv_sep",";")
        self._add_timestamp = kwargs.get("add_timestamp",False)

        logger.debug(f"Decimal Separator: {self._dec_sep}, CSV Separator: {self._csv_sep}")

    @property
    def f_read(self)->Path:
        """ returns the original file path as path object """
        return Path(self._f_read)

    @property
    def f_save(self)->str:
        """ returns the original save path """
        if self._f_save:
            self._get_save_file_name()
        else:
            return None

    @staticmethod
    def replace_file_suffix(f_name:str,new_suffix:str):
        """ Replaces file suffix """
        p_file = Path(f_name)
        suffix = p_file.suffix
        if suffix:
            return f_name.replace(suffix,"."+new_suffix)
        else:
            return f_name+"."+new_suffix

    @staticmethod
    def dict_stringify(d:dict)->dict:
        """ converts a dict with objects to stringified dict (for json) """
        for k, v in d.copy().items():
            v_type = str(type(v).__name__)
            logger.debug(f"Key {k} type {v_type}")
            if isinstance(v, dict): # For DICT
                d[k]= PersistenceHelper.dict_stringify(v)
            elif isinstance(v, list): # itemize LIST as dict
                d[k] = [PersistenceHelper.dict_stringify(i) for i in v]
            elif isinstance(v, str): # Update Key-Value
                d.pop(k)
                d[k] = v
            elif isinstance(v,DateTime): # stringify date
                d.pop(k)
                d[k]=v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                d.pop(k)
                d[k] = v
        return d

    @staticmethod
    def get_headerdict_template(keys:list,attribute_dict:dict):
        """ creates a headerdict template from keys and attributes """
        default = PersistenceHelper.TEMPLATE_DEFAULT_VALUE
        out_dict = {}
        for key in keys:
            dict_line = {}
            for attribute,value in attribute_dict.items():
                if not value:
                    value = default
                dict_line[attribute]=value
            out_dict[key]=dict_line
        return out_dict

    @staticmethod
    def create_headerdict_template(f:str,headers:list,template_body:dict)->str:
        """ creates a headerdict template and saves it """
        template=PersistenceHelper.get_headerdict_template(headers,template_body)
        p_file=Path(f)
        p_suffix = p_file.suffix
        if not p_file.is_absolute():
            p_file = Path(os.path.join(os.getcwd(),f))
        p_file = str(p_file)
        if p_suffix.lower().endswith("yaml"):
            PersistenceHelper.save_yaml(p_file,template)
        elif p_suffix.lower().endswith("json"):
            PersistenceHelper.save_json(p_file,template)
        elif p_suffix.lower().endswith("csv"):
            csv_data = PersistenceHelper.headerdict2list(template)
            persistence_helper=PersistenceHelper(f_save=p_file)
            persistence_helper.save(csv_data)
        else:
            logger.error("File template creation only allowed for type yaml,json,csv")
        logger.info(f"Created Template file {p_file}")
        return p_file

    @staticmethod
    def headerdict2list(d:dict,filter_list:list=None,header_name:str=ID_TITLE,column_list:list=None)->list:
        """ linearizes a dictionary containing header and attributes
            sample_key1:
                comment: comment 1
                property1: value1.1
                property2: value1.2
                status: open
            ...
            you may filter out entries using keywords for fields

            [{"status":"ignore"},...] would ignore any dictionaries with field status having ignore as value
            {"<header_name>":"sample"}: Any entries with header containing "sample" would be filtered
            header name attribute may be adjusted
            field list can be passed to extract only a subset / for a given order
        """
        def is_passed(header,value_dict):
            passed = True
            for f in filter_list:
                filter_field = list(f.keys())[0]
                filter_value = f[filter_field]
                value = None
                if filter_field == header_name:
                    value = header
                else:
                    value = value_dict.get(filter_field)
                if not value:
                    continue
                if filter_value in value:
                    logger.info(f"Item [{header}] will be filtered, Rule ({filter_field}:{filter_value}), value ({value})")
                    passed = False
                    break
            return passed

        num_col_title = PersistenceHelper.NUM_COL_TITLE
        out_list = []
        columns=[]
        column_counts=[]
        index = 1
        for header,value_dict in d.items():
            if filter_list:
                passed = is_passed(header,value_dict)
                if passed is False:
                    continue
            keys = list(value_dict.keys())
            # get some stats
            columns.append(keys)
            columns = list(set(keys))
            column_counts.append(len(keys))
            column_counts=list(set(column_counts))
            line_dict = {num_col_title:str(index).zfill(2),header_name:header}
            index += 1
            for k in keys:
                line_dict[k]=str(value_dict[k])
            out_list.append(line_dict)

        logger.debug(f"Created {len(out_list)} entries, columns {columns}")
        if len(column_counts) > 1:
            logger.debug("Different Columns present for each line, appending missing columns")
            out_list_new = []
            for line_dict in out_list:
                out_dict_new={num_col_title:line_dict[num_col_title],header_name:line_dict[header_name]}
                for column in sorted(columns):
                    v = line_dict.get(column)
                    if v is None:
                        logger.debug(f"Adding empty value for line with key {line_dict[header_name]}")
                        v = ""
                    out_dict_new[column]=v
                out_list_new.append(out_dict_new)
            out_list = out_list_new

        if column_list:
            # create column subset only / use to ensure column order
            out_list_new = []
            for line_dict in out_list:
                out_dict_new={header_name:line_dict[header_name]}
                for column in column_list:
                    v = line_dict.get(column)
                    if v is not None:
                        out_dict_new[column]=v
                out_list_new.append(out_dict_new)
            out_list = out_list_new

        return out_list

    def _csv2dict(self,lines)->dict:
        """ transform csv lines to dictionary """
        out_list = []
        if len(lines) <= 1:
            logger.warning("Too few lines in CSV")
            return {}
        keys = lines[0].split( self._csv_sep)
        num_keys = len(keys)
        logger.debug(f"CSV COLUMNS ({num_keys}): {keys}")
        for i,l in enumerate(lines[1:]):
            values = l.split( self._csv_sep)
            if len(values) != num_keys:
                logger.warning(f"Entry [{i}]: Wrong number of entries, expected {num_keys} {l}")
                continue
            out_list.append(dict(zip(keys,values)))
        logger.debug(f"Read {len(out_list)} lines from CSV")
        return out_list

    def _dicts2csv(self,data_list:list)->list:
        """ try to convert a list of dictionaries into csv format """
        out = []
        if not list:
            logger.warning("no data in list")
            return None
        key_row = data_list[0]
        if not isinstance(key_row,dict):
            logger.warning("List data is ot a dictionary, nothing will be returned")
            return None
        keys = list(key_row.keys())
        out.append(self._csv_sep.join(keys))
        for data in data_list:
            data_row = []
            for k in keys:
                v=data.get(k,"")
                if self._csv_sep in v:
                    logger.warning(f"CSV Separator {v} found in {k}:{v}, will be replaced by _sep_")
                    v = v.replace(self._csv_sep,"_sep_")
                data_row.append(v)
            out.append(self._csv_sep.join(data_row))
        return out

    @staticmethod
    def read_txt_file(filepath,encoding='utf-8',comment_marker="# ",skip_blank_lines=True)->list:
        """ reads data as lines from file
        """
        lines = []
        bom_check = False
        try:
            with open(filepath,encoding=encoding,errors='backslashreplace') as fp:
                for line in fp:
                    if not bom_check:
                        bom_check = True
                        if line[0] == PersistenceHelper.BOM:
                            line = line[1:]
                            logger.warning("Line contains BOM Flag, file is special UTF-8 format with BOM")
                    if len(line.strip())==0 and skip_blank_lines:
                        continue
                    if line.startswith(comment_marker):
                        continue
                    lines.append(line.strip())
        except:
            logger.error(f"Exception reading file {filepath}",exc_info=True)
        return lines

    @staticmethod
    def read_yaml(filepath:str)->dict:
        """ Reads YAML file"""
        if not os.path.isfile(filepath):
            logger.warning(f"File path {filepath} does not exist. Exiting...")
            return None
        data = None
        try:
            with open(filepath, encoding='utf-8',mode='r') as stream:
                data = yaml.load(stream,Loader=CLoader)
        except:
            logger.error(f"Error opening {filepath} ****",exc_info=True)
        return data

    @staticmethod
    def read_json(filepath:str)->dict:
        """ Reads JSON file"""
        data = None

        if not os.path.isfile(filepath):
            logger.warning(f"File path {filepath} does not exist. Exiting...")
            return None
        try:
            with open(filepath,encoding='utf-8') as json_file:
                data = json.load(json_file)
        except:
            logger.error(f"Error opening {filepath} ****",exc_info=True)

        return data

    @staticmethod
    def save_json(filepath,data:dict)->None:
        """ Saves dictionary data as UTF8 json """
        # TODO encode date time see
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

        with open(filepath, 'w', encoding='utf-8') as json_file:
            try:
                json.dump(data, json_file, indent=4,ensure_ascii=False)
            except:
                logger.error("Exception writing file {filepath}",exc_info=True)

            return None

    @staticmethod
    def save_yaml(filepath,data:dict)->None:
        """ Saves dictionary data as UTF8 yaml"""
        # encode date time and other objects in dict see
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

        with open(filepath, 'w', encoding='utf-8') as yaml_file:
            try:
                yaml.dump(data,yaml_file,default_flow_style=False,sort_keys=False)
            except:
                logger.error(f"Exception writing file {filepath}",exc_info=True)
            return None

    def read(self):
        """ read file, depending on file extension """
        if not self._f_read:
            logger.error("No file found")
            return
        out = None
        p = Path(self._f_read)
        suffix = p.suffix[1:].lower()
        if suffix in ["txt","plantuml","csv"]:
            out = PersistenceHelper.read_txt_file(self._f_read)
            if suffix == "csv":
                out = self._csv2dict(out)
        elif suffix == "yaml":
            out = PersistenceHelper.read_yaml(self._f_read)
        elif suffix == "json":
            out = PersistenceHelper.read_json(self._f_read)
        else:
            logger.warning(f"File {self._f_read}, no supported suffix {suffix}, skip read")
            out = None

        logger.info(f"Reading {self._f_read}")

        return out

    def save_txt_file(self,filepath,data:str,encoding='utf-8')->None:
        """ saves string to file  """
        try:
            with open(filepath,encoding=encoding,mode="+wt") as fp:
                fp.write(data)
        except:
            logger.error(f"Exception writing file {filepath}",exc_info=True)
        return

    def get_adjusted_filename(self,f)->str:
        """ gets adjusted and absolute filename """

        p_file = Path(f)
        dt = DateTime.now().strftime('%Y%m%d_%H%M%S')
        if self._add_timestamp:
            p_file_new = p_file.stem+"_"+dt+p_file.suffix
        else:
            p_file_new = p_file.name

        # get path
        if p_file.is_absolute():
            p_path = str(p_file.parent)
        else:
            p_path = os.getcwd()

        f_adjusted = os.path.join(p_path,p_file_new)
        return f_adjusted

    def _get_save_file_name(self,f_save:str=None)->str:
        """ creates an adjusted and absolute save filename """
        if f_save is None:
            f_save = self._f_save

        if not f_save:
            logger.warning("No file name for saving data was found")
            return None

        f_save = self.get_adjusted_filename(f_save)
        return f_save

    def save(self,data,f_save:str=None)->str:
        """ save file, optionally with path, returns filename """
        f_save = self._get_save_file_name(f_save)

        if not f_save:
            return

        p = Path(f_save)
        suffix = p.suffix[1:].lower()

        if suffix in ["txt","plantuml","csv"]:
            if isinstance(data,list):
                try:
                    data = "\n".join(data)
                except TypeError:
                    # try to convert into a csv list
                    data = self._dicts2csv(data)
                    data = "\n".join(data)
                    if not data:
                        logger.error(f"Elements in list are not string / (plain) dicts, won't save {f_save}")
                        return
            if not isinstance(data,str):
                logger.warning(f"Data is not of type string, won't save {f_save}")
                return
            data = data+"\n"
            self.save_txt_file(f_save,data)
        elif suffix in ["yaml","json"]:
            if isinstance(data,list):
                data = {"data":data}
                logger.warning(f"Data is a list, will save it as pseudo dict in {suffix} File")
            if not isinstance(data,dict):
                logger.warning("Data is not a dict, won't save {f_save}")
                return
            # convert objects in json
            data = PersistenceHelper.dict_stringify(data)
            if suffix == "yaml":
                PersistenceHelper.save_yaml(f_save,data)
            elif suffix == "json":
                PersistenceHelper.save_json(f_save,data)
        else:
            logger.warning(f"File {f_save}, no supported suffix {suffix} (allowed: {PersistenceHelper.ALLOWED_FILE_TYPES}), skip save")
            return
        logger.info(f"Saved [{suffix}] data: {f_save}")
        return f_save

class Config():
    """ handles configuration """

    def __init__(self,f_config:str=None,params_template:str=None,
                 default_params:list=None,**kwargs) -> None:
        """ constructor """
        if not os.path.isfile(f_config):
            logger.warning(f"{f_config} is missing as Config File, skip")
            return
        self._config_dict = PersistenceHelper.read_yaml(f_config)
        self._argparser = ParseHelper(self,params_template,default_params,**kwargs)

    def get_config(self,config_key:Enum=None):
        """ gets the respective config area, should match to enum in CONFIG """
        try:
            key = CONFIG[config_key.name].name.lower()
            return self._config_dict.get(key,{})
        except (KeyError, AttributeError):
            logger.error(f"Config Key {config_key} doesn't match to CONFIG enums")
            return {}
    
    @property
    def argparser(self):
        return self._argparser

class ParseHelper():
    """ Arguments Parsing """
    DEFAULT = "default"
    ARGS =  "args"
    KWARGS = "kwargs"
    CMDPARAMS_DEFAULT = "cmdparams_default"

    def __init__(self,config:Config,
                 params_template:str=None,
                 params_default:list=None,
                 **kwargs) -> None:
        """ constuctor, uses the params dict from config file """
        self._params_template=params_template
        self._config = config
        self._arguments = []
        self._cmd_params_dict = config.get_config(CONFIG.CMD_PARAMS)
        # add additional params from default input args
        self._add_default_params_filters(params_default)        
        # add params from the template
        self._add_args_dict(params_template)

        # check for any additonal valiues relevant for configuration
        parse_args = {}
        prog = kwargs.get(PARSER_ATTRIBUTE.PROG.value)
        if prog:
            parse_args[PARSER_ATTRIBUTE.PROG.value]=prog
        desc = kwargs.get(PARSER_ATTRIBUTE.DESCRIPTION.value)
        if desc:
            parse_args[PARSER_ATTRIBUTE.DESCRIPTION.value]=desc        
        epilog = kwargs.get(PARSER_ATTRIBUTE.EPILOG.value)
        if epilog:
            parse_args[PARSER_ATTRIBUTE.EPILOG.value]=epilog
        parse_args = {}            
        self._parser = argparse.ArgumentParser(**parse_args)
        self._add_arguments()
    
    def _add_arguments(self):
        """ adds arguments to parser """        
        for arg in self._arguments:
            args = arg[ParseHelper.ARGS]
            kwargs = arg[ParseHelper.KWARGS]
            self._parser.add_argument(*args,**kwargs)
            default = arg.get(ParseHelper.DEFAULT)
            if default:
                self._parser.set_defaults(**default)


    def _add_default_params_filters(self,params_default:list)->None:
        """ get list of argparse default arguments from Enum List """
        # check for existing default params 
        cmdparams_default = ParseHelper.CMDPARAMS_DEFAULT
        cmdparams_default_dict = self._cmd_params_dict.get(cmdparams_default)
        if cmdparams_default_dict is None:
            logger.warning("Config Yaml seems to not cotnain cmd_params > cmdparams_default section, check")
            return
        default_params_keys = list(cmdparams_default_dict.keys())

        params_filter = [p.value for p in params_default if p.value in default_params_keys]
        if len(params_filter) == 0:
            params_filter = None
        self._add_args_dict(cmdparams_default,params_filter)

    def _add_args_dict(self,params_template:str,filter:list=None)->None:
        """ creates argparse list, if filter is supplied, only
            generate parse arguments for specified filters
        """
        c = ParseHelper
        arguments=[]
        parse_args_dict = self._cmd_params_dict.get(params_template)
        if not parse_args_dict:
            logger.error(f"There is no cmd_params configuration named {params_template}, check")
            return
        if filter is None:
            filter = list(parse_args_dict.keys())
        logger.info(f"Read ArgParse Config {params_template}")

        for param,params_dict in parse_args_dict.items():
            if not param in filter:
                continue
            param_name = params_dict.get(PARSER_ATTRIBUTE.PARAM.value)
            params_copy = params_dict.copy()
            param_short = "-"+params_copy.pop(PARSER_ATTRIBUTE.PARAM_SHORT.value)
            param = "--"+params_copy.pop(PARSER_ATTRIBUTE.PARAM.value)
            args = [param_short,param]
            kwargs=params_copy
            # add default value for case of input flag
            action = params_copy.get(PARSER_ATTRIBUTE.ACTION.value)
            default = None
            if action:
                if action == PARSER_ATTRIBUTE.STORE_FALSE.value:
                    default = {param_name:True}
                elif action == PARSER_ATTRIBUTE.STORE_TRUE.value:
                    default = {param_name:False}
            arguments.append({c.ARGS:args,c.KWARGS:kwargs,c.DEFAULT:default})
        self._arguments.extend(arguments)
        logger.info(f"Numbe of ParseArg arguments {len(self._arguments)} ")

    def parse_args(self,*testargs)->dict:
        """ get parsed results, additional args value can be used for debugging """
        args_dict = vars(self._parser.parse_args(*testargs))
        return args_dict        

class Runner():
    """ bundling of File Transformer Properties for parsing """
    DEFAULT_CONFIG = "config.json"

    """ Runs Command Line """

    def __init__(self,f_config:str=None,
                 params_template:str=None,
                 default_params:list=None,**kwargs) -> None:
        """ Constructor """
        self._path = Path(__file__)
        self._cwd = os.getcwd()
        self._f_config = None
        # argparse handling
        self._read_config(f_config)
        # get the Configuration from a yaml file
        self._config = Config(self._f_config,params_template,default_params,**kwargs)        

    def _get_file(self,f:str,)->str:
        """ trys to locate a file """
        p = Path(f)
        # get absolute path with current work directory as path
        if not p.is_absolute():
            p = Path(self._cwd,f)
        else:
            p = p.absolute()
        if p.is_file():
            return str(p)
        else:
            logger.warning(f"Couldn find a file at location {str(p)}")
            return None

    def _read_config(self,f_config:str=None)->None:
        """ reads config file """
        if f_config is None:
            f_config = Runner.DEFAULT_CONFIG
        self._f_config = self._get_file(f_config)
        self._f_config = f_config
        if self._f_config is None:
            return
    
    @property
    def config(self):
        return self._config

if __name__ == "__main__":
    # location of config file 
    # copy the configpath_template, supply path and 
    # set the path pointing to the param_config.yaml file
    f_config = CONFIG_PATH
    # get the argparseconfig from the yaml template file
    params_template = "cmdparams_template"
    # additional parameters (as defined in
    # cmd_params > cmdparams_default / or via Enum Definition)
    pa = DEFAULT_PARSER_ATTRIBUTES
    default_params = [pa.ADD_TIMESTAMP,pa.LOGLEVEL]
    # additional parameters that may be used
    kwargs = { PARSER_ATTRIBUTE.DESCRIPTION.value: "Description", # Argparse add. Description
               PARSER_ATTRIBUTE.PROG.value: "PROPG", # Used in Argparse description
               PARSER_ATTRIBUTE.EPILOG.value: "EPILOG DESCRIPTION"             
             }
    runner = Runner(f_config,params_template,default_params,**kwargs)
    # get the argparser 
    argparser = runner.config.argparser
    # testargs
    if True:
        config_dict = argparser.parse_args("--sbtrue -ll debug".split())
    else:
        config_dict = argparser.parse_args()

    loglevel = LOGLEVEL[config_dict.get("loglevel","DEBUG").upper()].value
    # loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # show config
    logger.info(f"\nConfig:\n {json.dumps(config_dict, indent=4)}")
    
    # main(**config_dict)
    # EnumHelper.as_dict(CONFIG)
    value = EnumHelper.keys(PARSER_ATTRIBUTE)
    pass


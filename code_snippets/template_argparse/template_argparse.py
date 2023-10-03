""" argparse template """

# https://docs.python.org/3/library/argparse.html
import argparse
import logging
import json
import sys
import os
from enum import Enum
from pathlib import Path
from datetime import datetime as DateTime
import yaml
from yaml import CLoader

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """ loglevel handling """
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    @staticmethod
    def get(level:str)->int:
        """ returns the integer loglevel with a default level of info"""
        if not level:
            level = "INFO"
        try:
            level = LogLevel[level.upper()].value
        except KeyError:
            level = LogLevel["INFO"].value
        return level

class ParserAttribute(Enum):
    """ Configuration, each param is modeled as a dictionary """
    DESCRIPTION = "description"
    EPILOG      = "epilog"
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

class ParserTemplate(Enum):
    """ Some Default Templates for arg parse input parameters """
    BOOL_TEMPLATE_TRUE = { "dest":None,
                           "action":ParserAttribute.STORE_TRUE.value,
                           "help":"No help"
    }

    BOOL_TEMPLATE_FALSE = { "dest":None,
                            "action":ParserAttribute.STORE_FALSE.value,
                            "help":"No help"
    }

    PARAM_TEMPLATE = { "default":None,
                       "type":str,
                       "help":"No help",
                       "metavar":"var"
                    }

    PARAM_INPUTFILE = { "default":"file_in",
                        "type":str,
                        "help":"Input file path",
                        "metavar": "<filename_in>"
                    }

    PARAM_OUTPUTFILE = { "default":"file_out",
                        "type":str,
                        "help":"Output file path",
                        "metavar": "<filename_out>"
                     }

    PARAM_LOGLEVEL = { "default":"info",
                       "type":str,
                       "choices":["debug","info","warning","error"],
                       "help":"Set loglevel to (debug,info,warning,error)",
                       "metavar":"<level>",
                       "args": ["--loglevel","-lg"]
                    }

    PARAM_CSV_SEPARATOR = { "default":";",
                            "type":str,
                            "help":"csv file separator, default is ;",
                            "metavar": "<sep>",
                            "args": ["--csv_sep","-cs"]
                           }

    PARAM_DECIMAL_SEP = {   "default":",",
                            "type":str,
                            "help":"decimal spearator, default is ,",
                            "metavar": "<decsep>",
                            "args": ["--dec_sep","-ds"]
                           }

    @staticmethod
    def get_parser_arguments(template,arg_long:str,arg_short:str,params:dict)->dict:
        """ get parser args and kwargs from a template dict """
        cmd_args=["--"+arg_long,"-"+arg_short]
        # try to get every arguments in the template
        template_dict = ParserTemplate[template.name].value.copy()
        if ( template == ParserTemplate.BOOL_TEMPLATE_TRUE or
           template == ParserTemplate.BOOL_TEMPLATE_FALSE ):
            template_dict["dest"]=arg_long
        # use passed arguments or default values from template
        for key,template_value in template_dict.items():
            try:
                value = params[key]
            except KeyError:
                if template_value:
                    value = template_value
                else:
                    logger.error(f"Parameter {arg_long} value missing for {key}")
                    continue
            template_dict[key] = value
        return (cmd_args,template_dict)

class PersistenceHelper():
    """ Helper class to read / write (single) file """

    # byte order mark indicates non standard UTF-8
    BOM = '\ufeff'

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
        if f_save:
            logger.info(f"File save path: {f_save}")
            self._f_save = f_save
        # get more params form kwargs
        self._dec_sep = kwargs.get("dec_sep",",")
        self._csv_sep = kwargs.get("csv_sep",";")
        logger.debug(f"Decimal Separator: {self._dec_sep}, CSV Separator: {self._csv_sep}")

    @staticmethod
    def dict_stringify(d:dict):
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

    def _csv2dict(self,lines):
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

    def _dicts2csv(self,data_list:list):
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
    def read_txt_file(filepath,encoding='utf-8',comment_marker="#",skip_blank_lines=True):
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
                    if line[0]==comment_marker:
                        continue
                    lines.append(line.strip())
        except:
            logger.error(f"Exception reading file {filepath}",exc_info=True)
        return lines

    @staticmethod
    def read_yaml(filepath:str):
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
    def read_json(filepath:str):
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
    def save_json(filepath,data:dict):
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
    def save_yaml(filepath,data:dict):
        """ Saves dictionary data as UTF8 yaml"""
        # encode date time and other objects in dict see
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

        with open(filepath, 'w', encoding='utf-8') as yaml_file:
            try:
                yaml.dump(data,yaml_file,default_flow_style=False)
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

    def save_txt_file(self,filepath,data:str,encoding='utf-8'):
        """ saves string to file  """
        try:
            with open(filepath,encoding=encoding,mode="+wt") as fp:
                fp.write(data)
        except:
            logger.error(f"Exception writing file {filepath}",exc_info=True)
        return

    def save(self,data):
        """ save file """
        if not self._f_save:
            logger.warning("No file name for saving data was found")
            return
        p = Path(self._f_save)
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
                        logger.error(f"Elements in list are not of type string / dict, won't save {self._f_save}")
                        return
            if not isinstance(data,str):
                logger.warning(f"Data is not of type string, won't save {self._f_save}")
                return
            data = data+"\n"
            self.save_txt_file(self._f_save,data)
        elif suffix in ["yaml","json"]:
            if isinstance(data,list):
                data = {"data":data}
                logger.warning(f"Data is a list, will save it as pseudo dict in {suffix} File")
            if not isinstance(data,dict):
                logger.warning("Data is not a dict, won't save {self._f_save}")
                return
            # convert objects in json
            data = PersistenceHelper.dict_stringify(data)
            if suffix == "yaml":
                PersistenceHelper.save_yaml(self._f_save,data)
            elif suffix == "json":
                PersistenceHelper.save_json(self._f_save,data)
        else:
            logger.warning(f"File {self._f_save}, no supported suffix {suffix} (allowed: {PersistenceHelper.ALLOWED_FILE_TYPES}), skip save {self._f_save}")
            return
        logger.info(f"Saved data: {os.path.abspath(self._f_save)}")

class ParserHelper():
    """ Helper class for argument parsing """

    def __init__(self,description=None,prog=None,epilog=None) -> None:
        argparser_args={}
        if prog:
            argparser_args["prog"]=prog
        if description:
            argparser_args["description"]=description
        if epilog:
            argparser_args["epilog"]=epilog

        if description:
            self._parser = argparse.ArgumentParser(**argparser_args)
        else:
            self._parser = argparse.ArgumentParser()
        self._args_dict = {}

    def parse_args(self,*testargs):
        """ get parsed results, additional args value can be used for debugging """
        self._args_dict = vars(self._parser.parse_args(*testargs))
        # transform special arguments
        loglevel = self._args_dict.get("loglevel")
        if loglevel:
            self._args_dict["loglevel"] = LogLevel.get(loglevel)

        return self._args_dict

    def add_arg_template(self,parser_template:Enum)->set:
        """ add arguments templates """
        template_dict = parser_template.value.copy()
        try:
            args = template_dict.pop("args")
        except KeyError:
            logger.warning(f"Couldn't find 'args' value in Parser Template {parser_template}")
            return
        self._parser.add_argument(*args,**template_dict)
        return (args,template_dict)

    def add_file_param(self,is_output:bool=False,suffix:str="txt",params:dict=None):
        """ add file input / output file, default is input """

        if not params:
            params = {}

        # default params
        if is_output:
            parser_template = ParserTemplate.PARAM_OUTPUTFILE
            short_param = "fo"
        else:
            parser_template = ParserTemplate.PARAM_INPUTFILE
            short_param = "fi"
        long_param = parser_template.value["default"]
        # set a default file name if not passed
        if params.get("default"):
            default_param = params.get("default")
        else:
            default_param = long_param
        default_file = default_param+"."+suffix
        params["default"] = default_file
        args, kwargs = ParserTemplate.get_parser_arguments(parser_template,long_param,short_param,params)
        self._parser.add_argument(*args,**kwargs)
        return (args,kwargs)

    def add_argument(self,long_arg:str,short_arg:str,argument_dict:dict,
                          parser_template:ParserTemplate.PARAM_TEMPLATE):
        """ adds an argument to the argument parser """
        args,kwargs=ParserTemplate.get_parser_arguments(parser_template,long_arg,short_arg,
                                                        argument_dict)
        self._parser.add_argument(*args,**kwargs)
        # add default value in case we have a bool argument
        if parser_template == ParserTemplate.BOOL_TEMPLATE_TRUE:
            self._parser.set_defaults(**{long_arg:False})
        elif parser_template == ParserTemplate.BOOL_TEMPLATE_FALSE:
            self._parser.set_defaults(**{long_arg:True})
        return (args,kwargs)

    def add_arguments(self,arg_list:list,
                      input_filetype:str="json",
                      output_filetype:str=None,
                      add_log_level:bool=True,
                      add_csv_separator:bool=True,
                      add_decimal_separator:bool=True):
        """ multiple inserts of arguments, each entry needs to conform to the schema
            [long_shortcut(str),short_shortcut(str),argument_dict(dict),ParserTemplate(ParserTemplate)]
            Optionally create argument templates for logging level, input file and output file
            file siffixes supported ["json","txt","yaml","plantuml"]
        """
        for arg in arg_list:
            long_arg = arg[0]
            short_arg = arg[1]
            arg_dict = arg[2]
            parser_template = arg[3]
            logger.debug(f"Adding Parameter {long_arg}/{short_arg}, template {parser_template.name}")
            self.add_argument(long_arg,short_arg,arg_dict,parser_template)
            logger.debug(f"Adding argument {long_arg}, {parser_template}")
        # add template parameters
        if input_filetype and input_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(suffix=input_filetype)
        if output_filetype and output_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(is_output=True,suffix=output_filetype)
        if add_log_level:
            self.add_arg_template(ParserTemplate.PARAM_LOGLEVEL)
            #self.add_loglevel_arg()
        if add_csv_separator:
            self.add_arg_template(ParserTemplate.PARAM_CSV_SEPARATOR)
            #self.add_csv_separator()
        if add_decimal_separator:
            self.add_arg_template(ParserTemplate.PARAM_DECIMAL_SEP)
            #self.add_decimal_separator()

def get_argument_list()->list:
    """ compiles argument list """
    arg_list=[["myvar","v",{  "default":"default","help":"help description","metavar":"<var>" } ,
               ParserTemplate.PARAM_TEMPLATE],
              ["myflag","f",
               { "help":"help flag (Default False, True if set)" },
               ParserTemplate.BOOL_TEMPLATE_TRUE]]
    return arg_list

if __name__ == "__main__":
    parser =  ParserHelper(description="Test Description",prog="my Prog",epilog="The End")
    # handle files, in general use case it is to read a file and save a file
    arg_list = get_argument_list()
    parser.add_arguments(arg_list,add_log_level=True,input_filetype="json",output_filetype="txt")

    # test file param, added manually
    # parser.add_file_param(is_output=True,suffix="json",params={"help":"my own help text","default":"my_own_file_name"})
    # parser.add_file_param(suffix="json",params={"help":"my own help text","default":"myownfile"})

    # all command line arguments passed as dict, get some cofnigurations
    # debug configuration by adding command string
    config_dict = parser.parse_args("--file_in test.json --file_out test_out.json".split())
    # config_dict = parser.parse_args()
    loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    csv_sep = config_dict.get("csv_sep",";")
    dec_sep = config_dict.get("dec_sep",",")
    file_in = config_dict.get("file_in")
    file_out = config_dict.get("file_out")

    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    logger.info(f"\nConfig:\n {json.dumps(config_dict, indent=4)}")

    # get the file names from configuration
    work_dir = r"C:\<...>\Desktop"
    os.chdir(work_dir)

    file_helper = PersistenceHelper(f_read=file_in,f_save=file_out)
    in_dict = file_helper.read()
    file_helper.save(in_dict)
    pass

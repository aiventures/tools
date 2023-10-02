""" argparse template """

# https://docs.python.org/3/library/argparse.html
import argparse
import logging
import json
import sys
import os
from enum import Enum
from pathlib import Path
from tools import file_module as fm

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

    PARAM_LOGLEVEL = { "default":"info",
                       "type":str,
                       "choices":["debug","info","warning","error"],
                       "help":"Set loglevel to (debug,info,warning,error)",
                       "metavar":"<level>"
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

    ALLOWED_FILE_TYPES = ["yaml","txt","json","plantuml"]

    def __init__(self,f_read:str=None,f_save:str=None) -> None:
        """ constructor """
        self._cwd = os.getcwd()
        if f_read:
            if os.path.isfile(f_read):
                self._f_read = os.path.abspath(f_read)
                logger.info(f"File read path: {f_read}")
            else:
                self._f_read = None
                logger.warning(f"File path {f_read} not found, check")
        if f_save:
            logger.info(f"File save path: {f_save}")
            self._f_save = f_save

    def read(self):
        """ read file, depending on file extension """
        if not self._f_read:
            logger.error("No file found")
            return
        out = None
        p = Path(self._f_read)
        suffix = p.suffix[1:].lower()
        if suffix in ["txt","plantuml","csv"]:
            out = fm.read_txt_file(self._f_read)
        elif suffix == "yaml":
            out = fm.read_yaml(self._f_read)
        elif suffix == "json":
            out = fm.read_json(self._f_read)
        else:
            logger.warning(f"File {self._f_read}, no supported suffix {suffix}, skip read")
            out = None

        logger.info(f"Reading {self._f_read}")

        return out

    def save(self,data):
        """ save file """
        if not self._f_save:
            logger.warning("No file name for saving data was found")
            return
        p = Path(self._f_save)
        suffix = p.suffix[1:].lower()
        if suffix in ["txt","plantuml","csv"]:
            if isinstance(data,list):
                data = "\n".join(data)
            if not isinstance(data,str):
                logger.warning("Data is not of type string, won't save")
                return
            fm.save_txt_file(self._f_save,data)

        if suffix in ["yaml","json"] and not isinstance(data,dict):
            logger.warning("Data is not a dict, won't save")
            return

        if suffix == "yaml":
            fm.save_yaml(self._f_save,data)
        elif suffix == "json":
            fm.save_json(self._f_save,data)

        if not suffix in PersistenceHelper.ALLOWED_FILE_TYPES:
            logger.warning(f"File {self._f_save}, no supported suffix {suffix}, skip save")

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

    def parse_args(self):
        """ get parsed results """
        self._args_dict = vars(self._parser.parse_args())
        # transform special arguments
        loglevel = self._args_dict.get("loglevel")
        if loglevel:
            self._args_dict["loglevel"] = LogLevel.get(loglevel)

        return self._args_dict

    def add_loglevel_arg(self)-> set:
        """ add loglevel option """
        args = ["--loglevel","-lg"]
        kwargs = ParserTemplate.PARAM_LOGLEVEL.value
        self._parser.add_argument(*args,**kwargs)
        return (args,kwargs)

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
                      add_log_level:bool=True,
                      input_filetype:str="json",
                      output_filetype:str=None):
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
        if add_log_level:
            self.add_loglevel_arg()
        if input_filetype and input_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(suffix=input_filetype)
        if output_filetype and output_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(is_output=True,suffix=output_filetype)


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

    # all command line arguments passed as dict
    config_dict = parser.parse_args()
    print(f"Config:\n {json.dumps(config_dict, indent=4)}")
    loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # get the file names from configuration
    file_in = config_dict.get("file_in")
    file_out = config_dict.get("file_out")
    file_helper = PersistenceHelper(f_read=file_in,f_save=file_out)

    pass


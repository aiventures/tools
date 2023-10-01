# """ sargparse template """
# https://docs.python.org/3/library/argparse.html
import argparse
import logging
import sys
from enum import Enum

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
    
    def add_loglevel_arg(self):
        """ add loglevel option """
        args = ["--loglevel","-lg"]
        kwargs = ParserTemplate.PARAM_LOGLEVEL.value
        self._parser.add_argument(*args,**kwargs)
    
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
            pass
    
    def add_arguments(self,arg_list:list,add_log_level:bool=True):
        """ multiple inserts of arguments, each entri needs to conform to the schema 
            [long_shortcut(str),short_shortcut(str),argument_dict(dict),ParserTemplate(ParserTemplate)]
        """
        for arg in arg_list:
            long_arg = arg[0]
            short_arg = arg[1]
            arg_dict = arg[2]
            parser_template = arg[3]
            logger.debug(f"Adding Parameter {long_arg}/{short_arg}, template {parser_template.name}")            
            self.add_argument(long_arg,short_arg,arg_dict,parser_template)
        if add_log_level:
            self.add_loglevel_arg()

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
    arg_list = get_argument_list()
    parser.add_arguments(arg_list,add_log_level=True)
    # all command line arguments passed as dict
    args_dict = parser.parse_args()
    print(args_dict)
    loglevel = args_dict.get("loglevel",LogLevel.INFO.value)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")     
    logger.info(f"hello {loglevel}")


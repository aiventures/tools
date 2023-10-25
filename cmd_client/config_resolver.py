""" resolving and parsing configuration yaml """

import re
import os
from pathlib import Path
import logging
import sys
from enum import Enum
from datetime import datetime as DateTime
from pathlib import PureWindowsPath, PurePosixPath, PurePath

import tools.cmd_client.constants as C
from tools.cmd_client.enum_helper import EnumHelper
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.cmd_runner import CmdRunner

logger = logging.getLogger(__name__)

class ConfigResolver():
    """ a class to parse the config yaml and to link it with file system objects """

    # one regex is to be used for catching params
    # (xyz [v]) is a variable v that will be used for
    # the pattern xyz v
    REGEX_PARAM=r"\[.+?\]"
    REGEX_PLACEHOLDER=r"\{.+?\}"

    def __init__(self,config_dict:dict) -> None:
        """ constructor """
        self._config_dict = config_dict
        if not config_dict:
            logger.warning("No Configuration was provided")
            return
        self.PATH_KEY = C.CONFIG_ATTRIBUTE.PATH.name.lower()
        self.FILE_KEY = C.CONFIG_ATTRIBUTE.FILE.name.lower()
        self.EXECUTABLE_KEY = C.CONFIG_ATTRIBUTE.EXECUTABLE.name.lower()
        self.TYPE = C.CONFIG_ATTRIBUTE.TYPE.name.lower()
        self.REF_KEY = C.CONFIG_ATTRIBUTE.REFERENCE.name.lower()
        self.RESOLVED_PATH = C.CONFIG_ATTRIBUTE.RESOLVED_PATH_REF.name.lower()
        self.RESOLVED_FILE = C.CONFIG_ATTRIBUTE.RESOLVED_FILE_REF.name.lower()
        self.HELP = C.CONFIG_ATTRIBUTE.HELP.name.lower()
        self.PATTERN_KEY = C.CONFIG_ATTRIBUTE.PATTERN.name.lower()
        self.PARAM_KEY = C.CONFIG_ATTRIBUTE.PARAM.name.lower()
        self.VALUE = C.CONFIG_ATTRIBUTE.VALUE.name.lower()
        self.EXPORT = C.CONFIG_ATTRIBUTE.EXPORT.name.lower()
        self.FILE_TYPES = [self.PATH_KEY,self.FILE_KEY,self.EXECUTABLE_KEY]
        self._config_types = self.get_config_types()

        # put together all files and paths, resolve
        self._resolve_references()
        self._resolve_patterns()

    @staticmethod
    def get_filled_pattern(pattern,**kwargs):
        """ replaces patterns in brackets with same name in kwargs
            if parama is None, the expression will be dropped
        """
        out = pattern
        regex = ConfigResolver.REGEX_PLACEHOLDER
        placeholders = re.findall(regex,pattern)
        regex = ConfigResolver.REGEX_PARAM
        # get all placeholders
        for placeholder in placeholders:
            # within each placeholder, get the param
            placeholder_out = placeholder
            params = re.findall(regex,placeholder)
            complete = True
            for param in params:
                attribute = param[1:-1].strip()
                value = kwargs.get(attribute)
                if not value:
                    logger.info(f"Attribute {attribute} not found in parameters")
                    complete = False
                    break
                logger.debug(f"Replacing {param} using {value}")
                placeholder_out=placeholder_out.replace(param,value)
            if complete:
                out = out.replace(placeholder,placeholder_out[1:-1])
            else:
                out = out.replace(placeholder,"")
        return out.strip()

    def get_config_types(self)->list:
        """ get validated available config types as validated Enum Keys"""
        all_configs = EnumHelper.keys(C.CONFIG,lower=True,as_dict=True)
        configs_available = list(self._config_dict.keys())
        # validate against Enum
        configs_available = [c for c in configs_available if c in all_configs.values()]
        logger.debug(f"Configuration Types Found: {configs_available}")
        # convert to enums
        configs_available = [EnumHelper.enum(C.CONFIG,k) for k in configs_available]
        return configs_available

    def _resolve_item(self,config:Enum,
                      name:str,attribute:str)->dict:
        """ either gets the item itself or the item
            being pointed to in configuration """
        # # check if it is referencing another part of the configuration
        # config_enum = EnumHelper.enum(C.CONFIG,config_value)
        # if config_enum:
        config_value,ref_config = self._get_config_item(config,name,attribute)
        if not config_value:
            return
        # if returned value is pointing to another configuration type
        # get the value for this reference
        config_ref = EnumHelper.enum(C.CONFIG,config_value)
        if config_ref:
            config_value,_ = self._get_config_item(config_ref,ref_config,attribute)
        return config_value

    def _get_config_item(self,config:Enum,
                            name:str,attribute:str):
        """ tries to retrieve a configuration value
            from config dict returns config category and name"""

        # check config types
        config_name = config.name
        if not config in self._config_types:
            logger.info(f"CONFIGURATION: No Configuration for {config_name}")
            return (None,None)
        # config type specific dict
        config_dict = self._config_dict.get(config.name.lower())
        # get specific config
        config_entry = config_dict.get(name)
        if config_entry is None:
            logger.warning(f"No Configuration [{config_name}]>[{name}]")
            return (None,None)
        # get config value
        config_value = config_entry.get(attribute)
        if config_value is None:
            logger.info(f"No Config Attribute [{config_name}]>[{name}]>[{attribute}]")
            return (None,None)
        # check if we need to redirect target configuration (reference)
        ref_config = config_entry.get(self.REF_KEY)
        if ref_config:
            name = ref_config
        return (config_value,name)

    def _validated_path(self,path:str)->str:
        """ resolves path information and returns absolute path None if invalid"""
        if path and os.path.isdir(path):
            return os.path.abspath(path)
        else:
            return

    def _validated_file(self,file:str,path:str)->str:
        """ resolves file information and returns absolute path None if invalid"""
        out_file = None
        if file and os.path.isfile(file):
            out_file = os.path.abspath(file)
        elif path is not None and file is not None and os.path.isdir(path):
            file_abs = os.path.join(path,file)
            if os.path.isfile(file_abs):
                out_file = os.path.abspath(file_abs)
        return out_file

    def _resolve_config(self,config_category_enum:Enum)->None:
        """ Resolves a configuration item   """
        config_category = config_category_enum.name.lower()
        config_category_dict = self._config_dict.get(config_category)
        if not config_category_dict:
            logger.warning(f"No Configuration: {config_category}")
            return

        for name,config in config_category_dict.items():
            # replace reference config if set
            #reference_config = config.get(ref_key)
            #if not reference_config:
            reference_config = name
            path = self._resolve_item(config_category_enum,
                                      reference_config,self.PATH_KEY)
            path = self._validated_path(path)
            file = self._resolve_item(config_category_enum,
                                      reference_config,self.FILE_KEY)
            file = self._validated_file(file,path)
            config[self.RESOLVED_PATH] = path
            config[self.RESOLVED_FILE] = file
            if not path and file:
                config[self.RESOLVED_PATH]=str(Path(file).parent)

    def _resolve_references(self):
        """ resolves references in the config and amends config """
        # list of enums to be ignored
        ignore_config = [C.CONFIG.PATTERN,C.CONFIG.SHORTCUT,
                         C.CONFIG.FILE,C.CONFIG.PATH,
                         C.CONFIG.EXECUTABLE,
                         C.CONFIG.CMD_PARAM,C.CONFIG.CMD_SUBPARSER]
        # start with path, file, executable
        self._resolve_config(C.CONFIG.PATH)
        self._resolve_config(C.CONFIG.FILE)
        self._resolve_config(C.CONFIG.EXECUTABLE)
        for config in iter(C.CONFIG):
            if config in ignore_config:
                continue
            self._resolve_config(config)

    def _resolve_pattern(self,param_name:str,param_dict:dict)->str:
        """ resolves a file used in pattern, returns path and file """
        resolved_path = None
        resolved_file = None
        config_type = param_dict.get(self.TYPE).lower()
        config_enum = None
        if config_type:
            config_enum = EnumHelper.enum(C.CONFIG,config_type)
        # config is refering to a configuration
        if config_enum:
            config_dict = self._config_dict.get(config_type)
            # check if there is a reference field use param name as default
            name = param_dict.get(self.REF_KEY)
            if not name:
                name = param_name
            config = config_dict.get(name)
            if config:
                resolved_path = config.get(self.RESOLVED_PATH)
                resolved_file = config.get(self.RESOLVED_FILE)
            else:
                logger.info(f"Pattern {param_name} can't be configured from [{config_type}]>[{name}]")
        # try to resolve file and path directly
        else:
            resolved_path = param_dict.get(self.PATH_KEY)
            resolved_file = param_dict.get(self.FILE_KEY)
            resolved_path = self._validated_path(resolved_path)
            resolved_file = self._validated_file(resolved_file,resolved_path)
            if resolved_file:
                resolved_path = str(Path(resolved_file).parent)
        return resolved_path,resolved_file

    def _resolve_pattern_params(self,param_dict:dict)->None:
        for param_name,param_info in param_dict.items():
            logger.debug(f"Resolve Pattern Param [{param_name}]")
            # param_type = param_info.get(self.TYPE)
            path,file = self._resolve_pattern(param_name,param_info)
            param_info[self.RESOLVED_FILE]=file
            param_info[self.RESOLVED_PATH]=path

    def _resolve_patterns(self)->None:
        """ resolve the pattern configuration should be done after
            references were resolved """
        pattern_configs = self._config_dict.get(self.PATTERN_KEY)
        if not pattern_configs:
            logger.info("no Config section [pattern] found")
            return
        for pattern_name, pattern_config in pattern_configs.items():
            logger.debug(f"Resolve Pattern [{pattern_name}]")
            pattern_params = pattern_config.get(self.PARAM_KEY)
            if pattern_params:
                self._resolve_pattern_params(pattern_params)
            else:
                logger.info(f"No pattern parameters for Pattern [{pattern_name}]")

    def get_pattern(self,name:str,**kwargs):
        """ fille a given pattern with predefined / submitted params """
        pattern_configs = self._config_dict.get(self.PATTERN_KEY)
        if not pattern_configs:
            logger.info("no Config section [pattern] found")
            return
        pattern_config = pattern_configs.get(name)
        if not pattern_config:
            logger.info(f"No Pattern Config [{name}] found")
            return

        pattern = pattern_config.get(self.PATTERN_KEY)
        if not pattern:
            logger.warning(f"No pattern found in cofiguration for pattern [{name}]")
            return

        params_dict = {}
        # supply all params given in config as template params
        pattern_params = pattern_config.get(self.PARAM_KEY)
        for param_name,param_dict in pattern_params.items():
            param_type = param_dict.get(self.TYPE,self.PARAM_KEY)
            match param_type:
                case self.PATH_KEY:
                    resolved_path = param_dict.get(self.RESOLVED_PATH)
                    if isinstance(resolved_path,str):
                        resolved_path = '"'+resolved_path.strip()+'"'
                    params_dict[param_name]=resolved_path
                case self.FILE_KEY | self.EXECUTABLE_KEY:
                    resolved_file = param_dict.get(self.RESOLVED_FILE)
                    if isinstance(resolved_file,str):
                        resolved_file = '"'+resolved_file.strip()+'"'
                    params_dict[param_name]=resolved_file
                case _:
                    params_dict[param_name]=param_dict.get(self.VALUE)
        # overwrite any default values using kwargs
        for param_name,param_value in kwargs.items():
            param_spec = pattern_params.get(param_name)
            is_file_type = False
            if param_spec:
                param_type = param_spec.get(self.TYPE)
                if param_type and param_type in self.FILE_TYPES:
                    is_file_type = True
            # wrap os objects in quotes
            if is_file_type:
                logger.debug(f"Adding quotes for param {param_name} (file type)")
                param_value='"'+param_value+'"'
            params_dict[param_name]=param_value

        filled_pattern = ConfigResolver.get_filled_pattern(pattern,**params_dict)
        return filled_pattern

    def _export_env_cmd(self,export_help:bool=True):
        """ exports environment variables as batch file alongside with help """
        pattern_help = "rem environment_win (_field_) [_help_]"
        pattern = "set _key_=_value_"
        dt_now = DateTime.now().strftime('%Y-%m-%d %H-%M-%S')
        out_echo=[f"echo ### SETTING ENVIRONMENT (created {dt_now}) ###"]        
        out = ["@echo off",f"rem CREATED {dt_now} using cmd_client"]
        config_env = C.CONFIG.ENVIRONMENT_WIN.name.lower()
        env_vars = self._config_dict.get(config_env)
        if not env_vars:
            logger.info(f"Couldn't get config type {env_vars}")
            return
        for env_var,env_info in env_vars.items():
            export_field = env_info.get(self.EXPORT)
            help_comment = env_info.get(self.HELP)
            if not export_field:
                continue            
            # use resolved path
            match export_field:
                case self.PATH_KEY:
                    export_field = self.RESOLVED_PATH
                case self.FILE_KEY:
                    export_field = self.RESOLVED_FILE
            value = env_info.get(export_field)
            if not value:
                continue
            # wrap path / file in quotes
            if export_field in [self.RESOLVED_PATH,self.RESOLVED_FILE]:
                value = '"'+value+'"'
            if help_comment:
                out_line = pattern_help.replace("_field_",env_var)
                out_line = out_line.replace("_help_",help_comment)
                out.append(out_line)
            out_line = pattern.replace("_key_",env_var)
            out_line = out_line.replace("_value_",value)
            logger.debug(f"Adding env [{env_var}]: {value}")            
            # add comment 
            out_echo_line = "echo "+out_line
            if help_comment:
                out_echo_line += " ("+help_comment+")"                 
            out.append(out_line)         
            out_echo.append(out_echo_line)
        out.extend(out_echo)
        return out

    def export(self,export_type,**kwargs):
        """ exports different types of configuration in different formats """
        export_enum = EnumHelper.enum(C.EXPORT,export_type)
        # Path("c:\\").drive / anchor
        if not export_enum:
            logger.info(f"Couldn't find an export option {export_type}, check settings")
            return
        match export_enum:
            case C.EXPORT.ENV_WIN:
                return self._export_env_cmd()
        pass
        return [None]


if __name__ == "__main__":

    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # for demo purposes read the configs from the file path
    p = Path(__file__).parent
    p_config = str(p.joinpath("param_config.yaml"))
    config_dict = PersistenceHelper.read_yaml(p_config)
    ch = ConfigResolver(config_dict)

    args = {"file":"<path to any local file>"}
    # testing the rendering of patterns
    if False:
        out = ch.get_pattern("vscode",**args)

    # testing the creation of env

    # todo evaluate pattern
    # todo create markdown report
    # todo create bat file to set env variables

    # use square brackets to denote expressions to be replaced / deleted
    if False:
        pattern="my expression with [parama] and [paramb] and [xyz paramc]"
        params = {"parama":"myvaluea","paramb":"myvalueb","paramc":None}
        fp = ConfigResolver.get_filled_pattern(pattern,**params)
        print(fp)
    # ch.resolve_references()
    if True:
        ph = PersistenceHelper()
        exported = ch.export(C.EXPORT.ENV_WIN)
        f = r"C:\<path to a local>\env.bat"
        ph.save_txt_file(f,"\n".join(exported))
        pass

    # resolve issues with quotes can be done using shlex split nit wit os.system
    # subprocess.run(shlex.split(out))
    #totalcmd.exe [/o] [/n] [/L=Drive1:\Directory1] [/R=Drive2:\Directory2] [/i=name.ini] [/f=ftpname.ini]
    #cmd_runner = CmdRunner()
    #cmd_runner.run_cmd(out)


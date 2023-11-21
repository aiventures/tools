""" Utility Class """

import logging
import os
from datetime import datetime as DateTime

import tools.cmd_client.constants as C
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.cmd_runner import CmdRunner

logger = logging.getLogger(__name__)

class Utils():
    """ Utilities Class / Reuse Elements"""

    @staticmethod
    def open_files(editor:str,files:dict)->None:
        """ opens files in standard editor """
        CMD_OPEN_FILE = '"_EDITOR_" "_FILE_"'
        cmd_runner = CmdRunner()        
        if not editor or not os.path.isfile(editor):
            logger.warning(f"Editor [{editor}] is not a valid editor location")
            return
        CMD_OPEN_FILE = CMD_OPEN_FILE.replace("_EDITOR_",editor)
        for f in files:
            cmd_open_file = CMD_OPEN_FILE.replace("_FILE_",f)
            cmd_runner.run_cmd(cmd_open_file)

    @staticmethod
    def get_config_element(config:str,
                           config_name:str=None,
                           config_attribute:str=None,
                           resolve:bool=False,
                           config_dict_in:dict=None):
        """ returns a config element down the hierarchy according to hierarchy
            CONFIG > CONFIG_NAME (TEMPLATE SPECIFIC) > CONFIG_ATTRIBUTE
            If none is used the complete config substructure is used
            if resolve is then resolved attribute values are returned
        """
        if not config:
            return
        config_type_dict = config_dict_in
        if not isinstance(config_type_dict,dict):
            logger.warning("There is no Configuration")
            return
        if not config_name:
            logger.debug(f"Returning Config {config}")
            return config_type_dict
        config_dict = config_type_dict.get(config_name,{})
        if not config_dict:
            logger.warning(f"There is no Configuration {config} > {config_name}")
        if not config_attribute:
            logger.debug(f"Returning Config {config} > {config_name}")
            return config_dict
        value = config_dict.get(config_attribute,None)
        if not config_dict:
            logger.warning(f"There is no Value {config} > {config_name} > {config_attribute}")
        else:
            logger.debug(f"Returning Config {config} > {config_name} > {config_attribute} > {value}")
        # now try to resolve attributes
        resolved = None
        match config_attribute:
            case C.FILE_KEY:
                resolved = config_dict.get(C.RESOLVED_FILE)
            case C.PATH_KEY:
                resolved = config_dict.get(C.RESOLVED_PATH)
            case C.EXPORT:
                export_field = config_dict.get(C.EXPORT)
                if not export_field:
                    logger.warning(f"Couldn't find export field in configuration {config}>{config_name}")
                resolved = config_dict.get(export_field)
        if resolve and resolved:
            value = resolved
        return value

    @staticmethod
    def export_env_win(config_dict:dict)->list:
        """ exports environment variables as windows batch file alongside with help
            will export items having the export parameter, this value will be exported
            only parts in envirionment win will be used
        """
        # TODO Implement export help files
        pattern_help = "rem environment_win (_field_) [_help_]"
        pattern = "set _key_=_value_"
        dt_now = DateTime.now().strftime('%Y-%m-%d %H-%M-%S')
        out_echo=[f"echo ### SETTING ENVIRONMENT (created {dt_now}) ###"]
        out = ["@echo off",f"rem CREATED {dt_now} using cmd_client"]
        config_env = C.key(C.CONFIG.ENVIRONMENT_WIN)
        env_vars = config_dict.get(config_env)
        if not env_vars:
            logger.info(f"Couldn't get config type {config_env}, check configuration file")
            return
        for env_var,env_info in env_vars.items():
            export_field = env_info.get(C.EXPORT)
            config_type = export_field
            help_comment = env_info.get(C.HELP)
            if not export_field:
                continue
            # use resolved path
            match export_field:
                case C.PATH_KEY:
                    export_field = C.RESOLVED_PATH
                case C.FILE_KEY | C.EXECUTABLE_KEY:
                    export_field = C.RESOLVED_FILE
            value = env_info.get(export_field)
            # try to resolve it from configuration
            if not value:
                config_attribute = env_info.get(config_type)
                value = Utils.get_config_element(config=config_type,config_name=config_attribute,
                                                 config_attribute=export_field,
                                                 config_dict_in=config_dict)
                if not value:
                    logger.info(f"Couldn't Resolve {config_env}: {config_attribute}")
                    continue
            # wrap path / file in quotes
            if export_field in [C.RESOLVED_PATH,C.RESOLVED_FILE]:
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

    @staticmethod
    def save_lines(f:str,lines:str):
        """ saves a text file """
        if not f:
            logger.warning("Can't save data, no file path submitted")
            return
        ph = PersistenceHelper()
        ph.save_txt_file(f,"\n".join(lines))
        if os.path.isfile(f):
            logger.info(f"Saved file: {f}")
        else:
            logger.warning(f"Couldn't save file {f}")
            f = None
        return f

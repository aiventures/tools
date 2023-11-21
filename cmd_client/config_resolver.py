""" resolving and parsing configuration yaml """

import re
import os
from pathlib import Path
import logging
import sys
from enum import Enum
from copy import deepcopy

import tools.cmd_client.constants as C
from tools.cmd_client.utils import Utils as U
from tools.cmd_client.enum_helper import EnumHelper
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.action_resolver import ActionResolver


logger = logging.getLogger(__name__)
class ConfigResolver():
    """ a class to parse the config yaml and to link it with file system objects """

    # one regex is to be used for catching params
    # (xyz [v]) is a variable v that will be used for
    # the pattern xyz v
    REGEX_PARAM=r"\[.+?\]"
    REGEX_PLACEHOLDER=r"\{.+?\}"

    def __init__(self,config_dict:dict,action_resolver:ActionResolver) -> None:
        """ constructor """
        self._config_dict = config_dict
        if not config_dict:
            logger.warning("No Configuration was provided")
            return
        self.FILE_TYPES = [C.PATH_KEY,C.FILE_KEY,C.EXECUTABLE_KEY]
        self._config_types = self.get_config_types()
        self._action_resolver = action_resolver
        # put together all files and paths, resolve
        self._resolve_references()
        self._resolve_patterns()
        self._action_resolver.config_dict = self._config_dict
        pass

    @staticmethod
    def get_filled_pattern(pattern,**kwargs):
        """ replaces patterns in brackets with same name in kwargs
            if param is None, the expression will be dropped
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
                            name:str=None,attribute:str=None):
        """ tries to retrieve a configuration value
            from config dict returns config category and name"""
        if not config:
            logger.warning("No Enum was passed")
            return

        config_name = config.name
        # check config types
        if not config in self._config_types:
            logger.info(f"CONFIGURATION: No Configuration for {config_name}")
            return (None,None)
        # config type specific dict
        config_dict = self._config_dict.get(C.key(config))
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
        ref_config = config_entry.get(C.REF_KEY)
        if ref_config:
            name = ref_config
        return (config_value,name)

    def _validated_path(self,path:str)->str:
        """ resolves path information and returns absolute path None if invalid"""
        if path:
            if os.path.isdir(path):
                return os.path.abspath(path)
            # now resolve the path variable if given
            resolved_path = self._get_config_element(C.PATH_KEY,path,C.RESOLVED_PATH)
            return resolved_path
        else:
            return

    def _validated_file(self,file:str,path:str)->str:
        """ resolves file information and returns absolute path None if invalid"""
        out_file = None
        # file path is already resolved
        if file and os.path.isfile(file):
            out_file = os.path.abspath(file)
        # path is given
        elif path is not None and file is not None and os.path.isdir(path):
            file_abs = os.path.join(path,file)
            out_file = os.path.abspath(file_abs)
            if not os.path.isfile(file_abs):
                logger.warning(f"Validated File {out_file} does not exist")
        # no path is given, try to get from dereferencing file
        elif file is not None and path is None:
            out_file = self._get_config_element(C.FILE_KEY,file,C.RESOLVED_FILE)

        return out_file

    def _resolve_indirect_config(self,name:str,config:dict)->str:
        """ tries to resolve indirect link from config """
        config_dict = self._config_dict
        path_config = config_dict.get(C.PATH_KEY,{})
        file_config = config_dict.get(C.FILE_KEY,{})
        exec_config = config_dict.get(C.EXECUTABLE_KEY,{})
        path_key = config.get(C.PATH_KEY,"###")
        file_key = config.get(C.FILE_KEY,"###")
        exec_key = config.get(C.EXECUTABLE_KEY,"###")
        if not os.path.isdir(path_key):
            path_resolved = path_config.get(path_key,{}).get(C.RESOLVED_PATH)
        else:
            path_resolved = path_key
        if not os.path.isfile(file_key):
            file_resolved = file_config.get(file_key,{}).get(C.RESOLVED_FILE)
        else:
            file_resolved = file_key
        if not os.path.isfile(exec_key):            
            exec_resolved = exec_config.get(exec_key,{}).get(C.RESOLVED_FILE)
        else:
            exec_resolved = exec_key
        if exec_resolved:
            return exec_resolved
        elif file_resolved:
            return file_resolved
        elif path_resolved:
            return path_resolved
        else:
            return None

    def _resolve_config(self,config_category_enum:Enum)->None:
        """ Resolves a configuration item   """
        config_category = C.key(config_category_enum)
        config_category_dict = self._config_dict.get(config_category)
        if not config_category_dict:
            logger.warning(f"No Configuration: {config_category}")
            return

        for name,config in config_category_dict.items():
            keys = list(config.keys())
            # replace reference config if set
            #reference_config = config.get(ref_key)
            #if not reference_config:
            reference_config = name
            path = self._resolve_item(config_category_enum,
                                      reference_config,C.PATH_KEY)
            path = self._validated_path(path)
            file = self._resolve_item(config_category_enum,
                                      reference_config,C.FILE_KEY)
            file = self._validated_file(file,path)
            # try to resolve from indirect link
            if not path and C.PATH_KEY in keys:
                path = self._resolve_indirect_config(name,config)
            # try to resolve from indirect link
            if not file:
                if C.EXECUTABLE_KEY in keys or C.FILE_KEY in keys:
                    file = self._resolve_indirect_config(name,config)
            if file and not path:
                path = str(Path(file).parent)

            config[C.RESOLVED_PATH] = path
            config[C.RESOLVED_FILE] = file
            if not path and file:
                config[C.RESOLVED_PATH]=str(Path(file).parent)

    def _resolve_references(self):
        """ resolves references in the config and amends config """
        # list of enums to be ignored
        ignore_config = [C.CONFIG.CMD_PARAM,
                         C.CONFIG.CMD_SUBPARSER,
                         C.CONFIG.CMD_MAP,
                         C.CONFIG.PATH,
                         C.CONFIG.FILE,
                         C.CONFIG.EXECUTABLE,
                         C.CONFIG.CONFIGURATION
                         ]
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
        config_type = param_dict.get(C.TYPE).lower()
        config_enum = None
        if config_type:
            config_enum = EnumHelper.enum(C.CONFIG,config_type)
        # config is refering to a configuration
        if config_enum:
            config_dict = self._config_dict.get(config_type)
            # check if there is a reference field use param name as default
            name = param_dict.get(C.REF_KEY)
            if not name:
                name = param_name
            config = config_dict.get(name)
            if config:
                resolved_path = config.get(C.RESOLVED_PATH)
                resolved_file = config.get(C.RESOLVED_FILE)
            else:
                logger.info(f"Pattern {param_name} can't be configured from [{config_type}]>[{name}]")
        # try to resolve file and path directly
        else:
            resolved_path = param_dict.get(C.PATH_KEY)
            resolved_file = param_dict.get(C.FILE_KEY)
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
            param_info[C.RESOLVED_FILE]=file
            param_info[C.RESOLVED_PATH]=path

    def _resolve_patterns(self)->None:
        """ resolve the pattern configuration should be done after
            references were resolved """
        pattern_configs = self._config_dict.get(C.PATTERN_KEY)
        if not pattern_configs:
            logger.info("no Config section [pattern] found")
            return
        for pattern_name, pattern_config in pattern_configs.items():
            logger.debug(f"Resolve Pattern [{pattern_name}]")
            pattern_params = pattern_config.get(C.PARAM_KEY)
            if pattern_params:
                self._resolve_pattern_params(pattern_params)
            else:
                logger.info(f"No pattern parameters for Pattern [{pattern_name}]")

    def _resolve_cmd(self,cmd_params_key:str,parsed_args:dict):
        """ map argparse params to configuration """
        resolved = {}
        type_cmdparam = C.key(C.CONFIG.CMD_PARAM)
        DEFAULT = C.key(C.CONFIG_ATTRIBUTE.DEFAULT)
        # get the params dict
        cmd_param_dict = self._get_config_element(config=type_cmdparam,
                                                 config_name=cmd_params_key)
        if not cmd_param_dict:
            logger.warning(f"Couldn't find cmd_param > [{cmd_params_key}]")
            return resolved

        for cmd_param,cmd_info in cmd_param_dict.items():
            if not isinstance(cmd_info,dict):
                continue
            # use argparse arguments or default value from
            value = parsed_args.get(cmd_param)
            if not value:
                value = cmd_info.get(DEFAULT)
            resolved[cmd_param] = value

        # also retrieve the argparse-config map
        type_cmdmap = C.key(C.CONFIG.CMD_MAP)
        MAP = C.key(C.CONFIG_ATTRIBUTE.MAP)
        cmd_map = self._get_config_element(config=type_cmdmap,
                                          config_name=cmd_params_key)
        resolved[MAP]=cmd_map
        logger.debug(f"Resolved Params for {cmd_params_key}: {list(resolved.keys())}")
        return resolved

    def _resolve_params(self,pattern_key:str,params_dict:dict)->dict:
        """ replaces any aliases by its  resolved values if there are any"""
        # get the pattern
        out_dict = deepcopy(params_dict)
        pattern_dict_params = self._get_config_element(config=C.PATTERN_KEY,
                                                      config_name=pattern_key)
        pattern_dict_params = pattern_dict_params.get(C.PARAM_KEY)
        if not pattern_dict_params:
            logger.warning(f"Pattern {pattern_key} not found in configuration, pls check, returns original dict")
            return params_dict
        for key,pattern_info in pattern_dict_params.items():
            value = params_dict.get(key)
            if not value:
                logger.debug(f"Pattern {pattern_key}, Param {key}, no value found")
                continue
            # check if there is a resolved file for this parameter in param configuration
            resolved_value = None
            param_type = pattern_info.get(C.TYPE)
            if not param_type:
                continue
            match param_type:
                case C.FILE_KEY:
                    resolved_value = pattern_info.get(C.RESOLVED_FILE)
                case C.PATH_KEY:
                    resolved_value = pattern_info.get(C.RESOLVED_PATH)
                case _:
                    resolved_value = pattern_info.get(C.VALUE)
            # check if the passed value is pointing to a configuration item
            config_dict = self._get_config_element(config=param_type, config_name=value)
            if config_dict:
                logger.debug(f"Pattern {pattern_key}, key {key}, config value {value} points to a config item")
                match param_type:
                    case C.FILE_KEY:
                        resolved_value = config_dict.get(C.RESOLVED_FILE)
                    case C.PATH_KEY:
                        resolved_value = config_dict.get(C.RESOLVED_PATH)
                    case _:
                        resolved_value = config_dict.get(C.VALUE)
            if resolved_value:
                logger.debug(f"Pattern {pattern_key}, key {key}, will replace value {value} with {resolved_value}")
            else:
                resolved_value = value
            out_dict[key] = resolved_value

        return out_dict

    def _resolve_actions(self,param_type:str,param_info_dict:dict)->dict:
        """ try to reolve  actions from configuration mapping """
        # get known actions
        actions = EnumHelper.keys(C.ACTION,lower=True)
        actions_dict = {}
        logger.info(f"Resolving actions for {param_type}")
        map_dict = param_info_dict.get(C.VALUE,{}).get(C.MAP,{}).get(C.MAP,{})
        if map_dict is None:
            logger.info("No action mapping defined")
            return

        param_info_dict = param_info_dict.get(C.VALUE,{})
        # check for each argparse parameter whether there is an action mapping
        for p_name,p_info in param_info_dict.items():
            if not p_info: # option was not chosen, skip
                continue
            action_map = map_dict.get(p_name)
            if not action_map:
                continue
            # try to map all actions params cmd_map > .. map > [argaprse] > param
            action = action_map.get(C.ACTION_KEY)
            config_dict = {}
            action_params = action_map.get(C.PARAM_KEY,{})
            for action_param,action_param_info in action_params.items():
                a_type = action_param_info.get(C.TYPE)
                a_param = action_param_info.get(C.PARAM_KEY)
                a_key = action_param_info.get(C.KEY)
                value = self._get_config_element(a_type,a_param,a_key,resolve=True)
                config_dict[action_param] = value

            logger.debug(f"Arg Parse [{p_name}], Resolve Action {action}")
            if not action:
                logger.warning(f"There is no action in Configuration {param_type}>{p_name}")
                continue
            if not action in actions:
                logger.info(f"Action {action} is not defined in (standard) ACTION Enum")
            # return the resolved action (action key alongside with variables)
            action_dict = self._action_resolver.resolve_action(action,config_dict)
            actions_dict.update(action_dict)

        return actions_dict

    def _map_params2config(self,param_maps:dict)->dict:
        """ map resolved params from input / parseargs to configuration
            default, main, custom maps (section cmd_map)
        """
        # out = {}
        out_pattern = {}
        out_action = {}
        # resolved values
        # resolved_default, resolved_main, resolved_subparser
        for param_type,param_info in param_maps.items():
            # cmd = None
            # cmd_map > [configuration]
            map_key = param_info.get(C.KEY)
            map_dict = param_info.get(C.VALUE,{}).get(C.MAP,{}).get(C.MAP)
            if not map_dict:
                logger.debug(f"No map Info for Param Configuration {param_type}")
                continue
            logger.debug(f"Map [{param_type}], cmd map [{map_key}]")

            # now do the confugration value mapping
            map_type = map_dict.get(C.TYPE)
            if not map_type in EnumHelper.keys(C.CMD_MAP,lower=True):
                logger.warning(f"Map {map_key} (used for {param_type}), map type {map_type} is not supported")
                continue
            # get the params dict from argparse
            params_dict = param_info.get(C.VALUE)
            # apply mapping rules
            # TODO CHECK WHETHER THE ACTION KEY NEEDS TO BE PART OF THE MAP
            match map_type:
                case C.PATTERN_KEY:
                    pattern_key = map_dict.get(C.PATTERN_KEY)
                    params_dict = self._resolve_params(pattern_key,params_dict)
                    if not pattern_key:
                        logger.warning("Map {map_key} (used for {param_type}), has no pattern defined")
                    pattern = self.get_pattern(pattern_key,**params_dict)
                    if pattern:
                        out_pattern[param_type]=pattern
                case C.MULTIPLE: # map multiple items
                    resolved_actions = self._resolve_actions(param_type,param_info)
                    if resolved_actions:
                        out_action.update(resolved_actions)
                case C.ACTION_KEY: # generic mapping of input params to configuration
                    # TODO Do The Action handling in CONFIG
                    # test single action
                    resolved_actions = self._resolve_actions(param_type,param_info)
                    if resolved_actions:
                        out_action.update(resolved_actions)
                case _:
                    logger.warning(f"Map {map_key} (used for {param_type}), Map Type {map_type} is not supported ")
        return {C.PATTERN_KEY:out_pattern,C.ACTION_KEY:out_action}

    def _resolve_cmd_param_map(self,params_template:str,param_map:dict,parsed_args:dict)->None:
        """ resolve a single param map """
        for map_param,map_param_info in param_map.items():
            if not map_param_info:
                continue
            # try to find a mapping if parameter is supplied
            if not parsed_args.get(map_param):
                continue
            if not isinstance(map_param_info,dict):
                continue
            logger.info(f"Mapping Params [{params_template}]>[{map_param}]")
            config_type = map_param_info.get(C.TYPE)
            config_map = map_param_info.get(C.MAP,{})
            pattern = map_param_info.get(C.PATTERN_KEY)
            pattern_params = []
            if pattern:
                pattern_info = self._get_config_element(C.PATTERN_KEY,pattern,C.PARAM_KEY)
                if pattern_info:
                    pattern_params = list(pattern_info.keys())

            # mapping_list = map_param_info.get(C.MAP)
            for mapping in config_map:
                if not isinstance(mapping,dict):
                    continue

                param = mapping.get(C.PARAM_KEY)
                if not param:
                    logger.warning(f"No param attribute found in input map, parameter [{map_param}] ")
                    continue

                src = mapping.get(C.SOURCE,{})
                config_param = src.get(C.PARAM_KEY)
                key = src.get(C.KEY)
                # we have a pattern, validate it against pattern
                if key and pattern and not param in pattern_params:
                    logger.warning(f"Key [{param}] is not in pattern {pattern}, check cmd_input_map config [{map_param}]")
                    continue

                # get the value
                value = self._get_config_element(config_type,config_param,key,resolve=True)

                s_param_path = f"[{config_type}>{config_param}>{key}]"
                if not value:
                    logger.warning(f"ARGPARSE [{map_param}]: No value found for Config {s_param_path}")
                    continue
                # pass over value
                logger.info(f"ARGPARSE [{map_param}]: map {s_param_path}>[{param}] ({value})")
                if value:
                    parsed_args[param] = value
                # do a check / right now only issue warning if parameter is not in configuration
                cmd_params = self._get_config_element(C.CMD_PARAM,params_template)
                if isinstance(cmd_params,dict):
                    cmd_params = list(cmd_params.keys())
                    if param not in cmd_params:
                        logger.warning(f"Map Input Param: No Config: {config_type}>{config_param}>{key} has no param [{param}]")

    def _resolve_cmd_param_maps(self,cmd_params_key:str,parsed_args:dict,
                          subparser_template:str=None,
                          cmd_params_default:str="cmdparam_default")->None:
        """ resolves input mapping  """

        cmd_input_map = self._get_config_element(C.CMD_INPUT_MAP,{})

        subparser_cmd = parsed_args.get(C.COMMAND)
        # subparser_map = {}
        # get the cmd cofig template for the subcommand
        cmd_params_subcommand = None
        if subparser_cmd:
            cmd_params_subcommand = self._get_config_element(C.CMD_SUBPARSER,
                                                            subparser_template,
                                                            subparser_cmd)
        input_maps = {C.DEFAULT:cmd_params_default,
                      C.MAIN:cmd_params_key,
                      subparser_cmd:cmd_params_subcommand}
        for input_map,map_key in input_maps.items():
            if not map_key:
                continue
            cmd_map = cmd_input_map.get(input_map,{})
            self._resolve_cmd_param_map(map_key,cmd_map,parsed_args)

    def get_cmd_dict(self,cmd_params_key:str,parsed_args:dict,
                          subparser_template:str=None,
                          cmd_params_default:str="cmdparam_default")->dict:
        """ parses / returns the argparse params, blends in configuration, returns command line(s) as array """
        cmd_out = []
        # MAP SHORTCUTS
        self._resolve_cmd_param_maps(cmd_params_key,parsed_args,
                           subparser_template,cmd_params_default)

        param_maps = self._resolve_argparser(cmd_params_key,parsed_args,
                           subparser_template,cmd_params_default)
        # TODO call this this in configuration
        cmd_out = self._map_params2config(param_maps)
        return cmd_out

    def _resolve_argparser(self,cmd_params_key:str,parsed_args:dict,
                          subparser_template:str=None,
                          cmd_params_default:str="cmdparam_default")->dict:
        """ tries to resolve commandline arguments with passed and default values
            returns map references alongside with resolved values from
            default values / parsed input
        """
        out = {}
        # 1st handle the default params
        resolved_default = self._resolve_cmd(cmd_params_default,parsed_args)
        # get cmd main params
        resolved_main = self._resolve_cmd(cmd_params_key,parsed_args)
        # handle subparser
        resolved_subparse = {}
        subparser_key = parsed_args.get(C.key(C.CONFIG_ATTRIBUTE.COMMAND))
        cmd_params_subparse = None
        if subparser_key:
            if not subparser_template:
                logger.warning(f"Subparser Command {subparser_key}, but no ")
                return {}
            # get the params template
            type_subparser = C.key(C.CONFIG.CMD_SUBPARSER)
            cmd_params_subparse = self._get_config_element(type_subparser,
                                                    subparser_template,
                                                    subparser_key)
            resolved_subparse = self._resolve_cmd(cmd_params_subparse,parsed_args)

        # put everything into an output structure so that mapping rules can be applied
        # right now we only have mappping to pattern
        mapped = {C.KEY:cmd_params_default,C.VALUE:resolved_default}
        out[C.RESOLVED_DEFAULT]=mapped
        mapped = {C.KEY:cmd_params_key,C.VALUE:resolved_main}
        out[C.RESOLVED_MAIN]=mapped
        mapped = {C.KEY:cmd_params_subparse,C.VALUE:resolved_subparse}
        out[C.RESOLVED_SUBPARSER]=mapped
        return out

    def _get_config_element(self,config:str,config_name:str=None,
                           config_attribute:str=None,resolve:bool=False,):
        """ returns a config element down the hierarchy according to hierarchy
            CONFIG > CONFIG_NAME (TEMPLATE SPECIFIC) > CONFIG_ATTRIBUTE
            If none is used the complete config substructure is used
            if resolve is then resolved attribute values are returned
        """
        config_dict = self._config_dict.get(config,{})
        return U.get_config_element(config,config_name,
                                    config_attribute,resolve,
                                    config_dict)

    def get_pattern(self,name:str,**kwargs):
        """ fill a given pattern with predefined / submitted params """

        # check if we have configuration for py scripts
        py_bat_name = self._get_config_element(C.CONFIGURATION_KEY,
                                                C.CONFIGURATION_PY_BAT)
        # for this check pattern name must be the same as given in configuration
        is_py_bat = False
        if py_bat_name == name:
            is_py_bat = True

        pattern_configs = self._config_dict.get(C.PATTERN_KEY)
        if not pattern_configs:
            logger.info("no Config section [pattern] found")
            return
        pattern_config = pattern_configs.get(name)
        if not pattern_config:
            logger.info(f"No Pattern Config [{name}] found")
            return

        pattern = pattern_config.get(C.PATTERN_KEY)
        if not pattern:
            logger.warning(f"No pattern found in cofiguration for pattern [{name}]")
            return

        params_dict = {}
        # supply all params given in config as template params
        pattern_params = pattern_config.get(C.PARAM_KEY)
        for param_name,param_dict in pattern_params.items():
            param_type = param_dict.get(C.TYPE,C.PARAM_KEY)
            match param_type:
                case C.PATH_KEY:
                    resolved_path = param_dict.get(C.RESOLVED_PATH)
                    if isinstance(resolved_path,str):
                        resolved_path = '"'+resolved_path.strip()+'"'
                    params_dict[param_name]=resolved_path
                case C.FILE_KEY | C.EXECUTABLE_KEY:
                    resolved_file = param_dict.get(C.RESOLVED_FILE)
                    if isinstance(resolved_file,str):
                        resolved_file = '"'+resolved_file.strip()+'"'
                    params_dict[param_name]=resolved_file
                case _:
                    params_dict[param_name]=param_dict.get(C.VALUE)
        # overwrite any default values using kwargs
        for param_name,param_value in kwargs.items():
            if not param_value:
                continue
            param_spec = pattern_params.get(param_name)
            is_file_type = False
            if param_spec:
                param_type = param_spec.get(C.TYPE)
                if param_type and param_type in self.FILE_TYPES:
                    is_file_type = True
            # wrap os objects in quotes
            if is_file_type:
                # wrap in quotes, do not do this in case we already have quotes in the pattern
                logger.debug(f"Adding quotes for param {param_name} (file type)")
                re_quotes=r"\"{\["+param_name
                has_quotes=re.findall(re_quotes,pattern)
                if not has_quotes:
                    param_value='"'+param_value+'"'
            # special case: for py_bat pattern replace dashes
            if is_py_bat and param_name == C.PARAMS_KEY:
                param_value = param_value.replace("_","-")
                param_value = param_value.replace('"',"")
                param_value = '"'+C.PARAMS_MARKER+param_value+C.PARAMS_MARKER+'"'
            params_dict[param_name]=param_value

        filled_pattern = ConfigResolver.get_filled_pattern(pattern,**params_dict)
        return filled_pattern

class CmdMap():
    """ Maps Input Parameters to Configuration Items """
    def __init__(self,config_dict:dict) -> None:
        self._map_keys = EnumHelper.keys(C.CMD_MAP,lower=True)
        self._config_dict = config_dict
        self._map_dict = self._config_dict.get(C.key(C.CONFIG.CMD_MAP))
        if not self._map_dict:
            logger.warning("Config yaml doesn't have a 'cmd_map' section")
        self._cmd_params={}
        self._cmd_map_dict={}
        self._cmd_map = None

    def map_pattern(self):
        """ maps cmd params to pattern fields """
        out_dict = {}
        pattern_key = self._cmd_map_dict.get(C.key(C.CONFIG.PATTERN))
        pattern = self._config_dict.get(C.key(C.CONFIG.PATTERN),{})
        pattern_params = pattern.get(pattern_key,{}).get(C.key(C.CONFIG_ATTRIBUTE.PARAM))
        if not pattern_params:
            logger.warning(f"Couldn't find PATTERN Configuration for Pattern {pattern_key}")
            return
        # map all transferred values get all pattern attributes
        for pattern_param in pattern_params.keys():
            value = self._cmd_params.get(pattern_param)
            if value:
                value = str(value)
            out_dict[pattern_param]=value
        return out_dict

    def map_cmd(self,cmd_map:str,cmd_params:dict)->dict:
        """ takes input paramter dict, creates parameter dict to be used for command line  """

        out_dict = {}
        cmd_map_dict = self._map_dict.get(cmd_map,{}).get(C.key(C.CONFIG_ATTRIBUTE.MAP))
        if not cmd_map_dict:
            logger.warning(f"CMD MAP {cmd_map} has no map section, check")
            return {}
        self._cmd_map_dict = cmd_map_dict
        map_type = cmd_map_dict.get(C.key(C.CONFIG_ATTRIBUTE.TYPE))
        if not map_type in self._map_keys:
            logger.warning(f"{map_type} is not a valid mapping, allowed values: {self._map_keys}")
            return
        map_type = EnumHelper.enum(C.CMD_MAP,map_type)
        self._cmd_params = cmd_params
        self._cmd_map = cmd_map

        match map_type:
            case C.CMD_MAP.PATTERN:
            # case "pattern":
                out_dict = self.map_pattern()
        return out_dict

if __name__ == "__main__":

    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # for demo purposes read the configs from the file path
    p = Path(__file__).parent
    p_config = str(p.joinpath("param_config.yaml"))
    config_dict = PersistenceHelper.read_yaml(p_config)
    ch = ConfigResolver(config_dict,ActionResolver())

    args = {"file":"<path to any local file>"}
    # testing the rendering of patterns
    if False:
        out = ch.get_pattern("vscode",**args)

    # testing the creation of env
    # todo create bat file to set env variables

    # use square brackets to denote expressions to be replaced / deleted
    if False:
        pattern="my expression with {[parama]} and {[paramb]} and {[xyz paramc]}"
        params = {"parama":"myvaluea","paramc":None}
        fp = ConfigResolver.get_filled_pattern(pattern,**params)
        print(fp)
    # ch.resolve_references()
    if False:
        ph = PersistenceHelper()
        exported = ch.export(C.EXPORT_OPTION.ENV_WIN)
        f = r"C:\<path to a local>\env.bat"
        ph.save_txt_file(f,"\n".join(exported))

    if True:
        cmd_map = CmdMap(config_dict)
        # file line extra
        cmd_params = {"file":"test_file","line":10}
        mapped = cmd_map.map_cmd("cmdparam_notepadpp",cmd_params)

    # resolve issues with quotes can be done using shlex split nit wit os.system
    # subprocess.run(shlex.split(out))
    #totalcmd.exe [/o] [/n] [/L=Drive1:\Directory1] [/R=Drive2:\Directory2] [/i=name.ini] [/f=ftpname.ini]
    #cmd_runner = CmdRunner()
    #cmd_runner.run_cmd(out)

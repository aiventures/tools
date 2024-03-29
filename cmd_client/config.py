""" Configuration Class """
import sys
import os
import logging
from datetime import datetime as DateTime
from enum import Enum
import json
from copy import deepcopy
import tools.cmd_client.constants as C
from tools.cmd_client.utils import Utils as U
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.parse_helper import ParseHelper
from tools.cmd_client.config_resolver import ConfigResolver
from tools.cmd_client.action_resolver import ActionResolver
logger = logging.getLogger(__name__)
class Config():
    """ handles configuration """

    def __init__(self,f_config:str=None,
                 params_template:str=None,
                 subparser_template:str=None,
                 default_params:list=None,
                 **kwargs) -> None:
        """ constructor """
        if not os.path.isfile(f_config):
            logger.warning(f"{f_config} is missing as Config File, skip")
            return
        self._f_config = f_config
        self._config_dict = PersistenceHelper.read_yaml(f_config)

        self._argparser = ParseHelper(self,params_template,subparser_template,
                                      default_params,**kwargs)
        self._action_resolver = ActionResolver()
        self._config_resolver = ConfigResolver(self._config_dict,self._action_resolver)
        self._configuration = {}
        self._get_configuration()

    def get_config(self,config_key:Enum=None):
        """ gets the respective config area, should match to enum in CONFIG """
        try:
            key = C.CONFIG[config_key.name].name.lower()
            return self._config_dict.get(key,{})
        except (KeyError, AttributeError):
            logger.error(f"Config Key {config_key} doesn't match to CONFIG enums")
            return {}

    def _get_configuration(self):
        """ reads the customizing part of the configuration """
        # maps configuration to config paths in configuration
        CONFIG_MAP = { C.CONFIGURATION_DEFAULT_EDITOR: {"config":C.EXECUTABLE_KEY,
                                                        "config_name":None,
                                                        "config_attribute":C.FILE_KEY},
                       C.CONFIGURATION_DEFAULT_VENV:   {"config":C.PATH_KEY,
                                                        "config_name":None,
                                                        "config_attribute":C.PATH_KEY},
                       C.CONFIGURATION_PY_BAT:         {"config":C.EXECUTABLE_KEY,
                                                        "config_name":None,
                                                        "config_attribute":C.FILE_KEY},
                      }

        configuration = deepcopy(self._config_dict.get(C.CONFIGURATION_KEY,{}))

        # change / validate settings
        for config,config_value in configuration.items():
            config_map = CONFIG_MAP.get(config)
            if config_map:
                config_map["resolve"]=True
                config_map["config_name"]=config_value
                # now get the element from the configuration
                element_value = self._config_resolver._get_config_element(**config_map)
                configuration[config]=element_value
                if not element_value:
                    config_map = None
            # treat other configurations
            match config:
                case C.CONFIGURATION_LOGLEVEL:
                    configuration[config]=C.LOGLEVEL[config_value.upper()].value
        # show config in log
        logger.info(f"\nParser Configuration:\n {json.dumps(configuration, indent=4)}")
        self._configuration = configuration

    def get_configuration(self,configuration:str)->str:
        """ gets a configuration setting """
        config_setting = self._configuration.get(configuration)
        if not config_setting:
            logger.warning(f" Invalid Configuration Setting, check configuration, values: {list(self._configuration.keys())}")
        return config_setting

    def get_cmd(self,parsed_args:dict)->str:
        """ receives the cmd commands as dict
            and attempts to construct
            an output command / resolving an action
        """
        cmd_params_key = self._argparser.params_template
        subparser_template = self._argparser.subparser_template
        # now get resolved values for the various configurations
        cmd_conmands = self._config_resolver.get_cmd_dict(cmd_params_key,parsed_args,
                                                        subparser_template)
        # TODO resolve items for actions

        return cmd_conmands

    @property
    def argparser(self):
        """ return the argparser """
        return self._argparser

    @property
    def config_resolver(self):
        """ return config_resolver """
        return self._config_resolver

    @property
    def configuration(self):
        """ return config_resolver """
        return self._configuration

    def _get_report_param_types(self)->list:
        param_types = [C.PATTERN_KEY,
                        C.EXECUTABLE_KEY,
                        C.FILE_KEY,
                        C.PATH_KEY,
                        C.SCRIPT_WIN,
                        C.SCRIPT_BASH,
                        C.ENVIRONMENT_WIN,
                        C.ENVIRONMENT_BASH,
                        C.SHORTCUT,
                        C.CMD_PARAM,
                        C.CMD_SUBPARSER,
                        C.CMD_MAP_KEY,
                        C.CMD_INPUT_MAP,
                        C.CMD_INPUT_MAP_PATTERN
                        ]
        return param_types

    def _action_create_report(self,action_info,)->str:
        """ creates a report using resolved file path returns created file"""
        f_report = action_info.get(C.CONFIG_REPORT)
        lines_report = ConfigReport(self).report()
        return U.save_lines(f_report,lines_report)

    def _action_export_env(self,action_info,)->str:
        """ creates a environment generation script from env command segment """
        f_env_bat = action_info.get(C.WIN_ENV_BAT)
        config_dict = self._config_resolver._config_dict
        env_lines = U.export_env_win(config_dict)
        return U.save_lines(f_env_bat,env_lines)

    def run_actions(self,actions_dict,**parsed_args):
        """ run specific actions """
        actions = {C.FILE_CREATED:[],C.ACTION_KEY:[]}
        for action,action_info in actions_dict.items():
            logger.info(f"Run action {action}")
            file_created = None
            match action:
                # create configuration report
                case C.ACTION_CREATE_REPORT:
                    file_created = self._action_create_report(action_info)
                # create export
                case C.ACTION_EXPORT_ENV:
                    file_created = self._action_export_env(action_info)
                # resolve any other custom actions defined by user
                case _:
                    action = None
                    self._action_resolver.run_actions(actions_dict,**parsed_args)
                    pass
            if action:
                actions[C.ACTION_KEY].append(action)
            if file_created:
                if os.path.isfile(file_created):
                    actions[C.FILE_CREATED].append(file_created)


        # todo define what need to be returned
        return actions

class ConfigReport():
    """ creates an output report  """

    def __init__(self,config:Config) -> None:
        self._config = config

    def report(self):
        """ returns the config as report """
        param_types = self._config._get_report_param_types()
        out = []
        toc = []
        dt = DateTime.now().strftime('%Y-%m-%d %H:%M:%S')
        info = f"**`Configuration ({self._config._f_config}) / {dt}`**"
        for config_type in param_types:
            title = f"CONFIGURATION {config_type.upper()}"
            out.append(f"# {title}")
            toc_link="#"+title.replace(" ","-").lower()
            toc.append(f"* [{title}]({toc_link})")
            config_elem = self._config._config_resolver._get_config_element(config=config_type)

            for config_name, config_info in config_elem.items():
                toc_link = "#"+config_type.lower()+"-"+config_name.lower()
                toc.append(f"  * [{config_type.upper()} {config_name.lower()}]({toc_link})")
                config_out = self._report_config(config_type,config_name,config_info)
                out.extend(config_out)
                out.append("\n  _[TOC](#toc)_")
        out.append("----")
        out.append(info)
        out=["# TOC",*toc,*out]
        return out

    def _report_config(self,config_type,config_name,config_dict):
        out = []
        pattern = config_dict.get(C.PATTERN_KEY)
        p = pattern if pattern else ""
        h = config_dict.get(C.HELP)
        out.append(f"## {config_type.upper()} `{config_name}`")
        if p:
            out.append(f"```\n{p}\n```")
        if h:
            out.append(f"**DESCRIPTION**: {h}")
        # now get all parameters
        out_param = None
        if pattern:
            params_info = config_dict.get(C.PARAM_KEY,{})
            for param_name,param_info in params_info.items():
                if not isinstance(param_info,dict):
                    continue
                out_param=self._report_param(param_name,param_info)
                if isinstance(out_param,list):
                    out.extend(out_param)
        else:
            out_param=self._report_param(config_name,config_dict,config_type)
            if isinstance(out_param,list):
                out.extend(out_param)
        return out

    def _report_param(self,param_name,param_dict,config_type:str=None):
        # TODO REFACTOR METHOD
        out=[]

        match config_type:
            case C.CMD_PARAM:
                out = ConfigReport._report_cmd_param(param_dict)
                return out
            case C.CMD_SUBPARSER:
                out = ConfigReport._report_cmd_subparser(param_dict)
                return out
            case C.CMD_MAP_KEY:
                out = self._report_cmd_map(param_dict)
                return out
            case C.CMD_INPUT_MAP:
                out = ConfigReport._report_cmd_input_map(param_dict)
                return out
            case C.CMD_INPUT_MAP_PATTERN:
                out = ConfigReport._report_cmd_input_map_pattern(param_dict)
                return out

        param_type = param_dict.get(C.TYPE)
        pt = " [`"+param_type+"`]" if param_type else ""
        help_s = param_dict.get(C.HELP)
        h = " ("+help_s+")" if help_s else ""
        reference = param_dict.get(C.REF_KEY)
        r = "[`refers to:"+reference+"`]: " if reference else ""
        out.append(f"* **`{param_name}`** "+r+pt+h+"  ")

        file = param_dict.get(C.FILE_KEY)
        f = f"  * `file: {file}`" if file is not None else None
        path = param_dict.get(C.PATH_KEY)
        p = f"  * `path: {path}`" if path is not None else None
        value = param_dict.get(C.VALUE)
        v = f"  * `value: {value}`" if value is not None else None
        resolved_path = param_dict.get(C.RESOLVED_PATH)
        resolved_file = param_dict.get(C.RESOLVED_FILE)
        resolved  = "[NO_RESOLVED_REF]"
        if resolved_path:
            resolved  = f"{resolved_path}"
        if resolved_file:
            resolved  = f"{resolved_file}"
        rp = f"  * `resolved`:``` {resolved}```"
        # get export value if specified
        export_type = param_dict.get(C.EXPORT)
        export = None
        if export_type:
            # return the resolved path
            match export_type:
                case C.PATH_KEY:
                    export = resolved_path
                case C.FILE_KEY:
                    export = resolved_file
                case C.VALUE:
                    export = value
        ex = f"  * `export to env: {export}`" if export is not None else None
        add_lines=[f,p,v,rp,ex]
        add_lines=[l for l in add_lines if l is not None]
        out.extend(add_lines)
        return out

    @staticmethod
    def _report_cmd_maps_sources(mappings:dict)->list:
        if not isinstance(mappings,list):
            return
        out = []
        for mapping in mappings:
            source_info = mapping.get(C.SOURCE,{})
            params = [C.TYPE,C.PARAM_KEY,C.KEY]
            values = [source_info.get(p,f"[No PARAM {p}]") for p in params]
            param = mapping.get(C.PARAM_KEY,"[NO_MAPPING_TO_PARAM]")
            # generate link
            config_path = "Config Path (not resolved)"
            if values[0] and values[1]:
                text = "Config Path "
                if values[2]:
                    text += " (resolved)"
                else:
                    text += " (not resolved)"
                config_path = f"[{text}](#{values[0]}-{values[1]})"
            s= f'  * {config_path} ```[{">".join(params)}]: [{">".join(values)}] => {param}``` (parser value)'
            out.append(s)
        return out

    @staticmethod
    def _report_cmd_input_map(param_dict):
        """ maps the input pattern """
        if not isinstance(param_dict,dict):
            return []
        out = []
        cmd_input_iter = iter(param_dict)
        try:
            while ( key := next(cmd_input_iter) ) is not None:
                info = param_dict[key]
                if not isinstance(info,dict):
                    continue
                help_s = info.get(C.HELP,"")
                if help_s:
                    help_s = f"({help_s})"
                out.append(f"* **CMD INPUT MAP** `{key}` {help_s}")
                mappings = info.get(C.MAP,[])
                mappings_out = ConfigReport._report_cmd_maps_sources(mappings)
                out.extend(mappings_out)
        except StopIteration:
            pass

        return out

    @staticmethod
    def _report_cmd_input_map_pattern(param_dict):
        """ reports input map """
        # TODO ADD REPORT SECTION
        if not isinstance(param_dict,dict):
            return []
        out = []
        cmd_input_iter = iter(param_dict)
        try:
            while ( key := next(cmd_input_iter) ) is not None:
                info = param_dict.get(key)
                if not isinstance(info,dict):
                    continue
                pass
                pattern = info.get(C.PATTERN_KEY)
                pattern_link = f"[Pattern](#{C.PATTERN_KEY}-{pattern}) "
                help_s = info.get(C.HELP,"")
                if help_s:
                    help_s = f"{help_s}"
                out.append(f"* **CMD INPUT MAP PATTERN** `{key}`  \n{pattern_link} `{pattern}`: {help_s}")
                mappings = info.get(C.MAP,[])
                mappings_out = ConfigReport._report_cmd_maps_sources(mappings)
                out.extend(mappings_out)

        except StopIteration:
            pass

        return out

    def _report_cmd_action_map(self,param_info:dict):
        """ get the input values from an action map """
        out = []
        for key,info in param_info.items():
            if not isinstance(info,dict):
                continue
            config_type = info.get(C.TYPE)
            config_key = info.get(C.KEY)
            config_link = f"[`{config_type}-{key}`](#{config_type.lower()}-{key.lower()})"
            k = f"* **OPTION** `{config_key}` (config type: {config_link})  "
            out.append(k)
            # try to get the configuration values
            # TODO CHANGE / VERRIFY
            config_element = self._config._config_resolver._get_config_element(config=config_type,config_name=config_key)
            help_info = config_element.get(C.HELP)
            h = f"{help_info}"  if help_info is not None else None
            out.append(h)
            config_list=[C.FILE_KEY,C.ACTION_KEY,C.PATH_KEY,C.RESOLVED_PATH,C.RESOLVED_FILE,C.EXPORT]
            out.extend(ConfigReport._report_render_params(config_list,config_element))
        return out

    def _report_cmd_map(self,param_dict):
        out = []
        for param,param_info in param_dict.items():
            if param == "map":
                map_type = param_info.get(C.TYPE)
                match map_type:
                    case C.PATTERN_KEY:
                        t = f"  * **MAPPING TYPE**: `{map_type}`" if map_type is not None else ""
                        cmd_param = param_info.get(C.CMD_PARAM)
                        if isinstance(cmd_param,str):
                            c =f"[`{cmd_param}`](#cmd_param-{cmd_param.lower()})"
                        pattern = param_info.get(C.PATTERN_KEY)
                        if isinstance(pattern,str):
                            p =f"[`{pattern}`](#pattern-{pattern.lower()})"
                        cp = f"  * **COMMAND LINE PROFILE** {c}" if cmd_param is not None else None
                        pp = f"  * **PATTERN**: {p}" if pattern is not None else None
                        params = [t,cp,pp]
                        params = [p for p in params if p is not None]
                        out.extend(params)
                    case C.ACTION_KEY:
                        params = self._report_cmd_action_map(param_info)
                        out.extend(params)
        return out

    @staticmethod
    def _report_cmd_param(param_dict):
        out = []
        params = ["param_short","param","default","help","metavar","choices","action"]
        for param,param_info in param_dict.items():
            if param=="help":
                continue
            if not isinstance(param_info,dict):
                continue
            cmd_params = {p:param_info.get(p) for p in params}

            help_s = cmd_params.get("help")
            help_s = f"{help_s}" if help_s is not None else "Not available"
            pl = cmd_params.get(C.PARAM_KEY)
            ps = cmd_params.get(C.key(C.PARSER_ATTRIBUTE.PARAM_SHORT),"")
            mv = cmd_params.get(C.key(C.PARSER_ATTRIBUTE.METAVAR),"")
            mv = f"{mv}" if mv is not None else ""
            dv = cmd_params.get(C.key(C.PARSER_ATTRIBUTE.DEFAULT),"")
            dv = f"(DEFAULT: {dv})" if dv is not None else ""
            out.append(f"* **`{param}`**: {help_s}  \n```\n   [-{ps}/--{pl}] {mv} {dv}\n```  ")
        return out

    @staticmethod
    def _report_cmd_subparser(param_dict,):
        out = []
        for _,param_info in param_dict.items():
            out_s = f"1. **`subparser`**: [{param_info}](#cmd_param-{param_info.lower()})"
            out.append(out_s)
        return out

    @staticmethod
    def _report_render_params(render_list:list,info:dict):
        """ renders parameters for report """
        out = []
        for k in render_list:
            v = info.get(k)
            if v is None:
                continue
            out_s = f"  * `{k}`: ```{v}```"
            out.append(out_s)
        return out

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

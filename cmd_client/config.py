""" Configuration Class """
import sys
import os
import logging
from datetime import datetime as DateTime
from enum import Enum
import tools.cmd_client.constants as C
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.parse_helper import ParseHelper
from tools.cmd_client.config_resolver import ConfigResolver

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
        self._config_resolver = ConfigResolver(self._config_dict)

    def get_config(self,config_key:Enum=None):
        """ gets the respective config area, should match to enum in CONFIG """
        try:
            key = C.CONFIG[config_key.name].name.lower()
            return self._config_dict.get(key,{})
        except (KeyError, AttributeError):
            logger.error(f"Config Key {config_key} doesn't match to CONFIG enums")
            return {}

    def get_cmd(self,parsed_args:dict)->str:
        """ receives the cmd commands as dict
            and attempts to construct
            an output command
        """
        cmd_params_key = self._argparser.params_template
        subparser_template = self._argparser.subparser_template
        # now get resolved values for the various configurations
        cmd_conmands = self._config_resolver.get_cmd_dict(cmd_params_key,parsed_args,
                                                        subparser_template)
        return cmd_conmands

    @property
    def argparser(self):
        """ return the argparser """
        return self._argparser

    @property
    def config_resolver(self):
        """ return config_resolver """
        return self._config_resolver

    def _get_report_param_types(self)->list:
        param_types = [C.PATTERN_KEY,
                        C.EXECUTABLE_KEY,
                        C.FILE_KEY,
                        C.PATH_KEY,
                        C.SCRIPT,
                        C.SCRIPT_BASH,
                        C.ENVIRONMENT_WIN,
                        C.ENVIRONMENT_BASH,
                        C.SHORTCUT,
                        C.CMD_PARAM,
                        C.CMD_SUBPARSER,
                        C.CMD_MAP_KEY
                        ]
        return param_types

    def _report_cmd_param(self,param_dict):
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

    def _report_cmd_subparser(self,param_dict,):
        out = []
        for _,param_info in param_dict.items():
            out_s = f"1. **`subparser`**: [{param_info}](#cmd_param-{param_info.lower()})"
            out.append(out_s)
        return out

    def _report_cmd_map(self,param_dict):
        out = []
        for param,param_info in param_dict.items():
            if param == "map":
            # out_s = f"1. **`subparser`**: [{param_info}](#cmd_param-{param_info.lower()})"
                map_type = param_info.get(C.TYPE)
                t = f"  * **MAPPING TYPE**: `{map_type}`" if map_type is not None else ""
                cmd_param = param_info.get(C.CMD_PARAM)
                c =f"[`{cmd_param}`](#cmd_param-{cmd_param.lower()})"
                pattern = param_info.get(C.PATTERN_KEY)
                p =f"[`{pattern}`](#pattern-{pattern.lower()})"
                cp = f"  * **COMMAND LINE PROFILE** {c}" if cmd_param is not None else None
                pp = f"  * **PATTERN**: {p}" if pattern is not None else None
        params = [t,cp,pp]
        params = [p for p in params if p is not None]
        out.extend(params)
        return out

    def _report_param(self,param_name,param_dict,config_type:str=None):
        out=[]

        match config_type:
            case C.CMD_PARAM:
                out = self._report_cmd_param(param_dict)
                return out
            case C.CMD_SUBPARSER:
                out = self._report_cmd_subparser(param_dict)
                return out
            case C.CMD_MAP_KEY:
                out = self._report_cmd_map(param_dict)
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
            resolved  = f"`{resolved_path}`"
        if resolved_file:
            resolved  = f"`{resolved_file}`"
        rp = f"  * `resolved`: `{resolved}`" if value else None
        export = param_dict.get(C.RESOLVED_PATH)
        ex = f"  * `export to env: {export}`" if export is not None else None
        add_lines=[f,p,v,rp,ex]
        add_lines=[l for l in add_lines if l is not None]
        out.extend(add_lines)
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

    def report(self):
        """ returns the config as report """
        param_types = self._get_report_param_types()
        out = []
        toc = []
        dt = DateTime.now().strftime('%Y-%m-%d %H:%M:%S')
        info = f"**`Configuration ({self._f_config}) / {dt}`**"
        for config_type in param_types:
            title = f"CONFIGURATION {config_type.upper()}"
            out.append(f"# {title}")
            toc_link="#"+title.replace(" ","-").lower()
            toc.append(f"* [{title}]({toc_link})")
            config_dict = self._config_resolver.get_config_element(config_type)
            for config_name, config_info in config_dict.items():
                toc_link = "#"+config_type.lower()+"-"+config_name.lower()
                toc.append(f"  * [{config_type.upper()} {config_name.lower()}]({toc_link})")
                config_out = self._report_config(config_type,config_name,config_info)
                out.extend(config_out)
                out.append("\n  _[TOC](#toc)_")
        out.append("----")
        out.append(info)
        out=["# TOC",*toc,*out]
        return out

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

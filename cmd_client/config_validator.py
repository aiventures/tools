""" Validates the cmd_client Config """
import sys
import os
import logging
from pathlib import Path
from datetime import datetime as DateTime

from tools.util.recurse_dict import DictParser
# from tools.util.tree import Tree
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.configpath import CONFIG_PATH, VALIDATION_REPORT
from tools.cmd_client import constants as C
from tools.cmd_client.enum_helper import EnumHelper

logger = logging.getLogger(__name__)

ROOT = "root"
KEY_PATH = "key_path"
VALUE = "value"
IS_PATH = "is_path"
IS_FILE = "is_file"
OS_OBJECT = "os_object"
RESOLVED_PATH = "resolved_path"
RESOLVED_FILE = "resolved_file"
REFERENCE = "REFERENCE"
CONFIG_TYPES = EnumHelper.keys(C.CONFIG,lower=True)
PATTERN_REF = "pattern_ref"
WARNING = "warning"
ACTIONS = EnumHelper.keys(C.ACTION,lower=True)
LINE_KEY = PersistenceHelper.LINE_KEY

class ConfigValidator():
    """ Validator Main Class  """
    def __init__(self,f_config:str,f_validation:str=None) -> None:
        """ Constructor """
        self._persistence = PersistenceHelper(f_config,f_validation)
        config = self._persistence.read(line_key=LINE_KEY)
        self._config_dict = DictParser(config)
        # get all configuration leafs
        self._config_leaves = {}
        self._analyze_tree()
        # we do two runs to apply resolved os objects
        for _ in range(2):
            logger.info("Resolve References")
            self._resolve_os_references()

    def _analyze_tree(self):
        """ analyze the configuration tree get all config values """
        config_tree = self.config_tree
        line = None
        # get all leaves
        leaf_ids = config_tree.get_leaves()
        for leaf_id in leaf_ids:
            # get the complete key path for each leaf
            key_list = config_tree.get_key_path(leaf_id)[1:]
            # skip the line attribute to be added
            if isinstance(key_list,list) and key_list[-1]==LINE_KEY:
                continue
            key_path = "/".join(key_list)
            value = self._config_dict.itemized_dict
            if value:
                for key in key_list:
                    value = value[key]
                    if isinstance(value,dict):
                        line = value.get(LINE_KEY)
            if value:
                self._config_leaves[key_path]={KEY_PATH:key_list,VALUE:value,LINE_KEY:line}
        logger.info(f"Processed Leaves in Config: {len(self._config_leaves)} elements")

    def check(self)->None:
        """ do overall check """
        self._check_os_references()
        self._check_patterns()
        self._check_subparsers()
        self._check_cmd_maps()
        self._check_input_maps()

    def get_config_element(self,*args,info:bool=False):
        """ returns the subtree element of the configuration
            returns value and optionally key path and line
        """
        out = self._config_dict.itemized_dict
        warning_s = None
        if not out:
            return
        out_args = []
        for arg in args:
            if not arg:
                break
            if isinstance(out,dict):
                out = out.get(arg)
                if out:
                    out_args.append(arg)
                    if isinstance(out,dict):
                        line = out.get(LINE_KEY)
                else:
                    break

        # do an additional check whether the number of elements is used
        if len(args) != len(out_args):
            warning_s = f"Couldn't find element in path [{str(args)}], only found [{str(out_args)}]"
            logger.info(warning_s)

        if not info:
            return out
        else:
            return {C.VALUE:out,LINE_KEY:line,KEY_PATH:out_args,WARNING:warning_s}

    def _resolve_os_reference(self,config_type:str,config_name:str)->dict:
        """ tries to resolve os reference from a config path """
        config_info = self.get_config_element(config_type,config_name)

        # get path
        path = config_info.get(C.PATH_KEY)
        os_path = config_info.get(C.RESOLVED_PATH)
        # skip it was resolved already
        if path and not os_path:
            # check if we have direct links to files
            is_os_path = os.path.isdir(path)
            # resolve any paths
            if is_os_path:
                os_path = os.path.abspath(path)
            # check if there is path in referenced area
            else:
                os_path = self.get_config_element(C.PATH_KEY,path,C.PATH_KEY)
                os_path_resolved = self.get_config_element(C.PATH_KEY,path,C.RESOLVED_PATH)
                # direct path
                if os_path and os.path.isdir(os_path):
                    is_os_path = True
                if not is_os_path and os_path_resolved and os.path.isdir(os_path_resolved):
                    is_os_path = True
                    os_path = os_path_resolved

            if is_os_path:
                logger.debug(f"Found path [{config_type}>{config_name}]: {os_path}")
                config_info[C.RESOLVED_PATH] = os.path.abspath(os_path)
            else:
                os_path = None
                logger.warning(f"Could not resolve path [{config_type}>{config_name}]")

        # get file
        file = config_info.get(C.FILE_KEY)
        os_file = config_info.get(C.RESOLVED_FILE)
        if file and not os_file:
            is_os_file = os.path.isfile(file)
            if is_os_file:
                os_file = os.path.abspath(file)
            else:
                # try to concatenate path and file
                if os_path:
                    os_file = os.path.join(os_path,file)
                    if os.path.isfile(os_file):
                        is_os_file = True
                if not is_os_file and config_type in CONFIG_TYPES:
                    os_file = self.get_config_element(C.FILE_KEY,file,C.FILE_KEY)
                    os_file_resolved = self.get_config_element(C.FILE_KEY,file,C.RESOLVED_PATH)
                    if os_file and os.path.isfile(os_file):
                        is_os_file = True
                    if not is_os_file and os_file_resolved and os.path.isfile(os_file_resolved):
                        is_os_file = True
                        os_file = os_file_resolved

            if is_os_file:
                logger.debug(f"Found file [{config_type}>{config_name}]: {os_file}")
                os_file = os.path.abspath(os_file)
                config_info[C.RESOLVED_FILE] = os_file
                if not os_path:
                    config_info[C.RESOLVED_PATH] = str(Path(os_file).parent)
            else:
                os_file = None
                logger.warning(f"Could not resolve file [{config_type}>{config_name}]")

    def _resolve_os_references(self)->None:
        """ resolves os references """
        config_types = [ C.ENVIRONMENT_WIN,C.ENVIRONMENT_BASH,
                         C.EXECUTABLE_KEY,C.PATH_KEY,C.FILE_KEY,C.SCRIPT_WIN,
                         C.SCRIPT_BASH,C.SHORTCUT]
        # check through config types
        for config_type in config_types:
            config_type_info = self.get_config_element(config_type)
            for config_name,config_info in config_type_info.items():
                if not isinstance(config_info,dict):
                    continue
                self._resolve_os_reference(config_type,config_name)

    def _check_subparsers(self)->None:
        """ checks integrity of subparser elements """
        subparser_dict = self.get_config_element(C.CMD_SUBPARSER)
        for subparser_key,subparser_info in subparser_dict.items():
            if subparser_key == LINE_KEY:
                continue
            for subcommand,cmdparam_template in subparser_info.items():
                if subcommand == LINE_KEY:
                    continue
                # get the param template
                cmdparam_template_info = self.get_config_element(C.CMD_PARAM,cmdparam_template)
                if not cmdparam_template_info:
                    leaf_key=[C.CMD_SUBPARSER,subparser_key,subcommand,cmdparam_template]
                    warning = f"cmd_subparser [{'>'.join(leaf_key)}], template {cmdparam_template} missing in {C.CMD_PARAM}"
                    logger.warning(warning)
                    self._add_config_leaf_warning(leaf_key,warning)
                else:
                    logger.info(f"Valid Map: Subcommand [{subcommand}] ({subparser_key}) => cmd_template [{cmdparam_template}]")

    def _check_cmd_map_pattern(self,map_key:str,cmd_map:dict)->None:
        """ checks the cmd_map pattern """
        # get the pattern
        warning = False
        pattern = cmd_map.get(C.PATTERN_KEY)
        pattern_params = self.get_config_element(C.PATTERN_KEY,pattern,C.PARAM_KEY)

        params_list = []
        if isinstance(pattern_params,dict):
            params_list = list(pattern_params.keys())
        # get the cmd params
        cmd_param_key = cmd_map.get(C.CMD_PARAM)
        cmd_params = self.get_config_element(C.CMD_PARAM,cmd_param_key)

        if not pattern_params:
            leaf_key = [C.CMD_MAP_KEY,map_key,C.MAP,C.PATTERN_KEY]
            warning_s = f"Invalid Pattern [{'>'.join(leaf_key)}]: {pattern}"
            self._add_config_leaf_warning(leaf_key,warning_s)
            warning = True

        if not cmd_params:
            leaf_key = [C.CMD_MAP_KEY,map_key,C.MAP,C.CMD_PARAM]
            warning_s = f"Invalid cmd_param [{'>'.join(leaf_key)}]: {cmd_param_key}"
            self._add_config_leaf_warning(leaf_key,warning_s)
            warning = True

        if warning:
            return

        for cmd_param,cmd_param_info in cmd_params.items():
            if not isinstance(cmd_param_info,dict):
                continue
            mapped_param_key = cmd_param_info.get(C.PARAM_KEY)
            if mapped_param_key in params_list:
                logger.info(f"cmd_map [{map_key}]: argparse [{mapped_param_key}] => [{pattern}-{mapped_param_key}] (pattern)")
            else:
                warning_s = f"cmd_param [{cmd_param_key}-{cmd_param}] does not map to pattern [{pattern}]"
                logger.warning(warning_s)
                leaf_key = [C.CMD_MAP_KEY,map_key,C.MAP,C.CMD_PARAM,mapped_param_key]
                self._add_config_leaf_warning(leaf_key,warning_s)

    def _check_cmd_map_action(self,map_key:str,cmd_map:dict)->None:
        """ checks the cmd_map action """
        # pattern = cmd_map.get(C.KEY)
        # cmd_param = cmd_map.get(C.CMD_PARAM)
        # parse_args = self.get_config_element(C.CMD_PARAM,cmd_param)
        for cmd_map_key,cmd_map_info in cmd_map.items():
            if not isinstance(cmd_map_info,dict):
                continue
            cmd_type = cmd_map_info.get(C.TYPE)
            cmd_key = cmd_map_info.get(C.KEY)
            action_info = self.get_config_element(cmd_type,cmd_key,{})
            action = action_info.get(C.ACTION_KEY)
            # leaf_key_action = [cmd_type,cmd_key,action]
            if not action in ACTIONS:
                leaf_key = [cmd_type,cmd_key,action]
                warning_s = f"Action [{'>'.join(leaf_key)}] is not a valid action (allowed: {ACTIONS}), check Constants"
                logger.warning(warning_s)
                self._add_config_leaf_warning(leaf_key,warning_s)
                leaf_key = [C.CMD_MAP_KEY,map_key,C.MAP,cmd_map_key]
                warning_s = f"CMD_MAP [{'>'.join(leaf_key)}], action is not valid, check Action"
                logger.warning(warning_s)
                self._add_config_leaf_warning(leaf_key,warning_s)
            if action:
                leaf_key = [C.CMD_MAP_KEY,map_key,C.MAP,cmd_map_key,C.ACTION_KEY]
                leaf_info = {C.VALUE:action}
                info_s = f"CMD_MAP, command [{cmd_map_key}] [{'>'.join(leaf_key)}], action resolved: [{action}]"
                logger.info(info_s)
                if action_info.get(C.RESOLVED_PATH):
                    leaf_info[C.RESOLVED_PATH] = action_info.get(C.RESOLVED_PATH)
                if action_info.get(C.RESOLVED_FILE):
                    leaf_info[C.RESOLVED_FILE] = action_info.get(C.RESOLVED_FILE)
                self._add_leaf(leaf_key,**leaf_info)
        pass

    def _check_cmd_maps(self)->None:
        """ checks the parse args to commands mapping  """
        cmd_map_dict = self.get_config_element(C.CMD_MAP_KEY)
        for cmd_map_key,cmd_map_info in cmd_map_dict.items():
            if cmd_map_key == LINE_KEY:
                continue
            cmd_map = cmd_map_info.get(C.MAP,{})
            map_type = cmd_map.get(C.TYPE)
            match map_type:
                case C.PATTERN_KEY:
                    self._check_cmd_map_pattern(cmd_map_key,cmd_map)
                case C.ACTION_KEY:
                    self._check_cmd_map_action(cmd_map_key,cmd_map)

    def _get_subcommands(self):
        """ gets all subcommands """
        subcommands = []
        subparsers = self.get_config_element(C.CMD_SUBPARSER)
        for subparser_config in subparsers.keys():
            if subparser_config == LINE_KEY:
                continue
            subparser_cmds = list(subparsers.get(subparser_config).keys())
            subcommands.extend(subparser_cmds)
        subcommands = [cmd for cmd in subcommands if cmd != LINE_KEY]
        return subcommands

    def _check_input_maps(self)->None:
        """ checks the input maps """
        subcommands = self._get_subcommands()
        subcommands.extend([C.DEFAULT,C.MAIN])
        cmd_input_map_dict = self.get_config_element(C.CMD_INPUT_MAP)
        for cmd_input_map_type,cmd_input_map_type_info in cmd_input_map_dict.items():
            if cmd_input_map_type == LINE_KEY:
                continue
            logger.info(f"Processing Input Map {cmd_input_map_type} (L{cmd_input_map_type_info.get(LINE_KEY)})")
            # check input map type
            if not cmd_input_map_type in subcommands:
                leaf_key=[C.CMD_INPUT_MAP,cmd_input_map_type]
                line = cmd_input_map_type_info.get(LINE_KEY)
                warning_s = f"Subcommand {cmd_input_map_type} (L{line})is not a valid type, check {C.CMD_SUBPARSER} section"
                logger.warning(warning_s)
                self._add_config_leaf_warning(leaf_key,warning_s)
                continue

            for cmd_input_map, cmd_input_map_info in cmd_input_map_type_info.items():
                if cmd_input_map == LINE_KEY or not isinstance(cmd_input_map_info,dict):
                    continue
                config_type = cmd_input_map_info.get(C.TYPE)
                mappings = cmd_input_map_info.get(C.MAP)
                pattern = cmd_input_map_info.get(C.PATTERN_KEY)
                for _,mapping_info in mappings.items():
                    source = mapping_info.get(C.SOURCE)
                    param = source.get(C.PARAM_KEY)
                    key = source.get(C.KEY)
                    argparse_param = mapping_info.get(C.PARAM_KEY)
                    leaf_key=[config_type,param,key]
                    source_info = self.get_config_element(*leaf_key,info=True)
                    warning_s = source_info.get(WARNING)
                    line = source_info.get(LINE_KEY)
                    p = [cmd_input_map_type,cmd_input_map,"(L"+line+")"]
                    s = f"{'>'.join(p)}: "
                    if warning_s:
                        logger.warning(s+warning_s)
                        self._add_config_leaf_warning(leaf_key,warning_s)
                    else:
                        info_s = f"CMD_INPUT_MAP {s}: ({'>'.join(leaf_key)}) => ARGPARSE PARAMETER [{argparse_param}]"
                        logger.info(info_s)
                    if pattern: # validate pattern
                        leaf_key_pattern = [C.PATTERN_KEY,pattern,C.PARAM_KEY,argparse_param]
                        pattern_info = self.get_config_element(*leaf_key_pattern,info=True)
                        line = pattern_info.get(LINE_KEY)
                        warning_s = pattern_info.get(WARNING)
                        if warning_s:
                            logger.warning(s+warning_s)
                            self._add_config_leaf_warning(leaf_key_pattern,warning_s)
                        else:
                            logger.info(f"Map {s}: Mapping pattern {pattern} to {leaf_key_pattern}: Argparse [{argparse_param}]")

    def _check_os_references(self)->None:
        """" checks for os references (either file or path objects) """
        config_types = [ C.ENVIRONMENT_WIN,C.ENVIRONMENT_BASH,
                         C.EXECUTABLE_KEY,C.PATH_KEY,C.FILE_KEY,C.SCRIPT_WIN,
                         C.SCRIPT_BASH,C.SHORTCUT]
        warnings=[]
        # now go through all leaves in the configuration check whether files were resolved
        for leaf,leaf_info in self._config_leaves.items():
            if leaf.endswith(LINE_KEY):
                continue
            config_type, config_name = leaf_info[KEY_PATH][:2]
            if not config_type in config_types:
                continue
            config_info = self.get_config_element(config_type,config_name)
            resolved_file = config_info.get(C.RESOLVED_FILE)
            resolved_path = config_info.get(C.RESOLVED_PATH)
            warning = False
            if leaf.endswith(C.FILE_KEY):
                leaf_info[C.RESOLVED_FILE]=resolved_file
                if not resolved_file:
                    warning = True
            elif leaf.endswith(C.PATH_KEY):
                leaf_info[C.RESOLVED_PATH]=resolved_path
                if not resolved_path:
                    warning = True
            # add warnings to leaf info
            if warning:
                leaf_key = leaf_info.get(KEY_PATH)
                warning = f"Could not resolve OS object [{'>'.join(leaf_key)}]"
                logger.warning(warning)
                warnings.append([leaf_key,warning])
        for warning in warnings:
            self._add_config_leaf_warning(warning[0],warning[1])


    def _add_config_leaf_warning(self,leaf_key:list,error:str)->None:
        """ adds an error to the leaf dict """
        leaf_info = self.get_config_element(*leaf_key,info=True)
        line = None
        if isinstance(leaf_info,dict):
            line = leaf_info.get(LINE_KEY)
        leaf_key.append(WARNING)
        key = "/".join(leaf_key)
        # line_number = self._get_line_number(leaf_key)
        error_leaf = self._config_leaves.get(key,{})
        error_leaf[KEY_PATH]=leaf_key
        error_leaf[WARNING]=error
        error_leaf[VALUE]=None
        error_leaf[LINE_KEY]=line
        self._config_leaves[key]=error_leaf

    def _add_leaf(self,leaf_key:list,**kwargs)->None:
        """ adds an error to the leaf dict """
        leaf_info = self.get_config_element(*leaf_key,info=True)
        line = None
        if isinstance(leaf_info,dict):
            line = leaf_info.get(LINE_KEY)
        key = "/".join(leaf_key)
        leaf = self._config_leaves.get(key,{})
        leaf[KEY_PATH]=leaf_key
        leaf[LINE_KEY]=line
        for kw_key,value in kwargs.items():
            leaf[kw_key] = value
        self._config_leaves[key]=leaf

    def _check_patterns(self)->None:
        """ checks pattern """
        # for leaf,leaf_info in self._config_leaves.items():
        config_info = self.get_config_element(C.PATTERN_KEY)
        for pattern_key,pattern_info in config_info.items():
            if not isinstance(pattern_info,dict):
                continue
            pattern = pattern_info.get(C.PATTERN_KEY)
            param_info = pattern_info.get(C.PARAM_KEY,{})
            for param,param_dict in param_info.items():
                if not isinstance(param_dict,dict):
                    continue
                param_type = param_dict.get(C.TYPE)
                leaf_warn = [C.PATTERN_KEY,pattern_key,C.PARAM_KEY,param]
                # check if param is in pattern
                if not f"[{param}]" in pattern:
                    warning = f"Pattern [{pattern_key}]: Parameter [{param}] not in pattern"
                    logger.warning(warning)
                    self._add_config_leaf_warning(leaf_warn,warning)
                # check if executable was resolved
                if param_type == C.EXECUTABLE_KEY:
                    executable = self.get_config_element(C.EXECUTABLE_KEY,param,C.RESOLVED_FILE)
                    if not executable:
                        warning=f"Pattern [{pattern_key}]: Executable [{param}] can not be resolved"
                        logger.warning(warning)
                        self._add_config_leaf_warning(leaf_warn,warning)
                    pass

    @property
    def config_tree(self):
        """ gets the config tree """
        return self._config_dict.tree

    def _report_get_objects(self)->dict:
        """ get objects as output data """

        out_dict = {WARNING:{},OS_OBJECT:{},C.VALUE:{}}

        def resolve_os_object(info:dict)->str:
            """ resolves item whether it is a foile object """
            file_object = None
            file_object = info.get(C.RESOLVED_FILE)
            if not file_object:
                file_object = info.get(C.RESOLVED_PATH)
            return file_object

        line = 1
        for leaf_id,leaf_info in self._config_leaves.items():
            if leaf_info.get(LINE_KEY):
                line = leaf_info.get(LINE_KEY)
            value = leaf_info.get(C.VALUE)
            title=f"**(L{line.zfill(3)})** `[{leaf_id}]`"
            os_object = resolve_os_object(leaf_info)
            warning = leaf_info.get(WARNING)
            if warning:
                info = f"* {title}: {warning}  "
                type = WARNING
            elif os_object:
                info = f"* {title}: {value} ({os_object})  "
                type = OS_OBJECT
            else:
                info = f"* {title}: {value}  "
                type  = C.VALUE
            info_dict = out_dict.get(type)
            info_dict[line]=info

        return out_dict

    def create_report(self,)->list:
        """ outputs report file lines """
        toc = []
        lines = []
        out = ["# TOC"]
        ref_toc="[TOC](#toc)"
        out_dict = self._report_get_objects()
        sections = {WARNING:"WARNINGS",OS_OBJECT:"OS OBJECTS",C.VALUE:"OTHER VALUES"}
        for section_id,section_title in sections.items():
            title = f"# {section_title}"
            lines.append(title)
            link = section_title.lower()
            link = "#"+link.replace(" ","-")
            toc.append(f"* [{section_title}]({link})")
            section_lines = out_dict.get(section_id,[])
            section_keys = sorted([int(i) for i in section_lines.keys()])
            for key in section_keys:
                line = section_lines.get(str(key))
                lines.append(line)
            lines.append(ref_toc)
            lines.append("----")
        out.extend(toc)
        out.extend(lines)
        out.append(f"CREATED: {DateTime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._persistence.save("\n".join(out))
        return out

if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    f_config = CONFIG_PATH
    f_validation = VALIDATION_REPORT
    validator = ConfigValidator(f_config,f_validation)
    validator.check()
    out = validator.create_report()
    pass

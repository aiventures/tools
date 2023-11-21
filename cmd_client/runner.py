""" bundling of File Transformer Properties for parsing """
import sys
import os
import logging
import json
import shlex
from pathlib import Path
from tools.cmd_client.config import Config
from tools.cmd_client.configpath import CONFIG_PATH, REPORT
import tools.cmd_client.constants as C
from tools.cmd_client.utils import Utils
from tools.cmd_client.cmd_runner import CmdRunner

logger = logging.getLogger(__name__)

class Runner():
    """ bundling of File Transformer Properties for parsing """
    DEFAULT_CONFIG = "config.json"

    """ Runs Command Line """

    def __init__(self,f_config:str=None,
                 params_template:str=None,
                 subparser_template:str=None,
                 default_params:list=None,**kwargs) -> None:
        """ Constructor """
        self._path = Path(__file__)
        self._cwd = os.getcwd()
        self._f_config = None
        # argparse handling
        self._read_config(f_config)
        # get the Configuration from a yaml file
        self._config = Config(self._f_config,params_template,
                              subparser_template,default_params,**kwargs)

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
        """ config getter method """
        return self._config

    @staticmethod
    def get_cmd_client(f_config:str=CONFIG_PATH):
        """ creates cmd client """
        # location of config file
        # copy the configpath_template, supply path and
        # set the path pointing to the param_config.yaml file
        f_config = f_config
        # get the argparseconfig from the yaml template file
        # main parser (as in yaml)
        main_config = "cmd_client_main"
        # sub parser configuration (as in yaml)
        subparser_config = "subparser_cmd_client"
        # add default parameters to parser configuration
        default_params = [ # C.DEFAULT_PARSER_ATTRIBUTES.ADD_TIMESTAMP,
                          # C.DEFAULT_PARSER_ATTRIBUTES.LOGLEVEL
                          ]
        # additional main attributes for the arg parser
        kwargs = { C.PARSER_ATTRIBUTE.DESCRIPTION.value: "Command Line Client",
                   C.PARSER_ATTRIBUTE.PROG.value: "COMMAND LINE CLI",
                   C.PARSER_ATTRIBUTE.EPILOG.value: "ONE CLI to bond them all ..."
                }
        runner = Runner(f_config,main_config, subparser_config,
                        default_params,**kwargs)
        return runner

    def log_results(self,action_dict:dict,cmd_dict:dict)->None:
        """ log the parsing results """
        logger.info("### ACTIONS")
        for action,action_info in action_dict.items():
            logger.info(f"*  [{action}]: {action_info}")
        logger.info("### COMMANDS")
        for cmd,cmd_info in cmd_dict.items():
            logger.info(f"*  [{cmd}]: {cmd_info}")   
    
    def transform_cmds(self,cmd_list):
        """ transforms the params for passing over to py_bat """
        out_list = []
        for cmd in cmd_list:
            cmd_s = cmd.replace('"'+C.PARAMS_MARKER,"")
            cmd_s = cmd_s.replace(C.PARAMS_MARKER+'"',"")
            pass
            out_list.append(cmd_s)
        return out_list

    def run_cmd(self,parsed_args,open_files:bool=False)->str:
        """ returns the os command """
        commands = self._config.get_cmd(parsed_args)
        cmd_dict = commands.get(C.PATTERN_KEY)
        action_dict = commands.get(C.ACTION_KEY,{})
        # move actions to action resolver
        if action_dict:
            num_actions = len(action_dict)
            logger.info(f"Retrieved ({num_actions}) Actions {list(action_dict.keys())}")
            action_dict = self._config.run_actions(action_dict,**parsed_args)
        else:
            logger.info("No actions")

        cmds = None
        if cmd_dict:
            num_cmds = len(cmd_dict)
            cmds = list(cmd_dict.values())
            logger.info(f"Retrieved ({num_cmds}) Commands {list(cmd_dict.keys())}")
            cmds = self.transform_cmds(cmds)
        else:
            logger.info("No commands Derived (actions were done before)")
        
        self.log_results(action_dict,cmd_dict)

        open_files = self._config.configuration.get(C.CONFIGURATION_OPEN_FILES,False)
        if open_files and action_dict:
            default_editor = self._config.get_configuration(C.CONFIGURATION_DEFAULT_EDITOR)
            files_created = action_dict.get(C.FILE_CREATED,{})
            Utils.open_files(default_editor,files_created)

        if isinstance(cmds,list):
            if len(cmds)>1:
                logger.warning("There's more than one command, check the settings")
            return cmds[0]

if __name__ == "__main__":
    # here's a list of collected commamnds for test driving
    # aleays use option -h / --help to display commands
    CMD_NPP = "npp -f xyz --line 10" # open notepadplusplus with a file defined in file>xyz
    CMD_VSCODE = "vs -f xyz -l 10 -pv cwd" # open vs code with the same file at line 10
    CMD_REPORT = "--cc_report" # create a configuration report
    CMD_NPP_TODO = "npp --todo -l 5" # open notepadplusplus with a fixed file defined in shortcut file
    CMD_NPP_TODO3 = "npp --todo3 -l 5" # open notepadplusplus with calling pattern with predefined values
    CMD_EXPORT_ENV = "--export_env" # export env params as file
    CMD_ACTION = "--action_param" # testing action resolver, set a breakpoint at action_resolver
    CMD_CREATE_REPORT = "--create_report" # default action to create a configuration report
    CMD_CREATE_ENV_BAT = "--export_env" # default action to create environment setup file
    CMD_TWOCMDS = "--export_env --create_report" # testing multiple commands
    CMD_TOTALCMD = 'tc --left cwd --right C:/10_Tools' # testing total commander, path shortcut is working
    CMD_TOTALCMD2 = 'tc ' # testing total commander with default
    CMD_DIFF = "diff -of f_test -nf f_test_new --path cwd" # VSCODE diff tool
    CMD_MERGE = "merge -lf f_test_new -rf f_test_different -bf f_test -tf f_test_merged" # VSCODE merge tool
    CMD_PY = 'py -m py_argparse_test -pp "__test xyz _p"' # check python launcher

    # TODO Pyhton
    # TODO PlantUml
    # Todo Markdown

    f_config = CONFIG_PATH
    #  pass over configuration file
    if len(sys.argv) <= 1:        
        # use one of the sample configs above
        test_cmd = CMD_CREATE_ENV_BAT
    else:
        print(f"RUNNING FROM COMMAND LINE (CONFIG FILE: {f_config})")
        test_cmd = None

    runner = Runner.get_cmd_client(f_config)

    # sample test all configurations
    argparser = runner.config.argparser

    if test_cmd:
        test_cmd = shlex.split(test_cmd,posix=False)
        parsed_args = argparser.parse_args(test_cmd)
    else:
        parsed_args = argparser.parse_args()
    loglevel = runner.config.configuration.get(C.CONFIGURATION_LOGLEVEL,logging.WARNING)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # show config in log
    logger.info(f"\n## Parser Configuration:\n {json.dumps(runner.config.configuration, indent=4)}")
    logger.info(f"\n## Config:\n {json.dumps(parsed_args, indent=4)}")
    logger.info(f"## Work Dir: {os.getcwd()}")

    if True or not test_cmd:
        cmd = runner.run_cmd(parsed_args)
        # run the command
        CmdRunner().run_cmd(cmd)

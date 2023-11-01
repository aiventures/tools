""" bundling of File Transformer Properties for parsing """
import sys
import os
import logging
import json
from pathlib import Path
from tools.cmd_client.config import Config
from tools.cmd_client.configpath import CONFIG_PATH, REPORT
import tools.cmd_client.constants as C
from tools.cmd_client.cmd_runner import CmdRunner
from tools.cmd_client.persistence_helper import PersistenceHelper

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
    def get_cmd_client():
        """ creates cmd client """
        # location of config file
        # copy the configpath_template, supply path and
        # set the path pointing to the param_config.yaml file
        f_config = CONFIG_PATH
        # get the argparseconfig from the yaml template file
        # main parser (as in yaml)
        main_config = "cmd_client_main"
        # sub parser configuration (as in yaml)
        subparser_config = "subparser_cmd_client"
        # add default parameters to parser configuration
        default_params = [ # C.DEFAULT_PARSER_ATTRIBUTES.ADD_TIMESTAMP,
                        C.DEFAULT_PARSER_ATTRIBUTES.LOGLEVEL]
        # additional main attributes for the arg parser
        kwargs = { C.PARSER_ATTRIBUTE.DESCRIPTION.value: "Command Line Client",
                C.PARSER_ATTRIBUTE.PROG.value: "COMMAND LINE CLI",
                C.PARSER_ATTRIBUTE.EPILOG.value: "ONE CLI to bond them all ..."
                }
        runner = Runner(f_config,main_config, subparser_config,
                        default_params,**kwargs)
        return runner

    def run_cmd(self,parsed_args)->str:
        """ returns the os command """
        commands = self._config.get_cmd(parsed_args)
        cmd_dict = commands.get(C.PATTERN_KEY)
        action_dict = commands.get(C.ACTION_KEY)
        if action_dict:
            num_actions = len(action_dict)            
            logger.info(f"Retrieved ({num_actions}) Actions {list(action_dict.keys())}")            
            actions = self._config.run_actions(action_dict,**parsed_args)
        else:
            logger.info("No actions")            

        cmds = None
        if cmd_dict:
            num_cmds = len(cmd_dict)
            cmds = list(cmd_dict.values())
            logger.info(f"Retrieved ({num_cmds}) Commands {list(cmd_dict.keys())}")
        else:
            logger.info("No commands Derived")        

        if isinstance(cmds,list):
            if len(cmds)>1:
                logger.warning("There's more than one command, check the settings")
            return cmds[0]
        


if __name__ == "__main__":
    runner = Runner.get_cmd_client()
    # sample test all configurations
    argparser = runner.config.argparser
    # here's a list of collected commamnds for test driving 
    # aleays use option -h / --help to display commands
    CMD_NPP = "npp -f xyz --line 10" # open notepadplusplus with a file defined in file>xyz
    CMD_VSCODE = "vs -f xyz -l 10" # open vs code with the same file at line 10
    CMD_REPORT = "--cc_report" # create a configuration report    
    CMD_NPP_TODO = "npp --todo -l 5" # open notepadplusplus with a fixed file defined in shortcut file
    CMD_NPP_TODO2 = "npp --todo2 -l 5" # open notepadplusplus with calling pattern with predefined values
    # use one of the sample configs above
    test_cmd = CMD_NPP_TODO2
    if test_cmd:
        parsed_args = argparser.parse_args(test_cmd.split())
    else:
        parsed_args = argparser.parse_args()
    loglevel = C.LOGLEVEL[parsed_args.get("loglevel","DEBUG").upper()].value

    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    # show config in log
    logger.info(f"\nConfig:\n {json.dumps(parsed_args, indent=4)}")

    if True:
        cmd = runner.run_cmd(parsed_args)
        logger.info(f"COMMAND: {cmd}")
        # run the command
        CmdRunner().run_cmd(cmd)

    pass

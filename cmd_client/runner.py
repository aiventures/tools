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
            self._config.run_actions(action_dict,**parsed_args)
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
    test_mode = True
    if test_mode:
        parsed_args_main = argparser.parse_args("-ps testparant".split())
        parsed_args_main = argparser.parse_args("--cc_report".split())
        parsed_args_subparser = argparser.parse_args("npp -f xyz".split())
        loglevel = C.LOGLEVEL[parsed_args_main.get("loglevel","DEBUG").upper()].value
        parsed_args = parsed_args_main
        # parsed_args = parsed_args_main
    else:
        parsed_args = argparser.parse_args()
        loglevel = C.LOGLEVEL[parsed_args.get("loglevel","DEBUG").upper()].value

    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    # show config in log
    if test_mode:
        logger.info(f"\nConfig (MAIN):\n {json.dumps(parsed_args_main, indent=4)}")
        logger.info(f"\nConfig (SUBCONFIG):\n {json.dumps(parsed_args_subparser, indent=4)}")
    else:
        logger.info(f"\nConfig:\n {json.dumps(parsed_args, indent=4)}")

    if True:
        cmd = runner.run_cmd(parsed_args)
        logger.info(f"COMMAND: {cmd}")
        # run the command
        CmdRunner().run_cmd(cmd)

    pass

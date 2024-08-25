""" Slim version of a CLI Client
    (not to confuse with the package )  """

import sys
import os
import re
# when doing tests add this to reference python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import logging
import shlex
import argparse
from util.config_env import ConfigEnv
from util.cmd_runner import CmdRunner
from util.const_local import F_CONFIG_ENV
from util.const_local import LOG_LEVEL

# list of exprected enviroment variables
CMD_CYGPATH = "CMD_CYGPATH" # executable to CYGPATH

# allowed actions
COMMAND_CONV_PATH = "p_conv"

# list of CYGPATH Transformations
CYGPATH_WIN2UNC = "w2u"
CYGPATH_WIN2DOS = "w2d"
CYGPATH_DOS2UNC = "d2u"
CYGPATH_UNC2WIN = "u2w"
CYGPATH_UNC2DOS = "u2d"

# param definitions
P_CONV_PATH = "path"
P_CONV_CONF = "conv"

logger = logging.getLogger(__name__)
config = ConfigEnv(F_CONFIG_ENV)

class PathConverter():
    """ converting paths into different path formats """
    def __init__(self) -> None:
        self.cmd_cygpath = config.get_ref(CMD_CYGPATH)
        if self.cmd_cygpath is None:
            logger.error(f"Couldn't find CMD_CYGPATH entry in [{F_CONFIG_ENV}], check Configuraiton JSON")
            return
        self.cmd_cygpath = '"'+self.cmd_cygpath+'"'

    def convert(self,args:dict) -> str:
        """ convert passed path """

        cygpath_params = {  CYGPATH_WIN2UNC : "--unix --absolute",
                            CYGPATH_WIN2DOS : "--dos --absolute",
                            CYGPATH_DOS2UNC : "--unix --absolute",
                            CYGPATH_UNC2WIN : "--windows --absolute",
                            CYGPATH_UNC2DOS : "--dos --absolute" }
        if self.cmd_cygpath is None:
            return
        _path = args.get(P_CONV_PATH,"CWD")
        if _path == "CWD" or _path ==".":
            _path = os.getcwd()
        if not _path[0] == '"':
            _path = '"'+_path+'"'
        _conv = args.get(P_CONV_CONF,CYGPATH_WIN2UNC)
        logger.debug(f"Converting [{_path}] ({_conv})")
        try:
            cmd_args = cygpath_params[_conv]
        except KeyError:
            logger.error(f"Error In Command, use one of the following {list(cygpath_params.keys())}")
            return
        cmd = f"{self.cmd_cygpath} {cmd_args} {_path}"
        cmd_runner = CmdRunner()
        cmd_runner.run_cmd(cmd)
        converted_path = cmd_runner.get_output()
        return '"'+converted_path+'"'

class CliClient():
    """ Command Line Client """
    def __init__(self,command_line=None) -> None:
        self._argparser = None
        self._args = {}
        self._parse_args(command_line)
        pass

    def _parse_args(self,command_line=None):
        """ Parse the args from the command line """

        # do not split in quoted file paths
        if isinstance(command_line,str):
            command_line=shlex.split(command_line)

        # create Main Parser
        parser = argparse.ArgumentParser(prog='cmd_client.py',
                                         description="Additional Commands for the Command Line",)
        parser.add_argument('--loglevel',"-ll", default="info",
                            help="Log Level (DEBUG,INFO,WARNING,ERROR)",
                            metavar='[loglevel]')

        # subparser to add path conversion
        subparsers = parser.add_subparsers(dest='command')
        p_conv = subparsers.add_parser(COMMAND_CONV_PATH, help='mutually convert paths (UNC,DOS,WIN)')
        p_conv.add_argument('--'+P_CONV_CONF,'-c', default="w2u", help='conversion (w2d,w2u,d2u,u2w,u2d)', metavar="[mode]")
        p_conv.add_argument('--'+P_CONV_PATH,'-p', default="CWD", help='convert win to unix', metavar="[path]" )

        args = parser.parse_args(command_line)
        # not necessarily needed
        self._argparser = parser
        # get config as dict
        self._args = vars(args)
        logger.debug(f"Parsed Args from command line:\n{self._args}")

        # parser.add_argument('--filter',"-f", default=config["filter"], help="Model Filter List [...], or use filter options ")
        # # flags activating options
        # parser.add_argument('--test',"-t", dest='test', action='store_true',help="Test using reference model")

    def run(self):
        """ Perform actions """
        out = None
        command = self._args.get("command")
        match command:
            case "p_conv": # constants not interpreted here
                out = PathConverter().convert(self._args)
                logger.debug(f"Converted Path to [{out}]")
        return out


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=LOG_LEVEL, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # args = parser.parse_args("group1 -foo myargvalue".split())
    # cli_client = CliClient("-ll debug")

    if False:
        # print(f"Passed ARGS {sys.argv[1:]}")
        cli_client = CliClient()
    else:
        # simulating the passed args
        # cli_client = CliClient('p_conv -c w2u')
        cmd_string = 'p_conv -p "C:\Program Files (x86)" -c w2u'
        # oscmd_shlex=shlex.split(cmd_string)
        cli_client = CliClient(cmd_string)
    out = cli_client.run()
    print(out)

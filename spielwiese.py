""" Spielwiese zum Ausprobieren """

import os
import re
import sys
#import glob
import re
from pathlib import Path
#import shutil
#from datetime import date
from pathlib import Path
#import shlex
#import subprocess
import json
import traceback
# import yaml
# from yaml import CLoader
import logging
from util.cmd_runner import CmdRunner
from util.config_env import ConfigEnv
from util.const_local import F_CONFIG_ENV,P_GIT

logger = logging.getLogger(__name__)

def test_cygwin():
    """ 11.8.2024  """
    cmd_cygpath = os.path.join(P_GIT,"usr","bin","cygpath.exe")
    cmd = "-d -a ."
    _runner = CmdRunner()
    _runner.run_cmd(cmd_cygpath+" "+cmd)
    last_output = _runner.get_output()
    pass

def test_config():
    """ 11.8.2024 """
    # https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
    # relative import
    # if starting directly in submodule, imports are not recognized
    # so you need to create a test program im root path
    # import os.path
    # import sys
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    # you need to define your own const_local with correct paths to the config file
    config = ConfigEnv(F_CONFIG_ENV)
    config.show()
    pass

def test_regex():
    """ 11.8.2024 testing regex """
    REGEX_BRACKETS = r"\[.+?\]"
    s = "[abc]fsdfdsd[def]"
    regex_found = re.findall(REGEX_BRACKETS,s)
    pass

def test_path():
    """ 25.8.2024 """
    p_current = Path(__file__).parent
    f = os.path.join(p_current,"sample_path","lorem_doc_root.md")
    f_path = Path(f)
    _stem = f_path.stem
    _suffix = f_path.suffix
    _absolute = f_path.absolute()
    _posix = f_path.as_posix()
    _uri = f_path.as_uri()
    _is_abs = f_path.is_absolute()
    _parent = f_path.parent
    _name = f_path.name
    _text = f_path.read_text(encoding="utf-8")
    pass



if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # test_cygwin()
    # test_config()
    # test_regex()
    test_path()
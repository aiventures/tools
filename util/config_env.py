""" Managing Configuration for a given command line """

import os
import sys
import re
# when doing tests add this to reference python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import logging
from util.persistence import Persistence
from util.colors import col
from util.const_local import F_CONFIG_ENV

logger = logging.getLogger(__name__)
# JSON keys
PATH = "p"
FILE = "f"
DESCRIPTION = "d"
GROUPS = "g"
REFERENCE = "ref"
CONFIG_KEYS = [PATH,FILE,DESCRIPTION,REFERENCE]
# if this is set in path, then the current path is used
PATH_CWD = "CWD"
# Key Markers
KEY_CMD = "CMD_"
KEY_FILE = "F_"
KEY_PATH = "P_"
KEY_TYPES = [KEY_CMD,KEY_FILE,KEY_PATH]

# REGEX EXPRESSIONS USED
# regex to find all strings envlosed n brackets
REGEX_BRACKETS = r"\[.+?\]"

class ConfigEnv():
    """ Configuration of Command Line Environment  """

    def __init__(self,f_config:str=None) -> None:
        """ constructor """
        self._f_config = f_config
        self._config = Persistence.read_json(self._f_config)
        self._config_keys = list(self._config.keys())
        if not self._config:
            self._config = {}
        self._validate()
        pass

    def _resolve_path_ref(self,p_ref:str,key:str):
        """ resolves the path references """
        _path_resolved = p_ref
        if _path_resolved is None:
            return _path_resolved

        # path is current directory
        if _path_resolved == PATH_CWD: # use current path as directory
            _path_resolved = os.getcwd()
            return _path_resolved

        # plain and valid path
        if os.path.isdir(_path_resolved):
            return _path_resolved

        path_key = None
        # check if there are multiple replacements
        regex_subpaths = re.findall(REGEX_BRACKETS,_path_resolved)
        if len(regex_subpaths) == 1:
            path_key = regex_subpaths[0][1:-1]
        # check if there is a single key reference
        elif _path_resolved in self._config_keys:
            path_key = _path_resolved

        if path_key:
            _path_ref = self._config.get(path_key,{}).get(REFERENCE)
            if len(regex_subpaths) == 1:
                _path_ref = p_ref.replace(regex_subpaths[0],_path_ref)
            if os.path.isdir(_path_ref):
                _path_resolved = _path_ref


            else:
                logger.warning(f"Resolved path [{_path_ref}] for key [{key}] is invalid")
            return _path_resolved

    def _validate(self) -> None:
        """ validates the configuration and creates references """
        _config = self._config
        logger.debug(f"Configuration ({self._f_config}) contains [len({_config})] items")
        for key, config in _config.items():
            config[REFERENCE] = None
            # try to get a valid file directly
            _file = config.get(FILE,"")
            if os.path.isfile(_file):
                config[REFERENCE] = _file
                logger.debug(f"Config [{key}]: Valid File Reference")
                continue

            # try to get a path reference
            _path = self._resolve_path_ref(config.get(PATH),key)

            if not _path:
                logger.warning(f"Path is not set for key [{key}]")
                continue

            # check wheteher we need to set a reference for a path or a file
            if key.startswith(KEY_PATH):
                config[REFERENCE] = _path
                continue

            # now check for a valid file
            _fileref = os.path.join(_path,_file)
            if not os.path.isfile(_fileref):
                logger.warning(f"File Path [{_fileref}] is invalid for key [{key}]")
            else:
                config[REFERENCE] = _fileref

    def get_ref(self,key:str)->str:
        """ returns the constructed reference from Configuration """
        _ref = self._config.get(key,{}).get(REFERENCE)
        if _ref is None:
            logger.warning(f"Key [{key}] is invalid")
        return _ref

    def show(self)->None:
        """ displays the config  """
        print(col(f"\n###### CONFIGURATION [{self._f_config}]\n","C_T"))
        _list = col("    *","C_TX")
        n = 1
        for key,config in self._config.items():
            _num = col(f"[{str(n).zfill(3)}] ","C_LN")
            _key = col(f"{key:<20} ","C_KY")
            _description = col(f"[{config.get(DESCRIPTION,'NO DESCRIPTION')}]","C_TX")
            _description = f"{_description:<60}"
            _ref = config.get(REFERENCE)
            if _ref:
                _ref = col("("+_ref+")","C_F")
            else:
                _ref = col("INVALID","C_ERR")
            print(_num+_key+_description+_ref)
            n+=1

if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    config = ConfigEnv(F_CONFIG_ENV)
    config.show()


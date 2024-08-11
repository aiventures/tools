""" Managing Configuration for a given command line """

import os
import logging
from util.persistence import Persistence
from util.colors import col

logger = logging.getLogger(__name__)
# JSON keys
PATH = "p"
FILE = "f"
DESCRIPTION = "d"
REFERENCE = "ref"
CONFIG_KEYS = [PATH,FILE,DESCRIPTION,REFERENCE]
# if this is set in path, then the current path is used
PATH_CWD = "CWD"
# Key Markers
KEY_CMD = "CMD_"
KEY_FILE = "F_"
KEY_PATH = "P_"
KEY_TYPES = [KEY_CMD,KEY_FILE,KEY_PATH]

class ConfigEnv():
    """ Configuration of Command Line Environment  """

    def __init__(self,f_config:str=None) -> None:
        """ constructor """
        self._f_config = f_config
        self._config = Persistence.read_json(self._f_config)
        if not self._config:
            self._config = {}
        self._validate()

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
            _path_ref = config.get(PATH)
            # special cases
            if _path_ref == PATH_CWD: # use current path as directory
                _path_ref = os.getcwd()

            if not _path_ref:
                logger.warning(f"Path is not set for key [{key}]")
                continue

            # try to dereference path
            if _path_ref.startswith(KEY_PATH):
                _path = _config.get(_path_ref,{}).get(PATH)
                if _path is None:
                    logger.warning(f"Couldn't resolve path key [{_path_ref}] for key [{key}]")
                    continue
            else:
                _path = _path_ref

            if not os.path.isdir(_path):
                logger.warning(f"Path [{_path}] is invalid for key [{key}]")
                continue
            else:
                # it's a path
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
            _num = col(f"   [{str(n).zfill(3)}] ","C_LN")
            _key = col(f"{key:<15} ","C_KY")
            _description = col(f"[{config.get(DESCRIPTION,'NO DESCRIPTION')}]","C_TX")
            _description = f"{_description:<60}"
            _ref = config.get(REFERENCE)
            if _ref:
                _ref = col("("+_ref+")","C_F")
            else:
                _ref = col("INVALID","C_ERR")
            print(_num+_key+_description+_ref)
            n+=1
            













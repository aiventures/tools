""" Configuration Class """
import sys
import os
import logging
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

    @property
    def argparser(self):
        """ return the argparser """
        return self._argparser
    
    @property
    def config_resolver(self):
        """ return config_resolver """
        return self._config_resolver

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

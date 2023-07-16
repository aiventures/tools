""" simple python lib to perform some tasks for batch files """
import sys
import argparse
import os
import logging

logger = logging.getLogger(__name__)

class BatchUtil():
    """ a simple batch to python interface taking away some pains in batch files """

    @staticmethod
    def read_file(p_file:str)->list:
        """ reading UTF8 txt File """
        lines = []
        try:
            with open(p_file,encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    lines.append(line)
        except Exception as e:
            logger.error(f"Exception reading file {p_file}, Exception {e}")
        return lines

    @staticmethod
    def save_file(p_file:str,data:str):
        """ save data to a UTF8 file """
        with open(p_file, 'w', encoding="utf-8") as f:
            try:
                f.write(data)
                logger.info(f"Data saved to {f.name}")
            except Exception as e:
                logger.error(f"Exception saving file {f}, Exception {e}")

    def __init__(self) -> None:
        p_self = os.path.normpath(os.path.dirname(__file__))
        p_parts = p_self.split(os.sep)
        self._p_self = p_self
        logger.debug(f"Path of python file {p_self}")
        
        # replace the last path with config and check whether this path exists
        p_config = p_self.replace(p_parts[-1:][0],"config")
        # get the root path
        self._p_root=None
        if os.path.isdir(p_config) and p_config!=p_self:
            logger.debug(f"Found Config Folder {p_config}")
            p_root = p_self.replace(p_parts[-1:][0],"")
            self._p_root=p_root            
        else:
            logger.error(f"There should be a config folder {p_config}, create it")
            p_config = None
        self._p_config = p_config


    def set_config(self,f_config):
        """ try to parse config file and create config files """
        logger.debug(f"Configure Parameters from {f_config}")
        if not os.path.isfile(f_config):
            logger.warning(f"f_config {f_config} is not a valid file can't process variables")
            return
        
        if not self._p_config:
            logger.warningf(f"There should be a config subfolder in folder {self._p_self}, create it")
            return
        
        lines = BatchUtil.read_file(f_config)
        p_cwd=os.getcwd()
        os.chdir(self._p_config)
        logger.info(f"Writing config to {self._p_config}")
        for line in lines:
            key_values=line.split("=")
            if not len(key_values)==2:
                continue
            key,value=key_values[0],key_values[1]
            logger.info(f"* {key} [{value}]")
            BatchUtil.save_file(key,value)

        os.chdir(p_cwd)

    def get_env(self,name):
        """ displays environment variable in log """
        logger.info(f"ENV {name}: [{os.getenv(name)}]")
    
    def open_venv_mult(self,f_venv_list:str=None):
        """ opens multiple virtual environemts from list """

        # read the venv list
        if not os.path.isfile(f_venv_list):
            logger.error(f"Passed file name {f_venv_list} is not a file, pls check")
            return
        
        venv_list = BatchUtil.read_file(f_venv_list)

        CMD_OPEN_VENV="start venv_activate.bat _venv_"
        os.chdir(self._p_root)

        for venv in venv_list:
            logger.info(f"Opening VENV {venv}")
            cmd_open_venv = CMD_OPEN_VENV.replace("_venv_",venv)
            os.system(cmd_open_venv)

if __name__ == "__main__":
    loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")

    batch_util = BatchUtil()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',"-c", default=None, help="creates env params from config file")
    parser.add_argument('--env',"-e", default=None, help="display env variable from environment")
    parser.add_argument('--venv_list',"-v", default=None, help="file name containing list of venvs to be opened")

    args = parser.parse_args()
    f_config=args.config
    env_name=args.env
    f_venv_list=args.venv_list
   
    # set up configuration file from config.txt
    if f_config:
        batch_util.set_config(f_config)

    # getting the setting from environment 
    if env_name:
        batch_util.get_env(env_name)
    
    if f_venv_list:
        batch_util.open_venv_mult(f_venv_list)

    sys.exit(0)

# do the other stuff
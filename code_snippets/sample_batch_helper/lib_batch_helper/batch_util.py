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
        self._work_dir=None
        self._venv_dir=None
        # read any existing config
        _ = self._read_config()

    def _read_config(self):
        """ reads config from config folder """
        config_out={}
        if not self._p_config:
            logger.warning(f"No config path found")
            return
        logger.info(f"Reading Configuration from [{self._p_config}]")
        for subpath_s,_,files in os.walk(self._p_config):
            for f in files:
                config=BatchUtil.read_file(os.path.join(subpath_s,f))
                if len(config)==0:
                    continue
                value=config[0]
                config_out[f]=value
                logger.debug(f"KEY {f} [{value}]")
                if f=="MY_WORK_DIR":
                    self._work_dir=value
                elif f== "MY_VENV_DIR":
                    self._venv_dir=value
        return config_out

    def _get_repo_list(self):
        """ reads the list of top level directories from repo """
        repo_list=[]
        if not self._work_dir:
            logger.error( ("Couldn't find Variable MY_WORK_DIR in configuration,"
                           " check config folder or reread configuration"))
            return

        for subpath_s,directories,_ in os.walk(self._work_dir):
            # ignore subfolder
            if not subpath_s == self._work_dir:
                break

            for directory in directories:
                # check if there is a .git subfolder indicating it's a repo
                fp_git=os.path.join(self._work_dir,directory,".git")
                if not os.path.isdir(fp_git):
                    logger.debug(f"SKIP {directory} (no git folder)")
                    continue
                logger.debug(f"ADD REPO {directory}")
                repo_list.append(directory)
        return repo_list

    def _get_venv_list(self):
        """ reads the list of top level directories from venv folder """
        venv_list=[]
        if not self._venv_dir:
            logger.error( ("Couldn't find Variable MY_VENV_DIR in configuration,"
                           " check config folder or reread configuration"))
            return

        for subpath_s,directories,_ in os.walk(self._venv_dir):
            # ignore subfolders
            if not subpath_s == self._venv_dir:
                break

            for directory in directories:
                # check if there is a scripts subfolder indicating it's a repo
                fp_scripts=os.path.join(self._venv_dir,directory,"Scripts")
                if not os.path.isdir(fp_scripts):
                    logger.debug(f"SKIP {directory} (no scripts folder)")
                    continue
                logger.debug(f"ADD VENV {directory}")
                venv_list.append(directory)
        return venv_list

    def check_repo_venvs(self):
        """ analyzes whether repo has a venv of its own (VENV with same name as repo exists) """
        logger.info("Check for Venvs of valid repos")
        venv_list = self._get_venv_list()
        repo_list = self._get_repo_list()
        has_venv=[]
        no_venv=[]
        for repo in repo_list:
            if repo in venv_list:
                has_venv.append(repo)
                logger.debug(f"Repo {repo} has a VENV")
            else:
                no_venv.append(repo)
                logger.debug(f"Repo {repo} has NO VENV")
        analyze_dict =  { "VENV":has_venv,"NO_VENV":no_venv}
        logger.info(analyze_dict)
        return analyze_dict

    def set_config(self,f_config):
        """ try to parse config file and create config files """
        logger.debug(f"Configure Parameters from {f_config}")
        if not os.path.isfile(f_config):
            logger.warning(f"f_config {f_config} is not a valid file can't process variables")
            return

        if not self._p_config:
            logger.warning(f"There should be a config subfolder in folder {self._p_self}, create it")
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
    parser.add_argument('--venvs_analyze',"-a", dest='venvs_analyze', action='store_true', help="Output List of missing VENVs for valid REPOS")
    parser.set_defaults(venvs_analyze=False)

    args = parser.parse_args()
    f_config=args.config
    env_name=args.env
    f_venv_list=args.venv_list
    venvs_analyze=args.venvs_analyze
    venvs_analyze=True
    
    # set up configuration file from config.txt
    if f_config:
        batch_util.set_config(f_config)

    # getting the setting from environment
    if env_name:
        batch_util.get_env(env_name)

    # analyze venvs
    if venvs_analyze:
        analyze_dict = batch_util.check_repo_venvs()

    # open multiple batch windows each with its own venv
    if f_venv_list:
        batch_util.open_venv_mult(f_venv_list)

    sys.exit(0)

""" loading python modules programmatically can be used for inspect """

import sys
import logging
import os
from pathlib import Path
from importlib import util as import_util
from os import walk

logger = logging.getLogger(__name__)

class ModuleLoader():
    def __init__(self,p_root) -> None:
        if os.path.isdir(p_root):
            self._p_root =  Path(os.path.abspath(p_root))
            logger.info(f"{p_root} initialized")
        else:
            logger.error(f"{p_root} is not a valid path, check")
            return
        self._module_paths={}
        self._walk_paths()
        self._loaded_modules=[]
        self._load_modules()        

    def _walk_paths(self):
        """ iterate through directories of root path and check for any module paths  """
        module_paths={}
        for subpath,_,files in os.walk(self._p_root):
            logger.debug(f"Walk path {subpath}")

            module_dict={}
            is_package = False
            for f in files:
                f_path = Path(f)
                if f_path.suffix[1:] == "py":
                    if not f_path.stem == "__init__":
                        module_dict[ f_path.stem]=f_path
                        logger.debug(f"found python file {f}")

                if f == "__init__.py":
                    is_package = True
                    logger.debug(f"found module path {subpath}")

            if is_package:
                module_paths[subpath] = module_dict
        self._module_paths = module_paths

    def _load_modules(self):
        """ load modules from module paths """
        for package_path,files in self._module_paths.items():
            p_package = Path(package_path)
            package_parts = p_package.parts
            # get path elements relative to root
            main_package = ".".join(package_parts[len(self._p_root.parts):])
            logger.info(f"Process folder {package_path} as package [{main_package}]")

            for module,module_file_name in files.items():
                p_module = Path.joinpath(p_package,module_file_name)
                module_name = main_package+"."+module
                logger.info(f"Loading module {module_name}")
                spec = import_util.spec_from_file_location(module_name, p_module)
                import_module = import_util.module_from_spec(spec)
                sys.modules[module_name] = import_module
                spec.loader.exec_module(import_module)
                self._loaded_modules.append(module_name)
        logger.info(f"Loaded Modules {self._loaded_modules}")

if __name__ == "__main__":
    loglevel=logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")
    # root path / set path to  path of this executable so that demo modules are loaded 
    root_path = Path(__file__).parent
    module_loader = ModuleLoader(root_path)
    pass



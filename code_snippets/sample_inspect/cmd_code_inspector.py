""" command line version for the uml code inspector """

import sys
import argparse
from pathlib import Path
import os
import logging
from enum import Enum
from code_inspector import ObjectModelGenerator
from code_inspector import ModelFilter
from code_inspector import ObjectModel
from code_inspector import PlantUMLRenderer
from tools import file_module as fm

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """ loglevel handling """
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    @staticmethod
    def get(level:str)->int:
        """ returns the integer loglevel with a default level of info"""
        if not level:
            level = "INFO"
        try:
            level = LogLevel[level.upper()].value
        except KeyError:
            level = LogLevel["INFO"].value
        return level

class Config(Enum):
    """ some Configurations """
    # Default Configuration
    DEFAULT = { "path":".",                 # model path
                "loglevel":None,            # log level INFO
                "filter":None,              # No Filter
                "test":False,               # Test mode (i)
                "component_diagram":False,  # Render Component Diagram
                "model_instance":False,     # Render Instanicated Models
                "no_class_diagram":False,   # Render Class Diagram, default active
                "no_plant_uml":False,       # Render PLantuml files as image, default active
                "no_total_commander":False, # Open Total Commander, default active
                "no_images":False,          # OPen images with viewer, default active
               }

    # Configure render all models
    ALL_MODELS = { "component_diagram":True,
                   "no_class_diagram":False, }

    # Display Filter: only overview
    FILTER_INNER = ModelFilter.FILTER_INNER
    # Display Filter: only package module without systems packages
    FILTER_SYS_MODULE = ModelFilter.FILTER_SYS_MODULE
    # Display Filter: only public
    FILTER_INTERNAL = ModelFilter.FILTER_INTERNAL

    @staticmethod
    def configure(out_dict,configuration:str):
        """ change parameter sets """
        try:
            config = Config[configuration]
            config_name = config.name
            config_dict = config.value
            config_keys = list(config_dict.keys())
            for k in out_dict.keys():
                if k in config_keys:
                    out_dict[k]=config_dict[k]
        except KeyError:
            logger.error(f"Configuration {configuration} unknown check settings")
            return
        logger.info(f"CONFIGURATION [{config_name}]: {out_dict}")
        return out_dict

    @staticmethod
    def add_filter(out_dict,filter:str):
        """ add filter to configuration """
        try:
            filter = Config[filter.upper()].value
        except:
            logger.error(f"Filter {filter} unknown check settings")
            return
        filter_list = out_dict.get("filter")
        if filter_list is None:
            filter_list = []
        if not filter in filter_list:
            filter_list.append(filter)
            out_dict["filter"]=filter_list
        return out_dict

def run(args_dict):
    """ running the uml model generator """
    logger.debug("start")

    cwd = os.getcwd()

    # set predefined configurations
    if args_dict.get("config_all"):
        args_dict = Config.configure(args_dict,Config.ALL_MODELS.name)

    # add filters
    if args_dict.get("filter_sys") is True:
        Config.add_filter(args_dict,Config.FILTER_SYS_MODULE.value)
    if args_dict.get("filter_inner") is True:
        Config.add_filter(args_dict,Config.FILTER_INNER.value)
    if args_dict.get("filter_internal") is True:
        Config.add_filter(args_dict,Config.FILTER_INTERNAL.value)

    # get individual params from input, overwrite any existing defaults and configs
    p = args_dict.get("path")
    test_model = args_dict.get("test",False)
    component_diagram = args_dict.get("component_diagram",False)
    class_diagram = not args_dict.get("no_class_diagram",False)
    model_instance = args_dict.get("mdoel_instance",False)
    model_filter =  args_dict.get("filter",None)
    plant_uml =  not args_dict.get("no_plant_uml",False)
    total_commander =  not args_dict.get("no_total_commander",False)
    open_images =  not args_dict.get("no_images",False)
    log_level =  args_dict.get("loglevel")

    logger.debug(f"start, use path {p}")

    if os.path.isdir(p):
        p=Path(p).absolute()
        logger.info(f"Using Path {p}")
    else:
        logger.info(f"{p} is not a valid path")
        sys.exit()

    # this will load the sample modules in this path
    if test_model:
        root_path = Path(__file__).parent
    else:
        root_path = p

    if model_filter:
        filters = list(ModelFilter.FILTER_DICT.keys())
        logger.debug(f"Filters allowed: {filters}")
        validated_model_filter = [f.lower() for f in model_filter if f in filters]
        logger.debug(f"Filters used: {validated_model_filter}")
    else:
        validated_model_filter = None

    # render the model as plantuml: simple package diagram and class diagram
    om = ObjectModel(root_path,model_instance)

    uml_renderer = PlantUMLRenderer(om)
    uml_renderer.add_model_filter(validated_model_filter)

    os.chdir(root_path)

    if component_diagram:
        uml_component_s = uml_renderer.render_component_diagram()
        f_component = "uml_component.plantuml"
        fm.save_txt_file(f_component,uml_component_s)

    if class_diagram:
        uml_class_s = uml_renderer.render_class_diagram()
        f_class = "uml_class.plantuml"
        fm.save_txt_file(f_class,uml_class_s)

    if plant_uml:
        os.system("call plantuml.bat")

    if open_images and component_diagram:
        os.system("start uml_component.png")

    if open_images and class_diagram:
        os.system("start uml_class.png")

    if total_commander:
        os.system("call tc.bat")

    print("##### Execution Summary")
    print(f"      Model source: {str(root_path)=}, {test_model=}")
    print(f"      Model types: {component_diagram=}, {class_diagram=}")
    print(f"      Model filters: {validated_model_filter}")
    print(f"      Generate Images: {plant_uml=}, {open_images=}")
    print(f"      Open Total Commander: {total_commander=}")
    print(f"      LOG LEVEL ({log_level})")
    print("##### Generated IMAGE FILES (uml*.png)")
    os.system("dir /b uml*.png")
    os.chdir(cwd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # default config
    config = Config.DEFAULT.value
    # variables
    parser.add_argument("--path","-p",default=config["path"],help="StartPath",metavar='File Path')
    parser.add_argument('--loglevel',"-l", default=config["loglevel"], help="Log Level")
    parser.add_argument('--filter',"-f", default=config["filter"], help="Model Filter List")
    # flags activating options
    parser.add_argument('--test',"-t", dest='test', action='store_true',help="Test using reference model")
    parser.add_argument('--component_diagram',"-o", dest='component_diagram', action='store_true',help="Create Component Diagram")
    parser.add_argument('--model_instance',"-m", dest='model_instance', action='store_true',help="Try to create model instance (generate instance attributes)")
    parser.set_defaults(test=config["test"])
    parser.set_defaults(component_diagram=config["component_diagram"])
    parser.set_defaults(model_instance=config["model_instance"])
    # flags deactivating options
    parser.add_argument('--no_class_diagram',"-nc", dest='no_class_diagram', action='store_true',help="Do not Create Class Diagram")
    parser.add_argument('--no_plant_uml',"-nu", dest='no_plant_uml', action='store_true',help="Do not Create PLantUML diagram images ./bat/plantuml.bat")
    parser.add_argument('--no_total_commander',"-nt", dest='no_total_commander', action='store_true',help="Do not Open Total Commander ./bat/tc.bat")
    parser.add_argument('--no_images',"-i", dest='no_images', action='store_true',help="Open Images (Default Image Viewer)")
    parser.set_defaults(no_class_diagram=config["no_class_diagram"])
    parser.set_defaults(no_images=config["no_images"])
    parser.set_defaults(no_plant_uml=config["no_plant_uml"])
    parser.set_defaults(no_total_commander=config["no_total_commander"])
    # some default configurations
    parser.add_argument('--config_all',"-ca", dest='config_all', action='store_true',help="Create all diagram types")
    parser.set_defaults(config_all=False)
    # filters
    parser.add_argument('--filter_sys',"-fs", dest='filter_sys', action='store_true',help="Filter all sys modules (not part of the package)")
    parser.add_argument('--filter_inner',"-fi", dest='filter_inner', action='store_true',help="Filter protected and privated objects")
    parser.add_argument('--filter_internal',"-ft", dest='filter_internal', action='store_true',help="Filter all inner objects (methods and attributes)")
    parser.set_defaults(filter_sys=False)
    parser.set_defaults(filter_inner=False)
    parser.set_defaults(filter_internal=False)

    args = parser.parse_args()
    args_dict = {k:v for k,v in args._get_kwargs()}

    loglevel = LogLevel.get(args.loglevel)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    logger.info(f"Arguments: {args}")
    run(args_dict)

""" command line version for the uml code inspector """

import sys
import argparse
from pathlib import Path
import os
import logging
from code_inspector import ObjectModelGenerator
from code_inspector import ModelFilter
from code_inspector import PlantUMLRenderer
from tools import file_module as fm

logger = logging.getLogger(__name__)

def run(args_dict):
    """ running the uml model generator """
    logger.debug("start")

    cwd = os.getcwd()
    om = ObjectModelGenerator()

    p = args_dict.get("path")
    test_model = args_dict.get("test",False)
    component_diagram = args_dict.get("component_diagram",False)
    class_diagram = args_dict.get("class_diagram",False)
    model_filter =  args_dict.get("filter",None)
    plant_uml =  args_dict.get("plant_uml",True)
    total_commander =  args_dict.get("total_commander",True)
    open_images =  args_dict.get("open_images",True)

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
        validated_model_filter = [f for f in model_filter if f in filters]
        logger.debug(f"Filters used: {validated_model_filter}")
    else:
        validated_model_filter = None

    # render the model as plantuml: simple package diagram and class diagram
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
    print(f"      Model source: {root_path=}, {test_model=}")
    print(f"      Model types: {component_diagram=}, {class_diagram=}")
    print(f"      Generate Images: {plant_uml=}, {open_images=}")
    print(f"      Open Total Commander: {total_commander=}")
    print("##### Generated IMAGE FILES (uml*.png)")
    os.system("dir /b uml*.png")
    os.chdir(cwd)
    pass

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    parser = argparse.ArgumentParser()
    parser.add_argument("--path","-p",default=".",help="StartPath",metavar='File Path')
    parser.add_argument('--test',"-t", dest='test', action='store_true',help="Test using reference model")
    parser.set_defaults(test=False)
    parser.add_argument('--component_diagram',"-o", dest='component', action='store_true',help="Create Component Diagram")
    parser.set_defaults(component_diagram=False)
    parser.add_argument('--class_diagram',"-c", dest='class', action='store_true',help="Create Class Diagram")
    parser.set_defaults(class_diagram=True)
    parser.add_argument('--filter',"-f", default=None, help="Model Filter List")
    parser.add_argument('--plant_uml',"-u", dest='plant_uml', action='store_true',help="Create PLantUML diagram images ./bat/plantuml.bat")
    parser.set_defaults(plant_uml=True)
    parser.add_argument('--total_commander',"-a", dest='total_commander', action='store_true',help="Open Total Commander ./bat/tc.bat")
    parser.set_defaults(total_commander=True)
    parser.add_argument('--images',"-i", dest='images', action='store_true',help="Open Images (Default Image Viewer)")
    parser.set_defaults(images=True)

    args = parser.parse_args()
    args_dict = {k:v for k,v in args._get_kwargs()}
    logger.info(f"Arguments {args}")
    p=args.path
    run(*args._get_kwargs())

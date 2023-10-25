""" handling arparse templates and configuration example """
# https://docs.python.org/3/library/argparse.html

import logging
import sys
import json

# import modules
import tools.cmd_client.constants as C
from tools.cmd_client.configpath import CONFIG_PATH
from tools.cmd_client.enum_helper import EnumHelper
from tools.cmd_client.runner import Runner

logger = logging.getLogger(__name__)
config_dict = {}

if __name__ == "__main__":
    # location of config file
    # copy the configpath_template, supply path and
    # set the path pointing to the param_config.yaml file
    f_config = CONFIG_PATH
    # get the argparseconfig from the yaml template file
    params_template = None
    subparser_template = None
    if True:
        params_template = "cmdparam_template"
    elif False:
        # alternatively use subparser template or you may use both
        # if the commands do not have a conflict
        subparser_template = "subparser_sample_config"
    # additional parameters (as defined in
    # cmd_params > cmdparams_default / or via Enum Definition)
    # these params are always added to main arg parser
    pa = C.DEFAULT_PARSER_ATTRIBUTES
    default_params = [pa.ADD_TIMESTAMP,pa.LOGLEVEL]
    # additional parameters that may be used
    kwargs = { C.PARSER_ATTRIBUTE.DESCRIPTION.value: "Description", # Argparse add. Description
               C.PARSER_ATTRIBUTE.PROG.value: "PROPG", # Used in Argparse description
               C.PARSER_ATTRIBUTE.EPILOG.value: "EPILOG DESCRIPTION"
             }
    runner = Runner(f_config,params_template, subparser_template,
                    default_params,**kwargs)

    # get the argparser
    argparser = runner.config.argparser
    # testargs
    # sample for params template
    if params_template:
        config_dict = argparser.parse_args("--sbtrue -ll debug".split())
    elif subparser_template:
        config_dict = argparser.parse_args("subparse_cmd -ps xyz".split())
    else:
        config_dict = argparser.parse_args()

    loglevel = C.LOGLEVEL[config_dict.get("loglevel","DEBUG").upper()].value
    # loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    # show config
    logger.info(f"\nConfig:\n {json.dumps(config_dict, indent=4)}")

    # main(**config_dict)
    # EnumHelper.as_dict(CONFIG)
    value = EnumHelper.keys(C.PARSER_ATTRIBUTE)
    pass

""" Class Boilerplate """
import sys
import logging
import argparse
import tools.cmd_client.constants as C
from tools.cmd_client.config import Config
logger = logging.getLogger(__name__)

class ParseHelper():
    """ Arguments Parsing """
    DEFAULT = "default"
    ARGS =  "args"
    KWARGS = "kwargs"
    CMDPARAM_DEFAULT = "cmdparam_default"

    def __init__(self,config:Config,
                 params_template:str=None,
                 subparser_template:str=None,
                 params_default:list=None,
                 **kwargs) -> None:
        """ constuctor, uses the params dict from config file """
        self._params_template=params_template
        self._subparser_template=subparser_template
        self._config = config
        self._cmd_params_dict = config.get_config(C.CONFIG.CMD_PARAM)
        self._cmd_subparser_dict = config.get_config(C.CONFIG.CMD_SUBPARSER)

        # check for any additonal values relevant for configuration
        parse_args = {}
        prog = kwargs.get(C.PARSER_ATTRIBUTE.PROG.value)
        if prog:
            parse_args[C.PARSER_ATTRIBUTE.PROG.value]=prog
        desc = kwargs.get(C.PARSER_ATTRIBUTE.DESCRIPTION.value)
        if desc:
            parse_args[C.PARSER_ATTRIBUTE.DESCRIPTION.value]=desc
        epilog = kwargs.get(C.PARSER_ATTRIBUTE.EPILOG.value)
        if epilog:
            parse_args[C.PARSER_ATTRIBUTE.EPILOG.value]=epilog
        self._main_parser = argparse.ArgumentParser(**parse_args)
        # add additional params from default input args
        default_arguments = self._get_default_params_filters(params_default)
        if default_arguments:
            self._add_arguments(self._main_parser,default_arguments)
        # add without subparser arguments / valid for main argparser
        if self._params_template is not None:
            self._add_template()
        # add any subparsers
        if self._subparser_template is not None:
            self._add_subparser_template()
        else:
            logger.error("no parser or subparser was submitted, check settings")
            return

    def _add_template(self):
        """ adding a single template to parser """
        # add params from the template
        arguments = self._get_args_dict(self._params_template)
        self._add_arguments(self._main_parser,arguments)

    def _add_subparser_template(self):
        """ add subparser template """
        subparser_template_dict=self._cmd_subparser_dict.get(self._subparser_template)
        if subparser_template_dict is None:
            logger.error(f"Coulddn't find Subparser Template in cmd_subparsers > {self._subparser_template}")
            return None
        subparsers = self._main_parser.add_subparsers(dest="command")
        for subcommand,parse_template in subparser_template_dict.items():
            logger.info(f"Subparser Template {self._subparser_template}, subcommand {subcommand}, parse template {parse_template}")
            arguments = self._get_args_dict(parse_template)
            if arguments is None:
                logger.warning(f"Couldn't find args template {parse_template}")
                continue
            help_args = self._cmd_params_dict[parse_template].get(C.PARSER_ATTRIBUTE.HELP.value,"no help available")
            subparser = subparsers.add_parser(subcommand,help=help_args)
            self._add_arguments(subparser,arguments)

    def _add_arguments(self,parser,arguments):
        """ adds arguments to parser """
        for arg in arguments:
            args = arg[ParseHelper.ARGS]
            kwargs = arg[ParseHelper.KWARGS]
            parser.add_argument(*args,**kwargs)
            default = arg.get(ParseHelper.DEFAULT)
            if default:
                parser.set_defaults(**default)

    def _get_default_params_filters(self,params_default:list)->None:
        """ get list of argparse default arguments from Enum List """
        # check for existing default params
        cmdparams_default = ParseHelper.CMDPARAM_DEFAULT
        cmdparams_default_dict = self._cmd_params_dict.get(cmdparams_default)
        if cmdparams_default_dict is None:
            logger.warning("Config Yaml seems to not cotnain cmd_params > cmdparams_default section, check")
            return
        default_params_keys = list(cmdparams_default_dict.keys())
        if params_default is None:
            logger.warning("No default param list was submitted, pls check")
            return None

        params_filter = [p.value for p in params_default if p.value in default_params_keys]
        if len(params_filter) == 0:
            params_filter = None
        arguments = self._get_args_dict(cmdparams_default,params_filter)
        return arguments

    def _get_args_dict(self,params_template:str,args_filter:list=None)->list:
        """ creates argparse list, if filter is supplied, only
            generate parse arguments for specified filters
        """
        ph = ParseHelper

        arguments=[]
        parse_args_dict = self._cmd_params_dict.get(params_template)
        if not parse_args_dict:
            logger.error(f"There is no cmd_params configuration named {params_template}, check")
            return
        if args_filter is None:
            args_filter = list(parse_args_dict.keys())
        logger.info(f"Read ArgParse Config {params_template}")

        for param,params_dict in parse_args_dict.items():
            if param == C.PARSER_ATTRIBUTE.HELP.value:
                logger.info(f"Params Template {params_template} ({params_dict})")
                # help_args = params_dict
                continue
            if not param in args_filter:
                continue
            param_name = params_dict.get(C.PARSER_ATTRIBUTE.PARAM.value)
            params_copy = params_dict.copy()
            param_short = "-"+params_copy.pop(C.PARSER_ATTRIBUTE.PARAM_SHORT.value)
            param = "--"+params_copy.pop(C.PARSER_ATTRIBUTE.PARAM.value)
            args = [param_short,param]
            kwargs=params_copy
            # add default value for case of input flag
            action = params_copy.get(C.PARSER_ATTRIBUTE.ACTION.value)
            default = None
            if action:
                if action == C.PARSER_ATTRIBUTE.STORE_FALSE.value:
                    default = {param_name:True}
                elif action == C.PARSER_ATTRIBUTE.STORE_TRUE.value:
                    default = {param_name:False}
            arguments.append({ph.ARGS:args,ph.KWARGS:kwargs,ph.DEFAULT:default})
        logger.info(f"Number of ParseArg arguments {len(arguments)} ")
        return arguments

    def parse_args(self,*testargs)->dict:
        """ get parsed results, additional args value can be used for debugging """
        args_dict = vars(self._main_parser.parse_args(*testargs))
        return args_dict

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

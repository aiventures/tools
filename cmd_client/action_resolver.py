""" local exit class to resolve actions, is instanciated from config_resolver
    you may use it to enhanve / extend logic to your own needsa
    you may subclass ActionResoler to get your own logic
"""

import logging
from copy import deepcopy
import tools.cmd_client.constants as C
from tools.cmd_client.enum_helper import EnumHelper

logger = logging.getLogger(__name__)

# get default actions
ACTIONS = EnumHelper.keys(C.ACTION,lower=True)

class ActionResolverMain():
    """ this class provides some boilerplate code that can be used in custom implementation """
    def __init__(self) -> None:
        # access to the complete configuration yaml if needed
        self._config_dict = None
        self.hugo = 3
        pass

    @property
    def config_dict(self):
        """ config yaml as dict (copied from config_resolver) """
        return self._config_dict

    @config_dict.setter
    def config_dict(self, config_dict):
        """ inject config yaml as dict (called from config_resolver)  """
        logger.info("Copy Config Dict To ActionResolver")
        self._config_dict = deepcopy(config_dict)
        pass
    
    @staticmethod
    def _resolve_ref(ref_key:str,action_info:dict)->dict:
        """ tries to resolve reference in action dict  """
        try:
            ref_value = action_info.get(ref_key)
        except AttributeError:
            logger.warning(f"There is no resolved reference {ref_key} in action info {action_info}, check config")
            ref_value = None
        return {ref_key:ref_value}

    def resolve_action(self,action,action_info:dict)->dict:
        """ resolve specific actions, this is the entry method called from config_resolver """
        # this treats hard coded actions, implement your own in Action Class
        match action:
            case C.ACTION_CREATE_REPORT:
                return {action:ActionResolver._resolve_ref(C.CONFIG_REPORT,action_info)}
            case C.ACTION_EXPORT_ENV:
                return {action:ActionResolver._resolve_ref(C.WIN_ENV_BAT,action_info)}
            case _:
                logger.debug(f"{action} is no default action")

class ActionResolver(ActionResolverMain):
    """ exit class to allow for custom actions (is called from config_resolver) """
    ACTION_PARAM = "action_param" # this is defined in cmd_map>cmd_client_main>map>param_action

    """ this class can be enhanced for additional actions (will be called from config_resolver) """
    def __init__(self) -> None:
        # access to the complete configuration yaml if needed
        super().__init__()
        pass


    def _action_param(self):
        """ sample action for cmd_map>cmd_client_main>map>param_action """
        return

    def _resolve_action_param(self,action_info):
        """ sample implementation for cmd_map>cmd_client_main>map>param_action """
        resolved_action = {}
        return resolved_action

    def resolve_action(self,action,action_info:dict)->dict:
        """ resolve specific actions, this is the entry method called from config_resolver
            idea of resolve: collect all information to collect it as a "context", so
            the run action can be executed at a later stage
        """
        # collect any actions done
        resolved_action = super().resolve_action(action,action_info)
        logger.info(f"Resolving ACTION [{action}]")

        match action:
            case ActionResolver.ACTION_PARAM:  # sample action from example yaml
                resolved_action = self._resolve_action_param(action_info)
            case "hugo":
                pass #implement your own stuff
            case _:
                # action_dict[action]
                logger.info(f"Action {action} is not resolved / is a standard action, check ActionResolver->resolve_action")

        return resolved_action

    def run_actions(self,actions_dict,**parsed_args):
        """ this is an exit method to run all actions and return information on
            performed actions """

        for action,action_info in actions_dict.items():
            logger.action_info(f"Running ACTION {action}")
            match action:
                # create configuration report
                case "x": # do your own stuff
                    action["x"].append("some stuff done") # wil be used in log
                    pass
                case _:
                    pass
        return action_info



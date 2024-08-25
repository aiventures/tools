""" module to filter / match strings """

import sys
from copy import deepcopy
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

# when doing tests add this to reference python path
if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from util import constants as C

# reusing constants
RULE_NAME=C.RULE_NAME
RULE_IGNORECASE=C.RULE_IGNORECASE
RULE_IS_REGEX=C.RULE_IS_REGEX
RULE_RULE=C.RULE_RULE
RULE_REGEX=C.RULE_REGEX
RULEDICT=C.RULEDICT

# Rule for applying any or all rules
APPLY_ANY = C.APPLY_ANY
APPLY_ALL = C.APPLY_ALL

class StringMatcher():
    """ bundling sets of rules to perform rule matching on strings """
    def __init__(self,rules:list=None,apply:str=APPLY_ALL) -> None:
        self._rules = {}
        # apply all or any rules
        self._apply = apply
        self.add_rules(rules)

    def add_rules(self,rules:list)->None:
        """ add list of rules """
        _rules = rules
        if not isinstance(_rules,list):
            logger.warning("No list of rules was supplied, skip")
            return
        for _rule in rules:
            self.add_rule(_rule)

    def clear(self)->None:
        """ reset list of rules """
        self._rules = {}

    def add_rule(self,rule:dict)->None:
        """ validates and adds rule """
        _rule = rule
        if not isinstance(_rule,dict):
            logger.warning(f"Trying to add rule [{rule}], which is not a rule")
            return

        try:
            _name = rule[RULE_NAME]
        except KeyError:
            rule[RULE_NAME] = None

        if rule[RULE_NAME] is None:
            _name = str(uuid.uuid4())[-8:]
            rule[RULE_NAME] = _name
            logger.info(f"No name was given, using {rule[RULE_NAME]} a s rule name")

        # step 1 copy default values
        _rule = deepcopy(RULEDICT)
        # 2step 2 copy all other values from original dict       
        _rule = {key: value for (key, value) in rule.items()}

        # add regex
        try:
            if _rule[RULE_IS_REGEX]:
                if _rule[RULE_IGNORECASE] is True:
                    _rule[RULE_REGEX] = re.compile(rule[RULE_RULE],re.IGNORECASE)
                else:
                    _rule[RULE_REGEX] = re.compile(rule[RULE_RULE])
            logger.debug(f"Adding Rule [{_name}]: {_rule}")
            self._rules[_name] = _rule
        except (TypeError,KeyError) as e:
            logger.warning(f"Rule [{rule[RULE_NAME]}], no regex expression [{rule[RULE_RULE]}] was supplied, {e}")

    def find(self,s:str,rule:str)->list:
        """ looks for string using rule, returns found string as list """
        _rule_dict = self._rules.get(rule)
        if _rule_dict is None:
            logger.warning(f"There is no matching rule named [{rule}]")
            return False

        _regex = _rule_dict[RULE_REGEX]
        # either match using regex or simple rule
        if _regex is None:
            _rule = _rule_dict[RULE_RULE]
            if _rule_dict[RULE_IGNORECASE]:
                _s = s.lower()
            else:
                _s = s
            if _rule in _s:
                return [_rule]
            else:
                return []
        else:
            _regex = _rule_dict[RULE_REGEX]
            _matches = _regex.findall(s)
            return _matches

    def find_all(self,s:str,by_rule:bool=True):
        """ returns matches.
            returns found results as dict by rule
            or as list
            by_rule: control parameter whether results are grouped by rule
        """
        found_results = {}
        for _rule_name in self._rules.keys():
            found_results[_rule_name] = self.find(s,_rule_name)

        if by_rule is False:
            _results = list(found_results.values())
            found_results = []
            _ = [found_results.extend(_result) for _result in _results]
            found_results = list(set(found_results))

        return found_results

    def matches_rule(self,s:str,rule:str)->bool:
        """ check for matching rule """
        return len(self.find(s,rule)) > 0

    def is_match(self,s:str)->bool:
        """ checks against the list of rules """
        # get all matches
        _rule_matches = {key: self.matches_rule(s,key) for key in self._rules.keys()}
        logger.debug(f"[{s}] rule matches [{_rule_matches}]")
        # depending on matching mode, set the resulting overall match
        if len(_rule_matches) == 0:
            return False
        _matches = list(_rule_matches.values())
        if self._apply == APPLY_ALL:
            return all(_matches)
        else:
            return any(_matches)

def _test():
    s = "Lorem ipsum odor amet, consectetuer adipiscing elit. Consectetur rhoncus lorem maximus magnis nisl; elit phasellus vel. Etiam ullam"
    _rule = "(.+?consec)"
    sample_rule = {RULE_NAME:"SampleRule",RULE_RULE:_rule}
    _rule2 = "HUGO"
    sample_rule2 = {RULE_NAME:"SampleRuleHUGO",RULE_RULE:_rule2}
    _matcher = StringMatcher()
    _matcher.add_rule(sample_rule)
    _matcher.add_rule(sample_rule2)
    is_match = _matcher.is_match(s)
    results = _matcher.find_all(s,by_rule=True)
    pass

def main():
    _test()
    pass

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    main()

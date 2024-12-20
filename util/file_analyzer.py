""" Analyzing Files and Paths  """

import sys
import os
# import re
from copy import deepcopy
from pathlib import Path
import logging

from util.constants import APPLY_ALL
# from datetime import datetime as DateTime
# import json
# when doing tests add this to reference python path
if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from util.const_local import P_TOOLS
from util import constants as C
from util.colors import col
from util.persistence import Persistence
from util.string_matcher import StringMatcher, FileMatcher


logger = logging.getLogger(__name__)

class FileSysObjectInfo():
    """ class to read os file and path info into a dictionary """
    def __init__(self,root_paths:list|str=None) -> None:
        self._root_paths = []
        self._filter_matcher = StringMatcher()
        if self._root_paths is None:
            _root_paths = [os.getcwd()]
            logger.debug(f"No files addedAdding f{os.getcwd()} as root path")
        elif isinstance(root_paths,str):
            _root_paths = [root_paths]
        elif isinstance(root_paths,Path):
            _root_paths = [str(root_paths)]
        for _root_path in _root_paths:
            if not os.path.isdir(_root_path):
                logger.warning(f"[{_root_path}] is not a valid path, skipping root path")
                continue
            self._root_paths.append(_root_path)
        self._files = {}
        self._paths = {}

        self._read_file_objects()

    def _read_file_objects(self)->None:
        """ get a list of all file system objects """
        self._files = {}
        self._paths = {}
        for _root_path in self._root_paths:
            _paths = []
            logger.info(f"Adding file system objects from [{_root_path}]")
            for subpath,_,files in os.walk(_root_path):
                _path = Path(subpath).absolute()
                _files_absolute = [_path.joinpath(f) for f in files]
                self._files[subpath]={C.FILES_ABSOLUTE:_files_absolute,C.FILES:files}
                _paths.append(subpath)
            self._paths[_root_path]=_paths

    @property
    def path_dict(self)->dict:
        """ returns paths by root in a dict """
        return self._paths

    @property
    def paths(self)->list:
        """ get lsit of found paths / without root paths """
        out_list = []
        _ = [out_list.extend(paths) for paths in list(self._paths.values())]
        return out_list

    @property
    def file_dict(self)->dict:
        """ returns dict of files """
        logger.debug(f"Returning files dict covering [{len(self._files)}] Directories")
        return self._files

    @property
    def files(self)->list:
        """ returns absolute Paths of all files found"""
        _file_list = []
        for p,p_info in self._files.items():
            _files = p_info.get(C.FILES_ABSOLUTE,[])
            _ = [_file_list.append(str(f)) for f in _files]
        logger.debug(f"Returning [{len(_file_list)}] Files")
        return _file_list


class FileAnalyzer():
    """ search for file names and file contents """

    def __init__(self,root_paths:list|str=None,apply:str=C.APPLY_ALL,
                 by_line_default:bool=False,by_rule:bool=True) -> None:
        """  File Info Object Constructor."""
        self._file_info = FileSysObjectInfo(root_paths)
        # separate matchers for each of the file types
        self._rule_dicts = { C.RULE_FILENAME : StringMatcher(apply_default=apply),
                             C.RULE_PATH : StringMatcher(apply_default=apply),
                             C.RULE_ABSOLUTE_PATH : StringMatcher(apply_default=apply),
                             C.RULE_FILE_CONTENT : FileMatcher(apply=apply,by_line_default=by_line_default)
                            }
        self._rule_dict = StringMatcher(apply_default=apply)
        self._by_rule = by_rule

    def add_rule(self,rule:dict)->None:
        """ Adding Filename Rule """
        _new_rule = deepcopy(C.RULEDICT_FILENAME)
        # copy over default values / use default values
        for k,default_value in _new_rule.items():
            _new_rule[k] = rule.get(k,default_value)
        # according to rule add rule to the appropriate matcher
        _rule_name = _new_rule.get(C.RULE_NAME)
        _rule_type = _new_rule.get(C.RULE_FILE)
        try:
            _rule_matcher = self._rule_dicts[_rule_type]
            _rule_matcher.add_rule(_new_rule)
        except KeyError:
            logger.error(f"Can't Identify appropriate matcher, rule [{_rule_name}], got type [{_rule_type}]")
        pass

    def _get_matcher(self,rule:str)->StringMatcher|FileMatcher:
        """ returns the matcher, preserves the object type """
        return self._rule_dicts.get(rule)

    def add_rules(self,rules:list)->None:
        """ Adding Filename Rules (list of dicts of type RULEDICT_FILENAME ) """
        for _rule in rules:
            self.add_rule(_rule)

    def _match_files(self,find_dict:dict,matcher:str,filter_result_set:bool=True)->dict:
        """ Loop over all files and try to match objects 
            filter_result_set ist a flag whether apply _all ffilters should be treated as one set        
        """
        _file_object_matches = {}
        logger.info(f"Matcher [{matcher}], check [{len(find_dict)}] objects")
        _rule_matcher = self._get_matcher(matcher)
        for _file_object_key, _file_object in find_dict.items():
            search_result = _rule_matcher.find_all(s=_file_object,by_rule=self._by_rule,filter_result_set=filter_result_set)
            # check if there are results ar all
            if len(search_result) > 0:
                _file_object_matches[_file_object_key] = search_result
        logger.info(f"Matcher [{matcher}], found [{len(_file_object_matches)}] objects")

        return _file_object_matches

    def find_file_objects(self,filter_result_set:bool=True)->dict:
        """ get the file names  
            filter_result_set is flag to treat apply_all as a joint rule set 
        """
        _file_objects = {}
        _fi = self._file_info
        # iterate over all rule matchers
        for _rule in self._rule_dicts.keys():
            _rule_matcher = self._get_matcher(_rule)
            if not isinstance(_rule_matcher,StringMatcher):
                continue
            if _rule == C.RULE_FILENAME:
                _filenames = [Path(f).name for f in _fi.files]
                _find_dict = dict(zip(_fi.files,_filenames))
            elif _rule == C.RULE_ABSOLUTE_PATH:
                _find_dict = dict(zip(_fi.files,_fi.files))
            elif _rule == C.RULE_PATH:
                # TODO CHANGE TO PATHS
                _paths = _fi.paths
                _find_dict = dict(zip(_paths,_paths))
            else:
                logger.warning(f"Invalid File Object Rule: [{_rule}]")
                continue
            _file_object_matches = self._match_files(_find_dict,_rule,filter_result_set=filter_result_set)
            if len(_file_object_matches) > 0:
                _file_objects.update(_file_object_matches)
        # todo now blend all rules together
        return _file_objects

# todo also check for content with transformed yaml, json and csv
class FileContentAnalyzer(FileAnalyzer):
    """ Adding Features to read / filter file contents """
    def __init__(self, root_paths: list | str = None,
                 apply: str = C.APPLY_ALL,
                 by_line_default: bool = False,
                 by_rule: bool = True) -> None:

        """ Constructor """
        super().__init__(root_paths, apply, by_line_default, by_rule)
        # params to read out a text file
        self._encoding = 'utf-8'
        self._comment_marker=None
        self._skip_blank_lines=False
        self._strip_lines=True
        self._with_line_nums=False

    def _postprocess_file_content(self,content_dict:dict)->dict|list:
        """ reformat found file content according to settings """
        return []

    def _find_file_content_txt(self,f:str,filter_result_set:bool=True)->dict:
        """ read a text type file line by line 
            filter_result_set: Check the all rules
        """
        _results = {}
        _rules_matcher = self._get_matcher(C.RULE_FILE_CONTENT)
        _rules = _rules_matcher.rules
        _all_rules = _rules_matcher._all_rules
        # content lines
        _content_lines = Persistence.read_txt_file(f,encoding=self._encoding,
                              comment_marker=None,
                              skip_blank_lines=False,
                              strip_lines=False,
                              with_line_nums=True)
        # content all in one for searching content in file instead of lines
        _content_file = "\n".join(list(_content_lines.values()))

        # get all file rules
        _all_rules_set = True
        for _rule,_rule_dict in _rules.items():
            _find_by_line = _rule_dict.get(C.RULE_FIND_BY_LINE,True)
            if _find_by_line is False:
                _content_dict = {0:_content_file}
            else:
                _content_dict = _content_lines
            for _line_num,_content in _content_dict.items():
                _result_matches = []
                # try to find matches using rule
                _matches = _rules_matcher.find(_content,_rule)
                if len(_matches) > 0:
                    # get previous matching results
                    _results_by_line = _results.get(_line_num,{})
                    # add existing result
                    _results_by_line[_rule] = _matches
                    _results[_line_num]=_results_by_line
                # no matches, check whether an all_rules set needs to be applied                
                else:
                    if _rule in _all_rules:
                        _all_rules_set = False 
        
        # do process the all rules set         
        if filter_result_set is True and _all_rules_set is False:
            for line,_results_by_line in _results.items():
                for _rule in _results_by_line.keys():
                    if _rule in _all_rules:
                        _ = _results_by_line.pop(_rule)
                                            
        return _results


    def find_file_content(self,f:str,filter_result_set:bool=True)->dict:
        """ find occurences in file 
            filter_result_set: Check the all rules
        """
        # use the file content rule
        _results = self._find_file_content_txt(f)
        return _results


def test_file_dict():
    """  getting a test file from the sample path """
    f_sample = (Path(__file__).parent.parent).joinpath("sample_path","lorem_doc_root.md")
    text_lines_dict = Persistence.read_txt_file(f_sample,comment_marker=None,with_line_nums=True)
    return text_lines_dict

def test_file_objects():
    """ gettimg file objects """
    p_sample = (Path(__file__).parent.parent).joinpath("sample_path")
    files_info = FileSysObjectInfo(p_sample)
    file_dict = files_info.file_dict
    files = files_info.files
    return files_info.path_dict

def test_file_matcher():
    """ testing file matcher """
    p_sample = (Path(__file__).parent.parent).joinpath("sample_path")
    file_matcher = FileAnalyzer(p_sample)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_RULE] = "test"
    file_rule[C.RULE_NAME] = "testrule"
    file_matcher.add_rule(file_rule)
    #_paths = file_matcher._file_info.path_dict
    #_files = file_matcher._file_info.files
    # Path(_files[0]).name
    # dict(zip(_files,_files))
    pass


def main():
    """ run local in test mode """
    # text_lines_dict = get_test_file_dict()
    # files_info =  get_file_objects()
    # test_file_matcher()
    pass

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    main()

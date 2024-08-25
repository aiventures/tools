""" Analyzing Files and Paths  """
import sys
import os
# import re
from copy import deepcopy
from pathlib import Path
import logging
# from datetime import datetime as DateTime
# import json
# when doing tests add this to reference python path
if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from util.const_local import P_TOOLS
from util import constants as C
from util.colors import col
from util.persistence import Persistence
from util.string_matcher import StringMatcher


logger = logging.getLogger(__name__)

class FileSysObjectInfo():
    """ class to read os file and path info into a dictionary """
    def __init__(self,root_paths:list=None) -> None:
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
    def paths(self)->dict:
        """ returns paths """
        return self._paths

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


class FileMatcher():
    """ search for file names and file contents """

    def __init__(self,root_paths:list=None,apply:str=C.APPLY_ALL) -> None:
        """  File Info Object Constructor.
        """
        self._file_info = FileSysObjectInfo(root_paths)
        # separate matchers for each of the file types
        self._rule_dicts = { C.RULE_FILENAME : StringMatcher(apply=apply),
                             C.RULE_PATH : StringMatcher(apply=apply),
                             C.RULE_ABSOLUTE_PATH : StringMatcher(apply=apply),
                             C.RULE_FILE_CONTENT : StringMatcher(apply=apply)
                            }
        self._rule_dict = StringMatcher(apply=apply)

    def add_rule(self,rule:dict)->None:
        """ Adding Filename Rule """
        _new_rule = deepcopy(C.RULEDICT_FILENAME)
        # copy over default values
        for k,v in _new_rule.items():
            _new_rule[k] = rule.get(k,v)
        # according to rule add rule to the appropriate matcher
        _rule_name = _new_rule.get(C.RULE_NAME)
        _rule_type = _new_rule.get(C.RULE_FILE)
        try:
            _rule_dict = self._rule_dicts[_rule_type]
            _rule_dict.add_rule(_new_rule)
        except KeyError:
            logger.error(f"Can't Identify appropriate matcher, rule [{_rule_name}], got type [{_rule_type}]")
        pass

    def add_rules(self,rules:list)->None:
        """ Adding Filename Rules """
        for _rule in rules:
            self.add_rule(_rule)



# class TextFinder():
#     """ Analyzes a file for text files """

#     def __init__(self,f:str) -> None:
#         """ Constructor """
#         self._f = None
#         if not os.path.isfile(f):
#             logger.error(f"File Path [{f}] is not valid")
#         else:
#             self._f = f


    # def find(self,s_search:str,sep:str="/",
    #          match_all:bool=True,icase:bool=True,
    #          exact:bool=False) -> dict:
    #     """ Perform a regex search for given regex string.
    #         This string represents a multitude of single regexes
    #         so that it can be simply passed using console commands
    #         Parameters:
    #         * s_search: search string ( multiple regex expressions
    #                     separated ba separator )
    #         * sep:      separator string
    #         * match_al: all searches must be found to return entry
    #                     otherwise it's any and only one rule needs to match
    #         * icase     case insensitive search
    #         * exact     exact search. Instead of regex search, simply
    #                     use string search
    #     """
    #     pass

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
    return files_info.paths

def test_file_matcher():
    p_sample = (Path(__file__).parent.parent).joinpath("sample_path")
    file_matcher = FileMatcher(p_sample)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_RULE] = "test"
    file_rule[C.RULE_NAME] = "testrule"
    file_matcher.add_rule(file_rule)
    pass


def main():
    """ run local in test mode """
    # f_text = os.path.join(P_TOOLS,"sample","test_text.txt")
    # with open(f_text, 'r',encoding="UTF-8") as fp:
    #     for n, line in enumerate(fp):
    #         # search string
    #         print(f"[{n}] {line}")
    #file_info = FileSysObjectInfo([p])
    # text_lines_dict = get_test_file_dict()
    # files_info =  get_file_objects()
    test_file_matcher()
    pass

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    main()

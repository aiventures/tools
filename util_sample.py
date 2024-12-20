""" sample program for the util package """

import os
import sys

import logging
from pathlib import Path
from copy import deepcopy
from util import const_local
from util import constants as C
from util.file_analyzer import FileSysObjectInfo
from util.file_analyzer import FileAnalyzer
from util.file_analyzer import FileContentAnalyzer
from util.persistence import Persistence

logger = logging.getLogger(__name__)

p_testpath = Path(__file__).parent.joinpath("sample_path")
f_testfile = os.path.join(p_testpath,"subpath1","file1.txt")

def get_file_objects()->dict:
    """ simple retrieval of all objects """
    _files_info = FileSysObjectInfo(p_testpath)
    _file_dict = _files_info.file_dict
    _files = _files_info.files
    _paths = _files_info.path_dict
    return _file_dict

def read_file_content()->dict:
    """ read file data using Persistence """
    _f = Persistence(f_testfile)
    # Params
    # encoding='utf-8',
    # comment_marker=None,
    # skip_blank_lines=False,
    # strip_lines=True,
    # with_line_nums:bool=False)
    _content = _f.read_file()
    return _content

def find_by_filename()->dict:
    """ test: find by filename only (w/o path) """
    result = {}
    file_matcher = FileAnalyzer(p_testpath)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_NAME] = "rule_filename_md"
    # sample: find all files contiainng a md in filename
    file_rule[C.RULE_RULE] = r".*\.md"
    # sample file rule type: search in file name
    file_rule[C.RULE_FILE] = C.RULE_FILENAME
    file_matcher.add_rule(file_rule)
    result = file_matcher.find_file_objects()

    return result

def find_by_abs_filename()->dict:
    """ test: find by absolute filename  (including path) """
    result = {}
    file_matcher = FileAnalyzer(p_testpath)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_NAME] = "rule_filename_abs_md"
    # sample: find all files contiainng a md in absolute filename
    file_rule[C.RULE_RULE] = r".*\.md"
    # sample file rule type: search in file name
    file_rule[C.RULE_FILE] = C.RULE_ABSOLUTE_PATH
    file_matcher.add_rule(file_rule)
    result = file_matcher.find_file_objects()
    return result

def find_by_path()->dict:
    """ find in paths """
    result = {}
    file_matcher = FileAnalyzer(p_testpath)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_NAME] = "rule_path"
    # sample: find all files containing a md in absolute filename
    file_rule[C.RULE_RULE] = r".*path1"
    # sample file rule type: search in file name
    file_rule[C.RULE_FILE] = C.RULE_PATH
    file_matcher.add_rule(file_rule)
    result = file_matcher.find_file_objects()
    return result

def find_in_file()->dict:
    """ find content in file """
    result = {}    
    # TODO Integrate this into the FileAnalyzer Object 
    file_content_matcher = FileContentAnalyzer(p_testpath)
    file_rule = deepcopy(C.RULEDICT_FILENAME)
    file_rule[C.RULE_NAME] = "rule_file_content"
    # # sample: find all files containing a md in absolute filename
    file_rule[C.RULE_RULE] = "zombi"
    # # sample file rule type: search in file content
    file_rule[C.RULE_FILE] = C.RULE_FILE_CONTENT
    file_content_matcher.add_rule(file_rule)
    result = file_content_matcher.find_file_content(f_testfile)
    return result

def main():
    """ run local in test mode """
    # text_lines_dict = get_test_file_dict()
    # files_info =  get_file_objects()
    # test_file_matcher()
    files_info = get_file_objects()
    file_content = read_file_content()
    found_files_by_filename = find_by_filename()
    found_files_by_abs_filename = find_by_abs_filename()
    found_files_by_path = find_by_path()
    found_content_in_file = find_in_file()
    pass

if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    main()

    # test_cygwin()
    # test_config()
    # test_regex()
    # test_path()

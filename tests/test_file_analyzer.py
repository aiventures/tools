""" Testing the /util/file_analyzer module """

import pytest
from unittest.mock import MagicMock

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

def test_setup(fixture_testfile,fixture_testpath):
    """ Setup Method """
    assert fixture_testfile.is_file()
    assert fixture_testpath.is_dir()

def test_hugo():
    """  """
    assert True

def test_filesys_object_info(fixture_testpath):
    """ simple retrieval of all objects """
    _files_info = FileSysObjectInfo(fixture_testpath)
    _file_dict = _files_info.file_dict
    _files = _files_info.files
    _paths = _files_info.path_dict
    assert True


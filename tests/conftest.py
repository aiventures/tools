""" Test Setup """

import pytest
import sys
import os
from copy import deepcopy
from pathlib import Path
import logging

@pytest.fixture
def fixture_testpath()->Path:
    """ Sample Path """
    p_testpath = Path(__file__).parent.parent.joinpath("sample_path")
    return p_testpath

@pytest.fixture
def fixture_testfile(fixture_testpath)->Path:
    """ sample tesfile """
    f_testfile = Path(os.path.join(fixture_testpath,"subpath1","file1.txt"))
    return f_testfile

import pytest
from unittest.mock import Mock

from mypackage.module_external import ExternalClass
# from mypackage.module_myclass import MyClass01


@pytest.fixture(scope="package")
def side_effect_raise_exception():
    return Exception("side_effect_raise_exception")

@pytest.fixture(scope="package")
def mock_external_class():
    """ generate a Mock based on Class Definition """
    # does not contain any object attributes (external_att1 missing)
    _mock_external_class = Mock(spec=ExternalClass,name="mock_external_class")
    return _mock_external_class

@pytest.fixture(scope="package")
def mock_external_class_obj():
    """ generate a mock based on Object, also provides object atttributes """
    _mock_obj = ExternalClass()
    # contains external_att1
    _mock_external_class = Mock(spec=_mock_obj,name="mock_external_class_obj")
    # you may change attribuzte values / check in debugger
    # this will replace the magic mock by a value / object
    # mock_external_class.mock_external_class_obj = "mock_external_class_obj_v2"
    _mock_external_class.configure_mock(external_att1="mock_external_class_obj_v2")
    return _mock_external_class

@pytest.fixture
def monkeypatch_external_class_obj(monkeypatch):
    """ generate a monkeypatched version """
    _monkeypatch_extclass_obj = ExternalClass()
    # replacing attribute with monkeypatched version
    monkeypatch.setattr(_monkeypatch_extclass_obj, "external_att1", "monkeypatch_external_class_obj_v2")
    return _monkeypatch_extclass_obj

@pytest.fixture(scope="package")
def mock_external_class_obj_raise_exc(mock_external_class_obj,side_effect_raise_exception):
    _mock_raising_exc=mock_external_class_obj
    # add exception when calling external_instance_method
    _method_mock_exc=Mock(side_effect=side_effect_raise_exception)
    _mock_raising_exc.external_instance_method=_method_mock_exc
    return _mock_raising_exc





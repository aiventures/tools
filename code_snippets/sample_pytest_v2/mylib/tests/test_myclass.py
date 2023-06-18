""" Unit Test Samples """

from mypackage.module_myclass import MyClass01
from mypackage.module_external import ExternalClass
from unittest import mock
from unittest.mock import patch, PropertyMock, Mock
import pytest



def test_external_class_obj(mock_external_class_obj):
    """  getting mock object based on object instance """
    #
    print(mock_external_class_obj.external_instance_method())

def test_external_class(mock_external_class):
    """  getting mock object based on object definition """
    print(mock_external_class.external_instance_method())    

def test_monkeypatch_external_class(monkeypatch_external_class_obj):
    """  getting monkeypatched object """
    print(monkeypatch_external_class_obj.external_instance_method())        

def test_raise_exception(mock_external_class_obj_raise_exc):
    """  raising an exception """
    try:
        mock_external_class_obj_raise_exc.external_instance_method()
    #_raise_exc.external_instance_method()          
    except Exception as e:
        print("exception raised",e)

# @mock.patch("obj.meth",value) takes the object string returns / sets up mock obj
# @mock.path.object(Obj,meth,value) takes an object MyObject ...
# @mock.patch(
#         "mypackage.module_myclass.MyClass01.get_external",
#         return_value="mocking the method get_external"
# )
# class variables 
# @patch("mypackage.module_myclass.MyClass01.get_external",return_value="HUGO") # works
# @patch("mypackage.module_myclass.MyClass01.myclass_att1",return_value="HUGO") # does not work 
@patch('mypackage.module_myclass.MyClass01.myclass_class_att1', 
       new_callable=PropertyMock, return_value="HUGO")
def test_mock_self_method(mock_myclass_class_att1):
    """  mock parts of object instances in this case the get_external is patched  """    
    my_class01 = MyClass01()
    assert my_class01.myclass_class_att1 == "HUGO"
    # only the method / class attributes will be patched that way
    # objext attributes can't be patched this way ()
    # doesnt have the attribute ... for this use monkey patching or use encapsulation of objects
    # OR to be checked: call it with new attribute !
    pass

@mock.patch("mypackage.module_myclass.ExternalClass.external_instance_method") 
              # note the path: where its patched not where it is originated! 
def test_mock_external_class_method(mock_external_instance_method):
    """  mock parts of object instances in this case the get_external is patched  """    
    # set up the external instance mock return value 
    mock_external_instance_method.return_value="HUGO"

    my_class01 = MyClass01()
    value = my_class01.get_external() # this will implicitly call the mocked method

    assert value == "HUGO"

@patch("mypackage.module_myclass.MyClass01",return_value=Mock(spec=MyClass01)) 
# note the path: where its patched not where it is originated! 
def test_mock_object_attribute(mock_myclass_att1):
    """  mock parts of object instances in this case the get_external is patched  """    
    # set up the external instance mock return value 
    # mock_external_instance_method.return_value="HUGO"
    mock_myclass_att1.return_value.myclass_att1 = "HUGO"

    my_class01 = MyClass01()
    value=my_class01.myclass_att1 #  !!not replacing 
    assert not value == "HUGO"

def test_mock_object_attribute_v2():
    """  mock parts of object instances in this case the get_external is patched  """    
    # set up the external instance mock return value 
    # mock_external_instance_method.return_value="HUGO"
    patcher=patch("mypackage.module_myclass.MyClass01.myclass_att1",create=True)
    mock_att = patcher.start()
    mock_att.return_value = "HUGO"
    #mock_myclass_att1.return_value.myclass_att1 = "HUGO"
    my_class01 = MyClass01()
    value=my_class01.myclass_att1 # not replacing 
    patcher.stop
    # assert value == "HUGO"



# @pytest.mark.parametrize("mypackage.module_myclass.ExternalClass",
#                         [Mock(),Mock()])
# this is wrong 
# patching the call to the external class api method 
@mock.patch("mypackage.module_myclass.ExternalClass.external_instance_api_method") 
def test_call_mock_multiple(mock_external_api_call):
    """ calls a mock object multiple times """
    # return different values / coud also be a fixture 
    mock_external_api_call.side_effect=["MOCKING 1stCall","MOCKING 2ndCall",Exception("MOCK Exeption")]
    my_class01 = MyClass01()
    value = my_class01.get_external_api("test") # you see the test1 input is irrelevant
    assert value == "MOCKING 1stCall"
    print(value)
    value = my_class01.get_external_api("test")
    assert value == "MOCKING 2ndCall"
    print(value)
    # 3rd Call - Exception: verify that an exception was thrown using regex
    with pytest.raises(Exception,match=".*MOCK") as e:
        value = my_class01.get_external_api("test")

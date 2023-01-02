""" unit tests / just a copy of old unit test / they do not work due to wrong package import """

# unit tests in subfolder beneath root throw an error
# https://github.com/microsoft/vscode-python/issues/18030
# from datetime import datetime
# from datetime import timezone
# import unittest
from unittest.mock import MagicMock
import pytest
# from unittest import mock
from unittest.mock import create_autospec

# execute single unit test in Test Class TestCUT
# pytest -s -v ./test/test_class_under_test.py::TestCUT::test_method_mock_spec
# pytest -vvv --debug < dwebug pytest

#from unittest.mock import Mock
#from unittest.mock  import MagicMock
# in project folder, run pytest -s -v to get verbose oputput
# error fixture mocker not found > its in ..._env > requires pytest-mock package
# pytest-mock is missing!
#from unittest.mock import patch
#from unittest.mock import Mock

# from  unittest_sample.class_under_test import ClassUnderTest
# from class_under_test import ClassUnderTest

# @pytest.mark.parametrize(
#     "param1,param2",
#     [
#         ("a", "b"),
#         ("c", "d"),
#     ],
# )

# @pytest.fixture
# def my_cut():
#     #print("*** CREATED my_cut OBJECT")
#     return ClassUnderTest()

# # fixtures are not used when subclassing unittest.TestCase

# class TestCUT():
#     """A class with common parameters, `param1` and `param2`."""


#     @classmethod
#     def setup_class(cls):
#         print("\n### SETUP class: {} execution".format(cls.__name__))

#     @classmethod
#     def teardown_class(cls):
#         print("\n### TEARDOWN class: {} execution".format(cls.__name__))

#     def setup(self):
#         print("\n&&&&&& TC SETUP OBJECT METHOD, CALLED BY PYTEST")

#     def setup_method(self,method):
#         print("  TC SETUP METHOD, CALLED BY PYTEST")
#         print("  starting execution of tc: {}".format(method.__name__))

#     def teardown_method(self,method):
#         print("  TC TEARDOWN  METHOD, CALLED BY PYTEST")
#         print("  ending execution of tc: {}".format(method.__name__))

#     # using fixture object
#     def test_fixture(self,my_cut):
#         my_external_value = my_cut.method_cut()
#         print(f"** method_cut, returns {my_external_value} **")
#         assert True

#     # using mock for method return
#     def test_method_mock(self,mocker):
#         # patching objects: create method stubs
#         mocker.patch("refered_class.ReferedClass.get_refered_class_attribute", return_value="***MOCKED_RETURN***")

#         out = ClassUnderTest().method_cut()
#         print(f"returning value method_cut(): {out}")
#         assert True

#     # using mock for method return
#     def test_method_mock_fixture(self,my_cut,mocker):
#         # patching objects: create method stubs, also works for ficture objects
#         mocker.patch("refered_class.ReferedClass.get_refered_class_attribute", return_value="***MOCKED_RETURN***")
#         out = my_cut.method_cut()
#         print(f"returning value for fixtured object method_cut(): {out}")
#         assert True

#     # calling the same method but with side effect / different parameters
#     # https://alysivji.github.io/mocking-functions-inputs-args.html
#     # using magic mock to create different outputs dependent from input
#     def test_method_mock_dynamic_param(self,my_cut,mocker):

#         # arbitrary method to return dynamic return depending from input
#         def my_mocked_func(p):
#             if p == "test":
#                 return "SPECIAL MOCK FUNCTION CALLED"
#             else:
#                 return p

#         # patch the method with a side effect
#         mocker.patch("class_under_test.ClassUnderTest._method_internal", side_effect=my_mocked_func)
#         out = my_cut.method_call_internal("test")
#         assert "SPECIAL" in out
#         out = my_cut.method_call_internal("other")
#         assert "other" in out

#     # setting up a mock based on function signature using spec
#     def test_method_mock_spec(self,my_cut,mocker):

#         # sideffect functions needs to match the same signature
#         # sidefeffect_func even works with self
#         def sideeffect_func(p1,p2):
#             print(f"sidefeffect_func is called with {p1} {p2}")
#             return "sidefeffect_func"

#         #mock_func=MagicMock(name="cut.method_complex",spec=my_cut)

#         # if we call the mock with wrong parameters than method complex
#         # then a type error is thrown
#         mock_func=create_autospec(my_cut.method_complex)
#         mock_func.side_effect=sideeffect_func

#         # attach mock function to original object
#         m = mocker.patch("class_under_test.ClassUnderTest.method_complex", side_effect=mock_func)

#         # assert m.call_count == 2 # mock is called two times (is of type MagicMock)
#         #assert result == expected # expected result

#         #mock_func=create_autospec(my_cut)

#         #mock_func.name("my_cut.method_complex")
#         # print("FUNCTIONS IN MOCK",dir(mock_func))

#         # calling mock function with 2 params as original function shows results as expected
#         out=mock_func("a","b")
#         print(f"=> result of sideeffect_func is {out}")

        # calling it with only one params throws a type error
        #with pytest.raises(TypeError):
        #    print("RAISING TYPE ERROR")
        #    mock_func("ONLY ONE PARAM")

        #print("xxxx",x)

        # print(mock.method_complex("a","b"))
        #mock=mock
        #mock.method_complex=
        # this is the real method
        #print((my_cut.method_complex("a","b")))

        #print(mock.method_complex)
        #mock_method_complex.
        #

    # def test_autospec(self,my_cut,mocker):
    #     def patched_func(p1,p2):
    #         print("JUST A DUMMY PATCH")
    #         return "JUST A DUMMY PATCH"
    #     mocker.patch("class_under_test.ClassUnderTest._method_internal", side_effect=my_mocked_func)
    # get a dummy method with a side effect
    # my_dummy_method = MagicMock(name="my_dummy_method",side_effect=TestCUT.my_mocked_func)
    # patching a method with a function
    #mock_api = mocker.MagicMock(name='api')
    #mock_api.get.side_effect = load_data
    #mocker.patch('calc_stats.fitness_api', new=mock_api)
    #my_mock_func = MagicMock(name="FunctionDummy")
    #my_mock_func.side_effect = self.my_mocked_func
    #mocker.patch("class_under_test.ClassUnderTest")
    #pytest.fixture
    # def fixt(self):
    #     """This fixture will only be available within the scope of TestGroup"""
    #     return 123

    # def test_one(self, param1, param2, fixt):
    #     print("\ntest_one", param1, param2, fixt)

    # def test_two(self, param1, param2):
    #     print("\ntest_two", param1, param2)
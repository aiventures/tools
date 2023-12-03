""" this is a class representing implementation class with external dependencies """
import logging
from my_package.module_external import ExternalClass
from logging import BASIC_FORMAT
from logging import BufferingFormatter

logger = logging.getLogger(__name__)

my_module_var = "sfsfsffs"
my_module_dict = {"key":"value"}

def my_function(my_function_param:str)->dict:
    """ returns a dict """
    return {}

class MyClass01():
    """ sample class """
    myclass_class_att1="MyClass01.att11"
    myclass_dict={}    
    myclass_ref_ext_class = ExternalClass()

    def __init__(self):
        self.myclass_att1="<self.myclass_att1>"
        self.myclass_ext_att1=None
        self._get_external()
        self._my_class_list=list()
        s=f"Constructor MyClass01: self(MyClass01).myclass_att1: { self.myclass_att1}"
        logger.info("s")
        print("s")

    def _get_external(self,aFormatter:BufferingFormatter=None)->str:
        """ gets external class and reads object attribute """
        ext_class = ExternalClass()
        self.myclass_ext_att1 = ext_class.external_instance_method()
        s=f"self(MyClass01).myclass_ext_att1: { self.myclass_ext_att1}"
        logger.info(s)
        print(s)
        return self.myclass_ext_att1


    def get_external_api(self,param:str="test")->str:
        """ simulates returning something from an API """
        ext_class = ExternalClass()
        value = ext_class.external_instance_api_method(param)
        s=f"self(MyClass01).get_external_api({param}): { value }"
        logger.info(s)
        print(s)
        return value

    def myclass_instance_method(self, avar:int)->dict:
        """ an object method returning object value """
        s=f"myclass_method, return attribute self.myclass_att1 {self.myclass_att1}"
        logger.info(s)
        print(s)
        return self.myclass_att1

    @staticmethod
    def myclass_method(class_meth_param:list=[])->str:
        """ static method returning class attribute """
        s=f"myclass_method, return attribute MyClass01.myclass_class_att1 {MyClass01.myclass_class_att1}"
        logger.info(s)
        print(s)
        return MyClass01.myclass_class_att1

class MySubClass(MyClass01):
    """ Testing Subclass """
    myclass_subclass_att1="MySubClass.att11"

    def __init__(self):
        super().__init__()
        self.mysublass_att = 5

    @staticmethod
    def mysubclass_method(subclass_meth_param:list=[])->str:
        """ static method returning class attribute """
        s=f"myclass_method, return attribute MyClass01.myclass_class_att1 {MySubClass.myclass_subclass_att1}"
        logger.info(s)
        print(s)
        return MySubClass.myclass_subclass_att1

    def mysubclass_instance_method(self):
        """ an object method returning object value """
        s=f"mysubclass_method, return attribute self.mysubclass_att1 {self.mysublass_att}"
        logger.info(s)
        print(s)
        return self.myclass_att1



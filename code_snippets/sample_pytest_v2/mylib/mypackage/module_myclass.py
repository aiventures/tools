""" this is a class representing implementation class with external dependencies """
import logging
from mypackage.module_external import ExternalClass

logger = logging.getLogger(__name__)

class MyClass01():
    """ sample class """
    myclass_class_att1="MyClass01.att11"

    def __init__(self):
        self.myclass_att1="<self.myclass_att1>"
        self.myclass_ext_att1=None
        self.get_external()
        s=f"Constructor MyClass01: self(MyClass01).myclass_att1: { self.myclass_att1}"
        logger.info("s")
        print("s")

    def get_external(self):
        """ gets external class and reads object attribute """
        ext_class = ExternalClass()
        self.myclass_ext_att1 = ext_class.external_instance_method()
        s=f"self(MyClass01).myclass_ext_att1: { self.myclass_ext_att1}"
        logger.info(s)
        print(s)        
        return self.myclass_ext_att1 


    def get_external_api(self,param):
        """ simulates returning something from an API """
        ext_class = ExternalClass()
        value = ext_class.external_instance_api_method(param)
        s=f"self(MyClass01).get_external_api({param}): { value }"
        logger.info(s)
        print(s)        
        return value

    def myclass_instance_method(self):
        """ an object method returning object value """
        s=f"myclass_method, return attribute self.myclass_att1 {self.myclass_att1}"
        logger.info(s)
        print(s)
        return self.myclass_att1

    @staticmethod
    def myclass_method():
        """ static method returning class attribute """
        s=f"myclass_method, return attribute MyClass01.myclass_class_att1 {MyClass01.myclass_class_att1}"
        logger.info(s)
        print(s)
        return MyClass01.myclass_class_att1


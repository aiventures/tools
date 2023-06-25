""" this is a class representing external dependendies """
import logging

logger = logging.getLogger(__name__)

class ExternalClass():
    """ simulation of external dependency """
    externalclass_class_att1="ExternalClass.att1"
    def __init__(self):
        logger.info("Constructor ExternalClass")
        self.external_att1="self(ExternalClass).external_att1"

    def external_instance_method(self):
        """ an object method returning object value """
        logger.info(f"external_instance_method, return attribute self.external_att1 {self.external_att1}")
        return self.external_att1
    
    def external_instance_api_method(self,value):
        """ an object method simulating an api call or something, simply returns input """
        logger.info(f"external_instance_method, return attribute self.external_att1 {self.external_att1}")
        return value    

    @staticmethod
    def external_class_method():
        """ static method returning class attribute """
        logger.info(f"external_class_method, return attribute ExternalClass.class_att1 {ExternalClass.externalclass_class_att1}")
        return ExternalClass.externalclass_class_att1

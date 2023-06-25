""" testing the inspect module """
import inspect
from inspect import Attribute

# sys.path sys.modules
import sys
import types

from my_package import module_external
from my_package import module_myclass
from my_package.module_myclass import MyClass01

class CodeInspector():

    STATIC="static"
    INSTANCE="instance"
    MODULE = "MODULE"
    FUNCTION = "FUNCTION"
    PRIMITIVE = "PRIMITIVE"
    METHOD = "METHOD"
    CLASS = "CLASS"
    CLASS_INSTANCE = "CLASS_INSTANCE"
    BUILTIN = "BUILTIN"
    GETSETDESCRIPTOR = "GETSETDESCRIPTOR"
    ISMEMBERDESCRIPTOR = "ISMEMBER"
    ATTRIBUTE_OBJECTTYPE = "object_type"
    ATTRIBUTE_IS_INSTANCE = "is_instance"
    ATTRIBUTE_SIGNATURE = "signature"
    ATTRIBUTE_SCOPE = "scope"
    ATTRIBUTE_NAME="__name__"
    ATTRIBUTE_MODULE="__module__"
    ATTRIBUTE_FILE="__file__"
    ATTRIBUTE_DOC="__doc__"
    ATTRIBUTE_PACKAGE="__package__"
    ATTRIBUTE_OBJREF="objref"

    MEMBER_PRIVATE_ATTRIBUTES=[ATTRIBUTE_NAME,ATTRIBUTE_MODULE,
                               ATTRIBUTE_PACKAGE,ATTRIBUTE_DOC,
                               ATTRIBUTE_FILE]

    TYPES = {
        MODULE:(lambda o:inspect.ismodule(o)),
        PRIMITIVE:(lambda o: getattr(o,"__dict__",None) is None ),
        FUNCTION:(lambda o:inspect.isfunction(o)),
        METHOD:(lambda o:inspect.ismethod(o)),
        CLASS:(lambda o:inspect.isclass(o)),
        CLASS_INSTANCE:(lambda o:inspect.isclass(type(o))),
        ISMEMBERDESCRIPTOR:(lambda o: inspect.ismemberdescriptor(o)),
    }


    @staticmethod
    def get_type(object):
        """  """
        o_type = None
        """ gets the object type from inspect """
        for object_type in CodeInspector.TYPES.keys():
            if CodeInspector.TYPES[object_type](object):
                return object_type
        return None
        # return type(object).__name__

    @staticmethod
    def get_object_attributes(object):
        """ Gets the attributes for an object """
        # TODO check whether it is instanciated is class
        object_props = {}
        object_type = CodeInspector.get_type(object)

        # for an object instance check if it is an instanciated class
        # if object_type not in list(InspectTest.TYPES.keys()):
        if not object_type:
            object_type =  type(object).__name__

        # get attributes of interest
        for att in CodeInspector.MEMBER_PRIVATE_ATTRIBUTES:
            if hasattr(object,att):
                object_props[att]=getattr(object,att)
        object_props[CodeInspector.ATTRIBUTE_OBJECTTYPE]=object_type

        # now check method /( object signatures ) if there are any
        signature_dict = {}
        try:
            signature_dict = object.__annotations__
            for param,value in signature_dict.items():
                signature_dict[param]=value.__name__
            object_props[CodeInspector.ATTRIBUTE_SIGNATURE]=signature_dict
        except AttributeError:
            pass

        # TODO get members for class object

        object_props[CodeInspector.ATTRIBUTE_OBJREF]=object


        return object_props

    def __init__(self):
        pass

    def inspect_object(self,object):
        """  Get Object Information supports both objects and
             object instances (self attributes are only found in Instances) """

        # TODO load CLass information when object is a module

        object_props = CodeInspector.get_object_attributes(object)

        # create an obbject key separate by colons
        module=object_props.get(CodeInspector.ATTRIBUTE_MODULE)
        type=object_props.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        if type == CodeInspector.CLASS_INSTANCE:         
            instance_variables = vars(object)
            #all variables including class vars
            #instance_variables = [attr for attr in dir(object) if not callable(getattr(object, attr)) 
            #                      and not attr.startswith("__")]
        elif type == CodeInspector.MODULE:  
            module = CodeInspector.MODULE
        else:
            instance_variables = []

        try:
            name=object_props[CodeInspector.ATTRIBUTE_NAME]

        except Exception as e:
            name=type
        key=module+":"+name+":"+type

        members_dict ={}
        members_list = inspect.getmembers(object)



        for member_name, member_object in members_list:
            is_instance = None
            if member_name.startswith("__"):
                continue
            member_props = CodeInspector.get_object_attributes(member_object)
            member_props[CodeInspector.ATTRIBUTE_NAME]=member_name

            # check for static or instance methods methods
            if type == CodeInspector.CLASS_INSTANCE:            
                if member_props[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.FUNCTION:
                    is_instance = False
                elif member_props[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.METHOD:
                    is_instance = True
                # instance variables are found in object bit not class variables
                else:
                    if member_name in instance_variables:
                        is_instance = True
                    else:
                        is_instance = False

            # when calling the class all methods are functions ... 
            # if method is in dict, then check for staticmethod                  
            elif type == CodeInspector.CLASS:
                if member_props[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.FUNCTION:
                    try:
                        is_instance= not ( isinstance(object.__dict__[member_name],staticmethod) )
                    except Exception:
                        is_instance = None
                        print(f"Couldn't find method {member_name} in Class Definition")	                
                # when class is parsed, instance variables are absent 
                else:
                    is_instance = False

            member_props[CodeInspector.ATTRIBUTE_IS_INSTANCE]=is_instance
            members_dict[member_name]=member_props

        return { "key":key,
                 "object":object_props,
                 "members":members_dict
        }

        pass

if __name__ == "__main__":
    # InspectTest().inspect_object(module_myclass)
    #myclass = MyClass01()
    #object_info=CodeInspector().inspect_object(MyClass01)
    object_info=CodeInspector().inspect_object(module_myclass)
    external_class=CodeInspector().inspect_object(object_info['members']['ExternalClass']["objref"])
    class_info=object_info['members']['ExternalClass']["objref"]
    external_class_instance=class_info()
#    object_info=CodeInspector().inspect_object(myclass)
    pass
#    InspectTest().inspect_class()
#    for object attributes the object need to be instanciated
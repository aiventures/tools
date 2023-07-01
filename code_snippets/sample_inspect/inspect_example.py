""" testing the inspect module """
import inspect
from inspect import Attribute

# sys.path sys.modules
import os
import sys
import types
import logging
from pathlib import Path
from my_package import module_external
from my_package import module_myclass
from my_package.module_myclass import MyClass01
from my_package.module_myclass import MySubClass

logger = logging.getLogger(__name__)

class CodeInspector():

    STATIC="static"
    INSTANCE="instance"
    MODULE = "MODULE"
    FUNCTION = "FUNCTION"
    PRIMITIVE = "PRIMITIVE"
    METHOD = "METHOD"
    RELATION = "RELATION"
    RELATION_IMPLEMENTS = "implements"
    RELATION_IMPORTS = "imports"
    RELATION_MODULE_INSTANCE = "module_instance" # any type of things instanciated on module level
    RELATION_MODULE = "relation_module" # referred module

    KEY="keys"
    CLASS = "CLASS"
    CLASS_INSTANCE = "CLASS_INSTANCE"
    BUILTIN = "BUILTIN"
    OBJECT="object"
    MEMBERS="members"
    GETSETDESCRIPTOR = "GETSETDESCRIPTOR"
    ISMEMBERDESCRIPTOR = "ISMEMBER"
    ATTRIBUTE_SUPERCLASS = "superclass"
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
    def is_pythonlib_subpath(p_path):
        """ checks if file path is subpath of python system path """
        is_subpath=[False]
        p=os.path.realpath(p_path)
        python_syspaths = [os.path.realpath(sys.base_exec_prefix),os.path.realpath(sys.exec_prefix)]
        for python_syspath in python_syspaths:
            is_subpath.append(python_syspath == p or p.startswith(python_syspath+os.sep))
        return any(is_subpath)

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

        # check for superclass
        if object_type == CodeInspector.CLASS or object_type == CodeInspector.CLASS_INSTANCE:
            try:
                superclasses = inspect.getmro(object)
                if len(superclasses) > 2: # superclass is always object
                    object_props[CodeInspector.ATTRIBUTE_SUPERCLASS] = superclasses[1]
            except AttributeError as e:
                logger.warning(f"No superclass found, error {e}")

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

                        logger.warning(f"Couldn't find method {member_name} in Class Definition")
                # when class is parsed, instance variables are absent
                else:
                    is_instance = False

            member_props[CodeInspector.ATTRIBUTE_IS_INSTANCE]=is_instance
            members_dict[member_name]=member_props

        return { CodeInspector.KEY:key,
                 CodeInspector.OBJECT:object_props,
                 CodeInspector.MEMBERS:members_dict
        }

        pass

    @staticmethod
    def inspect_module(module_object):
        """ analyses module object """

        object = module_object.get(CodeInspector.OBJECT)

        if not object:
            logger.warning("Passed object may not be valid object info")
            return
        if not object[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.MODULE:
            logger.warning("Passed object is not a module")
            return
        object_module_name=object.get(CodeInspector.ATTRIBUTE_NAME)
        object_module_package=object.get(CodeInspector.ATTRIBUTE_PACKAGE)
        members = module_object.get(CodeInspector.MEMBERS)
        logger.info(f"Analyzing module {object_module_name} (Package {object_module_package})")

        # get list of modules as fallback when some attributes weren't found
        imported_modules=[]

        for member_name, member_object in members.items():
            member_module_name=member_object.get(CodeInspector.ATTRIBUTE_MODULE)
            member_object_type=member_object.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            member_package=member_object.get(CodeInspector.ATTRIBUTE_PACKAGE)
            # if module name is present, check for implementation in analysed module
            if member_module_name == object_module_name:
                member_object[CodeInspector.RELATION]=CodeInspector.RELATION_IMPLEMENTS
                member_object[CodeInspector.RELATION_MODULE] = object_module_name
                logger.debug(f"Module {object_module_name}, implements member {member_name}, type {member_object_type}")
                continue

            # determine module relations
            if member_module_name is None:
                # import of a module
                if member_object_type == CodeInspector.MODULE and member_package is not None:
                    member_object[CodeInspector.RELATION]=CodeInspector.RELATION_IMPORTS
                    member_object[CodeInspector.RELATION_MODULE]=member_package

            else:
                if not member_module_name in imported_modules:
                    imported_modules.append(member_module_name)
                member_object[CodeInspector.RELATION]=CodeInspector.RELATION_IMPORTS
                member_object[CodeInspector.RELATION_MODULE]=member_module_name
                if member_object_type == CodeInspector.CLASS_INSTANCE:
                    member_object[CodeInspector.RELATION]=CodeInspector.RELATION_MODULE_INSTANCE
                logger.debug(f"Module {object_module_name}, imports {member_name} from {member_module_name}, type {member_object_type}")
                continue

        # try to identify missing relations from imports
        logger.debug(f"Module {object_module_name}, imported modules: {imported_modules}")

        for member_name, member_object in members.items():
            if member_object.get(CodeInspector.RELATION):
                continue

            module_ref = None
            module_is_syspath = False
            for imported_module in imported_modules:
                module_variables = list(sys.modules[imported_module].__dict__)
                # check if module variable belongs to a base python module
                # assumes it will be a library module instead if not found
                if member_name in module_variables:
                    logger.debug(f"Module {object_module_name}, Member {member_name} was found in module {imported_module}")
                    file_ref_path = Path(sys.modules[imported_module].__file__).parent
                    is_syspath = CodeInspector.is_pythonlib_subpath(file_ref_path)
                    if not module_ref:
                        module_ref = imported_module
                        logger.debug(f"Module {object_module_name}, Referencing Member {member_name} to module {imported_module}")

                    if is_syspath is True and module_ref is not None:
                        module_is_syspath = True
                        logger.debug(f"Module {object_module_name}, imported Module {imported_module} is in syspath, referencing {member_name} to it")
                        module_ref = imported_module

            logger.debug(f"Module {object_module_name}, Member {member_name} from Module {module_ref}, syspath:{module_is_syspath}")

            if module_ref:
                member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPORTS
                member_object[CodeInspector.RELATION_MODULE] = module_ref

            if not member_object.get(CodeInspector.RELATION):
                # finally, check if there are objects implemented in module itself that couldn't be identified
                obj_attributes = list(object[CodeInspector.ATTRIBUTE_OBJREF].__dict__)
                if member_name in obj_attributes:
                    member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPLEMENTS
                    member_object[CodeInspector.RELATION_MODULE] = object_module_name
                    logger.debug(f"Module {object_module_name}, Member {member_name} (type {member_object_type}) is implemented in Module")

            if not member_object.get(CodeInspector.RELATION):
                logger.warning(f"Couldn't assign a module relation of member {member_name}, type {member_object_type}")
                
        return module_object            

if __name__ == "__main__":
    loglevel=logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")

    # TODO get superclass location of a method
    #mysubclass_obj = MySubClass()
    #info_mysubclass_obj = CodeInspector().inspect_object(mysubclass_obj)

    # info = CodeInspector().inspect_object(MySubClass)
    # info = CodeInspector().inspect_object(module_myclass)
    #myclass = MyClass01()
    # object_info=CodeInspector().inspect_object(MyClass01)
    #object_info=CodeInspector().inspect_object(module_myclass)
    #external_class=CodeInspector().inspect_object(object_info['members']['ExternalClass']["objref"])
    #class_info=object_info['members']['ExternalClass']["objref"]
    #external_class_instance=class_info()
#    object_info=CodeInspector().inspect_object(myclass)
    pass
#    InspectTest().inspect_class()
#    for object attributes the object need to be instanciated

# Testing inspect of a module
    info_module_myclass = CodeInspector().inspect_object(module_myclass)
    meta_module_myclass =  CodeInspector.inspect_module(info_module_myclass)
    pass
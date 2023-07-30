""" testing the inspect module """
import inspect
from inspect import Attribute
import hashlib

# sys.path sys.modules
import os
import sys
# import types
import logging
from pathlib import Path
#from sample_inspect.module_loader import ModuleLoader
from module_loader import ModuleLoader
from my_package import module_external
from my_package import module_myclass
from my_package.module_myclass import MyClass01
from my_package.module_myclass import MySubClass

logger = logging.getLogger(__name__)

class CodeInspector():

    STATIC="static"
    INSTANCE="instance"
    MODULE = "module"
    FUNCTION = "function"
    PRIMITIVE = "primitive"
    METHOD = "method"
    RELATION = "relation"
    RELATION_IMPLEMENTS = "implements"
    RELATION_IMPORTS = "imports"
    RELATION_MODULE_INSTANCE = "module_instance" # any type of things instanciated on module level
    RELATION_MODULE = "relation_module" # referred module
    CLASS_METHODS="class_methods"
    INSTANCE_METHODS="instance_methods"
    CLASS_VARIABLES="class_variables"
    INSTANCE_VARIABLES="instance_variables"
    IMPLEMENTED_CLASSES="implemented_classes"
    IMPORTED_CLASSES="imported_classes"

    KEY="key"
    KEY_DICT="key_dict"
    CLASS = "class"
    CLASS_INSTANCE = "class_instance"
    BUILTIN = "builtin"
    OBJECT="object"
    MEMBERS="members"
    GETSETDESCRIPTOR = "getsetdescriptor"
    ISMEMBERDESCRIPTOR = "ismember"
    ATTRIBUTE_SUPERCLASS = "superclass"
    ATTRIBUTE_SUPERCLASS_NAME = "superclass_name"
    ATTRIBUTE_SUPERCLASS_TYPE= "superclass_type"
    ATTRIBUTE_SUPERCLASS_MODULE= "superclass_module"
    ATTRIBUTE_SUPERCLASS_PACKAGE= "superclass_package"

    ATTRIBUTE_OBJECTTYPE = "object_type"
    ATTRIBUTE_TYPECLASS = "typeclass"
    ATTRIBUTE_IS_INSTANCE = "is_instance"
    ATTRIBUTE_IS_SYSMODULE = "is_sysmodule"
    ATTRIBUTE_SIGNATURE = "signature"
    ATTRIBUTE_SCOPE = "scope"
    ATTRIBUTE__NAME__="__name__"
    ATTRIBUTE_CLASS_NAME="class_name"
    ATTRIBUTE__MODULE__="__module__"
    ATTRIBUTE__FILE__="__file__"
    ATTRIBUTE__DOC__="__doc__"
    ATTRIBUTE__PACKAGE__="__package__"
    ATTRIBUTE_NAME="name"
    ATTRIBUTE_MODULE="module"
    ATTRIBUTE_FILE="file"
    ATTRIBUTE_DOC="doc"
    ATTRIBUTE_PACKAGE="package"
    ATTRIBUTE_OBJREF="objref"
    ATTRIBUTES_META = "attributes_meta"


    # mapping attributes in attribute map
    ATTRIBUTE_MAP = {
        ATTRIBUTE__NAME__ : ATTRIBUTE_NAME,
        ATTRIBUTE__MODULE__ : ATTRIBUTE_MODULE,
        ATTRIBUTE__FILE__:  ATTRIBUTE_FILE,
        ATTRIBUTE__DOC__ : ATTRIBUTE_DOC,
        ATTRIBUTE__PACKAGE__ : ATTRIBUTE_PACKAGE
    }

    KEY_DICT_ATTS= [ ATTRIBUTE_OBJECTTYPE,
                     ATTRIBUTE_TYPECLASS,
                     ATTRIBUTE__PACKAGE__,
                     ATTRIBUTE__MODULE__,
                     ATTRIBUTE_CLASS_NAME,
                     ATTRIBUTE__NAME__,
                     ]

    # attribtue list for analysis dictionary
    ATTRIBUTE_LIST = [
        # generic
        KEY,
        KEY_DICT,
        ATTRIBUTE__FILE__,
        ATTRIBUTE__DOC__,
        # module atts
        ATTRIBUTE_IS_SYSMODULE,
        RELATION,
        RELATION_MODULE,
        # class atts
        ATTRIBUTE_SUPERCLASS,
        ATTRIBUTE_IS_INSTANCE,
        # functions
        ATTRIBUTE_SIGNATURE,
    ]

    MEMBER_PRIVATE_ATTRIBUTES=[ATTRIBUTE__NAME__,ATTRIBUTE__MODULE__,
                               ATTRIBUTE__PACKAGE__,ATTRIBUTE__DOC__,
                               ATTRIBUTE__FILE__]

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
    def _get_attributes_dict(obj:dict):
        """ adds properties to object props """

        attributes_dict = {}

        # first process key_dict
        obj_key_dict = obj.get(CodeInspector.KEY_DICT,{})
        for att in CodeInspector.KEY_DICT_ATTS:
            key = CodeInspector.ATTRIBUTE_MAP.get(att,att)
            value = obj_key_dict.get(att)
            if value is not None:
                attributes_dict[key] = value

        # then process other attribute
        for att in CodeInspector.ATTRIBUTE_LIST:
            key = CodeInspector.ATTRIBUTE_MAP.get(att,att)
            value = obj.get(att)

            if value is not None:
                attributes_dict[key] = value

        # get key dict / map
        return attributes_dict

    @staticmethod
    def is_pythonlib_subpath(p_path):
        """ checks if file path is subpath of python system path """
        is_subpath=[False]
        path_ref = Path(p_path)
        # convert to path
        if os.path.isfile(path_ref):
            path_ref = Path(path_ref).parent

        if not path_ref.is_dir():
            logger.warning(f"Path {str(path_ref)} is not a directory")
            return
        p=os.path.realpath(path_ref)
        python_syspaths = [os.path.realpath(sys.base_exec_prefix),os.path.realpath(sys.exec_prefix)]
        for python_syspath in python_syspaths:
            is_subpath.append(python_syspath == p or p.startswith(python_syspath+os.sep))
        return any(is_subpath)

    @staticmethod
    def get_object_key(key_dict):
        """ constructs an obkect key from key dict  """
        key_list=[]
        for att in CodeInspector.KEY_DICT_ATTS:
            value= key_dict.get(att,"NO_ATTRIBUTE_"+att)
            if not value:
                value = "NO_ATTRIBUTE_"+att
            key_list.append(value)
        return ":".join(key_list)

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
                if object_type == CodeInspector.CLASS:
                    superclasses = inspect.getmro(object)
                elif object_type == CodeInspector.CLASS_INSTANCE:
                    superclasses = inspect.getmro(object.__class__)
                if len(superclasses) > 2: # superclass is always object
                    object_props[CodeInspector.ATTRIBUTE_SUPERCLASS] = superclasses[1]
            except AttributeError as e:
                logger.warning(f"No superclass found, error {e}")

        # get attributes of interest
        for att in CodeInspector.MEMBER_PRIVATE_ATTRIBUTES:
            if hasattr(object,att):
                object_props[att]=getattr(object,att)
                if att == CodeInspector.ATTRIBUTE__FILE__:
                    object_props[CodeInspector.ATTRIBUTE_IS_SYSMODULE] = CodeInspector.is_pythonlib_subpath(object_props[att])
        object_props[CodeInspector.ATTRIBUTE_OBJECTTYPE]=object_type

        # now check method /( object signatures ) if there are any
        signature_dict = {}
        try:
            # todo use get annotations method instead of attributes
            signature_dict = object.__annotations__
            for param,value in signature_dict.items():
                signature_dict[param]=value.__name__
            object_props[CodeInspector.ATTRIBUTE_SIGNATURE]=signature_dict
        except AttributeError:
            logger.warning(f"couldn't get annotations for object {object_props.get(CodeInspector.__new__)}")
            pass

        # construct a key:
        object_type = object_props.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        object_type_class = object.__class__.__name__
        object_package = object_props.get(CodeInspector.ATTRIBUTE__PACKAGE__)
        object_module = object_props.get(CodeInspector.ATTRIBUTE__MODULE__)
        object_class = None
        object_name = object_props.get(CodeInspector.ATTRIBUTE__NAME__)

        # special cases
        if object_type == CodeInspector.MODULE:
            object_module = object_name
        elif object_type == CodeInspector.CLASS_INSTANCE:
            class_ref = object.__class__
            object_class = class_ref.__name__
            object_module = class_ref.__module__
            object_name = object_class
        elif object_type == CodeInspector.CLASS:
            object_class = object.__name__

        # try to get package from module
        if object_module:
            try:
                object_package = sys.modules[object_module].__package__
            except:
                logger.warn(f"couldn't get package from module {object_module}")
                object_package = None

        # construct object key: <OBJECT_TYPE>:<OBJECT_PACKAGE>:<OBJECT_MODULE>:<OBJECT_CLASS>:<OBJECT_NAME>


        # key = ":".join([object_type,object_type_class, object_package,object_module,object_class,object_name])
        key_dict = {    CodeInspector.ATTRIBUTE_OBJECTTYPE:object_type,
                        CodeInspector.ATTRIBUTE_TYPECLASS:object_type_class,
                        CodeInspector.ATTRIBUTE__PACKAGE__:object_package,
                        CodeInspector.ATTRIBUTE__MODULE__:object_module,
                        CodeInspector.ATTRIBUTE_CLASS_NAME:object_class,
                        CodeInspector.ATTRIBUTE__NAME__:object_name
        }
        object_props[CodeInspector.KEY_DICT] = key_dict
        object_props[CodeInspector.KEY] = CodeInspector.get_object_key(key_dict)
        object_props[CodeInspector.ATTRIBUTE_OBJREF]=object

        return object_props

    def __init__(self):
        pass

    def inspect_object(self,object):
        """  Get Object Information supports both objects and
             object instances (self attributes are only found in Instances) """

        object_props = CodeInspector.get_object_attributes(object)

        # create an obbject key separate by colons
        module=object_props.get(CodeInspector.ATTRIBUTE__MODULE__)
        type=object_props.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        key=object_props.get(CodeInspector.KEY)

        if type == CodeInspector.CLASS_INSTANCE:
            instance_variables = vars(object)
        elif type == CodeInspector.MODULE:
            module = CodeInspector.MODULE
        else:
            instance_variables = []

        try:
            name=key[CodeInspector.ATTRIBUTE__NAME__]
        except Exception as e:
            name=type

        members_dict ={}
        members_list = inspect.getmembers(object)

        for member_name, member_object in members_list:
            is_instance = None
            if member_name.startswith("__"):
                continue
            member_props = CodeInspector.get_object_attributes(member_object)
            member_props[CodeInspector.ATTRIBUTE__NAME__]=member_name
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
            member_props[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(member_props)
            members_dict[member_name]=member_props

        key=object_props.get(CodeInspector.KEY)
        key_dict=object_props.get(CodeInspector.KEY_DICT)
        object_props[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(object_props)
        # TODO get superclass attribute
        return { CodeInspector.KEY:key,
                 CodeInspector.KEY_DICT:key_dict,
                 CodeInspector.OBJECT:object_props,
                 CodeInspector.MEMBERS:members_dict
        }

    @staticmethod
    def _get_class_info_from_module(module_info:dict):
        """ gets class info from module """
        out_dict = {}

        module_object = module_info[CodeInspector.OBJECT]
        module_name = module_object.get(CodeInspector.ATTRIBUTE__NAME__)
        logger.info(f"Get Classes from module {module_name}")

        class_infos_dict = { CodeInspector.INSTANCE: {},
                             CodeInspector.CLASS: {} }
        members_dict = module_info.get(CodeInspector.MEMBERS)
        class_types = [CodeInspector.CLASS,CodeInspector.CLASS_INSTANCE]
        for member_name, member_dict in members_dict.items():
            object_type = member_dict.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            if not object_type in class_types:
                continue
            object = member_dict.get(CodeInspector.ATTRIBUTE_OBJREF)
            # try to instanciate to class instance to get instance attributes
            info_class_instance = None
            # check class
            if object_type == CodeInspector.CLASS:
                object_class = object
                try:
                    logger.debug(f"Get object instance for Class {member_name}")
                    # try to get instance from class to get instance variables
                    object_instance = member_dict.get(CodeInspector.ATTRIBUTE_OBJREF)()
                except:
                    object_instance = None
                    logger.debug(f"Could not get object instance, using Class definition of {member_name}")
            # check class instance
            else:
                logger.debug(f"Anaylzing object Class instance {member_name}")
                object_instance = member_dict.get(CodeInspector.ATTRIBUTE_OBJREF)
                # try to get class from object instance
                try:
                    object_class = object_instance.__class__
                except Exception as e:
                    object_class = None
                    logger.warning(f"Couldn't retreieve class from class instance {member_name}")

            objects = [object_class,object_instance]
            for obj in objects:
                metainfo =  CodeInspector().inspect_object(obj)
                key = metainfo.get(CodeInspector.KEY)
                out_dict[key]=metainfo
            # ToDO get object props in one dictionary
        return  out_dict

    @staticmethod
    def _get_module_info(module_object):
        """ analyses module object """

        object = module_object.get(CodeInspector.OBJECT)
        if not object:
            logger.warning("Passed object may not be valid object info")
            return
        if not object[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.MODULE:
            logger.warning("Passed object is not a module")
            return
        object_module_name=object.get(CodeInspector.ATTRIBUTE__NAME__)
        object_module_package=object.get(CodeInspector.ATTRIBUTE__PACKAGE__)

        # check if module is a module somewhere in syspath
        is_syspath = CodeInspector.is_pythonlib_subpath(Path(sys.modules[object_module_name].__file__))
        object[CodeInspector.ATTRIBUTE_IS_SYSMODULE] = is_syspath

        object[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(object)


        members = module_object.get(CodeInspector.MEMBERS)
        logger.info(f"Analyzing module {object_module_name} (Package {object_module_package})")

        # get list of modules as fallback when some attributes weren't found
        imported_modules=[]

        for member_name, member_object in members.items():
            member_module_name=member_object.get(CodeInspector.ATTRIBUTE__MODULE__)
            member_object_type=member_object.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            member_package=member_object.get(CodeInspector.ATTRIBUTE__PACKAGE__)
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
                    is_syspath = CodeInspector.is_pythonlib_subpath(Path(sys.modules[imported_module].__file__))

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
            # get object props in one dictionary
            member_object[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(member_object)

        return module_object

    @staticmethod
    def get_meta_dict(info_obj):
        """ gets metadata from module info  """
        meta_out = {}

        try:
            meta_out[CodeInspector.KEY] = info_obj[CodeInspector.KEY]
            obj_metadata = info_obj[CodeInspector.OBJECT][CodeInspector.ATTRIBUTES_META]
            rel = info_obj.get(CodeInspector.RELATION)
            rel_module = info_obj.get(CodeInspector.RELATION_MODULE)
            if rel and rel_module:
                obj_metadata[CodeInspector.RELATION] = rel
                obj_metadata[CodeInspector.RELATION_MODULE] = rel_module
            meta_out[CodeInspector.OBJECT] = obj_metadata


            members_dict = {}
            for member, member_info in info_obj[CodeInspector.MEMBERS].items():
                member_metadata = member_info[CodeInspector.ATTRIBUTES_META]
                # add relations
                rel = member_info.get(CodeInspector.RELATION)
                rel_module = member_info.get(CodeInspector.RELATION_MODULE)
                if rel and rel_module:
                    member_metadata[CodeInspector.RELATION] = rel
                    member_metadata[CodeInspector.RELATION_MODULE] = rel_module
                members_dict[member] = member_metadata
            meta_out[CodeInspector.MEMBERS] = members_dict
        except KeyError as e:
            logger.error(f"Key error occured, {e}")
            return {}

        return meta_out

class ObjectModelGenerator():
    """ builds the object models from code """
    KEY="KEY"
    OBJECT_TYPE="OBJECT_TYPE"
    PACKAGES="PACKAGES"
    MODULES="MODULES"
    REL_SRC="SOURCE"
    REL_TRG="TARGET"
    REL_IMPLEMENTS="REL_IMPLEMENTS"
    REL_IMPORTS="REL_IMPORTS"

    REL_INHERITS="REL_INHERITS_FROM"
    REL_IMPORTS="REL_INHERITS_FROM"

    def __init__(self) -> None:
        pass

    @staticmethod
    def create_model_from_module(module):
        """ creates model dict for modules"""

        def get_class_data(member_info):
            class_data=None
            classes_obj=[CodeInspector.CLASS,CodeInspector.CLASS_INSTANCE]
            obj_type=member_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            if not obj_type in classes_obj:
                return class_data
            objref=member_info.get(CodeInspector.ATTRIBUTE_OBJREF)
            # try to get object instance
            try:
                obj_instance = objref()
                objref=obj_instance
            except TypeError as e:
                logger.info(f"couldn't instanciate Object {objref}")
            class_data=ObjectModelGenerator.create_model_from_class(objref)
            return class_data

        out_dict={}
        imports_dict={}
        implements_dict={}
        implemented_classes={}
        imported_classes={}
        """ creates model from module """
        info_module = CodeInspector().inspect_object(module)

        module_info =  CodeInspector._get_module_info(info_module)
        module_meta_dict = CodeInspector.get_meta_dict(module_info)
        module_key = module_meta_dict.get(CodeInspector.KEY)
        module_object = module_meta_dict.get(CodeInspector.OBJECT)
        module_members =  module_meta_dict.get(CodeInspector.MEMBERS)
        obj_type=module_object[CodeInspector.ATTRIBUTE_OBJECTTYPE]
        if not obj_type == CodeInspector.MODULE:
            logger.warn(f"Object is of type {obj_type}, not module")
            return None
        out_dict[CodeInspector.KEY]=module_key
        out_dict[CodeInspector.ATTRIBUTE_NAME]=module_object[CodeInspector.ATTRIBUTE_NAME]
        out_dict[CodeInspector.ATTRIBUTE_PACKAGE]=module_object[CodeInspector.ATTRIBUTE_PACKAGE]
        out_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE]=module_object.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        out_dict[CodeInspector.OBJECT]=module_object
        out_dict[CodeInspector.MODULE]=module_object[CodeInspector.MODULE]

        for module_member_name,module_member_dict in module_members.items():
            # try to get class information
            try:
                obj_info=module_info[CodeInspector.MEMBERS][module_member_name]
                cls_data=get_class_data(obj_info)
            except (KeyError,TypeError,NameError) as e:
                logger.warning(f"Couldn't get class information from {module_member_name}, {e}")
            if module_member_dict.get(CodeInspector.RELATION)==CodeInspector.RELATION_IMPLEMENTS:
                implements_dict[module_member_name]=module_member_dict
                implements_dict[module_member_name][CodeInspector.MODULE]=module_object[CodeInspector.MODULE]
                if cls_data:
                    implemented_classes[module_member_name]=cls_data
            elif module_member_dict.get(CodeInspector.RELATION)==CodeInspector.RELATION_IMPORTS:
                imports_dict[module_member_name]=module_member_dict
                imports_dict[module_member_name][CodeInspector.MODULE]=module_member_dict[CodeInspector.RELATION_MODULE]
                if cls_data:
                    imported_classes[module_member_name]=cls_data

        out_dict[CodeInspector.RELATION_IMPLEMENTS]=implements_dict
        out_dict[CodeInspector.RELATION_IMPORTS]=imports_dict
        out_dict[CodeInspector.IMPORTED_CLASSES]=imported_classes
        out_dict[CodeInspector.IMPLEMENTED_CLASSES]=implemented_classes
        return out_dict

    @staticmethod
    def create_model_from_class(cls):
        """ creates model dict for class"""
        methods = [CodeInspector.METHOD,CodeInspector.FUNCTION]

        out_dict={}
        instance_methods_dict={}
        instance_variables_dict={}
        class_methods_dict={}
        class_variables_dict={}

        myclass_info = CodeInspector().inspect_object(cls)
        class_meta_dict = CodeInspector.get_meta_dict(myclass_info)
        class_key = class_meta_dict.get(CodeInspector.KEY)
        class_object = class_meta_dict.get(CodeInspector.OBJECT)
        class_members =  class_meta_dict.get(CodeInspector.MEMBERS)
        class_obj_type=class_object[CodeInspector.ATTRIBUTE_OBJECTTYPE]
        if not class_obj_type in [CodeInspector.CLASS, CodeInspector.CLASS_INSTANCE]:
            logger.warn(f"Object is of type {class_obj_type}, not class or class instance")
            return None
        out_dict[CodeInspector.KEY]=class_key
        out_dict[CodeInspector.ATTRIBUTE_NAME]=class_object[CodeInspector.ATTRIBUTE_NAME]
        out_dict[CodeInspector.ATTRIBUTE_PACKAGE]=class_object[CodeInspector.ATTRIBUTE_PACKAGE]
        out_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE]=class_object.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)

        # get superclass
        superclass_obj=class_object.get(CodeInspector.ATTRIBUTE_SUPERCLASS)
        if superclass_obj:
            superclass_info = CodeInspector().inspect_object(superclass_obj)
            superclass_meta_dict = CodeInspector.get_meta_dict(superclass_info)
            superclass_obj_meta=superclass_meta_dict[CodeInspector.OBJECT]
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_NAME]=superclass_obj_meta.get(CodeInspector.ATTRIBUTE_NAME)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_MODULE]=superclass_obj_meta.get(CodeInspector.ATTRIBUTE_MODULE)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_PACKAGE]=superclass_obj_meta.get(CodeInspector.ATTRIBUTE_PACKAGE)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_TYPE]=superclass_obj_meta.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        else:
            superclass_meta_dict = None

        out_dict[CodeInspector.OBJECT]=class_object
        out_dict[CodeInspector.MODULE]=class_object[CodeInspector.MODULE]
        for class_member_name,class_member_dict in class_members.items():
            is_instance=class_member_dict.get(CodeInspector.ATTRIBUTE_IS_INSTANCE)
            object_type=class_member_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE]
            package=class_object[CodeInspector.ATTRIBUTE_PACKAGE]
            module=class_object[CodeInspector.ATTRIBUTE_MODULE]
            out_dict_current=None
            if is_instance is True:
                if object_type in methods:
                    out_dict_current=instance_methods_dict
                    logger.debug(f"Adding instance method {class_member_name}")
                else:
                    out_dict_current=instance_variables_dict
                    logger.debug(f"Adding instance variable {class_member_name}")
            else:
                if object_type in methods:
                    out_dict_current=class_methods_dict
                    logger.debug(f"Adding class method {class_member_name}")
                else:
                    out_dict_current=class_variables_dict
                    logger.debug(f"Adding class variable {class_member_name}")
            if out_dict_current is None:
                continue
            out_dict_current[class_member_name]=class_member_dict
            out_dict_current[class_member_name][CodeInspector.MODULE]=module
            out_dict_current[class_member_name][CodeInspector.ATTRIBUTE_PACKAGE]=package
            out_dict_current[class_member_name][CodeInspector.ATTRIBUTE_OBJECTTYPE]=object_type
        out_dict[CodeInspector.INSTANCE_METHODS]=instance_methods_dict
        out_dict[CodeInspector.INSTANCE_VARIABLES]=instance_variables_dict
        out_dict[CodeInspector.CLASS_METHODS]=class_methods_dict
        out_dict[CodeInspector.CLASS_VARIABLES]=class_variables_dict
        out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS]=superclass_meta_dict
        return out_dict

    @staticmethod
    def create_model_from_path(p):
        """ creates dict of modules / classes from a given file path """
        if not os.path.isdir(p):
            logger.warn(f"{p} is not a valid path")
            return
        logger.info(f"Read modules from Path {p}")
        module_loader = ModuleLoader(p)
        module_dict = module_loader.get_modules()
        out_module_model={}
        for module_name,module_info in module_dict.items():
            logger.info(f"get model information for module {module_name}")
            model = ObjectModelGenerator.create_model_from_module(module_info)
            out_module_model[module_name]=model
            pass
        return out_module_model

class ObjectModel():
    """ creates Object model from model """
    ROOT="ROOT"
    PARENT="PARENT"
    MODULE="MODULE"
    MODULE_SHORT="MODULE_SHORT"
    PACKAGE="PACKAGE"
    HASH="HASH"
    PARENT="PARENT"
    TYPE="TYPE"

    def __init__(self,p:str) -> None:
        """ right now model is created from path """
        self._module_model=ObjectModelGenerator.create_model_from_path(p)
        self._module_tree={}
        self._create_package_hierarchy()

    @property
    def module_tree(self):
        """ module tree property """
        return self._module_tree        

    def _create_package_hierarchy(self):
        """ creates package hierarchy """
        logger.info("Create Package Hierarchy")
        module_tree={}

        for full_module_name in self._module_model.keys():
            module_parts=full_module_name.split(".")
            module_name=module_parts[-1]
            hash_module=ObjectModel.get_hash(full_module_name)
            module_packages=module_parts[:-1]
            level=len(module_packages)
            # add module package tree 
            for i in range(level):
                parent_package_name=".".join(module_packages[:i])
                package_name=".".join(module_packages[:i+1])
                if not parent_package_name:
                    parent_package_name = ObjectModel.ROOT
                hash_parent=ObjectModel.get_hash(parent_package_name)
                hash_package=ObjectModel.get_hash(package_name)
                # add parent package
                if not module_tree.get(hash_parent):
                    parent_dict={ObjectModel.HASH:hash_parent,
                                 ObjectModel.PACKAGE:parent_package_name,
                                 ObjectModel.TYPE:ObjectModel.PACKAGE}
                    module_tree[hash_parent]=parent_dict
                # add containing package
                if not module_tree.get(hash_package):
                    package_dict={ObjectModel.HASH:hash_package,
                                 ObjectModel.PACKAGE:package_name,
                                 ObjectModel.TYPE:ObjectModel.PACKAGE,
                                 ObjectModel.PARENT:hash_parent}
                    module_tree[hash_package]=package_dict
            
            # add module to dict 
            if level == 0:
                package=ObjectModel.ROOT                
            else:
                package=".".join(module_packages)
            
            hash_package=ObjectModel.get_hash(package)
            module_dict={ ObjectModel.HASH:hash_module,
                          ObjectModel.MODULE:full_module_name,
                          ObjectModel.MODULE_SHORT:module_name,
                          ObjectModel.PACKAGE:package,
                          ObjectModel.TYPE:ObjectModel.MODULE,
                          ObjectModel.PARENT:hash_package}
            module_tree[hash_module]=module_dict
            self._module_tree=module_tree
            
    @staticmethod
    def get_hash(s:str):
        return hashlib.md5(s.encode()).hexdigest()

if __name__ == "__main__":
    loglevel=logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")
    om = ObjectModelGenerator()
    root_path = Path(__file__).parent

    # try:
    #     om2 = ObjectModel("ddd")
    # except TypeError as e:
    #     logger.info("couldn't instanciate Object")

    # Testing inspect of a module
    if False:
        module_model=ObjectModelGenerator.create_model_from_module(module_myclass)

    if False:
        class_model=ObjectModelGenerator.create_model_from_class(MyClass01)

    if False:
        myclass01 = MyClass01()
        myclass_instance_info = CodeInspector().inspect_object(myclass01)
        myclass_info = CodeInspector().inspect_object(MyClass01)
        my_module_info = CodeInspector().inspect_object(module_myclass)

        ObjectModelGenerator.create_model_from_class(myclass01)


    # testing class metadata
    if False:
        myclass_info = CodeInspector().inspect_object(MyClass01)
        class_meta_dict = CodeInspector.get_meta_dict(myclass_info)


    if False:
        s=hashlib.md5("xxxx".encode()).hexdigest()
        pass

    # root path
    if False:
        # load the modules in my_package
        model_modules=ObjectModelGenerator.create_model_from_path(root_path)

    if True:
        om=object_modekl=ObjectModel(root_path)
        module_tree=om.module_tree
        pass

    # TODO get superclass location of a method
    #mysubclass_obj = MySubClass()
    #info_mysubclass_obj = CodeInspector().inspect_object(mysubclass_obj)
    #meta_dict = CodeInspector.get_meta_dict(info_mysubclass_obj)


    pass
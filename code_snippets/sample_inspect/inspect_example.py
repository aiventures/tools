""" testing the inspect module """

import inspect
import hashlib

# sys.path sys.modules
import copy
import os
import sys
# import types
import logging
from pathlib import Path
from datetime import datetime as DateTime

from module_loader import ModuleLoader

from my_package import module_myclass
from my_package.module_myclass import MyClass01
# from my_package import module_external
# from sample_inspect.module_loader import ModuleLoader
# from my_package.module_myclass import MySubClass
from tools.tree_util import Tree
from tools import file_module as fm


logger = logging.getLogger(__name__)


class CodeInspector():
    """ Get Code Objects """

    STATIC = "static"
    INSTANCE = "instance"
    MODULE = "module"
    FUNCTION = "function"
    PRIMITIVE = "primitive"
    ATTRIBUTE = "attribute"
    METHOD = "method"
    RETURN = "return"
    RELATION = "relation"
    RELATION_IMPLEMENTS = "implements"
    RELATION_INHERITS = "inherits"
    RELATION_IMPORTS = "imports"
    # any type of things instanciated on module level
    RELATION_MODULE_INSTANCE = "module_instance"
    RELATION_MODULE = "relation_module"  # referred module
    CLASS_METHODS = "class_methods"
    INSTANCE_METHODS = "instance_methods"
    CLASS_VARIABLES = "class_variables"
    INSTANCE_VARIABLES = "instance_variables"
    IMPLEMENTED_CLASSES = "implemented_classes"
    IMPORTED_CLASSES = "imported_classes"
    NODE_SOURCE = "node_source"
    NODE_TARGET = "node_target"

    KEY = "key"
    HASH = "hash"
    KEY_DICT = "key_dict"
    CLASS = "class"
    CLASS_INSTANCE = "class_instance"
    BUILTIN = "builtin"
    OBJECT = "object"
    MEMBERS = "members"
    GETSETDESCRIPTOR = "getsetdescriptor"
    ISMEMBERDESCRIPTOR = "ismember"
    ATTRIBUTE_SUPERCLASS = "superclass"
    ATTRIBUTE_SUPERCLASS_NAME = "superclass_name"
    ATTRIBUTE_SUPERCLASS_TYPE = "superclass_type"
    ATTRIBUTE_SUPERCLASS_MODULE = "superclass_module"
    ATTRIBUTE_SUPERCLASS_PACKAGE = "superclass_package"

    ATTRIBUTE_OBJECTTYPE = "object_type"
    ATTRIBUTE_TYPECLASS = "typeclass"
    ATTRIBUTE_IS_INSTANCE = "is_instance"
    ATTRIBUTE_IS_SYSMODULE = "is_sysmodule"
    ATTRIBUTE_SIGNATURE = "signature"
    ATTRIBUTE_SCOPE = "scope"
    ATTRIBUTE__NAME__ = "__name__"
    ATTRIBUTE_CLASS_NAME = "class_name"
    ATTRIBUTE__MODULE__ = "__module__"
    ATTRIBUTE__FILE__ = "__file__"
    ATTRIBUTE__DOC__ = "__doc__"
    ATTRIBUTE__PACKAGE__ = "__package__"
    ATTRIBUTE_NAME = "name"
    ATTRIBUTE_MODULE = "module"
    ATTRIBUTE_FILE = "file"
    ATTRIBUTE_DOC = "doc"
    ATTRIBUTE_PACKAGE = "package"
    ATTRIBUTE_OBJREF = "objref"
    ATTRIBUTES_META = "attributes_meta"

    # mapping attributes in attribute map
    ATTRIBUTE_MAP = {
        ATTRIBUTE__NAME__: ATTRIBUTE_NAME,
        ATTRIBUTE__MODULE__: ATTRIBUTE_MODULE,
        ATTRIBUTE__FILE__:  ATTRIBUTE_FILE,
        ATTRIBUTE__DOC__: ATTRIBUTE_DOC,
        ATTRIBUTE__PACKAGE__: ATTRIBUTE_PACKAGE
    }

    KEY_DICT_ATTS = [ATTRIBUTE_OBJECTTYPE,
                     ATTRIBUTE_TYPECLASS,
                     ATTRIBUTE__PACKAGE__,
                     ATTRIBUTE__MODULE__,
                     ATTRIBUTE_CLASS_NAME,
                     ATTRIBUTE__NAME__,
                     ]

    KEY_DICT_ATTS2 = [# ATTRIBUTE_OBJECTTYPE,
                      # ATTRIBUTE_TYPECLASS,
                      ATTRIBUTE__PACKAGE__,
                      ATTRIBUTE__MODULE__,
                      # ATTRIBUTE_CLASS_NAME,
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

    MEMBER_PRIVATE_ATTRIBUTES = [ATTRIBUTE__NAME__, ATTRIBUTE__MODULE__,
                                 ATTRIBUTE__PACKAGE__, ATTRIBUTE__DOC__,
                                 ATTRIBUTE__FILE__]

    TYPES = {
        MODULE: (lambda o: inspect.ismodule(o)),
        PRIMITIVE: (lambda o: getattr(o, "__dict__", None) is None),
        FUNCTION: (lambda o: inspect.isfunction(o)),
        METHOD: (lambda o: inspect.ismethod(o)),
        CLASS: (lambda o: inspect.isclass(o)),
        CLASS_INSTANCE: (lambda o: inspect.isclass(type(o))),
        ISMEMBERDESCRIPTOR: (lambda o: inspect.ismemberdescriptor(o)),
    }

    @staticmethod
    def get_hash(s: str):
        """ calculate hash """
        hash_value = hashlib.md5(s.encode()).hexdigest()
        return hash_value

    @staticmethod
    def _get_attributes_dict(obj: dict):
        """ adds properties to object props """

        attributes_dict = {}

        # first process key_dict
        obj_key_dict = obj.get(CodeInspector.KEY_DICT, {})
        for att in CodeInspector.KEY_DICT_ATTS:
            key = CodeInspector.ATTRIBUTE_MAP.get(att, att)
            value = obj_key_dict.get(att)
            if value is not None:
                attributes_dict[key] = value

        # then process other attribute
        for att in CodeInspector.ATTRIBUTE_LIST:
            key = CodeInspector.ATTRIBUTE_MAP.get(att, att)
            value = obj.get(att)
            if value is not None:
                attributes_dict[key] = value
                if att == CodeInspector.KEY:
                    attributes_dict[CodeInspector.HASH] = CodeInspector.get_hash(
                        value)

        # get key dict / map
        return attributes_dict

    @staticmethod
    def is_pythonlib_subpath(p_path):
        """ checks if file path is subpath of python system path """
        is_subpath = [False]
        path_ref = Path(p_path)
        # convert to path

        if os.path.isfile(path_ref):
            path_ref = Path(path_ref).parent

        if not path_ref.is_dir():
            logger.warning(f"Path {str(path_ref)} is not a directory")
            return
        p = os.path.realpath(path_ref)
        python_syspaths = [os.path.realpath(
            sys.base_exec_prefix), os.path.realpath(sys.exec_prefix)]
        for python_syspath in python_syspaths:
            is_subpath.append(python_syspath ==
                              p or p.startswith(python_syspath+os.sep))
        return any(is_subpath)

    @staticmethod
    def get_object_key(key_dict):
        """ constructs an obkect key from key dict  """
        key_list = []
        for att in CodeInspector.KEY_DICT_ATTS2:
            value = key_dict.get(att, "NO_ATTRIBUTE_"+att)
            if not value:
                value = "NO_ATTRIBUTE_"+att
            key_list.append(value)
        return ":".join(key_list)

    @staticmethod
    def get_type(obj):
        """ gets the object type from inspect """
        for object_type in CodeInspector.TYPES.keys():
            if CodeInspector.TYPES[object_type](obj):
                return object_type
        return None

    @staticmethod
    def get_object_attributes(obj):
        """ Gets the attributes for an object """
        # TODO check whether it is instanciated is class
        object_props = {}
        object_type = CodeInspector.get_type(obj)

        # for an object instance check if it is an instanciated class
        # if object_type not in list(InspectTest.TYPES.keys()):
        if not object_type:
            object_type = type(obj).__name__

        # check for superclass
        if object_type == CodeInspector.CLASS or object_type == CodeInspector.CLASS_INSTANCE:

            try:
                if object_type == CodeInspector.CLASS:
                    superclasses = inspect.getmro(obj)
                elif object_type == CodeInspector.CLASS_INSTANCE:
                    superclasses = inspect.getmro(obj.__class__)
                if len(superclasses) > 2:  # superclass is always object
                    object_props[CodeInspector.ATTRIBUTE_SUPERCLASS] = superclasses[1]
            except AttributeError as e:
                logger.warning(f"No superclass found, error {e}")

        # get attributes of interest
        for att in CodeInspector.MEMBER_PRIVATE_ATTRIBUTES:
            if hasattr(obj, att):
                object_props[att] = getattr(obj, att)
                if att == CodeInspector.ATTRIBUTE__FILE__:
                    object_props[CodeInspector.ATTRIBUTE_IS_SYSMODULE] = CodeInspector.is_pythonlib_subpath(
                        object_props[att])
        object_props[CodeInspector.ATTRIBUTE_OBJECTTYPE] = object_type

        # now check method /( object signatures ) if there are any
        signature_dict = {}
        try:
            signature_dict = obj.__annotations__
            for param, value in signature_dict.items():
                signature_dict[param] = value.__name__
            object_props[CodeInspector.ATTRIBUTE_SIGNATURE] = signature_dict
        except AttributeError:
            logger.warning(
                f"couldn't get annotations for object {object_props.get(CodeInspector.__new__)}")

        # construct a key:
        object_type = object_props.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        object_type_class = obj.__class__.__name__
        object_package = object_props.get(CodeInspector.ATTRIBUTE__PACKAGE__)
        object_module = object_props.get(CodeInspector.ATTRIBUTE__MODULE__)
        object_class = None
        object_name = object_props.get(CodeInspector.ATTRIBUTE__NAME__)

        # special cases
        if object_type == CodeInspector.MODULE:
            object_module = object_name
        elif object_type == CodeInspector.CLASS_INSTANCE:
            class_ref = obj.__class__
            object_class = class_ref.__name__
            object_module = class_ref.__module__
            object_name = object_class
        elif object_type == CodeInspector.CLASS:
            object_class = obj.__name__

        # try to get package from module
        if object_module:
            try:
                object_package = sys.modules[object_module].__package__
            except:
                logger.warning(
                    f"couldn't get package from module {object_module}")
                object_package = None

        # construct object key: <OBJECT_TYPE>:<OBJECT_PACKAGE>:<OBJECT_MODULE>:<OBJECT_CLASS>:<OBJECT_NAME>

        # key = ":".join([object_type,object_type_class, object_package,object_module,object_class,object_name])
        # key = object_type:__module__:__package__:__name__
        key_dict = {CodeInspector.ATTRIBUTE_OBJECTTYPE: object_type,
                    CodeInspector.ATTRIBUTE_TYPECLASS: object_type_class,
                    CodeInspector.ATTRIBUTE__PACKAGE__: object_package,
                    CodeInspector.ATTRIBUTE__MODULE__: object_module,
                    CodeInspector.ATTRIBUTE_CLASS_NAME: object_class,
                    CodeInspector.ATTRIBUTE__NAME__: object_name
                    }
        object_props[CodeInspector.KEY_DICT] = key_dict
        object_props[CodeInspector.KEY] = CodeInspector.get_object_key(
            key_dict)
        object_props[CodeInspector.ATTRIBUTE_OBJREF] = obj

        return object_props

    def __init__(self):
        pass

    def inspect_object(self, obj):
        """  Get Object Information supports both objects and
             object instances (self attributes are only found in Instances) """

        object_props = CodeInspector.get_object_attributes(obj)

        # create an obbject key separate by colons
        module = object_props.get(CodeInspector.ATTRIBUTE__MODULE__)
        objtype = object_props.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        key = object_props.get(CodeInspector.KEY)

        if objtype == CodeInspector.CLASS_INSTANCE:
            instance_variables = vars(obj)
        elif objtype == CodeInspector.MODULE:
            module = CodeInspector.MODULE
        else:
            instance_variables = []

        try:
            name = key[CodeInspector.ATTRIBUTE__NAME__]
        except Exception as e:
            name = objtype

        members_dict = {}
        members_list = inspect.getmembers(obj)

        for member_name, member_object in members_list:
            is_instance = None
            if member_name.startswith("__"):
                continue
            member_props = CodeInspector.get_object_attributes(member_object)
            member_props[CodeInspector.ATTRIBUTE__NAME__] = member_name
            # check for static or instance methods methods
            if objtype == CodeInspector.CLASS_INSTANCE:
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
            elif objtype == CodeInspector.CLASS:
                if member_props[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.FUNCTION:
                    try:
                        is_instance = not (isinstance(
                            obj.__dict__[member_name], staticmethod))
                    except Exception:
                        is_instance = None

                        logger.warning(
                            f"Couldn't find method {member_name} in Class Definition")
                # when class is parsed, instance variables are absent
                else:
                    is_instance = False

            member_props[CodeInspector.ATTRIBUTE_IS_INSTANCE] = is_instance
            member_props[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(
                member_props)
            members_dict[member_name] = member_props

        key = object_props.get(CodeInspector.KEY)
        key_dict = object_props.get(CodeInspector.KEY_DICT)
        object_props[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(
            object_props)
        return {CodeInspector.KEY: key,
                CodeInspector.KEY_DICT: key_dict,
                CodeInspector.OBJECT: object_props,
                CodeInspector.MEMBERS: members_dict
                }

    @staticmethod
    def _get_class_info_from_module(module_info: dict):
        """ gets class info from module """
        out_dict = {}

        module_object = module_info[CodeInspector.OBJECT]
        module_name = module_object.get(CodeInspector.ATTRIBUTE__NAME__)
        logger.info(f"Get Classes from module {module_name}")

        class_infos_dict = {CodeInspector.INSTANCE: {},
                            CodeInspector.CLASS: {}}
        members_dict = module_info.get(CodeInspector.MEMBERS)
        class_types = [CodeInspector.CLASS, CodeInspector.CLASS_INSTANCE]
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
                    logger.debug(
                        f"Get object instance for Class {member_name}")
                    # try to get instance from class to get instance variables
                    object_instance = member_dict.get(
                        CodeInspector.ATTRIBUTE_OBJREF)()
                except:
                    object_instance = None
                    logger.debug(
                        f"Could not get object instance, using Class definition of {member_name}")
            # check class instance
            else:
                logger.debug(f"Anaylzing object Class instance {member_name}")
                object_instance = member_dict.get(
                    CodeInspector.ATTRIBUTE_OBJREF)
                # try to get class from object instance
                try:
                    object_class = object_instance.__class__
                except Exception as e:
                    object_class = None
                    logger.warning(
                        f"Couldn't retreieve class from class instance {member_name}, {e}")

            objects = [object_class, object_instance]
            for obj in objects:
                metainfo = CodeInspector().inspect_object(obj)
                key = metainfo.get(CodeInspector.KEY)
                out_dict[key] = metainfo

        return out_dict

    @staticmethod
    def _get_module_info(module_object):
        """ analyses module object """

        obj = module_object.get(CodeInspector.OBJECT)
        if not obj:
            logger.warning("Passed object may not be valid object info")
            return
        if not obj[CodeInspector.ATTRIBUTE_OBJECTTYPE] == CodeInspector.MODULE:
            logger.warning("Passed object is not a module")
            return
        object_module_name = obj.get(CodeInspector.ATTRIBUTE__NAME__)
        object_module_package = obj.get(CodeInspector.ATTRIBUTE__PACKAGE__)

        # check if module is a module somewhere in syspath
        is_syspath = CodeInspector.is_pythonlib_subpath(
            Path(sys.modules[object_module_name].__file__))
        obj[CodeInspector.ATTRIBUTE_IS_SYSMODULE] = is_syspath

        obj[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(
            obj)

        members = module_object.get(CodeInspector.MEMBERS)
        logger.info(
            f"Analyzing module {object_module_name} (Package {object_module_package})")

        # get list of modules as fallback when some attributes weren't found
        imported_modules = []

        for member_name, member_object in members.items():
            member_module_name = member_object.get(
                CodeInspector.ATTRIBUTE__MODULE__)
            member_object_type = member_object.get(
                CodeInspector.ATTRIBUTE_OBJECTTYPE)
            member_package = member_object.get(
                CodeInspector.ATTRIBUTE__PACKAGE__)
            # if module name is present, check for implementation in analysed module
            if member_module_name == object_module_name:
                member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPLEMENTS
                member_object[CodeInspector.RELATION_MODULE] = object_module_name
                logger.debug(
                    f"Module {object_module_name}, implements member {member_name}, type {member_object_type}")
                continue

            # determine module relations
            if member_module_name is None:
                # import of a module
                if member_object_type == CodeInspector.MODULE and member_package is not None:
                    member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPORTS
                    member_object[CodeInspector.RELATION_MODULE] = member_package

            else:
                if not member_module_name in imported_modules:
                    imported_modules.append(member_module_name)
                member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPORTS
                member_object[CodeInspector.RELATION_MODULE] = member_module_name
                if member_object_type == CodeInspector.CLASS_INSTANCE:
                    member_object[CodeInspector.RELATION] = CodeInspector.RELATION_MODULE_INSTANCE
                logger.debug(
                    f"Module {object_module_name}, imports {member_name} from {member_module_name}, type {member_object_type}")
                continue
        # try to identify missing relations from imports
        logger.debug(
            f"Module {object_module_name}, imported modules: {imported_modules}")

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
                    logger.debug(
                        f"Module {object_module_name}, Member {member_name} was found in module {imported_module}")
                    is_syspath = CodeInspector.is_pythonlib_subpath(
                        Path(sys.modules[imported_module].__file__))

                    if not module_ref:
                        module_ref = imported_module
                        logger.debug(
                            f"Module {object_module_name}, Referencing Member {member_name} to module {imported_module}")

                    if is_syspath is True and module_ref is not None:
                        module_is_syspath = True
                        logger.debug(
                            f"Module {object_module_name}, imported Module {imported_module} is in syspath, referencing {member_name} to it")
                        module_ref = imported_module

            logger.debug(
                f"Module {object_module_name}, Member {member_name} from Module {module_ref}, syspath:{module_is_syspath}")

            if module_ref:
                member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPORTS
                member_object[CodeInspector.RELATION_MODULE] = module_ref

            if not member_object.get(CodeInspector.RELATION):
                # finally, check if there are objects implemented in module itself that couldn't be identified
                obj_attributes = list(
                    obj[CodeInspector.ATTRIBUTE_OBJREF].__dict__)
                if member_name in obj_attributes:
                    member_object[CodeInspector.RELATION] = CodeInspector.RELATION_IMPLEMENTS
                    member_object[CodeInspector.RELATION_MODULE] = object_module_name
                    logger.debug(
                        f"Module {object_module_name}, Member {member_name} (type {member_object_type}) is implemented in Module")

            if not member_object.get(CodeInspector.RELATION):
                logger.warning(
                    f"Couldn't assign a module relation of member {member_name}, type {member_object_type}")
            # get object props in one dictionary
            member_object[CodeInspector.ATTRIBUTES_META] = CodeInspector._get_attributes_dict(
                member_object)

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
    KEY = "KEY"
    OBJECT_TYPE = "OBJECT_TYPE"
    PACKAGES = "PACKAGES"
    MODULES = "MODULES"
    REL_SRC = "SOURCE"
    REL_TRG = "TARGET"
    REL_IMPLEMENTS = "REL_IMPLEMENTS"
    REL_IMPORTS = "REL_IMPORTS"

    REL_INHERITS = "REL_INHERITS_FROM"
    REL_IMPORTS = "REL_INHERITS_FROM"

    def __init__(self) -> None:
        pass

    @staticmethod
    def create_model_from_module(module,model_instance:bool=False):
        """ creates model dict for modules"""

        def get_class_data(member_info):
            class_data = None
            classes_obj = [CodeInspector.CLASS, CodeInspector.CLASS_INSTANCE]
            obj_type = member_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            if not obj_type in classes_obj:
                return class_data
            objref = member_info.get(CodeInspector.ATTRIBUTE_OBJREF)
            # try to get object instance
            if model_instance:
                try:
                    obj_instance = objref()
                    objref = obj_instance
                except TypeError as e:
                    logger.info(f"couldn't instanciate Object {objref}, {e}")
            class_data = ObjectModelGenerator.create_model_from_class(objref)
            return class_data

        out_dict = {}
        imports_dict = {}
        implements_dict = {}
        implemented_classes = {}
        imported_classes = {}
        """ creates model from module """
        info_module = CodeInspector().inspect_object(module)

        module_info = CodeInspector._get_module_info(info_module)
        module_meta_dict = CodeInspector.get_meta_dict(module_info)
        module_object = module_meta_dict.get(CodeInspector.OBJECT)
        module_key = module_object.get(CodeInspector.MODULE)
        if module_key:
            module_hash = CodeInspector.get_hash(module_key)
        else:
            module_hash = "NO_KEY_FOUND"

        module_members = module_meta_dict.get(CodeInspector.MEMBERS)
        obj_type = module_object[CodeInspector.ATTRIBUTE_OBJECTTYPE]
        if not obj_type == CodeInspector.MODULE:
            logger.warning(f"Object is of type {obj_type}, not module")
            return None
        out_dict[CodeInspector.KEY] = module_key
        # TODO
        out_dict[CodeInspector.HASH] = module_hash
        out_dict[CodeInspector.ATTRIBUTE_NAME] = module_object[CodeInspector.ATTRIBUTE_NAME]
        out_dict[CodeInspector.ATTRIBUTE_PACKAGE] = module_object[CodeInspector.ATTRIBUTE_PACKAGE]
        out_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE] = module_object.get(
            CodeInspector.ATTRIBUTE_OBJECTTYPE)
        out_dict[CodeInspector.OBJECT] = module_object
        out_dict[CodeInspector.MODULE] = module_object[CodeInspector.MODULE]

        for module_member_name, module_member_dict in module_members.items():
            # try to get class information
            try:
                obj_info = module_info[CodeInspector.MEMBERS][module_member_name]
                cls_data = get_class_data(obj_info)
            except (KeyError, TypeError, NameError) as e:
                logger.warning(
                    f"Couldn't get class information from {module_member_name}, {e}")
            relation = module_member_dict.get(CodeInspector.RELATION)
            # TODO check for module instance
            if relation == CodeInspector.RELATION_IMPLEMENTS or relation == CodeInspector.RELATION_MODULE_INSTANCE:
                implements_dict[module_member_name] = module_member_dict
                implements_dict[module_member_name][CodeInspector.MODULE] = module_object[CodeInspector.MODULE]
                if cls_data:
                    implemented_classes[module_member_name] = cls_data
            elif relation == CodeInspector.RELATION_IMPORTS:
                imports_dict[module_member_name] = module_member_dict
                imports_dict[module_member_name][CodeInspector.MODULE] = module_member_dict[CodeInspector.RELATION_MODULE]
                if cls_data:
                    imported_classes[module_member_name] = cls_data

        out_dict[CodeInspector.RELATION_IMPLEMENTS] = implements_dict
        out_dict[CodeInspector.RELATION_IMPORTS] = imports_dict
        out_dict[CodeInspector.IMPORTED_CLASSES] = imported_classes
        out_dict[CodeInspector.IMPLEMENTED_CLASSES] = implemented_classes
        return out_dict

    @staticmethod
    def create_model_from_class(cls):
        """ creates model dict for class"""
        methods = [CodeInspector.METHOD, CodeInspector.FUNCTION]

        out_dict = {}
        instance_methods_dict = {}
        instance_variables_dict = {}
        class_methods_dict = {}
        class_variables_dict = {}

        myclass_info = CodeInspector().inspect_object(cls)
        class_meta_dict = CodeInspector.get_meta_dict(myclass_info)
        class_key = class_meta_dict.get(CodeInspector.KEY)
        class_object = class_meta_dict.get(CodeInspector.OBJECT)
        class_members = class_meta_dict.get(CodeInspector.MEMBERS)
        class_obj_type = class_object[CodeInspector.ATTRIBUTE_OBJECTTYPE]
        if not class_obj_type in [CodeInspector.CLASS, CodeInspector.CLASS_INSTANCE]:
            logger.warning(
                f"Object is of type {class_obj_type}, not class or class instance")
            return None
        out_dict[CodeInspector.KEY] = class_key
        if class_key:
            out_dict[CodeInspector.HASH] = CodeInspector.get_hash(class_key)
        out_dict[CodeInspector.ATTRIBUTE_NAME] = class_object[CodeInspector.ATTRIBUTE_NAME]
        out_dict[CodeInspector.ATTRIBUTE_PACKAGE] = class_object[CodeInspector.ATTRIBUTE_PACKAGE]
        out_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE] = class_object.get(
            CodeInspector.ATTRIBUTE_OBJECTTYPE)

        # get superclass
        superclass_obj = class_object.get(CodeInspector.ATTRIBUTE_SUPERCLASS)
        if superclass_obj:
            superclass_info = CodeInspector().inspect_object(superclass_obj)
            superclass_meta_dict = CodeInspector.get_meta_dict(superclass_info)
            superclass_obj_meta = superclass_meta_dict[CodeInspector.OBJECT]
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_NAME] = superclass_obj_meta.get(
                CodeInspector.ATTRIBUTE_NAME)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_MODULE] = superclass_obj_meta.get(
                CodeInspector.ATTRIBUTE_MODULE)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_PACKAGE] = superclass_obj_meta.get(
                CodeInspector.ATTRIBUTE_PACKAGE)
            out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS_TYPE] = superclass_obj_meta.get(
                CodeInspector.ATTRIBUTE_OBJECTTYPE)
        else:
            superclass_meta_dict = None

        out_dict[CodeInspector.OBJECT] = class_object
        out_dict[CodeInspector.MODULE] = class_object[CodeInspector.MODULE]
        for class_member_name, class_member_dict in class_members.items():
            is_instance = class_member_dict.get(
                CodeInspector.ATTRIBUTE_IS_INSTANCE)
            object_type = class_member_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE]
            package = class_object[CodeInspector.ATTRIBUTE_PACKAGE]
            module = class_object[CodeInspector.ATTRIBUTE_MODULE]
            out_dict_current = None
            if is_instance is True:
                if object_type in methods:
                    out_dict_current = instance_methods_dict
                    logger.debug(f"Adding instance method {class_member_name}")
                else:
                    out_dict_current = instance_variables_dict
                    logger.debug(
                        f"Adding instance variable {class_member_name}")
            else:
                if object_type in methods:
                    out_dict_current = class_methods_dict
                    logger.debug(f"Adding class method {class_member_name}")
                else:
                    out_dict_current = class_variables_dict
                    logger.debug(f"Adding class variable {class_member_name}")
            if out_dict_current is None:
                continue
            out_dict_current[class_member_name] = class_member_dict
            out_dict_current[class_member_name][CodeInspector.MODULE] = module
            out_dict_current[class_member_name][CodeInspector.ATTRIBUTE_PACKAGE] = package
            out_dict_current[class_member_name][CodeInspector.ATTRIBUTE_OBJECTTYPE] = object_type
        out_dict[CodeInspector.INSTANCE_METHODS] = instance_methods_dict
        out_dict[CodeInspector.INSTANCE_VARIABLES] = instance_variables_dict
        out_dict[CodeInspector.CLASS_METHODS] = class_methods_dict
        out_dict[CodeInspector.CLASS_VARIABLES] = class_variables_dict
        out_dict[CodeInspector.ATTRIBUTE_SUPERCLASS] = superclass_meta_dict
        return out_dict

    @staticmethod
    def create_model_from_path(p,model_instance:bool=False):
        """ creates dict of modules / classes from a given file path """
        if not os.path.isdir(p):
            logger.warning(f"{p} is not a valid path")
            return
        logger.info(f"Read modules from Path {p}")
        module_loader = ModuleLoader(p)
        module_dict = module_loader.get_modules()
        out_module_model = {}
        for module_name, module_info in module_dict.items():
            logger.info(f"get model information for module {module_name}")
            model = ObjectModelGenerator.create_model_from_module(module_info,model_instance)
            out_module_model[module_name] = model
        return out_module_model

class ObjectModel():
    """ creates Object model from model """
    ROOT = "ROOT"
    PARENT = "PARENT"
    MODULE = "MODULE"
    MODULE_SHORT = "MODULE_SHORT"
    PACKAGE = "PACKAGE"
    PARENT = "PARENT"
    TYPE = "TYPE"

    def __init__(self, p: str,model_instance:bool=False) -> None:
        """ right now model is created from path """
        self._path=p
        self._model_instance=model_instance
        self._module_model = ObjectModelGenerator.create_model_from_path(p,model_instance)
        self._module_tree = {}
        self._create_package_hierarchy()

    @property
    def modules(self):
        """ module tree property """
        return self._module_model

    @property
    def module_tree(self):
        """ module tree property """
        return self._module_tree

    def get_module(self, full_module_name):
        """ returns the module model """
        logger.debug(f"Get module {full_module_name}")
        module = self._module_model.get(full_module_name)
        if not module:
            logger.warning(f"Module {full_module_name} not foung")
        return module

    def _create_package_hierarchy(self):
        """ creates package hierarchy """
        logger.info("Create Package Hierarchy")
        module_tree = {}
        module_tree[Tree.ROOT] = {}
        module_tree[Tree.ROOT][Tree.PARENT] = None
        # build up tree from module name

        # collect all paths
        all_paths = {}
        hash_dict = {}
        for full_module_name, module_info in self._module_model.items():
            logger.debug(f"Processing module {full_module_name}")
            # ensure there is always a root
            hash_dict[full_module_name] = module_info.get(
                CodeInspector.HASH, "NO_HASH_FOUND")
            module_path = Tree.ROOT+"."+full_module_name
            module_parts = module_path.split(".")
            module_path = ""
            for num_elements in range(len(module_parts)):
                module_path = ".".join(module_parts[:num_elements+1])
                all_paths[module_path] = None
        # build up tree
        all_paths = list(all_paths.keys())
        for p in all_paths:
            logger.debug(f"Processing pacakge path {p}")
            module_parts = p.split(".")
            last_elem = module_parts[-1]
            if last_elem == Tree.ROOT:
                continue
            parent_path = ".".join(module_parts[:-1])
            module_tree[p] = {}
            module_tree[p][Tree.PARENT] = parent_path
            p_name = p.replace(Tree.ROOT+".", "")
            module_tree[p][CodeInspector.HASH] = hash_dict.get(p_name)

        path_tree = Tree()
        path_tree.create_tree(module_tree, name_field=CodeInspector.HASH)
        self._module_tree = path_tree

class ModelFilter(): #0918
    """ Filtering the results of PlantUMLRenderer """

    # filter attributes
    FILTER_ATTRIBUTES = "filter_attributes"
    # filter methods
    FILTER_METHODS = "filter_methods"
    # filter all inner properties (methods and attributes)
    FILTER_INNER = "filter_inner"
    # filter protected and private
    FILTER_INTERNAL = "filter_internal"
    # filter on module
    FILTER_MODULE = "filter_module"
    # filter on object name
    FILTER_NAME = "filter_name"
    # filtering out sys modules (external packages)
    FILTER_SYS_MODULE = "filter_sys_module"

    FILTER_DICT = {FILTER_ATTRIBUTES:FILTER_ATTRIBUTES,
                   FILTER_METHODS:FILTER_METHODS,
                   FILTER_INNER:FILTER_INNER,
                   FILTER_INTERNAL:FILTER_INTERNAL,
                   FILTER_MODULE:FILTER_MODULE,
                   FILTER_SYS_MODULE:FILTER_SYS_MODULE,
                   }

    def __init__(self,filter_list:list=None) -> None:
        """ constructor """
        self._filter_dict ={}
        self._obj_dict = {}
        if not filter_list:
            return
        self.add_filters(filter_list)

    def add_filters(self,filter_list:list=None)->None:
        """" add filters """
        # support currently only fixed rule
        if not filter_list:
            return
        filters = list(ModelFilter.FILTER_DICT.keys())
        for obj_filter in filter_list:
            if obj_filter in filters:
                self._filter_dict[obj_filter]=ModelFilter.FILTER_DICT[obj_filter]
                logger.debug(f"Add filter {obj_filter}")
            else:
                logger.warning(f"Filter {obj_filter} not supported")

    def pass_class_member_filter(self,filter_name,filter_value)->bool:
        """ check for class attributes to be filtered """
        passed = True
        name = self._obj_dict.get(CodeInspector.ATTRIBUTE_NAME)
        if filter_name == ModelFilter.FILTER_INTERNAL:
            vis,_ = PlantUMLRenderer._get_visibility(name)
            if vis in [PlantUMLRenderer.PROTECTED,PlantUMLRenderer.PRIVATE]:
                passed = False
        elif filter_name == ModelFilter.FILTER_INNER:
            passed = False # filter away all inner attributes
        return passed

    def pass_object_filter(self):
        """ generic filter  """
        passed = True
        return passed


    def passed(self,obj_name,class_member:bool=False,**kwargs)->bool:
        """ apply filters, cass instance indicates attribute of a class """

        object_keys=[CodeInspector.ATTRIBUTE_OBJECTTYPE,
                     CodeInspector.ATTRIBUTE_PACKAGE,CodeInspector.MODULE,
                     CodeInspector.RELATION,CodeInspector.RELATION_MODULE,
                     CodeInspector.ATTRIBUTE_IS_SYSMODULE,
                     CodeInspector.ATTRIBUTE_IS_INSTANCE]
        # transfer input dict into filter values
        self._obj_dict = {k:kwargs.get(k) for k in object_keys}
        self._obj_dict[CodeInspector.ATTRIBUTE_NAME]=obj_name
        # check if we have class member
        self._obj_dict[CodeInspector.CLASS_INSTANCE]=class_member
        is_passed = True
        logger.debug(f"Filter object {obj_name} ({self._obj_dict[CodeInspector.ATTRIBUTE_OBJECTTYPE]})")

        for filter_name,filter_value in self._filter_dict.items():
            logger.debug(f"Apply filter {filter_name}")

            # check for object attributes
            if class_member:
                is_passed = self.pass_class_member_filter(filter_name,filter_value)
            # apply other filters
            else:
                # TODO IMPLEMENT
                pass

        self._obj_dict = {}
        return is_passed



class PlantUMLRenderer():
    """ Renders an object model as Plant UML """
    UML_CONTENT = "_CONTENT_"
    # setting namespaceSeparator disables auztomatic creation of packages
    # DOC_UML = "@startuml\nset namespaceSeparator none\n_CONTENT_\n@enduml"
    DOC_UML ="\n".join(["@startuml",
                "'remark use together {...}",
                "left to right direction",
                "'top to bottom direction",
                "skinparam dpi 180",
                "set namespaceSeparator none",
                "skinparam linetype ortho",
                "'skinparam linetype polyline",
                "<style>",
                ".moduleclass { BackgroundColor LightBlue }",
                "</style>",
                "_CONTENT_",
                "hide <<moduleclass>> stereotype",
                "left footer Generated with CodeInspector on (_CREATED_) from (_SOURCE_)",
                "@enduml"])

    COMPONENT = "_COMPONENT_"
    PACKAGE = "_PACKAGE_"
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PLANTUML = "plantuml"
    UML_LINK = "+--"
    UML_INHERIT = "<|--"
    UML_IMPORT = "<.."
    UML_RELATION = "--"
    COLOR_MODULE = "#TECHNOLOGY"

    UML_SYNMBOL = "uml_symbol"
    UML_MAP = {CodeInspector.RELATION_IMPORTS: UML_IMPORT,
               CodeInspector.RELATION_IMPLEMENTS: UML_LINK,
               CodeInspector.RELATION: UML_RELATION}

    ID = "_ID_"
    UML_COMPONENT = 'component [_COMPONENT_] as _ID_'
    UML_PACKAGE = 'package _PACKAGE_ {\n_CONTENT_}'

    def __init__(self, model: ObjectModel) -> None:
        self._model = model
        self._path = model._path
        self._model_filter = ModelFilter() #0918

    def add_model_filter(self,filter_list:list=None)->None: #0918
        """ add filter names (applicable vslues defined in Model Filter) """
        self._model_filter.add_filters(filter_list)

    @staticmethod
    def _get_string_from_list(string_list: list, indent: int = 4) -> str:
        out_s = ""
        for s in string_list:
            out_s += indent*" "+s+"\n"
        return out_s

    @staticmethod
    def _render_module_name(s: str) -> str:
        """ renders package """
        s_list = s.split(".")
        if len(s_list) <= 1:
            return s
        else:
            package = "<<"+".".join(s_list[:-1])+">>\\n"
            module = s_list[-1]
            return package+module

    @staticmethod
    def _get_visibility(name: str) -> str:
        """ gets the UML visibility prefix """
        prefix = "+"
        vis = PlantUMLRenderer.PUBLIC
        if name.startswith("_"):
            prefix = "#"
            vis = PlantUMLRenderer.PROTECTED
            if name.startswith("__"):
                prefix = "~"
                vis = PlantUMLRenderer.PRIVATE
        return (vis, prefix)

    def _render_function(self, obj: dict, static: bool = False) -> str:
        uml = "        {method} _static__visibility__name__signature__return_"
        # hash=obj.get(CodeInspector.HASH,"_NO_HASH_")
        # uml=uml.replace("_hash_",hash)

        params = {"_static_": "", "_visibility_": "",
                  "_name_": "", "_signature_": "",
                  "_return_": ""}
        params["_name_"] = obj.get(CodeInspector.ATTRIBUTE_NAME)
        vis, prefix = PlantUMLRenderer._get_visibility(params["_name_"])
        params["_visibility_"] = prefix
        if static:
            params["_static_"] = "{static} "
        signatures = []
        signature = obj.get(CodeInspector.ATTRIBUTE_SIGNATURE, {})
        for param, value in signature.items():
            if param == CodeInspector.RETURN:
                params["_return_"] = ": "+value
            else:
                signatures.append(param+":"+value)
        params["_signature_"] = "("+",".join(signatures)+")"
        for k, v in params.items():
            uml = uml.replace(k, v)
        logger.debug(f"PlantUML: {uml}")
        return (CodeInspector.METHOD, vis, uml)

    def _render_primitive(self, name, obj_info: dict, static: bool = False) -> str:
        uml = "        {field} _static__visibility__name__typeclass_"
        # hash=obj_info.get(CodeInspector.HASH,"_NO_HASH_")
        # uml=uml.replace("_hash_",hash)
        params = {"_static_": "", "_visibility_": "",
                  "_name_": "", "_typeclass_": ""}
        params["_name_"] = name
        vis, prefix = PlantUMLRenderer._get_visibility(name)
        params["_visibility_"] = prefix
        if static:
            params["_static_"] = "{static} "
        typeclass = obj_info.get(CodeInspector.ATTRIBUTE_TYPECLASS)
        if typeclass:
            params["_typeclass_"] = ": "+typeclass
        for k, v in params.items():
            uml = uml.replace(k, v)

        logger.debug(f"PlantUML: {uml}")
        return (CodeInspector.ATTRIBUTE, vis, uml)

    def _render_class_instance(self, name, obj_info: dict, static: bool = False) -> str:
        uml = "        {field} _static__visibility__name__typeclass_"
        params = {"_static_": "", "_visibility_": "",
                  "_name_": "", "_typeclass_": ""}
        params["_name_"] = name
        vis, prefix = PlantUMLRenderer._get_visibility(name)
        params["_visibility_"] = prefix
        if static:
            params["_static_"] = "{static} "
        # module where class instance is implemented
        module = obj_info.get(CodeInspector.MODULE)
        # module where class is originated
        module_origin = obj_info.get(CodeInspector.RELATION_MODULE)
        class_name = obj_info.get(CodeInspector.ATTRIBUTE_CLASS_NAME)
        # if module is not origin then we have a relation
        if module != module_origin:
            params["_typeclass_"] = ": "+class_name
        else:
            logger.info(
                f"Attribute {name}, module {module}, class {class_name} is of same origin, will be skipped")
            return (CodeInspector.ATTRIBUTE, vis, None)

        # TODO FILTER OUT ITEMS
        passed = self._model_filter.passed(name,class_member=False,**obj_info)

        pass

        for k, v in params.items():
            uml = uml.replace(k, v)
        logger.debug(f"PlantUML: {uml}")
        return (CodeInspector.ATTRIBUTE, vis, uml)

    def _render_uml_dict(self, render_dict) -> str:
        """ renders the inner uml string fpor the module pseudo class """
        object_type = render_dict.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        object_name = render_dict.get(CodeInspector.ATTRIBUTE_NAME)
        logger.debug(
            f"render PLantUml parts for object {object_name} [{object_type}]")

        object_parts = [CodeInspector.ATTRIBUTE, CodeInspector.METHOD]
        visibility_list = [PlantUMLRenderer.PUBLIC,
                           PlantUMLRenderer.PROTECTED, PlantUMLRenderer.PRIVATE]
        out_list = []
        for object_part in object_parts:
            for vis in visibility_list:
                for attribute, attribute_info in render_dict[object_part][vis].items():
                    # TODO filter module class attribute
                    passed = self._model_filter.passed(attribute,class_member=True,**attribute_info[CodeInspector.OBJECT])
                    if not passed:
                        continue
                    try:
                        plantuml_s = attribute_info[PlantUMLRenderer.PLANTUML]
                        logger.debug(f"PlantUML: {plantuml_s}")
                        out_list.append(plantuml_s)
                    except KeyError as e:
                        logger.info(
                            f"Couldn't find plantuml for attribute {attribute}, {vis} object part {object_part} ")
                        continue
        return "\n".join(out_list)

    def _render_module(self, uml_rendered_module: dict):
        """ renders the module """
        uml_module="'### MODULE _module_ (_hash_)\n"
        uml_module += 'package "_module_" as _hash_ <<module>> _COLOR_MODULE_ {\n_uml_inner_\n}'
        uml_module = uml_module.replace("_COLOR_MODULE_",PlantUMLRenderer.COLOR_MODULE)
        uml = 'class "_module_" as _clsmoduleid_ << (M,APPLICATION) moduleclass >> {\n_uml_inner_\n}'

        params = {"_module_": "", "_uml_inner_": "", "_hash_": ""}
        module = uml_rendered_module.get(CodeInspector.ATTRIBUTE_NAME)
        clsmoduleid=CodeInspector.get_hash(module+"_class")
        hash_value = uml_rendered_module.get(CodeInspector.HASH)
        params["_module_"] = module
        params["_hash_"] = hash_value
        params["_clsmoduleid_"] = clsmoduleid
        # this is the inner uml of the module class 
        params["_uml_inner_"] = self._render_uml_dict(uml_rendered_module)

        logger.debug(f"Render UML Module {module} as plantuml")
        for k, v in params.items():
            uml = uml.replace(k, v)

        uml_classes = [uml]
        uml_links=[]
        uml_linksym=" "+PlantUMLRenderer.UML_LINK+" "
        try:
            classes_dict = uml_rendered_module[CodeInspector.CLASS][PlantUMLRenderer.PUBLIC]
            for class_name, class_info in classes_dict.items():
                uml = class_info.get(PlantUMLRenderer.PLANTUML, "")
                class_hash = class_info.get(CodeInspector.HASH,"NOLINK")
                logger.debug(
                    f"Module {module}, class {class_name}, uml: {len(uml)} bytes")
                if len(uml) == 0:
                    continue
                uml_classes.append(uml)
                uml_links.append(uml_linksym.join([clsmoduleid,class_hash]))
        except KeyError as e:
            logger.warning(f"couldn't get class from {params['_module_']}")
        params["_uml_inner_"] = "\n".join(uml_classes)
        uml = uml_module
        for k, v in params.items():
            uml = uml.replace(k, v)
        # add links
        uml="\n".join([uml,*uml_links])+"\n"
        uml_rendered_module[PlantUMLRenderer.PLANTUML] = uml
        return uml

    @staticmethod
    def _create_class_uml_inner(uml_rendered_module: dict):
        """ creates the inner uml string of a class as generated by _render_class """
        logger.debug("begin")
        vis_list = [PlantUMLRenderer.PUBLIC,
                    PlantUMLRenderer.PROTECTED, PlantUMLRenderer.PRIVATE]
        obj_list = [CodeInspector.ATTRIBUTE, CodeInspector.METHOD]
        uml_out = []
        for obj_type in obj_list:
            uml_list = []
            for vis in vis_list:
                try:
                    uml_dict = uml_rendered_module[obj_type][vis]
                    for attribute,plantuml in uml_dict.items():
                        logger.debug(f"<{obj_type}> [{attribute}][{vis}] , plantuml: [{plantuml}]")
                        if not plantuml:
                            continue
                        uml_list.append(plantuml)
                except KeyError as e:
                    continue
                uml_out.extend(uml_list)
        return "\n".join(sorted(list(set(uml_out))))

    def _render_class(self, class_info: dict):
        """ renders a class """
        uml_out = "' # CLASS _class_ (_hash_)\n"
        uml_out += '    class "_class_" as _hash_ {\n_uml_inner_\n}'
        cls_obj = class_info.get(CodeInspector.OBJECT)
        name = cls_obj.get(CodeInspector.ATTRIBUTE_NAME)
        logger.debug(f"Rendering class {name}")
        hash_value = class_info.get(CodeInspector.HASH)
        object_type = class_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
        module = cls_obj.get(CodeInspector.MODULE)
        package = class_info.get(CodeInspector.ATTRIBUTE_PACKAGE)
        uml_out = uml_out.replace("_class_", name)
        uml_out = uml_out.replace("_hash_", hash_value)

        uml_rendered_module = PlantUMLRenderer._create_render_dict()
        uml_rendered_module[CodeInspector.HASH] = hash_value
        uml_rendered_module[CodeInspector.ATTRIBUTE_OBJECTTYPE] = object_type
        uml_rendered_module[CodeInspector.ATTRIBUTE_NAME] = name
        uml_rendered_module[CodeInspector.ATTRIBUTE_MODULE] = module
        uml_rendered_module[CodeInspector.ATTRIBUTE_PACKAGE] = package

        logger.debug(f"Render Class: {name}, module {module}")

        # process methods
        methods_dict = class_info.get(CodeInspector.CLASS_METHODS)
        obj_methods = class_info.get(CodeInspector.INSTANCE_METHODS)
        methods_dict.update(obj_methods)

        for m_name, m_info in methods_dict.items():
            # TODO FILTER OUT ITEMS _render_class
            passed = self._model_filter.passed(m_name,class_member=True,**m_info)
            if not passed:
                continue
            uml = None
            # is_static = m_info.get(CodeInspector.ATTRIBUTE_IS_INSTANCE)
            is_static = not m_info.get(CodeInspector.ATTRIBUTE_IS_INSTANCE,False)
            o_type, o_visibility, uml = self._render_function(
                m_info, is_static)
            # uml_rendered_module[o_type][o_visibility] = uml
            # TODO CHECK
            if uml:
                uml_rendered_module[o_type][o_visibility][m_name] = uml

        # process variables
        vars_dict = class_info.get(CodeInspector.CLASS_VARIABLES)
        obj_vars = class_info.get(CodeInspector.INSTANCE_VARIABLES)
        vars_dict.update(obj_vars)

        for v_name, v_info in vars_dict.items():
            # TODO FILTER OUT ITEMS _render_class
            passed = self._model_filter.passed(v_name,class_member=True,**v_info)
            if not passed:
                continue
            v_type = v_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            is_static = not v_info.get(CodeInspector.ATTRIBUTE_IS_INSTANCE,False)
            # is_static = v_info.get(CodeInspector.ATTRIBUTE_IS_INSTANCE)
            uml = None
            if v_type == CodeInspector.PRIMITIVE:
                o_type, o_visibility, uml = self._render_primitive(
                    v_name, v_info, is_static)
            elif v_type == CodeInspector.CLASS_INSTANCE:
                o_type, o_visibility, uml = self._render_class_instance(
                    v_name, v_info, is_static)
            else:
                logger.warning(
                    f"Class {name}, attibute {v_name}, type {v_type}, can't create uml code")
            if uml:
                uml_rendered_module[o_type][o_visibility][v_name] = uml
        inner_uml = PlantUMLRenderer._create_class_uml_inner(
            uml_rendered_module)
        uml_out = uml_out.replace("_uml_inner_", inner_uml)

        return (CodeInspector.CLASS, PlantUMLRenderer.PUBLIC, uml_out)

    @staticmethod
    def _create_render_dict():
        """ creates a dict for keeping rendered plantum strings for a module"""
        logger.debug("begin")
        rendered_object = {}
        rendered_methods = {}
        rendered_attributes = {}
        rendered_classes = {}
        rendered_relations = {}
        rendered_classes[PlantUMLRenderer.PUBLIC] = {}
        rendered_relations[PlantUMLRenderer.PUBLIC] = {}
        rendered_methods[PlantUMLRenderer.PUBLIC] = {}
        rendered_methods[PlantUMLRenderer.PRIVATE] = {}
        rendered_methods[PlantUMLRenderer.PROTECTED] = {}
        rendered_attributes[PlantUMLRenderer.PUBLIC] = {}
        rendered_attributes[PlantUMLRenderer.PRIVATE] = {}
        rendered_attributes[PlantUMLRenderer.PROTECTED] = {}
        rendered_object[CodeInspector.METHOD] = rendered_methods
        rendered_object[CodeInspector.ATTRIBUTE] = rendered_attributes
        rendered_object[CodeInspector.CLASS] = rendered_classes
        rendered_object[CodeInspector.RELATION] = rendered_relations
        rendered_object[CodeInspector.HASH] = None
        rendered_object[CodeInspector.KEY] = None
        rendered_object[CodeInspector.OBJECT] = None
        rendered_object[CodeInspector.ATTRIBUTE_OBJECTTYPE] = None
        rendered_object[CodeInspector.ATTRIBUTE_MODULE] = None
        return rendered_object

    @staticmethod
    def _create_relation_dict():
        """ creates a relation dict """
        node_dict_src = {CodeInspector.ATTRIBUTE_NAME: None,
                         CodeInspector.ATTRIBUTE_PACKAGE: None,
                         CodeInspector.MODULE: None,
                         CodeInspector.HASH: None,
                         CodeInspector.KEY: None,
                         CodeInspector.ATTRIBUTE_OBJECTTYPE: None,
                         CodeInspector.OBJECT: None
                         }
        node_dict_trg = copy.deepcopy(node_dict_src)
        out_dict = {CodeInspector.NODE_SOURCE: node_dict_src,
                    CodeInspector.NODE_TARGET: node_dict_trg,
                    CodeInspector.RELATION: CodeInspector.RELATION_IMPORTS,
                    PlantUMLRenderer.PLANTUML: None,
                    PlantUMLRenderer.UML_SYNMBOL: PlantUMLRenderer.UML_RELATION}
        return out_dict

    @staticmethod
    def _populate_relation(info_dict: dict, rel_dict: dict, node: str = None, relation: str = None) -> dict:
        """ populates relation dict from info dict """
        logger.debug("start")
        uml_symbol = PlantUMLRenderer.UML_RELATION
        if relation:
            uml_symbol = PlantUMLRenderer.UML_MAP.get(
                relation, PlantUMLRenderer.UML_RELATION)
        if relation:
            rel_dict[CodeInspector.RELATION] = relation
            rel_dict[PlantUMLRenderer.UML_SYNMBOL] = uml_symbol
            logger.debug(
                f"Setting relation [{relation}], (PlantUML: {uml_symbol})")

        if node is None:
            node = CodeInspector.NODE_SOURCE
        logger.debug(f"Processing relation {relation} for node {node}")
        node_dict = rel_dict.get(node)
        if not node_dict:
            logger.warning(f"Couldn't find node type {node}")
            return
        # copy over dictionary info
        for node in node_dict.keys():
            info_value = info_dict.get(node)
            if not info_value:
                continue
            logger.debug(f"set node info {node}:{info_value}")
            node_dict[node] = info_value
        return rel_dict

    def _render_associated_objects(self,nodes_dict) -> list:
        """ renders the associated objects of relations """
        UML_CLASS_MODULE = '    class "_module_" <<module>> {\n_uml_inner_\n}'  #0918
        UML_CLASS = '    class "_object_" as _hash_'
        UML_MODULE = 'package "_module_" as _hash_ <<module>> {\n_uml_inner_\n}'
        UML_FUNCTION = '        {method} +_object_'
        UML_ATTRIBUTE ='        {field} +_object_' #0918
        UML_LOOKUP = {CodeInspector.METHOD: UML_FUNCTION,
                      CodeInspector.FUNCTION: UML_FUNCTION,
                      CodeInspector.CLASS: UML_CLASS,
                      CodeInspector.CLASS_INSTANCE: UML_CLASS,
                      CodeInspector.PRIMITIVE: UML_ATTRIBUTE
                      }

        logger.debug("start")
        uml_modules = []
        for module, module_objects_info in nodes_dict.items():
            hash_module = module_objects_info.get(CodeInspector.HASH)
            logger.debug(f"Rendering module {module} [{hash_module}]")
            uml_class_module = UML_CLASS_MODULE
            uml_class_module = uml_class_module.replace("_module_", module)
            uml_class_module = uml_class_module.replace("_hash_", hash_module)
            uml_module = UML_MODULE
            uml_module = uml_module.replace("_module_", module)
            uml_module = uml_module.replace("_hash_", hash_module)
            uml_module_inner = []
            uml_classes = []
            for obj, obj_info in module_objects_info.items():
                if obj == CodeInspector.HASH:
                    continue
                obj_type = obj_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
                hashvalue = obj_info.get(CodeInspector.HASH)
                if obj_type == CodeInspector.ATTRIBUTE_MODULE:
                    continue
                logger.debug(                    
                    f"Module {module}, rendering object {obj} [{hashvalue}], type {obj_type} ")
                uml_obj = UML_LOOKUP.get(obj_type)
                # TODO filter out inner objects of associated objects   
                passed = self._model_filter.passed(obj,class_member=True,**obj_info)
                if not passed:
                    continue

                if uml_obj:
                    uml_obj = uml_obj.replace("_object_", obj)
                    uml_obj = uml_obj.replace("_hash_", hashvalue)
                    logger.info(f"PLANT UML: {uml_obj}")
                else:
                    logger.error(
                        f"Couldn't find uml snippet for objtype {obj_type}")
                    continue
                if obj_type in [CodeInspector.CLASS_INSTANCE, CodeInspector.CLASS]:
                    uml_classes.append(uml_obj)
                else:
                    uml_module_inner.append(uml_obj)
            uml_class_module = uml_class_module.replace(
                "_uml_inner_", "\n".join(uml_module_inner))
            uml_module = uml_module.replace(
                "_uml_inner_", "\n".join([uml_class_module, *uml_classes]))
            module_objects_info[PlantUMLRenderer.PLANTUML] = uml_module
            uml_modules.append(uml_module)

        return uml_modules

    def _create_relation_objects(self,uml_relation_list: list, objects_dict: dict, rendered_modules_dict: dict):
        """ create relation objects of imports, updates uml relations """
        logger.debug("start, get module import relations")

        # collection of unresolved nodes
        unresolved_nodes = {}
        # collect existing modules that are already rendered
        rendered_modules = list(rendered_modules_dict.keys())

        object_hash_list = list(objects_dict.keys())

        # check for any missing modeled plantuml
        for uml_relation in uml_relation_list:
            nodes = [uml_relation.get(CodeInspector.NODE_SOURCE), uml_relation.get(
                CodeInspector.NODE_TARGET)]
            logger.debug(
                f"Process relation [{uml_relation[PlantUMLRenderer.PLANTUML]}]")
            for node in nodes:
                module_name = node.get(CodeInspector.MODULE)
                hash_value = node.get(CodeInspector.HASH)
                if module_name is None or module_name in rendered_modules:
                    continue

                unresolved_node_dict = unresolved_nodes.get(
                    module_name, {CodeInspector.HASH: None})

                obj_type = node.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
                if obj_type == CodeInspector.MODULE:
                    unresolved_node_dict[CodeInspector.HASH] = node.get(
                        CodeInspector.HASH)
                # unresolved_node_dict[CodeInspector.HASH]=CodeInspector.get_hash(module_name)
                name = node.get(CodeInspector.ATTRIBUTE_NAME)
                if name is None:
                    name = module_name+"_no_name"
                logger.debug(
                    f"Unresolved node <{name}> [{hash_value}], type {obj_type},  module {module_name} [{unresolved_node_dict[CodeInspector.HASH]}]")
                unresolved_node_dict[name] = node
                unresolved_nodes[module_name] = unresolved_node_dict

        # assign module hash node if nothing is found
        logger.debug("Check unresolved module hashes")
        for node_name, node_info in unresolved_nodes.items():
            hash_value = node_info.get(CodeInspector.HASH)
            logger.debug(f"Module <{node_name}> [{hash_value}]")
            if hash_value is not None:
                continue
            hash_value = CodeInspector.get_hash(node_name)
            node_info[CodeInspector.HASH] = hash_value
            logger.debug(f"Module <{node_name}>, set hash {hash_value}")

        # rework the link list
        unresolved_modules_list = list(unresolved_nodes.keys())
        logger.debug(
            f"Rework Link List using modules {unresolved_modules_list}")
        for uml_relation in uml_relation_list:
            nodes = [uml_relation.get(CodeInspector.NODE_SOURCE), uml_relation.get(
                CodeInspector.NODE_TARGET)]
            for node in nodes:
                module_name = node.get(CodeInspector.MODULE)
                hash_value = node.get(CodeInspector.HASH)
                unresolved_module = unresolved_nodes.get(module_name, {})
                hash_module = unresolved_module.get(CodeInspector.HASH)
                name = node.get(CodeInspector.ATTRIBUTE_NAME)
                objtype = node.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
                if module_name in unresolved_modules_list:
                    uml_content = uml_relation[PlantUMLRenderer.PLANTUML]
                    logger.debug(f"Replace relation [{uml_content}")
                    logger.debug(
                        f"Replace {objtype} <{name}> [{hash_value}] < [{hash_module}] (Module {module_name})")
                    uml_content = uml_content.replace(hash_value, hash_module)
                    logger.debug(f"Updated relation: {uml_content}")
                    uml_relation[PlantUMLRenderer.PLANTUML] = uml_content

        _ = self._render_associated_objects(unresolved_nodes)

        return unresolved_nodes

    @staticmethod
    def _create_module_obj_relation(module_info: dict, obj_info: dict, relation: str = CodeInspector.RELATION) -> dict:
        """ creates module class relation """
        rel_dict = PlantUMLRenderer._create_relation_dict()
        # process module
        _ = PlantUMLRenderer._populate_relation(
            module_info, rel_dict, relation=relation)
        # process object
        _ = PlantUMLRenderer._populate_relation(
            obj_info, rel_dict, node=CodeInspector.NODE_TARGET)
        # render the plant uml string
        # relation
        hash_source = rel_dict.get(CodeInspector.NODE_SOURCE)[
            CodeInspector.HASH]
        hash_target = rel_dict.get(CodeInspector.NODE_TARGET)[
            CodeInspector.HASH]
        symbol = rel_dict.get(PlantUMLRenderer.UML_SYNMBOL,
                              PlantUMLRenderer.UML_RELATION)
        rel_dict[PlantUMLRenderer.PLANTUML] = " ".join(
            [hash_source, symbol, hash_target])
        return rel_dict

    @staticmethod
    def _render_relations(relations)->dict:
        """ renders the relations alongside with a comment """
        relations_out={}
        for i,relation in enumerate(relations):
            src=relation.get(CodeInspector.NODE_SOURCE)
            src_obj=src.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            src_key=src.get(CodeInspector.KEY)
            trg=relation.get(CodeInspector.NODE_TARGET)
            trg_obj=trg.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
            trg_key=trg.get(CodeInspector.KEY)
            relation_s=relation.get(CodeInspector.RELATION)
            plantuml=relation.get(PlantUMLRenderer.PLANTUML)
            comment=f"'# RELATION ({i}) [{src_obj}-{relation_s}-{trg_obj}]: {src_key} - {trg_key} \n"
            relations_out[plantuml]={PlantUMLRenderer.PLANTUML:(comment+plantuml)}
        return relations_out

    def _render_footer(self,plantuml_s:str)->str:
        """ renders the footer info """
        date_s=DateTime.now().strftime("%Y-%m-%d %H:%M:%S")
        path=str(self._path).replace("\\","/")
        plantuml_s = plantuml_s.replace("_CREATED_",date_s)
        plantuml_s = plantuml_s.replace("_SOURCE_",str(path))
        return plantuml_s

    def render_class_diagram(self) -> str:
        """ renders all plantuml items """
        doc_uml = PlantUMLRenderer.DOC_UML
        doc_uml = self._render_footer(doc_uml)
        uml_inner = []
        modules, relations, related_objects = self._collect_render_objects()
        relations_dict=PlantUMLRenderer._render_relations(relations)
        logger.debug("start")
        render_object_dicts={"\n'### MODULES":modules,
                            "\n'### RELATED OBJECTS":related_objects,
                            "\n'### RELATIONS":relations_dict}
        for comment,render_object_dict in render_object_dicts.items():
            uml_inner.append(comment)
            uml_block=[]
            for uml_object, obj_info in render_object_dict.items():
                uml = obj_info.get(PlantUMLRenderer.PLANTUML)
                if uml:
                    logger.debug(f"Object {uml_object}, len {len(uml)} bytes")
                    uml_block.append(uml)
                else:
                    logger.warning(
                        f"No plantuml snippet found for object {uml_object}")

            # add a together bracket around own modules
            if "MODULES" in comment:
                uml_block = ["together {",*uml_block,"}","' (together ### MODULES)"]
            uml_inner.extend(uml_block)
        doc_uml = doc_uml.replace(
            PlantUMLRenderer.UML_CONTENT, "\n".join(uml_inner))
        return doc_uml

    @staticmethod
    def _collect_superclass_info(obj_info):
        """ creates superclass relation """
        # create relation dict
        rel_dict = PlantUMLRenderer._create_relation_dict()
        rel_dict[PlantUMLRenderer.UML_SYNMBOL]=PlantUMLRenderer.UML_INHERIT
        rel_dict[CodeInspector.RELATION]=CodeInspector.RELATION_INHERITS
        node_source=rel_dict[CodeInspector.NODE_SOURCE]
        node_target=rel_dict[CodeInspector.NODE_TARGET]

        attributes=[CodeInspector.ATTRIBUTE_NAME,CodeInspector.MODULE,CodeInspector.ATTRIBUTE_PACKAGE,
                    CodeInspector.KEY,CodeInspector.HASH,CodeInspector.RELATION_MODULE]
        superclass_info={}
        logger.debug("start")
        superclass_meta=obj_info.get(CodeInspector.ATTRIBUTE_SUPERCLASS)
        if not superclass_meta:
            return
        for attribute in attributes:
            superclass_info[attribute]=obj_info.get(attribute)
        try:
            superclass_name=superclass_meta.__name__
            superclass_module=superclass_meta.__module__
            superclass_package=superclass_module

        except AttributeError:
            logger.warning("couldn't find __name__ attribute")
            return

        if not superclass_name:
            logger.warning(f"No superclass found for Class {superclass_info[CodeInspector.ATTRIBUTE_NAME]}")
            return
        superclass_info[CodeInspector.ATTRIBUTE_SUPERCLASS_NAME]=superclass_name
        superclass_info[CodeInspector.RELATION]=CodeInspector.RELATION_INHERITS
        # get key and hash
        superclass_key_dict={}
        superclass_key_dict[CodeInspector.ATTRIBUTE__MODULE__]=superclass_module
        # get the complete module path without module name
        superclass_package=".".join(superclass_module.split(".")[:-1])
        superclass_key_dict[CodeInspector.ATTRIBUTE__PACKAGE__]=superclass_package
        superclass_key_dict[CodeInspector.ATTRIBUTE__NAME__]=superclass_name
        superclass_key=CodeInspector.get_object_key(superclass_key_dict)
        superclass_hash=CodeInspector.get_hash(superclass_key)
        # copy over node information
        node_source[CodeInspector.ATTRIBUTE_NAME] = superclass_name
        node_source[CodeInspector.ATTRIBUTE_PACKAGE] = superclass_package
        node_source[CodeInspector.ATTRIBUTE_MODULE] = superclass_module
        node_source[CodeInspector.HASH] = superclass_hash
        node_source[CodeInspector.KEY] = superclass_key
        node_source[CodeInspector.OBJECT] = superclass_meta
        for attribute in node_target.keys():
            node_target[attribute]=obj_info.get(attribute)
        node_target[CodeInspector.OBJECT]=obj_info
        uml_symbol=" "+rel_dict[PlantUMLRenderer.UML_SYNMBOL]+" "
        rel_dict[PlantUMLRenderer.PLANTUML]=uml_symbol.join([node_source[CodeInspector.HASH],node_target[CodeInspector.HASH]])
        trg_class=node_target[CodeInspector.ATTRIBUTE_NAME]
        trg_package=node_target[CodeInspector.ATTRIBUTE_PACKAGE]
        logger.debug(f"Relation  {superclass_name} ({superclass_package})  <|-- {trg_class} ({trg_package}) ")
        logger.debug(f"PLANTUML {rel_dict[PlantUMLRenderer.PLANTUML]}")
        return rel_dict

    @staticmethod
    def _validate_relations(uml_relation_list:list,obj_dict:dict)->list:
        """ validates relations for invbalid entries """
        validated_rel_list=[]
        logger.debug("start")
        hash_list=list(obj_dict.keys())
        for uml_relation in uml_relation_list:
            src=uml_relation[CodeInspector.NODE_SOURCE]
            trg=uml_relation[CodeInspector.NODE_TARGET]
            rel_hashes=[src.get(CodeInspector.HASH),trg.get(CodeInspector.HASH)]
            hashes_valid=[r in hash_list for r in rel_hashes]
            logger.debug(f"Validate {src.get(CodeInspector.KEY)} {uml_relation[CodeInspector.RELATION]} {trg.get(CodeInspector.KEY)}")
            plantuml=uml_relation.get(PlantUMLRenderer.PLANTUML)
            logger.debug(f"PLANTUML {plantuml}, {hashes_valid}")
            hashes_valid=all(hashes_valid)
            if not hashes_valid:
                logger.warning(f"Relation {plantuml} is not valid")
            else:
                validated_rel_list.append(uml_relation)
        return validated_rel_list

    def _collect_render_objects(self) -> tuple:
        """ central method to collect renderings of modules, functions, vars, classes relations """

        # classes rendered as plantuml
        uml_class_list = []
        # relations collected
        uml_relation_list = []
        # objects table all objects collected with their hash values
        objects_dict = {}

        model = self._model
        rendererd_modules = {}
        uml_superclass_relations=[]
        for module, module_info in model.modules.items():
            passed = self._model_filter.passed(module,**module_info)
            if not passed:
                continue
            objects_dict[module_info[CodeInspector.HASH]] = module_info
            uml_rendered_module = PlantUMLRenderer._create_render_dict()
            uml_rendered_module[CodeInspector.HASH] = module_info.get(
                CodeInspector.HASH)
            uml_rendered_module[CodeInspector.ATTRIBUTE_OBJECTTYPE] = module_info.get(
                CodeInspector.ATTRIBUTE_OBJECTTYPE)
            uml_rendered_module[CodeInspector.ATTRIBUTE_NAME] = module_info.get(
                CodeInspector.ATTRIBUTE_MODULE)
            uml_rendered_module[CodeInspector.ATTRIBUTE_MODULE] = module_info.get(
                CodeInspector.ATTRIBUTE_MODULE)
            uml_rendered_module[CodeInspector.ATTRIBUTE_PACKAGE] = module_info.get(
                CodeInspector.ATTRIBUTE_PACKAGE)
            uml_rendered_module[CodeInspector.OBJECT] = module_info.get(
                CodeInspector.OBJECT)

            classes_implemented = module_info.get(
                CodeInspector.IMPLEMENTED_CLASSES)

            # IMPLEMENTED CODE OBJECTS
            objects_implemented = module_info.get(
                CodeInspector.RELATION_IMPLEMENTS)
            for object_implemented, obj_info in objects_implemented.items():
                obj_type = obj_info.get(CodeInspector.ATTRIBUTE_OBJECTTYPE)
                hash_value =    obj_info.get(CodeInspector.HASH)
                superclass_info=PlantUMLRenderer._collect_superclass_info(obj_info)
                if superclass_info:
                    uml_superclass_relations.append(superclass_info)

                objects_dict[hash_value] = obj_info
                uml_s = None
                # TODO FILTER OUT ITEMS _collect_render_objects
                passed = self._model_filter.passed(object_implemented,**obj_info)
                if not passed:
                    continue
                if obj_type == CodeInspector.CLASS:
                    logger.debug(
                        f"Rendering class {object_implemented}, get relations")
                    class_info = classes_implemented.get(object_implemented)
                    uml_type, vis, uml_s = self._render_class(class_info)
                elif obj_type == CodeInspector.CLASS_INSTANCE:
                    uml_type, vis, uml_s = self._render_class_instance(
                        object_implemented, obj_info, static=True)
                    if uml_s is None:
                        continue
                elif obj_type == CodeInspector.FUNCTION or obj_type == CodeInspector.METHOD:
                    uml_type, vis, uml_s = self._render_function(
                        obj_info, static=True)
                elif obj_type == CodeInspector.PRIMITIVE:
                    uml_type, vis, uml_s = self._render_primitive(
                        object_implemented, obj_info, static=True)

                uml_rendered_module[uml_type][vis][object_implemented] = {CodeInspector.HASH: hash_value,
                                                                          PlantUMLRenderer.PLANTUML: uml_s,
                                                                          CodeInspector.OBJECT: obj_info}
            # Get Relations for IMPORTED CODE ELEMENTS
            objects_imported = module_info.get(CodeInspector.RELATION_IMPORTS)
            # here the import is class / probably we should calculate hash based on class name
            for object_imported, obj_info in objects_imported.items():
                # TODO FILTER OUT ITEMS _collect_render_objects
                passed = self._model_filter.passed(object_imported,**obj_info)
                if not passed:
                    continue
                logger.debug(
                    f"Imported class {object_imported}, get relations")
                hash_value = obj_info.get(CodeInspector.HASH)
                if hash_value:
                    objects_dict[hash_value] = obj_info
                rel = PlantUMLRenderer._create_module_obj_relation(
                    module_info, obj_info, relation=CodeInspector.RELATION_IMPORTS)
                if rel:
                    uml_relation_list.append(rel)

            # get the plantuml string for the module (without the classes)
            _ = self._render_module(uml_rendered_module)
            rendererd_modules[module] = uml_rendered_module

        # render associated objects like imports
        related_objects = self._create_relation_objects(
            uml_relation_list, objects_dict, rendererd_modules)

        # check relations
        uml_relation_list.extend(uml_superclass_relations)
        uml_relation_list = PlantUMLRenderer._validate_relations(uml_relation_list,objects_dict)

        return (rendererd_modules, uml_relation_list, related_objects)

    def render_component_diagram(self) -> str:
        """ generates a simple component / package diagram """
        logger.info("Render UML Component Diagram")

        def get_plantuml(s):
            """ analyse the string and transform it as plant UML """
            info = None
            is_module = False
            if ": {}" in s:
                is_module = True
            name = s.strip()
            name = name.replace('"', '')
            hash_value = None
            if len(name) > 1:
                name = name.split(":")[0].strip()
                info = hierarchy.get(name)
                if info:
                    hash_value = info.get(CodeInspector.HASH)

            name = name.replace("root.", "")

            if is_module:
                # TODO split at package
                name = PlantUMLRenderer._render_module_name(name)
                name = '    ['+name+']'
                if hash_value:
                    name += " as "+hash_value+" "+PlantUMLRenderer.COLOR_MODULE
            elif len(name) > 1:
                # comment = f"\n'### PACKAGE \n"
                name = 'package "'+name+'" {'
            return name

        module_tree = self._model.module_tree
        hierarchy = module_tree.hierarchy
        # root_id = module_tree.root_id

        module_hier_s = module_tree.json()
        string_list = module_hier_s.split("\n")
        if len(string_list) > 4:
            string_list = string_list[2:-2]
        out = [get_plantuml(s) for s in string_list]
        out = "\n".join(out)
        plantuml_s = PlantUMLRenderer.DOC_UML
        # render footer
        plantuml_s = self._render_footer(plantuml_s)
        plantuml_s = plantuml_s.replace(PlantUMLRenderer.UML_CONTENT, out)
        return plantuml_s


if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    # cwd = os.getcwd()
    om = ObjectModelGenerator()

    # Render instanciated objects as well (Constructor is called)
    model_instance = False

    # this will load the sample modules in this path
    if True:
        root_path = Path(__file__).parent
    # load path from input
    else:
        args = sys.argv
        # conventional command, use current directory
        arg_path = os.getcwd()
        if len(args) >= 2:
            arg_path=args[1]
        if not os.path.isdir(arg_path):
            print(f"Can't find path {arg_path}, check call of code_inspector")
            sys.exit(-1)
        root_path = arg_path

    # Testing inspect of a module
    if False:
        module_model = ObjectModelGenerator.create_model_from_module(
            module_myclass)

    # testing generation of class module
    if False:
        class_model = ObjectModelGenerator.create_model_from_class(MyClass01)

    # testing generation of a single class model
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
        # load the modules in my_package
        model_modules = ObjectModelGenerator.create_model_from_path(root_path,model_instance)

    # all in one go: create the module
    if True:
        om = ObjectModel(root_path,model_instance)
        module_tree = om.module_tree


    # # filter attributes
    # FILTER_ATTRIBUTES = "filter_attributes"
    # # filter methods
    # FILTER_METHODS = "filter_methods"
    # # filter all inner properties (methods and attributes)
    # FILTER_INNER = "filter_inner"
    # # filter protected and private
    # FILTER_INTERNAL = "filter_internal"
    # # filter on module
    # FILTER_MODULE = "filter_module"
    # # filter on object name
    # FILTER_NAME = "filter_name"
    # # filtering out sys modules (external packages)
    # FILTER_SYS_MODULE = "filter_sys_module"
    if True:
        model_filter = None
        # model_filter = [ModelFilter.FILTER_INNER]
        model_filter = [ModelFilter.FILTER_INTERNAL]

    # render the model as plantuml: simple package diagram and class diagram
    if True:
        uml_renderer = PlantUMLRenderer(om)
        uml_renderer.add_model_filter(model_filter)
        uml_component_s = uml_renderer.render_component_diagram()
        #print(uml_component_s)
        uml_class_s = uml_renderer.render_class_diagram()
        # print(plantuml)

    # print the files
    if True:
        print("###### PLANTUML CLASS DIAGRAM")
        print(uml_class_s)
        print("###### PLANTUML COMPONENT DIAGRAM")
        # print(uml_component_s)

    # save the files in current location
    if True:
        print(f"Save Files uml_component.plantuml, uml_class.plantuml ({os.getcwd()})")
        f=os.path.join("uml_component.plantuml")
        fm.save_txt_file(f,uml_component_s)
        f=os.path.join("uml_class.plantuml")
        fm.save_txt_file(f,uml_class_s)
        # set windows path to a folder containing all bat files
        os.system("call plantuml.bat")
        os.system("start uml_component.png")
        os.system("start uml_class.png")
        os.system("call tc.bat")
        print("##### IMAGE FILES")
        os.system("dir /b *.png")

""" helper methods to get some values out of enums """
import sys
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class EnumHelper():
    """ helper methods to get some values out of enums """

    @staticmethod
    def as_dict(enum_class:Enum)->dict:
        """ gets enum as dict """
        out = {}
        for enum_item in iter(enum_class):
            out[enum_item.name]=enum_item.value
        return out

    @staticmethod
    def keys(enum_class:Enum,lower:bool=False,upper:bool=False,
             as_dict:bool=False)->list:
        """ get names as list (optionally as lowercase / uppercase)
            if as_dict is set, original key from enum is returned
        """
        enum_dict = EnumHelper.as_dict(enum_class)
        keys = list(enum_dict.keys())
        keys_dict = dict(zip(keys,keys))
        for k,v in keys_dict.items():
            if lower:
                v = v.lower()
            elif upper:
                v = v.upper()
            keys_dict[k]=v
        if as_dict:
            return keys_dict
        else:
            return list(keys_dict.values())

    @staticmethod
    def key(enum_key:Enum,lower:bool=True,upper:bool=False)->dict:
        """ returns enum value if keys found returns original value"""
        name =  enum_key.name
        if lower:
            name = name.lower()
        elif upper:
            name = name.upper()
        return name

    @staticmethod
    def enum(enum_class:Enum,key,ignore_case:bool=True):
        """ Tries to get an enum from an enum key (str or enum) """
        key_s = key
        if isinstance(key,Enum):
            key_s = key.name
        out_enum = None
        enum_keys = EnumHelper.keys(enum_class)
        if key_s in enum_keys:
            out_enum = enum_class[key_s]
        # check if keys are in alt
        elif ignore_case:
            for k in enum_keys:
                if key_s.lower() == k.lower():
                    out_enum = enum_class[k]
                    break
        return out_enum

    @staticmethod
    def get_values_from_keys(enum_class:Enum,keys:list,ignorecase:bool=True):
        """ get list of values matching enum keys, also with the option to ignore case """
        enum_dict = EnumHelper.as_dict(enum_class)
        if ignorecase:
            enum_lower = {}
            for k,v in enum_dict.items():
                enum_lower[k.lower()]=v
            enum_dict = enum_lower
            keys = [k.lower() for k in keys]
        enum_keys = list(enum_dict.keys())
        out=[]
        for k in keys:
            if k in enum_keys:
                out.append(enum_dict[k])
        return out

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

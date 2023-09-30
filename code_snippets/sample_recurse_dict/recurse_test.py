""" recursive iteration through a dict """

import json
import copy
import hashlib
import re
import logging
import sys
from enum import Enum
# using the tree util to create a tree
from tools.tree_util import Tree

logger = logging.getLogger(__name__)

class Filter(Enum):
    """ filter values """
    TYPE = "filter_type"
    REGEX = "filter_regex"
    VALUE = "filter_value"
    KEY = "filter_key"
    LEVEL = "filter_level"
    LEVEL_MIN = "filter_level_min"
    LEVEL_MAX = "filter_level_max"
    LEVEL_RANGE = "filter_level_range"

    @staticmethod
    def get_values():
        """ returns maintained filter values """
        return [f.value for f in iter(Filter)]
    
    @staticmethod 
    def from_value(v:str):
        """ gets the enum from value """
        key = v.replace("filter_","").upper()
        try:
            enum_value = Filter[key] 
        except KeyError:
            logger.warning(f"There is no key {key} in ENUM")
            return None
        return enum_value
    
class DictProps(Enum):
    """  properties for DictParser """
    PARENT = "parent"
    KEY = "key"
    OBJECT = "object"
    OBJECT_TYPE = "obj_type"
    ID = "id"

    @staticmethod
    def get_values():
        """ returns maintained filter values """
        return [f.value for f in iter(DictProps)]    

class DictFilter():
    """ filtering the objects from DictParser """

    def __init__(self):
        """ constructor """
        self._allowed_filters = Filter.get_values()
        self._allowed_dict_props = DictProps.get_values()
        self._filters = []

    def add_filter(self,filter_value,filter_type:Filter=Filter.VALUE,**kwargs):
        """ adding filters with generic interface """
        if not filter_type in Filter:
            logger.warning(f"There is no filtertype {filter_type}")
            return

        filter_dict = { Filter.TYPE:filter_type,
                        Filter.VALUE:filter_value,}
        
        for k,v in kwargs.items():
            # try to get Filter Enum
            filter_enum = Filter.from_value(k)
            if not filter_enum:
                continue
            filter_dict[filter_enum]=v

        params = [(p.value,v) for p,v in list(filter_dict.items()) if not isinstance(v,Filter)]

        logger.debug(f"Adding [{filter_type.name}] filter, params {params}")
        self._filters.append(filter_dict)

    def add_value_filter(self,filter_value,**kwargs):
        """ convenience method for value filter, simply filter for any values """
        self.add_filter(filter_value,**kwargs)

    def add_regex_filter(self,regex:str,value:str,filter_type:Filter=Filter.VALUE,**kwargs):
        """ convenience method for regex filter """
        # regex_param = Filter.REGEX.valu
        kwargs[Filter.REGEX.value]=regex
        self.add_filter(filter_value=value,filter_type=filter_type,**kwargs)
    
    def filter(self,info_dict:dict):
        """ filter dict as defined by the DictProps Enum """
        # validate input
        validated_properties = [l for l in list(info_dict.keys()) if l in self._allowed_dict_props]
        if not validated_properties:
            logger.warning(f"passed dict has no proper keys ({list(info_dict.keys())})")
            return
        pass

class DictParser():
    """ parsing a dict into a tree structure """

    def __init__(self,input_dict:dict) -> None:
        """ constructor """
        self._hierarchy = {}
        self._num_nodes = 0
        self._dict = copy.deepcopy(input_dict)
        # turn lists into dicts
        self._dict = self._itemized_dict(self._dict,None)
        # get the dict index
        self._hierarchy = {}
        self._num_nodes = 0
        self._dict=self._itemized_dict(self._dict,"ROOT")
        self._hierarchy["ROOT"]={"parent":None,"key":"ROOT"}
        # get the tree object
        self._tree = Tree()
        self._tree.create_tree(self._hierarchy,name_field="key")
        # get the key map
        self._get_key_map()

    @property
    def itemized_dict(self):
        """ itemized dict """
        return self._dict

    @property
    def tree(self):
        """ tree object """
        return self._tree

    @staticmethod
    def get_hash(s: str):
        """ calculate hash """
        hash_value = hashlib.md5(s.encode()).hexdigest()
        return hash_value

    def _itemized_dict(self,d:dict,parent_id):
        """ turns lists into dicts, each list item gets an index """
        logging.debug(f"Iteration {self._num_nodes}")
        for k, v in d.copy().items():
            self._num_nodes += 1
            v_type = str(type(v).__name__)
            logger.debug(f"{self._num_nodes}: Key {k} type {v_type}, parent {parent_id}")
            if parent_id:
                obj_id = DictParser.get_hash(str(k)+str(self._num_nodes))
                self._hierarchy[obj_id]={"parent":parent_id,"key":k,"object":v,
                                         "obj_type":v_type,"id":obj_id}
            else:
                obj_id = None
            if isinstance(v, dict): # For DICT
                d[k]=self._itemized_dict(v,obj_id)
            elif isinstance(v, list): # itemize LIST as dict
                itemized = {"(L)"+str(i):item for i,item in enumerate(v)}
                d[k] = itemized
                self._itemized_dict(d[k],obj_id)
            elif isinstance(v, str): # Update Key-Value
                d.pop(k)
                d[k] = v
            else:
                d.pop(k)
                d[k] = v
                return d
        return d

    def _get_key_map(self):
        """ creates map of keys """
        for hier_id,hier_info in self._hierarchy.items():
            predecessors = self._tree.get_predecessors(hier_id)
            pred_ids=[hier_id,*predecessors][:-1]
            pred_ids.reverse()
            key_list=[ self._hierarchy[id]["key"] for id in pred_ids]
            logger.debug(f"[{hier_id}], key [{hier_info['key']}], key list {key_list}")
            hier_info["keylist"]=key_list
            hier_info["level"]=len(key_list)

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    # cwd = os.getcwd()
    test_struc = ('{"k1":"value1",'
                '"k2":{"k2.1":5,"k2.2":"v2.2",'
                '"k2.3":["l1","l2","l3"]}}')
    # test_dict = json.loads(test_struc)
    # dict_parser = DictParser(test_dict)
    # pass
    # s="acfg"
    # t="gte"
    # regex="^a"
    # x=re.findall(regex,s)
    # if x:
    #     pass
    # y=re.findall(regex,t)
    # if y:
    #     pass
    # pass
    # PARENT = "parent"
    # KEY = "key"
    # OBJECT = "obj"
    # OBJECT_TYPE = "obj_type"
    # ID = "id"

    
    df = DictFilter()
    df.add_value_filter("test",filter_level_min=5)
    df.add_regex_filter("regex_expr","test",filter_type=Filter.KEY,filter_level_min=5)
    test_dict = {"object":"test_object"}
    #x = Filter.KEY in iter(Filter)
    #Filter.
    #df.filter(test_dict)
    pass

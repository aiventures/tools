""" recursive iteration through a dict """

import json
import copy
import hashlib
import re
import logging
import sys
from enum import Enum
# using the tree util to create a tree
from tools.util.tree import Tree
# from datetime import datetime as DateTime

logger = logging.getLogger(__name__)

class Filter(Enum):
    """ filter values """
    OBJECT  = "filter_object"
    TYPE = "filter_type"
    REGEX = "filter_regex"
    VALUE = "filter_value"
    EQUAL = "filter_equal"
    CONTAINS = "filter_contains"
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
    KEYLIST = "keylist"
    LEVEL = "level"

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

    def add_filter(self,filter_value,**kwargs):
        """ adding filters with generic interface

        Args:
            filter_value (object): the filter value
            filter_type (Filter, optional):
                Filter.CONTAINS: filter_value needs to be cotained in dict field
                Filter.EQUAL: value in dict needs to be equal with filter_value
                Filter.REGEX: Match given by regex expression (added as filter_regex kwargs)
            Defaults to Filter.VALUE.
            filter_object (Filter, optional): Which object in dict is to be filtered. Defaults to
                Filter.KEY Filter by key field in dict
                Filter.OBJECT / Filter.VALUE Filter by object/value field in dictionary
        """

        # default filter dict
        filter_dict = { Filter.VALUE:filter_value,
                        Filter.TYPE:Filter.CONTAINS,
                        Filter.OBJECT:Filter.KEY   }

        # add overwrite using kwargs
        for k,v in kwargs.items():
            # try to get Filter Enum
            filter_enum = Filter.from_value(k)
            if not filter_enum:
                continue
            filter_dict[filter_enum]=v

        filter_type = filter_dict[Filter.TYPE].value.replace("filter_","")
        filter_value = filter_dict[Filter.VALUE].replace("filter_","")
        filter_object = filter_dict[Filter.OBJECT].value.replace("filter_","")
        logger.debug(f"Adding Filter for [{filter_object}][{filter_type}]:({filter_value}), [{len(filter_dict)-3}] additional params")
        self._filters.append(filter_dict)

    def add_value_filter(self,filter_value,**kwargs):
        """ convenience method for value filter, simply filter for any values """
        self.add_filter(filter_value,**kwargs)

    def add_regex_filter(self,regex:str,**kwargs):
        """ convenience method for regex filter """
        kwargs[Filter.TYPE.value]=Filter.REGEX
        self.add_filter(filter_value=regex,**kwargs)

    def clear_filters(self):
        """ removes all filters """
        logger.debug(f"Clear [{len(self._filters)}] Object Filters")
        self._filters = []

    def _filter_level(self,level,object_filter:dict)->bool:
        """ filter by level """
        filters_passed = []
        level_min = object_filter.get(Filter.LEVEL_MIN)
        if level_min:
            filters_passed.append( True if level >= level_min else False )
        level_max = object_filter.get(Filter.LEVEL_MAX)
        if level_max:
            filters_passed.append( True if level <= level_max else False )
        level_range = object_filter.get(Filter.LEVEL_RANGE)
        if level_range:
            level_min = level_range[0]
            level_max = level_range[1]
            filters_passed.append( True if level >= level_min else False )
            filters_passed.append( True if level <= level_max else False )

        return all(filters_passed)

    def filter(self,info_dict:dict,verbose:bool=False)->bool:
        """ filter dict as defined by the DictProps Enum
            if verbose is set, detailed filtering process is shown

        """
        # validate input
        validated_properties = [l for l in list(info_dict.keys()) if l in self._allowed_dict_props]
        if not validated_properties:
            logger.warning(f"passed dict has no proper keys ({list(info_dict.keys())})")
            return
        # get filterr object
        obj_key = info_dict.get(DictProps.KEY.value)
        obj_value = info_dict.get(DictProps.OBJECT.value)
        level = info_dict.get(DictProps.LEVEL.value)
        # keylist = info_dict.get(DictProps.KEYLIST.value)
        filters_passed = []
        for object_filter in self._filters:
            # get the object to be filtered
            filter_object = object_filter.get(Filter.OBJECT)
            filter_value = object_filter.get(Filter.VALUE)
            if filter_object == Filter.KEY:
                filtered_object = obj_key
            elif filter_object == Filter.VALUE or filter_object == Filter.OBJECT:
                filtered_object = obj_value
            else:
                filtered_object = None
            if not filtered_object:
                logger.warning(f"Object {filter_object} not found in {info_dict}")
                continue

            # filter by type
            filter_type = object_filter.get(Filter.TYPE)
            if filter_type == Filter.CONTAINS:
                filters_passed.append( True if filter_value in filtered_object else False )
            elif filter_type == Filter.EQUAL:
                filters_passed.append( True if filter_value == filtered_object else False )
            elif filter_type == Filter.REGEX:
                regex_match = re.findall(filter_value,filtered_object)
                filters_passed.append( True if len(regex_match) > 0 else False )
            else:
                logger.warning(f"Filter {object_filter} has no valid Filter Type")
                continue

            # filter by level
            level_passed = None
            if level:
                level_passed = self._filter_level(level,object_filter)
                filters_passed.append(level_passed)

            if verbose:
                logger.debug(f"#### FILTERING {info_dict}")
                logger.debug(f"FILTER       : {object_filter}")
                logger.debug(f"FILTER OBJECT [{filter_object.name}] {filtered_object} {filter_type.name} {filter_value}, level pass: {level_passed}")
                logger.debug(f"FILTER RESULT: {filters_passed} => {all(filters_passed)}")

        logger.debug(f"Filter {info_dict}, filters_passed: {filters_passed}")
        return all(filters_passed)

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
                # return d
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
    if True:
        test_struc = ('{"k1":"value1",'
                    '"test_key":500,'
                    '"k2":{"k2.1":5,"k2.2":"v2.2",'
                    '"k2.3":["l1","test value","l3"]}}')
        test_dict = json.loads(test_struc)
        dict_parser = DictParser(test_dict)

    df = DictFilter()

    test_dict = {"key":"this is my test_key","object":"this is my test_object","level":4}
    # straightforward: filter for filtering key
    verbose = True
    df.add_value_filter("test",filter_level_min=2)
    # passed = df.filter(test_dict,verbose=verbose)
    df.clear_filters()
    # test whether object contains "object"
    df.add_regex_filter("object",filter_object=Filter.OBJECT,filter_level_min=0)
    passed = df.filter(test_dict,verbose=verbose)
    df.clear_filters()
    # test whether key contains "key"
    df.add_regex_filter("key",filter_object=Filter.KEY,filter_level_min=0)
    passed = df.filter(test_dict,verbose=verbose)
    df.clear_filters()
    # same thing but with contains filter
    df.add_filter(filter_value="key",filter_object=Filter.KEY,filter_type=Filter.CONTAINS)
    passed = df.filter(test_dict,verbose=verbose)
    df.clear_filters()
    # Onyl EQUAL FILTER, TEST FOR DICT VALUE
    df.add_filter(filter_value="this is my test_object",filter_object=Filter.VALUE,filter_type=Filter.EQUAL)
    passed = df.filter(test_dict,verbose=verbose)
    df.clear_filters()

    # a very simple line that could be part of a dictionary hierarchy
    #x = Filter.KEY in iter(Filter)
    #Filter.
    # df.filter(test_dict)
    pass

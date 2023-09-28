import json
import copy
import hashlib
# using the tree utilk to create a tree
from tools.tree_util import Tree

""" test recursion """
object_tree = {}

def get_hash(s: str):
    """ calculate hash """
    hash_value = hashlib.md5(s.encode()).hexdigest()
    return hash_value

def get_object_id(obj):
    return get_hash(str(obj))

def itemized_dict(d:dict,parent_id):
    """ turns lists into dicts, each list item gets an index """
    # logging.debug("START")
    for k, v in d.copy().items():
        obj_id = get_hash(str(k)+str(id(d)))
        object_tree[obj_id]={"parent":parent_id,"key":k,"obj":v,"obj_type":type(v)}
        if isinstance(v, dict): # For DICT
            d[k]=itemized_dict(v,obj_id)
        elif isinstance(v, list): # itemize LIST as dict
            itemized = {"(L)"+str(i):item for i,item in enumerate(v)}            
            d[k] = itemized
            itemized_dict(d[k],obj_id)
        elif isinstance(v, str): # Update Key-Value
            d.pop(k)
            d[k] = v
        else:
            d.pop(k)
            d[k] = v
            return d
    return d

test_struc = '{"k1":"value1","k2":{"k2.1":"v2.1","k2.2":"v2.2","k2.3":["l1","l2","l3"]}}'
test_dict = json.loads(test_struc)
d_new=copy.deepcopy(test_dict)
d_new=itemized_dict(d_new,"ROOT")
object_tree={"ROOT":{"parent":None}}
d_new=itemized_dict(d_new,"ROOT")

my_tree=Tree()
my_tree.create_tree(object_tree)
my_root=my_tree.root_id
my_hierarchy=my_tree.hierarchy
my_levels=my_tree.max_level

pass
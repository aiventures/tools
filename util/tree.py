""" class to generically handle parent-child relationships """

import logging
import sys
import json
import yaml
logger = logging.getLogger(__name__)

class Tree():
    """ Tree Object """

    PARENT="parent"
    LEVEL="level"
    CHILDREN="children"
    NAME="name"
    NODE="node"
    ROOT="root"

    def __init__(self) -> None:
        logger.debug("Tree Constructor")
        self._nodes_dict = None
        self._hierarchy_nodes_dict = None
        self._root=None
        self._name_field=Tree.NAME
        self._parent_field=Tree.PARENT
        self._max_level=0

    @property
    def hierarchy(self):
        """ tree hierarchy """
        return self._hierarchy_nodes_dict

    @property
    def max_level(self):
        """ max level of tree """
        return self._max_level

    @property
    def root_id(self):
        """ nodes """
        return self._root

    def create_tree(self,nodes_dict:dict,name_field:str=None,parent_field:str=None):
        """ creates tree from passed dict root node is when there is a Non field
            returns tree structure
        """
        logger.debug("Create Tree")
        self._nodes_dict = {}
        if name_field:
            self._name_field = name_field

        if parent_field:
            self._parent_field = parent_field

        for node_id,node_info in nodes_dict.items():
            if isinstance(node_info,str) or isinstance(node_info,int):
                name=str(node_info)
                parent=node_info
            elif isinstance(node_info,dict):
                name=node_info.get(self._name_field,str(node_id))
                parent=node_info.get(self._parent_field)

            if parent is None:
                self._root=node_id

            node_dict={Tree.NODE:node_id,
                       self._name_field:name,
                       self._parent_field:parent}
            self._nodes_dict[node_id]=node_dict

        self._hierarchy_nodes_dict = self._get_hierarchy()

        return self._nodes_dict

    def _get_hierarchy(self):
        """ creates children hierarchy """
        logger.debug("Tree Get Node Hierarchy")

        all_nodes=[]

        def get_children_recursive(nodes):
            """ build up hierarchy """
            logger.debug(f"get children for nodes {nodes}")
            children=[]
            if len(nodes)>0:
                for parent_node in nodes:
                    for node_id,parent_id in parent_dict.items():
                        if parent_id == parent_node:
                            children.append(node_id)
                for children_id in children:
                    parent_dict.pop(children_id)
                if children:
                    all_nodes.append(children)
                    get_children_recursive(children)
            else:
                return

        parent_dict={}
        # get a simple dictionary with node ids and parent
        root_node=[]
        hierarchy_nodes_dict={}
        for node_id, node_dict in self._nodes_dict.items():
            if node_dict.get(self._parent_field):
                parent_dict[node_id]=node_dict.get(self._parent_field)
            else:
                parent_dict[node_id]=None
                root_node.append(node_id)
                all_nodes.append(root_node)
            hier_node_dict={}
            hier_node_dict[self._parent_field]=parent_dict[node_id]
            hier_node_dict[self._name_field]=node_dict.get(self._name_field)
            hier_node_dict[Tree.CHILDREN]=[]
            hierarchy_nodes_dict[node_id]=hier_node_dict

        # create layered relations
        get_children_recursive(root_node)
        # determine level
        level=0
        for nodes in all_nodes:
            for node in nodes:
                hierarchy_nodes_dict[node][Tree.LEVEL]=level
            level+=1
        self._max_level=level

        # get children
        for node,hierarchy_node_dict in hierarchy_nodes_dict.items():
            parent = hierarchy_node_dict.get(self._parent_field)
            if parent:
                hierarchy_nodes_dict[parent][Tree.CHILDREN].append(node)

        return hierarchy_nodes_dict

    def get_children(self,node_id,only_leaves=False)->list:
        """ gets children nodes as list (option to select only leaves) """
        logger.debug("Get Children Nodes")
        children_nodes = []
        parent_node=self._hierarchy_nodes_dict.get(node_id)

        if not parent_node:
            logger.warning(f"Parent node with node id {node_id} was not found")
            return


        def get_children_recursive(child_list):
            logger.debug(f"get children recursive {child_list}")
            new_children=[]
            if len(child_list) > 0:
                for child in child_list:
                    children_nodes.append(child)
                    new_children.extend(self._hierarchy_nodes_dict.get(child)[Tree.CHILDREN])
                get_children_recursive(new_children)
            else:
                return

        parent_children=parent_node[Tree.CHILDREN]
        get_children_recursive(parent_children)

        if only_leaves:
            leaves=[]
            for child in children_nodes:
                child_info = self._hierarchy_nodes_dict.get(child)
                if not child_info.get(Tree.CHILDREN):
                    leaves.append(child)
            children_nodes=leaves

        return children_nodes

    def get_predecessors(self,node_id)->list:
        """ gets the parent nodes in a list """
        parents=[]
        current_node=self._hierarchy_nodes_dict.get(node_id)
        while current_node is not None:
            parent_id=current_node[self._parent_field]
            if parent_id:
                current_node=self._hierarchy_nodes_dict.get(parent_id)
                parents.append(parent_id)
            else:
                current_node=None

        return parents

    def get_siblings(self,node_id,only_leaves=True)->list:
        """ gets the list of siblings and only leaves """

        def is_leaf(node_id):
            """ checks if node is leaf """
            node_info=self._hierarchy_nodes_dict.get(node_id)
            if not node_info.get(Tree.CHILDREN):
                return True
            else:
                return False

        siblings=[]
        current_node=self._hierarchy_nodes_dict.get(node_id)
        if not current_node:
            logger.warning(f"Node with ID {node_id} not found")
            return
        parent_id=current_node.get(self._parent_field)
        if parent_id:
            parent_node=self._hierarchy_nodes_dict.get(parent_id)
            siblings=parent_node.get(Tree.CHILDREN)
            siblings=[elem for elem in siblings if not elem==node_id]

        if only_leaves:
            siblings=[elem for elem in siblings if is_leaf(elem)]

        return siblings

    def get_key_path(self,node_id):
        """ returns the keys list required to navigate to the element """
        keys = []
        # get all predecessors
        predecessor_ids = self.get_predecessors(node_id)
        node_ids = [node_id,*predecessor_ids]
        for id in node_ids:
            tree_elem = self.get_element(id) 
            if not self._name_field:
                keys.append(tree_elem["node"])
            else:
                keys.append(tree_elem[self._name_field])
        keys.reverse()
        return keys

    def get_leaves(self)->list:
        """ returns the leaves of the tree """
        leaves=[]
        for node,node_info in self._hierarchy_nodes_dict.items():
            if node_info.get(Tree.CHILDREN):
                continue
            leaves.append(node)
        return leaves

    def get_leaf_siblings(self)->dict:
        """ gets sibling leaves alongside with parent node path """
        leaves = self.get_leaves()
        leaf_siblings = []
        # processed list
        processed=dict(zip(leaves,len(leaves)*[False]))
        for leaf in leaves:
            if processed[leaf]:
                continue
            siblings=[leaf]
            siblings.extend(self.get_siblings(leaf))
            for sibling in siblings:
                processed[sibling]=True
            predecessors=self.get_predecessors(leaf)
            leaf_siblings.append([siblings,predecessors])

        return leaf_siblings

    def get_nested_tree(self)->dict:
        """ gets the tree as nested dict """
        logger.info("Get nested Tree")
        node_hierarchy = self._hierarchy_nodes_dict
        # current_nodes = [self.root_id]
        nested_tree={self.root_id:{}}

        def get_next_nodes_recursive(nodes:dict):
            if nodes:
                for node,node_children in nodes.items():
                    children_nodes=node_hierarchy[node][Tree.CHILDREN]
                    children_dict={}
                    for children_node in children_nodes:
                        children_dict[children_node]={}
                    node_children.update(children_dict)
                    get_next_nodes_recursive(node_children)
            else:
                pass

        get_next_nodes_recursive(nested_tree)
        return nested_tree

    def get_reverse_tree_elements(self)->dict:
        """ gets the elements dict of nested tree elements """
        logger.info("Get reverse nested Tree")
        nested_tree = self.get_nested_tree()
        root_key=list(nested_tree.keys())[0]
        reverse_tree={root_key:nested_tree[root_key]}

        def get_next_nodes_recursive(nodes:dict)->dict:
            if nodes:
                next_nodes={}
                for node,node_info in nodes.items():
                    reverse_tree[node]=node_info
                    next_nodes.update(node_info)
                get_next_nodes_recursive(next_nodes)
            else:
                pass

        get_next_nodes_recursive(reverse_tree)
        return reverse_tree

    def get_element(self,node_id):
        """ returns the element for given node id"""
        element = self._nodes_dict.get(node_id)
        if not element:
            logger.warning(f"Element with node id {node_id} not found in tree")
            return
        return element

    def json(self)->str:
        """ returns json string """
        logger.debug("json()")
        nested_tree=self.get_nested_tree()
        return json.dumps(nested_tree,indent=3)

    def yaml(self)->str:
        """ returns yaml string """
        logger.debug("yaml()")
        nested_tree=self.get_nested_tree()
        return yaml.dump(nested_tree)

    def __str__(self)->str:
        return self.json()

if __name__ == "__main__":
    loglevel=logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")
    tree={
        1:{"parent":None,"value":"value 1"},
        2:{"parent":1},
        4:{"parent":2},
        5:{"parent":2},
        3:{"parent":1},
        6:{"parent":3},
        7:{"parent":6},
        8:{"parent":6},
        9:{"parent":6},
    }

    tree={
        1:{"parent":None,"value":"value 1"},
        2:{"parent":1,"value":"value 3"},
        4:{"parent":2,"value":"value 4"},
        5:{"parent":2,"value":"value 5"},
        3:{"parent":1,"value":"value 3"},
        6:{"parent":3,"value":"value 6"},
        7:{"parent":6,"value":"value 7"},
        8:{"parent":6,"value":"value 8"},
        9:{"parent":6,"value":"value 9"},
    }

    my_tree=Tree()
    # use name to get a different field 
    # my_tree.create_tree(tree,name_field="value")
    my_tree.create_tree(tree)
    my_root=my_tree.root_id
    my_hierarchy=my_tree.hierarchy
    my_levels=my_tree.max_level

    children=my_tree.get_children(1,only_leaves=False)
    print(children)
    my_parents=my_tree.get_predecessors(8)
    my_siblings=my_tree.get_siblings(8)
    my_leaves=my_tree.get_leaves()
    my_leave_siblings=my_tree.get_leaf_siblings()
    my_nested_tree=my_tree.get_nested_tree()
    my_reverse_tree=my_tree.get_reverse_tree_elements()
    my_element = my_tree.get_element(4)
    my_key_path = my_tree.get_key_path(7)
    # display tree as json
    #print("TREE AS JSON")
    #print(json.dumps(my_nested_tree,indent=3))
    #print("TREE AS YAML")
    #print(yaml.dump(my_nested_tree))
    print(str(my_tree))
    print(my_tree.yaml())

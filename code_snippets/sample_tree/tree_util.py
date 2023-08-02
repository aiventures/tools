""" class to generically handle parent-child relationships """

import logging
import sys
logger = logging.getLogger(__name__)

class Tree():

    PARENT="parent"
    LEVEL="level"
    CHILDREN="children"
    NAME="name"
    NODE="node"

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

    def get_children(self,node_id)->list:
        """ gets children nodes as list"""
        logger.debug("Get Children Nodes")
        children_nodes = []
        parent_node=self._hierarchy_nodes_dict.get(node_id)

        if not parent_node:
            logger.warn(f"Parent node with node id {node_id} was not found")
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

        return children_nodes

    def get_predecessors(self,node_id)->list:
        """ gets the parent nodes in a list """
        parents=[]
        logger.debug("Get Parent Nodes")
        current_node=self._hierarchy_nodes_dict.get(node_id)
        while current_node is not None:
            parent_id=current_node[self._parent_field]
            if parent_id:
                current_node=self._hierarchy_nodes_dict.get(parent_id)
                parents.append(parent_id)
            else:
                current_node=None

        return parents

    def get_siblings(self,node_id)->list:
        """ gets the list of siblings """
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

        return siblings

if __name__ == "__main__":
    loglevel=logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout,datefmt="%Y-%m-%d %H:%M:%S")    
    tree={
        1:{"parent":None},
        2:{"parent":1},
        4:{"parent":2},
        5:{"parent":2},
        3:{"parent":1},
        6:{"parent":3},
        7:{"parent":6},
        8:{"parent":6},
        9:{"parent":6},
    }

    my_tree=Tree()
    my_tree.create_tree(tree)
    my_root=my_tree.root_id
    my_hierarchy=my_tree.hierarchy
    my_levels=my_tree.max_level

    # tree_dict=my_tree.create_tree(tree)

    #my_hierarchy=my_tree._get_hierarchy()
    children=my_tree.get_children(1)
    my_parents=my_tree.get_predecessors(8)
    my_siblings=my_tree.get_siblings(8)
    pass
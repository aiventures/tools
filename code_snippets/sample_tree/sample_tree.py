import logging
import copy
logger = logging.getLogger(__name__)

# tree with parents
tree={
    1:{"parent":None},
    2:{"parent":1},
    4:{"parent":2},
    5:{"parent":2},
    3:{"parent":1},
    6:{"parent":3},
    7:{"parent":6},
    8:{"parent":6},
}

tree_copy = copy.deepcopy(tree)

checked_nodes=[]

def get_root():
    root_node=None
    for id,info in tree_copy.items():
        if not info["parent"]:
            root_node = id
            break
    logger.info(f"Root Node {root_node}")
    return root_node
            

all_children=[]
def get_children(nodes):
    """ returns children levels per level """
    children=[]
    if len(nodes)>0:
        for parent_node in nodes:
            for node_id,info in tree_copy.items():        
                if parent_node == info["parent"]:
                    children.append(node_id)
        for children_id in children:
            tree_copy.pop(children_id)
        if children:
            all_children.append(children)
        get_children(children)
    else:
        return

if __name__ == "__main__":    
    num_nodes=len(tree_copy.keys())
    # check for root element
    node = get_root()
    all_children = [node]
    root_node=[node]
    tree_copy.pop(node)
    get_children(root_node)
    pass

    # checked_nodes.append(node)
    #while num_nodes > len(checked_nodes):
    #    nodes

    

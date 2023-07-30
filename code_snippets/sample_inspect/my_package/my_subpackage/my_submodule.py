class MySubModule():
    """ simulation of module in a subpackage """
    submoduleclass_class_att1="ExternalClass.att1"
    def __init__(self):
        self.submoduleclassatt="self.submoduleclassatt"
        
    def submodulemethod(self,s:str)->str:
        print("a submodulestr")
        return s
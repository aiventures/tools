""" Class to simulate dependecy for unit test  """
class ReferedClass():
    """ dummy refeenced class """
     
    def __init__(self) -> None:
        self.refered_class_attribute = "<ReferedClassLASS> ***original***"

    def get_refered_class_attribute(self):
        return self.refered_class_attribute
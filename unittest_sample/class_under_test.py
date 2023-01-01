""" Dummy Class to use unittests on """

from unittest_sample.refered_class import ReferedClass

class ClassUnderTest():
    """ Dummy Class to use unittests on """

    def __init__(self) -> None:
        self.cut_attribute = "cut_attribute"
        print("<ClassUnderTest>: CONSTRUCTOR")
        self.ref_cls = ReferedClass()

    def method_cut(self):
        """ dummy method """
        ref_att= self.ref_cls.get_refered_class_attribute()
        print(f"<ClassUnderTest>-method_cut: REF ATTRIBUTE IS {ref_att}")
        return ref_att

    def _method_internal(self,s):
        """ some internal method """
        print(f"<ClassUnderTest>-_method_internal: PASSED STRING IS  {s}")
        return s+"_METHOD_INTERNAL"

    def method_call_internal(self,s):
        """ a method calling an internal method """
        print(f"<ClassUnderTest>-method_call_internal with {s}")
        s = self._method_internal(s)
        print(f"<ClassUnderTest>-method_call_internal: result is {s}")
        return s

    def method_complex(self,p1,p2):
        """ checking autospec """
        print(f"<ClassUnderTest>-method_call_internal with {p1} and {p2}")
        return p1+"_"+p2

if __name__ == '__main__':
    cut = ClassUnderTest()
    print("------------")
    cut.method_cut()
    print("------------")
    cut.method_call_internal("TESTING")



""" Class Boilerplate """
import sys
import logging

logger = logging.getLogger(__name__)

class MyClass():
    """ Template """
    def __init__(self) -> None:
        """ Constructor """
        pass

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")    

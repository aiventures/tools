""" just testing the sysarg stuff to directly pass over arguments """
""" Class Boilerplate """
import sys
import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")    
    args = sys.argv
    logger.info(f"ARGS {args}")
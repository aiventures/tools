""" set up logging programmatically
    https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    File Handlers 
    https://docs.python.org/3/library/logging.handlers.html
    Logging In General
    https://rmcomplexity.com/article/2020/12/01/introduction-to-python-logging.html
"""
import logging
import os
import sys
from logging import Handler
from logging import Filter as LoggingFilter
from logging import LogRecord
from api import my_api

logger = logging.getLogger("my_logger")

def filter_keyword(record:LogRecord):
    " simply lools for a keyword  "
    msg=record.getMessage()    
    if "#filter" in msg:
        print(f"filter record will be ignored: {msg}, attributes:")
        print(record.__dict__)
        return False
    else:
        return True

def get_formatter():
    """ set up formatter """
    format_s="{levelname:8s}; {asctime:s}; {name:<25s} {funcName:<15s} {lineno:4d}; {message:s}"
    return logging.Formatter(format_s,style="{")

def configure_handler(handler:Handler):
    """ adjust handler """
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(get_formatter())

def get_filehandler():
    """ filehandler  """
    module_path=os.path.dirname(os.path.abspath(__file__)) # get the log config file
    log_path = os.path.join(module_path,"log\log_example.log")
    fh = logging.FileHandler(log_path)
    configure_handler(fh)
    return fh

def get_streamhandler():
    """ streamhandler """
    sh = logging.StreamHandler(sys.stdout)
    configure_handler(sh)
    return sh


def test_log():
    print("test_log")
    logger.info("main logger Testing Info")
    logger.debug("main logger Testing Debug")
    logger.warning("main logger Testing Warning")
    logger.error("main logger Testing Error")
    # this should bre filtered
    logger.error("logger containing #filter keyword ")

def main():
    # set root level > DEBUG SHOULD BE FILTERED
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # call the api function and check for log > nothing should happen
    my_api.my_api_func()
    # adding a stream handler will start logging
    my_api.logger.addHandler(get_streamhandler())
    my_api.my_api_func()

if __name__ == "__main__":
    print(__name__,sys.modules[__name__])
    # print(sys.modules.keys())
    main()
import logging
from logging import NullHandler

logger = logging.getLogger(__name__)
s_out=f"Logging from module {__name__}, package {__package__}, file {__file__}"
# logger.addHandler(NullHandler())
print(s_out)
handlers=logger.handlers
print(f"handlers: {handlers}")
# logger.propagate=True
logger.debug(s_out)

def my_api_func():
    print("my_api_func")
    logger.info("DEBUG: my_api_func()")
    logger.info("INFO: my_api_func()")
    logger.warn("WARN: my_api_func()")
    logger.error("ERROR: my_api_func()")
    return None

def my_api_func2():
    print("CALL my_api_func2, handlers",logger.handlers)
    logger_parent = logger.parent    
    print("logger parent",logger_parent,"handler",logger_parent.handlers)
    # logger.propagate = True
    logger.info("DEBUG: my_api_func2()")
    logger.info("INFO: my_api_func2()")
    logger.warn("WARN: my_api_func2()")
    logger.error("ERROR: my_api_func2()")
    return None    
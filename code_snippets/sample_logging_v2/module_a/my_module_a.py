import logging


logger = logging.getLogger(__name__)
s_out=f"Logging from module {__name__}, package {__package__}, file {__file__}"
print(s_out)
logger.debug(s_out)

def my_a_func():
    print("my_a_func")
    logger.info("INFO: my_a_func()")
    logger.warn("WARN: my_a_func()")
    logger.error("ERROR: my_a_func()")
    return None

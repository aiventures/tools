""" main module 
    Diable logging modules
    https://stackoverflow.com/questions/35325042/python-logging-disable-logging-from-imported-modules
    https://stackoverflow.com/questions/35325042/python-logging-disable-logging-from-imported-modules


"""
import logging
from logging.config import dictConfig
from logging import Filter as LoggingFilter
import os
from tools_console.persistence  import Persistence
from api import my_api

print(f"Logging Name, module name {__name__}, package {__package__}, file {__file__}")

# activate Null Logger (deactivate)
null_logging = False

# activate API logging by adding a configuration entry into dictionary
activate_api_logging = True

# __name__ is main
logger_name = __name__ # name would be name of podule __main__ in this case
# in the config we have configured loggers named sample_logging_v2
# 
logger_name = "sample_logging_v2"

logger = logging.getLogger(logger_name)
sublogger = logging.getLogger(logger_name+".sublog")

class LoggingConfig():
    """ logging config """

    @staticmethod
    def get_config(fp:str)->dict:
        """ read config file """
        logger.info("Read Log Config file: %s",fp)
        if not os.path.isfile(fp):
            logger.error("Log Info file %s not found",fp)
            return
        config = Persistence.read_json(fp)
        # logger.debug("Config file: %s")
        return config

    @staticmethod
    def set_config(fp:str)->None:
        pass

class LevelFilter(LoggingFilter):
    """
    https://stackoverflow.com/a/7447596/190597
    https://stackoverflow.com/questions/18058817/python-logging-propagate-messages-of-level-below-current-logger-level

    """
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno >= self.level

class TestLogging():
    """ Sample Class for test logging """
    def test_log(self):
        print("test_log")
        logger.info("main logger Testing Info")
        logger.debug("main logger Testing Debug")
        logger.warning("main logger Testing Warning")
        logger.error("main logger Testing Error")
        # logger.exception("main logger Testing Exception")

    def test_sublog(self):
        print("test_sublog")
        sublogger.info("main sublogger Testing Info")
        sublogger.debug("main sublogger Testing Debug")
        sublogger.warning("main sublogger Testing Warning")
        sublogger.error("main sublogger Testing Error")
        # https://stackoverflow.com/questions/28302733/none-in-python-log-file
        # sublogger.exception("main sublogger Testing Exception")        

def main():
    print("############## main ############## ")
    logging.basicConfig(level=logging.DEBUG) # start logging
    module_path=os.path.dirname(os.path.abspath(__file__)) # get the log config file
    os.chdir(module_path)

    # set up logger
    log_config_dict = LoggingConfig.get_config(os.path.join(module_path,"log_config.json"))
    
    if activate_api_logging:
        # sample_logging_v2
        print("CONFIG FORT APIXXX",log_config_dict["loggers"]["apixxx"])
        log_config_dict["loggers"]["api"]=log_config_dict["loggers"]["apixxx"]


    if null_logging:
        print("-- SETTING TO NULL LOGGER ---")
        log_config_dict["loggers"]["root"]= log_config_dict["loggers"]["null_logger"]
        log_config_dict["loggers"]["sample_logging_v2"]= log_config_dict["loggers"]["null_logger"]
        # sample_logging_v2.sublog will be logged however 

    dictConfig(log_config_dict)
    # special set up / set up root logger that only logs critical logs
    root_log=logging.getLogger("root")
    root_log.setLevel(logging.WARN)
    logfilter=LevelFilter(logging.ERROR)
    root_log.addFilter(logfilter)    
    tl = TestLogging()

    print("--- root logger---")
    root_log.info("rootlogger info shouldn't be displayed")
    root_log.error("rootlogger error")
    print("--special logger ----------")
    tl = TestLogging()
    tl.test_log()
    print("--sub logger ----------")
    sublogger.setLevel(logging.WARN)    
    tl.test_sublog()    
    print("--LOGGING methods ----------")
    print(f"log parent: {logger.parent.name}")
    print(f"sublog parent: {sublogger.parent.name}")
    print("log handlers",logger.handlers)
    print("log filters",logger.filters)
    print("log level",logger.level)
    print("effective log level",logger.getEffectiveLevel())
    print("effective sub level",sublogger.getEffectiveLevel())    
    print("--LOGGING ADDITIONAL METHODS ----------")   
    from module_a.my_module_a import my_a_func
    my_a_func()
    print("--- loggers ---")
    loggers = [name for name in logging.RootLogger.manager.loggerDict]
    print(loggers)    
    print("api handlers:",logging.getLogger("api").handlers)       
    print("api.my_api handlers:",logging.getLogger("api.my_api").handlers)
    print("--LOGGING API Null Handler ----------")           
    #logging.getLogger("api.my_api").addHandler(logging.NullHandler())
    # because the logger is Null Handler it shouldnt be logged
    # if it is configured, in config json then it is logged
    print("Logging my_api_func with Null Handler (shouldn't log)")    
    my_api.my_api_func()
    # my_api.my_api_func2()    
    # # print(log_config_dict)

    # logging.getLogger().error("TEST ERROR")

if __name__ == "__main__":
    main()
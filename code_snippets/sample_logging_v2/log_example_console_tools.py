
""" testing console tool log """
import logging
from tools_console.log_util import LoggingConfig
from api.my_api import my_api_func

logger = logging.getLogger(__name__)

my_config = LoggingConfig()
config_dict = my_config.config
# if this is not called no logging will be output besides default output 
# my_config.configure()

# logging.getLogger().setLevel(logging.INFO)
def test():
    print("CALL test()")
    logger.debug("LOGGER DEBUG")
    logger.info("LOGGER INFO")
    logger.warning("LOGGER WARN")
    logger.error("LOGGER ERROR")
test()
my_api_func()

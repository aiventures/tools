"""  api module configurable logging see
     https://realpython.com/python-logging-source-code/#the-logrecord-class
"""

import logging
from logging import NullHandler
print(f"API(): __init__, handler name: {__name__}")
logger=logging.getLogger(__name__)
logger.addHandler(NullHandler())
handlers=logging.getLogger(__name__).handlers
# logger.setLevel(logging.ERROR)
print(f"handlers: {handlers}")
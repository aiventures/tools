""" Constant Definitions """

import logging
from enum import Enum

class CONFIG(Enum):
    """ CONFIG FILE MAIN CATEGORIES DEFINITION  """
    EXECUTABLE = "Executable Programs (absolute or filename only)"
    PATTERN = "Generating Commands based on Patterns"
    PATH = "Links to frequently used Paths"
    FILE = "Links to frequently used Files"
    SCRIPT = "Links to Win Scripts like shell scripts, bat files"
    SCRIPT_BASH = "Links to Bash Scripts"
    ENVIRONMENT_WIN = "Environment Variables (SET) for Windows Command Line"
    ENVIRONMENT_BASH = "Environment Variables (SET) for Bash Command Line"
    SHORTCUT = "Shortcut to any of the configuration elements above"
    CMD_PARAM = "Command Line Parameters for any template scripts"
    CMD_SUBPARSER = "Definition of Subparser Configuration"

class EXPORT(Enum):
    """ Exporting Options """
    ENV_WIN = "Export as Windows Command Line BAT File (as List)"

class CONFIG_ATTRIBUTE(Enum):
    """ available config fields """
    EXECUTABLE = "Executable Programs (absolute or filename only)"
    PATH = "Path (absolute or pointing to one in Path segment)"
    REFERENCE = "Configuration Reference (when using Path Pointing to COnfig)"
    FILE = "Filename (absolute or pointing to one in Path segment)"
    HELP = "Short Documentation"
    PATTERN = "String Pattern to Be Evaluated"
    TYPE = "Parameter Type"
    PARAM = "Parameter"
    VALUE = "Value attrubute (for example for Env Variables)"
    RESOLVED_PATH_REF = "Resolved Path Reference"
    RESOLVED_FILE_REF = "Resolved File Reference"
    EXPORT = "Flag to export the attribute (as value enter the field to be exported)"

class LOGLEVEL(Enum):
    """ loglevel handling """
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

class PARSER_ATTRIBUTE(Enum):
    """ Configuration, each param is modeled as a dictionary """
    DESCRIPTION = "description"
    EPILOG      = "epilog"
    PROG        = "prog"
    PARAM       = "param"
    PARAM_SHORT = "param_short"
    DEFAULT     = "default"
    ACTION      = "action"
    DEST        = "dest"
    HELP        = "help"
    METAVAR     = "metavar" # used for help text
    TYPE        = "type"
    STORE_TRUE  = "store_true"
    STORE_FALSE = "store_false"
    VAR         = "variable"

class DEFAULT_PARSER_ATTRIBUTES(Enum):
    """ Default ARGPARSE PARAMETERS """
    FILE = "file"
    FILE_OUT = "file_out"
    CSV_SEPARATOR = "csv_separator"
    DECIMAL_SEPARATOR = "decimal_separator"
    LOGLEVEL = "loglevel"
    ADD_TIMESTAMP = "add_timestamp"

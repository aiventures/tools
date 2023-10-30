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
    CMD_MAP = "Mapping Rules for assigning CLI command to Command"

class EXPORT_OPTION(Enum):
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
    KEY = "Key attribute"
    VALUE = "Value attrubute (for example for Env Variables)"
    DEFAULT = "Default Value"
    RESOLVED_DEFAULT = "Resolved Default Parameters"
    RESOLVED_MAIN = "Resolved Main Parameters (main command, no subcommands)"
    RESOLVED_SUBPARSER = "Resolved Subcommand Parameters"
    RESOLVED_PATH_REF = "Resolved Path Reference"
    RESOLVED_FILE_REF = "Resolved File Reference"
    RESOLVED_VALUE = "Resolved Value (Submitted Value and Default)"
    EXPORT = "Flag to export the attribute (as value enter the field to be exported)"
    MAP = "CMD CLI to Configuration Mapping Rule"
    COMMAND = "Subparser Shortcut (from Command line, empty if main parser is used)"
    CMDPARAM_DEFAULT = "Default CMD Params"

class CMD_MAP(Enum):
    """ Mapping rules Command Line Client to Configurations """
    PATTERN = "Map Params to Pattern"

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

def key(enum:Enum):
    """ transforms an Enum key into lower case string """
    return enum.name.lower()

PATH_KEY = key(CONFIG_ATTRIBUTE.PATH)
FILE_KEY = key(CONFIG_ATTRIBUTE.FILE)
EXECUTABLE_KEY = key(CONFIG_ATTRIBUTE.EXECUTABLE)
TYPE = key(CONFIG_ATTRIBUTE.TYPE)
REF_KEY = key(CONFIG_ATTRIBUTE.REFERENCE)
RESOLVED_PATH = key(CONFIG_ATTRIBUTE.RESOLVED_PATH_REF)
RESOLVED_FILE = key(CONFIG_ATTRIBUTE.RESOLVED_FILE_REF)
HELP = key(CONFIG_ATTRIBUTE.HELP)
PATTERN_KEY = key(CONFIG_ATTRIBUTE.PATTERN)
PARAM_KEY = key(CONFIG_ATTRIBUTE.PARAM)
VALUE = key(CONFIG_ATTRIBUTE.VALUE)
EXPORT = key(CONFIG_ATTRIBUTE.EXPORT)
RESOLVED_DEFAULT = key(CONFIG_ATTRIBUTE.RESOLVED_DEFAULT)
RESOLVED_MAIN = key(CONFIG_ATTRIBUTE.RESOLVED_MAIN)
RESOLVED_SUBPARSER = key(CONFIG_ATTRIBUTE.RESOLVED_SUBPARSER)
KEY = key(CONFIG_ATTRIBUTE.KEY)
MAP = key(CONFIG_ATTRIBUTE.MAP)
SCRIPT = key(CONFIG.SCRIPT)
SCRIPT_BASH = key(CONFIG.SCRIPT_BASH)
ENVIRONMENT_WIN = key(CONFIG.ENVIRONMENT_WIN)
ENVIRONMENT_BASH = key(CONFIG.ENVIRONMENT_BASH)
SHORTCUT = key(CONFIG.SHORTCUT)
CMD_PARAM = key(CONFIG.CMD_PARAM)
CMD_SUBPARSER = key(CONFIG.CMD_SUBPARSER)
CMD_MAP_KEY = key(CONFIG.CMD_MAP)

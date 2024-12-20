""" constants file """
from copy import deepcopy

# Rule for applying any or all rules
APPLY_ANY = "any"
APPLY_ALL = "all"

# Rule: Include or Exclude Result Entry (=Invert search result) / Default is True 
RULE_INCLUDE = "rule_include"

# REGEX FIELD NAME DEFINITIONS 
RULE_NAME="name"
RULE_IGNORECASE="ignorecase"
RULE_IS_REGEX="is_regex"
RULE_RULE="rule"
RULE_REGEX="regex"
RULE_APPLY = "apply"
RULE_RESULTS = "results"
RULEDICT = {RULE_NAME:None,RULE_IGNORECASE:True,RULE_IS_REGEX:True,RULE_RULE:None,RULE_REGEX:None,RULE_APPLY:APPLY_ANY,RULE_INCLUDE:True}

# RULES FOR FILENAME SEARCH

# search in file name objects 
RULE_FILE = "rule_file"              # additional search attribute: rule for file object
RULE_FILENAME = "filename"           # search in in filename only
RULE_PATH = "path"                   # search in path
RULE_ABSOLUTE_PATH = "absolute_path" # search in absolute path
# Path Objects 
FILES_ABSOLUTE = "files_absolute"    # attribute in search result dict: absolute path
FILES = "files"                      # attribute in search result dict: file names
FILE_LINE = "line"                   # file line in file

# in file: look in complete text or line by line
RULE_FIND_BY_LINE = "find_by_line"

# search in content
RULE_FILE_CONTENT = "file_content"
RULEDICT_FILENAME = deepcopy(RULEDICT)
RULEDICT_FILENAME[RULE_FILE] = RULE_ABSOLUTE_PATH
RULEDICT_FILENAME[RULE_FIND_BY_LINE] = True

# Map File Rule to Field
# FILE_RULE_MAP = {  RULE_FILENAME:
#                 }

# supported file types
FILETYPE_XLS = "xlsx"
FILETYPE_CSV = "csv"
FILETYPE_MD = "md"
FILETYPE_TXT = "txt"
FILETYPE_BAK = "bak"
FILETYPE_YAML = "yaml"

# Supported file types for search
FILETYPES_SUPPORTED = [FILETYPE_CSV,FILETYPE_MD,FILETYPE_TXT,FILETYPE_BAK]

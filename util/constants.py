""" constants file """

# REGEX FIELD NAME DEFINITIONS 
RULE_NAME="name"
RULE_IGNORECASE="ignorecase"
RULE_IS_REGEX="is_regex"
RULE_RULE="rule"
RULE_REGEX="regex"
RULEDICT = {RULE_NAME:None,RULE_IGNORECASE:True,RULE_IS_REGEX:True,RULE_RULE:None,RULE_REGEX:None}

# RULES FOR FILENAME SEARCH

# search in file name objects 
RULE_FILE = "rule_file"
RULE_FILENAME = "filename"
RULE_PATH = "path"
RULE_ABSOLUTE_PATH = "absolute_path"

# search in content
RULE_FILE_CONTENT = "file_content"
RULEDICT_FILENAME = {RULE_NAME:None,RULE_IGNORECASE:True,RULE_IS_REGEX:True,RULE_RULE:None,
                 RULE_REGEX:None, RULE_FILE:RULE_ABSOLUTE_PATH}

# Rule for applying any or all rules
APPLY_ANY = "any"
APPLY_ALL = "all"

# Path Objects 
FILES_ABSOLUTE = "files_absolute"
FILES = "files"

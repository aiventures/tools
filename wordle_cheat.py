""" wordle cheat file ... forgive me, I am a non native speaker """

import traceback
import re

def read_file(f:str)->list:
    """ reading UTF8 txt File """
    lines = []
    try:
        with open(f,encoding="utf-8") as fp:    
            for line in fp:
                lines.append(line.strip().lower())
    except:
        print(f"Exception reading file {f}")
        print(traceback.format_exc())
    lines.sort()
    return lines

def get_fixed_letter_regex(fixed_letters):
    ANY_LETTER = r"\w"
    fixed_letters_regex_s = fixed_letters.replace("*",ANY_LETTER)
    return "("+fixed_letters_regex_s+")"

def get_variable_letter_regex(variable_letters):
    REGEX_MATCH_CHAR =r"(?=.*X)"
    variable_letters_regex_s = "".join([REGEX_MATCH_CHAR.replace("X",letter) for letter in variable_letters])
    return variable_letters_regex_s

def get_missing_letter_regex(missing_letters):
    REGEX_MATCH_CHAR = r"(?!.*X)"
    missing_letters_regex_s = "".join([REGEX_MATCH_CHAR.replace("X",letter) for letter in missing_letters])
    return missing_letters_regex_s

def get_regex(variable_letters:str,fixed_letters:str=None):
    if len(fixed_letters) == 0:
        fixed_letters = "*****"
    
    regex_fix_s = get_fixed_letter_regex(fixed_letters)
        
    if len(variable_letters) > 0:
        regex_var_s = get_variable_letter_regex(variable_letters)
    else:
        regex_var_s = ""
        
    if len(missing_letters) > 0:
        regex_missing_s = get_missing_letter_regex(missing_letters)
    else:
        regex_missing_s = ""        
    
    return re.compile(regex_var_s + regex_missing_s + regex_fix_s)

# file containing five letter words 
# check out GitHub Repo for sources
f = r"C:\<file to>\FiveLetterWords.txt"

words = read_file(f)
# list of fixed position lettes * is wildcard
fixed_letters = "***l*"
# list of variable letters
variable_letters = "da"
# list of non contained characters
missing_letters = "i"
regex = get_regex(variable_letters,fixed_letters)
# output words that match fixed and variables 
print([word for word in words if regex.match(word)])
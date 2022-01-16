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

def get_misplaced_letter_regex(misplaced_letter_list):
    ANY_LETTER = r"\w"
    misplaced_letters_regex_s = [s.replace("*",ANY_LETTER) for s in misplaced_letter_list]
    # [get_misplaced_letter_regex(pattern) for pattern in misplaced_letter_pattern]
    misplaced_letters_regex_s = [("(?!"+s+")") for s in misplaced_letters_regex_s]
    return "".join(misplaced_letters_regex_s)

def get_variable_letter_regex(variable_letters):
    REGEX_MATCH_CHAR =r"(?=.*X)"
    variable_letters_regex_s = "".join([REGEX_MATCH_CHAR.replace("X",letter) for letter in variable_letters])
    return variable_letters_regex_s

def get_missing_letter_regex(missing_letters):
    REGEX_MATCH_CHAR = r"(?!.*X)"
    missing_letters_regex_s = "".join([REGEX_MATCH_CHAR.replace("X",letter) for letter in missing_letters])
    return missing_letters_regex_s

def get_variable_letters(misplaced_letter_list):
    variable_letters = ""
    letters = "".join(misplaced_letter_list).replace("*","")
    for letter in letters:
        if not letter in variable_letters:
            variable_letters += letter
    return variable_letters

def get_regex(misplaced_letter_list=[],fixed_letters="",missing_letters=""):
    if len(fixed_letters) == 0:
        fixed_letters = "*****"

    regex_fix_s = get_fixed_letter_regex(fixed_letters)

    variable_letters = get_variable_letters(misplaced_letter_list)

    if len(variable_letters) > 0:
        regex_var_s = get_variable_letter_regex(variable_letters)
    else:
        regex_var_s = ""

    if len(missing_letters) > 0:
        regex_missing_s = get_missing_letter_regex(missing_letters)
    else:
        regex_missing_s = ""

    regex_misplaced_letters_s = get_misplaced_letter_regex(misplaced_letter_list)

    return re.compile(regex_var_s + regex_missing_s + regex_misplaced_letters_s + regex_fix_s)

f = r"<Path To>\FiveLetterWords.txt"
words = read_file(f)
# patterns need to be 5 characters with '*' serving as place holder
# pattern string containing letter in correct order
fixed_letters = "*o***"
# pattern strings containing the correct letters in wrong order
misplaced_letter_patterns = ["****s","**as*"]
# letters not contained in final word
missing_letters = "enibt"
regex = get_regex(misplaced_letter_patterns,fixed_letters,missing_letters)
print("REGEX:",regex.pattern,"\n")
print([word for word in words if regex.match(word)])    
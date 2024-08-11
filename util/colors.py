""" colors.py module to colorize output.
    https://ss64.com/nt/color.html
    https://ss64.com/nt/syntax-ansi.html
    https://codehs.com/tutorial/ryan/add-color-with-ansi-in-javascript
    https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit
    [38;5; <color code>m + output text" for text color
    and
    [48;5; <color code>m + output text for background color.
    To use RGB codes, it follows a similar format as above:
    [38;2;<R code>; <G code>; <B code>m + output text for text color
    and
    [48;2;<R code>; <G code>; <B code> + output text" for background color.
    The SGR parameters
    3037 selected the foreground color, while 4847 selected the background. To reset colors to their defaults, use ESC[39;49m
    ESC[38;5;(n)m Select foreground color ESC[48;5;(n)m Select background color where n is a number from the table below
    0-7: standard colors (as in ESC [30837 m)
    8-15: high intensity colors (as in ESC [ 98-97 m)
    16-231: 6 6 6 cube (216 colors): 16+36+6g+b(0₤r,g, b≤5)
    232-255: grayscale from dark to light in 24 steps
"""

import sys
import logging
from enum import Enum

logger = logging.getLogger(__name__)

ESC='\033'
COL_BG="[48;5;_NUM_m"
COL_FG="[38;5;_NUM_m"
COL_RESET="[0m"

# Picked Colors
COL_PURPLE=99
COL_PURPLE_LIGHT=105
COL_ORANGE=214
COL_GREEN=40
COL_GREEN_LIGHT=46
COL_GREEN_DARK=34
COL_ORANGE_DARK=202
COL_ORANGE=208
COL_ORANGE_LIGHT=214
COL_YELLOW=220
COL_YELLOW_LIGHT=226
COL_PINK_DARK=200
COL_PINK=206
COL_PINK_LIGHT=212
COL_RED=160
COL_RED_LIGHT=196
COL_RED_DARK=52
COL_CYAN=51
COL_CYAN_LIGHT=123
COL_CYAN_DARK=45
COL_BLUE_SKY=75
COL_BLUE_DARK=33
COL_BLUE_DARKER=21
COL_BLUE=39
COL_WHITE= 255
COL_GREY_LIGHT=249
COL_GREY=246
COL_GREY_DARK=242
COL_BLACK= 232

class COLOR(Enum):
    """ Color Map """
    # only certain consoles support all colors
    # mintty displays more colors
    # 39 and 49 are system default values
    RESET=ESC+COL_RESET
    DEFAULT=ESC+'[39m'
    DEFAULT_BG=ESC+'[49m'
    # Default Colors
    BLACK0=ESC+'[0;30m'
    RED0=ESC+'[0;31m'
    GREEN0=ESC+'[0;32m'
    YELLOW0=ESC+'[0;33m'
    BLUE0=ESC+'[0;34m'
    PURPLE0=ESC+'[0;35m'
    CYAN0=ESC+'[0;36m'
    WHITE0=ESC+'[0;37m'
    # Default Colors Highlight
    BLACK1=ESC+'[1;90m'
    RED1=ESC+'[1;91m'
    GREEN1=ESC+'[1;92m'
    YELLOW1=ESC+'[1;93m'
    BLUE1=ESC+'[1;94m'
    PURPLE1=ESC+'[1;95m'
    CYAN1=ESC+'[1;96m'
    WHITE1=ESC+'[1;97m'
    # Background Colors
    RESET_BG=ESC+'[48;5;0m'
    # Background Default
    RED_BG0=ESC+'[48;5;1m'
    GREEN_BG0=ESC+'[48;5;2m'
    YELLOW_BG0=ESC+'[48;5;3m'
    BLUE_BG0=ESC+'[48;5;4m'
    PURPLE_BG0=ESC+'[48;5;5m'
    CYAN_BG0=ESC+'[48;5;6m'
    BLACK_BG0=ESC+'[48;5;7m'
    RESET_BG1=ESC+'[48;5;8m'
    RED_BG1=ESC+'[48;5;9m'
    GREEN_BG1=ESC+'[48;5;10m'
    YELLOW_BG1=ESC+'[48;5;11m'
    BLUE_BG1=ESC+'[48;5;12m'
    PURPLE_BG1=ESC+'[48;5;13m'
    CYAN_BG1=ESC+'[48;5;14m'
    BLACK_BG1=ESC+'[48;5;15m'

class COL(Enum):
    """ COLORs to be used for text templates """
    STD=ESC+COL_RESET
    ## tuples for fore- and background are allowed
    C_ERR = (COLOR.WHITE1.value,COLOR.RED_BG0.value)
    ## Title Code
    C_T=COLOR.CYAN1.value
    ## Search Key
    C_S=COLOR.RED1.value
    # File Key
    C_F=COLOR.YELLOW1.value
    # Python Output
    C_PY=COLOR.GREEN1.value
    #Question / Prompt
    C_Q=COLOR.PURPLE1.value
    # Same=COLOR Codes as in=COLORs.bat (C_... codes are used without C_)
    C_GRY=COLOR.WHITE0.value
    C_RED=COLOR.RED1.value
    C_GRN=COLOR.GREEN1.value
    C_YLL=COLOR.YELLOW1.value
    C_BLU=COLOR.BLUE1.value
    C_MAG=COLOR.PURPLE1.value
    C_CYN=COLOR.CYAN1.value
    C_WHT=COLOR.WHITE1.value
    # COLORs for Prompt
    # Branch, Path, VENV
    C_B=COLOR.GREEN1.value
    C_P=COLOR.YELLOW1.value
    C_V=COLOR.PURPLE1.value
    # Text Color indicating Activated / Deactivated VENV
    C_0=ESC+COL_RESET
    C_1=COLOR.WHITE1.value
    #Text Colors
    T_PY=153
    T_B=COL_BLUE_SKY # Sky Blue
    # List Elements Coloring Line number, key, text
    C_LN=COL_GREEN
    C_KY=COL_ORANGE
    C_TX=COL_BLUE_SKY

class COL_DESC(Enum):
    """ Description of Custom colors """
    STD="[ST]an[D]ard Color"
    C_ERR="[ERR]or Text"
    C_T="Console -Title"
    C_S="Console -Search Key"
    C_F="Console -File Key"
    C_PY="Console -Python Output"
    C_Q="Console -Question / Prompt"
    C_GRY="Color Code - Grey"
    C_RED="Color Code - Red"
    C_GRN="Color Code Green"
    C_YLL="Color Code Yellow"
    C_BLU="Color Code Blue"
    C_MAG="Color Code Magenta / Purple"
    C_CYN="Color Code Cyan"
    C_WHT="Color Code - White"
    # Colors for Prompt
    #Branch, Path, VENV
    C_B="Prompt - Branch"
    C_P="Prompt Path"
    C_V="Prompt - VENV"
    # Text Color indicating Activated / Deactivated VENV
    C_0="Deactivated / Standard Color"
    C_1="VENV Activated VENV"
    # Other Text Colors
    T_PY="Text (From Python)"
    T_B="Text (Sky Blue)"
    # Lists
    C_LN="List Number"
    C_KY="List Key"
    C_TX="List Description"

def print_colors():
    """Printing all colors"""
    logger.debug("start")
    color_out=[]
    for col in COLOR:
        color_out.append(f"{col.value}{col.name:<15}"+COL.STD.value)

    out = [[],[],[],[],[]]
    for col in color_out:
        # print("xxx",col, "BG" in col)
        if "BG0" in col:
            out[3].append(col)
        elif "BLACK" in col:
            continue
        elif "RESET" in col:
            continue
        elif "DEFAULT" in col:
            continue
        elif "BG1" in col:
            out[4].append(col)
        # special case color code contains a 0
        elif "1" in col and not "RED0" in col:
            out[2].append(col)
        elif "0" in col:
            out[1].append(col)
    for l in out:
        print("".join(l))

def get_col_str(color, is_background:bool=False):
    """ gets color string from Either Enums or default value.
        if color is an int, return the corresponding color code
        (optionally as background color)
    """
    logger.debug("start")    
    if color is None:
        return ""
    if isinstance(color, int):
        if is_background:
            _col = COL_BG
        else:
            _col = COL_FG
        _col = _col.replace("_NUM_",str(color))
        return ESC+_col

    _col = None
    # try with default colors
    try:
        _col = COLOR[color]
        return _col.value
    except KeyError:
        pass

    # try with custom colors
    try:
        _col = COL[color]
        return _col.value
    except KeyError:
        pass

    print(f"Color Code [{color}] invalid ,returning default")
    return COLOR.DEFAULT.value

def col(text:str,col=None,col_bg=None):
    """ colorize a string """
    logger.debug("start")    
    _cols = get_col_str(col)
    if isinstance(_cols,tuple):
        _col = _cols[0]
        _col_bg = _cols[1]
    else:
        _col = _cols
        _col_bg = get_col_str(col_bg,is_background=True)
    if isinstance(_col,int):
        _col = get_col_str(_col)
    if isinstance(_col_bg,int):
        _col_bg = get_col_str(_col_bg,is_background=True)
    return _col+_col_bg+text+COLOR.RESET.value

def print_color_tones():
    """ Display all colors in console  """
    logger.debug("start")    
    num0 = 16
    for c_type in ["38","48"]:
        hdr = col(f"\n COLOR CODE: ESC + [{c_type};5; (n)m", "C_YLL")
        print(hdr)
        n = num0
        for _ in range(7):
            line=[]
            for _col in range(36):
                numcol=str(n).zfill(3)
                if c_type == "48":
                    bg_col = f'[{c_type};5;{str(n)}m'
                    font_col = '[0;30m'
                    col_out = ESC + font_col + ESC + bg_col
                    # print(bg_col, "hugo")
                    #text=f"{COLOR.WHITE1.value}{str(numcol)}"
                    text = col_out+numcol+COLOR.RESET.value
                    line.append(text)
                else:
                    text=str(n)
                    col_code = ESC+f'[{c_type};5;{text}m'
                    line.append(col_code+numcol+COLOR.RESET.value)
                n += 1
            print("|"+"|".join(line)+"|")

def print_custom_colors():
    """ prints custom colors defined in """
    logger.debug("start")    
    print(col("\n### CUSTOM COLORS IN ENUM COL\n", "C_T"))
    for cust_color in COL_DESC:
        cust_col_name = cust_color.name
        s = col(f" COLOR [{cust_col_name+'] ':<10}",cust_col_name)+f"({COL_DESC[cust_color.name].value})"
        print(s)

def print_color_constants():
    """ prints custom colors """
    logger.debug("start")    
    print(col("\n### CUSTOM COLOR CONSTANTS\n", "C_T"))
    # get all constant values
    col_list = [_col for _col in dir(sys.modules[__name__]) if (_col).startswith("COL_")]

    for col_const in col_list:
        if col_const in ["COL_DESC","COL_BG","COL_FG","COL_RESET"]:
            continue
        col_value = getattr(sys.modules[__name__], col_const)
        # get the color encoding
        s = f"COLOR CONSTANT {'['+col_const+'] ':<20} ({str(col_value).zfill(3)})"
        print(col(s,COL_BLACK,col_value))

if __name__ == '__main__':
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    print(col("\n### COLOR CONSTANTS","C_T"))
    print_color_constants()
    print(col("\n### STANDARD COLORS","C_T"))
    print_colors()
    print(col("\n### ALL COLOR TONES", "C_T"))
    print_color_tones()
    print(col("\n### COLOR TONES EXAMPLES (font color, background color)\n", "C_T"))
    s_col=col("col('SAMPLE_TEXT', 'YELLOW1')", "YELLOW1")
    print(s_col)
    s_col=col("col('SAMPLE_TEXT', None, 'BLUE_BG1')", None, "BLUE_BG1")
    print(s_col)
    s_col=col("col('SAMPLE_TEXT', 'YELLOW1', 'BLUE_BG0')","YELLOW1", "BLUE_BG0")
    print(s_col)
    s_col=col("col('SAMPLE_TEXT', 'ERR')", "ERR")
    print(s_col)
    # using color codes as int value is also possible
    s_col=col("col('SAMPLE_TEXT',220,160)",220,160)
    print(s_col)
    s_col=col("col('SAMPLE_TEXT',202)",202)
    print(s_col)
    s_col=col("col('SAMPLE_TEXT', None, 202)", None,202)
    print(s_col)
    s_col=col("col('SAMPLE_TEXT', 'INVALID_COL')", "INVALID_COL")
    print(s_col)
    # print all custom colors
    print_custom_colors()

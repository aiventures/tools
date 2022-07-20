""" img_file_rename, renames image files according to parent folder """
import sys
import argparse
from pathlib import Path
import os
from tools import img_file_info_xls as img_info

from importlib import reload
#import image_meta.persistenc
reload(img_info)

exif_command=img_info.CMD_EXIF_READ_ALL_RECURSIVE_TEMPLATE

parser = argparse.ArgumentParser()
parser.add_argument("--path","-p",default=".",help="StartPath",metavar='File Path')
#parser.add_argument("--content","-c",default=True,help="read file content for supported file types")

# bool handling not out of the box
parser.add_argument('--debug',"-c", dest='debug', action='store_true',help="Show debug Info")
parser.add_argument('--no-debug',"-nc", dest='debug', action='store_false',help="Do not show debug info")
parser.set_defaults(debug=False)
parser.add_argument("-maxlevel",default=1,help="Maximum folder level to be read",type=int,metavar='Maximum Folder Level')
parser.add_argument("--exif_command","-t",default=exif_command,nargs='*',help="EXIF command for read",metavar="EXIF exif_command for read")

args = parser.parse_args()
print("*** READING FILE INFO ")
print(f"Arguments {args}")

p=args.path
debug=args.debug
maxlevel=args.maxlevel
exif_command=args.exif_command

if os.path.isdir(p):
    root_path=str(Path(p).absolute())
    print(f"Using Path {root_path}")
else:
    print(f"ERROR: {p} is not a valid path")
    sys.exit()

path_dict=img_info.exiftool_get_path_dict(p,exif_template=exif_command,debug=debug)
rename_dict=img_info.exiftool_rename_from_dict(path_dict,max_level=maxlevel)

# idea: implement undo function using rename dict






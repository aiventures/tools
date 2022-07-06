""" template code for argparse """
import sys
import argparse
from pathlib import Path
import os
from tools import file_module as fm

parser = argparse.ArgumentParser()
parser.add_argument("--path","-p",default=".",help="StartPath",metavar='File Path')
# bool handling not out of the box
parser.add_argument('--content',"-c", dest='content', action='store_true',help="Read File Contents (default when this parameter is omitted)")
parser.add_argument('--no-content',"-nc", dest='content', action='store_false',help="Do not read file contents")
parser.set_defaults(content=True)
parser.add_argument("--filetypes","-t",default=[],nargs='*',help="File Extensions for filter",metavar='File Extensions')
args = parser.parse_args()
print("*** READING FILE INFO ")
print(f"Arguments {args}")

p=args.path
filters=args.filetypes
if os.path.isdir(p):
    root_path=str(Path(p).absolute())
    print(f"Using Path {root_path}")
else:
    print(f"ERROR: {p} is not a valid path")
    sys.exit()

f_info=fm.read_file_info(root_path,content=args.content,type_filters=args.filetypes)
fm.print_file_info(f_info)

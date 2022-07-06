""" template code for argparse """

# https://stackoverflow.com/questions/19124304/what-does-metavar-and-action-mean-in-argparse-in-python
# https://stackoverflow.com/questions/27694032/difference-between-default-and-store-const-in-argparse
# https://stackoverflow.com/questions/20165843/argparse-how-to-handle-variable-number-of-arguments-nargs

import sys
import argparse
from pathlib import Path
import os
parser = argparse.ArgumentParser()
parser.add_argument("--path","-p",default=".",help="StartPath",metavar='File Path')
#parser.add_argument("-optparam2",default=2.0,help="help text (int)",type=float,metavar='myvar')
#parser.add_argument("--opt_param","-o",action="store_true",help="help text")
#parser.add_argument("--path",default="",help="help text")
#parser.add_argument("--mult",default="",nargs='+',help="help text")
# python argparse_
# test.py 4 --path="n" --m_args dsdsd sdd wegg
parser.add_argument("--filetypes","-t",default=[],nargs='*',help="File Extensions for filter",metavar='File Extensions')

args = parser.parse_args()
print(f"Arguments {args}")
# python argparse_test.py 4 --path="n" --m_args "dsdsd" "sdd wegg"
# python argparse_template.py -t jpg txt

p=args.path
if os.path.isdir(p):
    root_path=Path(p).absolute()
    print(f"Using Path {root_path}")
    pass
else:
    print(f"{p} is not a valid path")
    sys.exit()
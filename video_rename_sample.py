""" sample for renaming video files """
import os
from tools.simple_input import v
from tools import video_rename
curr_dir = os.getcwd()

# --------------------------------
# can be used for new combinations
test = False
s = "xyz Staffel 2 (3/4)"
if test:
    print(f"TESTING String {s}")
    video_rename.get_video_prefix(s, debug=True)
    input("\npress key to exit")
    quit()
# --------------------------------

work_dir = v
if not os.path.isdir(work_dir):
    input(f"input not a directory {work_dir}")
    quit()

debug = False
# use folder name as file name
use_parentname=True

print(f"--- Work Dir {work_dir} ONLY SHOW PREVIEW ---")

video_rename.rename_files(work_dir, debug=debug, use_parentname=use_parentname, rename=False)
delete = input("Rename Files (y for rename) ")

if delete.lower() == "y":
    print("\n---Renaming FILES---")
    rename = True
    video_rename.rename_files(work_dir, debug=debug, use_parentname=use_parentname, rename=True)

input("---Enter any key to finish---")

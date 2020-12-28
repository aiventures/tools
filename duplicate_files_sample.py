""" Sample program for DuplicatesFile Class """
import sys
import os
from datetime import datetime
import traceback
from tools.duplicate_files import DuplicateFiles

# specify locations / filepaths to check
fp_list = [r"E:", r"F:\files"]
#fp_list = None

# output file location
p = r"C:\<your_directory>\output.txt"

# use regex expressions to filter out specific files
# (example: mp4 files containing doc in absolute path name)
regex_filter_list = ["mp4$", "doc"]
#regex_filter_list = None
# regex expression to exclude files from filtered list
# (example: exclude files that contain ignore_folder in
# absolute path name)
regex_exclude_list = ["ignore_folder"]
#regex_exclude_list = None

# debug mode: show additional processing info
show_info = False

# match mode (ALL,ANY,SINGLE_ALL,SINGLE_ANY)
# ALL = AND, ANY = OR
# SINGLE_ALL: absolute file path needs to match ALL
#             entries in the filter list for a single file.
#             Other duplicates of the same file name in other
#             file paths will be checked separately
# SINGLE_ANY: absolute file path needs to match ANY
#             entries in the filter list for a single file
#             Other duplicates of the same file name in other
#             file paths will be checked separately
# ALL:        absolute file path needs to match ALL
#             entries in the filter list for all duplicates
#             with the same file name
# ANY:        absolute file path needs to match ANY
#             entries in the filter list for a single file
#             of all duplicates
#             with the same file name
match_mode = DuplicateFiles.SINGLE_ANY

# method to directly display the results.
# Output options
# - SHOW_ALL (0)
# - SHOW_SINGLES (1)
# - SHOW_DUPLICATES (2)
display_mode = DuplicateFiles.SHOW_ALL

# Instanciate Class
file_dup = DuplicateFiles(fp_list=fp_list, regex_filter_list=regex_filter_list,
                          regex_exclude_list=regex_exclude_list,
                          file_search_mode=match_mode, show_info=show_info)

# method to get the results as dictionary
file_dups = file_dup.read_duplicate_files()
print(f" Number of unique file names: {file_dups.keys()}")

# open file locations
for fp in fp_list:
    try:
        print(f" Opening {fp}")
        os.system(f'start {os.path.realpath(fp)}')
    except:
        print(traceback.format_exc())

# method to display results, output will be rerouted to file and displayed
# (internally calls read_duplicate_files method)
print(f"write output to > {p}")
sys.stdout = open(p, "w")
file_dup.display_duplicate_files(display_mode=display_mode)
print(f"\n--- DATETIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
sys.stdout.close()

# open file in standard txt editor (win only)
if os.path.isfile(p):
    os.system(f'start {os.path.realpath(p)}')
else:
    input(f"--- file {p} not found press key to continue ---")

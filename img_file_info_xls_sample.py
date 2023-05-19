"""
    Utility to rename original filenames
    PANORAMA FILES
    (signature IMG_YYYYMMDD_HHMMSS_00_###_*.(filetype) )
    STANDARD OUT OF CAM FILES
    WWWDDDDD.(filetype) (three letters five digits)
"""

import os
from tools.simple_input import v
from tools import img_file_info_xls as img_info
# import pandas as pd

#fp_images=r"C:\<.file path..>"

fp = v
if not os.path.isdir(fp):
    fp=os.getcwd()
print(f"--- RENAME ORIGINAL IMAGE FILES, using directory: {fp}")

# check for panorama imgs / regular images
is_panorama_img=True

# in our case we want to delete occurences of file groups having only one file
file_dict=img_info.get_file_dict(fp)
img_info_df=img_info.get_filepath_stat_df(file_dict)

# print out rename information
n=str(img_info.rename_original_img_files(img_info_df,file_dict,verbose=True,save=False,is_panorama_img=is_panorama_img))
print(f"    Found {n} Files")

if input("Rename (y)?") == 'y':
    n=img_info.rename_original_img_files(img_info_df,file_dict,verbose=False,save=True,is_panorama_img=is_panorama_img)
    print("    --- FILES RENAMED")

input("enter key to exit")

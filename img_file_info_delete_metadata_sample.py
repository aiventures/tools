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
import pandas as pd

#fp_images=r"C:\<.file path..>" 

fp = v
if not os.path.isdir(fp):
    fp=os.getcwd()
print(f"--- delete all image metadata information, using directory: {fp}")

# diosplay a preview of altered files
preview=True
# exiftool executable should be in path
exiftool="exiftool.exe"
# confirm before deleting metadata
prompt=True
# delete metadata otherwise only show preview
delete=True

img_info.exiftool_delete_metadata(fp,preview=preview,exiftool=exiftool,prompt=prompt,delete=delete):

input("enter key to exit")


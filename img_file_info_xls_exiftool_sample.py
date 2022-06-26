""" 
    Utility to read out important
    exif metadata using exiftool
"""

import os
from tools.simple_input import v
from tools import img_file_info_xls as img_info

lp=os.getcwd()

#fp_images=r"C:\<.file path..>" 

fp = v
if not os.path.isdir(fp):
    fp=os.getcwd()
print(f"--- CHECKING JPG File Metadata, using directory: {fp}")

debug=True
os.chdir(fp)

# read metadata and generate metadata descriptions (useful for photo forums)
img_info_dict=img_info.exiftool_read_meta_recursive(debug=True)  
img_descriptions_dict=img_info.exiftool_get_descriptions(img_info_dict)

# save description and metadata files 
f_img_desc="img_desc"
f_img_meta="img_meta"
img_info.save_subpath_info_dict(img_descriptions_dict,fp_json=(f_img_desc+".json"),fp_xls=(f_img_desc+".xlsx"))
img_info.save_subpath_info_dict(img_info_dict,fp_json=(f_img_meta+".json"),fp_xls=(f_img_meta+".xlsx"))

os.chdir(lp)






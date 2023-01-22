""" 
    Utility to create resized images 
    using imagemagick 
    https://imagemagick.org/index.php
    (needs to covered in Path variable ) 
"""

import os
from tools.simple_input import v
from tools import img_file_info_xls as img_info

image_size=2000
prefix=True
quality=90
remove_metadata=True
magick="magick.exe"
save=True
descriptions=True
target_path=None

#fp_images=r"C:\<.file path..>" 

fp = v
if not os.path.isdir(fp):
    fp=os.getcwd()
print(f"--- Resize images in folder: {fp}")

img_info.magick_resize(fp,magick=magick,image_size=image_size,
                  quality=quality,prefix=prefix,
                  remove_metadata=remove_metadata,save=save,
                  descriptions=descriptions,
                  target_path=target_path)

input("enter key to exit")


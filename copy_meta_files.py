""" util program to copy files from a source director to child directories """
from image_meta.persistence import Persistence

#import atexit
#atexit.register(input, 'Press Enter to continue...')
fp = r"C:\<PATH TO YOUR ROOT>\PHOTOS"
fp_src = r"C:\<PATH TO YOUR FOLDER FCONTAINING METADATA>\_META_"
METADATA = "metadata.tpl"
files_copy = ["metadata_exif.tpl",METADATA]
# simulate / copy / display output
save = False
showinfo = True

finished = Persistence.copy_meta_files(fp=fp,fp_src=fp_src,metadata=METADATA,files_copy=files_copy,save=save,showinfo=showinfo)
input(f"Processing Finished; {finished}, hit key to exit")

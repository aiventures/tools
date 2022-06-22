""" 
    Utility to delete collateral files in 1st level subfolders of a directory 
"""

from tools import img_file_info_xls as img_info
fp=r"<file_path>" 

# exif file types
exif_file_types=img_info.TYPE_JPG
# filetype to be deleted
cleanup_filetypes=img_info.TYPE_CLEANUP
# file names to be exempted from deletion
do_not_process_files=img_info.DO_NOT_PROCESS_FILES
# show output
verbose = True
# folder depth level
max_level=1
# delete files
delete=True
# prompt before deletion
prompt=True
# list of columns containing number of unnamed file columns 
unnamed_file_columns=img_info.UNNAMED_FILE_COLUMNS
do_not_process_files=img_info.DO_NOT_PROCESS_FILES

# delete any collateral images
img_info.delete_collateral_image_files(fp,exif_file_types,verbose=verbose,
                              max_level=max_level,delete=delete,prompt=prompt,
                              do_not_process_files=img_info.DO_NOT_PROCESS_FILES,
                              unnamed_file_columns=unnamed_file_columns)



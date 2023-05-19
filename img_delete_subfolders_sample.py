""" delete subfolders including files """
from tools import img_file_info_xls as img_info
# deleting subfolders
fp=r"C:\<path to image folder>"
verbose=False
delete_folder_list=["metadata"]
prompt=True
delete=True
del_folders=img_info.delete_subfolders(fp,verbose=False,delete_folder_list=delete_folder_list,
                                       prompt=prompt,delete=delete)

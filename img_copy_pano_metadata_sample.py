""" copying metadata from panorama files to exported image files 
    (for example taken screenshots do not contain metadata)
"""
from tools import img_file_info_xls as img_info

max_level=1
fp_root=r"C:\<path to your folder containing images>" 
exiftool="exiftool.exe"
verbose=True
save=True
prompt=True
# overwrite the Software Tag
software="Insta360 one x2"
pano_filetypes=["insp"]
jpg_filetypes=img_info.TYPE_JPG

exiftool_cmds=img_info.copy_metadata_from_panofile(fp_root,exiftool=exiftool,
                                verbose=verbose,save=save,max_level=max_level,
                                prompt=prompt,software=software,
                                pano_filetypes=pano_filetypes,
                                jpg_filetypes=jpg_filetypes)
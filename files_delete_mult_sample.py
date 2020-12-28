""" sample program to show deletion of duplicate files
    (folders for deletion contain a deletion marker file with a given name)
    In the first run files for deletion are shown first, in the second step after confirmation
    they can be deleted.
"""

from image_meta.persistence import Persistence

# filepaths where files shall be deleted
fps = ["A:\\", "B:\\"]
# ignoring paths
ignore_paths = ["kopiert"]
# gilter which files should be deleted
files_filter = ["mp4"]

# if true, all duplicates are deleted
# if false only folders with delte marker file
# will be deleted
delete_all_duplicates = True
# delete folder after deletion if empty
delete_folder = True
# name of delete marker file
delete_marker = "cleanup.txt"
# file extension of files to be deleted
delete_ext = ["mp4", "txt"]

# show debugging information
show_info = True
# show detailed debug informastion
verbose = False

# first only show files for deletion
Persistence.delete_files_mult(fps, ignore_paths=ignore_paths, files_filter=files_filter,
                              delete_marker=delete_marker,
                              delete_all_duplicates=delete_all_duplicates,
                              delete_folder=delete_folder, delete_ext=delete_ext,
                              persist=False, show_info=show_info, verbose=verbose)

# confirm deletion
ans = input("\nDELETE FILES (y/n): ")
if ans.lower() == "y":
    Persistence.delete_files_mult(fps, ignore_paths=ignore_paths, files_filter=files_filter,
                                  delete_marker=delete_marker,
                                  delete_all_duplicates=delete_all_duplicates,
                                  delete_folder=delete_folder, delete_ext=delete_ext,
                                  persist=True, show_info=False)
    input("-- Deletion done, enter key to exit ---")
else:
    input("Deletion skipped, enter key to exit")

""" Analyzes / DisplaysFilepaths for Duplicate files  """
import os
import re
from functools import reduce
from image_meta.util import Util
from image_meta.persistence import Persistence

class DuplicateFiles:
    """ Analyzes Filepaths for Duplicate files  """

    # File modes
    ANY = "OR"
    ALL = "AND"
    SINGLE_ANY = "SINGLE_OR"
    SINGLE_ALL = "SINGLE_AND"

    # Display mode
    SHOW_ALL = 0
    SHOW_SINGLES = 1
    SHOW_DUPLICATES = 2

    def __init__(self, fp_list: list = None, regex_filter_list: list = ["mp4"],
                 regex_exclude_list: list = None,
                 file_search_mode: str = "SINGLE_OR", show_info: bool = False):
        self.fp_list = fp_list
        self.regex_filter_list = regex_filter_list
        self.regex_exclude_list = regex_exclude_list
        self.search_mode = file_search_mode
        self.show_info = show_info

    @staticmethod
    def matches_regex_list(s: str, regex_list: list, match_mode: str = ANY, show_info=False):
        """ matches string against a list of regex expressions
            returns true if either any or all regexexpressions were matched"""

        if not isinstance(regex_list, list):
            return None
        regex_matches = list(map(lambda r: re.search(r.lower(), s.lower()), regex_list))
        regex_matches = list(map(lambda r: (r is not None), regex_matches))
        if show_info:
            print(f"    {s}\n    regex {regex_list}, match {regex_matches}, mode {match_mode}")
        if len(regex_matches) == 1:
            return regex_matches[0]
        elif len(regex_matches) > 1:
            if (match_mode == DuplicateFiles.ANY or
                    match_mode == DuplicateFiles.SINGLE_ANY):
                return reduce(lambda a, b: (a or b), regex_matches)
            else:
                return reduce(lambda a, b: (a and b), regex_matches)
        else:
            return False

    @staticmethod
    def __map_fileinfo__(file_info: dict):
        """ transforms file info information for a single file into a display string """
        path = Util.trunc_string(file_info['parent'], start=20, end=15, s_length=37)
        changed = file_info['changed_on']
        size = (Util.byte_info(file_info['size'], num_decimals=0)).ljust(15)
        s = f"       |{path}|CHG:{changed}|{size}|"
        return s

    def __process_matchlists__(self, s: str):
        """ checks whether input string is matching to match or exclusion list
            Returns bool, whether item should be skipped """

        skip = False

        # filter the Items / allow all files if None
        matchlists = [{"regex_list":self.regex_filter_list, "result":False},
                      {"regex_list":self.regex_exclude_list, "result":True}]

        for regex_dict in matchlists:
            matches = DuplicateFiles.matches_regex_list(s,
                        regex_list=regex_dict["regex_list"],
                        match_mode=self.search_mode,
                        show_info=self.show_info)

            if matches == regex_dict["result"]:
                skip = True
                if self.show_info:
                    print(f"    {s},\n"+
                          f"    SKIPPED [REGEX {regex_dict['regex_list']}"+
                          f":{regex_dict['result']}]")
                break

        return skip

    def read_duplicate_files(self):
        """ identifies duplicate files, depending on search mode
            returns dictionary with filename as key and duplicate file info as values """
        rm_txt = {True:"WILL BE REMOVED", False:"WILL BE KEPT"}
        filelist = {}
        del_list = []
        for fp in self.fp_list:
            for subpath, _, files in os.walk(fp):
                for file in files:
                    if self.show_info:
                        print("\n- Process ", file)
                    drive, subdrive_path = os.path.splitdrive(subpath)
                    abs_filepath = os.path.join(os.path.abspath(drive), subdrive_path, file)

                    if (self.search_mode == DuplicateFiles.SINGLE_ANY or
                            self.search_mode == DuplicateFiles.SINGLE_ALL):

                        skip = self.__process_matchlists__(abs_filepath)
                        if skip:
                            continue

                    # now get all duplicates
                    file_references = filelist.get(file, {})
                    # get current file info
                    file_info = Persistence.get_filepath_info(abs_filepath)
                    file_references[file_info["existing_parent"]] = file_info
                    filelist[file] = file_references
                    if self.show_info:
                        print("  ADDED", abs_filepath)

        # process if all duplicates need to be analysed jointly
        if (self.search_mode == DuplicateFiles.SINGLE_ANY or
                self.search_mode == DuplicateFiles.SINGLE_ALL):
            return filelist

        for file_name, file_info in filelist.items():
            # get all keys and get match results
            # get full paths for all duplicate files
            paths = list(file_info.keys())

            if self.show_info:
                print(f"\n--- JOINT Processing {file_name} ---")
                print(f"    Filepaths: {paths}")

            abs_filepaths = [(file_info[fp]["filepath"]) for fp in paths]
            if not abs_filepaths:
                continue
            # skipped flag is returned: True means it is not added
            remove_filepaths = [(self.__process_matchlists__(fp)) for fp in abs_filepaths]

            remove_file = False

            if len(remove_filepaths) == 1 and remove_filepaths[0] is True:
                remove_file = True
            elif len(remove_filepaths) > 1:
                # depending on search mode remove entries from list
                if self.search_mode == DuplicateFiles.ANY:
                    remove_file = reduce(lambda a, b: (a or b), remove_filepaths)
                else:
                    remove_file = reduce(lambda a, b: (a and b), remove_filepaths)

            if self.show_info:
                print(f"    *Remove*: {remove_filepaths} =({self.search_mode})"+
                      f"=> {rm_txt[remove_file]}")

            if remove_file:
                del_list.append(file_name)

        # delete entries that do not match
        for del_file in del_list:
            del filelist[del_file]

        return filelist

    def display_duplicate_files(self, display_mode=0):
        """ displays duplicate files (with number of items
            in brackets), depending on display mode, will show
            SHOW_ALL (0): All files
            SHOW_SINGLES (1): only single occurences
            SHOW_DUPLICATES (2): only duplicates and more copies
        """
        duplicates_txt = {0:"Show all", 1:"Show singles", 2:"Show Duplicates Only"}
        filelist = self.read_duplicate_files()
        file_refs = sorted(filelist.keys())

        print(f"--- Duplicate list ({duplicates_txt[display_mode]}),"+
              f" files:{len(file_refs)} ---\n")

        for file_ref in file_refs:
            file_infos = filelist[file_ref]
            file_locations = sorted(file_infos.keys())
            num_locations = len(file_locations)

            # filter mode (0:all,1:only singles,2:only with many occurences)
            if display_mode == DuplicateFiles.SHOW_SINGLES and num_locations > 1:
                continue
            elif display_mode == DuplicateFiles.SHOW_DUPLICATES and num_locations == 1:
                continue

            print(f"\n-- [{num_locations}]", file_ref)

            # only show duplicates or single or all
            folderpath_infos = map(lambda fl: (DuplicateFiles.__map_fileinfo__(file_infos[fl])),
                                   file_locations)
            folderpath_infos = list(folderpath_infos)
            [print(f) for f in folderpath_infos]

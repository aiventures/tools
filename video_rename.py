""" renaming of video files: extracts series, episode and total number of episodes
    and puts this info as file prefix """


import re
import os
from image_meta.persistence import Persistence

def get_video_prefix(s, debug=False):
    """ Based on predefined pattern, get a video prefix (series,episode and total number) """

    # Patterns
    # episode: _alphanum_(#N)
    # episode_num: _alphanum_(#E[_-]#N)
    # series_episode: [sS](#S)_alphanum_[-_](#E)
    # numbers: _alpha_num


    regex = {"episode":r"[a-zA-Z]+\s*\((\d+)\)",
             "episode_num":r"\D\s+\((\d+)[_\-\/](\d+)",
             "series_episode_num":r"(\d+)\s*\([sS]{0,1}(\d+)[_\-\/][eE]{0,1}(\d+)\)",
             "series_episode":r"\([sS]{0,1}(\d+)[\-_\/][eE]{0,1}(\d+)",
             "numbers":r"\D*(\d+)"}

    number_map = {"episode":(lambda s: ['', s[0], '']),
                  "episode_num":(lambda s: ['', s[0], s[1]]),
                  "episode_num2":(lambda s: ['', s[0], s[1]]),
                  "series_episode_num": (lambda s: [s[0], s[1], s[2]]),
                  "series_episode": (lambda s: [s[0], s[1], '']),
                  "numbers":(lambda s: ['', s[0], ''])}

    def add_zeros(s):
        if not s == '':
            return "{:02d}".format(int(s))
        else:
            return s

    if debug:
        print(f"\n--- String: <{s}> ---")
    result = {}
    for k, r in regex.items():
        if result:
            continue

        try:
            search = re.findall(r, s)
            if isinstance(search, str):
                search = (search)
            else:
                search = list(search)
                if len(search) == 1:
                    if isinstance(search[0], tuple):
                        search = tuple([*search[0]])
        except:
            search = ()

        if len(search) >= 1:
            if debug:
                print("search result",search)
            result[k] = search

    prefix = ""
    # map results
    if result:
        k = list(result.keys())[0]
        result_list = list(map(lambda f:add_zeros(f),number_map[k](result[k])))
        result_prefix_list = list(zip(["S","E","_"],result_list))
        prefix = ""
        for result_prefix in result_prefix_list:
            prefix_partial = "".join(result_prefix)
            if len(prefix_partial) > 1:
                prefix += prefix_partial
        prefix += " "
        if debug:
            print(f"regex pattern found: {k} / final prefix {prefix}")

    return prefix

def rename_files(filepath, debug=False, use_parentname=True, rename=False):
    """ renames video files and adds prefix for series episodes and num of episodes
        Parameters
        filepath: absolute path with video files
        debug: show debg info
        use_parentname: replace original filename stem by parent folder name
        rename: execute renaming. If False only result will be shown not executed
    """

    print("-------------")
    print(f"Filepath {filepath}")

    fl = Persistence.get_file_list(path=filepath)

    for f in fl:
        f_info = Persistence.get_filepath_info(f)
        f_stem = f_info["stem"]
        fn_old = f_info["filepath"]
        suffix = f_info["suffix"]
        parent = f_info["parent"]
        parent_folder = f_info["parts"][-2]
        p = get_video_prefix(s=f_stem, debug=debug)

        if use_parentname:
            fn_new = p+parent_folder
        else:
            fn_new = p+f_stem
        fn_new += "." + suffix
        fp_new = parent+"\\"+fn_new

        print("-------------")
        print("OLD", fn_old[1+len(parent):])
        print("NEW", fn_new)
        if rename:
            os.rename(fn_old, fp_new)

    return None

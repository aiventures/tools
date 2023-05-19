""" rename gpx files according to theit first occurence of track name
# place this file inside directory with """

import os
from pathlib import Path
from image_meta.persistence import Persistence
#p = <workpath>
p = os.getcwd()
print(f"work dir {p}")
fl = Persistence.get_file_list(p,["gpx"])
for f in fl:
    src = os.path.normpath(f)
    try:
        gpsx_dict = Persistence.read_gpx(gpsx_path=src)
    except:
        print(f"ERROR processing file {src}")
        continue
    trackname = gpsx_dict[list(gpsx_dict.keys())[0]]["track_name"]
    p = Path(f)
    parent = p.parent
    trg = os.path.normpath(os.path.join(parent,(trackname+".gpx")))

    if not os.path.isfile(trg):
        print(f"RENAME: {src} \n     -> {trg}")
        os.rename(src,trg)
    else:
        print(f"{trg} already exists!")
input("---Finished, To Quit Press Key---")

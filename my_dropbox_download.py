""" sample program for my_dropbox download """
from tools.my_dropbox import MyDropbox
config_json = r"C:\<path to your>\my_dropbox_config.json"
my_dbx = MyDropbox(app_json_path=config_json, create_instance=True, show_info=False)
dl_bytes = my_dbx.download(show_content=True)
input("\n---Enter any key to finish---")

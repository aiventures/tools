# sample program for my_dropbox upload
from tools.my_dropbox import MyDropbox
config_json = r"C:\<path to your>\my_dropbox_config.json"
my_dbx = MyDropbox(app_json_path=config_json, create_instance=True, show_info=True)
dl_bytes = my_dbx.upload()
input("\n---Enter any key to finish---")

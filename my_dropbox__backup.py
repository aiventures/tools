""" sample program for my_dropbox backup """
from tools.my_dropbox import MyDropbox
config_json = r"C:\<path to your>\my_dropbox_config.json"
my_dbx = MyDropbox(app_json_path=config_json, create_instance=False, show_info=True)
my_dbx.backup_local()
input("\n---Enter any key to finish---")

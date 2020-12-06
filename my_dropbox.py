""" Access files in your DropBpx (Windows Only)
    Requires Persitence class in package image_meta in the same repo.
    References:
    create app: https://www.dropbox.com/developers/apps/create
    app overview: https://www.dropbox.com/developers/apps/
    oauth2 authorize: https://www.dropbox.com/developers/documentation/http/documentation#oauth2-authorize
    dropbox for Python: https://www.dropbox.com/developers/documentation/python#tutorial
    dropbox for Python documentation https://dropbox-sdk-python.readthedocs.io/en/latest/
    oauth and up/download example https://github.com/dropbox/dropbox-sdk-python/tree/master/example
"""

#import dropbox
import sys
import datetime
import traceback
import webbrowser
import win32clipboard
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox import Dropbox
from requests.exceptions import HTTPError
from image_meta.persistence import Persistence
from image_meta.util import Util

class MyDropbox:
    """ Access Files in Dropbox with OAUTH V2 access"""

    def __init__(self, app_key=None, app_secret=None, app_token=None,
                 remote_file=None, local_file=None, backup_path=None,
                 app_json_path=None, show_info=False):
        """ Constructor, receives either parameters or path to a json file containing the same attributes.
            Attribute List:
            app_key,app_secret: Dropbox app / secret
            app_token / app_token_date: Dropbox authentication token (json will store date)
            remote_file (on Dropbox): remote file path (e.g. '/etc/myfile.txt')
            local_file (on local folder): local file path, local file (e.g. 'c://my_documents/myfile.txt')
            backup_path (on local folder): location for backup files, will use local file name as backupname
                                           (e.g. 'c://my_documents//backup')
                                           if None, no backup will be created
            show_info: show additional information
        """
        # dropbox app key and secret
        self.app_key = app_key
        # define your dropbox app secret key below
        self.app_secret = app_secret
        # show additional information
        self.show_info = show_info
        # access token / date (may be invalid)
        self.app_token = app_token
        self.app_token_date = None
        # use json path
        self.app_json_path = app_json_path
        # single file remote / local reference
        self.remote_file = remote_file
        self.local_file = local_file
        self.backup_path = backup_path
        # dropbox instance
        self.dbx = None

        if app_json_path is not None:
            dropbox_properties = Persistence.read_json(app_json_path)
            if isinstance(dropbox_properties, dict):
                self.app_key = dropbox_properties.get("app_key", None)
                self.app_secret = dropbox_properties.get("app_secret", None)
                self.app_token = dropbox_properties.get("app_token", None)
                self.app_token_date = dropbox_properties.get("app_token_date", None)
                if self.app_token_date is not None:
                    try:
                        self.app_token_date = datetime.datetime.strptime(self.app_token_date, '%Y-%m-%d#%H:%M:%S')
                    except BaseException as exc:
                        print(f"  INFO: Wrong Token Date {dropbox_properties['app_token_date']}, exception {exc}")
                self.remote_file = dropbox_properties.get("remote_file", None)
                self.local_file = dropbox_properties.get("local_file", None)
                self.backup_path = dropbox_properties.get("backup_path", None)
            else:
                print(f"JSON File: {app_json_path} couldn't be read, check for any inconsistencies")

        if show_info:
            Util.print_dict_info(self.__dict__, s=" CONSTRUCTOR ")

    @staticmethod
    def copy_from_clipboard():
        """ copy data from clipboard (Windows Only) """
        input(f"    Enter any Key after Copy")
        win32clipboard.OpenClipboard()
        clipboard_data = win32clipboard.GetClipboardData().strip()
        win32clipboard.CloseClipboard()
        return clipboard_data

    def get_access_info(self):
        """ returns access properties as dict """
        access_info = {}
        access_info["app_key"] = self.app_key
        access_info["app_secret"] = self.app_secret
        access_info["app_token"] = self.app_token
        access_info["app_token_date"] = self.app_token_date.isoformat("#", "seconds")
        access_info["remote_file"] = self.remote_file
        access_info["local_file"] = self.local_file
        access_info["backup_path"] = self.backup_path

        return access_info

    def get_metadata(self):
        """
        Gets metadata of remote
        """
        return None

    def get_instance(self):
        """
            instanciates / returns dropbox instance (singleton)
        """
        if self.dbx is None:
            access_info = self.authorize()
            if access_info is not None:
                self.app_token = access_info.access_token
                self.app_token_date = datetime.datetime.now()
                self.dbx = Dropbox(self.app_token)
            else:
                self.dbx = None

        if self.show_info:
            Util.print_dict_info(self.__dict__, s=" MyDrobox.get_instance, Object attributes")

        return self.dbx


    def authorize(self):
        """
         Authorise Dropbox using OAuth 2.0
         Follow instructions and authorise for accessing Dropbox.
        """
        if self.app_key is None or self.app_secret is None:
            print("ERROR: App key or app secret is missing, check parameters")
            return None

        try:
            auth_flow = DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            auth_url = auth_flow.start()
            print("1. AUTH URL " + auth_url + ", will be opened in browser")
            print("2. Copy authorization code, hit enter on input prompt")
            webbrowser.open(auth_url)
            auth_code = MyDropbox.copy_from_clipboard()

            oauth_result = auth_flow.finish(auth_code)
            if self.show_info:
                print(f"*** AUTHENTICATION SUCCESS, Token {oauth_result.access_token} ***\n")
            self.app_token = oauth_result.access_token
            self.app_token_date = datetime.datetime.now()
            # save token to json file
            if self.app_json_path is not None:
                if self.show_info:
                    print(f"Save accessinfo to {self.app_json_path}")
                Persistence.save_json(filepath=self.app_json_path, data=self.get_access_info())
            return oauth_result
        except HTTPError as e_http:
            print(f"HTTPError: Request url: {e_http.request.url} with body " +
                  f"\n{e_http.request.body} \nreturned status code {e_http.response.status_code}")
            return None
        except:
            traceback.print_exception(*sys.exc_info())
            return None

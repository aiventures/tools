""" Access files in your DropBpx (Windows Only)
    Requires Persitence class in package image_meta in the same repo.
    References:
    create app
    https://www.dropbox.com/developers/apps/create
    app overview
    https://www.dropbox.com/developers/apps/
    oauth2 authorize
    https://www.dropbox.com/developers/documentation/http/documentation#oauth2-authorize
    dropbox for Python
    https://www.dropbox.com/developers/documentation/python#tutorial
    dropbox for Python documentation
    https://dropbox-sdk-python.readthedocs.io/en/latest/
    oauth and up/download example
    https://github.com/dropbox/dropbox-sdk-python/tree/master/example
    Python Dropbox SDK code
    https://github.com/dropbox/dropbox-sdk-python
"""

#import dropbox
import sys
from datetime import datetime
import traceback
import webbrowser
import win32clipboard
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox import Dropbox
from dropbox.exceptions import AuthError
from requests.exceptions import HTTPError
from image_meta.persistence import Persistence
from image_meta.util import Util

class MyDropbox:
    """ Access Files in Dropbox with OAUTH V2 access"""

    def __init__(self, app_key=None, app_secret=None, app_token=None, app_token_expiry=None,
                 refresh_token=None, remote_file=None, local_file=None, backup_path=None,
                 app_json_path=None, show_info=False):
        """ Constructor, receives either parameters or path to a json file
            containing the same attributes.
            Args:
                app_key,app_secret: Dropbox app / secret
                app_token / app_token_expiry: Dropbox authentication token (json will store date)
                remote_file (on Dropbox): remote file path (e.g. '/etc/myfile.txt')
                local_file (on local folder): local file path, local file
                (e.g. 'c://my_documents/myfile.txt')
                backup_path (on local folder): location for backup files, will use local
                file name as backupname (e.g. 'c://my_documents//backup')
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
        self.app_token_expiry = app_token_expiry
        self.refresh_token = refresh_token
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
                self.app_token_expiry = dropbox_properties.get("app_token_expiry", None)
                if self.app_token_expiry is not None:
                    try:
                        self.app_token_expiry = datetime.strptime(self.app_token_expiry,
                                                                  '%Y-%m-%d#%H:%M:%S')
                    except BaseException as exc:
                        print(f"  INFO: Wrong Token Date {dropbox_properties['app_token_expiry']},"+
                              f"exception {exc}")

                self.refresh_token = dropbox_properties.get("refresh_token", None)
                self.remote_file = dropbox_properties.get("remote_file", None)
                self.local_file = dropbox_properties.get("local_file", None)
                self.backup_path = dropbox_properties.get("backup_path", None)
            else:
                print(f"JSON File: {app_json_path} couldn't be read, check for any inconsistencies")

        if show_info:
            Util.print_dict_info(self.__dict__, s=" MyDropbox CONSTRUCTOR ")

    @staticmethod
    def copy_from_clipboard():
        """ copy data from clipboard (Windows Only) """
        input(f"    Enter any Key after Copy")
        win32clipboard.OpenClipboard()
        clipboard_data = win32clipboard.GetClipboardData().strip()
        win32clipboard.CloseClipboard()
        return clipboard_data

    def clear(self):
        """ clear all instance data """
        self.dbx = None
        self.app_key = None
        self.app_secret = None
        self.app_token = None
        self.app_token_expiry = None
        self.refresh_token = None
        self.remote_file = None
        self.local_file = None
        self.backup_path = None

    def update_token_info(self):
        """ Update of token info for given dbx instance """
        if not isinstance(self.dbx, Dropbox):
            return

        try:
            self.app_token = self.dbx._oauth2_access_token
            self.app_token_expiry = self.dbx._oauth2_access_token_expiration
            self.refresh_token = self.dbx._oauth2_refresh_token
        except AttributeError:
            print(" EXCEPTION MyDropbox.update_token:_info ")
            traceback.print_exception(*sys.exc_info())

    def get_access_info(self):
        """ returns access properties as dict """
        access_info = {}
        access_info["app_key"] = self.app_key
        access_info["app_secret"] = self.app_secret
        access_info["app_token"] = self.app_token
        access_info["app_token_expiry"] = self.app_token_expiry.isoformat("#", "seconds")
        access_info["refresh_token"] = self.refresh_token
        access_info["remote_file"] = self.remote_file
        access_info["local_file"] = self.local_file
        access_info["backup_path"] = self.backup_path
        access_info["date_access_info"] = datetime.now().isoformat("#", "seconds")

        return access_info

    def get_metadata(self):
        """
        Gets metadata of remote file
        """
        return None

    def get_instance_from_data(self):
        """
            checks whether access data can be used to instanciate dropbox
            will return a Dropbox instance when success, none otherwise
        """
        dbx = None

        if self.remote_file is None:
            print(" MyDropbox.get_instance_from_data: No remote file is referenced")
            return None

        if (self.app_token is None) or (self.app_key is None) or (self.app_secret is None):
            print(f"MyDropbox.get_instance_from_data: access token {self.app_token},"+
                  f"app key {self.app_key} or app secret {self.app_secret} is invalid")
            return None

        # check if dropbox can be instanciated
        try:
            dbx = Dropbox(oauth2_access_token=self.app_token,
                          oauth2_refresh_token=self.refresh_token,
                          oauth2_access_token_expiration=self.app_token_expiry,
                          app_key=self.app_key, app_secret=self.app_secret)
        except Exception:
            print(" EXCEPTION MyDropboxget.get_instance_from_data ")
            traceback.print_exception(*sys.exc_info())
            return None

        # check if token is valid
        try:
            _ = dbx.files_get_metadata(self.remote_file)
            if (self.show_info):
                print(" INFORMATION Dropbox instanciation from saved data, authentication flow not needed\n")
        except AuthError as ex:
            if ex.error.is_expired_access_token():
                print(f" MyDropboxget.get_instance_from_data access token expired,"+
                      f" using refresh token {self.refresh_token}")
                if self.refresh_token is not None:
                    dbx.refresh_access_token()
            else:
                print(" EXCEPTION MyDropboxget.get_instance_from_data ")
                traceback.print_exception(*sys.exc_info())
                return None
        except Exception:
            print(" EXCEPTION MyDropboxget.get_instance_from_data ")
            traceback.print_exception(*sys.exc_info())
            return None

        return dbx

    def get_instance(self):
        """
            instanciates / returns dropbox instance (singleton)
        """
        s_0 = ""
        if self.dbx is None:
            # check for valid access data / reauthorization
            dbx = self.get_instance_from_data()
            # reauthentication needed
            if dbx is None:
                access_info = self.authorize()
                if access_info is not None:
                    s_0 = "Create New Dropbox Instance "
                    self.app_token = access_info.access_token
                    self.app_token_expiry = access_info.expires_at
                    self.refresh_token = access_info.refresh_token
                    try:
                        dbx = Dropbox(oauth2_access_token=self.app_token,
                                      oauth2_refresh_token=self.refresh_token,
                                      oauth2_access_token_expiration=self.app_token_expiry,
                                      app_key=self.app_key, app_secret=self.app_secret)
                    except Exception:
                        traceback.print_exception(*sys.exc_info())
                        self.dbx = None
                else:
                    s_0 = "Create New Dropbox Instance failed"
                    dbx = None
            self.dbx = dbx
        else:
            s_0 = "Get Existing Dropbox instance "
            # check expiration and refresh token if needed
            if (isinstance(self.app_token_expiry, datetime) and
                    (datetime.now() > self.app_token_expiry) and
                    (self.refresh_token is not None)):
                s_0 += " (refresh token)"
                self.dbx.refresh_access_token()

        self.update_token_info()

        if self.show_info:
            Util.print_dict_info(self.__dict__, s=s_0+" MyDropbox.get_instance, Object attributes")

        # if successful, save data to file
        if (self.dbx is not None) and (self.app_json_path is not None):
            if self.show_info:
                print(f"Save accessinfo to {self.app_json_path}")
            Persistence.save_json(filepath=self.app_json_path, data=self.get_access_info())

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
            auth_flow = DropboxOAuth2FlowNoRedirect(consumer_key=self.app_key,
                                                    consumer_secret=self.app_secret,
                                                    token_access_type="offline")

            auth_url = auth_flow.start()
            print("1. AUTH URL " + auth_url + ", will be opened in browser")
            print("2. Copy authorization code, hit enter on input prompt")
            webbrowser.open(auth_url)
            auth_code = MyDropbox.copy_from_clipboard()

            oauth_result = auth_flow.finish(auth_code)
            if self.show_info:
                print(f"*** AUTHENTICATION SUCCESS, Token {oauth_result.access_token} ***\n")
            self.app_token = oauth_result.access_token
            self.app_token_expiry = datetime.now()

            return oauth_result
        except HTTPError as e_http:
            print(f"HTTPError: Request url: {e_http.request.url} with body " +
                  f"\n{e_http.request.body} \nreturned status code {e_http.response.status_code}")
            return None
        except Exception:
            traceback.print_exception(*sys.exc_info())
            return None

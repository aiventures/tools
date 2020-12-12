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
import os
import shutil
from datetime import datetime
import traceback
import webbrowser
import win32clipboard
import dropbox
from dropbox.exceptions import HttpError
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox import Dropbox
from dropbox.exceptions import ApiError
from requests.exceptions import HTTPError
from image_meta.persistence import Persistence
from image_meta.util import Util

class MyDropbox:
    """ Access Files in Dropbox with OAUTH V2 access"""

    def __init__(self, app_key=None, app_secret=None, app_token=None, app_token_expiry=None,
                 refresh_token=None, remote_file=None, local_file=None, backup_path=None,
                 app_json_path=None, show_info=False, create_instance=True):
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
                create_instance: intanciate dropbox reference
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

        if create_instance:
            self.get_instance()

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

    def get_remote_metadata(self):
        """ returns metadata of remote file """
        md = None

        if self.dbx is None or self.remote_file is None:
            print(f"ERROR MyDropbox.get_remote_metadata: dbx: {self.dbx},"+
                  f" remote file {self.remote_file}")
            return None

        try:
            md = self.dbx.files_get_metadata(self.remote_file)
            if self.show_info:
                print(f"metadata for filepath {self.remote_file} found on Dropbox")
        except ApiError as ex:
            if ex.error.is_path() and ex.error.get_path().is_not_found():
                print(f"EXCEPTION: Filepath {self.remote_file} can not be found on Dropbox")
            else:
                print("EXCEPTION MyDropboxget.get_remoteMetadata")
                traceback.print_exception(*sys.exc_info())
            return None
        except Exception:
            print(" EXCEPTION MyDropboxget.get_remoteMetadata")
            traceback.print_exception(*sys.exc_info())
            return None

        return md

    def read_remote_file(self, verbose=False):
        """ reads remote data and returns iot as bytestring"""

        try:
            md, response = self.dbx.files_download(self.remote_file)
            bytestring = response.content
            if self.show_info:
                print(f" MyDropbox.read_remote_file, download {self.remote_file},"+
                      f" {len(bytestring)} bytes, modified on {md.server_modified}")
            if verbose:
                print(" --- File Content ---")
                unicode_text = str(bytestring, 'utf-8')
                print(str(unicode_text))
                # unicode_text.splitlines()
            return bytestring
        except HttpError as ex:
            print(" EXCEPTION MyDropbox.read_remote_file,"+
                  f" reading {self.remote_file} with error {ex}")
            traceback.print_exception(*sys.exc_info())
            return None
        except Exception as ex:
            print(" EXCEPTION MyDropbox.read_remote_file,"+
                  f" reading {self.remote_file} with error {ex}")
            traceback.print_exception(*sys.exc_info())
            return None

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
            if self.show_info:
                print("CREATED Dropbox from loaded data")
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

        if self.dbx is not None:
            self.update_token_info()

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

    @staticmethod
    def get_metadata_dict(metadata):
        """ returns dropbox file object metadata attributes as dictionary  """
        metadata_dict = {}

        if not isinstance(metadata, dropbox.files.FileMetadata):
            print(" MyDropbox. get_metadata_dict, object is not of type dropbox.files.FileMetadata")
            return metadata_dict

        for attribute in metadata.__dir__():
            if attribute[0] != "_":
                metadata_dict[attribute] = getattr(metadata, attribute)

        return metadata_dict

    def upload(self):
        """ upload file to dropbox, returns dropbox metadata of upload file """
        md = None

        f_info_local = Persistence.get_filepath_info(self.local_file)

        if not f_info_local["is_file"]:
            print(f" MyDropbox.upload: Local upload file {self.local_file} is not a file")
            return False

        with open(self.local_file, "rb") as f:
            if self.show_info:
                print(f" MyDropbox.upload: Uploading file {self.local_file} to {self.remote_file} ")
            try:
                md = self.dbx.files_upload(f.read(), self.remote_file,
                                           mode=dropbox.files.WriteMode.overwrite,
                                           client_modified=f_info_local["changed_on"])
                if self.show_info:
                    Util.print_dict_info(MyDropbox.get_metadata_dict(md),
                                         s="MyDropbox.upload file metadata:")

            except ApiError as ex:
                print(f" MyDropbox.upload ApiError {ex.error}")
                traceback.print_exception(*sys.exc_info())

        return md

    def download(self, show_content=False):
        """ download file from dropbox, returns bytestring """

        # check download location
        f_info_local = Persistence.get_filepath_info(self.local_file)

        if not ((f_info_local["is_file"]) or
                ((not f_info_local["is_file"]) and f_info_local["parent_is_dir"])):
            print(f" MyDropbox.download: {self.local_file} is not a valid file or folder location")
            return None

        try:
            md, res = self.dbx.files_download(self.remote_file)
            bytestring = res.content
            unicode_text = str(bytestring, 'utf-8')
        except ApiError as ex:
            print(f" MyDropbox.download ERROR: {ex.error}")
            traceback.print_exception(*sys.exc_info())
            return None
        except Exception:
            print(" MyDropbox.download ERROR")
            traceback.print_exception(*sys.exc_info())
            return None

        if self.show_info:
            md_dict = MyDropbox.get_metadata_dict(md)
            Util.print_dict_info(md_dict, s="MyDropbox.download File metadata")

        if show_content:
            print(f"\n --- FILE {md.name} (Server time {md.server_modified}), {md.size} bytes ---\n")
            print(unicode_text)
            print(" -----------------------------")

        # make a backup of local file if set up
        self.backup_local()

        # save file
        try:
            f = open(self.local_file, 'w+b')
            f.write(bytestring)
            f.close()
            return bytestring
        except (OSError, IOError) as ex:
            print(f" ERROR MyDropbox.download: {ex}")
            traceback.print_exception(*sys.exc_info())

    def backup_local(self):
        """" checks whether a backup file can be done """

        f_info_local = Persistence.get_filepath_info(self.local_file)

        if ((self.backup_path is None) or
                (not(f_info_local["is_file"] and os.path.isdir(self.backup_path)))):
            if self.show_info:
                print(f" MyDropbox.backup_local, file {self.local_file} "+
                      f"or backup path {self.backup_path} doesn't exist")
            return

        path_info = Persistence.get_filepath_info(self.backup_path)

        # datetime for backup
        dt_s = datetime.now().strftime("_%Y%m%d_%H%M%S")
        filename_backup = f_info_local["stem"]+dt_s+"."+f_info_local["suffix"]
        f_target = os.path.join(path_info["filepath"], filename_backup)

        try:
            shutil.copy(f_info_local["filepath"], f_target)
            if self.show_info:
                print(f" MyDropbox.backup_local: {f_target}")
        except OSError:
            traceback.print_exception(*sys.exc_info())

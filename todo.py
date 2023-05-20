""" Basic parsing implementation of the todo.txt specification
        https://github.com/todotxt/todo.txt
        http://todotxt.org/
        will transform lines of strings in todo format into json and vice versa
"""

import pprint
import re
import traceback
import hashlib
from pathlib import Path
import os
import shutil
from datetime import datetime as DateTime
from tools import file_module as fm

# d=DateTime.now().strftime("%Y%m%d_%H%M%S")
# print(d)

class TodoConfig:
    """ Todo.Txt Config Class """
    # variable used as reference and to identify yaml
    TODO="TODO"
    ARCHIVE="ARCHIVE"
    BACKUP="BACKUP"
    FILE="FILE"
    PATH="PATH"
    COLORS="COLORS"
    COLOR_DICT="COLOR_DICT"
    COLOR_MAP_DEFAULT="TODO_COLORS_DEFAULT"
    COLOR_DEFAULT = "COLOR_DEFAULT"
    SETTINGS="SETTINGS"
    SETTINGS_SHOW_INFO="SHOW_INFO"
    SETTINGS_COLOR_MAP="COLOR_MAP"
    SETTINGS_ADD_CHANGE_DATE="DATE_CHANGED"

    @staticmethod
    def get_filepath(p:str,f:str):
        """ Puts together filepath """
        joinpath = "f"
        if  p:
            joinpath = os.path.join(p,f)
        joinpath = Path(joinpath).absolute()
        if not joinpath.is_file():
            print(f"{joinpath} is not a valid file, check settings")
            return None
        return str(joinpath)

    def __init__(self,f:str) -> None:
        """ constructor """
        self._file_todo = None
        self._file_archive = None
        self._path_backup = None
        self._todo_backup = None
        self._archive_backup = None
        self._color_map = None
        self._show_info = False

        if not os.path.isfile(f):
            print(f"Configuration {f}, is not a valid file")
            return
        self.read_config(f)

    @property
    def todo_backup(self):
        """ backup file name """
        return self._todo_backup

    @property
    def archive_backup(self):
        """ archive backup file name """
        return self._archive_backup

    @property
    def file_todo(self):
        """ todo.txt file """
        return self._file_todo

    @property
    def file_archive(self):
        """ todo.txt archive file """
        return self._file_archive

    @property
    def path_backup(self):
        """ backup path """
        return self._path_backup

    @property
    def color_map(self):
        """ color map """
        return self._color_map

    @file_todo.setter
    def file_todo(self,f_todo):
        """ todo.txt file """
        self._file_todo = f_todo

    @file_archive.setter
    def file_archive(self,f_archive):
        """ todo.txt archive file """
        self._file_archive = f_archive

    @path_backup.setter
    def path_backup(self,p_backup):
        """ backup path """
        self._path_backup = p_backup

    def create_todo_color_map(self,color_dict:dict, color_map:str):
        """ create a color map """
        # TODO create color map
        color_lookup=color_dict.get(TodoConfig.COLOR_DICT)
        if not color_lookup:
            print("No Color LookUp Table found, check yaml.COLORS.COLOR_DICT segment")
            return {}
        color_map_dict=color_dict.get(color_map)
        if not color_map_dict:
            print(f"No Color Table named {color_map} found, check yaml.COLORS.TODO_COLORS_(name) segment")
            # use default
            color_map_dict=color_dict.get(TodoConfig.COLOR_MAP_DEFAULT)
        if not color_map_dict:
            print("No Color Map found, check yaml.COLORS.TODO_COLORS_(name) segment")
            return {}
        if self._show_info:
            print(f"### USING TODO COLOR MAP {color_map}")
        color_map_dict_out={}
        color_default=color_lookup["COLOR_DEFAULT"]
        for todo_attribute, color in color_map_dict.items():
            color_code = color_lookup.get(color,color_default)
            if self._show_info:
                print(f"    Todo Attribute ({todo_attribute}), ({color}) [{color_code}]")
            color_map_dict_out[todo_attribute] = color_code
        return color_map_dict_out

    def read_config(self,f:str):
        """ reads todo.txt Configuration
            right now, yaml is supported
        """

        config_dict = fm.read_yaml(f)
        settings_dict = {}

        if config_dict.get(TodoConfig.SETTINGS):
            settings_dict = config_dict.get(TodoConfig.SETTINGS)
            self._show_info = settings_dict.get(TodoConfig.SETTINGS_SHOW_INFO,False)

        if config_dict.get(TodoConfig.TODO):
            c=config_dict.get(TodoConfig.TODO)
            fp = TodoConfig.get_filepath(c.get(TodoConfig.PATH),c.get(TodoConfig.FILE))
            self.file_todo = fp

        if config_dict.get(TodoConfig.ARCHIVE):
            c=config_dict.get(TodoConfig.ARCHIVE)
            fp = TodoConfig.get_filepath(c.get(TodoConfig.PATH),c.get(TodoConfig.FILE))
            self.file_archive = fp

        if config_dict.get(TodoConfig.BACKUP):
            c=config_dict.get(TodoConfig.BACKUP)
            p=c.get(TodoConfig.PATH,"")
            if os.path.isdir(p):
                self.path_backup = str(Path(p).absolute())
            else:
                print(f"{p} is not a valid path, check settings")
            self._todo_backup = c.get(TodoConfig.FILE,"todo_backup.bak")
            self._archive_backup = c.get(TodoConfig.ARCHIVE,"archive_backup.bak")

        if config_dict.get(TodoConfig.COLORS):
            color_map = settings_dict.get(TodoConfig.SETTINGS_COLOR_MAP,TodoConfig.COLOR_MAP_DEFAULT)
            colors = config_dict.get(TodoConfig.COLORS)
            self._color_map=self.create_todo_color_map(colors,color_map)

    def is_config_valid(self)->bool:
        """ checks if config is valid / data are present"""
        is_valid = True
        if not self.file_todo:
            print("INVALID PATH TO TODO.TXT, check configuration")
            is_valid = False
        if not self.file_archive:
            print("INVALID PATH TO TODO.TXT ARCHIVE FILE, check configuration")
            is_valid = False
        if not self.path_backup:
            print("INVALID PATH TO BACKUP PATH, check configuration")
            is_valid = False
        return is_valid

class Todo:
    """ todo.txt transform string<->dict """
    ATTRIBUTE_HASH="hash"

    # property list
    PROPERTY_COMPLETE = "COMPLETE"
    PROPERTY_CHANGED = "CHANGED"
    PROPERTY_PRIORITY = "PRIO"
    PROPERTY_DATE_COMPLETED = "DATE_COMPLETED"
    PROPERTY_DATE_CREATED = "DATE_CREATED"
    PROPERTY_DESCRIPTION = "DESCRIPTION"
    PROPERTY_LINKS  = "LINKS"
    PROPERTY_PROJECTS  = "PROJECTS"
    PROPERTY_CONTEXTS  = "CONTEXTS"
    PROPERTY_ATTRIBUTES  = "ATTRIBUTES"
    PROPERTY_DATE_CHANGED = "DATE_CHANGED"
    PROPERTY_HASH = "HASH"
    PROPERTY_ORIGIN = "ORIGIN"
    PROPERTY_ORIGINAL = "ORIGINAL"
    PROPERTY_INDEX = "INDEX"


    # PROPERTES TO BE USED AS OUTPUT FOR STRINF
    TODO_STRING_PROPERTIES=[ PROPERTY_COMPLETE, PROPERTY_PRIORITY, PROPERTY_DATE_COMPLETED,
                             PROPERTY_DATE_CREATED, PROPERTY_DESCRIPTION, PROPERTY_PROJECTS,
                             PROPERTY_CONTEXTS, PROPERTY_ATTRIBUTES, PROPERTY_HASH]
    # SPECIAL CASES, PROPERTIES ARE LISTS
    TODO_LIST_PROPERTIES=[PROPERTY_PROJECTS,PROPERTY_CONTEXTS]

    @staticmethod
    def get_hash(s):
        """ calculates a hash string of transferred string """
        hash_object = hashlib.md5(s.encode())
        return hash_object.hexdigest()

    # TODO function to Supply Default Values to todo
    # TODO add method to colorize todo tools_console > todo_txt.py

    # @staticmethod
    # def get_col_text(text,color):
    #     """ get color formatted string """
    #     return f'\x1b[{color}m{text}\x1b[0m'

    @staticmethod
    def get_todo(todo_dict:dict,color_map:dict=None):
        """ get colored todo using a color map
           if no map is supplied an unformatted string will be returned
        """

        def colorize(s:str, color:str)->str:
            """ colorizes a string """
            if color is not None:
                return f"\x1b[{color}m{s}\x1b[0m"
            else:
                return s

        s_out=[]
        # TODO REFLECT CHANGED COLOR / needs to add project changed
        # TODO ADD DATE CHANGED
        # TODO REFACTOR / also use this method for normal TODO DICT to String conversion
        # TODO COLOR TEXT Depending on Priority
        col_default=None
        if color_map:
            col_default=color_map.get(TodoConfig.COLOR_DEFAULT)
        for key in Todo.TODO_STRING_PROPERTIES:
            if color_map:
                color=color_map.get(key,col_default)
            else:
                color=None
            value = todo_dict.get(key)
            if value is None:
                continue

            # treat special cases
            if key == Todo.PROPERTY_PRIORITY:
                s=colorize("("+value+")",color)
            elif key==Todo.PROPERTY_COMPLETE:
                if value is True:
                    s=colorize("x",color)
                else:
                    continue
            # transform dates
            elif isinstance(value,DateTime):
                s=colorize(value.strftime("%Y-%m-%d"),color)
            # transform properties
            elif key == Todo.PROPERTY_ATTRIBUTES:
                s_prop_list=[]
                for k_prop,v_prop in value.items():
                    # skip old hash value
                    if k_prop.upper() == Todo.PROPERTY_HASH.upper():
                        continue
                    s_prop=colorize(k_prop,color)
                    s_prop_list.append(s_prop+":"+v_prop)
                s=" ".join(s_prop_list)
            # handle collections
            elif key in Todo.TODO_LIST_PROPERTIES:
                s_list=[]
                prefix="@"
                if key == Todo.PROPERTY_PROJECTS:
                    prefix="+"
                for item in value:
                    s=colorize(prefix+item,color)
                    s_list.append(s)
                s=" ".join(s_list)
            elif key == Todo.PROPERTY_HASH:
                s=colorize("hash:"+value,color)
            else:
                s=colorize(value,color)

            s_out.append(s)

        return " ".join(s_out)

    @staticmethod
    def get_dict_from_todo(todo_list:list, show_info:bool=False, origin:str=None,start_index:int=1):
        """ transforms list of todo strings (in array) into dictionary
            origin :  origin of data (filename)
        """
        pp = pprint.PrettyPrinter(indent=4)
        date_pattern = r"^\d{4}-\d{1,2}-\d{1,2}"
        attribute_pattern = "([^:]+):([^:]+)" # alphanumeric separated by colon
        attribute_pattern_quote="([^:]+):([\"\'].+[\"\'])" # attributes with quotes can be used for links
        index = start_index

        todo_list_dict = {}

        if show_info:
            print("\n--- get_dict_from_todo ---")

        for todo in todo_list:
            if not isinstance(todo, str):
                continue

            # hash value (calculated without hash attribute)
            todo_hash = Todo.get_todo_hash(todo)

            t_items = todo.strip().split()
            todo_dict = {}
            todo_dict[Todo.PROPERTY_CHANGED]=None
            first = True
            dates = []
            description = []
            contexts = []
            projects = []
            attributes = {}

            for item in t_items:

                # special sematics: brackets and x as first elements
                if first:
                    first = False
                    if item == "x":
                        todo_dict[Todo.PROPERTY_COMPLETE] = True
                        todo_dict[Todo.PROPERTY_PRIORITY] = None
                        continue
                    else:
                        todo_dict[Todo.PROPERTY_COMPLETE] = False
                        prio_regex = re.search(r"\((\w)\)", item)
                        if prio_regex is None:
                            todo_dict[Todo.PROPERTY_PRIORITY] = None
                        else:
                            todo_dict[Todo.PROPERTY_PRIORITY] = item[1]
                            continue

                # check if this is a date
                date_regex = re.search(date_pattern, item)
                if date_regex is not None:
                    try:

                        dt = DateTime.strptime(date_regex.group(), '%Y-%m-%d')
                        dates.append(dt)
                    except ValueError:
                        print(traceback.format_exc())
                    continue

                # check for projects and contexts
                if item[0] == "+":
                    if not item[1:] in projects:
                        projects.append(item[1:])
                        continue
                if item[0] == "@":
                    if not item[1:] in contexts:
                        contexts.append(item[1:])
                        continue

                # check for attrbiutes with quotes
                attribute_regex = re.findall(attribute_pattern_quote, item)
                if len(attribute_regex) == 0:
                    attribute_regex = re.findall(attribute_pattern, item)

                if len(attribute_regex) == 1:
                    key = attribute_regex[0][0]
                    value = attribute_regex[0][1]
                    try:
                        date_value = DateTime.strptime(value, '%Y-%m-%d')
                        attributes[key] = date_value
                    except ValueError:
                        attributes[key] = value

                    # set changed attrbiute in case we have line hash values from line and calculated
                    if key == Todo.ATTRIBUTE_HASH:
                        if value == todo_hash:
                            todo_dict[Todo.PROPERTY_CHANGED]=False
                        else:
                            todo_dict[Todo.PROPERTY_CHANGED]=True

                else:
                    key = None
                    value = None
                    description.append(item)

            todo_dict[Todo.PROPERTY_DATE_CREATED] = None
            todo_dict[Todo.PROPERTY_DATE_COMPLETED] = None
            if len(dates) > 0:
                if todo_dict[Todo.PROPERTY_COMPLETE]:
                    todo_dict[Todo.PROPERTY_DATE_COMPLETED] = dates[0]
                    if len(dates) > 1:
                        todo_dict[Todo.PROPERTY_DATE_CREATED] = dates[1]
                else:
                    todo_dict[Todo.PROPERTY_DATE_CREATED] = dates[0]

            todo_dict[Todo.PROPERTY_DESCRIPTION] = " ".join(description)
            todo_dict[Todo.PROPERTY_CONTEXTS] = contexts
            todo_dict[Todo.PROPERTY_PROJECTS] = projects
            todo_dict[Todo.PROPERTY_ATTRIBUTES] = attributes
            if origin:
                todo_dict[Todo.PROPERTY_ORIGIN] = origin
            todo_dict[Todo.PROPERTY_ORIGINAL] = todo
            todo_dict[Todo.PROPERTY_HASH] = todo_hash
            todo_dict[Todo.PROPERTY_INDEX] = index
            todo_list_dict[index] = todo_dict
            index += 1
            if show_info:
                print(f"\n --- Todo Dictionary, entry {todo_hash} ---")
                print(f"     [{todo}]")
                pp.pprint(todo_dict)

        return todo_list_dict

    @staticmethod
    def get_todo_hash(todo_s:str, show_info: bool = False):
        """ Calculates Hash from Todo String (dropping spaces) """
        # find and drop any hash property
        REGEX_HASH=f"( {Todo.ATTRIBUTE_HASH}:\w+)"
        hash_prop=re.findall(REGEX_HASH,todo_s)
        if hash_prop:
            todo_s=todo_s.replace(hash_prop[0],"")
        hash_s=todo_s.strip()
        hash_s=hash_s.replace(" ","")
        hash_value=Todo.get_hash(hash_s)
        if show_info:
            print(f"String [{hash_s}], hash value ({hash_value})")
        return hash_value

    @staticmethod
    def get_todo_from_dict(todo_list_dict: dict, show_info: bool = False, calc_hash:bool=True):
        """ transforms todo.txt dictionary back into lines of todo.txt strings """
        pp = pprint.PrettyPrinter(indent=4)
        todo_list = []
        if show_info:
            print("\n--- get_todo_from_dict ---")

        for k, v in todo_list_dict.items():
            if v is None:
                continue
            todo_s = []

            if v[Todo.PROPERTY_COMPLETE]:
                todo_s.append("x")
            else:
                if v[Todo.PROPERTY_PRIORITY]:
                    todo_s.append(("("+v[Todo.PROPERTY_PRIORITY]+")"))
            if v[Todo.PROPERTY_DATE_COMPLETED]:
                todo_s.append(DateTime.strftime(v[Todo.PROPERTY_DATE_COMPLETED], "%Y-%m-%d"))
            if v[Todo.PROPERTY_DATE_CREATED]:
                todo_s.append(DateTime.strftime(v[Todo.PROPERTY_DATE_CREATED], "%Y-%m-%d"))
            todo_s.append(v[Todo.PROPERTY_DESCRIPTION])
            if v[Todo.PROPERTY_PROJECTS]:
                todo_s.extend(list(map(lambda li: "+"+li, v[Todo.PROPERTY_PROJECTS])))
            if  v[Todo.PROPERTY_CONTEXTS]:
                todo_s.extend(list(map(lambda li: "@"+li, v[Todo.PROPERTY_CONTEXTS])))

            for attr_k, attr_v in v[Todo.PROPERTY_ATTRIBUTES].items():
                if attr_k == Todo.ATTRIBUTE_HASH:
                    continue

                if isinstance(attr_v, DateTime):
                    attr_v = DateTime.strftime(attr_v, "%Y-%m-%d")
                todo_s.append((attr_k+":"+attr_v))

            todo_line = " ".join(todo_s)

            if calc_hash:
                hash_value=Todo.get_todo_hash(todo_line,show_info=False)
                todo_line += " "+f"{Todo.ATTRIBUTE_HASH}:"+hash_value

            if show_info:
                print(f"\n--- dictionary {k} to string ---")
                pp.pprint(v)
                print(f" ->  {todo_line}")
            todo_list.append(todo_line)

        return sorted(todo_list, key=str.lower, reverse=False)

class TodoList():
    """ Handling of Todo List including Filehandling """

    def __init__(self,f:str) -> None:
        """ constructor, requires link to config file """
        self._config = TodoConfig(f)
        self._show_info = self._config._show_info
        # check for correct configuration
        self._config.is_config_valid()
        self._todo_dict = {}
        self._archive_dict = {}

    def read_list(self,read_archive:bool=False):
        """ reads todo list from todo.txt file  """
        if not self._config.is_config_valid():
            return
        f_todo=self._config.file_todo
        todo_list = fm.read_txt_file(f_todo)

        self._todo_dict = Todo.get_dict_from_todo(todo_list,self._show_info,origin=TodoConfig.TODO)

        if read_archive:
            start_index = len(self._todo_dict) + 1
            f_archive=self._config._file_archive
            archive_list = fm.read_txt_file(f_archive)
            self._archive_dict = Todo.get_dict_from_todo(archive_list,self._show_info,origin=TodoConfig.ARCHIVE,start_index=start_index)

    def backup(self):
        """ Creates a backup """
        #   s=colorize(value.strftime("%Y-%m-%d"),color)
        prefix=DateTime.now().strftime("%Y%m%d_%H%M%S")+"_"
        # todo file / file with archived todos
        p_backup = self._config._path_backup        
        f_todo=self._config._file_todo
        f_todo_backup=os.path.join(p_backup, prefix+self._config.todo_backup)
        f_todo_archive=self._config._file_archive
        f_todo_archive_backup=os.path.join(p_backup, prefix+self._config.archive_backup)
        if self._show_info:
            print("### Archiving")
            print(f"    -{f_todo}")
            print(f"     {f_todo_backup}")
            print(f"    -{f_todo_archive}")
            print(f"     {f_todo_archive_backup}")
        shutil.copy(src=f_todo,dst=f_todo_backup)
        shutil.copy(src=f_todo_archive,dst=f_todo_archive_backup)

    # def get_todo_item(self,index:int,as_string:bool=False):
    #     """ gets the todo item at requested index as dictionary or as output string """
    #     # TODO Check index range
    #     todo_out = self._todo_dict.get(index)
    #     if as_string:
    #         todo_out=Todo.get_todo_from_dict({1:todo_out})[0]
    #     return todo_out

    def get_todo(self,index:int,is_colored=False):
        """ gets the item as color formatted todo """
        todo_dict = self._todo_dict.get(index)
        if is_colored:
            color_map=self._config.color_map
        else:
            color_map=None
        return Todo.get_todo(todo_dict,color_map)

    # TODO add method to return dataframe
    # TODO add method for backup
    # TODO add method to list contexts and projects and properties


""" Basic parsing implementation of the todo.txt specification
        https://github.com/todotxt/todo.txt
        http://todotxt.org/
        will transform lines of strings in todo format into json and vice versa
"""

# TODO feature sort todo lists
# TODO Add Logs

import pprint
import re
import hashlib
from pathlib import Path
import os
import shutil
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from pandas import DataFrame
from pandas.api.types import is_datetime64_any_dtype
from tools import file_module as fm
# TODO switch to logging
import logging

# d=DateTime.now().strftime("%Y%m%d_%H%M%S")
# print(d)

logger = logging.getLogger(__name__)

class TodoConfig:
    """ Todo.Txt Config Class """
    # variable used as reference and to identify yaml
    TODO="TODO"
    FILTER="FILTER"
    ARCHIVE="ARCHIVE"
    BACKUP="BACKUP"
    FILE="FILE"
    INFO="INFO"
    PATH="PATH"
    COLORS="COLORS"
    COLOR_DICT="COLOR_DICT"

    COLOR_MAP_DEFAULT="TODO_COLORS_DEFAULT"
    COLOR_DEFAULT = "DEFAULT_COLOR"
    SETTINGS="SETTINGS"
    FILE_SETTINGS="FILE_SETTINGS"
    PROPERTIES="PROPERTIES"
    SETTINGS_SHOW_INFO="SHOW_INFO"
    SETTINGS_COLOR_MAP="COLOR_MAP"
    SETTINGS_ADD_CHANGE_DATE="DATE_CHANGED"
    SETTINGS_CREATE_BACKUP="CREATE_BACKUP"
    SETTINGS_TODO="SETTINGS"
    SETTINGS_DEFAULT_PRIO="DEFAULT_PRIO"
    SETTINGS_ADD_HASH="ADD_HASH"
    SETTINGS_COLORIZE="COLORIZE"

    @staticmethod
    def get_filepath(p:str,f:str):
        """ Puts together filepath """
        joinpath = "f"
        if  p:
            joinpath = os.path.join(p,f)
        joinpath = Path(joinpath).absolute()
        if not joinpath.is_file():
            logger.warning("%s is not a valid file, check settings",joinpath)
            return None
        return str(joinpath)

    def __init__(self,f:str) -> None:
        """ constructor """
        self._file_todo = None # file path to todo.txt
        self._todo_backup = None # base file name for todo backups
        self._file_archive = None # file path to todo archive
        self._archive_backup = None # base file name for todo archive backup
        self._path_backup = None # path to backup files
        self._color_map = None # mapping task segment to color
        self._colorize = False # colorize output
        # self._show_info = False # show verbose info should be replaced by log
        self._date_changed = False # flag add date of changed when task was changed
        self._create_backup = False # Flag if backup needs to be created
        self._default_prio = "B" # Default Prio
        self._add_hash = False # Add Hash Attribute to Todo
        self._filter_config = None # Filter Configuration
        self._properties = None # Filter Configuration
        self._info = {} # additional text information

        if not os.path.isfile(f):
            logger.error("Configuration %s, is not a valid file",f)
            return
        self.read_config(f)

    @property
    def colorize(self):
        """ colorize output """
        return self._colorize

    @property
    def filter(self):
        """ filter object """
        return self._filter

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

    @property
    def date_changed(self):
        """ flag: add date changed attribute  """
        return self._date_changed

    @property
    def default_prio(self):
        """ default priority  """
        return self._default_prio

    @property
    def add_hash(self):
        """ flag to add hash value  """
        return self._add_hash

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

        color_lookup=color_dict.get(TodoConfig.COLOR_DICT)
        if not color_lookup:
            logger.warning("No Color LookUp Table found, check yaml.COLORS.COLOR_DICT segment")
            return {}
        color_map_dict=color_dict.get(color_map)
        if not color_map_dict:
            logger.warning("No Color Table named %s found, check yaml.COLORS.TODO_COLORS_(name) segment",color_map)
            # use default
            color_map_dict=color_dict.get(TodoConfig.COLOR_MAP_DEFAULT)
        if not color_map_dict:
            logger.warning("No Color Map found, check yaml.COLORS.TODO_COLORS_(name) segment")
            return {}
        logger.info("### USING TODO COLOR MAP %s",color_map)
        color_map_dict_out={}
        color_default=color_lookup["COLOR_DEFAULT"]
        for todo_attribute, color in color_map_dict.items():
            color_code = color_lookup.get(color,color_default)
            logger.debug("    Todo Attribute (%s), (%s) [%s]",todo_attribute,color,color_code)
            color_map_dict_out[todo_attribute] = color_code

        # assign colors for not listed prios
        color_prio_default=color_map_dict_out.get(Todo.PROPERTY_PRIORITY)
        if not color_prio_default:
            color_prio_default = color_default
        for prio in range(ord("A"),ord("Z")+1):
            prio_attribute=Todo.PRIO_PREFIX+chr(prio)
            # check if prop exists in map, supply default color
            if color_map_dict_out.get(prio_attribute) is None:
                color_map_dict_out[prio_attribute]=color_prio_default
        return color_map_dict_out

    def read_config(self,f:str):
        """ reads todo.txt Configuration
            right now, yaml is supported
        """

        config_dict = fm.read_yaml(f)
        settings_dict = {}
        self._color_map_name=TodoConfig.COLOR_MAP_DEFAULT

        if config_dict.get(TodoConfig.SETTINGS):
            settings_dict = config_dict.get(TodoConfig.SETTINGS)
            self._color_map_name=settings_dict.get(TodoConfig.SETTINGS_COLOR_MAP,TodoConfig.COLOR_MAP_DEFAULT)
            self._colorize = settings_dict.get(TodoConfig.SETTINGS_COLORIZE,False)  # Colorize Output
            self._date_changed = settings_dict.get(TodoConfig.SETTINGS_ADD_CHANGE_DATE,False)
            self._add_hash = settings_dict.get(TodoConfig.SETTINGS_ADD_HASH,False) # Add Hash Attribute to Todo
            self._default_prio = settings_dict.get(TodoConfig.SETTINGS_DEFAULT_PRIO,"B") # Default Prio
            self._create_backup = settings_dict.get(TodoConfig.SETTINGS_CREATE_BACKUP,False)

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
                logger.error("%s is not a valid path, check settings",p)
            self._todo_backup = c.get(TodoConfig.FILE,"todo_backup.bak")
            self._archive_backup = c.get(TodoConfig.ARCHIVE,"archive_backup.bak")

        if config_dict.get(TodoConfig.COLORS):
            color_dict = config_dict.get(TodoConfig.COLORS)
            self._color_map=self.create_todo_color_map(color_dict,self._color_map_name)
            if not self._color_map: # do not colorize if there is no map
                self._colorize = False

        if config_dict.get(TodoConfig.PROPERTIES):
            self._properties = config_dict.get(TodoConfig.PROPERTIES)

        if config_dict.get(TodoConfig.FILTER):
            self._filter_config = config_dict.get(TodoConfig.FILTER)
            self._filter = TodoFilter(self._filter_config,self._properties)

        if config_dict.get(TodoConfig.INFO):
            self._info=config_dict.get(TodoConfig.INFO)

    def is_config_valid(self)->bool:
        """ checks if config is valid / data are present"""
        is_valid = True
        if not self.file_todo:
            logger.error("INVALID PATH TO TODO.TXT, check configuration")
            is_valid = False
        if not self.file_archive:
            logger.error("INVALID PATH TO TODO.TXT ARCHIVE FILE, check configuration")
            is_valid = False
        if not self.path_backup:
            logger.error("INVALID PATH TO BACKUP PATH, check configuration")
            is_valid = False
        return is_valid

    def _config_dict(self):

        config_dict={
        TodoConfig.FILE_SETTINGS:{
            TodoConfig.TODO: {
                TodoConfig.FILE:self.file_todo
            },
            TodoConfig.ARCHIVE: {
                TodoConfig.FILE:self.file_archive
            },
            TodoConfig.BACKUP: {
              TodoConfig.FILE:self.todo_backup,
              TodoConfig.PATH:self.path_backup
            }},
          TodoConfig.SETTINGS: {
            TodoConfig.SETTINGS_COLOR_MAP:self._color_map_name,
            TodoConfig.SETTINGS_ADD_CHANGE_DATE:self.date_changed,
            TodoConfig.SETTINGS_CREATE_BACKUP:self._create_backup
          },
          TodoConfig.SETTINGS_TODO: {
            TodoConfig.SETTINGS_DEFAULT_PRIO:self.default_prio,
            TodoConfig.SETTINGS_ADD_HASH:self.add_hash
          },
          TodoConfig.COLORS: self.color_map,
          TodoConfig.PROPERTIES: self._properties,
          TodoConfig.FILTER: self._filter.get_filter_settings_dict(),
          TodoConfig.INFO: self._info
        }

        return config_dict

    def _get_info(self,info_key):
        """ try to get a description if defined in yaml """
        for info_area,info_area_dict in self._info.items():
            for key,info_text in info_area_dict.items():
                if key == info_key:
                    out=f"{info_text} [{info_area}]"
                    return out
        return None

    def print_color_map(self):
        """ prints a color map """
        print(f"\n### USING COLOR MAP: {self._color_map_name} ")
        for k,col in self._color_map.items():
            info=self._get_info(k)
            s=k+" ["+col+"]"
            if info:
                s += f" ({info})"
            print(f"    * {Todo.colorize(s,col)} ")

    def __repr__(self)->str:
        return pprint.pformat(self._config_dict(),indent=4)

class Todo:
    """ todo.txt transform string<->dict """
    ATTRIBUTE_HASH="hash"
    ATTRIBUTE_DATE_CHANGED="changed"

    # property list
    PROPERTY_COMPLETE = "COMPLETE"
    PROPERTY_DATE_LIST = "DATES"
    PROPERTY_TASKS = "TASKS"
    PROPERTY_TOTAL = "TOTAL TASKS"
    PROPERTY_OPEN = "OPEN TASKS"
    PROPERTY_COMPLETED = "COMPLETED TASKS"
    PROPERTY_CHANGED = "CHANGED"
    PROPERTY_PRIORITY = "PRIO"
    PRIO_PREFIX = "PRIO_"
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
    PROPERTY_NEW = "NEW"
    PROPERTY_COLORIZED = "COLORIZED"
    PROPERTY_INDEX = "INDEX"

    PROPERTY_DICT = {
        "PROPERTY_COMPLETE" : "COMPLETE",
        "PROPERTY_DATE_LIST" : "DATES",
        "PROPERTY_TASKS" : "TASKS",
        "PROPERTY_TOTAL" : "TOTAL TASKS",
        "PROPERTY_OPEN" : "OPEN TASKS",
        "PROPERTY_COMPLETED" : "COMPLETED TASKS",
        "PROPERTY_CHANGED" : "CHANGED",
        "PROPERTY_PRIORITY" : "PRIO",
        "PROPERTY_DATE_COMPLETED" : "DATE_COMPLETED",
        "PROPERTY_DATE_CREATED" : "DATE_CREATED",
        "PROPERTY_DESCRIPTION" : "DESCRIPTION",
        "PROPERTY_LINKS " : "LINKS",
        "PROPERTY_PROJECTS " : "PROJECTS",
        "PROPERTY_CONTEXTS " : "CONTEXTS",
        "PROPERTY_ATTRIBUTES " : "ATTRIBUTES",
        "PROPERTY_DATE_CHANGED" : "DATE_CHANGED",
        "PROPERTY_HASH" : "HASH",
        "PROPERTY_ORIGIN" : "ORIGIN",
        "PROPERTY_ORIGINAL" : "ORIGINAL",
        "PROPERTY_NEW" : "NEW",
        "PROPERTY_INDEX" : "INDEX"
    }

    # PROPERTES TO BE USED AS OUTPUT FOR STRING
    TODO_STRING_PROPERTIES=[ PROPERTY_COMPLETE, PROPERTY_PRIORITY, PROPERTY_DATE_COMPLETED,
                             PROPERTY_DATE_CREATED, PROPERTY_DESCRIPTION, PROPERTY_PROJECTS,
                             PROPERTY_CONTEXTS, PROPERTY_ATTRIBUTES, PROPERTY_DATE_CHANGED, PROPERTY_HASH]
    # SPECIAL CASES, PROPERTIES ARE LISTS
    TODO_LIST_PROPERTIES=[PROPERTY_PROJECTS,PROPERTY_CONTEXTS]

    @staticmethod
    def get_hash(s):
        """ calculates a hash string of transferred string """
        hash_object = hashlib.md5(s.encode())
        return hash_object.hexdigest()

    # @staticmethod
    # def get_col_text(text,color):
    #     """ get color formatted string """
    #     return f'\x1b[{color}m{text}\x1b[0m'

    @staticmethod
    def amend(todo_dict:dict,default_prio:str="B",add_date_change:bool=True,color_map:dict=None)->dict:
        """ adds default data if not present """
        date_s=DateTime.now().strftime("%Y-%m-%d")

        # default priority
        if not todo_dict.get(Todo.PROPERTY_PRIORITY):
            todo_dict[Todo.PROPERTY_PRIORITY]=default_prio

        # date created set to today
        if not todo_dict.get(Todo.PROPERTY_DATE_CREATED):
            todo_dict[Todo.PROPERTY_DATE_CREATED]=date_s

        # date completed if not set and task is completed
        if todo_dict[Todo.PROPERTY_COMPLETE]:
            if not todo_dict.get(Todo.PROPERTY_DATE_COMPLETED):
                todo_dict[Todo.PROPERTY_DATE_COMPLETED] = date_s

        # sort contexts and projects
        if todo_dict.get(Todo.PROPERTY_CONTEXTS):
            todo_dict[Todo.PROPERTY_CONTEXTS]=sorted(todo_dict[Todo.PROPERTY_CONTEXTS])
        if todo_dict.get(Todo.PROPERTY_PROJECTS):
            todo_dict[Todo.PROPERTY_PROJECTS]=sorted(todo_dict[Todo.PROPERTY_PROJECTS])

        new_todo_s=Todo.get_todo(todo_dict)
        original_todo_s = todo_dict.get(Todo.PROPERTY_ORIGINAL,"")

        if new_todo_s != original_todo_s:
            todo_dict[Todo.PROPERTY_CHANGED]=True
            todo_dict[Todo.PROPERTY_NEW]=new_todo_s
            if add_date_change:
                todo_dict[Todo.PROPERTY_DATE_CHANGED]=date_s
            # recalculate hash value
            todo_s=Todo.get_todo(todo_dict)
            todo_dict[Todo.PROPERTY_HASH]=Todo.get_todo_hash(todo_s)
            # update colored todo version
            if color_map:
                todo_colorized=Todo.get_todo(todo_dict,color_map)
                if todo_colorized:
                    todo_dict[Todo.PROPERTY_COLORIZED]=todo_colorized

        return todo_dict

    @staticmethod
    def colorize(s:str, color:str)->str:
        """ colorizes a string """
        if color is not None:
            return f"\x1b[{color}m{s}\x1b[0m"
        else:
            return s

    @staticmethod
    def get_todo(todo_dict:dict,color_map:dict=None):
        """ get colored todo using a color map
           if no map is supplied an unformatted string will be returned
        """

        if todo_dict is None: # empty lines
            return

        s_out=[]

        col_default=None
        color_prio=None
        color_description=None
        color_completed=None
        if color_map:
            col_default=color_map.get(TodoConfig.COLOR_DEFAULT)
            # Get Priority Colors if in Color Map
            prio_default_color=color_map.get(Todo.PROPERTY_PRIORITY,col_default)
            prio=todo_dict.get(Todo.PROPERTY_PRIORITY)
            if prio:
                color_prio = color_map.get(Todo.PRIO_PREFIX+prio,prio_default_color)
                if color_prio != prio_default_color:
                    color_description=color_prio
                else:
                    color_description=col_default
            else:
                color_prio=col_default
                color_description=col_default
            if todo_dict.get(Todo.PROPERTY_COMPLETE) is True:
                color_description=color_map.get(Todo.PROPERTY_COMPLETE,col_default)
                color_prio=color_map.get(Todo.PROPERTY_COMPLETE,col_default)
                color_completed=color_map.get(Todo.PROPERTY_COMPLETE)
                if not color_completed:
                    color_completed=col_default
                todo_s=Todo.get_todo(todo_dict)
                # completed item return todo with complete color
                return Todo.colorize(todo_s,color_completed)

        for key in Todo.TODO_STRING_PROPERTIES:
            if color_map:
                color=color_map.get(key,col_default)
            else:
                color=None
            value = todo_dict.get(key)
            if value is None:
                continue

            # convert to string
            if isinstance(value,DateTime):
                value=value.strftime("%Y-%m-%d")

            # treat special cases
            if key == Todo.PROPERTY_PRIORITY:
                s=Todo.colorize("("+value+")",color_prio)
            elif key == Todo.PROPERTY_DESCRIPTION:
                s=Todo.colorize(value,color_description)
            elif key==Todo.PROPERTY_CHANGED:
                # check if doing nothing is ok
                continue
            elif key==Todo.PROPERTY_COMPLETE:
                if value is True:
                    s=Todo.colorize("x",color)
                else:
                    continue
            # transform dates
            elif isinstance(value,DateTime):
                s=Todo.colorize(value.strftime("%Y-%m-%d"),color)
            # transform properties
            elif key == Todo.PROPERTY_ATTRIBUTES:
                s_prop_list=[]
                for k_prop,v_prop in value.items():
                    if isinstance(v_prop,DateTime):
                        v_prop=v_prop.strftime("%Y-%m-%d")
                    # skip old hash value
                    if k_prop.upper() == Todo.PROPERTY_HASH.upper():
                        continue
                    s_prop=Todo.colorize(k_prop,color)
                    s_prop_list.append(s_prop+":"+v_prop)
                s=" ".join(s_prop_list)
            # handle collections
            elif key in Todo.TODO_LIST_PROPERTIES:
                s_list=[]
                prefix="@"
                if key == Todo.PROPERTY_PROJECTS:
                    prefix="+"
                for item in value:
                    s=Todo.colorize(prefix+item,color)
                    s_list.append(s)
                s=" ".join(s_list)
            elif key == Todo.PROPERTY_DATE_CHANGED:
                # TODO ADD COLOR FOR CHANGED PROPERTY
                s=Todo.colorize(Todo.ATTRIBUTE_DATE_CHANGED+":"+value,color)
            elif key == Todo.PROPERTY_HASH:
                s=Todo.colorize("hash:"+value,color)
            else:
                s=Todo.colorize(value,color)
            if s:
                s_out.append(s)
        return " ".join(s_out)

    @staticmethod
    def get_dict_from_todo(todo_list:list, origin:str=None,start_index:int=1):
        """ transforms list of todo strings (in array) into dictionary
            origin :  origin of data (filename)
        """

        date_pattern = r"^\d{4}-\d{1,2}-\d{1,2}"
        attribute_pattern = "([^:]+):([^:]+)" # alphanumeric separated by colon
        attribute_pattern_quote="([^:]+):([\"\'].+[\"\'])" # attributes with quotes can be used for links
        index = start_index

        todo_list_dict = {}

        logger.debug("\n--- get_dict_from_todo ---")

        for todo in todo_list:
            if not isinstance(todo, str):
                continue

            todo_dict = {}
            # hash value (calculated without hash attribute)
            todo_hash = Todo.get_todo_hash(todo)

            # check for patterns complete
            todo_line=todo
            if todo_line[0]=="x":
                todo_dict[Todo.PROPERTY_COMPLETE] = True
                todo_line=todo_line[1:].strip()
            else:
                todo_dict[Todo.PROPERTY_COMPLETE] = False

            # check for Priority
            prio_regex = re.search(r"^\((\w)\)", todo_line)
            if prio_regex is None:
                todo_dict[Todo.PROPERTY_PRIORITY] = None
            else:
                todo_dict[Todo.PROPERTY_PRIORITY] = todo_line[1]
                todo_line = todo_line[3:]

            t_items = todo_line.strip().split()
            todo_dict[Todo.PROPERTY_CHANGED]=None
            dates = []
            description = []
            contexts = []
            projects = []
            attributes = {}

            for item in t_items:

                # check if this is a date
                date_regex = re.search(date_pattern, item)
                if date_regex is not None:
                    try:

                        dt = DateTime.strptime(date_regex.group(), '%Y-%m-%d')
                        dates.append(dt)
                    except ValueError as e:
                        logger.error("Couldn't convert DateTime: %s",e)
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

                    # special case attribute is date_changed
                    if key == Todo.ATTRIBUTE_DATE_CHANGED:
                        todo_dict[Todo.PROPERTY_DATE_CHANGED]=value

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
            todo_dict[Todo.PROPERTY_ORIGINAL] = todo.strip()
            todo_dict[Todo.PROPERTY_HASH] = todo_hash
            todo_dict[Todo.PROPERTY_INDEX] = index
            todo_list_dict[index] = todo_dict

            index += 1
            logger.debug("\n --- Todo Dictionary, entry %s ---",todo_hash)
            logger.debug("     [%s]",todo)
            logger.debug(pprint.pformat(todo_dict,indent=4,compact=True,width=40))

        return todo_list_dict

    @staticmethod
    def get_todo_hash(todo_s:str):
        """ Calculates Hash from Todo String (dropping spaces) """
        # find and drop any hash property
        REGEX_HASH=f"( {Todo.ATTRIBUTE_HASH}:\\w+)"
        hash_prop=re.findall(REGEX_HASH,todo_s)
        if hash_prop:
            todo_s=todo_s.replace(hash_prop[0],"")
        hash_s=todo_s.strip()
        hash_s=hash_s.replace(" ","")
        hash_value=Todo.get_hash(hash_s)
        logger.debug("String [%s], hash value (%s)",hash_s,hash_value)
        return hash_value

    @staticmethod
    def get_todo_from_dict(todo_list_dict: dict, calc_hash:bool=True):
        """ transforms todo.txt dictionary back into lines of todo.txt strings """
        todo_list = []
        logger.debug("\n--- get_todo_from_dict ---")

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
                hash_value=Todo.get_todo_hash(todo_line)
                todo_line += " "+f"{Todo.ATTRIBUTE_HASH}:"+hash_value

            logger.debug("\n --- Dictionary, %s ---",k)
            logger.debug(pprint.pformat(v,indent=4,compact=True,width=40))
            logger.debug(" ->  %s",todo_line)

            todo_list.append(todo_line)

        return sorted(todo_list, key=str.lower, reverse=False)



class TodoList():
    """ Handling of Todo List including Filehandling """

    CHANGED="CHANGED"
    DELETED="DELETED"
    ADDED="ADDED"
    ARCHIVED="ARCHIVED"
    LIST_CHANGES=[ADDED,CHANGED,DELETED,ARCHIVED]

    def __init__(self,f:str) -> None:
        """ constructor, requires link to config file """
        self._config = TodoConfig(f)
        # check for correct configuration
        self._config.is_config_valid()
        self._todo_dict = {}
        self._archive_dict = {}
        self._counter = 0
        self._changed_todos = { TodoList.CHANGED:{},
                                TodoList.DELETED:{},
                                TodoList.ADDED:{},
                                TodoList.ARCHIVED:{} }

    @property
    def config(self):
        """ fconfiguration """
        return self._config

    def read_list(self,read_archive:bool=False):
        """ reads todo list from todo.txt file  """
        if not self._config.is_config_valid():
            return
        f_todo=self._config.file_todo
        todo_list = fm.read_txt_file(f_todo)

        self._todo_dict = Todo.get_dict_from_todo(todo_list,origin=TodoConfig.TODO)
        self._counter = len(self._todo_dict )

        for index, todo_dict_item in self._todo_dict.items():
            todo_dict_item[Todo.PROPERTY_NEW]=self.get_todo(index)
            todo_dict_item[Todo.PROPERTY_COLORIZED]=self.get_todo(index,is_colored=True)

        if read_archive:
            start_index = 1
            f_archive=self._config._file_archive
            archive_list = fm.read_txt_file(f_archive)
            self._archive_dict = Todo.get_dict_from_todo(archive_list,origin=TodoConfig.ARCHIVE,start_index=start_index)
            default_prio=self.config.default_prio
            add_date_changed=self.config.date_changed
            for index, arch_dict_item in self._archive_dict.items():
                Todo.amend(arch_dict_item,default_prio,add_date_changed,self.config.color_map)

    def backup(self):
        """ Creates a backup of both archive and todo """
        #   s=colorize(value.strftime("%Y-%m-%d"),color)
        prefix=DateTime.now().strftime("%Y%m%d_%H%M%S")+"_"
        p_backup = self._config._path_backup
        f_todo=self._config._file_todo
        f_todo_backup=os.path.join(p_backup, prefix+self._config.todo_backup)
        f_todo_archive=self._config._file_archive
        f_todo_archive_backup=os.path.join(p_backup, prefix+self._config.archive_backup)

        logger.debug("### Archiving")
        logger.debug("    -%s",f_todo)
        logger.debug("     %s",f_todo_backup)
        logger.debug("    -%s",f_todo_archive)
        logger.debug("     %s",f_todo_archive_backup)
        shutil.copy(src=f_todo,dst=f_todo_backup)
        shutil.copy(src=f_todo_archive,dst=f_todo_archive_backup)

    def amend(self,index:int):
        """ amend data with default data if missing """
        todo_dict = self._todo_dict.get(index)
        default_prio=self._config.default_prio
        add_date_change=self._config.date_changed
        if not todo_dict:
            logger.warning("Couldn't find Todo Item at index %s",index)
            return
        todo_dict_amend = Todo.amend(todo_dict,default_prio,add_date_change,self.config.color_map)
        if todo_dict_amend.get(Todo.PROPERTY_CHANGED) is True:
            self._changed_todos[TodoList.CHANGED][index]=todo_dict
        return todo_dict_amend

    def _amend_todo_dict(self,todo_dict:dict):
        """ amends the transferred dict by standard settings """
        default_prio=self._config.default_prio
        add_date_change=self._config.date_changed
        # TODO RECOLOR
        return Todo.amend(todo_dict,default_prio,add_date_change)

    def add_todo(self,todo_str:str):
        """ adds a todo item to the todo list """
        counter=self._counter+1
        todo_dict = Todo.get_dict_from_todo(todo_list=[todo_str],start_index=counter)[counter]
        self._todo_dict[counter]=self._amend_todo_dict(todo_dict)
        self._counter=counter
        self._changed_todos[TodoList.ADDED][counter]=todo_dict


    def _get_amended_todo_str(self,todo_str,colorize:bool=False):
        """ returns the amended version of a todo string """
        todo_dict = Todo.get_dict_from_todo([todo_str])[1]
        self._amend_todo_dict(todo_dict)
        if colorize:
            return Todo.get_todo(todo_dict,color_map=self.config.color_map)
        else:
            return Todo.get_todo(todo_dict)

    def add_todo_input(self):
        """ adds a todo item with additional display of information """
        stats=self.get_stats()
        color_map=self.config.color_map
        contexts=sorted(list(stats.get(Todo.PROPERTY_CONTEXTS,{}).keys()))
        projects=sorted(list(stats.get(Todo.PROPERTY_PROJECTS,{}).keys()))
        attributes=sorted(list(stats.get(Todo.PROPERTY_ATTRIBUTES,{}).keys()))
        col={"prj":color_map.get(Todo.PROPERTY_PROJECTS),
             "ctx":color_map.get(Todo.PROPERTY_CONTEXTS),
             "att":color_map.get(Todo.PROPERTY_ATTRIBUTES)
             }
        if self.config.color_map:
            color_map=self.config.color_map
            contexts=[Todo.colorize("@"+c,col["ctx"]) for c in contexts]
            projects=[Todo.colorize("+"+p,col["prj"]) for p in projects]
            attributes=[Todo.colorize(a,col["att"]) for a in attributes]
        print(Todo.colorize("PROJECTS  : ",col["prj"]),", ".join(projects))
        print(Todo.colorize("CONTEXTS  : ",col["ctx"]),", ".join(contexts))
        print(Todo.colorize("ATTRIBUTES: ",col["att"]),", ".join(attributes))
        new_todo_s=input("NEW:\n")
        if new_todo_s == "":
            print("No Input")
            return
        colorize = self.config.colorize
        new_todo_colored=self._get_amended_todo_str(new_todo_s,colorize)
        print(f"ADDING LINE ({self._counter+1})\n{new_todo_colored}")
        self.add_todo(new_todo_s)

    def save(self,output:bool=False):
        """ save all changes (also on console)"""

        def _clean_change_log():
            """ get rid of duplicates in changed todo list"""
            arch_keys=list(self._changed_todos.get(TodoList.ARCHIVED,{}).keys())
            del_keys=list(self._changed_todos.get(TodoList.DELETED,{}).keys())
            add_keys=list(self._changed_todos.get(TodoList.ADDED,{}).keys())
            changed_keys=list(set([*arch_keys,*del_keys,*add_keys]))
            meta_keys=self._changed_todos.get(TodoList.CHANGED,{}).keys()

            for changed_key in changed_keys:
                if changed_key in meta_keys:
                    _ = self._changed_todos.get(TodoList.CHANGED).pop(changed_key)

        _clean_change_log()

        color=None
        archive_list=[]
        todo_list=[]

        if output:
            print("\n####   SAVE CHANGES (TODO LIST)")
            if self.config.colorize:
                color=self.config.color_map.get(Todo.PROPERTY_COMPLETE)


        for index in sorted(list(self._todo_dict.keys())):
            todo_s=self.get_todo(index)
            todo_out = todo_s
            if output and self.config.colorize:
                todo_out=self.get_todo(index,is_colored=self.config.colorize)
                todo_list.append(todo_s)
                if self._todo_dict[index].get(Todo.PROPERTY_CHANGED,False) is True:
                    chg="(CHG) "
                else:
                    chg="      "
                print(f"{chg} [{str(index).zfill(3)}] {todo_out}")

        # update archive if items were archived
        new_archive_item_dict = self._changed_todos.get(TodoList.ARCHIVED)
        if new_archive_item_dict:

            archive_output=[]
            idx=1

            for index in sorted(list(new_archive_item_dict.keys())):
                arch_todo = new_archive_item_dict[index][Todo.PROPERTY_NEW]
                archive_list.append(arch_todo)
                if output:
                    out_s = f"(ARC)  [{str(index).zfill(3)}] {Todo.colorize(arch_todo,color)}"
                    archive_output.append(out_s)
                    idx += 1

            for index in sorted(list(self._archive_dict.keys())):
                arch_todo = self._archive_dict[index][Todo.PROPERTY_NEW]
                archive_list.append(arch_todo)
                if output:
                    out_s = f"       [{str(idx).zfill(3)}] {Todo.colorize(arch_todo,color)}"
                    archive_output.append(out_s)
                    idx += 1

            if output:
                print("\n####   SAVE CHANGES (TODO ARCHIVE)")
                _ = [print(arch_todo) for arch_todo in archive_output]

        if output:
            deleted_item_dict = self._changed_todos.get(TodoList.DELETED)
            if deleted_item_dict:
                print("\n####   DELETIONS")
                deletion_list=[]
                for index in sorted(list(deleted_item_dict.keys())):
                    del_todo = deleted_item_dict[index][Todo.PROPERTY_NEW]
                    out_s = f"(DEL)  [{str(index).zfill(3)}] {Todo.colorize(del_todo,color)}"
                    deletion_list.append(out_s)
                _ = [print(del_todo) for del_todo in deletion_list]

            changes_s="\n####   CHANGES: "
            for change in TodoList.LIST_CHANGES:
                if self._changed_todos.get(change):
                    changes_s += change+":"+str(list(self._changed_todos.get(change).keys()))+"; "
            print(changes_s)
        
    def complete(self,index:int):
        """ completes a todo """
        todo_dict = self._todo_dict.get(index)
        todo_dict[Todo.PROPERTY_COMPLETE]=True
        Todo.amend(todo_dict,color_map=self.config.color_map)

    def change_todo_input(self,index:int):
        """ changes todo using dialog / displays previous todo """

        colorize = self.config.colorize
        old_todo_s=self._todo_dict[index].get(Todo.PROPERTY_ORIGINAL)
        if not old_todo_s:
            logger.warning("Couldn't access ols todo string for todo %s",index)
        old_todo_colored=self._get_amended_todo_str(old_todo_s,colorize)
        old_todo_s=self._get_amended_todo_str(old_todo_s)
        print(f"CHANGE TODO [{index}]:\n{old_todo_colored}")
        new_todo_s=input("CHANGE:\n")
        if new_todo_s == old_todo_s or new_todo_s == "":
            print("Nothing changed/No Input")
            return
        # check for valid input
        new_todo_colored=self._get_amended_todo_str(new_todo_s,colorize)
        print(f"CHANGING TO\n{new_todo_colored}")
        self.change_todo(index,new_todo_s)

    def change_todo(self,index:int, todo_str:str):
        """ change / replace the todo by input / returns the changed item """
        todo_dict = Todo.get_dict_from_todo(todo_list=[todo_str],start_index=index)[index]
        todo_dict = self._amend_todo_dict(todo_dict)

        try:
            todo_dict_old = self._todo_dict.pop(index)
            self._changed_todos[TodoList.CHANGED][index]=todo_dict_old
        except KeyError as e:
            logger.warning("Index %s, not found %s",index,e.with_traceback)
            return
        self._todo_dict[index]=todo_dict
        return todo_dict

    def delete(self,index:int):
        """ delete the given todo item, returns deleted item """
        try:
            todo_dict = self._todo_dict.pop(index)
            self._changed_todos[TodoList.DELETED][index]=todo_dict
            return todo_dict
        except KeyError as e:
            logger.warning("Index %s, not found %s",index,e.with_traceback)
            return

    def get_todo(self,index:int,is_colored=False,as_dict=False,as_json=False):
        """ gets the item as text / color formatted todo / dict item / json
        """

        # todo_dict = self._todo_dict.get(index,{})
        todo_dict = self.amend(index)
        if as_dict:
            return todo_dict
        elif as_json:
            return pprint.pformat(todo_dict,indent=4)        
        else: 
            if is_colored:
                return todo_dict.get(Todo.PROPERTY_COLORIZED)
            else:
                return todo_dict.get(Todo.PROPERTY_NEW)

        # if as_dict:
        #     return todo_dict
        # elif as_json:
        #     return pprint.pformat(todo_dict,indent=4)
        # else:
        #     color_map=None
        #     if is_colored:
        #         color_map=self._config.color_map
        #     return Todo.get_todo(todo_dict,color_map)

    def archive(self):
        """ moves completed items to archive """
        delete_index=[]
        for index,todo_dict in self._todo_dict.items():
            if todo_dict.get(Todo.PROPERTY_COMPLETE) is True:
                delete_index.append(index)
                self._changed_todos[TodoList.ARCHIVED][index]=todo_dict.copy()
        for index in delete_index:
            _ = self._todo_dict.pop(index)
            # self.delete_todo(index)


    def print_config(self)->str:
        """ prints config generated from yaml configuration """
        print(repr(self._config))

    def get_df(self)->DataFrame:
        """ returns todo list as data frame """
        # TODO fix warning
        df = DataFrame.from_dict(self._todo_dict,orient="index")
        return df

    def get_stats(self,as_json=False):
        """ returns todo list stats """

        def get_list_counts(columns,df):
            """ create occurences of attributes in list """
            out_dict={}
            for column in columns:
                if not column in df.columns:
                    continue
                list_items=df[column].sum()
                count_dict={}
                for key in set(list_items):
                    count_dict[key]=list_items.count(key)
                out_dict[column]=count_dict
            return out_dict

        df = self.get_df()

        # task stats
        list_counts={}
        task_dict={}
        task_dict[Todo.PROPERTY_TOTAL]=df.shape[0]
        task_dict[Todo.PROPERTY_COMPLETED]=(df[Todo.PROPERTY_COMPLETE] == True).sum()
        task_dict[Todo.PROPERTY_OPEN]=(df[Todo.PROPERTY_COMPLETE] == False).sum()
        list_counts[Todo.PROPERTY_TASKS]=task_dict

        # number of prios
        prio_list=[p for p in list(df["PRIO"].unique()) if p is not None]
        prio_dict={}
        for prio in prio_list:
            prio_dict[prio]=(df[Todo.PROPERTY_PRIORITY]==prio).sum()
        list_counts[Todo.PROPERTY_PRIORITY]=prio_dict

        list_columns=[Todo.PROPERTY_PROJECTS,Todo.PROPERTY_CONTEXTS]
        list_counts={**list_counts,**get_list_counts(list_columns,df)}

        # attributes list
        list_counts[Todo.PROPERTY_ATTRIBUTES]={}
        attributes=df[Todo.PROPERTY_ATTRIBUTES].apply(lambda d:list(d.keys()) if isinstance(d,dict) else []).sum()
        for attribute in set(attributes):
            list_counts[Todo.PROPERTY_ATTRIBUTES][attribute]=attributes.count(attribute)

        # dates list
        list_columns=[Todo.PROPERTY_DATE_CREATED,Todo.PROPERTY_DATE_COMPLETED,Todo.PROPERTY_DATE_CHANGED]
        dates_dict={}
        for column in list_columns:
            if not column in df.columns:
                continue
            # get list of dates as string
            dates=df[df[column].notna()][column]
            if is_datetime64_any_dtype(df[column].dtype):
                date_strings=list(dates.apply(lambda dt:dt.strftime("%Y-%m-%d")))
            else:
                date_strings= list(dates.astype(str))

            date_dict={}
            for date_s in set(date_strings):
                date_dict[date_s]=date_strings.count(date_s)
            dates_dict[column]=date_dict

        list_counts[Todo.PROPERTY_DATE_LIST] = dates_dict

        if as_json:
            return pprint.pformat(list_counts,indent=4)
        else:
            return list_counts

    def filter(self,index:int,filter_set_name:str,search_term:str=None):
        """ filter item at index using filter set """
        todo_dict=self.get_todo(index,as_dict=True)
        if not todo_dict:
            return
        if not hasattr(self._config,"_filter"):
            print("NO CONFIGURATION FOUND FOR FILTER, CHECK YOUR CONFIG YAML")
            return True
        todo_filter = self._config._filter
        is_filtered = todo_filter.filter(todo_dict,filter_set_name,search_term)
        return is_filtered

    def get_task_dict(self,group_by:str,filter_set_name:str=None,search_term:str=None,color:bool=False):
        """ returns copy of task list grouped by criteria in dict and output may be filtered filter
        """
        out_dict={}
        # Todo.PROPERTY_COMPLETED
        properties=list(Todo.PROPERTY_DICT.values())

        if group_by and not group_by in properties:
            print(f"Attribute {group_by} is not a valid group attribute, check")

        for index,todo_item in self._todo_dict.items():

            # filter item
            if filter_set_name:
                passed_filter=self.filter(index,filter_set_name,search_term)
                if not passed_filter:
                    continue

            if group_by:
                group_keys=todo_item.get(group_by)
            else:
                group_keys=todo_item.get(Todo.PROPERTY_INDEX)

            if not group_keys:
                continue
            if isinstance(group_keys,dict):
                att_list=[]
                for att in group_keys.keys():
                    att_list.append(att)
            elif not isinstance(group_keys,list):
                group_keys=[group_keys]

            for group_key in group_keys:
                grouped_todos = out_dict.get(group_key,[])
                if not grouped_todos:
                    out_dict[group_key]=grouped_todos
                if color:
                    todo=self.get_todo(index,is_colored=True)
                else:
                    todo=todo_item.get(Todo.PROPERTY_NEW)
                grouped_todos.append("["+str(index).zfill(2)+"] "+todo)

        return out_dict

    # TODO CHANGE TOdo set completed
    # TODO ARCHIVE ITEM
    # TODO COLOR PRIORITY LABEL

class TodoFilter():
    """ Filtering Todo Items """

    # Filter VALUES
    # TYPE="TYPE"                    # filter type, allowed: REGEX, DATE, VALUE
    PROPERTY="PROPERTY"              # property name to be filtered (Any of the PROPERTY_... values)
    PROPERTY_ORIGINAL="PROPERTY_ORIGINAL"  # property name to be filtered (Any of the PROPERTY_... values)
    INFO = "INFO"           # PROPERTY for optional Info string
    REGEX="REGEX"                    # will use REGEX filter
    DATE="DATE"                      # begin of date range, is today if not supplied
    DATE_FROM="DATE_FROM"            # begin of date range, is today if not supplied
    DATE_TO="DATE_TO"                # end of date range, is today if not supplied
    INCLUDE="INCLUDE"                # include search to pass, values: true (DEFAULT) or false  (then it's excluded)
    VALUE="VALUE"                    # will search for value to be filtered
    TYPE="TYPE"                      # will search for value to be filtered
    PATTERN="PATTERN"                # search pattern
    REGEX_TODAY="TODAY([+-].\d+)?"   # regex for today pattern TODAY[+-]#
    REGEX_DATE=r"20\d\d[01]\d[0-3]\d" # regex for day pattern 20YYMMDD

    # Keys for Dict Access
    FILTER="FILTER"
    FILTER_LIST="FILTER_LIST" # Single Filter Rules
    FILTER_SETS="FILTER_SETS" # FILTER SETS

    VALID_FILTER_ROPERTIES = [PROPERTY,REGEX,INCLUDE,DATE_FROM,DATE_TO,VALUE,INFO,TYPE]

    def __init__(self,filter_config:dict, property_list:list=None) -> None:
        """ Constructor gets filter settings from TodoConfig """
        self._filter_config = filter_config
        self._filter_dict = None
        self._filter_sets = None
        self._property_list = property_list

        if not filter_config:
            logger.warning("No Filter Configuration")

        # parse all filters
        self._parse_config_dict(self._filter_config)

    @staticmethod
    def get_date(d):
        """ get date from search pattern """
        if isinstance(d,DateTime):
            return d

        if d is None:
            return DateTime.now()

        match=re.findall(TodoFilter.REGEX_TODAY,d,re.IGNORECASE)
        dt=None
        if match:
            dt=DateTime.now()
            try:
                offset = int(match[0])
            except ValueError:
                offset = 0
            dt=dt+TimeDelta(days=offset)
        else:
            d=d.replace("-","")
            match=re.findall(TodoFilter.REGEX_DATE,d,re.IGNORECASE)
            if match:
                y,m,d=[int(v) for v in match[0]]
                dt=DateTime(year=y,month=m,day=d)
            else:
                print(f"{d} is no Valid Date Pattern, check input")

        return dt

    def _parse_config_dict(self,filter_config:dict):
        """ complement and validate filter list """

        filter_list=filter_config.get(TodoFilter.FILTER_LIST)
        if not filter_list:
            print("*** NO FILTER LIST FOUND")
            return

        filter_sets=filter_config.get(TodoFilter.FILTER_SETS)
        if not filter_sets:
            print("*** NO FILTER SETS FOUND")


        self._filter_dict = {}
        for filter_name , filter_properties in filter_list.items():

            filter_properties[TodoFilter.TYPE]=None
            logger.debug("### Configuring Filter %s",filter_name)

            # check for correct FILTER LIST PROPERTIES
            filter_property_keys=list(filter_properties.keys())
            props_valid = [prop in TodoFilter.VALID_FILTER_ROPERTIES for prop in filter_property_keys]
            if not all(props_valid):
                logger.error("Filter %s has invalid attributes: %s, pls check",filter_name,filter_property_keys)
                continue


            if not filter_properties.get(TodoFilter.PROPERTY):
                logger.warning("Filter: %s, no PROPERTY found, will be set to ORIGINAL TODO Line",filter_name)
                filter_properties[TodoFilter.PROPERTY]=TodoFilter.PROPERTY_ORIGINAL

            # CHECK FOR CORRECT PROPERTY  FIELDS IF LIST AVAILABLE
            if self._property_list:
                prop = filter_properties.get(TodoFilter.PROPERTY)
                if not prop in self._property_list:
                    logger.warn("Filter: %s, PROPERTY with value %s can not be validated, check",filter_name,property)
                    continue

            filter_properties[TodoFilter.INCLUDE] = filter_properties.get(TodoFilter.INCLUDE,True)

            # TODO set appropriate values for different filter type
            if filter_properties.get(TodoFilter.VALUE):
                filter_properties[TodoFilter.TYPE]=TodoFilter.VALUE
                filter_properties[TodoFilter.PATTERN]=filter_properties.get(TodoFilter.VALUE)
            elif filter_properties.get(TodoFilter.REGEX):
                filter_properties[TodoFilter.TYPE]=TodoFilter.REGEX
                filter_properties[TodoFilter.PATTERN]=filter_properties.get(TodoFilter.REGEX)
            elif filter_properties.get(TodoFilter.DATE_FROM) or filter_properties.get(TodoFilter.DATE_TO):
                filter_properties[TodoFilter.TYPE]=TodoFilter.DATE
                date_from = TodoFilter.get_date(filter_properties.get(TodoFilter.DATE_FROM,"TODAY"))
                date_to = TodoFilter.get_date(filter_properties.get(TodoFilter.DATE_TO,"TODAY"))
                filter_properties[TodoFilter.PATTERN]=[date_from,date_to]

            self._filter_dict[filter_name] = filter_properties

        self._filter_sets={}

        # now add single filters as filter sets
        for filter_name in self._filter_dict.keys():
            self._filter_sets[filter_name] = [filter_name]

        if filter_sets:
            # cross check for correct filter sets
            valid_filters = self._filter_dict.keys()
            #self._filter_sets = self._filter_config.get(TodoFilter.FILTER_SETS)

            for filterset_name, filter_list in filter_sets.items():
                logger.debug("### Check Filter Set %s",filterset_name)
                exist = [v in valid_filters for v in filter_list]
                if not all(exist):
                    logger.warning("### FILTERSET %s contains invalid filter references and will be ignored please check",filterset_name)
                    continue
                self._filter_sets[filterset_name]=filter_list

    def get_filter_settings_dict(self):
        """ returns validated filter data """
        # TODO COLORIZE DICT
        return {
           TodoFilter.FILTER_LIST: self._filter_dict,
           TodoFilter.FILTER_SETS: self._filter_sets
        }

    def __repr__(self)->str:
        return pprint.pformat(self.get_filter_settings_dict(),indent=4)


    def filter(self,todo_dict:dict,filter_set_name:str,search_term:str=None):
        """ Filter Todo Dict. search variable can be used to
           override search term from template
        """

        def filter_date(d,date_interval):
            d_ts = TodoFilter.get_date(d).timestamp()
            from_ts=date_interval[0].timestamp()
            to_ts=date_interval[1].timestamp()
            if d_ts >= from_ts and d_ts <= to_ts:
                return True
            else:
                return False

        filter_passed = []

        # get filter
        filter_sets=self._filter_sets.get(filter_set_name)
        if not filter_sets:
            logger.warning("Could not find filter set %s",filter_set_name)
            return

        for filter_name in filter_sets:
            filter_dict = self._filter_dict.get(filter_name)
            if not filter_dict:
                logger.warning(f"Could not find filter %s, filter set %s",filter_name,filter_set_name)
                return

            filter_type = filter_dict.get(TodoFilter.TYPE)
            if not filter_type:
                logger.warning(f"Could not find filter type for filter set %s",filter_set_name)
                return

            todo_property = filter_dict.get(TodoFilter.PROPERTY)
            if not todo_property:
                logger.warning(f"Couldn't find Todo Property for filter set %s",filter_set_name)
                return

            if search_term:
                pattern = search_term
            else:
                pattern = filter_dict.get(TodoFilter.PATTERN)
                if not pattern:
                    logger.warning(f"Couldn't find Todo Search Pattern property for filter set %s",filter_set_name)
                    return

            prop = Todo.PROPERTY_DICT.get(todo_property)
            value = todo_dict.get(prop)

            if value is None:
                logger.warning("Couldn't find Value for Property %s using filter set %s",todo_property,filter_set_name)
                return

            # do the test for the various options
            passed = False
            if filter_type == TodoFilter.VALUE:
                if isinstance(value,str):
                    if pattern in value:
                        passed = True
                elif isinstance(value,bool):
                    if pattern == value:
                        passed = True

            elif filter_type == TodoFilter.REGEX:
                match=re.findall(pattern,value,re.IGNORECASE)
                if match:
                    passed = True
            elif filter_type == TodoFilter.DATE:
                passed = filter_date(value,pattern)
            else:
                logger.warning("Invalid filter Type %s used in filter %s, check",filter_type,filter_name)
                return

            # now check for including / excluding criteria
            if not filter_dict.get(TodoFilter.INCLUDE,True):
                passed = not passed

            filter_passed.append(passed)

        filter_passed = all(filter_passed)
        return filter_passed

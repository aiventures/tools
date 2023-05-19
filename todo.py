""" Basic parsing implementation of the todo.txt specification
        https://github.com/todotxt/todo.txt
        http://todotxt.org/
        will transform lines of strings in todo format into json and vice versa
"""

import pprint
import re
import traceback
import hashlib
from datetime import datetime

class Todo:
    """ todo.txt transform string<->dict """
    ATTRIBUTE_HASH="hash"

    @staticmethod
    def get_hash(s):
        """ calculates a hash string of transferred string """
        hash_object = hashlib.md5(s.encode())
        return hash_object.hexdigest()

    @staticmethod
    def get_dict_from_todo(todo_list: list, show_info: bool = False):
        """ transforms list of todo strings (in array) into dictionary"""
        pp = pprint.PrettyPrinter(indent=4)
        date_pattern = r"^\d{4}-\d{1,2}-\d{1,2}"
        attribute_pattern = "([^:]+):([^:]+)" # alphanumeric separated by colon

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
            todo_dict["changed"]=None
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
                        todo_dict["done"] = True
                        todo_dict["prio"] = None
                        continue
                    else:
                        todo_dict["done"] = False
                        prio_regex = re.search(r"\((\w)\)", item)
                        if prio_regex is None:
                            todo_dict["prio"] = None
                        else:
                            todo_dict["prio"] = item[1]
                            continue

                # check if this is a date
                date_regex = re.search(date_pattern, item)
                if date_regex is not None:
                    try:
                        dt = datetime.strptime(date_regex.group(), '%Y-%m-%d')
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

                # check for either attributes or strings
                attribute_regex = re.findall(attribute_pattern, item)

                if len(attribute_regex) == 1:
                    key = attribute_regex[0][0]
                    # format value into other format if applicable
                    value = attribute_regex[0][1]
                    try:
                        date_value = datetime.strptime(value, '%Y-%m-%d')
                        attributes[key] = date_value
                    except ValueError:
                        attributes[key] = value

                    # set changed attrbiute in case we have line hash values from line and calculated
                    if key == Todo.ATTRIBUTE_HASH:
                        if value == todo_hash:
                            todo_dict["changed"]=False
                        else:
                            todo_dict["changed"]=True

                else:
                    key = None
                    value = None
                    description.append(item)

            todo_dict["date_started"] = None
            todo_dict["date_finished"] = None
            if len(dates) > 0:
                if todo_dict["done"]:
                    todo_dict["date_finished"] = dates[0]
                    if len(dates) > 1:
                        todo_dict["date_started"] = dates[1]
                else:
                    todo_dict["date_started"] = dates[0]

            todo_dict["description"] = " ".join(description)
            todo_dict["contexts"] = contexts
            todo_dict["projects"] = projects
            todo_dict["attributes"] = attributes

            todo_list_dict[todo_hash] = todo_dict
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
            todo_s = []

            if v["done"]:
                todo_s.append("x")
            else:
                if v["prio"]:
                    todo_s.append(("("+v["prio"]+")"))
            if v["date_finished"]:
                todo_s.append(datetime.strftime(v["date_finished"], "%Y-%m-%d"))
            if v["date_started"]:
                todo_s.append(datetime.strftime(v["date_started"], "%Y-%m-%d"))
            todo_s.append(v["description"])
            if v["projects"]:
                todo_s.extend(list(map(lambda li: "+"+li, v["projects"])))
            if  v["contexts"]:
                todo_s.extend(list(map(lambda li: "@"+li, v["contexts"])))

            for attr_k, attr_v in v["attributes"].items():
                if attr_k == Todo.ATTRIBUTE_HASH:
                    continue

                if isinstance(attr_v, datetime):
                    attr_v = datetime.strftime(attr_v, "%Y-%m-%d")
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

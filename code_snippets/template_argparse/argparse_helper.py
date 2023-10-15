""" argparse template  and utility for handling / converting csv, yaml, json """

# https://docs.python.org/3/library/argparse.html
import argparse
import logging
import json
import sys
import os
import re
from enum import Enum
from pathlib import Path
from datetime import datetime as DateTime
import yaml
from yaml import CLoader

logger = logging.getLogger(__name__)

class Status(Enum):
    """ genric status """
    UNKNOWN = "unknown"
    IN_PROCESS = "in_process"
    NOT_RELEVANT = "not_relevant"
    DONE = "done"
    IGNORE = "ignore"

class LogLevel(Enum):
    """ loglevel handling """
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    @staticmethod
    def get(level:str)->int:
        """ returns the integer loglevel with a default level of info"""
        if not level:
            level = "INFO"
        try:
            level = LogLevel[level.upper()].value
        except KeyError:
            level = LogLevel["INFO"].value
        return level

class ParserAttribute(Enum):
    """ Configuration, each param is modeled as a dictionary """
    DESCRIPTION = "description"
    EPILOG      = "epilog"
    PARAM       = "param"
    PARAM_SHORT = "param_short"
    DEFAULT     = "default"
    ACTION      = "action"
    DEST        = "dest"
    HELP        = "help"
    METAVAR     = "metavar" # used for help text
    TYPE        = "type"
    STORE_TRUE  = "store_true"
    STORE_FALSE = "store_false"
    VAR         = "variable"

class ParserTemplate(Enum):
    """ Some Default Templates for arg parse input parameters """
    BOOL_TEMPLATE_TRUE = { "dest":None,
                           "action":ParserAttribute.STORE_TRUE.value,
                           "help":"No help"
    }

    BOOL_TEMPLATE_FALSE = { "dest":None,
                            "action":ParserAttribute.STORE_FALSE.value,
                            "help":"No help"
    }

    PARAM_TEMPLATE = { "default":None,
                       "type":str,
                       "help":"No help",
                       "metavar":"var"
                    }

    PARAM_INPUTFILE = { "default":"file_in",
                        "type":str,
                        "help":"Input file path",
                        "metavar": "<filename_in>"
                    }

    PARAM_OUTPUTFILE = { "default":"file_out",
                        "type":str,
                        "help":"Output file path",
                        "metavar": "<filename_out>"
                     }

    PARAM_LOGLEVEL = { "default":"info",
                       "type":str,
                       "choices":["debug","info","warning","error"],
                       "help":"Set loglevel to (debug,info,warning,error)",
                       "metavar":"<level>",
                       "args": ["--loglevel","-lg"]
                    }

    PARAM_CSV_SEPARATOR = { "default":";",
                            "type":str,
                            "help":"csv file separator, default is ;",
                            "metavar": "<sep>",
                            "args": ["--csv_sep","-cs"]
                           }

    PARAM_DECIMAL_SEP = {   "default":",",
                            "type":str,
                            "help":"decimal spearator, default is ,",
                            "metavar": "<decsep>",
                            "args": ["--dec_sep","-ds"]
                           }

    PARAM_ADD_TIMESTAMP = { "dest":"add_timestamp",
                            "action":ParserAttribute.STORE_TRUE.value,
                            "help":"add timestamp to filename",
                            "args": ["--add_timestamp","-as"]
                           }
    @staticmethod
    def get_value(name:str)->dict:
        """ returns a template if found """
        out = None
        try:
            enum_value = ParserTemplate[name]
            out = enum_value.value
        except ValueError:
            logger.error(f"Couldn't find Enum for key {name}")
        return out
    
    @staticmethod
    def as_dict()->dict:
        """ gets enum as dict """
        out = {}
        for enum_item in iter(ParserTemplate):
            out[enum_item.name]=enum_item.value
        return out

    @staticmethod
    def get_parser_arguments(template,arg_long:str,arg_short:str,params:dict)->dict:
        """ get parser args and kwargs from a template dict """
        cmd_args=["--"+arg_long,"-"+arg_short]
        # try to get every arguments in the template
        template_dict = ParserTemplate[template.name].value.copy()
        # copy over dest value for flag arguments
        try:
            template_dict["dest"]=arg_long
            #arg_is_flag = True
        except KeyError:
            pass
            #arg_is_flag = False
        # use passed arguments or default values from template
        for key,template_value in template_dict.items():
            try:
                value = params[key]
            except KeyError:
                if template_value:
                    value = template_value
                else:
                    logger.error(f"Parameter {arg_long} value missing for {key}")
                    continue
            template_dict[key] = value
        return (cmd_args,template_dict)

class PersistenceHelper():
    """ Helper class to read / write (single) file """

    # byte order mark indicates non standard UTF-8
    BOM = '\ufeff'
    NUM_COL_TITLE = "num" # csv column title for number
    ID_TITLE = "id" # column name of object header
    TEMPLATE_DEFAULT_VALUE = "undefined" # default value for template value

    ALLOWED_FILE_TYPES = ["yaml","txt","json","plantuml"]

    def __init__(self,f_read:str=None,f_save:str=None,**kwargs) -> None:
        """ constructor """
        self._cwd = os.getcwd()
        if f_read:
            if os.path.isfile(f_read):
                self._f_read = os.path.abspath(f_read)
                logger.info(f"File read path: [{self._f_read}]")
            else:
                self._f_read = None
                logger.warning(f"File path {f_read} not found, check")
        self._f_save = None
        if f_save:
            logger.info(f"File save path: {f_save}")
            self._f_save = f_save
        # get more params form kwargs
        self._dec_sep = kwargs.get("dec_sep",",")
        self._csv_sep = kwargs.get("csv_sep",";")
        self._add_timestamp = kwargs.get("add_timestamp",False)

        logger.debug(f"Decimal Separator: {self._dec_sep}, CSV Separator: {self._csv_sep}")

    @property
    def f_read(self)->Path:
        """ returns the original file path as path object """
        return Path(self._f_read)

    @property
    def f_save(self)->str:
        """ returns the original save path """
        if self._f_save:
            self._get_save_file_name()
        else:
            return None

    @staticmethod
    def replace_file_suffix(f_name:str,new_suffix:str):
        """ Replaces file suffix """
        p_file = Path(f_name)
        suffix = p_file.suffix
        if suffix:
            return f_name.replace(suffix,"."+new_suffix)
        else:
            return f_name+"."+new_suffix

    @staticmethod
    def dict_stringify(d:dict)->dict:
        """ converts a dict with objects to stringified dict (for json) """
        for k, v in d.copy().items():
            v_type = str(type(v).__name__)
            logger.debug(f"Key {k} type {v_type}")
            if isinstance(v, dict): # For DICT
                d[k]= PersistenceHelper.dict_stringify(v)
            elif isinstance(v, list): # itemize LIST as dict
                d[k] = [PersistenceHelper.dict_stringify(i) for i in v]
            elif isinstance(v, str): # Update Key-Value
                d.pop(k)
                d[k] = v
            elif isinstance(v,DateTime): # stringify date
                d.pop(k)
                d[k]=v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                d.pop(k)
                d[k] = v
        return d

    @staticmethod
    def get_headerdict_template(keys:list,attribute_dict:dict):
        """ creates a headerdict template from keys and attributes """
        default = PersistenceHelper.TEMPLATE_DEFAULT_VALUE
        out_dict = {}
        for key in keys:
            dict_line = {}
            for attribute,value in attribute_dict.items():
                if not value:
                    value = default
                dict_line[attribute]=value
            out_dict[key]=dict_line
        return out_dict

    @staticmethod
    def create_headerdict_template(f:str,headers:list,template_body:dict)->str:
        """ creates a headerdict template and saves it """
        template=PersistenceHelper.get_headerdict_template(headers,template_body)
        p_file=Path(f)
        p_suffix = p_file.suffix
        if not p_file.is_absolute():
            p_file = Path(os.path.join(os.getcwd(),f))
        p_file = str(p_file)
        if p_suffix.lower().endswith("yaml"):
            PersistenceHelper.save_yaml(p_file,template)
        elif p_suffix.lower().endswith("json"):
            PersistenceHelper.save_json(p_file,template)
        elif p_suffix.lower().endswith("csv"):
            csv_data = PersistenceHelper.headerdict2list(template)
            persistence_helper=PersistenceHelper(f_save=p_file)
            persistence_helper.save(csv_data)
        else:
            logger.error("File template creation only allowed for type yaml,json,csv")
        logger.info(f"Created Template file {p_file}")
        return p_file

    @staticmethod
    def headerdict2list(d:dict,filter_list:list=None,header_name:str=ID_TITLE,column_list:list=None)->list:
        """ linearizes a dictionary containing header and attributes
            sample_key1:
                comment: comment 1
                property1: value1.1
                property2: value1.2
                status: open
            ...
            you may filter out entries using keywords for fields

            [{"status":"ignore"},...] would ignore any dictionaries with field status having ignore as value
            {"<header_name>":"sample"}: Any entries with header containing "sample" would be filtered
            header name attribute may be adjusted
            field list can be passed to extract only a subset / for a given order
        """
        def is_passed(header,value_dict):
            passed = True
            for f in filter_list:
                filter_field = list(f.keys())[0]
                filter_value = f[filter_field]
                value = None
                if filter_field == header_name:
                    value = header
                else:
                    value = value_dict.get(filter_field)
                if not value:
                    continue
                if filter_value in value:
                    logger.info(f"Item [{header}] will be filtered, Rule ({filter_field}:{filter_value}), value ({value})")
                    passed = False
                    break
            return passed

        num_col_title = PersistenceHelper.NUM_COL_TITLE
        out_list = []
        columns=[]
        column_counts=[]
        index = 1
        for header,value_dict in d.items():
            if filter_list:
                passed = is_passed(header,value_dict)
                if passed is False:
                    continue
            keys = list(value_dict.keys())
            # get some stats
            columns.append(keys)
            columns = list(set(keys))
            column_counts.append(len(keys))
            column_counts=list(set(column_counts))
            line_dict = {num_col_title:str(index).zfill(2),header_name:header}
            index += 1
            for k in keys:
                line_dict[k]=str(value_dict[k])
            out_list.append(line_dict)

        logger.debug(f"Created {len(out_list)} entries, columns {columns}")
        if len(column_counts) > 1:
            logger.debug("Different Columns present for each line, appending missing columns")
            out_list_new = []
            for line_dict in out_list:
                out_dict_new={num_col_title:line_dict[num_col_title],header_name:line_dict[header_name]}
                for column in sorted(columns):
                    v = line_dict.get(column)
                    if v is None:
                        logger.debug(f"Adding empty value for line with key {line_dict[header_name]}")
                        v = ""
                    out_dict_new[column]=v
                out_list_new.append(out_dict_new)
            out_list = out_list_new

        if column_list:
            # create column subset only / use to ensure column order
            out_list_new = []
            for line_dict in out_list:
                out_dict_new={header_name:line_dict[header_name]}
                for column in column_list:
                    v = line_dict.get(column)
                    if v is not None:
                        out_dict_new[column]=v
                out_list_new.append(out_dict_new)
            out_list = out_list_new

        return out_list

    def _csv2dict(self,lines)->dict:
        """ transform csv lines to dictionary """
        out_list = []
        if len(lines) <= 1:
            logger.warning("Too few lines in CSV")
            return {}
        keys = lines[0].split( self._csv_sep)
        num_keys = len(keys)
        logger.debug(f"CSV COLUMNS ({num_keys}): {keys}")
        for i,l in enumerate(lines[1:]):
            values = l.split( self._csv_sep)
            if len(values) != num_keys:
                logger.warning(f"Entry [{i}]: Wrong number of entries, expected {num_keys} {l}")
                continue
            out_list.append(dict(zip(keys,values)))
        logger.debug(f"Read {len(out_list)} lines from CSV")
        return out_list

    def _dicts2csv(self,data_list:list)->list:
        """ try to convert a list of dictionaries into csv format """
        out = []
        if not list:
            logger.warning("no data in list")
            return None
        key_row = data_list[0]
        if not isinstance(key_row,dict):
            logger.warning("List data is ot a dictionary, nothing will be returned")
            return None
        keys = list(key_row.keys())
        out.append(self._csv_sep.join(keys))
        for data in data_list:
            data_row = []
            for k in keys:
                v=data.get(k,"")
                if self._csv_sep in v:
                    logger.warning(f"CSV Separator {v} found in {k}:{v}, will be replaced by _sep_")
                    v = v.replace(self._csv_sep,"_sep_")
                data_row.append(v)
            out.append(self._csv_sep.join(data_row))
        return out

    @staticmethod
    def read_txt_file(filepath,encoding='utf-8',comment_marker="# ",skip_blank_lines=True)->list:
        """ reads data as lines from file
        """
        lines = []
        bom_check = False
        try:
            with open(filepath,encoding=encoding,errors='backslashreplace') as fp:
                for line in fp:
                    if not bom_check:
                        bom_check = True
                        if line[0] == PersistenceHelper.BOM:
                            line = line[1:]
                            logger.warning("Line contains BOM Flag, file is special UTF-8 format with BOM")
                    if len(line.strip())==0 and skip_blank_lines:
                        continue
                    if line.startswith(comment_marker):
                        continue
                    lines.append(line.strip())
        except:
            logger.error(f"Exception reading file {filepath}",exc_info=True)
        return lines

    @staticmethod
    def read_yaml(filepath:str)->dict:
        """ Reads YAML file"""
        if not os.path.isfile(filepath):
            logger.warning(f"File path {filepath} does not exist. Exiting...")
            return None
        data = None
        try:
            with open(filepath, encoding='utf-8',mode='r') as stream:
                data = yaml.load(stream,Loader=CLoader)
        except:
            logger.error(f"Error opening {filepath} ****",exc_info=True)
        return data

    @staticmethod
    def read_json(filepath:str)->dict:
        """ Reads JSON file"""
        data = None

        if not os.path.isfile(filepath):
            logger.warning(f"File path {filepath} does not exist. Exiting...")
            return None
        try:
            with open(filepath,encoding='utf-8') as json_file:
                data = json.load(json_file)
        except:
            logger.error(f"Error opening {filepath} ****",exc_info=True)

        return data

    @staticmethod
    def save_json(filepath,data:dict)->None:
        """ Saves dictionary data as UTF8 json """
        # TODO encode date time see
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

        with open(filepath, 'w', encoding='utf-8') as json_file:
            try:
                json.dump(data, json_file, indent=4,ensure_ascii=False)
            except:
                logger.error("Exception writing file {filepath}",exc_info=True)

            return None

    @staticmethod
    def save_yaml(filepath,data:dict)->None:
        """ Saves dictionary data as UTF8 yaml"""
        # encode date time and other objects in dict see
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

        with open(filepath, 'w', encoding='utf-8') as yaml_file:
            try:
                yaml.dump(data,yaml_file,default_flow_style=False,sort_keys=False)
            except:
                logger.error(f"Exception writing file {filepath}",exc_info=True)
            return None

    def read(self):
        """ read file, depending on file extension """
        if not self._f_read:
            logger.error("No file found")
            return
        out = None
        p = Path(self._f_read)
        suffix = p.suffix[1:].lower()
        if suffix in ["txt","plantuml","csv"]:
            out = PersistenceHelper.read_txt_file(self._f_read)
            if suffix == "csv":
                out = self._csv2dict(out)
        elif suffix == "yaml":
            out = PersistenceHelper.read_yaml(self._f_read)
        elif suffix == "json":
            out = PersistenceHelper.read_json(self._f_read)
        else:
            logger.warning(f"File {self._f_read}, no supported suffix {suffix}, skip read")
            out = None

        logger.info(f"Reading {self._f_read}")

        return out

    def save_txt_file(self,filepath,data:str,encoding='utf-8')->None:
        """ saves string to file  """
        try:
            with open(filepath,encoding=encoding,mode="+wt") as fp:
                fp.write(data)
        except:
            logger.error(f"Exception writing file {filepath}",exc_info=True)
        return

    def get_adjusted_filename(self,f)->str:
        """ gets adjusted and absolute filename """

        p_file = Path(f)
        dt = DateTime.now().strftime('%Y%m%d_%H%M%S')
        if self._add_timestamp:
            p_file_new = p_file.stem+"_"+dt+p_file.suffix
        else:
            p_file_new = p_file.name

        # get path
        if p_file.is_absolute():
            p_path = str(p_file.parent)
        else:
            p_path = os.getcwd()

        f_adjusted = os.path.join(p_path,p_file_new)
        return f_adjusted

    def _get_save_file_name(self,f_save:str=None)->str:
        """ creates an adjusted and absolute save filename """
        if f_save is None:
            f_save = self._f_save

        if not f_save:
            logger.warning("No file name for saving data was found")
            return None

        f_save = self.get_adjusted_filename(f_save)
        return f_save

    def save(self,data,f_save:str=None)->str:
        """ save file, optionally with path, returns filename """
        f_save = self._get_save_file_name(f_save)

        if not f_save:
            return

        p = Path(f_save)
        suffix = p.suffix[1:].lower()

        if suffix in ["txt","plantuml","csv"]:
            if isinstance(data,list):
                try:
                    data = "\n".join(data)
                except TypeError:
                    # try to convert into a csv list
                    data = self._dicts2csv(data)
                    data = "\n".join(data)
                    if not data:
                        logger.error(f"Elements in list are not string / (plain) dicts, won't save {f_save}")
                        return
            if not isinstance(data,str):
                logger.warning(f"Data is not of type string, won't save {f_save}")
                return
            data = data+"\n"
            self.save_txt_file(f_save,data)
        elif suffix in ["yaml","json"]:
            if isinstance(data,list):
                data = {"data":data}
                logger.warning(f"Data is a list, will save it as pseudo dict in {suffix} File")
            if not isinstance(data,dict):
                logger.warning("Data is not a dict, won't save {f_save}")
                return
            # convert objects in json
            data = PersistenceHelper.dict_stringify(data)
            if suffix == "yaml":
                PersistenceHelper.save_yaml(f_save,data)
            elif suffix == "json":
                PersistenceHelper.save_json(f_save,data)
        else:
            logger.warning(f"File {f_save}, no supported suffix {suffix} (allowed: {PersistenceHelper.ALLOWED_FILE_TYPES}), skip save")
            return
        logger.info(f"Saved [{suffix}] data: {f_save}")
        return f_save

class ParserHelper():
    """ Helper class for argument parsing """

    def __init__(self,description=None,prog=None,epilog=None) -> None:
        argparser_args={}
        if prog:
            argparser_args["prog"]=prog
        if description:
            argparser_args["description"]=description
        if epilog:
            argparser_args["epilog"]=epilog

        if description:
            self._parser = argparse.ArgumentParser(**argparser_args)
        else:
            self._parser = argparse.ArgumentParser()
        self._args_dict = {}

    def parse_args(self,*testargs)->dict:
        """ get parsed results, additional args value can be used for debugging """
        self._args_dict = vars(self._parser.parse_args(*testargs))
        # transform special arguments
        loglevel = self._args_dict.get("loglevel")
        if loglevel:
            self._args_dict["loglevel"] = LogLevel.get(loglevel)
        return self._args_dict

    def add_arg_template(self,parser_template:Enum)->set:
        """ add arguments templates """
        template_dict = parser_template.value.copy()
        try:
            args = template_dict.pop("args")
        except KeyError:
            logger.warning(f"Couldn't find 'args' value in Parser Template {parser_template}")
            return
        try:
            action = template_dict["action"]
            # use the dest value from the template
            dest = template_dict["dest"]
            if action == ParserAttribute.STORE_TRUE.value:
                self._parser.set_defaults(**{dest:False})
            else:
                self._parser.set_defaults(**{dest:True})
        except KeyError:
            pass
        self._parser.add_argument(*args,**template_dict)
        return (args,template_dict)

    def add_file_param(self,is_output:bool=False,suffix:str="txt",params:dict=None)->set:
        """ add file input / output file, default is input """

        if not params:
            params = {}

        # default params
        if is_output:
            parser_template = ParserTemplate.PARAM_OUTPUTFILE
            short_param = "fo"
        else:
            parser_template = ParserTemplate.PARAM_INPUTFILE
            short_param = "fi"
        long_param = parser_template.value["default"]
        # set a default file name if not passed
        if params.get("default"):
            default_param = params.get("default")
        else:
            default_param = long_param
        default_file = default_param+"."+suffix
        params["default"] = default_file
        args, kwargs = ParserTemplate.get_parser_arguments(parser_template,long_param,short_param,params)
        self._parser.add_argument(*args,**kwargs)
        return (args,kwargs)

    def add_argument(self,long_arg:str,short_arg:str,argument_dict:dict,
                          parser_template:ParserTemplate.PARAM_TEMPLATE)->set:
        """ adds an argument to the argument parser """
        args,kwargs=ParserTemplate.get_parser_arguments(parser_template,long_arg,short_arg,
                                                        argument_dict)
        self._parser.add_argument(*args,**kwargs)
        # add default value in case we have a bool argument
        try:
            action = parser_template.value["action"]
            if action == ParserAttribute.STORE_TRUE.value:
                self._parser.set_defaults(**{long_arg:False})
            else:
                self._parser.set_defaults(**{long_arg:True})
        except KeyError:
            pass

        return (args,kwargs)

    def add_arguments(self,arg_list:list,
                      input_filetype:str="yaml",
                      output_filetype:str=None,
                      add_log_level:bool=True,
                      add_csv_separator:bool=True,
                      add_decimal_separator:bool=True,
                      add_timestamp:bool=True)->None:
        """ multiple inserts of arguments, each entry needs to conform to the schema
            [long_shortcut(str),short_shortcut(str),argument_dict(dict),ParserTemplate(ParserTemplate)]
            Optionally create argument templates for logging level, input file and output file
            file suffixes supported ["json","txt","yaml","plantuml"]
        """
        for arg in arg_list:
            long_arg = arg[0]
            short_arg = arg[1]
            arg_dict = arg[2]
            parser_template = arg[3]
            logger.debug(f"Adding Parameter {long_arg}/{short_arg}, template {parser_template.name}")
            self.add_argument(long_arg,short_arg,arg_dict,parser_template)
            logger.debug(f"Adding argument {long_arg}, {parser_template}")
        # add template parameters
        if input_filetype and input_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(suffix=input_filetype)
        if output_filetype and output_filetype.lower() in PersistenceHelper.ALLOWED_FILE_TYPES:
            self.add_file_param(is_output=True,suffix=output_filetype)
        if add_log_level:
            self.add_arg_template(ParserTemplate.PARAM_LOGLEVEL)
            #self.add_loglevel_arg()
        if add_csv_separator:
            self.add_arg_template(ParserTemplate.PARAM_CSV_SEPARATOR)
            #self.add_csv_separator()
        if add_decimal_separator:
            self.add_arg_template(ParserTemplate.PARAM_DECIMAL_SEP)
            #self.add_decimal_separator()
        if add_timestamp:
            self.add_arg_template(ParserTemplate.PARAM_ADD_TIMESTAMP)

class FileTransformer():
    """ sample class to transform from various input to output formats """
    OUT_FIELDS = "out_fields"
    TEMPLATE_DICT = "template_dict"

    def __init__(self,f_read:str=None,**kwargs) -> None:
        """ original file location """
        self._persistence_helper = PersistenceHelper(f_read,**kwargs)
        self._data = None
        # used for control of csv output
        self._header_filter = None # filtering entries
        self._template_dict = {} # string templates to get derived field entries

        self._out_fields = kwargs.get(FileTransformer.OUT_FIELDS,[]) # list of fields for export
        self._template_dict = kwargs.get(FileTransformer.TEMPLATE_DICT,{}) # replacement dict for template
        # output
        self._line_dict_list = []

    @property
    def data(self):
        """ gets the data """
        return self._data

    @property
    def header_filter(self):
        """ headerdict filter """
        return self._header_filter

    @header_filter.setter
    def header_filter(self,header_filter:list)->None:
        """ adds a headerdict filter """
        logger.info(f"Adding header filter {header_filter}")
        self._header_filter = header_filter

    def _modify_header_dict_list(self):
        """ adjust fields / enrich fields, this is use case  specific, example for sample is shown  """
        # name convention: __attribute__ will be replaced by attribute attribute in field list
        REGEX_PLACEHOLDERS="__[A-Za-z_#0-9]+__" # regex to identify placeholders
        out_list = []
        for line_dict in self._line_dict_list:
            line_out={}
            for out_field in self._out_fields:
                v = line_dict.get(out_field,"FIELD_NOT_FOUND")
                t = self._template_dict.get(out_field)
                if t:
                    placeholders = re.findall(REGEX_PLACEHOLDERS,t)
                    # replace all placeholders from values in line dict
                    for placeholder in placeholders:
                        column = placeholder[2:-2] # note case sensitive
                        col_value = line_dict.get(column)
                        if not col_value:
                            col_value="_NOT_FOUND_"
                        t = t.replace(placeholder,col_value)
                    line_out[out_field]=t
                else:
                    line_out[out_field]=v
            out_list.append(line_out)
        self._line_dict_list = out_list
        return out_list

    def get_list_from_header_dict(self):
        """ returns the dict list for a header dict """
        self._line_dict_list = PersistenceHelper.headerdict2list(self._data,self._header_filter)
        if self._out_fields:
            self._modify_header_dict_list() # modify / enrich the list for csv output
        return self._line_dict_list

    def get_header_dict_from_list(self,id_title:str=PersistenceHelper.ID_TITLE,
                                  num_col_title:str=PersistenceHelper.NUM_COL_TITLE)->dict:
        """ returns the header dict from a dict list """
        out_dict = {}
        if self._data is None:
            logger.warning("Data is empty, read data before call")
            return
        if not isinstance(self._data,list):
            logger.warning("Data stored in object is not a list, check your program")
        for dict_line in self._data:
            # remove index and keys
            keys = list(dict_line.keys())
            keys = [k for k in keys if k not in [id_title,num_col_title]]
            # overwrite by out fields list
            if self._out_fields:
                keys = self._out_fields
            line_dict = {}
            header_key = dict_line.get(id_title)
            if not header_key:
                logger.warning(f"Couldn't find attribute {id_title} in dict to get header dict {dict_line}")
            for key in keys:
                v = dict_line.get(key)
                if v:
                    line_dict[key]=v
            out_dict[header_key]=line_dict
            logger.info(f"Added dict with key {header_key}")
        return out_dict


    def read(self)->None:
        """ reads data """
        self._data = self._persistence_helper.read()
        return self._data

    def save(self,f_save:str=None,file_type:str=None)->str:
        """ saves data either using given file or file in class, returns filename """
        # get the original file format so as to check for possible transformations
        f_read = self._persistence_helper.f_read
        original_filetype = f_read.suffix[1:]

        data = self._data

        # if file type is used get save file name based on read file name
        if file_type and file_type.lower() in [*PersistenceHelper.ALLOWED_FILE_TYPES,"csv"]:
            f_read = self._persistence_helper.f_read
            f_name = f_read.stem+"."+file_type
            f_save = os.path.join(f_read.parent,f_name)

        # linearize dict item when saving as csv
        if file_type == "csv"  and isinstance(data,dict):
            data = self.get_list_from_header_dict()

        # turn list of dicts into a dict structure to allow for saving as yaml, json
        if file_type in ["yaml","json"] and original_filetype in ["csv"]:
            data = self.get_header_dict_from_list()

        f_saved = self._persistence_helper.save(data,f_save)
        return f_saved

def get_argument_list()->list:
    """ sample how to compile argument list """
    arg_list=[["myvar","v",{  "default":"default","help":"help description","metavar":"<var>" } ,
               ParserTemplate.PARAM_TEMPLATE],
              ["myflag","f",
               { "help":"help flag (Default False, True if set)" },
               ParserTemplate.BOOL_TEMPLATE_TRUE]]
    return arg_list

if __name__ == "__main__":
    parser =  ParserHelper(description="Test Description",prog="my Prog",epilog="The End")
    # handle files, in general use case it is to read a file and save a file
    arg_list = get_argument_list()
    parser.add_arguments(arg_list,add_log_level=True,input_filetype="yaml",output_filetype="csv",add_timestamp=True)

    # test file param, added manually
    # parser.add_file_param(is_output=True,suffix="json",params={"help":"my own help text","default":"my_own_file_name"})
    # parser.add_file_param(suffix="json",params={"help":"my own help text","default":"myownfile"})

    # all command line arguments passed as dict, get some cofnigurations
    # debug configuration by adding command string
    if False:
        config_dict = parser.parse_args("--file_in test2.csv --file_out test_out.csv".split())
    else:
        config_dict = parser.parse_args()
    loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    csv_sep = config_dict.get("csv_sep",";")
    dec_sep = config_dict.get("dec_sep",",")
    file_in = config_dict.get("file_in")
    file_out = config_dict.get("file_out")
    add_timestamp = config_dict.get("add_timestamp",False)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")

    logger.info(f"\nConfig:\n {json.dumps(config_dict, indent=4)}")

    # get the file name from configuration
    if False:
        work_dir = str(Path(__file__).parent)
        # read sample file
        file_in="sample.yaml"
        os.chdir(work_dir)

        # control order and output fields
        num_col_title = PersistenceHelper.NUM_COL_TITLE
        header_id = PersistenceHelper.ID_TITLE
        out_fields=[num_col_title,header_id,"property1","part","url","comment","status"]
        # templates to generate new csv columns based on existing attributes
        template_dict={"url":f"http://www.test/__part__/__{num_col_title}__"}
        sample_transformer = FileTransformer(file_in,add_timestamp=True,out_fields=out_fields,template_dict=template_dict)
        # dict_filter=[{"status":"ignore"},{header_id:"key1"}]
        # ignore any input entries isth ignore status
        dict_filter=[{"status":"ignore"}]
        sample_transformer.header_filter = dict_filter
        data = sample_transformer.read()
        f_csv = sample_transformer.save(file_type="csv")
        # try to read saved csv again and recreate yaml with header again
        # out_fields=[]
        # out_fields=[num_col_title,header_id,"property1","part","url","comment","status"]
        out_fields=["property1","part","url","comment","status"]
        out_fields=[num_col_title,header_id,"part","url","comment","status"]
        sample_transformer_csv = FileTransformer(f_csv,add_timestamp=True,out_fields=out_fields)
        data_csv = sample_transformer_csv.read()
        # header_dict = sample_transformer_csv.get_header_dict_from_list()
        # save yaml into csv again
        sample_transformer_csv.save(file_type="json")

        # creating a headerdict template
        f = "template_test.json"
        headers = ["header2","header1"]
        headerdict_attributes = ["att3","att1","status"]
        headerdict_values = ["default",None,"undefined"]
        headerdict_template = dict(zip(headerdict_attributes,headerdict_values))
        f_save = PersistenceHelper.create_headerdict_template("template_test.json",headers,headerdict_template)
        f_save = PersistenceHelper.create_headerdict_template("template_test.yaml",headers,headerdict_template)
        f_save = PersistenceHelper.create_headerdict_template("template_test.csv",headers,headerdict_template)


    if False:
        file_helper = PersistenceHelper(f_read=file_in,f_save=file_out,add_timestamp=add_timestamp)
        in_dict = file_helper.read()
        file_helper.save(in_dict)
        pass


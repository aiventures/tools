""" Validates the cmd_client Config """
import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime as DateTime

from tools.util.recurse_dict import DictParser
# from tools.util.tree import Tree
from tools.cmd_client.persistence_helper import PersistenceHelper
from tools.cmd_client.configpath import TEST_CONFIG,VALIDATION_REPORT
from tools.cmd_client import constants as C
from tools.cmd_client.enum_helper import EnumHelper

logger = logging.getLogger(__name__)

# ROOT = "root"
KEY_PATH = "key_path"
VALUE = "value"
LINE_KEY = PersistenceHelper.LINE_KEY
LEAF_DICT = "leaf_dict"
DEFAULT_CATEGORY = "result"
MD_LINES = "md_lines"
LINK = "links"
HEADER = "header"
SPACER = "----"
TOC = "# TOC"

REGEX_SPECIALCHARS = "[\\\;:().,;/]"

class YamlAnalyzer():
    """ Template """
    def __init__(self,f_config:str,f_validation:str=None,categories:dict=None) -> None:
        """ Constructor """
        self._persistence = PersistenceHelper(f_config,f_validation)
        # read configuration with line numbers
        self._read_config(line_key=LINE_KEY)
        # get all configuration leafs
        self._config_leaves = {}
        self._config_leaf_keys = []
        self._analyze_tree()
        # read configuration again, without the index numbers
        self._read_config()
        # report categories: uses variable / text
        self._categories = {DEFAULT_CATEGORY:"Elements"}
        if categories:
            self._categories = categories

    def _read_config(self,line_key:str=None):
        """ reads the configuration """
        config = self._persistence.read(line_key=line_key)
        self._config_dict = DictParser(config)

    def _analyze_tree(self):
        """ analyze the configuration tree get all config values """

        config_tree = self.config_tree
        line = None
        # get all leaves
        leaf_ids = config_tree.get_leaves()
        for leaf_id in leaf_ids:
            # get the complete key path for each leaf
            key_list = config_tree.get_key_path(leaf_id)[1:]
            # skip the line attribute to be added
            if isinstance(key_list,list) and key_list[-1]==LINE_KEY:
                continue
            key_path = "/".join(key_list)
            value = self._config_dict.itemized_dict
            if value:
                for key in key_list:
                    value = value[key]
                    if isinstance(value,dict):
                        try:
                            line = value.get(LINE_KEY)
                        except KeyError:
                            line = None
            if value:
                self._config_leaves[key_path]={KEY_PATH:key_list,VALUE:value,LINE_KEY:line}
        self._config_leaf_keys = list(self._config_leaves.keys())
        logger.info(f"Processed Leaves in Config: {len(self._config_leaves)} elements")

    @property
    def config_tree(self):
        """ gets the config tree """
        return self._config_dict.tree

    @property
    def leaf_keys(self):
        """ gets all leaf keys  """
        return self._config_leaf_keys

    def get_leaf_elements(self,*args)->dict:
        """ gets all leaf elements """
        leaf_dict = {}
        key = "/".join(args)
        # check if it is a single key or a partial key is submitted
        if key in self.leaf_keys:
            leaf_keys = [key]
        else:
            leaf_keys = [l for l in self._config_leaf_keys if l.startswith(key)]

        for leaf in leaf_keys:
            leaf_dict[leaf] = self._config_leaves[leaf]

        return leaf_dict

    def get_config_element(self,*args,info:bool=False):
        """ returns the subtree element of the configuration
            returns value and optionally key path and line
        """
        out = self._config_dict.itemized_dict
        warning_s = None
        if not out:
            logger.warning("Empty Data")
            return
        out_args = []
        for arg in args:
            if not arg:
                break
            if isinstance(out,dict):
                out = out.get(arg)
                if out:
                    out_args.append(arg)
                else:
                    break

        # check on number of hierarchy elements read
        if len(args) != len(out_args):
            warning_s = f"Couldn't find element in path [{str(args)}], only found [{str(out_args)}]"
            logger.info(warning_s)

        # now get the leaf elements
        leaf_dict = self.get_leaf_elements(*out_args)

        # get the minimum line
        min_line = 999999
        if leaf_dict:
            for v in leaf_dict.values():
                l = v.get(LINE_KEY)
                if l and int(l) < min_line:
                    min_line = int(l)
        min_line = str(l)
        if not info:
            return out
        else:
            return {C.VALUE:out,LEAF_DICT:leaf_dict,LINE_KEY:min_line}

    def create_category_header(self,category:str):
        """ creates a category header """
        f = self._persistence.f_read
        return f"{category} ({f})"

    @staticmethod
    def get_md_link(link:str,text:str=None):
        """ gets an md anchor / link """
        if not text:
            text = link
        link = link.lower()
        link = re.sub(REGEX_SPECIALCHARS,"",link)
        link = "#"+link.replace(" ","-")
        return f"[{text}]({link})"

    def get_markdown_dict(self)->dict:
        """ gets markdown """

        toc = []
        lines_dict = {}
        categories = list(self._categories.keys())
        f = self._persistence.f_read

        for leaf,leaf_info in self._config_leaves.items():
            key = leaf.split("/")
            config_element = self.get_config_element(*key,info=True)
            value = config_element.get(C.VALUE)
            line = str(config_element.get(LINE_KEY)).zfill(3)
            category = self.get_category(leaf,leaf_info,config_element)
            if not category:
                continue
            # markdown line
            md_line = f"(`L{line}`) `{leaf}`: {value}"
            cat_line_dict = lines_dict.get(category,{})
            if not cat_line_dict:
                lines_dict[category]=cat_line_dict
            out_key=f"{line}_{leaf}"
            cat_line_dict[out_key]=md_line

        #  assemble the markdown        
        for category in categories:
            cat_text = self._categories.get(category)
            cat_header = self.create_category_header(cat_text)
            cat_link = YamlAnalyzer.get_md_link(cat_header)

            cat_dict = lines_dict.get(category)
            if not cat_dict:
                continue

            lines = []
            for key in sorted(cat_dict.keys()):
                lines.append(cat_dict.get(key))
            lines_dict[category]={HEADER:cat_header,LINK:cat_link,MD_LINES:lines.copy()}

        return {str(f):lines_dict}
    
    def get_category(self,leaf,leaf_info,config_element):
        """ determine the category based on single line input"""
        # ... do your own implementation ... as a default only return a default category<
        # if None is returned this item wont be added to output list
        return DEFAULT_CATEGORY    
    
    def create_report(self):
        """ creates a report """
        markdown_dict = self.get_markdown_dict()
        md_report = MarkDownRenderer(markdown_dict).create_report()
        self._persistence.save("\n".join(md_report))

class MarkDownRenderer():
    """ renders markdown from input"""            

    def __init__(self,md_dict:dict) -> None:
        self._md_dict = md_dict
        
    def create_report(self)->list:
        """ returns the complete markdown as list """    
        logger.info("Create Report Lines")    
        num = 0
        out_lines = [SPACER]
        toc = [TOC]
        dt = f"CREATED: {DateTime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        for file,category_info in self._md_dict.items():
            for category,md_info in category_info.items():
                toc.append(f"* {md_info.get(LINK)}")
                out_lines.append(f"# {md_info.get(HEADER)}")
                md_lines = md_info.get(MD_LINES)
                for md_line in md_lines:
                    out_lines.append(f"1. {md_line}")
                out_lines.extend(["  ",f"[**TOC**](#toc)"," "])
                out_lines.append(SPACER)
        out_lines.append(dt)
        return [*toc,*out_lines]
    
if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    f_config = TEST_CONFIG
    f_validation = VALIDATION_REPORT
    analyzer = YamlAnalyzer(f_config,f_validation)
    # all leaf keys
    leaf_keys = analyzer.leaf_keys
    if False:
        # test: get element
        hier = ["pattern","notepadpp","param","notepadpp"]
        elem = analyzer.get_config_element(*hier,info=True)
    # get the report
    analyzer.create_report()

    pass


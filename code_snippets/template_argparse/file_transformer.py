""" argparse example """

import logging
import sys
import json
from argparse_helper import ParserHelper
from argparse_helper import ParserTemplate
from argparse_helper import FileTransformer
from argparse_helper import PersistenceHelper
from argparse_helper import Status
from argparse_helper import LogLevel

logger = logging.getLogger(__name__)
config_dict = {}

class FileTransformerRunner():
    """ bundling of File Transformer Properties for parsing """

    # added argparse fields
    ARG_TEMPLATE_FILE = "template_file"
    ARG_FILE_INPUT = "file_input"
    ARG_TRANSFORM_FILE = "transform_file"
    ARG_CREATE_TEMPLATE = "create_template"
    ARG_TO_CSV = "to_csv"
    ARG_TO_JSON = "to_json"
    ARG_TO_YAML = "to_yaml"

    # create a template with name
    PARSEARG_TEMPLATE = [ARG_TEMPLATE_FILE,"tf",
                          {"default":"data_template.yaml",
                           "help":"Creates Template File",
                           "metavar":"<templatename.(yaml|json|csv)>" },
                           ParserTemplate.PARAM_TEMPLATE]
    INPUT_FILE        = [ARG_FILE_INPUT,"if",
                         {"default":"data_template.yaml",
                          "help":"Input File to be transformed",
                          "metavar":"<filename.(yaml|json|csv)>" },
                          ParserTemplate.PARAM_TEMPLATE]
    PARSEFLAG_XFILE = [ARG_TRANSFORM_FILE,"xf",
                       { "help":"Transform File <input_file> (-xc) (-xj) (-xy)" },
                       ParserTemplate.BOOL_TEMPLATE_TRUE]      
    PARSEFLAG_TPL = [ARG_CREATE_TEMPLATE,"ct",
                     { "help":"Create Template File <template_file> (-xc) (-xj) (-xy)" },
                     ParserTemplate.BOOL_TEMPLATE_TRUE]                     
    PARSEFLAG_CSV = [ARG_TO_CSV,"xc",
                     { "help":"Use CSV format" },
                     ParserTemplate.BOOL_TEMPLATE_TRUE]
    PARSEFLAG_JSON = [ARG_TO_JSON,"xj",
                     { "help":"Use JSON format" },
                     ParserTemplate.BOOL_TEMPLATE_TRUE]
    PARSEFLAG_YAML = [ARG_TO_YAML,"xy",
                     { "help":"Use YAML format" },
                     ParserTemplate.BOOL_TEMPLATE_TRUE]

    PARSE_ARGS = [PARSEARG_TEMPLATE,INPUT_FILE,PARSEFLAG_XFILE,
                  PARSEFLAG_TPL,PARSEFLAG_CSV,
                  PARSEFLAG_JSON,PARSEFLAG_YAML]

    # HEADER DICT
    HEADERS = ["header2","header1"]
    HEADER_DICT_ATTRIBUTES = ["att1","att2","comment","url","status"]
    HEADER_DICT_VALUES = ["default","default","","url","new"]
    HEADER_DICT_TEMPLATE = dict(zip(HEADER_DICT_ATTRIBUTES,HEADER_DICT_VALUES))

    # TEMPLATE DICT
    TEMPLATE_DICT={"url":"http://www.test.com/__att1__/__att2__"}
    # Fields that shall be used in transformation, should be part of HEADER_DICT_ATTRIBUTES
    OUT_FIELDS=HEADER_DICT_ATTRIBUTES

def main(**kwargs):
    """ main logic """
    ftr = FileTransformerRunner()
    # num_col_title = PersistenceHelper.NUM_COL_TITLE
    # header_id = PersistenceHelper.ID_TITLE
    # create a template
    if kwargs.get(ftr.ARG_CREATE_TEMPLATE):
        headerdict_template = ftr.HEADER_DICT_TEMPLATE
        f_template = kwargs.get(ftr.ARG_TEMPLATE_FILE)
        if kwargs.get(ftr.ARG_TO_CSV):
            f_tpl = PersistenceHelper.replace_file_suffix(f_template,"csv")
            f_csv = PersistenceHelper.create_headerdict_template(f_tpl,ftr.HEADERS,headerdict_template)
        if kwargs.get(ftr.ARG_TO_JSON):
            f_tpl = PersistenceHelper.replace_file_suffix(f_template,"json")
            f_json = PersistenceHelper.create_headerdict_template(f_tpl,ftr.HEADERS,headerdict_template)
        if kwargs.get(ftr.ARG_TO_YAML):
            f_tpl = PersistenceHelper.replace_file_suffix(f_template,"yaml")
            f_yaml = PersistenceHelper.create_headerdict_template(f_tpl,ftr.HEADERS,headerdict_template)

    # transform file to target formats
    if kwargs.get(ftr.ARG_TRANSFORM_FILE):
        f_transform = kwargs.get(ftr.ARG_FILE_INPUT)
        kwargs[FileTransformer.TEMPLATE_DICT]=ftr.TEMPLATE_DICT
        kwargs[FileTransformer.OUT_FIELDS]=ftr.OUT_FIELDS
        file_transformer = FileTransformer(f_transform,**kwargs)
        # filter items tbd
        #     # dict_filter=[{"status":"ignore"},{header_id:"key1"}]
        #     # ignore any input entries isth ignore status
        #     dict_filter=[{"status":"ignore"}]
        #     sample_transformer.header_filter = dict_filter
        data = file_transformer.read()
        if not data:
            return
        if kwargs.get(ftr.ARG_TO_CSV):
            f_csv = file_transformer.save(file_type="csv")
            
        if kwargs.get(ftr.ARG_TO_JSON):
            f_json = file_transformer.save(file_type="json")
            
        if kwargs.get(ftr.ARG_TO_YAML):
            f_yaml = file_transformer.save(file_type="yaml")
            

if __name__ == "__main__":
    parser =  ParserHelper(description="File Transformer Utilityy, transforms data into Fileformats (json,yaml,csv)",
                           prog="file_transformer",epilog="Check the help options")
    # handle files, in general use case it is to read a file and save a file
    arg_list = FileTransformerRunner.PARSE_ARGS
    # add more input arguments to parser arguments
    # "template_file": "data_template.yaml",
    # "transform_file": "data_template.yaml",
    # "create_template": true,
    # "to_csv": false,
    # "to_json": false,
    # "to_yaml": false,
    # "loglevel": 20,
    # "csv_sep": ";",
    # "dec_sep": ",",
    # "add_timestamp": false
    parser.add_arguments(arg_list,
                         add_log_level=True,         # add an option to control log level
                         input_filetype=None,
                         output_filetype=None,
                         add_csv_separator=True,     # add option to define csv file separator char
                         add_decimal_separator=True, # add option to change decimal separator
                         add_timestamp=True)         # add option to automatically add timestamp to file name

    # debug configuration by adding command string
    if False:
        # sample config to create a template in all formats 
        config_dict = parser.parse_args("-ct -tf template_test.csv -xj -xy -xc".split())
        # sample config to create an output file form template with timestamp
        config_dict = parser.parse_args("-if template_test.json -xf -xc -as".split())
    else:
        config_dict = parser.parse_args()
    loglevel = config_dict.get("loglevel",LogLevel.INFO.value)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
    # show config
    logger.info(f"\nConfig:\n {json.dumps(config_dict, indent=4)}")
    main(**config_dict)



